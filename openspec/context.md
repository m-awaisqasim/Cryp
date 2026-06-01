# Cryp — Project Context for AI Agents

> This file is the single source of truth about the Cryp project.
> Every AI agent working on this codebase must read this file before
> proposing, planning, or implementing any change.

---

## 1. Project Identity

| Field            | Value                                              |
| ---------------- | -------------------------------------------------- |
| **Project Name** | Cryp (V2)                                          |
| **Type**         | Desktop AI Assistant (JARVIS-style)                |
| **Version**      | V2 — codename XXXIX                               |
| **Author**       | Awais (m-awaisqasim)                               |
| **Goal**         | Level up into a true JARVIS-like assistant         |
| **License**      | Creative Commons BY-NC 4.0                        |
| **OS**           | Ubuntu 26.04 (primary), cross-platform target: Windows 10/11, macOS, Linux |
| **Python**       | 3.11+                                              |
| **AI Backend**   | Google Gemini Live API (gemini-2.5-flash-native-audio-preview) |

---

## 2. Repository Structure

```
Cryp/
├── main.py                  # CORE — entry point, JarvisLive class, full session loop
├── ui.py                    # JarvisUI — Tkinter desktop GUI
├── setup.py                 # Package setup
├── requirements.txt         # Python dependencies
├── run.txt                  # Run instructions
│
├── core/
│   └── prompt.txt           # System prompt — Jarvis personality and instructions
│
├── config/
│   └── api_keys.json        # {"gemini_api_key": "..."}
│
├── memory/
│   └── memory_manager.py    # load_memory(), update_memory(), format_memory_for_prompt()
│
├── actions/                 # One file per tool — all tool implementations
│   ├── file_processor.py
│   ├── flight_finder.py
│   ├── open_app.py
│   ├── weather_report.py
│   ├── send_message.py
│   ├── reminder.py
│   ├── computer_settings.py
│   ├── screen_processor.py
│   ├── youtube_video.py
│   ├── desktop.py
│   ├── browser_control.py
│   ├── file_controller.py
│   ├── code_helper.py
│   ├── dev_agent.py
│   ├── web_search.py
│   ├── computer_control.py
│   └── game_updater.py
│
├── agent/
│   └── task_queue.py        # Priority task queue for agent_task tool
│
├── Context/                 # Contextual data files
├── tests/                   # Playwright test suite
│
├── openspec/                # SDD layer — specs for every planned feature
│   └── context.md           # THIS FILE
│
└── assets/
    ├── logo.png
    ├── preferred_UI.png
    └── Later_UI_intgeration.png
```

---

## 3. Core Architecture

### 3.1 Entry Point — `main.py`

The entire assistant runs from a single `JarvisLive` class that manages 4 concurrent async tasks:

```
JarvisLive
├── _listen_audio()     → Mic capture via sounddevice (16kHz PCM) → out_queue
├── _send_realtime()    → Pumps out_queue frames into Gemini live session
├── _receive_audio()    → Receives audio + transcripts + tool_calls from Gemini
└── _play_audio()       → Plays AI voice response via sounddevice (24kHz)
```

**Critical constants:**
```python
LIVE_MODEL        = "models/gemini-2.5-flash-native-audio-preview-12-2025"
SEND_SAMPLE_RATE  = 16000   # mic input
RECEIVE_SAMPLE_RATE = 24000 # speaker output
CHANNELS          = 1
CHUNK_SIZE        = 1024
```

### 3.2 Session Configuration — `_build_config()`

Called once per session. Dynamically builds `types.LiveConnectConfig` by:
1. Injecting current date/time string
2. Loading and formatting persistent memory via `format_memory_for_prompt()`
3. Loading `core/prompt.txt` as system instruction
4. Declaring all 20 tools in `TOOL_DECLARATIONS`
5. Setting voice to "Charon"
6. Enabling input + output audio transcription
7. Enabling `SessionResumptionConfig`

### 3.3 Tool Dispatch — `_execute_tool(fc)`

All tool calls flow through `_execute_tool()`. Pattern:
```python
result = await loop.run_in_executor(None, lambda: tool_function(parameters=args, player=self.ui))
```

Thread-safe: tools run in a thread pool executor. UI state is set to "THINKING" before and "LISTENING" after.

### 3.4 Reconnect Logic

Auto-reconnects on:
- `ConnectionClosedError` (WebSocket drop)
- `genai_errors.APIError` with status_code=1011
- "deadline expired" in error message
- `asyncio.TimeoutError`

Reconnect delay: 3 seconds.

---

## 4. Tool Registry (20 Tools)

| Tool Name           | File                         | Description                                    |
| ------------------- | ---------------------------- | ---------------------------------------------- |
| `open_app`          | `actions/open_app.py`        | Launch any application by name                 |
| `web_search`        | `actions/web_search.py`      | Web search with compare/search modes           |
| `weather_report`    | `actions/weather_report.py`  | Weather by city                                |
| `send_message`      | `actions/send_message.py`    | WhatsApp/Telegram messaging                    |
| `reminder`          | `actions/reminder.py`        | Task Scheduler reminders                       |
| `youtube_video`     | `actions/youtube_video.py`   | Play, summarize, trending videos               |
| `screen_process`    | `actions/screen_processor.py`| Screenshot + webcam vision (daemon thread)     |
| `computer_settings` | `actions/computer_settings.py`| Volume, brightness, WiFi, shutdown, etc.       |
| `browser_control`   | `actions/browser_control.py` | Full Playwright browser automation             |
| `file_controller`   | `actions/file_controller.py` | File/folder CRUD, search, disk usage           |
| `desktop_control`   | `actions/desktop.py`         | Wallpaper, organize, clean desktop             |
| `code_helper`       | `actions/code_helper.py`     | Write/edit/explain/run code files              |
| `dev_agent`         | `actions/dev_agent.py`       | Build complete multi-file projects             |
| `agent_task`        | `agent/task_queue.py`        | Multi-step task queue (NEEDS REACT UPGRADE)    |
| `computer_control`  | `actions/computer_control.py`| Direct mouse/keyboard/pyautogui control        |
| `game_updater`      | `actions/game_updater.py`    | Steam/Epic Games install, update, schedule     |
| `flight_finder`     | `actions/flight_finder.py`   | Google Flights search via Playwright           |
| `file_processor`    | `actions/file_processor.py`  | Analyze PDFs, images, audio, video, CSV, code  |
| `save_memory`       | `memory/memory_manager.py`   | Silently persist user facts (no announcement)  |
| `shutdown_jarvis`   | inline in `main.py`          | Graceful exit via `os._exit(0)`                |

---

## 5. Memory System

**Current implementation** (`memory/memory_manager.py`):
- Flat key-value store persisted to disk
- Categories: `identity`, `preferences`, `projects`, `relationships`, `wishes`, `notes`
- Injected into every session via `format_memory_for_prompt()`
- Written silently via `save_memory` tool (never announced to user)
- Values stored in English regardless of conversation language

**Planned upgrade** (Phase 1 roadmap):
- Add episodic memory (conversation summaries)
- Add semantic layer with vector search (chromadb or faiss)
- Add procedural memory ("always open Chrome, not Edge")

---

## 6. UI System

**Current**: Tkinter desktop GUI (`JarvisUI` in `ui.py`)
- States: LISTENING / THINKING / SPEAKING
- `ui.write_log(text)` for transcript display
- `ui.set_state(state)` to control visual state
- `ui.muted` boolean to suppress mic input
- `ui.current_file` for drag-and-drop file uploads
- `ui.on_text_command` callback for typed input

**Planned upgrade** (Phase 3 roadmap):
- Replace with PyQt6 HUD (frameless, transparent, pulse animation)
- Floating always-on-top ambient presence mode

---

## 7. Key Patterns and Conventions

### Tool Function Signature
All action files follow this pattern:
```python
def tool_name(parameters: dict, player: JarvisUI, **kwargs) -> str:
    # implementation
    return "Result description"
```

### Adding a New Tool
1. Create `actions/new_tool.py` with the function
2. Import it in `main.py`
3. Add declaration to `TOOL_DECLARATIONS` list in `main.py`
4. Add dispatch branch in `_execute_tool()` in `main.py`

### State Management
- `self._is_speaking` + `threading.Lock` = echo cancel
- `self.ui.muted` = user-controlled mic mute
- `asyncio.Event` (`_turn_done_event`) = coordinates audio playback end

### Error Handling Convention
```python
except Exception as e:
    result = f"Tool '{name}' failed: {e}"
    traceback.print_exc()
    self.speak_error(name, e)  # announces error to user via voice
```

---

## 8. Development Roadmap

### Phase 1 — The Brain (Current Priority)
- [ ] **ReAct agent loop** — replace `agent_task` with Reason→Act→Observe loop in `agent/react_agent.py`
- [ ] **Episodic memory** — add conversation summaries + vector search to `memory/`
- [ ] **Planner layer** — Jarvis announces plan before executing multi-step tasks

### Phase 2 — Always-On Presence
- [ ] **Hotword detection** — `openWakeWord` so mic only activates on "Hey Jarvis"
- [ ] **Background daemon** — `core/daemon.py` monitoring battery, calendar, system events

### Phase 3 — The Interface
- [ ] **PyQt6 HUD** — frameless transparent window with waveform visualizer
- [ ] **Web dashboard** — FastAPI + frontend at localhost:7070

### Phase 4 — Intelligence Depth
- [ ] **Deep system prompt rewrite** — personality, situational awareness rules
- [ ] **Live context injection** — active window title, clipboard, battery into session config
- [ ] **Proactive suggestions** — Jarvis notices patterns and offers help

### Phase 5 — Polish & Robustness
- [ ] **Structured logging** — replace print() with structlog
- [ ] **Silent retry logic** — transient failures retry without speaking errors
- [ ] **Self-awareness commands** — version, status, memory stats

---

## 9. Dependencies

**Runtime (requirements.txt)**:
- `google-genai` — Gemini Live API client
- `sounddevice` — audio I/O
- `websockets` — WebSocket connection management
- `playwright` — browser automation (Chromium)
- `pyautogui` — computer_control tool
- `python-dotenv` — optional .env loading

**Dev tools**:
- Node.js 20.19+ + OpenSpec (`@fission-ai/openspec`) — SDD framework
- pytest / Playwright test suite in `tests/`

---

## 10. Rules Every AI Agent Must Follow

1. **Never rewrite `main.py` wholesale** — it is 977 lines of carefully structured async code. Make surgical changes only.
2. **Always follow the tool function signature** — `(parameters: dict, player: JarvisUI, **kwargs) -> str`
3. **New tools require 3 changes**: new file in `actions/`, entry in `TOOL_DECLARATIONS`, branch in `_execute_tool()`
4. **`save_memory` is always silent** — never add print/log/speak calls inside it
5. **Threading discipline** — tools that need UI interaction must use `threading.Thread(daemon=True)` like `screen_process`
6. **`loop.run_in_executor`** — all synchronous tool calls must be wrapped in executor to avoid blocking the async loop
7. **State resets** — every tool branch must call `self.ui.set_state("LISTENING")` on exit (already handled by `_execute_tool` finally block — don't add duplicate calls)
8. **Ubuntu 26.04 target** — Playwright browser download is unsupported on this host; use installed system browsers
9. **No hardcoded API keys** — always read from `config/api_keys.json`
10. **Keep `core/prompt.txt` as the only personality source** — don't embed personality in code

---

## 11. File Change Map

When working on a feature, here are the files typically involved:

| Feature Area           | Files to Touch                                                  |
| ---------------------- | --------------------------------------------------------------- |
| New tool               | `actions/new_tool.py`, `main.py` (2 places)                    |
| Memory upgrade         | `memory/memory_manager.py`, `main.py` (_build_config)          |
| Agent / planning       | `agent/`, `main.py` (_execute_tool agent_task branch)          |
| UI changes             | `ui.py` only                                                    |
| Personality changes    | `core/prompt.txt` only                                         |
| Session config         | `main.py` (_build_config method only)                          |
| New dependency         | `requirements.txt` + import in relevant file                   |
| Voice / audio          | `main.py` (constants + _listen_audio / _play_audio)            |