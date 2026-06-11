## Why

The current PyQt6 desktop GUI (`ui.py`) is tightly coupled to the Python process, preventing remote access, mobile use, and modern frontend capabilities. Moving to a browser-based UI enables phone access from the same WiFi network, tunnel-based remote access, over-the-air updates, and a richer HUD-style interface without platform-specific GUI frameworks.

## What Changes

- **BREAKING**: Delete `ui.py` entirely (PyQt6, `HudCanvas`, `MetricBar`, `LogWidget`, `SetupOverlay`, `MainWindow`, `CrypUI` class)
- **NEW**: Create `ui_web.py` — a drop-in replacement for the `CrypUI` class with identical public API (`muted`, `current_file`, `on_text_command`, `on_wake_request`, `set_state`, `write_log`, `wait_for_api_key`, `audio_analyzer`) — routing all `self.ui.*` calls through WebSocket to connected browser clients
- **NEW**: Build `dashboard/frontend/` — a Vite + React 18 SPA with HUD-style dark interface (cyan/teal aesthetic), live-transcript panel, rotating 3D orb, animated scan rings, system metric gauges, file upload, command input, and log viewer
- **MODIFY**: `dashboard/server.py` — FastAPI serves built static files in production, retains WebSocket `/ws` endpoint, adds WebSocket events for all `CrypUI` methods (`set_state`, `write_log`, `update_metrics`, `mute_toggle`, `file_dropped`, `command_submitted`)
- **MODIFY**: `main.py` — import `CrypUI` from `ui_web` instead of `ui`; `wait_for_api_key()` replaced by inline overlay served at `<host>/setup`; `self.ui.root.mainloop()` becomes `uvicorn.run()` blocking call
- **NEW**: Tunnel support — optional `--tunnel` flag using `pyngrok` or `cloudflared` for public URL
- **NEW**: `dashboard/frontend/package.json` with React, Vite, Zustand, three.js (orb), recharts (sparklines)

## Capabilities

### New Capabilities
- `web-hud-interface`: Full React SPA replacing PyQt6 HUD — rotating orb, animated scan rings, status states, particles, data bits, radial waveform
- `websocket-ui-bridge`: `ui_web.py` as a drop-in `CrypUI` replacement routing all UI calls over WebSocket to browser clients
- `phone-remote-access`: UI accessible from mobile devices on same LAN and via tunnel (ngrok/cloudflared) for outside access
- `file-upload-web`: Drag-and-drop file upload in browser replacing PyQt6 `FileDropZone`

### Modified Capabilities
- `web-dashboard`: Upgraded from a simple static HTML page to a full React SPA served by the same FastAPI server, with richer HUD visuals, bidirectional WebSocket communication, and mobile-responsive layout

## Impact

- **Deleted**: `ui.py` (2088 lines) — entire PyQt6 codebase removed
- **New files**: `ui_web.py`, `dashboard/frontend/` (Vite + React project scaffold)
- **Modified**: `dashboard/server.py` (static file serving, expanded WS events), `main.py` (import swap, `mainloop()` → `uvicorn.run()`), `requirements.txt` (remove `pyqt6`, add `pyngrok`/`cloudflared`), `package.json` (devDependencies), `openspec/context.md` (Phase 7 marked complete)
- **Dependencies added**: React, Vite, Zustand, three.js, recharts, `python-multipart`
- **Dependencies removed**: `PyQt6`
- **Env**: New optional env vars `DASHBOARD_PORT`, `TUNNEL_ENABLED`, `TUNNEL_PROVIDER`
