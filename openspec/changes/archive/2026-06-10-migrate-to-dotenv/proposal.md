## Why

The project currently stores the Gemini API key and OS override in `config/api_keys.json` as plain-text JSON. Nineteen Python files independently construct the file path, open the file, parse JSON, and extract keys — duplicating fragile I/O logic everywhere. There is no single source of truth for configuration, no environment-variable fallback, and no safe mechanism for secret management. This makes the codebase hard to configure, error-prone (any missing file crashes at a different call site), and insecure (secrets in plain JSON with no `.env` convention).

## What Changes

- **Replace** `config/api_keys.json` with a `.env` file at the project root as the single source of configuration
- **Create** `config/settings.py` — a central settings module that reads all values from environment variables (loaded via `python-dotenv`)
- **Refactor** all 19 Python files that currently read `api_keys.json` directly to import from `config.settings` instead
- **Remove** `api_keys.json` from git tracking (it's already gitignored; delete the file entirely)
- **Create** `.env.example` as a documented template with all expected variables
- **No fallback**: the project will no longer read `api_keys.json` at all after migration

## Capabilities

### New Capabilities
- `env-config`: Centralized environment-variable configuration via `config/settings.py`, loaded from `.env` via `python-dotenv`

### Modified Capabilities

None — this is a pure infrastructure migration. No spec-level behavior changes.

## Impact

- `config/api_keys.json` will be deleted and no longer read by any code
- `.env` at project root becomes the required configuration mechanism
- All 19 Python files that reference `api_keys.json` will be updated to import from `config.settings`
- `config/__init__.py` helpers (`get_os`, `is_windows`, etc.) will be refactored to read from `config.settings` instead of JSON
- `scripts/check_deps.sh` will be updated to check for `.env` instead of `api_keys.json`
- Documentation in `readme.md` and context files will be updated
- No new external dependencies required (`python-dotenv` already in `requirements.txt`)
