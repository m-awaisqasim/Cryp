## 1. Core Version Source

- [x] 1.1 Create `core/version.py` with `__version__`, `__build_date__`, and `__model__` constants as the single source of truth for Jarvis's version identity
- [x] 1.2 Update `main.py` to import and use `VERSION` from `core/version.py` in `_build_config()` date/time injection

## 2. In-Memory Metrics Tracking

- [ ] 2.1 Add a `SessionMetrics` dataclass to `main.py` (or a new `core/metrics.py`) with fields: `start_time`, `tool_call_counts: dict[str, int]`, `turn_count`, `agent_task_count`
- [ ] 2.2 Initialize `SessionMetrics` in `JarvisLive.__init__()` with `start_time = datetime.now()`
- [ ] 2.3 Increment `tool_call_counts[tool_name]` in `_execute_tool()` after every successful tool dispatch
- [ ] 2.4 Increment `turn_count` in `_receive_audio()` on each user turn (transcript received from Gemini)
- [ ] 2.5 Track `agent_task_count` by incrementing when `agent_task` tool is dispatched in `_execute_tool()`

## 3. `jarvis_status` Tool — Action File

- [x] 3.1 Create `actions/jarvis_status.py` with function `jarvis_status(parameters: dict, player: JarvisUI, **kwargs) -> str`
- [x] 3.2 Implement `_handle_status()` — read `JarvisLive.ui` state (LISTENING/THINKING/SPEAKING), compute uptime from session start time, return formatted status string
- [x] 3.3 Implement `_handle_version()` — import `core/version.py` and return version, model, build date
- [x] 3.4 Implement `_handle_memory()` — count entries in `memory/long_term.json`, count files in `memory/episodic/` (cached, 30s TTL), count patterns from `memory_manager.query_patterns()`, return formatted summary
- [x] 3.5 Implement `_handle_activity()` — read `SessionMetrics` from `JarvisLive` (passed via kwargs or a shared reference), format tool call counts, turn count, task count
- [x] 3.6 Implement `_handle_system()` — try `get_health_snapshot()` from daemon, fall back to optional `psutil`, return CPU/RAM/disk or "unavailable"
- [x] 3.7 Wire dispatch from `query` parameter to handler methods

## 4. Main.py Integration

- [x] 4.1 Import `jarvis_status` function and `SessionMetrics` in `main.py`
- [x] 4.2 Add `jarvis_status` entry to `TOOL_DECLARATIONS` with description covering status/version/memory/activity/system queries and parameters schema (query: STRING)
- [x] 4.3 Add `jarvis_status` dispatch branch in `_execute_tool()` that passes `SessionMetrics` via kwargs
- [x] 4.4 Update `core/prompt.txt` to mention that Jarvis has a `jarvis_status` tool for answering self-awareness questions without calling `agent_task`

## 5. Tests

- [x] 5.1 Write unit tests for `actions/jarvis_status.py` — mock memory files, SessionMetrics, and verify each query mode returns correct output format
- [x] 5.2 Write unit test for `core/version.py` — verify version string format matches semver
- [x] 5.3 Write integration test in `main.py` context — mock `_execute_tool()` dispatch and verify jarvis_status is routed correctly
- [x] 5.4 Verify all 21 existing tool declarations still work and `jarvis_status` is the 22nd
