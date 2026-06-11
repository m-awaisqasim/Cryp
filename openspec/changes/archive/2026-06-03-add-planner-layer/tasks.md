## 1. Configuration

- [x] 1.1 Add `PlannerConfig` dataclass to `agent/config.py` with fields: `enabled`, `model_name`, `speak_wait_seconds`, `min_goal_chars`, `coordination_words`, `max_plan_chars`, `planner_always_on`
- [x] 1.2 Add `default_planner_config()` factory in `agent/config.py` returning a `PlannerConfig` with `enabled=True`, `model_name="gemini-2.0-flash"`, `speak_wait_seconds=1.5`, `min_goal_chars=40`, default coordination words, `max_plan_chars=800`, `planner_always_on=False`
- [x] 1.3 Honor env var override `CRYP_PLANNER=off` to disable the planner at startup

## 2. Planner Layer module

- [x] 2.1 Create `agent/planner_layer.py` with module docstring describing the role (intercept `agent_task`, announce a plan, hand off to ReAct)
- [x] 2.2 Define `PLANNER_PROMPT` system prompt instructing Gemini to return a numbered, human-readable plan (prose, not JSON) and forbidding tool internals / invented tools
- [x] 2.3 Implement `is_complex_goal(goal: str, config: PlannerConfig) -> bool` heuristic checking goal length and coordination words, with `planner_always_on` override
- [x] 2.4 Implement `generate_plan(goal: str, config: PlannerConfig) -> str | None` that calls Gemini via `google.generativeai as genai`, strips code fences, and returns the plan text or `None` on any failure. Use `asyncio.get_event_loop().run_in_executor` for the sync Gemini call
- [x] 2.5 Implement `truncate_plan(plan: str, max_chars: int) -> str` that clips long plans with an ellipsis marker
- [x] 2.6 Implement `PlannerLayer.announce(goal: str, *, speak, write_log, cancel_flag) -> str | None` that composes the above, speaks once, writes to the log, sleeps `speak_wait_seconds`, and returns the plan (or `None` on failure / disabled / simple goal). Must check `cancel_flag` during the model call and during the wait.

## 3. ReAct loop integration

- [x] 3.1 Add optional `plan_context: str | None = None` parameter to `ReactAgentLoop.run` in `agent/react_loop.py` (no other behavior changes)
- [x] 3.2 In `_build_user_message`, when `plan_context` is non-empty, prepend a `PLANNED APPROACH` block to the user message; otherwise keep the existing format
- [x] 3.3 Add a unit test in `tests/test_react_loop.py` verifying that when `plan_context` is provided, the model call receives a user message that includes the plan under a `PLANNED APPROACH` heading, and that without it the message is unchanged
- [x] 3.4 Add a unit test verifying the loop's behavior (blocked tools, iteration cap, cancellation) is unchanged regardless of `plan_context`

## 4. Wire into main.py

- [x] 4.1 In `main.py`, in the `agent_task` branch of `_execute_tool`, after creating `cancel_event`, build a `PlannerConfig` (from `default_planner_config()` plus any env override)
- [x] 4.2 Instantiate `PlannerLayer` and call `announce(goal=..., speak=self.speak, write_log=self.ui.write_log, cancel_flag=cancel_event)` to obtain the plan (or `None`)
- [x] 4.3 Pass the plan as the new `plan_context` argument to `ReactAgentLoop.run(goal=..., executor=..., cancel_flag=..., plan_context=plan)` — wrap the call so a `TypeError` for the new arg falls back to the old signature if an older `ReactAgentLoop` is somehow in use (defensive)
- [x] 4.4 Leave all other `elif name == "..."` branches (`browser_control`, `file_processor`, `computer_control`, `game_updater`, `flight_finder`, `web_search`, `youtube_video`, `screen_process`, `computer_settings`, `desktop_control`, `code_helper`, `dev_agent`, `recall_episodes`, `shutdown_cryp`, etc.) byte-identical
- [x] 4.5 Leave `TOOL_DECLARATIONS` byte-identical — do not register the planner as a tool

## 5. Tests

- [x] 5.1 Add `tests/test_planner_layer.py` covering: `is_complex_goal` heuristic (simple vs complex, always-on override), `generate_plan` returns `None` on model error and on empty output, `truncate_plan` clips with marker, `announce` calls `speak` exactly once with a non-empty plan, calls `write_log` once, sleeps for `speak_wait_seconds`, returns the plan, and skips speaking/logging/waiting when planning is disabled or goal is simple
- [x] 5.2 Add test that `announce` returns `None` and does not speak when `speak` raises
- [x] 5.3 Add test that `announce` aborts and returns `None` if `cancel_flag` is set during the model call and during the wait
- [x] 5.4 Run the existing test suite (`pytest tests/`) and confirm all existing tests still pass; in particular, all `tests/test_react_loop.py` cases

## 6. Verification

- [x] 6.1 Run `python -m py_compile agent/planner_layer.py agent/react_loop.py agent/config.py main.py` to confirm syntax
- [x] 6.2 Run `openspec validate add-planner-layer --strict` and resolve any reported issues
- [x] 6.3 Run the full test suite one final time and confirm zero regressions
- [x] 6.4 Manual smoke: temporarily set `PlannerConfig.enabled = False` and confirm `agent_task` behavior is identical to the previous release; then re-enable and confirm an announced plan is spoken + logged for a complex goal like "research mechanical engineering and save it to a notepad file"
