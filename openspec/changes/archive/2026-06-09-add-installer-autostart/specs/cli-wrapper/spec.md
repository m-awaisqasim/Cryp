## ADDED Requirements

### Requirement: CLI entry point
The system SHALL provide a `cryp` CLI command at `~/.local/bin/cryp` that wraps systemd user service management.

#### Scenario: Command location
- **WHEN** a user runs `which cryp`
- **THEN** it resolves to `<install_dir>/bin/cryp`

### Requirement: Start command
The `cryp start` command SHALL start the Cryp service.

#### Scenario: Start service
- **WHEN** a user runs `cryp start`
- **THEN** the script executes `systemctl --user start cryp`
- **AND** waits for the service to activate
- **AND** prints "Cryp started" on success

### Requirement: Stop command
The `cryp stop` command SHALL stop the Cryp service.

#### Scenario: Stop service
- **WHEN** a user runs `cryp stop`
- **THEN** the script executes `systemctl --user stop cryp`
- **AND** prints "Cryp stopped" on success

### Requirement: Restart command
The `cryp restart` command SHALL restart the Cryp service.

#### Scenario: Restart service
- **WHEN** a user runs `cryp restart`
- **THEN** the script executes `systemctl --user restart cryp`
- **AND** prints "Cryp restarted" on success

### Requirement: Status command
The `cryp status` command SHALL show the current service status.

#### Scenario: Status output
- **WHEN** a user runs `cryp status`
- **THEN** the script shows the output of `systemctl --user status cryp`
- **AND** includes a human-readable summary line ("Cryp is running" or "Cryp is stopped")

### Requirement: Logs command
The `cryp logs` command SHALL tail the service logs.

#### Scenario: Follow logs
- **WHEN** a user runs `cryp logs`
- **THEN** the script executes `journalctl --user -u cryp -f`

#### Scenario: Last N lines
- **WHEN** a user runs `cryp logs -n 50`
- **THEN** the script shows the last 50 lines of the Cryp journal

### Requirement: Enable/Disable commands
The `cryp enable` and `cryp disable` commands SHALL control auto-start on login.

#### Scenario: Enable auto-start
- **WHEN** a user runs `cryp enable`
- **THEN** the script executes `systemctl --user enable cryp`
- **AND** prints "Cryp will start automatically on login"

#### Scenario: Disable auto-start
- **WHEN** a user runs `cryp disable`
- **THEN** the script executes `systemctl --user disable cryp`
- **AND** prints "Cryp will no longer start automatically"

### Requirement: Help command
The `cryp help` command SHALL print usage information.

#### Scenario: Help output
- **WHEN** a user runs `cryp help` or `cryp` with no arguments
- **THEN** it prints available commands and their descriptions

### Requirement: Error handling
The CLI SHALL handle errors gracefully and exit with non-zero codes on failure.

#### Scenario: Service not installed
- **WHEN** a user runs `cryp start` on a system where Cryp is not installed
- **THEN** the script prints "Cryp is not installed. Run install.sh first."
- **AND** exits with code 1

#### Scenario: systemctl failure
- **WHEN** `systemctl --user` returns a non-zero exit code
- **THEN** the script prints the systemctl error output
- **AND** exits with the same exit code
