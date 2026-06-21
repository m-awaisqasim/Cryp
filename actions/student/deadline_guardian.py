import os
import datetime as dt
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"
TOKEN_PATH = CONFIG_DIR / "token.json"


def _get_credentials():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}. "
                    "Google Cloud OAuth setup needs to be completed first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def _fetch_classroom_deadlines(creds, days_ahead=14):
    service = build("classroom", "v1", credentials=creds)
    results = []
    courses = service.courses().list(courseStates=["ACTIVE"]).execute().get("courses", [])
    cutoff = dt.date.today() + dt.timedelta(days=days_ahead)
    for course in courses:
        course_id = course["id"]
        course_name = course.get("name", "Course")
        try:
            work_resp = service.courses().courseWork().list(courseId=course_id).execute()
        except HttpError as e:
            print(f"courseWork list failed for {course_name}: {e}")
            continue
        for work in work_resp.get("courseWork", []):
            due = work.get("dueDate")
            if not due:
                continue
            try:
                due_date = dt.date(due["year"], due["month"], due["day"])
            except (KeyError, ValueError):
                continue
            if due_date < dt.date.today() or due_date > cutoff:
                continue
            results.append({
                "source": "classroom",
                "course": course_name,
                "title": work.get("title", "Untitled"),
                "due_date": due_date.isoformat(),
                "link": work.get("alternateLink", ""),
            })
    return results


def _fetch_calendar_deadlines(creds, days_ahead=14):
    service = build("calendar", "v3", credentials=creds)
    now = dt.datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + dt.timedelta(days=days_ahead)).isoformat() + "Z"
    events = service.events().list(
        calendarId="primary", timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy="startTime",
    ).execute().get("items", [])
    results = []
    for event in events:
        start = event.get("start", {})
        due_raw = start.get("date") or start.get("dateTime")
        if not due_raw:
            continue
        results.append({
            "source": "calendar",
            "course": "",
            "title": event.get("summary", "Untitled event"),
            "due_date": due_raw[:10],
            "link": event.get("htmlLink", ""),
        })
    return results


def _dedupe_against_tracker(items):
    from actions.student.assignment_tracker import _load as load_tracker
    tracker_titles = {
        a["title"].lower()
        for a in load_tracker()
        if a.get("status") != "done"
    }
    return [it for it in items if it["title"].lower() not in tracker_titles]


def deadline_guardian(parameters: dict, player=None, **kwargs) -> str:
    action = parameters.get("action", "check")
    days = int(parameters.get("days", 7))

    try:
        creds = _get_credentials()
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Could not authenticate with Google, sir: {e}"

    try:
        classroom_items = _fetch_classroom_deadlines(creds, days_ahead=days)
    except Exception:
        classroom_items = []
    try:
        calendar_items = _fetch_calendar_deadlines(creds, days_ahead=days)
    except Exception:
        calendar_items = []

    all_items = sorted(classroom_items + calendar_items, key=lambda x: x["due_date"])
    new_items = _dedupe_against_tracker(all_items)

    if action == "sync":
        from actions.student.assignment_tracker import _load as load_tracker, _save as save_tracker
        tracker_items = load_tracker()
        added = 0
        existing_titles = {a["title"].lower() for a in tracker_items}
        for it in new_items:
            if it["title"].lower() not in existing_titles:
                from datetime import datetime as dt_now
                tracker_items.append({
                    "id": f"a{len(tracker_items) + 1}_{int(dt_now.now().timestamp())}",
                    "title": it["title"],
                    "course": it.get("course", ""),
                    "due_date": it["due_date"],
                    "priority": "normal",
                    "status": "pending",
                    "created": dt_now.now().isoformat(timespec="seconds"),
                })
                existing_titles.add(it["title"].lower())
                added += 1
        save_tracker(tracker_items)
        if added:
            return f"Synced {added} new deadline(s) into your assignment tracker, sir."
        return "Nothing new to sync — deadlines already in your tracker, sir."

    if not new_items:
        return "Nothing new coming up beyond what's already on your tracker, sir."
    lines = [
        f"{it['title']} due {it['due_date']}" + (f" ({it['course']})" if it["course"] else "")
        for it in new_items[:5]
    ]
    extra = f", and {len(new_items) - 5} more" if len(new_items) > 5 else ""
    return "Upcoming deadlines: " + "; ".join(lines) + extra + "."
