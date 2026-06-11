## Context

Cryp is a desktop AI assistant with ~30 Python modules, a FastAPI web dashboard, and a PyQt6 desktop HUD. Logging is done via bare `print()` statements with tag prefixes (~260 calls). There is no way to filter by severity, persist logs to disk with rotation, or stream logs to the web dashboard for live debugging. The project roadmap identifies structured logging as a needed Phase 5 feature.

The existing `DashboardEventBus` in `dashboard/event_bus.py` already implements a pub-sub pattern for streaming events (transcripts, state changes, system stats) to the dashboard via WebSocket. The log system should integrate with this pattern.

## Goals / Non-Goals

**Goals:**
- Replace every `print()` call with a proper structlog call at the correct severity level
- Provide rotating file logging to `logs/cryp.log` (and `logs/cryp-error.log` for errors only)
- Stream live logs to the web dashboard via a new WebSocket endpoint
- All log output visible to the user currently (via terminal) must remain visible — no silent loss of information
- Zero impact on existing functionality — logging is purely additive

**Non-Goals:**
- Replacing the PyQt6 HUD `LogWidget` in `ui.py` (it displays conversation transcripts, not application logs)
- Adding log levels to the existing conversation transcript (different concerns)
- Changing the Gemini Live API audio streaming code
- Performance optimization beyond what structlog provides by default

## Decisions

**1. Use structlog with stdlib logging as backend**
- *Rationale*: structlog provides the cleanest API for structured logging in Python — event-based API (not format-string-based), automatic context binding, multiple output processors, and easy integration with stdlib handlers for file output
- *Alternative considered*: Raw stdlib `logging` with custom formatters — more verbose, no structured output by default, no context binding without boilerplate
- *Alternative considered*: `loguru` — simpler API but tighter coupling, harder to integrate with existing FastAPI/uvicorn logging, no WebSocket handler pattern

**2. Single pre-configured module (`core/logger.py`)**
- *Rationale*: One import (`from core.logger import log`) provides a ready-to-use logger with all handlers attached. Configuration happens once at import time. The `structlog.get_logger()` call returns a bound logger with the module name automatically.
- *Alternative considered*: Configuring per-module — duplicates config logic, harder to maintain
- *Alternative considered*: Dependency injection — over-engineered for logging, Python's module-level singleton pattern is standard for logging

**3. Three output handlers (console, file-rotating, websocket-broadcast)**
- Console: `structlog.dev.ConsoleRenderer` for readable terminal output with colors
- File rotation: `logging.handlers.RotatingFileHandler` (10 MB per file, 5 backups, JSON output via `structlog.processors.JSONRenderer`)
- Error file: Separate `RotatingFileHandler` at WARNING+ level for errors-only log
- WebSocket: Custom handler that pushes to `DashboardEventBus` — logs become events streamed to the dashboard

**4. Log level mapping for existing print() calls**
- `print("[CRYP] connected")` → `log.info("connected")`
- `print("[Vision] camera not detected")` → `log.warning("camera not detected")`  
- `print("[daemon] unexpected error: ...")` → `log.error("unexpected error", exc_info=True)`
- Trivial status prints without user-facing value → `log.debug(...)`

**5. Log viewer in dashboard**
- New WebSocket endpoint `/ws/logs` in `dashboard/server.py`
- New `LogPanel` section in `index.html` with auto-scroll, severity color coding, and a filter input
- Uses the same event bus pattern as existing dashboard events

## Risks / Trade-offs

- **Risk**: structlog adds a dependency and import overhead in every module
  - *Mitigation*: structlog is lightweight (pure Python, no C extensions) and the `core/logger.py` singleton means minimal per-module cost

- **Risk**: Log file rotation on Linux with multiple processes could cause conflicts
  - *Mitigation*: Cryp is a single-process application (asyncio event loop), so file locking is not needed

- **Risk**: The WebSocket log stream could overwhelm the dashboard if logs are very frequent
  - *Mitigation*: Apply a rate limit in the custom WebSocket handler (max N messages per second), and only stream INFO+ by default from the dashboard

- **Trade-off**: Console output will change from raw `print()` to structlog's colored console rendering — slightly different formatting but all information is preserved
