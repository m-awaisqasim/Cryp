## ADDED Requirements

### Requirement: React SPA replaces static HTML
The dashboard SHALL be served as a Vite-built React 18 SPA instead of a single static HTML file. In production, FastAPI mounts the built `dist/` directory as static files.

#### Scenario: Production serves built SPA
- **WHEN** a browser requests `GET /`
- **THEN** FastAPI serves `dashboard/frontend/dist/index.html`
- **AND** all static assets (JS, CSS, fonts) are served from `dashboard/frontend/dist/`

#### Scenario: Development uses Vite proxy
- **WHEN** `DASHBOARD_DEV=true` is set
- **THEN** the Vite dev server runs on `localhost:5173`
- **AND** API/WebSocket requests are proxied to `localhost:7070`

### Requirement: Command input via WebSocket
The SPA SHALL provide a text input field that sends commands to the assistant via WebSocket.

#### Scenario: Text command sent
- **WHEN** the user types a command and presses Enter
- **THEN** a `{"type": "command", "text": "..."}` message is sent via WebSocket
- **AND** the input field is cleared
- **AND** the command appears in the transcript as "You: ..."

### Requirement: Wake button
The SPA SHALL provide a manual wake button to trigger wake word detection when in sleeping state.

#### Scenario: Wake button clicked
- **WHEN** the user clicks the wake button
- **THEN** a `{"type": "wake"}` message is sent via WebSocket
- **AND** the state transitions from SLEEPING

### Requirement: Setup page for initial config
The FastAPI server SHALL serve a `/setup` page for initial Gemini API key and OS configuration when `.env` is not configured.

#### Scenario: Setup page served when unconfigured
- **WHEN** `GEMINI_API_KEY` is not set in `.env`
- **THEN** `GET /setup` returns an initial configuration form
- **AND** submitting the form writes `.env` and restarts the server

#### Scenario: Setup form submission
- **WHEN** the user submits the setup form with API key and OS selection
- **THEN** a POST to `/api/setup` writes the `.env` file
- **AND** returns `{"status": "ok"}`
- **AND** the UI transitions to the main HUD

### Requirement: Live metrics panel with sparklines
The SPA SHALL render real-time system metrics with animated arc gauges and sparkline history charts.

#### Scenario: Metrics received via WebSocket
- **WHEN** a `{"type": "metrics", "cpu": 45, "mem": 62, ...}` message arrives
- **THEN** the arc gauges animate to the new values
- **AND** sparkline history charts update with the latest reading
- **AND** uptime and process count labels update

#### Scenario: Metrics polling fallback
- **WHEN** WebSocket is not connected
- **THEN** the SPA polls `GET /api/stats` every 10s as a fallback

### Requirement: Log viewer panel
The SPA SHALL display a scrollable log viewer with level filtering similar to the current dashboard.

#### Scenario: Logs displayed on connect
- **WHEN** the SPA connects
- **THEN** it fetches `GET /api/logs?lines=100` for initial log display
- **AND** polls every 5s for new logs

#### Scenario: Log level filtering
- **WHEN** the user selects "ERROR" from the log level filter
- **THEN** only log lines containing `|ERROR|` are shown
