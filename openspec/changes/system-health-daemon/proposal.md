## Why

Cryp currently only displays system metrics (CPU, RAM, etc.) passively in the UI. The user must notice and act on problems themselves. A true JARVIS-like assistant proactively alerts when system health degrades — speaking warnings about low battery, high CPU, memory pressure, or critical disk usage without being asked. This bridges the gap from "tool you query" to "presence that watches over you."

## What Changes

- Introduce a new `core/daemon.py` module with a `SystemHealthDaemon` asyncio task that periodically monitors CPU, RAM, disk, and battery
- Wire the daemon into `JarvisLive.run()` as a 6th concurrent asyncio task inside the existing `TaskGroup`
- When configurable thresholds are exceeded, the daemon calls `JarvisLive.speak()` to proactively alert the user via voice
- Alert thresholds are configurable via a `config/health_daemon.yaml` file (or env defaults)
- Add a `psutil` import/usage layer (psutil is already a project dependency via `ui.py`)
- No new external dependencies required

## Capabilities

### New Capabilities
- `system-health-daemon`: Background async task that monitors CPU, RAM, disk, and battery at configurable intervals and speaks alerts when thresholds are exceeded

### Modified Capabilities

None — no existing specs have requirement changes.

## Impact

- **New file**: `core/daemon.py` — `SystemHealthDaemon` class
- **Modified file**: `main.py` — add daemon task to `TaskGroup` in `run()`, store reference for `speak()`
- **New file** (optional): `config/health_daemon.yaml` — threshold configuration
- **Dependencies**: `psutil` (already present in `requirements.txt` used by `ui.py`)
- No changes to existing tools, UI, prompt, or session config
