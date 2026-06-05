## Why

Jarvis has zero awareness of what the user is currently doing — no active window, no clipboard, no system state. This makes context-blind responses that feel robotic. Injecting live system context at session start gives Jarvis situational awareness without needing a separate tool call.

## What Changes

- Add `core/context_collector.py` — gathers active window title, clipboard preview, battery status, CPU/RAM usage, current time
- Add `main.py` — inject `gather_live_context()` output into `_build_config()` system prompt assembly
- The live context block is injected fresh on every session connect, before memory/episodic blocks
- No new tool, no schema changes — purely a prompt injection at config build time

## Capabilities

### New Capabilities

- `live-context`: Gather and inject live desktop context (window, clipboard, battery, CPU/RAM, time) into every Gemini session's system instruction

### Modified Capabilities

*(none — existing spec behavior is unchanged)*

## Impact

- **`main.py`**: Small change in `_build_config()` — call `gather_live_context()` and prepend its output to `parts` list
- **New file**: `core/context_collector.py` with platform-specific logic
- **`requirements.txt`**: Optional: `psutil` (CPU/RAM), `pyperclip` (clipboard) — or use stdlib alternatives
- **Testability**: Context output can be unit-tested independently; integration tested via session log
