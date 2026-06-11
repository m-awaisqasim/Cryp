## 1. Frontend Scaffold — Vite + React + Dependencies

- [ ] 1.1 Create `dashboard/frontend/` with `npm create vite@latest` (React + TypeScript template)
- [ ] 1.2 Install dependencies: `react`, `zustand`, `three`, `@react-three/fiber`, `@react-three/drei`, `react-dropzone`, `recharts`
- [ ] 1.3 Install dev deps: `@types/three`, `tailwindcss`, `postcss`, `autoprefixer`
- [ ] 1.4 Configure Vite proxy: dev server proxies `/ws` and `/api/*` to `localhost:7070`
- [ ] 1.5 Create `tailwind.config.js` with cyan/teal dark theme palette matching PyQt6 `class C`
- [ ] 1.6 Set up directory structure: `src/components/`, `src/stores/`, `src/hooks/`, `src/types/`

## 2. WebSocket Store — Zustand State Management

- [ ] 2.1 Create `src/stores/wsStore.ts` — Zustand store for WebSocket connection, auto-reconnect with exponential backoff
- [ ] 2.2 Implement message dispatch: `state`, `log`, `transcript`, `metrics`, `file_ack`, `config`, `setup_required`, `error`
- [ ] 2.3 Implement outgoing messages: `command`, `file_upload`, `mute_toggle`, `wake`
- [ ] 2.4 Create `src/stores/appStore.ts` — Zustand store for UI state: currentState, transcript log, metrics, file info, wake/speak flags

## 3. HUD Orb — Three.js 3D Central Component

- [ ] 3.1 Create `src/components/HudOrb.tsx` — React Three Fiber Canvas with rotating orb mesh
- [ ] 3.2 Implement concentric arc rings that spin at different speeds (matching `_rings` in `HudCanvas._step`)
- [ ] 3.3 Implement scanner arcs with glow trail (matching `_scan`, `_scan2`)
- [ ] 3.4 Implement pulsing halo glow with 12 concentric circles (matching `paintEvent` halo)
- [ ] 3.5 Implement pulse ring expansion effect (matching `_pulses`)
- [ ] 3.6 Implement ambient particle burst system for speaking state (matching `_particles`)
- [ ] 3.7 Implement floating hex data bits (matching `_data_bits`)
- [ ] 3.8 Implement sparkle particles (matching `_sparkles`)
- [ ] 3.9 Implement radial waveform bars around orb (matching circular waveform in `HudCanvas`)
- [ ] 3.10 Implement tick marks (degree markers) around perimeter
- [ ] 3.11 Implement corner brackets decoration
- [ ] 3.12 Animate orb state transitions: pulse rate, halo size, color shifts for LISTENING/THINKING/SPEAKING/MUTED/SLEEPING

## 4. Header & Status Bar

- [ ] 4.1 Create `src/components/Header.tsx` — Cryp logo, J.A.R.V.I.S title, pulsing status dot, state badge, clock
- [ ] 4.2 Implement clock with colon pulse animation (matching PyQt6 `_tick_clock`)
- [ ] 4.3 Implement status dot with color transitions: green (LISTENING), amber (THINKING), orange (SPEAKING), magenta (MUTED), dim (SLEEPING)
- [ ] 4.4 Implement connection indicator (WebSocket online/offline dot)

## 5. System Metrics Panel — Gauges & Sparklines

- [ ] 5.1 Create `src/components/MetricsPanel.tsx` — CPU, MEM, NET, GPU, TEMP metric bars with labels
- [ ] 5.2 Implement animated arc gauges for CPU, RAM, DISK, BAT (matching PyQt6 gauge styling)
- [ ] 5.3 Implement sparkline history charts using Recharts for last 30 readings
- [ ] 5.4 Implement uptime and process count labels
- [ ] 5.5 Add color thresholds: green <60%, orange 60-85%, red >85%

## 6. Transcript Panel

- [ ] 6.1 Create `src/components/TranscriptPanel.tsx` — scrolling log with role-based coloring (You→cyan, Jarvis→green, SYS→amber)
- [ ] 6.2 Implement auto-scroll to bottom on new entry
- [ ] 6.3 Add clear button and timestamp toggle
- [ ] 6.4 Cap at 300 entries with FIFO eviction

## 7. File Upload — Drag-and-Drop Zone

- [ ] 7.1 Create `src/components/FileDropZone.tsx` with `react-dropzone`
- [ ] 7.2 Implement drag-over glow animation, idle bounce animation
- [ ] 7.3 Implement file upload via WebSocket (base64 encode, send `file_upload` message)
- [ ] 7.4 Implement file info display: type icon, filename, extension + size, directory path
- [ ] 7.5 Implement clear file button ("✕")
- [ ] 7.6 Implement click-to-browse fallback

## 8. Command Input

- [ ] 8.1 Create `src/components/CommandInput.tsx` — text input with cyan focus border
- [ ] 8.2 Implement Enter-to-send + send button
- [ ] 8.3 Wire to wsStore to emit `command` message
- [ ] 8.4 Implement wake button

## 9. Mute Toggle Button

- [ ] 9.1 Create `src/components/MuteButton.tsx` — microphone active/muted states with green/magenta styling
- [ ] 9.2 Wire click to wsStore `mute_toggle` message

## 10. Setup Overlay

- [ ] 10.1 Create `src/components/SetupOverlay.tsx` — initial config form for API key and OS selection
- [ ] 10.2 Implement POST to `/api/setup` on form submit
- [ ] 10.3 Show overlay when `setup_required` WS message received or `GET /api/config` returns unconfigured

## 11. Log Viewer Panel

- [ ] 11.1 Create `src/components/LogViewer.tsx` — fetch logs from `/api/logs?lines=100`, poll every 5s
- [ ] 11.2 Implement log level filter dropdown (ALL, INFO, WARNING, ERROR, DEBUG)
- [ ] 11.3 Color-code log lines by level

## 12. Main App Shell & Layout

- [ ] 12.1 Create `src/App.tsx` — grid layout: left panel (metrics), center (orb), right panel (transcript + file + command + mute)
- [ ] 12.2 Implement responsive grid: single column on mobile (<768px), 2-column on tablet, full HUD grid on desktop
- [ ] 12.3 Add animated background grid dots (matching `_bg_grid_offset` animation)
- [ ] 12.4 Add scanline overlay effect (matching existing dashboard `body::before`)
- [ ] 12.5 Add footer with shortcuts hint ([F4] Mute · [F11] Fullscreen) and version label

## 13. ui_web.py — Drop-in JarvisUI Replacement

- [ ] 13.1 Create `ui_web.py` with `JarvisUI` class exposing same public API as PyQt6 version
- [ ] 13.2 Implement WebSocket manager: accept connections, broadcast state/log/metrics, maintain subscriber list
- [ ] 13.3 Implement thread-safe send via `asyncio.run_coroutine_threadsafe` for calls from executor threads
- [ ] 13.4 Implement incoming message handler: `command` → `on_text_command`, `mute_toggle` → toggle muted, `wake` → `on_wake_request`, `file_upload` → save to `/tmp/cryp-uploads/` and set `current_file`
- [ ] 13.5 Implement reconnect replay buffer: store last 20 log entries + last state, send on new WS connection
- [ ] 13.6 Wire `set_state()` to broadcast `{"type": "state", "state": "..."}` to all clients
- [ ] 13.7 Wire `write_log()` to broadcast `{"type": "log", "text": "..."}` to all clients
- [ ] 13.8 Port `AudioAnalyzer` class from `ui.py` to `ui_web.py` (no Qt dependencies)
- [ ] 13.9 Implement `wait_for_api_key()` — non-blocking, returns immediately; server serves `/setup` instead
- [ ] 13.10 Add metrics broadcast loop (every 2s) using `_SysMetrics` snapshots

## 14. dashboard/server.py — React SPA Serving + Expanded WS

- [ ] 14.1 Add `StaticFiles` mount for production: mount `dashboard/frontend/dist/` at `/`
- [ ] 14.2 Add `GET /api/config` — returns `{gemini_configured: bool, os: str}`
- [ ] 14.3 Add `POST /api/setup` — writes `.env` with API key and OS selection
- [ ] 14.4 Add `GET /api/stats` — returns latest `_SysMetrics` snapshot for polling fallback
- [ ] 14.5 Enable CORS middleware for tunnel domains
- [ ] 14.6 Integrate `ui_web.py` WebSocket manager with FastAPI lifespan

## 15. main.py — Import Swap & Server Integration

- [ ] 15.1 Change `from ui import JarvisUI` to `from ui_web import JarvisUI`
- [ ] 15.2 Remove `ui.root.mainloop()` — replace with `uvicorn.run(app, ...)` blocking call that also starts the WS server
- [ ] 15.3 Ensure `JarvisLive` daemon thread starts before `uvicorn.run()`
- [ ] 15.4 Update `main.py` to accept `--tunnel` CLI arg and `TUNNEL_ENABLED` env var

## 16. Tunnel Support — Remote Access

- [ ] 16.1 Add `cloudflared` tunnel support: spawn subprocess `cloudflared tunnel --url http://localhost:7070`
- [ ] 16.2 Add `pyngrok` fallback tunnel support
- [ ] 16.3 Log tunnel URL to console and broadcast via WebSocket `tunnel_url` message
- [ ] 16.4 Add `TUNNEL_PROVIDER` env var (cloudflared | ngrok | none)

## 17. Cleanup — Remove PyQt6 + Verification

- [ ] 17.1 Delete `ui.py` after verifying `ui_web.py` works with all action files
- [ ] 17.2 Remove `PyQt6` from `requirements.txt`
- [ ] 17.3 Verify `pip install` succeeds without PyQt6
- [ ] 17.4 Run full test suite: `pytest tests/` — all tests pass
- [ ] 17.5 Verify `npm run build` produces `dashboard/frontend/dist/`
- [ ] 17.6 Verify end-to-end: start Cryp, open browser to `localhost:7070`, see HUD, send command, see transcript and state updates
- [ ] 17.7 Update `openspec/context.md` Phase 7 → COMPLETE ✅

## 18. Documentation & Configuration

- [ ] 18.1 Update `.env.example` with new env vars: `DASHBOARD_PORT`, `TUNNEL_ENABLED`, `TUNNEL_PROVIDER`
- [ ] 18.2 Add `python-multipart` to `requirements.txt`
- [ ] 18.3 Update `package.json` scripts: add `dev:dashboard` and `build:dashboard` scripts
- [ ] 18.4 Add run instructions for development mode (Vite proxy) to `run.txt`
