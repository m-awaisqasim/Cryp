## ADDED Requirements

### Requirement: Background system health monitoring
The system SHALL run a background async task that periodically monitors CPU usage, RAM usage, disk usage, and battery level at a configurable interval.

#### Scenario: Daemon starts with JarvisLive
- **WHEN** `JarvisLive.run()` creates the `TaskGroup`
- **THEN** a 6th task is created that runs `SystemHealthDaemon.run()`
- **AND** the daemon task does not block the other 5 tasks

#### Scenario: Daemon stops on session disconnect
- **WHEN** the Gemini Live session disconnects and the TaskGroup exits
- **THEN** the daemon task is cancelled cleanly via `CancelledError`

#### Scenario: Daemon resumes on reconnect
- **WHEN** a new session connects and a new TaskGroup is created
- **THEN** a fresh daemon task starts with the new task group

### Requirement: CPU threshold alert
The system SHALL monitor CPU usage percent and speak an alert when it exceeds the configured threshold for 2 consecutive checks.

#### Scenario: CPU exceeds threshold
- **WHEN** `psutil.cpu_percent(interval=0)` returns a value >= `HEALTH_CPU_THRESHOLD` (default 90)
- **AND** the previous check also exceeded the threshold
- **AND** the debounce cooldown has elapsed
- **THEN** the daemon calls `speak("Sir, CPU is at X percent.")` and `write_log("ALERT: CPU at X%")`

#### Scenario: CPU returns below threshold
- **WHEN** CPU percent drops below 90
- **THEN** no alert is spoken
- **AND** the 2-consecutive-check counter resets

### Requirement: RAM threshold alert
The system SHALL monitor RAM usage percent and speak an alert when it exceeds the configured threshold for 2 consecutive checks.

#### Scenario: RAM exceeds threshold
- **WHEN** `psutil.virtual_memory().percent` returns a value >= `HEALTH_RAM_THRESHOLD` (default 85)
- **AND** the previous check also exceeded the threshold
- **AND** the debounce cooldown has elapsed
- **THEN** the daemon calls `speak("Sir, memory is at X percent.")` and `write_log("ALERT: RAM at X%")`

### Requirement: Disk threshold alert
The system SHALL monitor disk usage percent on the root filesystem and speak an alert when it exceeds the configured threshold for 2 consecutive checks.

#### Scenario: Disk exceeds threshold
- **WHEN** `psutil.disk_usage('/').percent` returns a value >= `HEALTH_DISK_THRESHOLD` (default 90)
- **AND** the previous check also exceeded the threshold
- **AND** the debounce cooldown has elapsed
- **THEN** the daemon calls `speak("Sir, disk is at X percent.")` and `write_log("ALERT: Disk at X%")`

### Requirement: Battery threshold alert
The system SHALL monitor battery level when discharging and speak an alert when it drops below the configured threshold.

#### Scenario: Battery low and discharging
- **WHEN** `psutil.sensors_battery()` returns a valid result
- **AND** `power_plugged` is `False`
- **AND** `percent` <= `HEALTH_BATTERY_THRESHOLD` (default 20)
- **AND** the debounce cooldown has elapsed
- **THEN** the daemon calls `speak("Sir, battery is at X percent.")` and `write_log("ALERT: Battery at X%")`

#### Scenario: No battery detected
- **WHEN** `psutil.sensors_battery()` returns `None` (desktop without battery)
- **THEN** battery monitoring is silently skipped

#### Scenario: Battery charging
- **WHEN** `psutil.sensors_battery()` returns a result with `power_plugged` set to `True`
- **THEN** no battery alert is spoken regardless of percentage

### Requirement: Configurable thresholds
The system SHALL allow all thresholds and the check interval to be configured via environment variables with sensible defaults.

#### Scenario: Default configuration
- **WHEN** no environment variables are set
- **THEN** the daemon uses: `HEALTH_CHECK_INTERVAL=60`, `HEALTH_CPU_THRESHOLD=90`, `HEALTH_RAM_THRESHOLD=85`, `HEALTH_DISK_THRESHOLD=90`, `HEALTH_BATTERY_THRESHOLD=20`, `HEALTH_DEBOUNCE_SECONDS=300`

#### Scenario: Custom configuration
- **WHEN** `HEALTH_CHECK_INTERVAL=30` is set
- **THEN** the daemon checks every 30 seconds instead of 60

### Requirement: Alert debouncing
The system SHALL prevent repeated alerts for the same metric within a configurable cooldown period.

#### Scenario: Repeated high CPU
- **WHEN** CPU exceeds threshold at check 1 → alert fires
- **AND** CPU still exceeds threshold at check 2 (60s later)
- **AND** less than `HEALTH_DEBOUNCE_SECONDS` (default 300s) has elapsed since the last alert
- **THEN** no alert is spoken

#### Scenario: Cooldown expires
- **WHEN** CPU exceeded threshold and alerted at T=0
- **AND** CPU still exceeds threshold at T=300
- **THEN** a new alert is spoken
