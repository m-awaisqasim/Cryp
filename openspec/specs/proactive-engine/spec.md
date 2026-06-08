# proactive-engine Specification

## Requirements

### Requirement: Background proactive engine task
The system SHALL run a `ProactiveEngine` async background task that orchestrates all proactive features (daily briefing, pattern detection, anomaly detection, contextual suggestions). The engine SHALL be launched as a 5th concurrent task in the `JarvisLive` TaskGroup alongside listen/send/receive/play.

#### Scenario: Engine starts with JarvisLive
- **WHEN** `JarvisLive.run()` creates the TaskGroup
- **THEN** a `ProactiveEngine` task is created and started
- **AND** the engine task does not block the other 4 tasks

#### Scenario: Engine stops on session disconnect
- **WHEN** the Gemini Live session disconnects and the TaskGroup exits
- **THEN** the proactive engine task is cancelled cleanly via `CancelledError`

#### Scenario: Engine resumes on reconnect
- **WHEN** a new session connects and a new TaskGroup is created
- **THEN** a fresh ProactiveEngine task starts with the new TaskGroup

### Requirement: Conversation state awareness
The system SHALL provide a thread-safe `conversation_state` object shared between the proactive engine and the main audio loop. The engine MUST NOT speak when the conversation is active.

#### Scenario: Engine checks state before speaking
- **WHEN** the engine has a proactive message ready
- **AND** `conversation_state.is_active` is `True` (user speaking or Jarvis responding)
- **THEN** the engine waits and does not speak

#### Scenario: Engine speaks during natural pause
- **WHEN** the engine has a proactive message ready
- **AND** `conversation_state.is_active` is `False`
- **AND** `conversation_state.last_audio_end` was more than 5 seconds ago
- **THEN** the engine enqueues the message to `proactive_queue` for speaking

### Requirement: Proactive message queue
The system SHALL use an `asyncio.Queue` for proactive messages. The main audio loop SHALL drain this queue during natural pauses (after turn completion or 5+ seconds of silence).

#### Scenario: Queue drained on turn completion
- **WHEN** a Gemini turn completes (`TurnComplete` received)
- **THEN** the audio loop checks `proactive_queue`
- **AND** speaks the next message from the queue if present

#### Scenario: Queue drained on silence timeout
- **WHEN** no mic input is detected for 5 consecutive seconds
- **AND** no audio is currently playing
- **AND** `conversation_state.is_active` is `False`
- **THEN** the audio loop checks `proactive_queue`
- **AND** speaks the next message from the queue if present

### Requirement: Configurable engine settings
The system SHALL support environment variable configuration for all proactive engine parameters with sensible defaults.

#### Scenario: Default configuration
- **WHEN** no proactive-specific environment variables are set
- **THEN** the engine uses: `PROACTIVE_PAUSE_SECONDS=5`, `PROACTIVE_SUGGESTION_COOLDOWN=1800`, `PROACTIVE_PATTERN_SCAN_INTERVAL=3600`

#### Scenario: Custom pause threshold
- **WHEN** `PROACTIVE_PAUSE_SECONDS=8` is set
- **THEN** the engine waits 8 seconds of silence before speaking proactive messages

### Requirement: Proactive message logging
All proactive messages SHALL be written to the UI log via `write_log()` when spoken.

#### Scenario: Proactive message logged
- **WHEN** the engine enqueues a proactive message for speaking
- **THEN** the message is also written to `ui.write_log()` with a `[PROACTIVE]` prefix
