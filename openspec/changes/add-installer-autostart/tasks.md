## 1. Create systemd service unit

- [x] 1.1 Create `cryp.service` unit file with Type=simple, ExecStart pointing to virtualenv python + main.py, and WantedBy=default.target
- [x] 1.2 Verify unit file parses correctly with `systemd-analyze verify`

## 2. Create cryp CLI wrapper

- [x] 2.1 Create `cryp` bash script with start/stop/restart/status/logs subcommands delegating to systemctl --user and journalctl --user
- [x] 2.2 Include usage/help output for unknown subcommands

## 3. Create install.sh

- [x] 3.1 Add dependency checks for python3, pip, venv, systemd
- [x] 3.2 Add virtualenv creation at `~/.local/share/cryp/venv/` and pip install from requirements.txt
- [x] 3.3 Add config directory setup at `~/.config/cryp/` with default config files
- [x] 3.4 Add systemd unit installation to `~/.config/systemd/user/cryp.service` with `systemctl --user daemon-reload && systemctl --user enable --now cryp`
- [x] 3.5 Add cryp CLI wrapper installation to `~/.local/bin/cryp`
- [x] 3.6 Add idempotency check — detect existing install and offer reinstall/upgrade
- [x] 3.7 Add PATH check — warn if `~/.local/bin` not in PATH, offer to add to shell rc

## 4. Update setup.py

- [ ] 4.1 Add `console_scripts` entry point for `cryp` if needed — not applicable: setup.py is a custom pip runner, not setuptools.setup()

## 5. Update .gitignore

- [x] 5.1 Add entries for `install.sh` temp artifacts if any — none created (scripts are tracked in repo)

## 6. Manual verification

- [ ] 6.1 Run install.sh on clean Ubuntu test and verify full flow
- [ ] 6.2 Test cryp start/stop/restart/status/logs commands
- [ ] 6.3 Test auto-start on re-login
- [ ] 6.4 Test idempotency — run install.sh again
