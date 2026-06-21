# Cryp — Project Context for AI Agents

> This file is the single source of truth about the Cryp project.
> Every AI agent working on this codebase must read this file before
> proposing, planning, or implementing any change.

---

## 1. Project Identity

| Field            | Value                                              |
| ---------------- | -------------------------------------------------- |
| **Project Name** | Cryp (V2)                                          |
| **Type**         | Desktop AI Assistant (CRYP-style)                |
| **Version**      | V2 — codename V2                                   |
| **Author**       | Awais (m-awaisqasim)                               |
| **Goal**         | Level up into a true CRYP-like assistant         |
| **License**      | Creative Commons BY-NC 4.0                         |
| **OS**           | Ubuntu 26.04 (primary), cross-platform target: Windows 10/11, macOS, Linux |
| **Python**       | 3.11+                                              |
| **AI Backend**   | Google Gemini Live API (gemini-2.5-flash-native-audio-preview) |

---

## 2. Repository Structure

```
Cryp/
├── main.py                  # CORE — entry point, CrypLive class, full session loop
├── ui_web.py                # WebCrypUI — WebSocket bridge (drop-in for PyQt6 UI)
├── setup.py                 # Package setup
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .env                     # Local secrets & config (gitignored)
│
├── core/
│   ├── prompt.txt           # System prompt — Cryp personality and instructions
│   ├── context_collector.py # gather_live_context(), gather_proactive_context()
│   ├── hotword.py           # HotwordDetector via openWakeWord
│   ├── wake_config.py       # WakeConfig dataclass
│   └── daemon.py            # SystemHealthDaemon, get_health_snapshot()
│
├── proactive/
│   ├── __init__.py
│   ├── engine.py            # ProactiveEngine, 7th async TaskGroup task
│   ├── briefing.py          # Daily briefing generation + date persistence
│   ├── patterns.py          # Time/frequency pattern detection
│   ├── anomalies.py         # 2σ CPU/RAM/app anomaly detection
│   ├── conversation_state.py # Thread-safe conversation state tracker
│   └── queue.py             # Async proactive message queue
│
├── dashboard/
│   ├── __init__.py
│   ├── event_bus.py         # DashboardEventBus pub-sub per-subscriber
│   ├── server.py            # FastAPI + WebSocket at localhost:7070
│   └── frontend/            # React 18 + Vite + Tailwind SPA
│       ├── src/             # Components (OrbHUD, MetricBar, panels), hooks, styles
│       └── dist/            # Built production assets (gitignored)
│
├── config/
│   ├── settings.py          # Central config loader (reads .env)
│   └── proactive_rules.json # 4 default suggestion rules
│
├── memory/
│   ├── memory_manager.py    # load_memory(), update_memory(), format_memory_for_prompt()
│   └── last_briefing_date.txt # Tracks daily briefing (gitignored)
│
├── agent/
│   ├── task_queue.py        # Priority task queue for agent_task tool
│   ├── react_loop.py        # ReactAgentLoop, ReAct reasoning loop
│   ├── planner_layer.py     # PlannerLayer, announces plan before ReAct
│   ├── config.py            # ReactConfig + PlannerConfig dataclasses
│   └── executor.py          # AgentExecutor shell (deprecated)
│
├── actions/                 # One file per tool — all tool implementations
│   ├── webbridge.py         # Kimi WebBridge browser control tool
│   ├── flight_finder.py
│   ├── open_app.py
│   ├── weather_report.py
│   ├── send_message.py
│   ├── reminder.py
│   ├── computer_settings.py
│   ├── screen_processor.py
│   ├── desktop.py
│   ├── browser_control.py
│   ├── file_controller.py
│   ├── web_search.py
│   ├── computer_control.py
│   ├── game_updater.py
│   ├── cryp_status.py
│   │
│   ├── student/             # Phase 8 — Student Intelligence tools
│   │   ├── assignment_tracker.py
│   │   ├── deadline_guardian.py
│   │   ├── code_helper.py
│   │   ├── dev_agent.py
│   │   ├── file_processor.py
│   │   ├── youtube_video.py
│   │   ├── focus_mode.py
│   │   └── exam_prep_coach.py
│   │
│   ├── trading/             # Phase 9 — Trading Intelligence tools
│   │   ├── __init__.py
│   │   ├── market_data.py         # Shared CoinGecko + F&G fetchers with cache
│   │   ├── market_brief.py        # BTC/ETH price snapshot
│   │   ├── sentiment_tracker.py    # Fear & Greed Index with trend
│   │   ├── trade_journal.py       # Manual trade logging + PnL tracking
│   │   ├── news_filter.py         # RSS → Gemini-filtered crypto news
│   │   └── price_anomaly.py       # Proactive 3%/6% price move detection
│   │
│   └── scripts/
│       ├── install.sh
│       └── uninstall.sh
│
├── tests/                   # Test suite
│   ├── test_react_loop.py       # 43 tests
│   ├── test_episodic_memory.py  # 30 tests
│   ├── test_planner_layer.py    # tests
│   ├── test_hotword.py          # 10 tests
│   ├── test_daemon.py           # 23 tests
│   ├── test_dashboard.py        # tests
│   ├── test_context_collector.py # tests
│   ├── test_proactive.py        # 28 tests
│   └── Total: 186 tests passing
│
├── UI testing/              # Design assets & screenshots
├── Context/                 # Contextual data files
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

The entire assistant runs from a single `CrypLive` class that manages 4 concurrent async tasks:

```
CrypLive
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

## 4. Tool Registry (29 Tools)

| Tool Name           | File                                     | Description                                        |
| ------------------- | ---------------------------------------- | -------------------------------------------------- |
| `open_app`          | `actions/open_app.py`                    | Launch any application by name                     |
| `web_search`        | `actions/web_search.py`                  | Web search with compare/search modes               |
| `weather_report`    | `actions/weather_report.py`              | Weather by city                                    |
| `send_message`      | `actions/send_message.py`                | WhatsApp/Telegram messaging                        |
| `reminder`          | `actions/reminder.py`                    | OS-level scheduled notifications                   |
| `screen_process`    | `actions/screen_processor.py`            | Screenshot + webcam vision (daemon thread)         |
| `computer_settings` | `actions/computer_settings.py`           | Volume, brightness, WiFi, shutdown, etc.           |
| `browser_control`   | `actions/browser_control.py`             | Full Playwright browser automation                 |
| `file_controller`   | `actions/file_controller.py`             | File/folder CRUD, search, disk usage               |
| `desktop_control`   | `actions/desktop.py`                     | Wallpaper, organize, clean desktop                 |
| `computer_control`  | `actions/computer_control.py`            | Direct mouse/keyboard/pyautogui control            |
| `webbridge`         | `actions/webbridge.py`                   | Kimi WebBridge via Chrome extension                |
| `game_updater`      | `actions/game_updater.py`                | Steam/Epic Games install, update, schedule         |
| `flight_finder`     | `actions/flight_finder.py`               | Google Flights search via Playwright               |
| `cryp_status`       | `actions/cryp_status.py`                 | System health, version, diagnostics                |
| `agent_task`        | `agent/react_loop.py` + `agent/planner_layer.py` | Multi-step goals via Planner + ReAct loop |
| `save_memory`       | `memory/memory_manager.py`               | Silently persist user facts (no announcement)      |
| `shutdown_cryp`     | inline in `main.py`                      | Graceful exit via `os._exit(0)`                    |
| `code_helper`       | `actions/student/code_helper.py`         | Write/edit/explain/run code files                  |
| `dev_agent`         | `actions/student/dev_agent.py`           | Build complete multi-file projects                 |
| `file_processor`    | `actions/student/file_processor.py`      | Analyze PDFs, images, audio, video, CSV, code      |
| `youtube_video`     | `actions/student/youtube_video.py`       | Play, summarize, trending YouTube videos           |
| `assignment_tracker`| `actions/student/assignment_tracker.py`  | Assignment CRUD + JSON persistence                 |
| `deadline_guardian` | `actions/student/deadline_guardian.py`   | Google Classroom + Calendar deadline sync          |
| `focus_mode`        | `actions/student/focus_mode.py`          | Pomodoro focus session with interruption suppression |
| `exam_prep_coach`   | `actions/student/exam_prep_coach.py`     | Quiz generation + AI grading + weak area tracking  |
| `market_brief`      | `actions/trading/market_brief.py`        | BTC/ETH price + 24h change snapshot                |
| `sentiment_tracker` | `actions/trading/sentiment_tracker.py`   | Fear & Greed Index with local trend history        |
| `trade_journal`     | `actions/trading/trade_journal.py`       | Manual trade log/close/list/stats + JSON persistence |
| `news_filter`       | `actions/trading/news_filter.py`         | RSS → Gemini-filtered top 3 crypto headlines       |

---

## 5. Memory System

**Current implementation**:

- Flat key-value: `memory/long_term.json` (6 categories + patterns namespace)
- Episodic: `memory/episodic/*.json` (dated session files)
- Assignments: `memory/assignments.json` (assignment_tracker data)
- Exam prep stats: `memory/exam_prep.json` (per-topic accuracy + weak areas)
- Trades: `memory/trades.json` (trade_journal entries)
- Sentiment history: `memory/sentiment_history.json` (Fear & Greed daily snapshots)
- News dedup: `memory/news_seen.json` (seen article titles, capped at 200)
- Daily briefing date: `memory/last_briefing_date.txt`
- Functions: `load_memory`, `update_memory`, `save_episode`, `load_recent_episodes`, `search_episodes`, `format_episodes_for_prompt`, `prune_episodes`, `summarize_session`, `query_patterns`
- EpisodicStore singleton via `get_episodic_store()`

---

## 6. UI System

**Current**: React 18 SPA served by FastAPI (`WebCrypUI` in `ui_web.py`)

- States: LISTENING / THINKING / SPEAKING / PROCESSING / MUTED
- `ui.write_log(text)` — appends to transcript log (pushed via WebSocket)
- `ui.set_state(state)` — updates orb visuals and status badge over WebSocket
- `ui.muted` — boolean, mic mute toggle syncs to HUD header dot color
- `ui.current_file` — tracks drag-and-drop / API-uploaded file
- `ui.on_text_command` — callback for typed input from web UI command bar
- `ui.register_client / unregister_client` — WebSocket client lifecycle
- `ui.start_speaking / stop_speaking / speak` — voice state coordination

**Audio Analyzer**: `AudioAnalyzer` class in `ui_web.py` (`portaudio` + FFT)
- 38-band circular waveform around the orb (gemini voice-driven)
- 64-bar log-spectrum analyzer in the React frontend (Web Audio API)

**Frontend stack** (`dashboard/frontend/`):
- Vite + React 18 + Tailwind CSS 3
- Canvas 2D atomic orb (6 elliptical rings, particles, glow core, radial tick marks)
- MetricBar components (CPU/RAM/DISK/NET/GPU/TMP with gradient fill)
- Activity log with color-coded entries
- File upload (click or drag-and-drop)
- Toast notification system
- Command palette (`Cmd/Ctrl+K` or `?`)
- Mobile-responsive layout with collapsible side panels

**Backend routes** (`dashboard/server.py`):
| Route | Description |
|---|---|
| `GET /` | Serves React SPA (`dist/index.html`) |
| `GET /assets/*` | Static JS/CSS assets |
| `WS /ws/cryp` | Bidirectional state/command/mute sync |
| `GET /api/stats` | CPU/RAM/DISK/BAT/NET/GPU/TMP/uptime/procCount |
| `POST /api/upload` | File upload handler |
| `GET /api/logs` | Last N log lines |
| `GET /api/logs/download` | Full log file download |

---

## 7. Key Patterns and Conventions

### Tool Function Signature

All action files follow this pattern:

```python
def tool_name(parameters: dict, player: CrypUI, **kwargs) -> str:
    # implementation
    return "Result description"
```

### Adding a New Tool

1. Create `actions/student/new_tool.py` (or `actions/new_tool.py` for general tools)
2. Import it in `core/cryp_live.py`
3. Add declaration to `TOOL_DECLARATIONS` list in `core/cryp_live.py`
4. Add dispatch branch in `_execute_tool()` in `core/cryp_live.py`

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

### Phase 1 — The Brain — COMPLETE ✅

- [x] ReAct Agent Loop
- [x] Episodic Memory
- [x] Planner Layer

### Phase 2 — Always-On Presence — COMPLETE ✅

- [x] Hotword Detection (openWakeWord)
- [x] Background Daemon (system health monitoring)

### Phase 3 — The Interface — COMPLETE ✅

- [x] WebSocket UI bridge (WebCrypUI drop-in for PyQt6)
- [x] React 18 + Vite + Tailwind HUD served via FastAPI
- [x] Canvas 2D atomic orb + circular waveform + MetricBar system
- [x] Real-time stats, file upload, activity log, command palette

### Phase 4 — Intelligence Depth — COMPLETE ✅

- [x] Deep System Prompt Rewrite
- [x] Live Context Injection
- [x] Kimi WebBridge Integration
- [x] Proactive Intelligence Engine

### Phase 5 — Polish & Robustness — COMPLETE ✅

- [x] Structured Logging (structlog)
- [x] Silent Retry Logic
- [x] Self-Awareness Commands
- [x] Installer & Auto-Start
- [x] Migrated config to `.env` (dotenv)

### Phase 6 — Full Web UI Migration — COMPLETE ✅

- [x] Replaced PyQt6 desktop HUD with React SPA (Canvas 2D orb, 64-bar spectrum analyzer)
- [x] Drop-in `WebCrypUI` class — zero changes to `main.py` beyond import swap
- [x] FastAPI serves React build at `/` + REST endpoints (`/api/stats`, `/api/upload`, `/api/logs`)
- [x] WebSocket `/ws/cryp` for real-time bidirectional state sync
- [x] Mobile-responsive layout with collapsible panels
- [x] Systemd service updated for headless operation
- [x] Audio analyzer + circular waveform + 38-band visualizer

### Phase 7 — Grand Testing of All Features — PENDING

- [ ] Full regression test suite for all tools
- [ ] End-to-end audio session stability test
- [ ] Reconnect & resilience stress testing
- [ ] Cross-platform compatibility check (Ubuntu, Windows, macOS)
- [ ] Hotword accuracy evaluation
- [ ] Proactive engine non-crash validation
- [ ] Dashboard WebSocket & event bus reliability test
- [ ] Memory persistence & episodic recall verification
- [ ] Performance benchmarking & latency profiling

### Phase 8 — Student Intelligence — COMPLETE ✅

- [x] Deadline Guardian (Google Classroom + Calendar sync)
- [x] Document Summarizer (file_processor summarize action)
- [x] Study Focus Mode (Pomodoro with interruption suppression)
- [x] YouTube Lecture Assistant (youtube_video summarize action)
- [x] Assignment & Project Tracker (memory/assignments.json CRUD)
- [x] Exam Prep Coach (quiz generation + Gemini grading + weak area tracking)
- [x] Morning Academic Brief (upcoming deadlines in daily briefing)

### Phase 9 — Trading & Quant Intelligence — COMPLETE ✅

- [x] Shared Market Data module (`get_prices()` + `get_fear_greed()`, 60s cache)
- [x] Crypto Market Brief (BTC/ETH price + 24h change, wired into daily briefing)
- [x] Sentiment Tracker (F&G with local trend history at `memory/sentiment_history.json`)
- [x] Trade Journal (log/close/list/stats, persists to `memory/trades.json`)
- [x] Crypto News Filter (CoinDesk + Cointelegraph RSS → Gemini-filtered top 3, deduped)
- [x] Price Anomaly Watcher (proactive 5-min check in engine.py; 3%+ queued, 6%+ critical bypass via `speak_fn`)

---

## 9. Dependencies

**Runtime (requirements.txt)**:

- `google-genai` — Gemini Live API client
- `sounddevice` — audio I/O
- `websockets` — WebSocket connection management
- `playwright` — browser automation (Chromium)
- `pyautogui` — computer_control tool
- `python-dotenv` — loads .env at startup via `config/settings.py`
- `fastapi` + `uvicorn` — web server for React HUD
- `python-multipart` — file upload support

**Dev tools**:

- Node.js 18+ + npm — building the React frontend
- OpenSpec (`@fission-ai/openspec`) — SDD framework
- pytest / Playwright test suite in `tests/`

---

## 10. Rules Every AI Agent Must Follow

1. **Never rewrite `main.py` wholesale** — it is ~980 lines of carefully structured async code. Make surgical changes only.
2. **Always follow the tool function signature** — `(parameters: dict, player: WebCrypUI, **kwargs) -> str`
3. **New tools require 3 changes**: new file in `actions/`, entry in `TOOL_DECLARATIONS`, branch in `_execute_tool()`
4. **`save_memory` is always silent** — never add print/log/speak calls inside it
5. **New tools go in `actions/student/`** if student-related, **`actions/trading/`** if trading/quant-related, otherwise `actions/`
6. **Focus mode** — `is_focus_active()` suppresses non-critical proactive messages at the queue drain point in `cryp_live.py`; health daemon alerts bypass the queue via `_alert_speak()` and always get through
7. **Threading discipline** — tools that need UI interaction must use `threading.Thread(daemon=True)` like `screen_process`
8. **`loop.run_in_executor`** — all synchronous tool calls must be wrapped in executor to avoid blocking the async loop
9. **State resets** — every tool branch must call `self.ui.set_state("LISTENING")` on exit (already handled by `_execute_tool` finally block — don't add duplicate calls)
10. **Ubuntu 26.04 target** — Playwright browser download is unsupported on this host; use installed system browsers
11. **No hardcoded API keys** — always read from `config.settings` (loaded from `.env`)
12. **Keep `core/prompt.txt` as the only personality source** — don't embed personality in code
13. Never rewrite `proactive/` modules wholesale — surgical only
14. ProactiveEngine is the 7th TaskGroup task — never add more tasks without explicit instruction
15. `speak()` is SYNC — never await it
16. Proactive briefing fires ONCE per day via `memory/last_briefing_date.txt`
17. Kimi WebBridge auto-starts in `_start_webbridge()` on init and stops in `_stop_webbridge()` on shutdown
18. Dashboard is the primary UI — FastAPI + React SPA at port 7070; event bus is optional (`event_bus=None` safe)
19. All proactive code wrapped in try/except — never crash

---

## 11. File Change Map

When working on a feature, here are the files typically involved:

| Feature Area        | Files to Touch                                                                 |
| ------------------- | ------------------------------------------------------------------------------ |
| New tool            | `actions/student/new_tool.py`, `core/cryp_live.py` (2 places)                |
| Memory upgrade      | `memory/memory_manager.py`, `main.py` (_build_config)                         |
| Agent / planning    | `agent/`, `main.py` (_execute_tool agent_task branch)                         |
| UI changes          | `ui_web.py` only                                                               |
| Personality changes | `core/prompt.txt` only                                                        |
| Session config      | `main.py` (_build_config method only)                                         |
| New dependency      | `requirements.txt` + import in relevant file                                  |
| Voice / audio       | `main.py` (constants + _listen_audio / _play_audio)                          |
| Proactive features  | `proactive/*.py`, `core/cryp_live.py` (focus mode suppression), `core/daemon.py` |
| Trading tools       | `actions/trading/*.py`, `core/cryp_live.py` (3 places), `core/prompt.txt`, `proactive/briefing.py`, `proactive/engine.py` |
| Dashboard updates   | `dashboard/server.py`, `dashboard/frontend/src/` (React components, hooks)   |
| WebBridge           | `actions/webbridge.py`, `main.py` (_start/_stop only)                         |
| Live context        | `core/context_collector.py`                                                   |
| Hotword/sleep       | `core/hotword.py`, `core/wake_config.py`, `main.py`                          |
| Suggestion rules    | `config/proactive_rules.json` only                                             |
| Daily briefing      | `proactive/briefing.py` only                                                  |
| Pattern detection   | `proactive/patterns.py` only                                                  |