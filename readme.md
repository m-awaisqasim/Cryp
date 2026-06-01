# Cryp

**Cryp** is a cross-platform personal AI assistant built for real-time voice interaction, desktop control, screen understanding, file processing, persistent memory, and autonomous task execution.

It is designed to feel like a practical JARVIS-style assistant: local UI, Gemini-powered reasoning, tool calling, memory, and direct computer actions from one Python application.

## Highlights

| Capability | What It Does |
|---|---|
| Real-time voice | Uses Gemini Live audio for low-latency conversation. |
| Desktop control | Opens apps, controls windows, sends hotkeys, types, clicks, scrolls, and manages system settings. |
| Browser automation | Opens sites, searches, clicks elements, fills forms, navigates tabs, and captures page state. |
| Screen vision | Captures screen or camera input and asks Gemini to analyze what is visible. |
| File handling | Reads, summarizes, converts, analyzes, and extracts content from images, PDFs, documents, spreadsheets, audio, code, archives, and presentations. |
| Persistent memory | Stores useful user facts and project context across sessions. |
| Autonomous workflows | Plans and executes multi-step tasks through specialized action modules. |
| PyQt interface | Provides a local HUD-style UI with logs, controls, file drop support, and system metrics. |

## Requirements

| Requirement | Details |
|---|---|
| OS | Windows 10/11, macOS, or Linux |
| Python | 3.11 or newer |
| API key | Gemini API key |
| Audio | Microphone and speakers for voice mode |
| Optional browsers | System browser or Playwright browsers for web automation |

On Linux, some desktop/audio features may also require system packages such as PulseAudio/PipeWire, notification tools, screenshot permissions, and display server access.

## Quick Start

```bash
git clone https://github.com/m-awaisqasim/Cryp.git
cd Cryp

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python main.py
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## Configuration

Cryp looks for its local configuration at:

```text
config/api_keys.json
```

Example:

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "os_system": "linux"
}
```

Use one of these values for `os_system`:

```text
windows
mac
linux
```

`config/api_keys.json` is ignored by Git so secrets stay local.

## Running Checks

Python compile check:

```bash
python -m py_compile main.py ui.py actions/*.py agent/*.py memory/*.py core/*.py config/*.py setup.py
```

Project smoke tests:

```bash
npm test
```

The current Playwright tests are repository smoke tests and do not require downloaded Playwright browser binaries.

## Useful Commands

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the app:

```bash
python main.py
```

Check installed package health:

```bash
python -m pip check
```

Run Node/Playwright smoke tests:

```bash
npm test
```

## Project Structure

```text
Cryp/
├── main.py                 # Gemini Live session, tool routing, voice loop
├── ui.py                   # PyQt HUD interface
├── actions/                # Tool implementations for desktop, files, browser, search, etc.
├── agent/                  # Planning, execution, task queue, error handling
├── core/                   # Gemini compatibility layer and system prompt
├── memory/                 # Long-term memory and config helpers
├── config/                 # Local ignored API key config
├── tests/                  # Playwright smoke tests
├── Context/                # Project planning and architecture notes
├── requirements.txt        # Python dependencies
├── package.json            # Node test scripts
└── setup.py                # Convenience installer
```

## Core Modules

| Path | Purpose |
|---|---|
| `main.py` | Starts the UI, connects Gemini Live, streams audio, and routes function calls. |
| `ui.py` | Builds the desktop interface, logs, controls, API key flow, and file-drop experience. |
| `actions/browser_control.py` | Browser automation through Playwright. |
| `actions/screen_processor.py` | Screen/camera capture and vision analysis. |
| `actions/file_processor.py` | Document, image, audio, archive, code, and spreadsheet processing. |
| `actions/computer_control.py` | Direct input control such as typing, clicking, hotkeys, and screenshots. |
| `agent/executor.py` | Runs multi-step agent plans and delegates work to tools. |
| `memory/memory_manager.py` | Loads, formats, and updates long-term memory. |

## Troubleshooting

### `ModuleNotFoundError: No module named 'google'`

Your shell is not using the project virtual environment, or dependencies were not installed into it.

```bash
deactivate 2>/dev/null || true
source .venv/bin/activate
which python
python -m pip install -r requirements.txt
python -c "from google import genai; print('ok')"
```

`which python` should print:

```text
/home/awais/Cryp/.venv/bin/python
```

### Audio or PortAudio Errors

If PulseAudio/PipeWire is unavailable, Cryp should still start and log that microphone or speaker audio is unavailable. Fix the host audio service, then restart the app.

On Linux, check:

```bash
pactl info
```

### Playwright Browser Errors

The smoke tests do not need browser downloads. Browser automation features can use installed system browsers. If you specifically want Playwright-managed browsers:

```bash
python -m playwright install
```

On some newer Ubuntu releases, Playwright browser downloads may be unsupported; use system browsers in that case.

### Virtualenv Points to an Old Folder

If the project was moved from another directory, recreate the environment cleanly:

```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Security Notes

- Keep `config/api_keys.json` private.
- Review any desktop-control or browser-control action before using it on sensitive data.
- Be careful with file operations such as delete, move, overwrite, and archive extraction.
- Avoid committing personal memory files if they contain private information.

## Episodic Memory (BETA)

Cryp remembers full conversation summaries, not just isolated facts. Each live session is summarized at shutdown, on reconnect, after 20+ turns (rollover), or via the `atexit` safety net, and stored as a dated JSON file under `memory/episodic/`. On the next connection, the most recent episodes are loaded and injected into the system prompt so Jarvis can answer questions like "what did we discuss last week?".

### Storage layout

```text
memory/episodic/YYYY-MM-DD.json
```

Each file is a JSON list of episode objects:

```json
[
  {
    "timestamp":  "2026-06-01T14:32:00",
    "summary":    "User asked Jarvis to summarize the README.",
    "tools_used": ["file_controller", "code_helper"],
    "goal":       "",
    "closed_via": "shutdown"
  }
]
```

`memory/episodic/*.json` is git-ignored; the directory itself is tracked via `.gitkeep`.

### Configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `EPISODIC_RECENT_COUNT` | `5` | Number of most recent episodes injected into the system prompt at session start. |
| `ENABLE_RECALL_TOOL` | `0` | When set to `1`, exposes the `recall_episodes` tool so the model can search past sessions on demand. |

Pruning (default 500 files) runs at the top of every `_build_config` call and is idempotent.

### Programmatic API

All helpers live in `memory/memory_manager.py`:

| Function | Purpose |
| --- | --- |
| `EpisodicStore().save_episode(ep)` | Appends `ep` to today's dated JSON file. |
| `EpisodicStore().get_latest_episodes(n)` | Newest `n` episodes, sorted desc. |
| `EpisodicStore().get_recent_episodes(days)` | Episodes from the last `days` calendar days. |
| `EpisodicStore().format_for_prompt(days=3)` | Human-readable block for the system prompt. |
| `load_recent_episodes(n=5)` | Module-level wrapper around `get_latest_episodes`. |
| `search_episodes(query, limit=5)` | Case-insensitive substring search over `summary`/`topics`/`goal`/`tools_used`. |
| `format_episodes_for_prompt(eps, max_chars=1500)` | Bullet block capped at `max_chars` characters. |
| `prune_episodes(keep_last=500)` | Deletes oldest JSON files; returns count deleted. |
| `summarize_session(transcript, api_key, model="gemini-2.0-flash")` | Async helper that calls Gemini and returns an episode dict (never raises). |
| `get_episodic_store()` | Returns the process-wide singleton `EpisodicStore`. |
| `format_full_memory_for_prompt(semantic_memory)` | Joins semantic facts with recent episodes for a one-shot prompt block. |

## License

Personal and non-commercial use only.

Licensed under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

## Author

Created by **Awais** as a real-world personal AI assistant project.
