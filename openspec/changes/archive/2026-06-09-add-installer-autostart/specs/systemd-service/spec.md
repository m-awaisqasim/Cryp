## ADDED Requirements

### Requirement: Systemd user unit
The system SHALL provide a `cryp.service` systemd user unit that manages the Cryp daemon lifecycle.

#### Scenario: Service starts on login
- **WHEN** the user logs into their desktop environment
- **THEN** systemd starts `cryp.service` automatically
- **AND** the service runs as the current user (no root)

#### Scenario: Service definition
- **WHEN** `systemctl --user cat cryp` is run
- **THEN** the unit file shows `ExecStart` pointing to the Cryp install directory's venv Python + `main.py`
- **AND** `WorkingDirectory` is set to the Cryp install directory
- **AND** `Restart=on-failure` with `RestartSec=10`
- **AND** `Type=simple`

### Requirement: Environment handling
The service SHALL forward environment variables from the user session and allow overrides.

#### Scenario: Default environment
- **WHEN** the service starts
- **THEN** it inherits the user's `PATH`, `HOME`, `XDG_*` variables
- **AND** activates the project venv

#### Scenario: Custom environment variables
- **WHEN** `CRYP_HOTWORD=0` needs to be set
- **THEN** the service file supports an `Environment=` line or `EnvironmentFile=` that can be customized per-install

### Requirement: Logging to journald
The service SHALL capture all stdout/stderr output to the systemd journal.

#### Scenario: View logs via journalctl
- **WHEN** a user runs `journalctl --user -u cryp -f`
- **THEN** they see live Cryp log output with timestamps

### Requirement: Service lifecycle
The service SHALL support standard systemd lifecycle commands.

#### Scenario: Stop and start
- **WHEN** `systemctl --user stop cryp` is run
- **THEN** the Cryp process receives SIGTERM and shuts down gracefully

#### Scenario: Service status
- **WHEN** `systemctl --user status cryp` is run
- **THEN** it shows active/running, exit code, and recent log lines
