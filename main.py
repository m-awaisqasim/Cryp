import asyncio
import atexit
import os
import re
import sys
import threading
import time
import traceback
import warnings
from datetime import datetime
from pathlib import Path

from config.settings import GEMINI_API_KEY

warnings.filterwarnings(
    "ignore",
    message="Specified provider 'CUDAExecutionProvider' is not in available provider names",
    category=UserWarning,
)


def _reexec_with_local_venv() -> None:
    if getattr(sys, "frozen", False):
        return

    base_dir = Path(__file__).resolve().parent
    try:
        invoked_path = Path(sys.argv[0]).resolve()
    except Exception:
        return
    if invoked_path != Path(__file__).resolve():
        return

    if os.name == "nt":
        venv_python = base_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = base_dir / ".venv" / "bin" / "python"

    if not venv_python.exists():
        return

    current = Path(sys.executable).resolve()
    target = venv_python.resolve()
    if current != target:
        os.execv(str(target), [str(target), *sys.argv])


_reexec_with_local_venv()

from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from websockets.exceptions import ConnectionClosedError
from ui import JarvisUI
from core.wake_config import WakeConfig
from core.daemon import SystemHealthDaemon
from core.context_collector import gather_live_context, log_app_launch
from proactive.conversation_state import ConversationState
from proactive.queue import ProactiveQueue
from proactive.engine import ProactiveEngine
try:
    from dashboard.event_bus import DashboardEventBus
    from dashboard.server import start_dashboard
except ImportError:
    DashboardEventBus = None
    start_dashboard = None
from memory.memory_manager import (
    load_memory, update_memory, format_memory_for_prompt,
    load_recent_episodes, format_episodes_for_prompt,
    search_episodes, prune_episodes,
)

from actions.file_processor import file_processor
from actions.flight_finder     import flight_finder
from actions.open_app          import open_app
from actions.weather_report    import weather_action
from actions.send_message      import send_message
from actions.reminder          import reminder
from actions.computer_settings import computer_settings
from actions.screen_processor  import screen_process
from actions.youtube_video     import youtube_video
from actions.desktop           import desktop_control
from actions.browser_control   import browser_control
from actions.file_controller   import file_controller
from actions.code_helper       import code_helper
from actions.dev_agent         import dev_agent
from actions.web_search        import web_search as web_search_action
from actions.computer_control  import computer_control
from actions.game_updater      import game_updater
from actions.webbridge          import webbridge_tool
from actions.jarvis_status      import jarvis_status
from core.retry import make_retry_decorator
from agent.config import RetryConfig
from core.logger import get_logger

log = get_logger(__name__)


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR        = get_base_dir()
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"

LIVE_MODEL          = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS            = 1
SEND_SAMPLE_RATE    = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE          = 1024
ENABLE_RECALL_TOOL  = os.getenv("ENABLE_RECALL_TOOL", "0") == "1"


class ReconnectRequested(Exception):
    pass


def _get_sounddevice():
    import sounddevice as sd
    return sd


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are JARVIS, Awais's AI assistant. "
            "Be concise, direct, and always use the provided tools to complete tasks. "
            "Never simulate or guess results — always call the appropriate tool."
        )


_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)


def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()


def _should_reconnect(exc: Exception) -> bool:
    if isinstance(exc, ConnectionClosedError):
        return True

    if isinstance(exc, genai_errors.APIError):
        if getattr(exc, "status_code", None) == 1011:
            return True
        if "deadline expired" in str(exc).lower():
            return True

    if isinstance(exc, asyncio.TimeoutError):
        return True

    return False


TOOL_DECLARATIONS = [
    {
        "name": "open_app",
        "description": (
            "Opens any application on the computer. "
            "Use this whenever the user asks to open, launch, or start any app, "
            "website, or program. Always call this tool — never just say you opened it."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Exact name of the application (e.g. 'WhatsApp', 'Chrome', 'Spotify')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "web_search",
        "description": "Searches the web for any information.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Search query"},
                "mode":   {"type": "STRING", "description": "search (default) or compare"},
                "items":  {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Items to compare"},
                "aspect": {"type": "STRING", "description": "price | specs | reviews"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "weather_report",
        "description": "Gives the weather report to user",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "send_message",
        "description": "Sends a text message via WhatsApp, Telegram, or other messaging platform.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver":     {"type": "STRING", "description": "Recipient contact name"},
                "message_text": {"type": "STRING", "description": "The message to send"},
                "platform":     {"type": "STRING", "description": "Platform: WhatsApp, Telegram, etc."}
            },
            "required": ["receiver", "message_text", "platform"]
        }
    },
    {
        "name": "reminder",
        "description": "Sets a timed reminder using Task Scheduler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "date":    {"type": "STRING", "description": "Date in YYYY-MM-DD format"},
                "time":    {"type": "STRING", "description": "Time in HH:MM format (24h)"},
                "message": {"type": "STRING", "description": "Reminder message text"}
            },
            "required": ["date", "time", "message"]
        }
    },
    {
        "name": "youtube_video",
        "description": (
            "Controls YouTube. Use for: playing videos, summarizing a video's content, "
            "getting video info, or showing trending videos."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "play | summarize | get_info | trending (default: play)"},
                "query":  {"type": "STRING", "description": "Search query for play action"},
                "save":   {"type": "BOOLEAN", "description": "Save summary to Notepad (summarize only)"},
                "region": {"type": "STRING", "description": "Country code for trending e.g. TR, US"},
                "url":    {"type": "STRING", "description": "Video URL for get_info action"},
            },
            "required": []
        }
    },
    {
        "name": "screen_process",
        "description": (
            "Captures and analyzes the screen or webcam image. "
            "MUST be called when user asks what is on screen, what you see, "
            "analyze my screen, look at camera, etc. "
            "You have NO visual ability without this tool. "
            "After calling this tool, stay SILENT — the vision module speaks directly."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "angle": {"type": "STRING", "description": "'screen' to capture display, 'camera' for webcam. Default: 'screen'"},
                "text":  {"type": "STRING", "description": "The question or instruction about the captured image"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "computer_settings",
        "description": (
            "Controls the computer: volume, brightness, window management, keyboard shortcuts, "
            "typing text on screen, closing apps, fullscreen, dark mode, WiFi, restart, shutdown, "
            "scrolling, tab management, zoom, screenshots, lock screen, refresh/reload page. "
            "Use for ANY single computer control command. NEVER route to agent_task."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "The action to perform"},
                "description": {"type": "STRING", "description": "Natural language description of what to do"},
                "value":       {"type": "STRING", "description": "Optional value: volume level, text to type, etc."}
            },
            "required": []
        }
    },
    {
        "name": "browser_control",
        "description": (
            "Controls any web browser. Use for: opening websites, searching the web, "
            "clicking elements, filling forms, scrolling, screenshots, navigation, any web-based task. "
            "Always pass the 'browser' parameter when the user specifies a browser (e.g. 'open in Edge', "
            "'use Firefox', 'open Chrome'). Multiple browsers can run simultaneously."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "go_to | search | click | type | scroll | fill_form | smart_click | smart_type | get_text | get_url | press | new_tab | close_tab | screenshot | back | forward | reload | switch | list_browsers | close | close_all"},
                "browser":     {"type": "STRING", "description": "Target browser: chrome | edge | firefox | opera | operagx | brave | vivaldi | safari. Omit to use the currently active browser."},
                "url":         {"type": "STRING", "description": "URL for go_to / new_tab action"},
                "query":       {"type": "STRING", "description": "Search query for search action"},
                "engine":      {"type": "STRING", "description": "Search engine: google | bing | duckduckgo | yandex (default: google)"},
                "selector":    {"type": "STRING", "description": "CSS selector for click/type"},
                "text":        {"type": "STRING", "description": "Text to click or type"},
                "description": {"type": "STRING", "description": "Element description for smart_click/smart_type"},
                "direction":   {"type": "STRING", "description": "up | down for scroll"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount in pixels (default: 500)"},
                "key":         {"type": "STRING", "description": "Key name for press action (e.g. Enter, Escape, F5)"},
                "path":        {"type": "STRING", "description": "Save path for screenshot"},
                "incognito":   {"type": "BOOLEAN", "description": "Open in private/incognito mode"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_controller",
        "description": "Manages files and folders: list, create, delete, move, copy, rename, read, write, find, disk usage.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "list | create_file | create_folder | delete | move | copy | rename | read | write | find | largest | disk_usage | organize_desktop | info"},
                "path":        {"type": "STRING", "description": "File/folder path or shortcut: desktop, downloads, documents, home"},
                "destination": {"type": "STRING", "description": "Destination path for move/copy"},
                "new_name":    {"type": "STRING", "description": "New name for rename"},
                "content":     {"type": "STRING", "description": "Content for create_file/write"},
                "name":        {"type": "STRING", "description": "File name to search for"},
                "extension":   {"type": "STRING", "description": "File extension to search (e.g. .pdf)"},
                "count":       {"type": "INTEGER", "description": "Number of results for largest"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "desktop_control",
        "description": "Controls the desktop: wallpaper, organize, clean, list, stats.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "wallpaper | wallpaper_url | organize | clean | list | stats | task"},
                "path":   {"type": "STRING", "description": "Image path for wallpaper"},
                "url":    {"type": "STRING", "description": "Image URL for wallpaper_url"},
                "mode":   {"type": "STRING", "description": "by_type or by_date for organize"},
                "task":   {"type": "STRING", "description": "Natural language desktop task"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "code_helper",
        "description": "Writes, edits, explains, runs, or builds code files.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "write | edit | explain | run | build | auto (default: auto)"},
                "description": {"type": "STRING", "description": "What the code should do or what change to make"},
                "language":    {"type": "STRING", "description": "Programming language (default: python)"},
                "output_path": {"type": "STRING", "description": "Where to save the file"},
                "file_path":   {"type": "STRING", "description": "Path to existing file for edit/explain/run/build"},
                "code":        {"type": "STRING", "description": "Raw code string for explain"},
                "args":        {"type": "STRING", "description": "CLI arguments for run/build"},
                "timeout":     {"type": "INTEGER", "description": "Execution timeout in seconds (default: 30)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "dev_agent",
        "description": "Builds complete multi-file projects from scratch: plans, writes files, installs deps, opens VSCode, runs and fixes errors.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "description":  {"type": "STRING", "description": "What the project should do"},
                "language":     {"type": "STRING", "description": "Programming language (default: python)"},
                "project_name": {"type": "STRING", "description": "Optional project folder name"},
                "timeout":      {"type": "INTEGER", "description": "Run timeout in seconds (default: 30)"},
            },
            "required": ["description"]
        }
    },
    {
        "name": "agent_task",
        "description": (
            "Executes complex multi-step tasks requiring multiple different tools. "
            "Examples: 'research X and save to file', 'find and organize files'. "
            "DO NOT use for single commands. NEVER use for Steam/Epic — use game_updater."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal":     {"type": "STRING", "description": "Complete description of what to accomplish"},
                "priority": {"type": "STRING", "description": "low | normal | high (default: normal)"}
            },
            "required": ["goal"]
        }
    },
    {
        "name": "computer_control",
        "description": "Direct computer control: type, click, hotkeys, scroll, move mouse, screenshots, find elements on screen.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "type | smart_type | click | double_click | right_click | hotkey | press | scroll | move | copy | paste | screenshot | wait | clear_field | focus_window | screen_find | screen_click | random_data | user_data"},
                "text":        {"type": "STRING", "description": "Text to type or paste"},
                "x":           {"type": "INTEGER", "description": "X coordinate"},
                "y":           {"type": "INTEGER", "description": "Y coordinate"},
                "keys":        {"type": "STRING", "description": "Key combination e.g. 'ctrl+c'"},
                "key":         {"type": "STRING", "description": "Single key e.g. 'enter'"},
                "direction":   {"type": "STRING", "description": "up | down | left | right"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount (default: 3)"},
                "seconds":     {"type": "NUMBER",  "description": "Seconds to wait"},
                "title":       {"type": "STRING",  "description": "Window title for focus_window"},
                "description": {"type": "STRING",  "description": "Element description for screen_find/screen_click"},
                "type":        {"type": "STRING",  "description": "Data type for random_data"},
                "field":       {"type": "STRING",  "description": "Field for user_data: name|email|city"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
                "path":        {"type": "STRING",  "description": "Save path for screenshot"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "game_updater",
        "description": (
            "THE ONLY tool for ANY Steam or Epic Games request. "
            "Use for: installing, downloading, updating games, listing installed games, "
            "checking download status, scheduling updates. "
            "ALWAYS call directly for any Steam/Epic/game request. "
            "NEVER use agent_task, browser_control, or web_search for Steam/Epic."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":    {"type": "STRING",  "description": "update | install | list | download_status | schedule | cancel_schedule | schedule_status (default: update)"},
                "platform":  {"type": "STRING",  "description": "steam | epic | both (default: both)"},
                "game_name": {"type": "STRING",  "description": "Game name (partial match supported)"},
                "app_id":    {"type": "STRING",  "description": "Steam AppID for install (optional)"},
                "hour":      {"type": "INTEGER", "description": "Hour for scheduled update 0-23 (default: 3)"},
                "minute":    {"type": "INTEGER", "description": "Minute for scheduled update 0-59 (default: 0)"},
                "shutdown_when_done": {"type": "BOOLEAN", "description": "Shut down PC when download finishes"},
            },
            "required": []
        }
    },
    {
        "name": "flight_finder",
        "description": "Searches Google Flights and speaks the best options.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "origin":      {"type": "STRING",  "description": "Departure city or airport code"},
                "destination": {"type": "STRING",  "description": "Arrival city or airport code"},
                "date":        {"type": "STRING",  "description": "Departure date (any format)"},
                "return_date": {"type": "STRING",  "description": "Return date for round trips"},
                "passengers":  {"type": "INTEGER", "description": "Number of passengers (default: 1)"},
                "cabin":       {"type": "STRING",  "description": "economy | premium | business | first"},
                "save":        {"type": "BOOLEAN", "description": "Save results to Notepad"},
            },
            "required": ["origin", "destination", "date"]
        }
    },
    {
        "name": "webbridge",
        "description": (
            "Controls the user's REAL browser using Kimi WebBridge. "
            "Use for: navigating to sites, clicking elements, filling forms, "
            "taking screenshots, reading page content (snapshot), scrolling, "
            "and any browser task where the user is already logged in. "
            "Unlike browser_control (Playwright), this uses the user's actual "
            "browser with all their login sessions, cookies, and extensions. "
            "Actions: navigate, snapshot, click, fill, screenshot, evaluate, "
            "save_as_pdf, find_tab, list_tabs, close_tab, close_session, status."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": (
                        "navigate | snapshot | click | fill | screenshot | evaluate | "
                        "save_as_pdf | find_tab | list_tabs | close_tab | close_session | status"
                    )
                },
                "url":      {"type": "STRING", "description": "URL for navigate / find_tab"},
                "selector": {"type": "STRING", "description": "@e ref or CSS selector for click/fill/screenshot"},
                "value":    {"type": "STRING", "description": "Text value for fill action"},
                "code":     {"type": "STRING", "description": "JavaScript code for evaluate action"},
                "format":   {"type": "STRING", "description": "png | jpeg for screenshot"},
                "quality":  {"type": "INTEGER", "description": "JPEG quality 0-100"},
                "newTab":   {"type": "BOOLEAN", "description": "Open in new tab (default: false)"},
                "session":  {"type": "STRING", "description": "Session name for tab grouping"},
                "path":     {"type": "STRING", "description": "File path to save screenshot/PDF"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "shutdown_jarvis",
        "description": (
            "Shuts down the assistant completely. "
            "Call this when the user expresses intent to end the conversation, "
            "close the assistant, say goodbye, or stop Jarvis. "
            "The user can say this in ANY language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        }
    },
    {
    "name": "file_processor",
    "description": (
        "Processes any file that the user has uploaded or dropped onto the interface. "
        "Use this when the user refers to an uploaded file and wants an action on it. "
        "Supports: images (describe/ocr/resize/compress/convert), "
        "PDFs (summarize/extract_text/to_word), "
        "Word docs & text files (summarize/fix/reformat/translate), "
        "CSV/Excel (analyze/stats/filter/sort/convert), "
        "JSON/XML (validate/format/analyze), "
        "code files (explain/review/fix/optimize/run/document/test), "
        "audio (transcribe/trim/convert/info), "
        "video (trim/extract_audio/extract_frame/compress/transcribe/info), "
        "archives (list/extract), "
        "presentations (summarize/extract_text). "
        "ALWAYS call this tool when a file has been uploaded and the user gives a command about it. "
        "If the user's command is ambiguous, pick the most logical action for that file type."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_path": {
                "type": "STRING",
                "description": "Full path to the uploaded file. Leave empty to use the currently uploaded file."
            },
            "action": {
                "type": "STRING",
                "description": (
                    "What to do with the file. Examples by type:\n"
                    "image: describe | ocr | resize | compress | convert | info\n"
                    "pdf: summarize | extract_text | to_word | info\n"
                    "docx/txt: summarize | fix | reformat | translate_hint | word_count | to_bullet\n"
                    "csv/excel: analyze | stats | filter | sort | convert | info\n"
                    "json: validate | format | analyze | to_csv\n"
                    "code: explain | review | fix | optimize | run | document | test\n"
                    "audio: transcribe | trim | convert | info\n"
                    "video: trim | extract_audio | extract_frame | compress | transcribe | info | convert\n"
                    "archive: list | extract\n"
                    "pptx: summarize | extract_text | analyze"
                )
            },
            "instruction": {
                "type": "STRING",
                "description": "Free-form instruction if action doesn't cover it. E.g. 'translate this to Turkish', 'find all email addresses'"
            },
            "format": {
                "type": "STRING",
                "description": "Target format for conversion. E.g. 'mp3', 'pdf', 'csv', 'png'"
            },
            "width":     {"type": "INTEGER", "description": "Target width for image resize"},
            "height":    {"type": "INTEGER", "description": "Target height for image resize"},
            "scale":     {"type": "NUMBER",  "description": "Scale factor for image resize (e.g. 0.5)"},
            "quality":   {"type": "INTEGER", "description": "Quality 1-100 for image/video compress"},
            "start":     {"type": "STRING",  "description": "Start time for trim: seconds or HH:MM:SS"},
            "end":       {"type": "STRING",  "description": "End time for trim: seconds or HH:MM:SS"},
            "timestamp": {"type": "STRING",  "description": "Timestamp for video frame extraction HH:MM:SS"},
            "column":    {"type": "STRING",  "description": "Column name for CSV filter/sort"},
            "value":     {"type": "STRING",  "description": "Filter value for CSV filter"},
            "condition": {"type": "STRING",  "description": "Filter condition: equals|contains|gt|lt"},
            "ascending": {"type": "BOOLEAN", "description": "Sort order for CSV sort (default: true)"},
            "save":      {"type": "BOOLEAN", "description": "Save result to file (default: true)"},
            "destination": {"type": "STRING", "description": "Output folder for archive extract"},
        },
        "required": []
    }
},
    {
        "name": "jarvis_status",
        "description": (
            "Returns real-time information about Jarvis itself. "
            "Use when user asks: what version are you, what is "
            "your status, how many memories do you have, what "
            "did you do today, how long have you been running, "
            "what can you do, are you working properly. "
            "Query types: version, memory, status, activity, "
            "uptime, capabilities."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": (
                        "The type of self-awareness query: "
                        "version | memory | status | activity | "
                        "uptime | capabilities"
                    )
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": (
            "Save an important personal fact about the user to long-term memory. "
            "Call this silently whenever the user reveals something worth remembering: "
            "name, age, city, job, preferences, hobbies, relationships, projects, or future plans. "
            "Do NOT call for: weather, reminders, searches, or one-time commands. "
            "Do NOT announce that you are saving — just call it silently. "
            "Values must be in English regardless of the conversation language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": (
                        "identity — name, age, birthday, city, job, language, nationality | "
                        "preferences — favorite food/color/music/film/game/sport, hobbies | "
                        "projects — active projects, goals, things being built | "
                        "relationships — friends, family, partner, colleagues | "
                        "wishes — future plans, things to buy, travel dreams | "
                        "notes — habits, schedule, anything else worth remembering"
                    )
                },
                "key":   {"type": "STRING", "description": "Short snake_case key (e.g. name, favorite_food, sister_name)"},
                "value": {"type": "STRING", "description": "Concise value in English (e.g. Fatih, pizza, older sister)"},
            },
            "required": ["category", "key", "value"]
        }
    },
]


RECALL_TOOL_DECL = {
    "name": "recall_episodes",
    "description": (
        "Searches past conversation summaries by keyword. "
        "Use when the user asks about previous chats, e.g. "
        "'what did we discuss last week?' or 'do you remember when we fixed X?'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Keyword to search summaries, topics, and tools used"},
            "limit": {"type": "INTEGER", "description": "Max episodes to return (default 3)"},
        },
        "required": [],
    },
}


class JarvisLive:

    def __init__(self, ui: JarvisUI, event_bus=None):
        self.ui             = ui
        self.session        = None
        self.audio_in_queue = None
        self.out_queue      = None
        try:
            self._loop      = asyncio.get_event_loop()
        except RuntimeError:
            self._loop      = None
        self._is_speaking   = False
        self._speaking_lock = threading.Lock()
        self.ui.on_text_command = self._on_text_command
        self._turn_done_event: asyncio.Event | None = None
        self._react_cancel_event: threading.Event | None = None
        self._session_transcript: list[str]    = []
        self._episode_turns:     list[dict]    = []
        self._episode_tools:     list[str]    = []
        self._last_rollover_ts:  float         = 0.0
        self._episode_started_at: datetime | None = None
        self._wake_config = WakeConfig()
        self._is_awake = False
        self._silence_timer: asyncio.TimerHandle | None = None
        self._hotword: "HotwordDetector | None" = None
        self.ui.on_wake_request = self._on_wake_word_detected
        self._dashboard_bus = event_bus
        self._health_daemon = SystemHealthDaemon(speak=self.speak, write_log=self.ui.write_log, event_bus=event_bus)
        self._conv_state = ConversationState()
        self._proactive_queue = ProactiveQueue()
        self._start_webbridge()

        if self._dashboard_bus is not None:
            _original_write_log = self.ui.write_log

            def _patched_write_log(text: str):
                _original_write_log(text)
                try:
                    if text.startswith("You: "):
                        role, content = "user", text[5:]
                    elif text.startswith("Jarvis: "):
                        role, content = "jarvis", text[8:]
                    else:
                        role, content = "system", text
                    self._dashboard_bus.publish({
                        "type": "transcript",
                        "role": role,
                        "text": content,
                        "ts": datetime.now().isoformat()
                    })
                except Exception:
                    pass

            self.ui.write_log = _patched_write_log

        def _atexit_handler():
            try:
                if not self._episode_turns and not self._episode_tools:
                    return
                if not (self._loop and self._loop.is_running()):
                    return
                asyncio.run_coroutine_threadsafe(
                    self._finalize_session_episode("atexit"), self._loop
                )
            except Exception:
                pass
        atexit.register(_atexit_handler)

    def _start_webbridge(self) -> None:
        import subprocess, urllib.request
        bridge_bin = os.path.expanduser(
            "~/.kimi-webbridge/bin/kimi-webbridge"
        )
        if not os.path.exists(bridge_bin):
            return
        try:
            urllib.request.urlopen(
                "http://127.0.0.1:10086", timeout=1
            )
            log.info("webbridge_already_running")
            return
        except Exception:
            pass
        try:
            subprocess.Popen(
                [bridge_bin, "start"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log.info("webbridge_started")
        except Exception as e:
            log.warning("webbridge_start_failed", error=str(e))

    def _stop_webbridge(self) -> None:
        import subprocess
        bridge_bin = os.path.expanduser(
            "~/.kimi-webbridge/bin/kimi-webbridge"
        )
        if not os.path.exists(bridge_bin):
            return
        try:
            subprocess.run(
                [bridge_bin, "stop"],
                timeout=5,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log.info("webbridge_stopped")
        except Exception as e:
            log.warning("webbridge_stop_failed", error=str(e))

    def _on_text_command(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
            self._publish_state("SPEAKING")
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")
            self._publish_state("LISTENING")

    def speak(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.speak(f"Sir, {tool_name} encountered an error. {short}")

    def _on_wake_word_detected(self):
        if not self._is_awake:
            self._is_awake = True
            self.ui.write_log("SYS: Wake word detected.")

    def _go_to_sleep(self):
        self._is_awake = False
        self.ui.write_log("SYS: Going to sleep. Say 'Hey Jarvis' to wake.")
        self.ui.set_state("SLEEPING")
        self._publish_state("SLEEPING")

    def _publish_state(self, state: str):
        if self._dashboard_bus is not None:
            try:
                self._dashboard_bus.publish({
                    "type": "state",
                    "state": state
                })
            except Exception:
                pass

    async def _finalize_session_episode(self, reason: str = ""):
        from memory.memory_manager import summarize_session, get_episodic_store
        log.info("episodic_finalize", turns=len(self._episode_turns), tools=list(self._episode_tools))
        try:
            if not self._episode_turns and not self._episode_tools and not self._session_transcript:
                return
            lines = [f"{t['role'].title()}: {t['text']}" for t in self._episode_turns if t.get("text")]
            if not lines:
                lines = list(self._session_transcript)
            goal = ""
            for turn in self._episode_turns:
                if turn.get("role") == "user" and turn.get("text"):
                    goal = turn["text"][:200]
                    break
            api_key = GEMINI_API_KEY
            episode = await summarize_session(
                lines, api_key,
                tools_used=list(self._episode_tools),
                goal=goal,
            )
            if reason:
                episode["closed_via"] = reason
            get_episodic_store().save_episode(episode)
            self._session_transcript = []
            self._episode_turns      = []
            self._episode_tools      = []
        except Exception as e:
            log.warning("episodic_save_failed", reason=reason, error=str(e))

    async def _episode_rollover_task(self):
        while True:
            try:
                await asyncio.sleep(60)
                if len(self._episode_turns) >= 20:
                    now = time.time()
                    if now - self._last_rollover_ts >= 1800:
                        await self._finalize_session_episode("rollover")
                        self._last_rollover_ts = now
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("episodic_rollover_error", error=str(e))

    def _build_config(self) -> types.LiveConnectConfig:
        prune_episodes()

        memory     = load_memory()
        mem_str    = format_memory_for_prompt(memory)
        n          = int(os.getenv("EPISODIC_RECENT_COUNT", "5"))
        ep_str     = format_episodes_for_prompt(load_recent_episodes(n))
        sys_prompt = _load_system_prompt()

        now      = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )

        parts = [time_ctx]
        ctx = gather_live_context()
        if ctx:
            parts.insert(0, ctx)
        if mem_str:
            parts.append(mem_str)
        if ep_str:
            parts.append(ep_str)
        parts.append(sys_prompt)

        tool_list = TOOL_DECLARATIONS + ([RECALL_TOOL_DECL] if ENABLE_RECALL_TOOL else [])

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": tool_list}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
        )

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})

        self._conv_state.set_active(True)

        log.info("tool_execute", tool=name, args=args)
        self.ui.set_state("THINKING")
        self._publish_state("THINKING")

        if name == "save_memory":
            category = args.get("category", "notes")
            key      = args.get("key", "")
            value    = args.get("value", "")
            if key and value:
                update_memory({category: {key: {"value": value}}})
                log.info("memory_save", category=category, key=key)
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
                self._publish_state("LISTENING")
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": "ok", "silent": True}
            )

        loop   = asyncio.get_event_loop()
        result = "Done."
        _cfg = RetryConfig()
        _retrying = make_retry_decorator(_cfg)

        try:
            if name == "open_app":
                r = await loop.run_in_executor(None, lambda: open_app(parameters=args, response=None, player=self.ui))
                result = r or f"Opened {args.get('app_name')}."

            elif name == "weather_report":
                r = await loop.run_in_executor(None, lambda: _retrying(weather_action)(parameters=args, player=self.ui))
                result = r or "Weather delivered."

            elif name == "browser_control":
                try:
                    r = await loop.run_in_executor(None, lambda: _retrying(browser_control)(parameters=args, player=self.ui))
                except Exception as e:
                    action = args.get("action", "")
                    query = args.get("query") or args.get("url", "")
                    if action == "search" and query:
                        try:
                            from actions.web_search import web_search
                            r = await loop.run_in_executor(None, lambda: web_search(parameters={"query": query, "mode": "search"}, player=self.ui))
                            log.info("browser_control_degraded")
                        except Exception:
                            raise e
                    else:
                        raise
                result = r or "Done."

            elif name == "file_controller":
                r = await loop.run_in_executor(None, lambda: file_controller(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "send_message":
                r = await loop.run_in_executor(None, lambda: send_message(parameters=args, response=None, player=self.ui, session_memory=None))
                result = r or f"Message sent to {args.get('receiver')}."

            elif name == "reminder":
                r = await loop.run_in_executor(None, lambda: reminder(parameters=args, response=None, player=self.ui))
                result = r or "Reminder set."

            elif name == "youtube_video":
                r = await loop.run_in_executor(None, lambda: _retrying(youtube_video)(parameters=args, response=None, player=self.ui))
                result = r or "Done."

            elif name == "screen_process":
                threading.Thread(
                    target=screen_process,
                    kwargs={"parameters": args, "response": None,
                            "player": self.ui, "session_memory": None},
                    daemon=True
                ).start()
                result = "Vision module activated. Stay completely silent — vision module will speak directly."

            elif name == "computer_settings":
                r = await loop.run_in_executor(None, lambda: computer_settings(parameters=args, response=None, player=self.ui))
                result = r or "Done."

            elif name == "desktop_control":
                r = await loop.run_in_executor(None, lambda: desktop_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "code_helper":
                r = await loop.run_in_executor(None, lambda: code_helper(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "dev_agent":
                r = await loop.run_in_executor(None, lambda: dev_agent(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "agent_task":
                from agent.react_loop import (
                    ReactAgentLoop,
                    build_tool_registry,
                )
                from agent.config import default_planner_config
                from agent.planner_layer import PlannerLayer

                cancel_event = threading.Event()
                self._react_cancel_event = cancel_event
                registry = build_tool_registry(TOOL_DECLARATIONS)
                loop_runner = ReactAgentLoop(registry=registry, event_bus=self._dashboard_bus)

                goal_text = args.get("goal", "")
                planner_cfg = default_planner_config()
                planner = PlannerLayer(planner_cfg)
                plan = await planner.announce(
                    goal=goal_text,
                    speak=self.speak,
                    write_log=self.ui.write_log,
                    cancel_flag=self._react_cancel_event,
                )

                try:
                    react_result = await loop_runner.run(
                        goal=goal_text,
                        executor=self._react_tool_executor,
                        cancel_flag=cancel_event,
                        plan_context=plan,
                    )
                except TypeError:
                    react_result = await loop_runner.run(
                        goal=goal_text,
                        executor=self._react_tool_executor,
                        cancel_flag=cancel_event,
                    )

                self._react_cancel_event = None
                status_line = (
                    f"ReAct {react_result.status} "
                    f"in {react_result.iterations} step(s)"
                )
                log.info("react_status", status=status_line)
                self.ui.write_log(status_line)
                result = react_result.answer or "Task complete."

            elif name == "web_search":
                r = await loop.run_in_executor(None, lambda: _retrying(web_search_action)(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "file_processor":
                if not args.get("file_path") and self.ui.current_file:
                    args["file_path"] = self.ui.current_file
                r = await loop.run_in_executor(
                    None,
                    lambda: file_processor(parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Done."

            elif name == "computer_control":
                r = await loop.run_in_executor(None, lambda: computer_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "game_updater":
                r = await loop.run_in_executor(None, lambda: game_updater(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "jarvis_status":
                r = await loop.run_in_executor(None, lambda: jarvis_status(parameters=args, player=self.ui))
                result = r or "All systems nominal, sir."

            elif name == "flight_finder":
                r = await loop.run_in_executor(None, lambda: _retrying(flight_finder)(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "webbridge":
                r = await loop.run_in_executor(None, lambda: _retrying(webbridge_tool)(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "recall_episodes":
                results = search_episodes(
                    args.get("query", ""),
                    int(args.get("limit", 3)),
                )
                result = format_episodes_for_prompt(results) or "No matching episodes found."

            elif name == "shutdown_jarvis":
                self.ui.write_log("SYS: Shutdown requested.")
                self.speak("Goodbye, sir.")
                def _shutdown():
                    import time, os
                    try:
                        if self._loop and self._loop.is_running():
                            fut = asyncio.run_coroutine_threadsafe(
                                self._finalize_session_episode("shutdown"),
                                self._loop,
                            )
                            try:
                                fut.result(timeout=5)
                            except Exception as e:
                                log.warning("episodic_shutdown_error", error=str(e))
                    finally:
                        self._stop_webbridge()
                        time.sleep(1)
                        os._exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()

            else:
                result = f"Unknown tool: {name}"

        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            log.error("tool_execution_failed", tool=name, error=str(e), exc_info=True)
            self.speak_error(name, e)

        if not self.ui.muted:
            self.ui.set_state("LISTENING")
            self._publish_state("LISTENING")

        if name and name not in self._episode_tools:
            self._episode_tools.append(name)

        self._conv_state.set_active(False)

        log.info("tool_result", tool=name, result=str(result)[:80])
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _react_tool_executor(self, tool_name: str, parameters: dict) -> str:
        fc = types.FunctionCall(
            id=f"react-{int(time.time() * 1000)}",
            name=tool_name,
            args=parameters or {},
        )
        fr = await self._execute_tool(fc)
        response = fr.response if fr is not None else {}
        if not isinstance(response, dict):
            return str(response)
        return str(response.get("result", ""))

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    async def _listen_audio(self):
        log.info("mic_started")
        loop = asyncio.get_event_loop()

        try:
            sd = _get_sounddevice()
        except Exception as e:
            msg = f"SYS: Microphone audio unavailable: {e}"
            log.error("mic_unavailable", msg=msg)
            self.ui.write_log(msg)
            while True:
                await asyncio.sleep(3600)

        def callback(indata, frames, time_info, status):
            with self._speaking_lock:
                jarvis_speaking = self._is_speaking
            if self._wake_config.enabled and not self._is_awake:
                return
            if not jarvis_speaking and not self.ui.muted:
                data = indata.tobytes()
                def _put():
                    try:
                        self.out_queue.put_nowait({"data": data, "mime_type": "audio/pcm"})
                    except asyncio.QueueFull:
                        pass
                loop.call_soon_threadsafe(_put)
            self.ui.audio_analyzer.feed(indata.copy())

        try:
            with sd.InputStream(
                samplerate=SEND_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=callback,
            ):
                log.info("mic_stream_open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            log.error("mic_error", error=str(e))
            raise

    async def _receive_audio(self):
        log.info("recv_started")
        out_buf, in_buf = [], []

        try:
            while True:
                async for response in self.session.receive():

                    if response.data:
                        if self._turn_done_event and self._turn_done_event.is_set():
                            self._turn_done_event.clear()
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.output_transcription and sc.output_transcription.text:
                            txt = _clean_transcript(sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = _clean_transcript(sc.input_transcription.text)
                            if txt:
                                in_buf.append(txt)

                        if sc.turn_complete:
                            self._conv_state.set_active(False)
                            if self._turn_done_event:
                                self._turn_done_event.set()
                            if hasattr(self, '_proactive_queue') and not self._proactive_queue.empty():
                                try:
                                    msg = self._proactive_queue.get_nowait()
                                    await asyncio.sleep(1.5)
                                    self.speak(msg)
                                    self.ui.write_log(f"[PROACTIVE] {msg}")
                                except Exception:
                                    pass

                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.ui.write_log(f"You: {full_in}")
                                self._session_transcript.append(f"You: {full_in}")
                                self._episode_turns.append({
                                    "role": "user", "text": full_in,
                                    "ts":   datetime.now().isoformat(timespec="seconds"),
                                })
                                if len(self._episode_turns) > 200:
                                    self._episode_turns = self._episode_turns[-200:]
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"Jarvis: {full_out}")
                                self._session_transcript.append(f"Jarvis: {full_out}")
                                self._episode_turns.append({
                                    "role": "assistant", "text": full_out,
                                    "ts":   datetime.now().isoformat(timespec="seconds"),
                                })
                                if len(self._episode_turns) > 200:
                                    self._episode_turns = self._episode_turns[-200:]
                            out_buf = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            log.info("tool_call_received", tool=fc.name)
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(
                            function_responses=fn_responses
                        )
        except Exception as e:
            if _should_reconnect(e):
                log.warning("recv_stream_ended", error=str(e))
                raise ReconnectRequested from None
            log.error("recv_error", error=str(e), exc_info=True)
            raise

    async def _play_audio(self):
        log.info("play_started")

        try:
            sd = _get_sounddevice()
            stream = sd.RawOutputStream(
                samplerate=RECEIVE_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
            )
            stream.start()
        except Exception as e:
            msg = f"SYS: Speaker audio unavailable: {e}"
            log.error("speaker_unavailable", msg=msg)
            self.ui.write_log(msg)
            while True:
                await self.audio_in_queue.get()

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        self.audio_in_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    if (
                        self._turn_done_event
                        and self._turn_done_event.is_set()
                        and self.audio_in_queue.empty()
                    ):
                        self.set_speaking(False)
                        self._turn_done_event.clear()
                    continue
                self.set_speaking(True)
                import numpy as np
                self.ui.audio_analyzer.feed(np.frombuffer(chunk, dtype=np.int16))
                await asyncio.to_thread(stream.write, chunk)
        except Exception as e:
            log.error("play_error", error=str(e))
            raise
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()

    async def run(self):
        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options={"api_version": "v1beta"}
        )

        if self._wake_config.enabled:
            from core.hotword import HotwordDetector
            self._hotword = HotwordDetector(
                threshold=self._wake_config.threshold,
            )
            self._hotword.start(self._on_wake_word_detected)
            self.ui.write_log("SYS: Say 'Hey Jarvis' to begin.")

        while True:
            if self._wake_config.enabled and not self._is_awake:
                self.set_speaking(False)
                self.ui.set_state("SLEEPING")
                self._publish_state("SLEEPING")
                log.info("waiting_for_wake_word")
                while not self._is_awake:
                    await asyncio.sleep(0.2)
                log.info("connecting")
            else:
                log.info("connecting")
            self.ui.set_state("THINKING")
            self._publish_state("THINKING")

            try:
                self.ui.set_state("THINKING")
                self._publish_state("THINKING")
                config = self._build_config()

                try:
                    async with (
                        client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
                        asyncio.TaskGroup() as tg,
                    ):
                        self.session        = session
                        self._loop          = asyncio.get_event_loop()
                        self.audio_in_queue = asyncio.Queue()
                        self.out_queue      = asyncio.Queue(maxsize=10)
                        self._turn_done_event = asyncio.Event()
                        if self._episode_started_at is None:
                            self._episode_started_at = datetime.now()

                        log.info("connected")
                        self.ui.set_state("LISTENING")
                        self._publish_state("LISTENING")
                        self.ui.write_log("SYS: JARVIS online.")
                        if self._silence_timer:
                            self._silence_timer.cancel()
                        self._silence_timer = self._loop.call_later(
                            self._wake_config.silence_timeout,
                            self._go_to_sleep,
                        )

                        tg.create_task(self._send_realtime())
                        tg.create_task(self._listen_audio())
                        tg.create_task(self._receive_audio())
                        tg.create_task(self._play_audio())
                        tg.create_task(self._episode_rollover_task())
                        tg.create_task(self._health_daemon.run())
                        tg.create_task(
                            ProactiveEngine(
                                conv_state=self._conv_state,
                                queue=self._proactive_queue,
                                health_daemon=self._health_daemon,
                                speak_fn=self.speak,
                                write_log_fn=self.ui.write_log,
                            ).run()
                        )
                except* ReconnectRequested:
                    pass

            except Exception as e:
                log.warning("session_error", error=str(e), exc_info=True)

            self.set_speaking(False)
            self._is_awake = False
            self.ui.set_state("THINKING")
            self._publish_state("THINKING")
            if len(self._session_transcript) > 5 or len(self._episode_turns) >= 20:
                asyncio.create_task(self._finalize_session_episode("reconnect"))
            log.info("reconnecting")
            await asyncio.sleep(3)


def main():
    from core.logger import setup_logging

    ui = JarvisUI("face.png")

    event_bus = DashboardEventBus() if DashboardEventBus is not None else None
    setup_logging(event_bus=event_bus if DashboardEventBus is not None else None)
    if event_bus is not None and start_dashboard is not None:
        start_dashboard(event_bus)

    def runner():
        ui.wait_for_api_key()
        jarvis = JarvisLive(ui, event_bus=event_bus)
        try:
            asyncio.run(jarvis.run())
        except KeyboardInterrupt:
            log.info("shutting_down")
        finally:
            if hasattr(jarvis, '_hotword') and jarvis._hotword and jarvis._hotword.is_running():
                jarvis._hotword.stop()
            sys.exit(0)

    threading.Thread(target=runner, daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
