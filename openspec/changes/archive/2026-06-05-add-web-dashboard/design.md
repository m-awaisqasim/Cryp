## Context

Cryp's PyQt6 HUD (`MainWindow` in `ui.py`) provides rich real-time visualization: animated waveform, system metrics, and a typewriter log. However, this is a single-window desktop GUI accessible only on the primary display. The assistant's state (transcript, active ReAct task, memory facts, system health) has no secondary or remote view.

The `main()` function starts the PyQt6 event loop on the main thread and runs `JarvisLive`'s async event loop in a daemon thread. `JarvisLive` already integrates a `SystemHealthDaemon` as a background asyncio task. The codebase uses `fastapi` and `uvicorn` (already in `requirements.txt`) but has no custom WebSocket server or event bus — coordination uses `pyqtSignal`, `asyncio.Event`, and `threading.Event`.

This design adds a lightweight, read-only web dashboard that mirrors key state without modifying any existing `JarvisLive` interface or the PyQt6 UI.

## Goals / Non-Goals

**Goals:**
- Serve a single-page HTML dashboard at `http://localhost:7070`
- Push live updates via WebSocket (no polling): transcript lines, assistant state, ReAct task status, memory facts, system health metrics
- Introduce a `DashboardEventBus` that collects state from `JarvisLive` and broadcasts to connected WebSocket clients
- Wire `JarvisLive` to push transcript lines and state changes into the event bus with zero changes to `JarvisLive`'s public API
- Start the FastAPI+WebSocket server in a daemon thread from `main()`, alongside the existing PyQt6 thread
- All existing PyQt6 UI (`JarvisUI`/`MainWindow`) remains completely unchanged
- All existing `JarvisLive` interfaces remain completely unchanged

**Non-Goals:**
- No authentication or TLS (localhost-only)
- No persistent dashboard state (refresh resets)
- No write-back from dashboard to JarvisLive (read-only)
- No mobile-responsive layout (desktop-focused)
- No modifications to any existing file except `main.py` and `requirements.txt`

## Decisions

1. **New `dashboard/event_bus.py` — `DashboardEventBus` using `asyncio.Queue` per subscriber** — A pub-sub event bus that `JarvisLive` pushes events into via a `publish()` method. Each WebSocket connection gets a dedicated `asyncio.Queue`. The bus is thread-safe (uses `asyncio.run_coroutine_threadsafe` internally) so it can be called from sync contexts like tool execution or the health daemon. Alternative considered: global `pyqtSignal` — rejected because signals are Qt-specific and tie the bus to the GUI thread.

2. **New `dashboard/server.py` — FastAPI app with WebSocket endpoint** — A single FastAPI application with one WebSocket endpoint (`/ws`) and one HTTP endpoint (`/` serving the SPA). The server is started with `uvicorn` in a daemon thread using `uvicorn.run(app, host="127.0.0.1", port=7070, log_level="warning")`. Alternative considered: bare `websockets` library — rejected because FastAPI provides clean routing, static file serving, and graceful shutdown integration.

3. **New `dashboard/templates/index.html` — Self-contained SPA** — A single HTML file with embedded CSS and JS (~300 lines). Four panels arranged in a 2x2 CSS grid: (top-left) live transcript, (top-right) memory explorer, (bottom-left) active ReAct task, (bottom-right) system stats. Uses native `WebSocket` API — no frameworks needed. Updates arrive as JSON messages with a `type` field.

4. **Wire `JarvisLive` to the event bus via `write_log` and a new `publish_state` hook** — The `DashboardEventBus` is created in `main()` and passed to `JarvisLive`'s constructor. Inside `JarvisLive`, `self.ui.write_log` calls are already the central logging mechanism — the event bus subscribes to the same log output. For state changes (LISTENING/THINKING/SPEAKING/SLEEPING), a thin `publish_state()` method is added to `JarvisLive` that the existing state transitions already call. This approach requires zero refactoring of existing methods. Alternative considered: monkey-patching `ui.write_log` — rejected as fragile.

5. **System stats sourced from the existing `SystemHealthDaemon`** — The health daemon already polls CPU, RAM, disk, battery. The event bus receives a snapshot from the daemon's latest readings (stored as instance attributes) on a timer or when polled. No duplicate monitoring logic. Alternative considered: adding independent `psutil` calls in the dashboard server — rejected as duplicative.

6. **ReAct task status sourced from `ReactAgentLoop`'s current state** — The `ReactAgentLoop` already tracks `_current_step`, `_total_steps`, `_current_goal`, and a `_latest_result`. The event bus reads these via a callback registered at loop creation time. The existing `write_log` calls inside the ReAct loop already provide the step-by-step transcript; the event bus picks these up directly.

7. **Memory facts sourced from `memory_manager.py`'s `load_memory()`** — On WebSocket connect, the server reads the current memory dict and sends it as an initial snapshot. Subsequent updates arrive when `update_memory()` is called (picked up via the `write_log` hook, or a dedicated callback).

8. **No new Python dependencies** — `fastapi`, `uvicorn`, and `websockets` are already in `requirements.txt`. The SPA uses vanilla JS.

## Risks / Trade-offs

- **Thread safety of `DashboardEventBus.publish()`** → mitigated by using `asyncio.run_coroutine_threadsafe` to enqueue events. The bus never holds a lock across `await` points.
- **WebSocket client disconnects** → each subscriber queue is drained and cleaned up on disconnect. Slow consumers are dropped after a timeout.
- **uvicorn in a daemon thread has no graceful shutdown** → acceptable for a local-only dev dashboard. The thread is daemon so it dies when the process exits.
- **Firewall blocking port 7070** → the server binds to `127.0.0.1` only (not `0.0.0.0`), so it is never exposed to the network.
- **Transcript backlog on connect** → on WebSocket connect, the last 20 transcript lines are replayed from the event bus's ring buffer to give context.
- **Potential performance impact of JSON serialization on every log line** → mitigated by batching: the event bus coalesces rapid log writes into a single JSON message sent at most every 100ms.
