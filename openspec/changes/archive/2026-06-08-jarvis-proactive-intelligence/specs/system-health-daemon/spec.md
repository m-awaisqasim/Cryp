## ADDED Requirements

### Requirement: Health snapshot API
The system SHALL expose a `get_health_snapshot()` function that returns the current system health state as a structured dict. This SHALL be callable by the proactive engine and daily briefing without duplicating health monitoring logic.

#### Scenario: Snapshot returns current metrics
- **WHEN** `get_health_snapshot()` is called
- **THEN** it returns a dict with: `cpu_percent`, `ram_percent`, `ram_used_gb`, `ram_total_gb`, `disk_percent`, `battery_percent`, `battery_plugged`, `last_check_timestamp`

#### Scenario: Snapshot during daemon idle
- **WHEN** `get_health_snapshot()` is called between daemon check intervals
- **THEN** it returns the most recently collected metrics (stale data is acceptable; proactive engine runs on ~1s timescale, not sub-second)

### Requirement: Alert history for anomaly cross-reference
The system SHALL maintain an in-memory list of the last N health alerts (default: 50) with timestamp, metric name, and value. The proactive engine SHALL query this history to avoid duplicating anomaly alerts.

#### Scenario: Alert recorded
- **WHEN** the daemon speaks a CPU, RAM, disk, or battery alert
- **THEN** the alert is appended to the alert history with `{timestamp, metric, value, message}`

#### Scenario: Alert history query
- **WHEN** the proactive engine calls `get_alert_history(minutes_back=30)`
- **THEN** it receives alerts from the last 30 minutes

#### Scenario: Alert history bounded
- **WHEN** the alert history exceeds 50 entries
- **THEN** the oldest entries are dropped
