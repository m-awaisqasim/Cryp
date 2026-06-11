## Context

Cryp is a Python 3.11+ app that currently requires a manual venv + pip workflow. There is no install script, no auto-start mechanism, and no lifecycle CLI. The project lives at `/home/awais/Cryp` with a standard Python project layout. Systemd user services are available on all modern Ubuntu desktops and require no root privileges.

## Goals / Non-Goals

**Goals:**
- A single `install.sh` that sets up venv, installs dependencies, installs the systemd user unit, enables/starts the service, and creates the `cryp` CLI symlink.
- A systemd user service (`cryp.service`) that starts Cryp on user login and restarts it on crash.
- A `cryp` CLI wrapper around `systemctl --user` for start/stop/restart/status/logs.
- All operations work without `sudo` on Ubuntu.

**Non-Goals:**
- Cross-platform support (Windows/macOS) — Ubuntu only for now.
- System-level installation (`/usr/local/bin`, system-wide systemd) — user-level only.
- Dependency bundling (PyInstaller, Nix, etc.) — standard venv + pip is sufficient.

## Decisions

1. **Systemd user services over crontab @reboot or desktop autostart `.desktop` files** — systemd offers robust lifecycle management (restart on failure, logging via journald, dependency ordering) that neither crontab nor `.desktop` provides. `.desktop` autostart lacks restart-on-crash and unified logging.

2. **Standalone `cryp` shell script over Python entry point** — A minimal POSIX shell script (`bin/cryp`) that wraps `systemctl --user` is zero-dependency, works even if the venv is broken, and is trivial to understand. A Python CLI would add complexity and a bootstrapping problem (can't run if venv is broken).

3. **Service name `cryp.service` over `cryp.service`** — The project is called Cryp but the in-app branding is "CRYP" (the HUD title, log prefix, etc.). Using `cryp` aligns with the existing `run.txt` references (`systemctl --user enable cryp`). Aliases can be added later.

4. **Single `install.sh` over a multi-step setup** — A single script reduces friction to exactly one command and is self-documenting (prints each step). Users can inspect it before running.

5. **Service file template with `%%` placeholders over hardcoded paths** — `install.sh` uses `sed` to substitute the actual install directory into the service file at install time, so the repo can be cloned anywhere.

## Risks / Trade-offs

- **[Systemd user service not available on WSL]** → Mitigation: Ubuntu on bare metal or VM is the primary target; WSL users can use manual setup. Install script detects WSL and prints a clear message.
- **[Service fails silently if Python/virtualenv broken]** → Mitigation: `ExecStart` checks for venv existence and falls back to recreating it; `Restart=on-failure` with `RestartSec=10` ensures recovery.
- **[User may have multiple cloned copies of Cryp]** → Mitigation: `install.sh` records the installed path in `~/.config/cryp/install.conf`; running install again updates the service file to point at the new location.
- **[`cryp` CLI name conflicts with other tools]** → Mitigation: Low risk for a personal assistant tool. Install script places it at `~/.local/bin/cryp` (which is typically early in `$PATH`). Users can alias if needed.
