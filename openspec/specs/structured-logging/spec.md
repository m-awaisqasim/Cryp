## ADDED Requirements

### Requirement: Log configuration initialized at startup
The system SHALL configure structlog with console, rotating file, and WebSocket broadcast handlers at application startup in `main.py`.

#### Scenario: Log configuration loads without error
- **WHEN** `main.py` starts
- **THEN** structlog SHALL be configured with console, rotating file, and WebSocket broadcast handlers

### Requirement: All print() calls replaced with structlog
The system SHALL replace every `print()` statement across all modules with appropriate `structlog` calls at the correct severity level (debug, info, warning, error).

#### Scenario: Existing print calls produce equivalent log output
- **WHEN** any module executes a code path that previously called `print()`
- **THEN** the equivalent structured log message SHALL be emitted at the appropriate level

#### Scenario: No new print() calls introduced
- **WHEN** the codebase is scanned for `print(` calls
- **THEN** zero `print(` calls SHALL remain in any Python file

### Requirement: Rotating file logging
The system SHALL write log files to `logs/` directory with automatic rotation. The main log file SHALL be `logs/cryp.log` with 10 MB max size and 5 backup files. An error-only log SHALL be written to `logs/cryp-error.log` at WARNING+ level.

#### Scenario: Log files are created and rotated
- **WHEN** the application runs and produces logs
- **THEN** `logs/cryp.log` SHALL be created and grow with log entries

#### Scenario: Log rotation triggers at size limit
- **WHEN** `cryp.log` reaches 10 MB
- **THEN** the file SHALL be rotated and up to 5 backup files SHALL be retained

### Requirement: Console output preserved
The system SHALL continue to produce human-readable output on the terminal console via structlog's console renderer.

#### Scenario: Console shows log output
- **WHEN** the application runs in a terminal
- **THEN** log messages SHALL appear on stdout in a human-readable colored format

### Requirement: Dashboard log viewer
The system SHALL stream live log entries to the FastAPI web dashboard via a WebSocket endpoint at `/ws/logs`. The dashboard SHALL display logs with severity color coding, auto-scroll, and a filter input.

#### Scenario: Log viewer WebSocket streams logs
- **WHEN** a log entry is emitted
- **THEN** it SHALL be broadcast to all connected WebSocket clients at `/ws/logs`

#### Scenario: Dashboard displays log entries
- **WHEN** the dashboard is open and logs are streaming
- **THEN** the LogPanel SHALL display entries with color-coded severity, auto-scroll, and filter capability

### Requirement: Logging is purely additive
The system SHALL NOT change any existing functionality, output format, or behavior. Logging SHALL be a non-invasive addition.

#### Scenario: Application behavior unchanged
- **WHEN** all existing unit tests are run
- **THEN** all tests SHALL pass without modification
