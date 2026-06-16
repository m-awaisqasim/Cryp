import json
import math
import time
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.memory_manager import load_memory
from core.logger import get_logger

log = get_logger(__name__)

ANOMALY_COOLDOWN = int(os.getenv("PROACTIVE_ANOMALY_COOLDOWN", "1800"))
_last_alert_times: dict[str, float] = {}


def _debounce_allowed(metric: str) -> bool:
    last = _last_alert_times.get(metric)
    if last is None:
        return True
    return (time.time() - last) >= ANOMALY_COOLDOWN


def check_cpu_anomaly(current_cpu: float, baseline: dict) -> str | None:
    try:
        current = float(current_cpu)
        bl = baseline.get("cpu_baseline", {})
        if not bl or "mean" not in bl or "std" not in bl:
            return None
        mean = bl["mean"]
        std = bl["std"]
        if std <= 0:
            return None
        if current > mean + 2 * std and _debounce_allowed("cpu"):
            _last_alert_times["cpu"] = time.time()
            return f"Sir, CPU is unusually high at {current:.0f} percent compared to the usual {mean:.0f} at this time."
    except Exception as e:
        log.error("anomaly_cpu_check_failed", exc_info=True)
    return None


def check_ram_anomaly(current_ram: float, baseline: dict) -> str | None:
    try:
        current = float(current_ram)
        bl = baseline.get("ram_baseline", {})
        if not bl or "mean" not in bl or "std" not in bl:
            return None
        mean = bl["mean"]
        std = bl["std"]
        if std <= 0:
            return None
        if current > mean + 2 * std and _debounce_allowed("ram"):
            _last_alert_times["ram"] = time.time()
            return f"Sir, memory is unusually high at {current:.0f} percent compared to the usual {mean:.0f} at this time."
    except Exception as e:
        log.error("anomaly_ram_check_failed", exc_info=True)
    return None


_consecutive_app: dict[str, int] = {}


def check_app_anomaly(current_app: str | None, baseline: dict, hour: str) -> str | None:
    try:
        bl = baseline.get("app_baseline", {})
        if not bl:
            return None
        typical = bl.get(hour)
        if not typical or typical == current_app:
            _consecutive_app["app"] = 0
            return None
        _consecutive_app["app"] = _consecutive_app.get("app", 0) + 1
        if _consecutive_app["app"] >= 3 and _debounce_allowed("app"):
            _last_alert_times["app"] = time.time()
            _consecutive_app["app"] = 0
            return f"Sir, I notice you are using something different instead of your usual {typical} at this time."
    except Exception as e:
        log.error("anomaly_app_check_failed", exc_info=True)
    return None
