## 1. Systemd Service Unit

- [x] 1.1 Create `cryp.service` template with `%%INSTALL_DIR%%` placeholder for the project root path
- [x] 1.2 Set `ExecStart` to `%%INSTALL_DIR%%/.venv/bin/python %%INSTALL_DIR%%/main.py`
- [x] 1.3 Set `WorkingDirectory` to `%%INSTALL_DIR%%`
- [x] 1.4 Configure `Restart=on-failure` with `RestartSec=10`
- [x] 1.5 Set `Type=simple` and add `EnvironmentFile` support at `%%INSTALL_DIR%%/.env`

## 2. CLI Wrapper

- [x] 2.1 Create `bin/cryp` shell script skeleton with command dispatch
- [x] 2.2 Implement `cryp start` → `systemctl --user start cryp`
- [x] 2.3 Implement `cryp stop` → `systemctl --user stop cryp`
- [x] 2.4 Implement `cryp restart` → `systemctl --user restart cryp`
- [x] 2.5 Implement `cryp status` with human-readable summary
- [x] 2.6 Implement `cryp logs` with `-n` flag support
- [x] 2.7 Implement `cryp enable` and `cryp disable`
- [x] 2.8 Implement `cryp help` and no-arg usage display
- [x] 2.9 Add error handling for missing install and systemctl failures

## 3. Install Script

- [x] 3.1 Create `install.sh` with pre-flight checks (Python version, systemd availability, WSL detection)
- [x] 3.2 Implement venv creation and pip dependency installation
- [x] 3.3 Implement service file generation from template (substitute install dir via sed)
- [x] 3.4 Implement CLI symlink creation at `~/.local/bin/cryp`
- [x] 3.5 Implement `systemctl --user daemon-reload`, `enable`, `start`
- [x] 3.6 Implement idempotency guards (skip if already done)
- [x] 3.7 Implement colored `[OK]/[SKIP]/[FAIL]` output for each step
- [x] 3.8 Implement `--uninstall` flag to stop/disable/remove all artifacts
- [x] 3.9 Record install path in `~/.config/cryp/install.conf` for re-install detection

## 4. Testing & Verification

- [x] 4.1 Test `install.sh` from clean state on Ubuntu VM: verify venv, deps, service, CLI
- [x] 4.2 Test `install.sh` re-run: verify idempotency and path update
- [x] 4.3 Test `cryp start/stop/restart/status/logs` end-to-end
- [x] 4.4 Test `cryp enable/disable` and login auto-start behavior
- [x] 4.5 Test `install.sh --uninstall`: verify service removed, CLI removed, config removed
- [x] 4.6 Test `install.sh` with `INSTALL_DIR` override
- [x] 4.7 Test pre-flight failure on missing Python 3.11+ and on WSL

## 5. Documentation

- [x] 5.1 Update `README.md` with one-command install section
- [x] 5.2 Add `cryp` CLI usage examples to README
