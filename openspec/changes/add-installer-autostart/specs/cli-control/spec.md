## ADDED Requirements

### Requirement: cryp CLI wrapper

A `cryp` shell script SHALL be installed at `~/.local/bin/cryp` providing commands for everyday lifecycle management. The wrapper SHALL support the following subcommands: `start`, `stop`, `restart`, `status`, `logs`. Each subcommand SHALL delegate to the appropriate systemctl --user invocation.

#### Scenario: cryp start

- **WHEN** user runs `cryp start`
- **THEN** the wrapper runs `systemctl --user start cryp` and prints a confirmation message

#### Scenario: cryp stop

- **WHEN** user runs `cryp stop`
- **THEN** the wrapper runs `systemctl --user stop cryp` and prints a confirmation message

#### Scenario: cryp restart

- **WHEN** user runs `cryp restart`
- **THEN** the wrapper runs `systemctl --user restart cryp`

#### Scenario: cryp status

- **WHEN** user runs `cryp status`
- **THEN** the wrapper runs `systemctl --user status cryp` and displays the output

#### Scenario: cryp logs

- **WHEN** user runs `cryp logs`
- **THEN** the wrapper runs `journalctl --user -u cryp -n 50 -f` to tail Cryp logs

#### Scenario: Unknown subcommand

- **WHEN** user runs `cryp` with an unknown subcommand
- **THEN** the wrapper prints usage information listing valid subcommands and exits with code 1
