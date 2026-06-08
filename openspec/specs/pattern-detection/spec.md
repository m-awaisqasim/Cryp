# pattern-detection Specification

## Requirements

### Requirement: Periodic pattern scan
The system SHALL periodically scan episodic memory to detect behavioral patterns. The scan interval SHALL be configurable (default: 1 hour). The scan SHALL run as a subtask of the ProactiveEngine.

#### Scenario: Pattern scan runs on schedule
- **WHEN** `PROACTIVE_PATTERN_SCAN_INTERVAL` seconds have elapsed since the last scan
- **THEN** the engine triggers a pattern detection scan
- **AND** the scan queries episodic memory summaries from the last 7 days

#### Scenario: First scan after startup
- **WHEN** the engine starts
- **THEN** a pattern scan runs immediately (no delay for initial patterns)

### Requirement: Time-based pattern detection
The system SHALL detect patterns where the user consistently performs the same action at the same time of day or day of week.

#### Scenario: Detects time-based pattern
- **WHEN** episodic memory shows the user opened "Chrome" at 9:00-9:15 AM on 3+ weekdays in the last 7 days
- **THEN** the engine stores a procedural memory entry: `patterns/time_based: { action: "open_app Chrome", time: "09:00", days: "weekdays", confidence: 0.85 }`

#### Scenario: Low-frequency pattern ignored
- **WHEN** an action appears at a given time fewer than 3 times
- **THEN** no pattern is stored for that action-time combination

### Requirement: Frequency-based pattern detection
The system SHALL track the most frequently used applications per time block and day of week.

#### Scenario: Detects top apps
- **WHEN** the scan runs
- **THEN** it computes top 3 most-used applications for each: morning (6-12), afternoon (12-18), evening (18-24)
- **AND** stores the result as procedural memory: `patterns/top_apps: { morning: ["Chrome", "Terminal", "VS Code"], ... }`

### Requirement: Pattern storage
All detected patterns SHALL be stored as procedural memory entries using the existing `memory_manager.py` API.

#### Scenario: Pattern stored in memory
- **WHEN** a pattern is detected
- **THEN** `update_memory("patterns/...", pattern_data)` is called silently
- **AND** the pattern is available for future queries (suggestions, anomaly baseline)

#### Scenario: Pattern updated on new detection
- **WHEN** a pattern scan detects a pattern that already exists
- **THEN** the existing entry is updated with new confidence and timestamp
