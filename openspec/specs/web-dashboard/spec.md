## ADDED Requirements

### Requirement: Dashboard server serves SPA at localhost:7070
The system SHALL start a FastAPI HTTP server on `127.0.0.1:7070` that serves a single-page HTML dashboard at the root endpoint (`/`).

#### Scenario: Server starts on application launch
- **WHEN** `main()` executes
- **THEN** a daemon thread starts running `uvicorn` on `127.0.0.1:7070`
- **AND** the dashboard is reachable at `http://localhost:7070`

#### Scenario: Server does not block main threads
- **WHEN** the dashboard server is running
- **THEN** the PyQt6 event loop on the main thread is not blocked
- **AND** the JarvisLive asyncio event loop in its daemon thread is not blocked

### Requirement: Real-time updates via WebSocket
The server SHALL expose a WebSocket endpoint at `/ws` that pushes live state updates to all connected clients.

#### Scenario: Client connects to WebSocket
- **WHEN** a browser opens a WebSocket connection to `ws://localhost:7070/ws`
- **THEN** the server accepts the connection and subscribes it to the event bus
- **AND** the server sends the last 20 transcript lines as an initial replay

#### Scenario: Client disconnects
- **WHEN** a WebSocket client disconnects
- **THEN** the server removes the client subscription and cleans up resources

### Requirement: Live conversation transcript
The dashboard SHALL display a scrolling, auto-updating transcript of the conversation between the user and Jarvis.

#### Scenario: User speaks
- **WHEN** `JarvisLive` logs "You: {text}" via `write_log`
- **THEN** the event bus publishes a `{"type": "transcript", "role": "user", "text": "..."}` message
- **AND** all connected WebSocket clients receive it
- **AND** the dashboard appends it to the transcript panel

#### Scenario: Jarvis responds
- **WHEN** `JarvisLive` logs "Jarvis: {text}" via `write_log`
- **THEN** the event bus publishes a `{"type": "transcript", "role": "jarvis", "text": "..."}` message
- **AND** all connected WebSocket clients receive it
- **AND** the dashboard appends it to the transcript panel

#### Scenario: System message logged
- **WHEN** `JarvisLive` logs "SYS: {text}" via `write_log`
- **THEN** the event bus publishes a `{"type": "transcript", "role": "system", "text": "..."}` message
- **AND** the dashboard appends it to the transcript panel

### Requirement: Assistant state display
The dashboard SHALL display the current assistant state (LISTENING, THINKING, SPEAKING, SLEEPING, MUTED).

#### Scenario: State changes
- **WHEN** JarvisLive transitions to a new state
- **THEN** the event bus publishes a `{"type": "state", "state": "LISTENING"}` message
- **AND** the dashboard updates the state indicator

### Requirement: Memory explorer
The dashboard SHALL display a read-only view of the assistant's persistent memory (key-value facts).

#### Scenario: Initial memory snapshot on connect
- **WHEN** a WebSocket client connects
- **THEN** the server reads the current memory via `load_memory()`
- **AND** sends a `{"type": "memory", "data": {...}}` message with all key-value pairs

#### Scenario: Memory updated
- **WHEN** `update_memory()` is called in `memory_manager.py`
- **THEN** the event bus publishes a `{"type": "memory", "data": {...}}` message with the full updated memory dict
- **AND** all connected WebSocket clients receive it

### Requirement: Active ReAct task status
The dashboard SHALL display the current or most recent ReAct task: goal, current step, total steps, and latest result.

#### Scenario: ReAct task starts
- **WHEN** a new `agent_task` tool call creates a ReAct loop
- **THEN** the event bus publishes a `{"type": "react", "status": "running", "goal": "...", "step": 0, "total": N}` message

#### Scenario: ReAct step completes
- **WHEN** a step in the ReAct loop finishes
- **THEN** the event bus publishes a `{"type": "react", "status": "running", "goal": "...", "step": n, "total": N, "result": "..."}` message

#### Scenario: ReAct task completes
- **WHEN** the ReAct loop finishes all steps or is cancelled
- **THEN** the event bus publishes a `{"type": "react", "status": "completed"}` or `{"type": "react", "status": "cancelled"}` message

### Requirement: System stats panel
The dashboard SHALL display real-time system health metrics: CPU, RAM, disk, and battery.

#### Scenario: Stats update
- **WHEN** `SystemHealthDaemon` checks metrics
- **THEN** the event bus publishes a `{"type": "stats", "data": {"cpu": ..., "ram": ..., "disk": ..., "battery": ...}}` message
- **AND** all connected WebSocket clients receive it
- **AND** the dashboard updates the stats panel

### Requirement: Event bus integration
The system SHALL provide a `DashboardEventBus` class that collects state updates from `JarvisLive` and `SystemHealthDaemon` and broadcasts them to WebSocket subscribers.

#### Scenario: Thread-safe publish from sync context
- **WHEN** `publish(event)` is called from a sync (non-async) thread
- **THEN** the event is enqueued to all subscriber queues using `asyncio.run_coroutine_threadsafe`
- **AND** no subscribers block the publishing thread

#### Scenario: Multiple subscribers
- **WHEN** two WebSocket clients are connected simultaneously
- **THEN** each client receives all events independently
- **AND** one client disconnecting does not affect the other

### Requirement: No changes to PyQt6 UI
The dashboard feature SHALL NOT require any modifications to `JarvisUI`, `MainWindow`, `HudCanvas`, or any other class in `ui.py`.

#### Scenario: Existing UI unchanged
- **WHEN** the dashboard server starts
- **THEN** the PyQt6 window renders identically to before the change
- **AND** all pyqtSignals, timers, and event handlers continue to function

### Requirement: No interface changes to JarvisLive
The dashboard feature SHALL NOT require any changes to `JarvisLive`'s public methods, constructor signature, tool dispatch, or state machine.

#### Scenario: JarvisLive public API stable
- **WHEN** `JarvisLive` is instantiated with the same `(ui: JarvisUI)` signature
- **THEN** all existing callers and tests continue to work without modification
