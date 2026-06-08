import json
import os
import time
from datetime import datetime
from pathlib import Path

from core.logger import get_logger

log = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
RULES_PATH = BASE_DIR / "config" / "proactive_rules.json"
DEFAULT_RULES = [
    {
        "id": "terminal_updates",
        "condition": {
            "window_contains": ["Terminal", "bash", "zsh"],
            "time_range": ["08:00", "10:00"],
            "weekday_only": True,
        },
        "suggestion": "Sir, would you like me to run system updates while you work?",
    },
    {
        "id": "git_conflict",
        "condition": {
            "clipboard_contains": ["CONFLICT", "<<<<<<<"],
        },
        "suggestion": "Sir, I noticed a merge conflict in your clipboard. Shall I open VS Code to resolve it?",
    },
    {
        "id": "late_night_work",
        "condition": {
            "time_range": ["01:00", "04:00"],
        },
        "suggestion": "Sir, it is past 1 AM. Shall I save your work and set a reminder to continue tomorrow?",
    },
    {
        "id": "study_time",
        "condition": {
            "window_contains": ["pdf", "PDF", "slides", "Slides"],
            "time_range": ["09:00", "22:00"],
        },
        "suggestion": "Sir, I can summarize this document for you if needed.",
    },
]

_last_suggestion_time: float = 0.0
SUGGESTION_COOLDOWN = int(os.getenv("PROACTIVE_SUGGESTION_COOLDOWN", "1800"))


def _load_rules() -> list[dict]:
    try:
        if RULES_PATH.exists():
            return json.loads(RULES_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        log.error("suggestions_failed_to_load_rules", exc_info=True)
    return list(DEFAULT_RULES)


def _time_in_range(start: str, end: str) -> bool:
    try:
        now = datetime.now()
        start_h, start_m = map(int, start.split(":"))
        end_h, end_m = map(int, end.split(":"))
        start_min = start_h * 60 + start_m
        end_min = end_h * 60 + end_m
        now_min = now.hour * 60 + now.minute
        if start_min <= end_min:
            return start_min <= now_min <= end_min
        return now_min >= start_min or now_min <= end_min
    except Exception:
        return False


def _matches_condition(condition: dict, context: dict) -> bool:
    window = (context.get("active_window") or "").lower()
    clipboard = (context.get("clipboard") or "").lower()

    if "window_contains" in condition:
        if not any(kw.lower() in window for kw in condition["window_contains"]):
            return False

    if "clipboard_contains" in condition:
        if not any(kw.lower() in clipboard for kw in condition["clipboard_contains"]):
            return False

    if "time_range" in condition:
        if not _time_in_range(condition["time_range"][0], condition["time_range"][1]):
            return False

    if condition.get("weekday_only"):
        if datetime.now().weekday() >= 5:
            return False

    return True


def evaluate_suggestions(context: dict) -> str | None:
    global _last_suggestion_time
    now = time.time()
    if now - _last_suggestion_time < SUGGESTION_COOLDOWN:
        return None
    try:
        rules = _load_rules()
        for rule in rules:
            if _matches_condition(rule.get("condition", {}), context):
                _last_suggestion_time = now
                return rule.get("suggestion", "")
    except Exception as e:
        log.error("suggestions_evaluate_failed", exc_info=True)
    return None
