## Context

Cryp currently runs a PyQt6 desktop GUI (`ui.py`, 2088 lines) that is tightly coupled to the Python process through `JarvisUI` class. The existing `dashboard/server.py` already has FastAPI + WebSocket infrastructure at `localhost:7070` serving a static HTML dashboard. This design replaces the desktop GUI with a React SPA that communicates with the Python backend exclusively via WebSocket, making the UI accessible from any browser on the local network or via tunnel.

## Goals / Non-Goals

**Goals:**
- Create `ui_web.py` as a drop-in `JarvisUI` replacement — every `self.ui.*` call in `main.py` and all action files must work unchanged
- Build a React SPA in `dashboard/frontend/` that visually matches the PyQt6 HUD (dark cyan/teal theme, rotating orb, scan rings, animated particles, data bits, sparklines, gauges)
- Serve the SPA via the existing FastAPI server in production; use Vite dev server during development
- Support phone access via LAN IP and optional ngrok/cloudflared tunnel
- Delete `ui.py` entirely once `ui_web.py` is verified

**Non-Goals:**
- No changes to `main.py`'s `JarvisLive` class logic, tool dispatch, or session management
- No changes to any `actions/*.py` files (they call `self.ui.*` which will be transparently routed)
- No authentication system (UI assumes trusted network; tunnel adds basic token auth)
- No PWA/offline support in v1

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| UI bridge pattern | WebSocket-only, no REST polling | Real-time state sync (listening/thinking/speaking), metrics every 2s, log streaming. REST adds latency and complexity |
| WS message format | JSON envelope `{type, payload}` | Consistent with existing `DashboardEventBus` pattern; easy to extend |
| React state | Zustand | Lightweight (1KB), no boilerplate, works outside React tree for WebSocket handler |
| 3D orb | Three.js via `@react-three/fiber` | Smooth GPU-accelerated rendering; PyQt6 HUD used `QPainter` — Three.js equivalents for scan rings, particles, pulses |
| Build tool | Vite | Fast HMR, simple config, native ESM |
| Static serving | FastAPI `StaticFiles` + `Mount` in production; Vite proxy to `localhost:7070` in dev | Zero extra infra; same port for API + UI |
| File upload | `react-dropzone` | Replicates PyQt6 drag-and-drop behaviour; sends via WebSocket as base64 or multipart |
| Tunnel | `cloudflared` (recommended) / `pyngrok` (fallback) | cloudflared is free, no auth token needed for basic tunnels; ngrok requires signup |
| `ui_web.py` threading | All WS send calls are thread-safe (`asyncio.run_coroutine_threadsafe`); receive runs in a daemon thread | Must match existing thread-safety assumptions in `_execute_tool()` and action files |

### WebSocket Protocol

```
Client → Server:
  {type: "command", text: "..."}           — text command submission
  {type: "file_upload", name, data, mime}  — file upload
  {type: "mute_toggle"}                     — mute/unmute microphone
  {type: "wake"}                            — manual wake request

Server → Client:
  {type: "state", state: "LISTENING|THINKING|SPEAKING|SLEEPING|MUTED"}
  {type: "log", text: "..."}
  {type: "metrics", cpu, mem, net, gpu, tmp, uptime, procs}
  {type: "transcript", role, text, ts}
  {type: "file_ack", name, size, status}
  {type: "config", gemini_configured, os}
  {type: "setup_required"}
  {type: "error", message}
```

### `ui_web.py` Public API Surface

The replacement must expose these exact properties/methods (matching `JarvisUI`):

```python
class JarvisUI:
    muted: bool
    current_file: str | None
    on_text_command: Callable[[str], None]
    on_wake_request: Callable[[], None]
    audio_analyzer: AudioAnalyzer  # same instance, same thread

    def set_state(self, state: str): ...
    def write_log(self, text: str): ...
    def wait_for_api_key(self): ...
    def start_speaking(self): ...
    def stop_speaking(self): ...
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **WebSocket disconnect during active tool call** — tool completes but UI never sees state update | `ui_web.py` buffers last N state changes and replays on reconnect; tools complete regardless of WS state |
| **Audio pipeline still requires desktop mic/speaker** — browser UI can't replace `sounddevice` | Audio I/O stays in Python; only the visual/log/command UI moves to browser. The browser UI is a companion, not a full replacement for local audio |
| **Multiple browser clients** — state sync conflicts if 2+ tabs open | `ui_web.py` broadcasts to all connected clients; last-writer-wins for commands; mute state is global |
| **`main.py` mainloop change** — `app.exec()` → `uvicorn.run()` is blocking but `JarvisUI.__init__` no longer creates a `QApplication` | `uvicorn.run()` runs in the main thread; all existing threading in `main.py` (JarvisLive runner thread, health daemon, etc.) continues unchanged |
| **Backward compat with action files** — some actions import `QApplication` or access Qt types via `self.ui` | Audit all action files; none currently import Qt directly (they pass `player=self.ui` which is used only for `write_log`, `set_state`, `speak`, `current_file`). `AudioAnalyzer` stays in `ui_web.py` |
| **`wait_for_api_key()` blocks** — replaced by `/setup` page | `JarvisUI.__init__` no longer blocks; instead, the server returns `setup_required` WS message and `/setup` page is served for initial config |
