### Requirement: System shall gather live context at session start
The system SHALL gather live context data every time `_build_config()` is called (i.e., at every session connect/reconnect). Failure to read any individual sensor SHALL NOT prevent session startup — the failed field is silently omitted.

#### Scenario: All sensors available
- **WHEN** `gather_live_context()` is called
- **THEN** it returns a formatted string containing active window title, clipboard preview, battery status, CPU usage, RAM usage, and current date/time

#### Scenario: Clipboard read fails
- **WHEN** `pyperclip.paste()` raises an exception
- **THEN** the clipboard field is omitted from the live context block and session start proceeds normally

#### Scenario: Battery not present (desktop)
- **WHEN** no battery is detected
- **THEN** the battery field is omitted from the live context block

### Requirement: Live context block format
The live context SHALL be formatted as a markdown code block with the header `[LIVE CONTEXT]` containing labeled key-value pairs.

#### Scenario: Formatted output contains all available fields
- **WHEN** `gather_live_context()` produces output
- **THEN** the output SHALL match the format `[LIVE CONTEXT]\nActive Window: <title>\nClipboard: <preview>\nBattery: <percentage>% (<charging state>)\nCPU: <percent>%\nRAM: <used>/<total> GB\nTime: <formatted datetime>\n`

### Requirement: Context injected into system instruction
The live context block SHALL be prepended to the `parts` list in `_build_config()` before memory, episodes, and personality parts.

#### Scenario: Live context appears first in system instruction
- **WHEN** `_build_config()` assembles the system instruction
- **THEN** the live context block SHALL be the first element in the joined parts

### Requirement: Clipboard preview limited to 200 characters
The clipboard preview SHALL be truncated to a maximum of 200 characters. Newlines and control characters SHALL be replaced with spaces to prevent formatting issues.

#### Scenario: Clipboard contains long text
- **WHEN** clipboard content exceeds 200 characters
- **THEN** the preview SHALL contain only the first 200 characters followed by `...`

### Requirement: CPU reading uses non-blocking sampling
The CPU reading SHALL use `psutil.cpu_percent(interval=0.1)` with a maximum 0.5s timeout to avoid delaying session connect.

#### Scenario: CPU reading takes too long
- **WHEN** `psutil.cpu_percent()` blocks longer than 0.5s
- **THEN** the CPU field SHALL be omitted and session continues

### Requirement: Active window detection on Linux
On Linux with X11, active window title SHALL be detected via `xprop -root _NET_ACTIVE_WINDOW` or `python-xlib`. On Wayland, a fallback using `ydotool` or `wlrctl` SHALL be attempted.

#### Scenario: X11 server available
- **WHEN** `DISPLAY` environment variable is set
- **THEN** active window title SHALL be read via X11

#### Scenario: Wayland compositor active
- **WHEN** `WAYLAND_DISPLAY` environment variable is set
- **THEN** active window title SHALL be attempted via Wayland fallback tools

### Requirement: Extended live context for proactive engine
The system SHALL provide an extended `gather_proactive_context()` function that returns a structured dict (not formatted string) containing all live context fields plus additional data needed by the proactive engine: session start timestamp, session uptime, daily app launch events, and active window change log since session start.

#### Scenario: Proactive context gathered
- **WHEN** `gather_proactive_context()` is called
- **THEN** it returns a dict containing: `active_window`, `clipboard`, `battery`, `cpu`, `ram`, `session_started_at`, `session_uptime_seconds`, `app_launches_today` (list of {app_name, timestamp}), `window_changes` (list of {window_title, timestamp})

#### Scenario: Sensor failure handling
- **WHEN** any individual sensor fails (e.g., clipboard read fails)
- **THEN** that field is set to `None` in the returned dict (no exception raised)

#### Scenario: Same-day session tracking
- **WHEN** `gather_proactive_context()` is called
- **THEN** `session_started_at` is the timestamp of the current JarvisLive session start
- **AND** `app_launches_today` and `window_changes` are accumulated across all sessions today (shared state via memory)

### Requirement: Daily aggregation store
The system SHALL maintain a lightweight daily aggregation dict in memory that tracks app launches and window changes across sessions on the same day. The store SHALL be reset at midnight.

#### Scenario: App launch logged
- **WHEN** the user opens an app via the `open_app` tool
- **THEN** the event is logged to the daily aggregation store with app name and current timestamp

#### Scenario: Daily store resets
- **WHEN** the date changes (based on system clock)
- **THEN** the daily aggregation store is cleared
