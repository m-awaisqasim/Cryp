## 1. Dependencies & Setup

- [x] 1.1 Add `psutil` and `pyperclip` to `requirements.txt`
- [x] 1.2 Verify cross-platform availability: `psutil` works on Linux/macOS/Windows, `pyperclip` requires `xclip`/`xsel` on Linux (add note to run.txt if needed)

## 2. Create `core/context_collector.py`

- [x] 2.1 Implement `get_active_window() -> str | None` — detect active window title via subprocess call to xdotool getactivewindow getwindowname (already installed and confirmed working on this system) on Linux (Ubuntu), stub on other platforms
- [x] 2.2 Implement `get_clipboard() -> str | None` — read clipboard via `pyperclip.paste()`, truncate to 200 chars, sanitize control characters
- [x] 2.3 Implement `get_battery() -> str | None` — read battery via `psutil.sensors_battery()` or `/sys/class/power_supply/`
- [x] 2.4 Implement `get_cpu_usage() -> str | None` — read CPU via `psutil.cpu_percent(interval=0.1)`, wrap in timeout guard (max 0.5s)
- [x] 2.5 Implement `get_ram_usage() -> str | None` — read RAM via `psutil.virtual_memory()`
- [x] 2.6 Implement `gather_live_context() -> str` — call all sensor functions, filter out `None` values, format into `[LIVE CONTEXT]` block
- [x] 2.7 Ensure every sensor function is wrapped in `try/except` so failures return `None` silently

## 3. Integrate Into Session Config

- [x] 3.1 Import `gather_live_context` in `main.py` from `core.context_collector`
- [x] 3.2 In `_build_config()`, call `gather_live_context()` and insert its result as the first element of the `parts` list (before time context)
- [x] 3.3 Verify that a sensor failure does not crash `_build_config()` — test by temporarily breaking a sensor

## 4. Test & Verify

- [x] 4.1 Run `python -c "from core.context_collector import gather_live_context; print(gather_live_context())"` and confirm output contains available fields
- [x] 4.2 Start Cryp and verify LIVE CONTEXT block appears in system instruction (check logs or print in `_build_config()`)
- [x] 4.3 Simulate sensor failure by raising exception in one sensor, confirm session starts normally without that field
