import asyncio
import os
import time

try:
    import psutil
except ImportError:
    psutil = None


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
                print(f"[daemon] unexpected error: {e}")

    def _publish_stats(self):
        if self._event_bus is None:
            return
        try:
            cpu = psutil.cpu_percent(interval=0)
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
            pct = psutil.cpu_percent(interval=0)
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
        self._alert_speak(text)

    def _check_metric(self, name: str, pct: float, threshold: int, alert_text: str):
        if pct >= threshold:
            self._consecutive[name] += 1
            if self._consecutive[name] >= 2 and self._debounce_allowed(name):
                self._last_alert_time[name] = time.time()
                self._write_log(f"ALERT: {name.upper()} at {pct:.0f}%")
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
