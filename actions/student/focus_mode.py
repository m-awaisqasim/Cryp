import time
from datetime import datetime, timedelta

from actions.reminder import reminder

_state = {"active": False, "subject": None, "started_at": None, "end_at": None}

# NOTE: reminder() has no exposed cancellation mechanism, so an early manual
# stop may still result in a stale end-of-session notification. This is a minor
# known limitation — notifications are harmless, just delayed. No crash.


def is_focus_active() -> bool:
    if not _state["active"]:
        return False
    if _state["end_at"] and time.time() > _state["end_at"]:
        _state["active"] = False
        return False
    return True


def focus_mode(parameters: dict, player=None, **kwargs) -> str:
    action = parameters.get("action", "status")

    if action == "start":
        subject = parameters.get("subject", "your work")
        duration = int(parameters.get("duration_minutes", 25))
        _state.update({
            "active": True,
            "subject": subject,
            "started_at": time.time(),
            "end_at": time.time() + duration * 60,
        })
        target = datetime.now() + timedelta(minutes=duration)
        reminder({
            "date": target.strftime("%Y-%m-%d"),
            "time": target.strftime("%H:%M"),
            "message": f"Focus session on {subject} is done, sir. Take a break.",
        })
        return f"Focus mode on for {subject}, {duration} minutes. I'll stay quiet unless it's urgent."

    if action == "stop":
        if not _state["active"]:
            return "Focus mode wasn't active, sir."
        elapsed = int((time.time() - _state["started_at"]) / 60)
        _state["active"] = False
        return f"Focus mode ended. You were focused on {_state['subject']} for {elapsed} minutes."

    if action == "status":
        if not is_focus_active():
            return "Focus mode is off, sir."
        remaining = int((_state["end_at"] - time.time()) / 60)
        return f"Focus mode active on {_state['subject']}, {remaining} minutes left."

    return "Unknown focus_mode action."
