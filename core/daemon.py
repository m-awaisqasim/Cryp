import asyncio
import os
import time
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

from core.logger import get_logger

log = get_logger(__name__)


class SystemHealthDaemon:

    def __init__(self, speak, write_log, event_bus=None):
        self._speak = speak
        self._write_log = write_log
        self._event_bus = event_bus

        self._interval = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
        self._cpu_threshold = int(os.getenv("HEALTH_CPU_THRESHOLD", "90"))
        self._ram_threshold = int(os.getenv("HEALTH_RAM_THRESHOLD", "85"))
        self._disk_threshold = int(os.getenv("HEALTH_DISK_THRESHOLD", "90"))
        self._battery_threshold = int(os.getenv("HEALTH_BATTERY_THRESHOLD", "20"))
        self._debounce_seconds = int(os.getenv("HEALTH_DEBOUNCE_SECONDS", "300"))

        self._consecutive = {"cpu": 0, "ram": 0, "disk": 0, "battery": 0}
        self._last_alert_time: dict[str, float] = {}
        self._last_stats: dict = {}
        self._alert_history: list[dict] = []

    def get_health_snapshot(self) -> dict:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            dsk = psutil.disk_usage("/")
            bat = psutil.sensors_battery()
            snap = {
                "cpu_percent": cpu,
                "ram_percent": mem.percent,
                "ram_used_gb": round(mem.used / (1024 ** 3), 1),
                "ram_total_gb": round(mem.total / (1024 ** 3), 1),
                "disk_percent": dsk.percent,
                "battery_percent": int(bat.percent) if bat else None,
                "battery_plugged": bat.power_plugged if bat else None,
                "last_check_timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            self._last_stats = snap
            return snap
        except Exception:
            return self._last_stats or {}

    def get_alert_history(self, minutes_back: int = 30) -> list[dict]:
        cutoff = time.time() - (minutes_back * 60)
        return [a for a in self._alert_history if a.get("timestamp", 0) >= cutoff]

    def _record_alert(self, metric: str, value: float, message: str):
        entry = {
            "timestamp": time.time(),
            "metric": metric,
            "value": value,
            "message": message,
        }
        self._alert_history.append(entry)
        if len(self._alert_history) > 50:
            self._alert_history = self._alert_history[-50:]

    async def run(self):
        if psutil is None:
            self._write_log("SYS: psutil not available — health daemon disabled")
            return
        while True:
            try:
                await asyncio.sleep(self._interval)
                self._check_cpu()
                self._check_ram()
                self._check_disk()
                self._check_battery()
                self._publish_stats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("daemon_unexpected_error", exc_info=True)

    def _publish_stats(self):
        if self._event_bus is None:
            return
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            battery = None
            bat = psutil.sensors_battery()
            if bat is not None and not bat.power_plugged:
                battery = bat.percent
            self._event_bus.publish({
                "type": "stats",
                "data": {
                    "cpu": cpu,
                    "ram": ram,
                    "disk": disk,
                    "battery": battery,
                }
            })
        except Exception:
            pass

    def _check_cpu(self):
        try:
            pct = psutil.cpu_percent(interval=0.1)
        except Exception:
            return
        self._check_metric("cpu", pct, self._cpu_threshold,
                           f"Sir, CPU is at {pct:.0f} percent.")

    def _check_ram(self):
        try:
            pct = psutil.virtual_memory().percent
        except Exception:
            return
        self._check_metric("ram", pct, self._ram_threshold,
                           f"Sir, memory is at {pct:.0f} percent.")

    def _check_disk(self):
        try:
            pct = psutil.disk_usage("/").percent
        except Exception:
            return
        self._check_metric("disk", pct, self._disk_threshold,
                           f"Sir, disk is at {pct:.0f} percent.")

    def _check_battery(self):
        try:
            bat = psutil.sensors_battery()
        except Exception:
            return
        if bat is None:
            return
        if bat.power_plugged:
            return
        pct = bat.percent
        if pct > self._battery_threshold:
            self._consecutive["battery"] = 0
            return
        if not self._debounce_allowed("battery"):
            return
        self._consecutive["battery"] = 0
        self._last_alert_time["battery"] = time.time()
        text = f"Sir, battery is at {pct:.0f} percent."
        self._write_log(f"ALERT: Battery at {pct:.0f}%")
        self._record_alert("battery", pct, text)
        self._alert_speak(text)

    def _check_metric(self, name: str, pct: float, threshold: int, alert_text: str):
        if pct >= threshold:
            self._consecutive[name] += 1
            if self._consecutive[name] >= 2 and self._debounce_allowed(name):
                self._last_alert_time[name] = time.time()
                self._write_log(f"ALERT: {name.upper()} at {pct:.0f}%")
                self._record_alert(name, pct, alert_text)
                self._alert_speak(alert_text)
        else:
            self._consecutive[name] = 0

    def _debounce_allowed(self, metric: str) -> bool:
        last = self._last_alert_time.get(metric)
        if last is None:
            return True
        return (time.time() - last) >= self._debounce_seconds

    def _alert_speak(self, text: str):
        try:
            self._speak(text)
        except Exception:
            pass
