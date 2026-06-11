## ADDED Requirements

### Requirement: Inactivity timeout sleep
The system SHALL monitor user and AI interaction activity and automatically transition CrypLive to SLEEPING state after a configurable period of inactivity.

#### Scenario: Timeout triggers sleep
- **WHEN** no user speech is received AND no AI speech is played for `HOTWORD_TIMEOUT` seconds
- **THEN** the system SHALL gracefully tear down the Gemini session and enter SLEEPING state

#### Scenario: Activity resets timeout
- **WHEN** the user speaks (input transcription received) OR the AI speaks (output audio played)
- **THEN** the inactivity timer SHALL be reset to zero

#### Scenario: Sleep during user speech
- **WHEN** the user is mid-sentence (no turn_complete received yet) at the timeout boundary
- **THEN** the system SHALL wait for turn_complete before entering SLEEPING, to avoid cutting off the user

### Requirement: Session state management
The system SHALL track and expose three states: SLEEPING, TRIGGERED, ACTIVE.

#### Scenario: State transitions
- **WHEN** `main.py` starts → state SHALL be SLEEPING
- **WHEN** wake word is detected → state SHALL transition to TRIGGERED
- **WHEN** Gemini session is fully connected → state SHALL transition to ACTIVE
- **WHEN** timeout expires → state SHALL transition back to SLEEPING

### Requirement: Configurable timeout
The inactivity timeout SHALL be configurable via environment variable `HOTWORD_TIMEOUT` (integer seconds, default 300) and optionally overridable in `config/api_keys.json`.

#### Scenario: Default timeout applied
- **WHEN** no `HOTWORD_TIMEOUT` env var is set and no `hotword_timeout` key exists in config
- **THEN** the timeout SHALL default to 300 seconds

#### Scenario: Env var override
- **WHEN** `HOTWORD_TIMEOUT=600` is set as an environment variable
- **THEN** the timeout SHALL be 600 seconds

#### Scenario: Invalid value
- **WHEN** `HOTWORD_TIMEOUT` is set to a non-positive integer or non-numeric value
- **THEN** the system SHALL fall back to the default of 300 seconds and log a warning

### Requirement: Graceful session teardown on sleep
When entering SLEEPING state, any in-progress session episode SHALL be finalized and saved to memory.

#### Scenario: Episode saved before sleep
- **WHEN** CrypLive transitions from ACTIVE to SLEEPING
- **THEN** `_finalize_session_episode("sleep_timeout")` SHALL be called to save the episode
