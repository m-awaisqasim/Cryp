## Context

Cryp is a Python desktop AI assistant that runs via `python main.py`. It currently has no packaging, no installer, and no auto-start mechanism. Users must manually clone the repo, create a virtualenv, install `requirements.txt`, configure API keys in `config/api_keys.json`, and run `python main.py` every session. The project targets Ubuntu 26.04 and uses systemd for the system health daemon (Phase 2), making systemd user services a natural fit for lifecycle management.

## Goals / Non-Goals

**Goals:**

- Provide a one-command `install.sh` that bootstraps Cryp from scratch on a fresh Ubuntu system
- Create a `cryp` CLI wrapper for everyday lifecycle management (start/stop/restart/status/logs)
- Create a systemd user service that auto-starts Cryp on graphical login
- All operations must work without root access, using `systemctl --user`
- Support standard Ubuntu 26.04 with Python 3.11+

**Non-Goals:**

- Cross-platform installer (Windows/macOS) — future work
- Package manager distribution (deb, snap, flatpak) — future work
- GUI installer — CLI-only
- Docker containerization

## Decisions

1. **CLI wrapper location: `~/.local/bin/cryp`** — `~/.local/bin` is in `PATH` by default on Ubuntu and requires no root. Symlink-based install avoids modifying system directories.
2. **systemd unit type: `simple`** — Cryp's `main.py` runs as a long-lived foreground process. `Type=simple` with `ExecStart` pointing to the virtualenv's Python is the cleanest fit. No forking needed.
3. **Logging: journald via stdout** — Cryp's `structlog` output goes to stdout/stderr; systemd captures this automatically. The `logs` command uses `journalctl --user -u cryp`.
4. **Virtualenv location: `~/.local/share/cryp/venv/`** — follows XDG base directory spec for user-local data.
5. **Config path: `~/.config/cryp/`** — follows XDG for configuration files. Existing `config/` directory is copied/symlinked here during install.
6. **Install script in one file** — `install.sh` handles everything: dependency checks, venv creation, pip install, config setup, service install, and start. No root, no separate steps.

## Risks / Trade-offs

- **[Risk] systemd user services only start on user login, not at boot** → Trade-off: avoids root. Acceptable for a desktop assistant. User can configure `linger` if boot-time start is needed.
- **[Risk] `~/.local/bin` not in PATH on some systems** → Mitigation: `install.sh` checks and prompts to add it to shell rc file.
- **[Risk] User might not have `systemd --user` available** → Mitigation: `install.sh` checks for systemd and exits with clear message. Ubuntu always has it.
- **[Risk] Breaking existing Cryp install** → Mitigation: `install.sh` detects existing install and offers to reinstall/upgrade rather than overwriting.
