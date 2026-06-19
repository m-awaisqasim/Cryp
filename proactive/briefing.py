from datetime import datetime, date
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.memory_manager import load_memory, query_patterns
from core.daemon import SystemHealthDaemon
from core.logger import get_logger

log = get_logger(__name__)


BRIEFING_FILE = Path(__file__).resolve().parent.parent / "memory" / "last_briefing_date.txt"


def _load_last_briefing_date() -> str | None:
    try:
        if BRIEFING_FILE.exists():
            return BRIEFING_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return None


def _save_last_briefing_date():
    try:
        BRIEFING_FILE.parent.mkdir(parents=True, exist_ok=True)
        BRIEFING_FILE.write_text(date.today().isoformat(), encoding="utf-8")
    except Exception as e:
        log.error("briefing_failed_to_save_date", exc_info=True)


def should_brief() -> bool:
    from config.settings import PROACTIVE_BRIEFING_ENABLED
    if not PROACTIVE_BRIEFING_ENABLED:
        return False
    last = _load_last_briefing_date()
    return last != date.today().isoformat()


def mark_briefed():
    try:
        BRIEFING_FILE.parent.mkdir(parents=True, exist_ok=True)
        BRIEFING_FILE.write_text(date.today().isoformat(), encoding="utf-8")
    except Exception as e:
        log.error("briefing_mark_briefed_failed", exc_info=True)


def generate_briefing(health_daemon: SystemHealthDaemon | None = None) -> str | None:
    try:
        now = datetime.now()
        hour = now.hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        parts = [f"{greeting}, sir."]

        if health_daemon is not None:
            snap = health_daemon.get_health_snapshot()
            if snap:
                battery = snap.get("battery_percent")
                if battery is not None and not snap.get("battery_plugged", True):
                    parts.append(f"Battery is at {battery} percent.")

        patterns = query_patterns(days_back=1)
        if patterns:
            last = patterns[0]
            summary = last.get("summary", "").strip()
            if summary and "Session on" not in summary:
                if len(summary) > 120:
                    summary = summary[:117] + "..."
                parts.append(f"Last session: {summary}")

        text = " ".join(parts)
        if len(text) > 400:
            text = text[:397] + "..."

        _save_last_briefing_date()
        return text
    except Exception as e:
        log.error("briefing_generate_failed", exc_info=True)
        return None
