import subprocess
import sys
import time
from datetime import datetime

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
