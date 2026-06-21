import json
from datetime import datetime, date
from pathlib import Path
import sys

from core.logger import get_logger
log = get_logger(__name__)


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "main.py").exists() or (p / ".git").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent.parent


ASSIGNMENTS_PATH = _base_dir() / "memory" / "assignments.json"


def _load() -> list[dict]:
    if not ASSIGNMENTS_PATH.exists():
        return []
    try:
        raw = ASSIGNMENTS_PATH.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else []
        return data if isinstance(data, list) else []
    except Exception:
        log.error("assignments_load_error", exc_info=True)
        return []


def _save(items: list[dict]) -> None:
    try:
        ASSIGNMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ASSIGNMENTS_PATH.write_text(
            json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        log.error("assignments_save_error", exc_info=True)


def _parse_due(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return raw


def _safe_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def assignment_tracker(parameters: dict, player=None, **kwargs) -> str:
    params = parameters or {}
    action = params.get("action", "list").lower().strip()
    items = _load()

    if action == "add":
        title = params.get("title", "").strip()
        if not title:
            return "Please give me the assignment title, sir."
        entry = {
            "id": f"a{len(items) + 1}_{int(datetime.now().timestamp())}",
            "title": title,
            "course": params.get("course", "").strip(),
            "due_date": _parse_due(params.get("due_date", "")),
            "priority": params.get("priority", "normal").lower().strip(),
            "status": "pending",
            "created": datetime.now().isoformat(timespec="seconds"),
        }
        items.append(entry)
        _save(items)
        if player:
            player.write_log(f"[Assignments] Added: {title}")
        due_str = f" due {entry['due_date']}" if entry["due_date"] else ""
        return f"Added '{title}'{due_str}, sir."

    if action == "complete":
        title_q = params.get("title", "").strip().lower()
        if not title_q:
            return "Please specify the assignment title to mark complete, sir."
        for it in items:
            if title_q in it["title"].lower() and it["status"] != "done":
                it["status"] = "done"
                it["completed"] = datetime.now().isoformat(timespec="seconds")
                _save(items)
                return f"Marked '{it['title']}' as complete, sir."
        return f"Couldn't find a pending assignment matching '{title_q}', sir."

    if action in ("list", "upcoming", "overdue"):
        today = date.today()
        pending = [it for it in items if it["status"] != "done"]

        if action == "overdue":
            pending = [
                it for it in pending
                if it["due_date"] and _safe_date(it["due_date"]) and _safe_date(it["due_date"]) < today
            ]
        elif action == "upcoming":
            pending = [
                it for it in pending
                if it["due_date"] and _safe_date(it["due_date"]) and _safe_date(it["due_date"]) >= today
            ]

        pending.sort(key=lambda it: it["due_date"] or "9999-99-99")

        if not pending:
            return "Nothing pending, sir. You're all caught up."

        lines = []
        for it in pending[:10]:
            due = it["due_date"] or "no due date"
            course = f" ({it['course']})" if it["course"] else ""
            lines.append(f"{it['title']}{course} — due {due}")
        return "Here's what's pending, sir: " + "; ".join(lines) + "."

    return f"Unknown assignment_tracker action: '{action}'."


def format_assignments_for_prompt(max_items: int = 8) -> str:
    items = [it for it in _load() if it["status"] != "done"]
    if not items:
        return ""
    items.sort(key=lambda it: it["due_date"] or "9999-99-99")
    lines = ["[PENDING ASSIGNMENTS]"]
    for it in items[:max_items]:
        due = it["due_date"] or "no due date"
        course = f" ({it['course']})" if it["course"] else ""
        lines.append(f"- {it['title']}{course} — due {due}")
    return "\n".join(lines) + "\n"
