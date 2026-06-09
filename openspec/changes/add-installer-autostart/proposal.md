## Why

Cryp currently has no install or startup mechanism — users must manually clone the repo, install dependencies, and run `python main.py` each time. This makes Cryp impractical as an always-on desktop assistant. Adding a one-command install script and systemd user service enables a seamless "install once, always-on" experience on Ubuntu without requiring root.

## What Changes

- **`install.sh`** — single-command bootstrap: creates virtualenv, installs pip dependencies, creates config directory, installs systemd user service, starts Cryp
- **`cryp` CLI wrapper** — bash script at `/usr/local/bin/cryp` (or `~/.local/bin/cryp`) for start / stop / restart / status / logs commands
- **systemd user service** — `cryp.service` that auto-starts Cryp on graphical login, manages process lifecycle, and logs to journald
- **`setup.py` / packaging update** — adjust `setup.py` if needed for proper entry-point discovery

## Capabilities

### New Capabilities
- `one-command-install`: Bootstrap script that clones/sets up Cryp from scratch with a single shell command.
- `systemd-autostart`: systemd user service to auto-start Cryp on login with lifecycle management.
- `cli-control`: A `cryp` CLI wrapper for start, stop, restart, status, and logs commands.

### Modified Capabilities

<!-- No existing capabilities have requirement changes. -->

## Impact

- **New files**: `install.sh`, `cryp` (CLI wrapper), `cryp.service` (systemd unit template)
- **Modified files**: `setup.py` (add `console_scripts` entry point if not present), `.gitignore` (if needed)
- **Dependencies**: No new Python dependencies; relies on `systemd --user` (built-in on Ubuntu), `python3`, `pip`, `venv`
- **System**: Only Ubuntu (primary target); no root required — everything works under the user's account
