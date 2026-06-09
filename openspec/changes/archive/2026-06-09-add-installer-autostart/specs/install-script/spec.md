## ADDED Requirements

### Requirement: One-command install
The system SHALL provide a single `install.sh` script that provisions the entire Cryp environment (venv, pip deps, systemd unit, CLI) with zero manual steps beyond invoking it.

#### Scenario: Fresh install from clean system
- **WHEN** a user runs `bash install.sh` from the Cryp repository root
- **THEN** the script creates a Python virtual environment at `<repo_root>/.venv`
- **AND** installs all pip dependencies from `requirements.txt`
- **AND** copies `jarvis.service` to `~/.config/systemd/user/jarvis.service`
- **AND** creates a `cryp` symlink at `~/.local/bin/cryp` pointing to `<repo_root>/bin/cryp`
- **AND** runs `systemctl --user daemon-reload`
- **AND** runs `systemctl --user enable --now jarvis`
- **AND** exits with code 0

#### Scenario: Re-run install on existing installation
- **WHEN** a user runs `bash install.sh` on an already-installed Cryp
- **THEN** the script updates pip dependencies if newer
- **AND** updates the service file to match the current repo path
- **AND** restarts the service
- **AND** exits with code 0

#### Scenario: Install with custom path
- **WHEN** a user runs `INSTALL_DIR=/opt/cryp bash install.sh`
- **THEN** the script uses `/opt/cryp` as the project root for all paths

### Requirement: Idempotent operation
The install script SHALL be safe to re-run multiple times without side effects.

#### Scenario: Re-run no-ops
- **WHEN** `install.sh` is run again on a fully up-to-date install
- **THEN** it skips venv creation (venv already exists)
- **AND** skips pip install if `requirements.txt` is unchanged
- **AND** skips `daemon-reload` if the service file hasn't changed
- **AND** skips `enable` if already enabled

### Requirement: Pre-flight checks
The install script SHALL verify system prerequisites before making changes.

#### Scenario: Missing Python 3.11+
- **WHEN** `python3 --version` returns a version < 3.11
- **THEN** the script prints an error message and exits with code 1

#### Scenario: Missing systemd user support
- **WHEN** `systemctl --user` is not available
- **THEN** the script prints a warning and falls back to venv-only install

#### Scenario: WSL detection
- **WHEN** running on Windows Subsystem for Linux
- **THEN** the script prints a message that auto-start is not supported on WSL
- **AND** completes the venv + pip install portion only

### Requirement: Self-documenting output
The install script SHALL print clear, colored status for each step.

#### Scenario: Verbose output
- **WHEN** `install.sh` runs
- **THEN** each step is printed with `[OK]`, `[SKIP]`, or `[FAIL]` prefix
- **AND** the final output shows overall status (success or which steps failed)

### Requirement: Uninstall support
The system SHALL provide `install.sh --uninstall` to remove all installed artifacts.

#### Scenario: Full uninstall
- **WHEN** a user runs `bash install.sh --uninstall`
- **THEN** the script stops and disables the systemd service
- **AND** removes `~/.config/systemd/user/jarvis.service`
- **AND** removes `~/.local/bin/cryp`
- **AND** removes `~/.config/cryp/`
- **AND** prints a message that the repository and venv were left in place
