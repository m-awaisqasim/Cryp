## ADDED Requirements

### Requirement: Wake word detection via openWakeWord
The system SHALL use the openWakeWord library to continuously listen for the phrase "Hey Jarvis" from the microphone and emit a wake event upon detection.

#### Scenario: Successful wake word detection
- **WHEN** the user says "Hey Jarvis" within 2 meters of the microphone
- **THEN** the system SHALL detect the wake word within 1 second and emit a wake event

#### Scenario: False acceptance
- **WHEN** a phrase acoustically similar to "Hey Jarvis" is spoken (e.g., "Hey Charles", "Hey Harvard")
- **THEN** the system MAY still trigger a wake event (false positive rate < 1 per 24 hours expected)

#### Scenario: Wake word ignored during active session
- **WHEN** JarvisLive is in ACTIVE state and the user says "Hey Jarvis"
- **THEN** the system SHALL NOT process the wake word (hotword detector is paused or ignored while active)

### Requirement: Standalone hotword audio stream
The hotword detector SHALL maintain its own `sounddevice.InputStream` independent of the Gemini session audio stream, ensuring continuous listening even when the session stream is closed.

#### Scenario: Hotword stream survives session teardown
- **WHEN** JarvisLive transitions from ACTIVE to SLEEPING state (session closed)
- **THEN** the hotword audio stream SHALL remain open and continue processing

#### Scenario: Hotword stream starts on launch
- **WHEN** `main.py` starts
- **THEN** the hotword audio stream SHALL be initialized before any Gemini session connection

### Requirement: Wake event mechanism
The hotword detector SHALL signal wake events to the main event loop via an `asyncio.Event` to trigger session (re)connection.

#### Scenario: Wake event triggers reconnect
- **WHEN** a wake event is fired while JarvisLive is in SLEEPING state
- **THEN** JarvisLive SHALL exit the sleep loop and initiate a new Gemini Live session within 3 seconds

#### Scenario: Wake event during session startup
- **WHEN** a wake event is fired while a session is already starting (TRIGGERED state)
- **THEN** the event SHALL be silently ignored (debounced)
