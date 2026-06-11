## ADDED Requirements

### Requirement: Drop-in JarvisUI replacement
The `ui_web.py` module SHALL expose a `JarvisUI` class with the exact same public API as the current `ui.py` `JarvisUI` class, enabling `main.py` and all action files to use it without modification.

#### Scenario: Properties match PyQt6 JarvisUI
- **WHEN** any action file accesses `player.muted`
- **THEN** `ui_web.JarvisUI.muted` returns a boolean indicating the current mute state
- **WHEN** any action file accesses `player.current_file`
- **THEN** `ui_web.JarvisUI.current_file` returns a `str | None` with the uploaded file path

#### Scenario: Methods match PyQt6 JarvisUI
- **WHEN** any action file calls `player.set_state("SPEAKING")`
- **THEN** the state is stored and broadcast to all WebSocket clients
- **WHEN** any action file calls `player.write_log("You: hello")`
- **THEN** the text is stored in a ring buffer and broadcast to all WebSocket clients

#### Scenario: Callbacks match
- **WHEN** `player.on_text_command` is set to a callable
- **THEN** incoming WebSocket `command` messages invoke that callable
- **WHEN** `player.on_wake_request` is set to a callable
- **THEN** incoming WebSocket `wake` messages invoke that callable

### Requirement: WebSocket state broadcast
The `JarvisUI` SHALL broadcast all UI state changes to connected WebSocket clients in real-time.

#### Scenario: set_state broadcasts
- **WHEN** `set_state("SPEAKING")` is called
- **THEN** a `{"type": "state", "state": "SPEAKING"}` message is sent to all connected WebSocket clients
- **AND** the message is sent within 50ms of the call

#### Scenario: write_log broadcasts
- **WHEN** `write_log("Jarvis: Hello sir")` is called
- **THEN** a `{"type": "log", "text": "Jarvis: Hello sir"}` message is sent to all connected WebSocket clients

#### Scenario: Multiple clients receive broadcast
- **WHEN** 2+ WebSocket clients are connected
- **THEN** each client receives all broadcast messages
- **AND** a client disconnecting does not affect other clients

### Requirement: WebSocket command reception
The `JarvisUI` SHALL receive text commands from WebSocket clients and forward them to `on_text_command`.

#### Scenario: Text command received
- **WHEN** a client sends `{"type": "command", "text": "What's the weather?"}`
- **THEN** `on_text_command("What's the weather?")` is called on a daemon thread

### Requirement: WebSocket file upload reception
The `JarvisUI` SHALL receive file uploads from WebSocket clients, save them to a temporary directory, and expose the path via `current_file`.

#### Scenario: File uploaded via WebSocket
- **WHEN** a client sends a file upload message with name, base64 data, and mime type
- **THEN** the file is saved to `/tmp/cryp-uploads/{uuid}.{ext}`
- **AND** `current_file` returns the saved path
- **AND** an `{"type": "file_ack", "name": "...", "path": "...", "status": "loaded"}` response is sent

### Requirement: Mute toggle via WebSocket
The `JarvisUI` SHALL support mute toggling from WebSocket clients.

#### Scenario: Mute toggled
- **WHEN** a client sends `{"type": "mute_toggle"}`
- **THEN** the `muted` property is toggled
- **AND** a `{"type": "state", "state": "MUTED"}` or `{"type": "state", "state": "LISTENING"}` is broadcast

### Requirement: Thread-safe WebSocket send
All WebSocket `send_text` calls from `JarvisUI` methods (called from action files' thread pool) MUST be thread-safe.

#### Scenario: Thread-safe send from executor
- **WHEN** a tool in `_execute_tool()` calls `self.ui.set_state()` from a thread pool worker
- **THEN** the WebSocket send is dispatched via `asyncio.run_coroutine_threadsafe` to the server's event loop
- **AND** no `RuntimeError` or blocking occurs

### Requirement: Reconnect replay buffer
The `JarvisUI` SHALL maintain a ring buffer of the last N log entries and last state to replay to newly connected WebSocket clients.

#### Scenario: Replay on reconnect
- **WHEN** a WebSocket client connects
- **THEN** the last state is sent immediately
- **AND** the last 20 log entries are replayed in order
