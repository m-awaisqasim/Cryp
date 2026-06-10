## 1. Create config/settings.py

- [x] 1.1 Create `config/settings.py` with `load_dotenv()` at module load, reading `GEMINI_API_KEY` and `OS_SYSTEM` from `os.environ`
- [x] 1.2 Raise `FileNotFoundError` if `.env` is missing, `ValueError` if `GEMINI_API_KEY` is unset
- [x] 1.3 Default `OS_SYSTEM` to `"windows"` and lowercase the value

## 2. Refactor config/__init__.py

- [x] 2.1 Replace `_CONFIG_PATH` and JSON reads with imports from `config.settings`
- [x] 2.2 Refactor `get_config()`, `get_os()`, `is_windows()`, `is_mac()`, `is_linux()` to delegate to `config.settings`

## 3. Create .env.example and delete api_keys.json

- [x] 3.1 Create `.env.example` at project root with `GEMINI_API_KEY=your_gemini_api_key_here` and `OS_SYSTEM=linux`
- [x] 3.2 Ensure `.env` is in `.gitignore` (add if missing)
- [x] 3.3 Run `git rm --cached config/api_keys.json` to remove from tracking
- [x] 3.4 Delete `config/api_keys.json` from disk

## 4. Refactor main.py

- [x] 4.1 Remove the standalone `load_dotenv()` call (handled by `config.settings` now)
- [x] 4.2 Replace `_get_api_key()` JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 4.3 Remove `API_CONFIG_PATH` constant

## 5. Refactor memory/config_manager.py

- [x] 5.1 Replace `load_api_keys()` / `get_gemini_key()` with imports from `config.settings`
- [x] 5.2 Remove JSON read/write methods (`save_api_keys`, `load_api_keys`)
- [x] 5.3 Remove `CONFIG_FILE` constant

## 6. Refactor agent/ files

- [x] 6.1 Refactor `agent/react_loop.py` — replace `_read_api_key()` with `from config.settings import GEMINI_API_KEY`
- [x] 6.2 Refactor `agent/planner_layer.py` — replace `_read_api_key()` with `from config.settings import GEMINI_API_KEY`
- [x] 6.3 Refactor `agent/error_handler.py` — remove unused `API_CONFIG_PATH`
- [x] 6.4 Refactor `agent/planner.py` — remove unused `API_CONFIG_PATH`

## 7. Refactor actions/ files

- [x] 7.1 Refactor `actions/file_processor.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.2 Refactor `actions/screen_processor.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.3 Refactor `actions/dev_agent.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.4 Refactor `actions/code_helper.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.5 Refactor `actions/youtube_video.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.6 Refactor `actions/desktop.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.7 Refactor `actions/computer_settings.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.8 Refactor `actions/flight_finder.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.9 Refactor `actions/computer_control.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.10 Refactor `actions/reminder.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.11 Refactor `actions/send_message.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`
- [x] 7.12 Refactor `actions/web_search.py` — replace JSON read with `from config.settings import GEMINI_API_KEY`

## 8. Refactor ui.py

- [x] 8.1 Replace JSON read in `ui.py` with `from config.settings import GEMINI_API_KEY`

## 9. Update scripts/check_deps.sh

- [x] 9.1 Change `api_keys.json` existence check to `.env` existence check
- [x] 9.2 Add check that `GEMINI_API_KEY` is non-empty (e.g., `grep -q 'GEMINI_API_KEY=' .env`)

## 10. Final cleanup

- [x] 10.1 Verify no Python file references `api_keys.json` (grep check)
- [x] 10.2 Verify all 19 files import from `config.settings` correctly
- [x] 10.3 Run the application to confirm startup succeeds
