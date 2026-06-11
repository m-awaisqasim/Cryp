# daily-briefing Specification

## Requirements

### Requirement: Daily briefing delivery
The system SHALL generate and speak a daily briefing on the first Cryp startup of each calendar day. The briefing SHALL be delivered before any user interaction.

#### Scenario: First startup of the day
- **WHEN** Cryp starts
- **AND** the current date differs from the last briefing date stored in `memory/last_briefing_date.txt`
- **THEN** the engine generates and speaks the daily briefing
- **AND** writes the current date to `memory/last_briefing_date.txt`

#### Scenario: Subsequent startup on same day
- **WHEN** Cryp restarts on the same calendar day
- **AND** the last briefing date matches the current date
- **THEN** no daily briefing is spoken

#### Scenario: Briefing persists across reconnects
- **WHEN** a session reconnect occurs on the same day
- **THEN** the last briefing date file is checked and no duplicate briefing is delivered

### Requirement: Briefing content composition
The briefing SHALL include: time-aware greeting, current weather, upcoming calendar events, active reminders, recent memory updates since last session, and a system health snapshot.

#### Scenario: Full briefing composition
- **WHEN** the daily briefing fires
- **THEN** the engine composes a message with:
  - Greeting appropriate to time of day (morning/afternoon/evening)
  - Current weather (via `weather_report` with saved city from memory)
  - Count of upcoming reminders for today
  - Recent memory updates (episodic summaries from previous day)
  - System health snapshot (CPU, RAM, disk, battery from system-health-daemon)

#### Scenario: Weather data unavailable
- **WHEN** weather report returns an error or no city is saved in memory
- **THEN** the briefing skips the weather section gracefully

#### Scenario: No reminders
- **WHEN** there are no reminders for today
- **THEN** the briefing skips the reminders section gracefully

### Requirement: Briefing style
The briefing SHALL be spoken in a concise, conversational tone — no more than 3-4 sentences. Detail is available on request.

#### Scenario: Briefing length
- **WHEN** the briefing is spoken
- **THEN** the spoken text SHALL be 3-4 sentences maximum
- **AND** each section SHALL be summarized in a single clause

### Requirement: Briefing opt-out
The system SHALL allow disabling the daily briefing via environment variable.

#### Scenario: Briefing disabled
- **WHEN** `PROACTIVE_BRIEFING_ENABLED=false` is set
- **THEN** no daily briefing is generated or spoken regardless of date
