## ADDED Requirements

### Requirement: systemd user service lifecycle

A systemd user service unit SHALL manage the Cryp process. The unit SHALL use `Type=simple` and SHALL run under the user's systemd instance. The service SHALL be enabled to start automatically on user login. Standard output and error SHALL be captured by journald. The service SHALL support the standard systemd lifecycle commands (start, stop, restart, enable, disable, status).

#### Scenario: Service starts manually

- **WHEN** user runs `systemctl --user start cryp`
- **THEN** the Cryp Python process starts as a systemd user service, with stdout/stderr routed to journald

#### Scenario: Service stops cleanly

- **WHEN** user runs `systemctl --user stop cryp`
- **THEN** systemd sends SIGTERM to the Cryp process, the process exits gracefully, and the service enters inactive state

#### Scenario: Auto-start on user login

- **WHEN** the user logs into their graphical desktop session
- **THEN** systemd automatically starts the cryp service (if enabled)

### Requirement: Service unit file installation

The install script SHALL copy the `cryp.service` unit file to `~/.config/systemd/user/cryp.service`. The unit SHALL reference the virtualenv Python binary at `~/.local/share/cryp/venv/bin/python` and the `main.py` entry point.

#### Scenario: Unit file installed

- **WHEN** the install script completes
- **THEN** the file `~/.config/systemd/user/cryp.service` exists with correct ExecStart pointing to the virtualenv Python and main.py

#### Scenario: Unit enabled for auto-start

- **WHEN** the install script completes
- **THEN** `systemctl --user is-enabled cryp` returns `enabled`
