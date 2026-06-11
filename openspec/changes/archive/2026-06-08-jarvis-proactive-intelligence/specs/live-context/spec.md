## ADDED Requirements

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
- **THEN** `session_started_at` is the timestamp of the current CrypLive session start
- **AND** `app_launches_today` and `window_changes` are accumulated across all sessions today (shared state via memory)

### Requirement: Daily aggregation store
The system SHALL maintain a lightweight daily aggregation dict in memory that tracks app launches and window changes across sessions on the same day. The store SHALL be reset at midnight.

#### Scenario: App launch logged
- **WHEN** the user opens an app via the `open_app` tool
- **THEN** the event is logged to the daily aggregation store with app name and current timestamp

#### Scenario: Daily store resets
- **WHEN** the date changes (based on system clock)
- **THEN** the daily aggregation store is cleared
