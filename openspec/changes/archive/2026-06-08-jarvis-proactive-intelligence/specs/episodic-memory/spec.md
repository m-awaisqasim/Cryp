## ADDED Requirements

### Requirement: Cross-session pattern query interface
The system SHALL provide a `query_patterns(days_back=7)` helper that aggregates episodic summaries across sessions and returns structured data suitable for pattern detection: per-session timestamps, tool usage counts per session, and topic frequency across sessions.

#### Scenario: Pattern query returns session timeline
- **WHEN** `query_patterns(days_back=7)` is called
- **THEN** it returns a list of sessions with `started_at`, `ended_at`, `tools_used` (list of tool names), `topics` (list), and `summary` for each session within the last 7 days

#### Scenario: No sessions in range
- **WHEN** `query_patterns(days_back=7)` is called
- **AND** there are no episodes in the last 7 days
- **THEN** an empty list is returned

#### Scenario: Pattern query limited to N days
- **WHEN** `query_patterns(days_back=30)` is called
- **THEN** sessions from the last 30 days are included

### Requirement: Procedural memory namespace for patterns
The system SHALL support a `patterns/` namespace in the flat key-value memory store for storing detected patterns. The namespace SHALL be managed via the existing `update_memory()` and `load_memory()` APIs without schema changes.

#### Scenario: Pattern stored in patterns namespace
- **WHEN** `update_memory("patterns", "time_based_0900", value_dict)` is called
- **THEN** the entry is stored under the `patterns` key in `long_term.json`
- **AND** it is retrievable via `load_memory()["patterns"]`

#### Scenario: Existing categories untouched
- **WHEN** patterns are stored
- **THEN** the existing six categories (`identity`, `preferences`, `projects`, `relationships`, `wishes`, `notes`) are unchanged
