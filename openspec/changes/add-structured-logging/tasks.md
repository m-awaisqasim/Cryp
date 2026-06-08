## 1. Dependency & Setup

- [x] 1.1 Add `structlog` to `requirements.txt`
- [x] 1.2 Create `logs/` directory and add to `.gitignore`
- [x] 1.3 Create `core/logger.py` with log configuration (console, rotating file, error file handlers)

## 2. Log Configuration in main.py

- [x] 2.1 Import and initialize the logger at startup in `main.py`
- [x] 2.2 Integrate structlog with DashboardEventBus for WebSocket log streaming

## 3. Replace print() in Core Modules

- [x] 3.1 Replace `print()` calls in `core/daemon.py`
- [x] 3.2 Replace `print()` calls in `core/hotword.py`
- [x] 3.3 Replace `print()` calls in `core/context_collector.py` (no print calls)
- [x] 3.4 Replace `print()` calls in `core/retry.py`
- [x] 3.5 Replace `print()` calls in `core/gemini_compat.py`
- [x] 3.6 Replace `print()` calls in `setup.py`

## 4. Replace print() in Dashboard

- [x] 4.1 Replace `print()` calls in `dashboard/server.py`

## 5. Replace print() in Actions

- [x] 5.1 Replace `print()` calls in `actions/screen_processor.py`
- [x] 5.2 Replace `print()` calls in `actions/game_updater.py`
- [x] 5.3 Replace `print()` calls in `actions/browser_control.py`
- [x] 5.4 Replace `print()` calls in `actions/computer_settings.py`
- [x] 5.5 Replace `print()` calls in `actions/code_helper.py`
- [x] 5.6 Replace `print()` calls in `memory/memory_manager.py`
- [x] 5.7 Replace `print()` calls in `actions/youtube_video.py`
- [x] 5.8 Replace `print()` calls in `actions/web_search.py`
- [x] 5.9 Replace `print()` calls in `actions/dev_agent.py`
- [x] 5.10 Replace `print()` calls in `actions/flight_finder.py`
- [x] 5.11 Replace `print()` calls in `actions/reminder.py`
- [x] 5.12 Replace `print()` calls in `actions/computer_control.py`
- [x] 5.13 Replace `print()` calls in `actions/open_app.py`
- [x] 5.14 Replace `print()` calls in `actions/send_message.py`
- [x] 5.15 Replace `print()` calls in `actions/desktop.py`
- [x] 5.16 Replace `print()` calls in `actions/file_processor.py`
- [x] 5.17 Replace `print()` calls in `actions/weather_report.py`

## 6. Replace print() in Agent & Proactive

- [x] 6.1 Replace `print()` calls in `agent/task_queue.py`
- [x] 6.2 Replace `print()` calls in `agent/planner.py`
- [x] 6.3 Skip — `agent/error_handler.py` does not exist
- [x] 6.4 Replace `print()` calls in `agent/executor.py`
- [x] 6.5 Replace `print()` calls in `proactive/engine.py`
- [x] 6.6 Replace `print()` calls in `proactive/briefing.py`
- [x] 6.7 Replace `print()` calls in `proactive/anomalies.py`
- [x] 6.8 Replace `print()` calls in `proactive/patterns.py`
- [x] 6.9 Replace `print()` calls in `proactive/suggestions.py`

## 7. Replace print() in Memory & Config

- [x] 7.1 Replace `print()` calls in `memory/memory_manager.py`
- [x] 7.2 Skip — `memory/config_manager.py` does not exist

## 8. Dashboard Log Viewer

- [x] 8.1 Add GET /api/logs endpoint to `dashboard/server.py`
- [x] 8.2 Add log viewer panel to `dashboard/templates/index.html` with severity colors, auto-scroll, and filter

## 9. Verification

- [x] 9.1 Run all unit tests to confirm no regressions
- [x] 9.2 Manually verify console output is preserved
- [x] 9.3 Verify log files are written to `logs/` with rotation
- [x] 9.4 Verify dashboard log viewer streams entries correctly
- [x] 9.5 Verify zero `print(` calls remain in the codebase
