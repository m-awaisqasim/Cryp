## ADDED Requirements

### Requirement: Single-command installation

The install.sh script SHALL bootstrap Cryp from a cloned repository with a single shell command run by the user. No root access SHALL be required. The script SHALL be idempotent — running it again on an existing install SHALL detect the existing installation and offer to reinstall or upgrade.

#### Scenario: Fresh install from clean system

- **WHEN** user runs `bash install.sh` on a system without Cryp installed
- **THEN** the script detects system dependencies (python3, pip, venv, systemd), creates a Python virtualenv at `~/.local/share/cryp/venv/`, installs pip dependencies from `requirements.txt`, creates config directory at `~/.config/cryp/`, copies default config files, installs the systemd user service, and starts Cryp

#### Scenario: Existing install detected

- **WHEN** user runs `bash install.sh` and Cryp is already installed
- **THEN** the script prints a message indicating Cryp is already installed and asks the user if they want to reinstall or upgrade

#### Scenario: Missing system dependencies

- **WHEN** python3, pip, venv, or systemd is not available
- **THEN** the script prints a clear error message listing the missing dependency and exits with a non-zero code

### Requirement: XDG-compliant directory layout

The install script SHALL place Cryp files according to the XDG Base Directory specification: binaries in `~/.local/bin/`, data in `~/.local/share/cryp/`, configuration in `~/.config/cryp/`, and logs managed by journald.

#### Scenario: Directory structure verification

- **WHEN** the install script completes successfully
- **THEN** the following directories exist: `~/.local/share/cryp/venv/`, `~/.config/cryp/`
- **AND** the cryp CLI wrapper is available at `~/.local/bin/cryp`
