## Context

The project stores its Gemini API key and OS override in `config/api_keys.json`. Nineteen Python files independently resolve the JSON path, open the file, parse it, and extract the key — duplicating error-prone, untested I/O throughout the codebase. Python-dotenv is already in `requirements.txt` and `main.py` already has an unused `load_dotenv()` call. However, no `.env` file exists and no code reads from environment variables. The `config/__init__.py` module provides helper functions (`get_config()`, `get_os()`, `is_windows()`, etc.) but these are only used by a few call sites — most files bypass them entirely and read JSON directly.

## Goals / Non-Goals

**Goals:**
- Single source of truth for all configuration: `.env` file at project root
- Central `config/settings.py` module that all other code imports from
- All 19 Python files refactored to import from `config.settings` instead of reading JSON
- `config/api_keys.json` deleted entirely — no fallback to JSON
- `.env.example` as a documented template for new developers
- `scripts/check_deps.sh` updated to check `.env` existence instead of JSON

**Non-Goals:**
- Encrypted secrets or vault integration (out of scope)
- Runtime config reload (config is read at import time)
- Refactoring `config/proactive_rules.json` (not a secrets/config file)
- Changing the OS detection logic or adding new config values

## Decisions

1. **Env var naming**: Use `GEMINI_API_KEY` and `OS_SYSTEM` as the environment variable names (uppercase, underscore-separated). These map 1:1 to the current JSON keys `gemini_api_key` and `os_system`.

2. **`config/settings.py` pattern**: A single module with module-level constants (`GEMINI_API_KEY: str`, `OS_SYSTEM: str`) loaded once at import time from `os.environ`. Calls `load_dotenv()` at module load to populate from `.env`. This is simpler than a class-based settings object and matches the current `config/__init__.py` pattern.

3. **`config/__init__.py` refactor**: Keep the helper functions (`get_os()`, `is_windows()`, etc.) but have them delegate to `config.settings` instead of reading JSON. This preserves the existing API for callers that already use these helpers.

4. **`memory/config_manager.py` refactor**: Replace `load_api_keys()` / `get_gemini_key()` with direct imports from `config.settings`. The CRUD methods (`save_api_keys`) that write to JSON become no-ops or are removed since `.env` is read-only through settings.

5. **No fallback**: If `.env` is missing or `GEMINI_API_KEY` is unset, raise a clear `ValueError` at import time. Fail fast rather than silently defaulting.

6. **Single `load_dotenv()` call**: Already present in `main.py:108`. Move it into `config/settings.py` so that any module importing settings triggers `.env` loading. This eliminates the dependency on `main.py` having already loaded dotenv.

7. **`scripts/check_deps.sh`**: Change the file-existence check from `config/api_keys.json` to `.env`. Also add a check for `GEMINI_API_KEY` being non-empty.

## Risks / Trade-offs

- **[Module-level state]** `config/settings.py` evaluates at import time, so env must be present before any module import. Mitigation: `load_dotenv()` is called inside `settings.py` itself, before reading `os.environ`.
- **[Breaking change]** Users upgrading must create `.env` from `.env.example` and delete `api_keys.json`. Mitigation: `.env.example` is well-documented; `check_deps.sh` catches missing config at startup.
- **[Read-only]** Unlike the old JSON approach, apps cannot programmatically write new keys to `.env`. This is acceptable because the Gemini API key is set once during setup, not at runtime.
- **[gitignore overlap]** `.env` is commonly gitignored by convention. Verify `.env` is in `.gitignore` (it should be; add if missing). `.env.example` is NOT gitignored.
