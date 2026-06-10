## ADDED Requirements

### Requirement: Configuration loaded from .env file
The system SHALL load all configuration from a `.env` file at the project root using `python-dotenv`. The `.env` file SHALL be the sole source of configuration values — no JSON fallback SHALL exist.

#### Scenario: .env file present at startup
- **WHEN** the application starts and `.env` exists at the project root
- **THEN** all values from `.env` SHALL be loaded into `os.environ` and accessible via `config.settings`

#### Scenario: .env file missing at startup
- **WHEN** the application starts and `.env` does not exist
- **THEN** `config.settings` SHALL raise a `FileNotFoundError` at import time

#### Scenario: Required key missing in .env
- **WHEN** `.env` exists but `GEMINI_API_KEY` is not set
- **THEN** `config.settings` SHALL raise a `ValueError` with a clear message indicating which key is missing

### Requirement: config.settings module provides all config values
The system SHALL provide a `config.settings` module that exports `GEMINI_API_KEY` and `OS_SYSTEM` as module-level constants, read from `os.environ` after `load_dotenv()`.

#### Scenario: GEMINI_API_KEY is accessible
- **WHEN** any module does `from config.settings import GEMINI_API_KEY`
- **THEN** the value SHALL be the string from the `GEMINI_API_KEY` environment variable

#### Scenario: OS_SYSTEM defaults to "windows" when unset
- **WHEN** `.env` does not set `OS_SYSTEM`
- **THEN** `config.settings.OS_SYSTEM` SHALL be `"windows"`

#### Scenario: OS_SYSTEM is lowercase
- **WHEN** `OS_SYSTEM` is set in `.env` (e.g., `Linux`, `LINUX`)
- **THEN** `config.settings.OS_SYSTEM` SHALL be lowercased to `"linux"`

### Requirement: All direct api_keys.json reads replaced
The system SHALL replace every instance of direct `api_keys.json` file reading with an import from `config.settings`. No Python file SHALL read `config/api_keys.json` after migration.

#### Scenario: No remaining api_keys.json reads in source
- **WHEN** the codebase is scanned for `api_keys.json` references in Python files
- **THEN** zero references SHALL remain (excluding `.md` docs and `.gitignore`)

#### Scenario: config/__init__.py delegates to settings
- **WHEN** any code calls `config.get_config()` or `config.get_os()`
- **THEN** the values SHALL come from `config.settings`, not from reading JSON

### Requirement: .env.example documents all variables
The system SHALL provide `.env.example` at the project root listing every expected environment variable with a placeholder value and a comment describing its purpose.

#### Scenario: .env.example contains all expected vars
- **WHEN** `.env.example` is read
- **THEN** it SHALL contain `GEMINI_API_KEY=your_gemini_api_key_here` and `OS_SYSTEM=linux`

#### Scenario: .env.example is NOT gitignored
- **WHEN** `.env.example` is tracked by git
- **THEN** it SHALL NOT appear in `.gitignore`

### Requirement: api_keys.json removed from project
The system SHALL delete `config/api_keys.json` and remove it from git tracking permanently.

#### Scenario: File deleted from disk
- **WHEN** the project directory is listed
- **THEN** `config/api_keys.json` SHALL NOT exist

#### Scenario: Git tracking removed
- **WHEN** `git rm --cached config/api_keys.json` is run
- **THEN** the file SHALL be removed from git tracking (remaining in `.gitignore` prevents re-addition)

### Requirement: check_deps.sh validates .env
The startup dependency check script SHALL verify that `.env` exists and that `GEMINI_API_KEY` is non-empty, instead of checking `config/api_keys.json`.

#### Scenario: Script passes with valid .env
- **WHEN** `scripts/check_deps.sh` runs and `.env` exists with a non-empty `GEMINI_API_KEY`
- **THEN** the script SHALL exit with code 0

#### Scenario: Script fails with missing .env
- **WHEN** `scripts/check_deps.sh` runs and `.env` does not exist
- **THEN** the script SHALL print an error and exit with non-zero code
