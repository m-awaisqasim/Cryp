## 1. Memory & Context Extensions

- [x] 1.1 Add `query_patterns(days_back=7)` helper to `memory/memory_manager.py` that aggregates episodic summaries across sessions with tool usage, topics, and timestamps
- [x] 1.2 Add `patterns/` namespace support to `update_memory()` in `memory/memory_manager.py` for storing detected patterns as procedural memory
- [x] 1.3 Add `gather_proactive_context()` to live context module that returns structured dict with session start, uptime, app launches today, and window change log
- [x] 1.4 Add daily aggregation store in memory for tracking app launches and window changes across sessions (resets at midnight)
- [x] 1.5 Add `get_health_snapshot()` to `core/daemon.py` exposing current CPU, RAM, disk, battery metrics as a dict
- [x] 1.6 Add alert history list (last 50) with `get_alert_history(minutes_back)` to `core/daemon.py`

## 2. Conversation State & Proactive Queue

- [x] 2.1 Create `proactive/conversation_state.py` with a thread-safe `ConversationState` class tracking `is_active`, `last_audio_end`, and `is_speaking`
- [x] 2.2 Create `proactive/queue.py` with an async `ProactiveQueue` wrapper around `asyncio.Queue` for enqueuing and draining proactive messages
- [x] 2.3 Integrate `ConversationState` into `JarvisLive._receive_audio()` — set `is_active=True` during tool calls and response, `False` on `TurnComplete`
- [x] 2.4 Integrate proactive queue draining into `JarvisLive._receive_audio()` after turn completion and during 5+ second silence pauses
- [x] 2.5 Add `proactive_queue` and `conversation_state` to `JarvisLive.__init__()` and wire into `_run()` TaskGroup

## 3. Proactive Engine

- [x] 3.1 Create `proactive/engine.py` with `ProactiveEngine` async task that initializes internal timers (briefing, pattern scan, suggestion cooldown, anomaly check)
- [x] 3.2 Implement `_check_briefing()` method — reads `memory/last_briefing_date.txt`, compares with today, fires briefing if different
- [x] 3.3 Implement `_scan_patterns()` method — hourly timer that calls `query_patterns()`, applies rule-based heuristics, stores results in memory
- [x] 3.4 Implement `_check_anomalies()` method — compares current system metrics against baseline from patterns, enqueues alerts for >2σ deviations
- [x] 3.5 Implement `_evaluate_suggestions()` method — loads `config/proactive_rules.json`, matches against current context, enqueues matching suggestions
- [x] 3.6 Add environment variable configuration support (`PROACTIVE_PAUSE_SECONDS`, `PROACTIVE_SUGGESTION_COOLDOWN`, `PROACTIVE_PATTERN_SCAN_INTERVAL`, `PROACTIVE_ANOMALY_COOLDOWN`, `PROACTIVE_BRIEFING_ENABLED`)
- [x] 3.7 Wire `ProactiveEngine` into `JarvisLive._run()` as a 5th concurrent task in the TaskGroup

## 4. Daily Briefing Module

- [x] 4.1 Create `proactive/briefing.py` with `generate_briefing()` function that composes: time-appropriate greeting, weather, reminders count, recent memory updates, system health snapshot
- [x] 4.2 Implement graceful fallback for each briefing section (skip if data unavailable)
- [x] 4.3 Keep briefing text to 3-4 sentences maximum
- [x] 4.4 Write `memory/last_briefing_date.txt` after successful briefing delivery

## 5. Pattern Detection Module

- [x] 5.1 Create `proactive/patterns.py` with `detect_time_patterns(sessions)` — finds actions repeated at same time on 3+ days
- [x] 5.2 Implement `detect_frequency_patterns(sessions)` — computes top 3 most-used apps per time block (morning/afternoon/evening)
- [x] 5.3 Implement pattern storage — detected patterns written to `patterns/` namespace in memory_manager
- [x] 5.4 Implement baseline computation — per-hour CPU/RAM/app means and stddevs from 7 days of data

## 6. Anomaly Detection Module

- [x] 6.1 Create `proactive/anomalies.py` with `check_cpu_anomaly(current, baseline)` — returns alert message if >2σ deviation
- [x] 6.2 Implement `check_ram_anomaly(current, baseline)` — returns alert if >2σ deviation
- [x] 6.3 Implement `check_app_anomaly(current_app, baseline, hour)` — returns alert if different from typical app for 3+ consecutive checks
- [x] 6.4 Implement debounce logic — prevent repeat alerts within `PROACTIVE_ANOMALY_COOLDOWN` seconds (default 1800)

## 7. Contextual Suggestions Module

- [x] 7.1 Create `proactive/suggestions.py` with rule evaluation engine that matches conditions against current context
- [x] 7.2 Create default rules file `config/proactive_rules.json` with terminal-update, git-conflict, and morning-planner rules
- [x] 7.3 Implement suggestion cooldown (default 30 minutes) to prevent annoyance
- [x] 7.4 Format suggestions as polite questions starting with "Sir, ..."

## 8. Main.py Integration

- [x] 8.1 Import `ProactiveEngine`, `ConversationState`, `ProactiveQueue` into `main.py`
- [x] 8.2 Initialize `conversation_state` and `proactive_queue` in `JarvisLive.__init__()`
- [x] 8.3 Add engine task to `_run()` TaskGroup — `engine = ProactiveEngine(conversation_state, proactive_queue, ...)`
- [x] 8.4 Wire proactive queue drain into `_receive_audio()` turn-complete and silence-detection paths
- [x] 8.5 Wire `conversation_state.is_active` toggle around tool execution and audio playback

## 9. Configuration & Prompt

- [x] 9.1 Add env var documentation to `run.txt` for all `PROACTIVE_*` configuration variables with defaults
- [x] 9.2 Update `core/prompt.txt` to inform Jarvis of its proactive capabilities — that it can give daily briefings, detect patterns, notice anomalies, and offer suggestions
- [x] 9.3 Add cooldown and enabling/disabling instructions to the prompt so Jarvis knows when it should or should not be proactive

## 10. Testing & Verification

- [x] 10.1 Write unit tests for `query_patterns()` with mock episode data
- [x] 10.2 Write unit tests for pattern detection heuristics (`detect_time_patterns`, `detect_frequency_patterns`)
- [x] 10.3 Write unit tests for anomaly detection math (>2σ deviation, debounce logic)
- [x] 10.4 Write unit tests for suggestion rule engine matching
- [x] 10.5 Write integration test: engine starts, briefing fires on first run, doesn't fire again same day
- [x] 10.6 Verify conversation state correctly blocks proactive speech during active conversation
- [x] 10.7 Test reconnect cycle: engine task creates fresh on reconnect, reads last_briefing_date, skips duplicate briefing
