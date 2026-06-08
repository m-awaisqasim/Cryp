## Why

Cryp currently relies on bare `print()` statements with ad-hoc tag prefixes (`[JARVIS]`, `[Memory]`, etc.) across 30+ Python files (~260 calls). This makes it impossible to filter logs by severity, search logs retroactively, or diagnose issues in production. The roadmap already lists structured logging as a planned feature (Phase 5). Adding structlog now provides proper log levels, rotating file output, and machine-readable JSON logs — without changing any existing behavior.

## What Changes

- Replace all `print()` calls with `structlog` log calls at appropriate levels (debug, info, warning, error)
- Add rotating log file handlers that write to `logs/` directory
- Add a log viewer WebSocket endpoint to the FastAPI dashboard
- Update the dashboard HTML with a log viewer panel
- No existing functionality, output, or behavior changes — logging is purely additive

## Capabilities

### New Capabilities
- `structured-logging`: Centralized structured logging system with structlog — replaces print() with proper log levels, handles log file rotation, and provides a log stream for the dashboard

### Modified Capabilities

None

## Impact

- All Python files with `print()` calls (~30 files) will have those calls replaced
- New dependency: `structlog`
- New directory: `logs/` (auto-created, gitignored)
- `dashboard/server.py`: new WebSocket endpoint `/ws/logs`
- `dashboard/templates/index.html`: new log viewer panel in the HUD
- `main.py`: log configuration initialized at startup
