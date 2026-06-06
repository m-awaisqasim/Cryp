import math
import subprocess
import sys
import threading
import time
from datetime import datetime, date

import psutil
import pyperclip


def get_active_window() -> str | None:
    try:
        if sys.platform != "linux":
            return None
        result = subprocess.check_output(
            ["xdotool", "getactivewindow", "getwindowname"],
            text=True, timeout=1
        ).strip()
        if not result:
            time.sleep(0.1)
            result = subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowname"],
                text=True, timeout=1
            ).strip()
        return result if result else None
    except Exception:
        return None


def get_clipboard() -> str | None:
    try:
        text = pyperclip.paste()
        if not text:
            return None
        text = text.replace("\n", " ").replace("\r", " ")
        if len(text) > 200:
            text = text[:200] + "..."
        return text
    except Exception:
        return None


def get_battery() -> str | None:
    try:
        bat = psutil.sensors_battery()
        if bat is None:
            return None
        pct = int(bat.percent)
        if bat.power_plugged:
            status = "charging"
            remaining = ""
        else:
            status = "discharging"
            if bat.secsleft > 0 and bat.secsleft != psutil.POWER_TIME_UNLIMITED:
                hrs = bat.secsleft // 3600
                mins = (bat.secsleft % 3600) // 60
                remaining = f" ({hrs}h {mins}m remaining)"
            else:
                remaining = ""
        return f"{pct}% \u2014 {status}{remaining}"
    except Exception:
        return None


def get_cpu_usage() -> str | None:
    try:
        pct = psutil.cpu_percent(interval=0.1)
        return f"{pct}%"
    except Exception:
        return None


def get_ram_usage() -> str | None:
    try:
        mem = psutil.virtual_memory()
        used_gb = mem.used / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        return f"{mem.percent}% ({used_gb:.1f} / {total_gb:.1f} GB)"
    except Exception:
        return None


_daily_agg_lock = threading.Lock()
_daily_agg_date: str | None = None
_daily_agg_data: dict = {"app_launches": [], "window_changes": []}


def _ensure_daily_agg():
    global _daily_agg_date, _daily_agg_data
    today = date.today().isoformat()
    if _daily_agg_date != today or "app_launches" not in _daily_agg_data:
        _daily_agg_date = today
        _daily_agg_data = {"app_launches": [], "window_changes": []}


def log_app_launch(app_name: str):
    with _daily_agg_lock:
        _ensure_daily_agg()
        _daily_agg_data["app_launches"].append({
            "app_name": app_name,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })


def log_window_change(window_title: str):
    with _daily_agg_lock:
        _ensure_daily_agg()
        _daily_agg_data["window_changes"].append({
            "window_title": window_title,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })


def get_daily_aggregation() -> dict:
    with _daily_agg_lock:
        _ensure_daily_agg()
        return {
            "app_launches": list(_daily_agg_data["app_launches"]),
            "window_changes": list(_daily_agg_data["window_changes"]),
        }


def gather_proactive_context() -> dict:
    ctx = {
        "active_window": get_active_window(),
        "clipboard": get_clipboard(),
        "battery": get_battery(),
        "cpu": get_cpu_usage(),
        "ram": get_ram_usage(),
        "session_started_at": datetime.now().isoformat(timespec="seconds"),
        "session_uptime_seconds": 0,
        "app_launches_today": [],
        "window_changes": [],
    }
    agg = get_daily_aggregation()
    ctx["app_launches_today"] = agg["app_launches"]
    ctx["window_changes"] = agg["window_changes"]
    return ctx


def gather_live_context() -> str:
    fields = {
        "Active Window": get_active_window(),
        "Clipboard": get_clipboard(),
        "Battery": get_battery(),
        "CPU": get_cpu_usage(),
        "RAM": get_ram_usage(),
        "Time": datetime.now().strftime("%A %d %B %Y \u2014 %H:%M:%S"),
    }
    lines = [
        line for line in (
            f"{k.ljust(14)}: {v}" for k, v in fields.items() if v is not None
        )
    ]
    if not lines:
        return ""
    return "[LIVE CONTEXT]\n" + "\n".join(lines) + "\n"
