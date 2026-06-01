## 1. Storage & Episode Schema

- [ ] 1.1 Create `memory/episodic/` directory lazily (in code, on first write); add a `.gitkeep` placeholder file under `memory/episodic/` so the empty folder is tracked
- [ ] 1.2 Define the episode JSON shape as a constant docstring at the top of the new section in `memory_manager.py` (id, started_at, ended_at, duration_minutes, summary, topics, decisions, user_turns, assistant_turns, tools_used)
- [ ] 1.3 Add module-level constants in `memory_manager.py`: `EPISODIC_DIR`, `EPISODE_MAX_CHARS = 2000`, `EPISODES_PROMPT_MAX_CHARS = 1500`, `DEFAULT_RECENT_EPISODES = 5`, `MAX_EPISODE_FILES = 500`

## 2. Episodic Helpers in memory_manager.py (additive)

- [ ] 2.1 Implement `save_episode(episode: dict) -> Path` — validates required keys, generates `id` if missing, truncates `summary` to `EPISODE_MAX_CHARS`, writes atomically under the existing `_lock`, returns the written path
- [ ] 2.2 Implement `load_recent_episodes(n: int = DEFAULT_RECENT_EPISODES) -> list[dict]` — lists `*.json` in `EPISODIC_DIR`, sorts by `started_at` descending, loads up to `n`, silently skips malformed files
- [ ] 2.3 Implement `search_episodes(query: str, limit: int = 5) -> list[dict]` — case-insensitive substring match over `summary` + each item in `topics`; returns newest-first
- [ ] 2.4 Implement `format_episodes_for_prompt(episodes: list[dict], max_chars: int = EPISODES_PROMPT_MAX_CHARS) -> str` — produces a header `[RECENT CONVERSATIONS — reference naturally, do not recite]` followed by one line per episode: `- <YYYY-MM-DD>: <summary first sentence> [topics: a, b, c]`; trims oldest-first to fit `max_chars`; returns `""` if no episodes
- [ ] 2.5 Implement `prune_episodes(keep_last: int = MAX_EPISODE_FILES) -> int` — deletes oldest files when count exceeds limit; returns number deleted
- [ ] 2.6 Verify no existing function signatures in `memory_manager.py` were changed (re-read `load_memory`, `update_memory`, `save_memory`, `format_memory_for_prompt`, `remember`, `forget`)

## 3. Summarization

- [ ] 3.1 Add `summarize_session(turns: list[dict], api_key: str) -> dict` to `memory_manager.py` — calls `gemini-2.5-flash` via `google.genai` text endpoint with a strict JSON prompt requesting `{summary, topics, decisions}`; uses `response_mime_type="application/json"`
- [ ] 3.2 Add `_fallback_summary(turns: list[dict], tools_used: list[str]) -> dict` — deterministic local summary used when the API call raises any exception
- [ ] 3.3 Wrap `summarize_session` in try/except in the caller and route to `_fallback_summary` on any error; log the failure to stdout

## 4. Session Lifecycle in main.py

- [ ] 4.1 Add instance attributes to `JarvisLive.__init__`: `self._episode_turns: list[dict] = []`, `self._episode_tools: list[str] = []`, `self._episode_started_at: datetime | None = None`, `self._last_rollover_ts: float = 0.0`
- [ ] 4.2 In `_receive_audio()` where `turn_complete` is handled, append `{"role": "user", "text": full_in, "ts": iso_now}` and `{"role": "assistant", "text": full_out, "ts": iso_now}` to `self._episode_turns` after the existing UI log writes (only when non-empty); cap buffer at 200 entries (drop oldest)
- [ ] 4.3 In `_execute_tool()`, append `name` to `self._episode_tools` after the tool dispatch block (deduped)
- [ ] 4.4 Set `self._episode_started_at = datetime.now()` inside `run()` immediately after the first successful `connect()` enters the `try` block, only if it is still `None` (so reconnects do not reset it)
- [ ] 4.5 Add async helper `_finalize_session_episode(self, reason: str)` on `JarvisLive` that: builds an episode dict from the buffers, calls `summarize_session` (off-thread via `run_in_executor`), merges results, calls `save_episode`, then clears the buffers and resets `self._episode_started_at`
- [ ] 4.6 Add async helper `_episode_rollover_task(self)` that loops `await asyncio.sleep(60)`, and if `len(self._episode_turns) >= 20` AND now-`_last_rollover_ts` ≥ 1800s, calls `_finalize_session_episode("rollover")` and updates `_last_rollover_ts`
- [ ] 4.7 Schedule `_episode_rollover_task` inside the existing `asyncio.TaskGroup()` block in `run()` alongside the four existing tasks
- [ ] 4.8 Call `_finalize_session_episode("shutdown")` from the `shutdown_jarvis` branch in `_execute_tool` BEFORE the 1-second sleep in the `_shutdown` thread (use `asyncio.run_coroutine_threadsafe` from the shutdown thread with a 5s timeout)
- [ ] 4.9 Register an `atexit` safety-net that schedules `_finalize_session_episode("atexit")` only if the buffer is non-empty and the event loop is still running

## 5. Prompt Injection in _build_config

- [ ] 5.1 At the top of `main.py`, import the new helpers: `from memory.memory_manager import load_recent_episodes, format_episodes_for_prompt, prune_episodes`
- [ ] 5.2 In `_build_config()`, after the existing `mem_str` block and before appending `sys_prompt`, read `n = int(os.getenv("EPISODIC_RECENT_COUNT", "5"))`, then `episodes_str = format_episodes_for_prompt(load_recent_episodes(n))` and append to `parts` when non-empty
- [ ] 5.3 Call `prune_episodes()` once at the top of `_build_config()` (cheap, idempotent) so first-of-day connects also trim the directory

## 6. Optional recall_episodes Tool

- [ ] 6.1 Add `ENABLE_RECALL_TOOL = os.getenv("ENABLE_RECALL_TOOL", "0") == "1"` constant in `main.py`
- [ ] 6.2 Define a `RECALL_TOOL_DECL` dict matching the schema in `design.md` §7
- [ ] 6.3 When building `TOOL_DECLARATIONS` (or right before passing it to `_build_config`), conditionally append `RECALL_TOOL_DECL` when `ENABLE_RECALL_TOOL` is true
- [ ] 6.4 In `_execute_tool`, add an `elif name == "recall_episodes":` branch that calls `search_episodes(args.get("query", ""), int(args.get("limit", 3)))` and returns formatted episode lines as the result string

## 7. Tests & Verification

- [ ] 7.1 Add `tests/test_episodic_memory.py` with unit tests: `save_episode` round-trip, `load_recent_episodes` ordering, `search_episodes` case-insensitivity, `format_episodes_for_prompt` 1500-char cap, `prune_episodes` enforces limit
- [ ] 7.2 Add a test confirming `load_memory()` / `update_memory()` behavior is unchanged before and after importing the new helpers (regression guard for backward compatibility requirement)
- [ ] 7.3 Mock the Gemini call in a test for `summarize_session` to verify the JSON-shape contract and the fallback path on API exception
- [ ] 7.4 Manually verify: run `python main.py`, have a short conversation, trigger `shutdown_jarvis`, and confirm a new file appears in `memory/episodic/` with the expected fields
- [ ] 7.5 Manually verify: restart Jarvis and confirm the system instruction logged at startup contains a "Recent conversations" block referencing the prior session

## 8. Cleanup

- [ ] 8.1 Add `memory/episodic/*.json` to `.gitignore` (keep `.gitkeep`)
- [ ] 8.2 Append a short "Episodic memory" subsection to `readme.md` describing where episodes are stored and the `EPISODIC_RECENT_COUNT` / `ENABLE_RECALL_TOOL` env vars
- [ ] 8.3 Run any project linter/formatter already in use (check `requirements.txt` / `setup.py` for ruff/black) on the changed files
