# Cryp — A Real-World JARVIS AI Assistant 🧠

<div align="center">

**Cryp** is an open-source, voice-first desktop AI assistant that lives on your machine.  
It sees your screen, controls your apps, remembers your context, and proactively helps you — all through natural conversation.

[Python 3.11+](https://www.python.org/downloads/release/python-3110/) · [Gemini Live API](https://ai.google.dev/) · [MIT-Adjacent License](#license) · [Cross-Platform](#)

</div>

---

## Why Cryp? 🤖

Most AI assistants live in the cloud. **Cryp lives with you** — on your desktop, in your processes, with access to your actual machine state.

| | |
|:---|:---|
| 🎙️ **Voice-native** | Low-latency conversation through Gemini Live. No API latency; just speech. |
| 🖥️ **Desktop-native** | Opens apps, manages windows, sends hotkeys, changes system settings. |
| 🌐 **Browser-native** | Real browser automation using your logged-in Chrome profile via WebBridge. |
| 👁️ **Screen-native** | "What's on my screen?" → captures + analyzes instantly. |
| 🧠 **Memory-native** | Long-term facts + episodic memory across sessions. |
| ⚡ **Proactive-native** | Notices patterns, detects anomalies, and offers help before you ask. |

---

## Quick Start ⚡

### One-command install (recommended)

```bash
curl -sSL https://raw.githubusercontent.com/m-awaisqasim/Cryp/main/install.sh | bash
```

Then copy `.env.example` to `.env`, add your Gemini API key, and run:

```bash
cryp start
```

### Manual install

```bash
# 1. Clone the repo
git clone https://github.com/m-awaisqasim/Cryp.git
cd Cryp

# 2. Create virtual environment & install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Add your Gemini API key
# Edit .env (copy from .env.example)

# 4. Check dependencies
bash scripts/check_deps.sh

# 5. Install and enable auto-start
bash install.sh

# 6. Start Cryp
cryp start
```

### CLI Commands

```bash
cryp start    # start Cryp
cryp stop     # stop Cryp
cryp restart  # restart Cryp
cryp status   # check if running
cryp logs     # follow live logs
cryp enable   # enable auto-start on login
cryp disable  # disable auto-start
```

### Manual Start (without auto-start)

```bash
source .venv/bin/activate
python3 main.py
```

Once running, say **"Hey Jarvis"** (hotword activation) or just start typing in the UI.

---

## Configuration 🔧

Cryp reads all configuration from a `.env` file at the project root via `config/settings.py`:

```bash
# Start from the template
cp .env.example .env
```

**Required variables:**

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `OS_SYSTEM` | `windows`, `mac`, or `linux` |

See `.env.example` for all optional settings (hotword, proactive engine, health daemon, retry logic, etc.).

> `.env` is gitignored. `.env.example` is tracked as a template.

---

## Roadmap 🗺️

The project is built in **phased milestones**:

### Phase 1 — The Brain ✅

- [x] ReAct Agent Loop (PlannerLayer + ReactAgentLoop)
- [x] Episodic Memory (conversation summaries + search)
- [x] Multi-step reasoning with plan announcement

### Phase 2 — Always-On Presence ✅

- [x] Hotword detection (`openWakeWord`)
- [x] Background system daemon (CPU/RAM/battery/calendar)

### Phase 3 — The Interface ✅

- [x] PyQt6 HUD (frameless, ambient presence mode)
- [x] Local web dashboard (FastAPI + WebSocket at `localhost:7070`)

### Phase 4 — Intelligence Depth ✅

- [x] Deep system prompt rewrite
- [x] Live context injection (clipboard, active window, battery)
- [x] Kimi WebBridge (browser control via Chrome extension)
- [x] Proactive Intelligence Engine (patterns, anomalies, daily briefing)

### Phase 5 — Polish & Robustness 🔜

- [x] Structured logging (`structlog`)
- [x] Silent retry logic
- [x] Self-awareness diagnostics
- [x] One-click installer + auto-start

- [x] Extra Feature: Migratation to dotenv

### Phase 6 — Full Web UI Migration 🌐

### Phase 7 — Grand Testing of All Features 🔜

- [ ] Full regression test suite for all 20 tools
- [ ] End-to-end audio session stability test
- [ ] Reconnect & resilience stress testing
- [ ] Cross-platform compatibility check (Ubuntu, Windows, macOS)
- [ ] Hotword accuracy evaluation
- [ ] Proactive engine non-crash validation
- [ ] Dashboard WebSocket & event bus reliability test
- [ ] Memory persistence & episodic recall verification
- [ ] Performance benchmarking & latency profiling

### Phase 8 — Student Intelligence 🎓

- [ ] Deadline Guardian (Google Classroom + Calendar)
- [ ] Document Summarizer
- [ ] Study Focus Mode
- [ ] YouTube Lecture Assistant
- [ ] Assignment & Project Tracker
- [ ] Exam Prep Coach
- [ ] Morning Academic Brief

### Phase 9 — Trading & Quant Intelligence 📈

- [ ] Crypto Market Brief
- [ ] Research Paper Digest
- [ ] Sentiment Tracker
- [ ] Trading Assistant
- [ ] Quant Research Assistant

---

## Project Structure 🏗️

```
Cryp/
├── main.py                        # Session orchestrator: audio loop, reconnect, task group
├── ui.py                          # PyQt6 HUD (frameless always-on-top mode)
│
├── core/
│   ├── prompt.txt                 # Personality & behavioral rules (sole source of truth)
│   ├── context_collector.py       # Live/system/proactive context gathering
│   ├── hotword.py                 # Wake-word detection via openWakeWord
│   ├── wake_config.py             # Wake thresholds & mic settings
│   └── daemon.py                  # Background health/scheduler signal emitter
│
├── proactive/
│   ├── engine.py                  # ProactiveEngine (7th async TaskGroup task)
│   ├── briefing.py                # Daily briefing + date persistence
│   ├── patterns.py                # Time/frequency pattern detection
│   ├── anomalies.py               # 2σ CPU/RAM/app anomaly detection
│   ├── conversation_state.py      # Thread-safe conversation state tracker
│   └── queue.py                   # Async proactive message queue
│
├── dashboard/
│   ├── event_bus.py               # Pub-sub per-subscriber event bus
│   ├── server.py                  # FastAPI + WebSocket at localhost:7070
│   └── templates/
│       └── index.html             # Iron Man HUD single-page dashboard
│
├── agent/
│   ├── react_loop.py              # ReAct reasoning loop
│   ├── planner_layer.py           # Plan announcement before execution
│   ├── config.py                  # ReactConfig + PlannerConfig
│   └── executor.py                # Deprecated legacy executor
│
├── actions/
│   ├── webbridge.py               # Kimi WebBridge (Chrome extension bridge)
│   ├── browser_control.py         # Playwright browser automation
│   ├── computer_control.py        # Direct input (mouse/keyboard/screenshot)
│   ├── screen_processor.py        # Vision analysis via Gemini
│   ├── file_processor.py          # PDF, image, audio, video, CSV, code
│   ├── file_controller.py         # File/folder CRUD + disk usage
│   ├── computer_settings.py       # Volume, brightness, WiFi, power
│   ├── web_search.py              # Web search with compare/search modes
│   ├── open_app.py                # Launch applications
│   ├── weather_report.py          # Weather by city
│   ├── send_message.py            # WhatsApp/Telegram messaging
│   ├── reminder.py                # Task scheduler reminders
│   ├── youtube_video.py           # Play, summarize, trending videos
│   ├── desktop.py                 # Wallpaper, clean, organize
│   ├── code_helper.py             # Write/edit/explain/run code
│   ├── dev_agent.py               # Multi-file project generation
│   └── game_updater.py            # Steam/Epic install/update/schedule
│
├── memory/
│   ├── memory_manager.py          # Semantic long-term memory
│   └── last_briefing_date.txt     # Daily briefing deduplication (gitignored)
│
├── config/
│   ├── settings.py                # Central config loader (reads .env)
│   └── proactive_rules.json       # 4 default suggestion rules
│
├── tests/                         # Unit tests (186 passing)
├── Context/                       # Planning, specs, architecture notes
└── openspec/                      # SDD / change-tracking layer
```

---

## Test Suite 🧪

```bash
npm test                          # Playwright smoke tests
python -m pytest tests/           # Unit tests (186 passing)
python -m py_compile main.py      # Fast syntax check
python -m pip check                # Dependency audit
```

| Test File | Tests |
|:---|:---|
| `test_react_loop.py` | 43 |
| `test_episodic_memory.py` | 30 |
| `test_daemon.py` | 23 |
| `test_proactive.py` | 28 |
| `test_hotword.py` | 10 |
| `test_planner_layer.py` | — |
| `test_dashboard.py` | — |
| `test_context_collector.py` | — |

---

## How It Works 🔄

```
                    ┌──────────────┐
  Mic (16kHz) ────▶│  main.py     │◀─── User (typed / hotword)
                    │  JarvisLive  │
  Speaker (24kHz) ◀─│  TaskGroup   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         [ReAct Loop] [Proactive]   [Tools]
         Planner ──▶ Reason ──▶ Act ──▶ Observe
              │
              └──▶ agent/react_loop.py
                   agent/planner_layer.py
```

1. **Audio loop** captures mic → streams to Gemini Live.
2. **Gemini Live** transcribes, reasons, decides to call a tool or speak.
3. **Tool dispatch** runs sync tools in a thread pool (no async blocking).
4. **ReAct loop** handles multi-step goals with PlannerLayer announcing plans first.
5. **ProactiveEngine** runs as a background TaskGroup task detecting patterns, anomalies, and delivering daily briefings.

---

## Troubleshooting 🩹

### Module not found after install
Your shell likely isn't pointing at the project virtualenv.

```bash
deactivate 2>/dev/null || true
source .venv/bin/activate
which python   # should print: .../Cryp/.venv/bin/python
python -m pip install -r requirements.txt
```

### No microphone / speakers
On Linux, verify PulseAudio/PipeWire:

```bash
pactl info
```

Cryp falls back gracefully — it starts without audio and logs the issue.

### Playwright failures
System-browser mode is the default. For Playwright-managed Chromium:

```bash
python -m playwright install
```

> Ubuntu 26.04 note: Playwright browser downloads may be unsupported on newer kernels. Use your system Chrome instead.

### Moved project folder?
Old virtualenv symlinks break. Re-create:

```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## Security & Privacy 🔒

- Keep `.env` private — it is `.gitignore`-d. Use `.env.example` as a template.
- Desktop-control and browser-control actions act on your real machine. Review actions before invoking sensitive operations.
- File actions (`delete`, `move`, `overwrite`, `archive extract`) are powerful — confirm intent.
- Episodic memory files (`memory/episodic/*.json`) are git-ignored; they may contain conversational data.

---

## Contributing 🤝

1. Fork the repo
2. Create your feature branch
3. Keep changes surgical — `main.py` and `proactive/` are touchy
4. Add tests for new behavior
5. Open a PR

Guidelines:
- Follow the tool-function signature: `def tool(parameters: dict, player: JarvisUI, **kwargs) -> str`
- Never await `speak()` — it is synchronous
- Wrap proactive code in `try/except`
- `core/prompt.txt` is the only personality source

---

## License 📄

Personal and non-commercial use only.

Licensed under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

---

## Author ✨

Built by **Awais** as a hands-on exploration of what a local, voice-first, fully-capable AI assistant can actually do.

Repository: [github.com/m-awaisqasim/Cryp](https://github.com/m-awaisqasim/Cryp)
