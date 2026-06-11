## Why

Cryp currently requires manual setup—create a venv, install dependencies, run `python main.py` in a terminal. There's no one-command install, no auto-start on login, and no built-in CLI to manage the daemon lifecycle. This friction makes Cryp feel like a dev tool rather than a personal assistant that's always available. Adding a proper installer and auto-start capability turns Cryp into a true always-on desktop companion.

## What Changes

- **New `install.sh` script**: One-command install that creates the venv, installs pip deps, copies the service file, enables/starts the systemd user service, and exits with clear status.
- **New `cryp` CLI wrapper**: A shell script (`bin/cryp`) that wraps `systemctl --user` for `start`, `stop`, `restart`, `status`, `logs`, `enable`, `disable` — no need to remember systemd commands.
- **New systemd user service file**: `cryp.service` (or `cryp.service`) placed into `~/.config/systemd/user/` by the installer, auto-starts Cryp on login.
- **Updated `README.md`**: New install/usage section for the one-command flow.

## Capabilities

### New Capabilities
- `install-script`: A single `install.sh` that provisions the entire Cryp environment (venv, deps, systemd service, CLI) with zero manual steps beyond running it.
- `systemd-service`: A systemd user unit that launches Cryp on user login, manages its lifecycle, and captures its output to journald.
- `cli-wrapper`: A `cryp` CLI command that provides unified start/stop/restart/status/logs management without requiring knowledge of systemd.

### Modified Capabilities

*(None — this change introduces brand-new capabilities. No existing spec requirements are altered.)*

## Impact

- **New files**: `install.sh`, `bin/cryp`, `cryp.service` (in `~/.config/systemd/user/` after install)
- **Modified files**: `README.md` (install section)
- **Runtime**: Cryp will start automatically on login via systemd user service
- **Dependencies**: `systemd --user` (available on any modern Ubuntu desktop — no additional packages needed)
- **No breaking changes**: Existing manual `python main.py` workflow still works
