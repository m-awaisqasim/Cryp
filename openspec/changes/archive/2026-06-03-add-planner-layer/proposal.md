## Why

When a user asks Cryp to do something complex, the assistant currently jumps straight into the ReAct loop and only narrates the result at the end. The user has no visibility into what Cryp is about to do, which makes long multi-step goals feel opaque and "black box". Adding a thin Planner Layer in front of `agent_task` lets Cryp announce a clear, numbered, human-readable plan out loud before it starts executing, so the user knows what's coming and can intervene if needed.

## What Changes

- Add a new `agent/planner_layer.py` module that:
  - Intercepts `agent_task` calls before they reach the ReAct loop.
  - Calls Gemini (default model `gemini-2.0-flash`) with a dedicated planning prompt to produce a numbered, human-readable plan for the goal.
  - Speaks the plan to the user via the existing UI / `speak` system.
  - Waits a short configurable pause (default ~1.5s) so the user can react.
  - Hands off execution to the existing `ReactAgentLoop` from `agent/react_loop.py` unchanged.
- Wire the Planner Layer into the `agent_task` branch in `main.py` so the existing ReAct execution path is preserved when planning is disabled or fails.
- Add a config flag to enable/disable the planner, and a threshold that decides when a goal is "complex enough" to be planned (e.g., based on goal length, presence of conjunctions, or always-on).
- Add a way to surface the plan in the UI log in addition to speaking it, so the user can read it back.
- Preserve direct tool calls (`browser_control`, `file_processor`, `computer_control`, etc.) completely untouched.
- Fall back gracefully to the existing ReAct execution if planning fails (no plan returned, JSON parse error, model error, etc.).

## Capabilities

### New Capabilities
- `planner-layer`: A new capability that adds a planning step in front of `agent_task`. It produces a numbered plan via Gemini, speaks it to the user, waits briefly, and then hands off to the existing ReAct loop.

### Modified Capabilities
- `react-agent-loop`: The existing ReAct loop itself is **not** modified. A new requirement is added to clarify that the ReAct loop accepts an optional pre-computed plan / context so that the Planner Layer can pass structured guidance into the first user message (without changing the loop's iteration model).

## Impact

- `main.py` — the `agent_task` branch in `_execute_tool` will call the new planner before invoking `ReactAgentLoop.run`.
- `agent/react_loop.py` — minimal change: optional parameter to inject planner context into the first user message; no change to the iteration logic.
- `agent/config.py` — add planner toggle, model name, wait duration, and complexity threshold.
- `agent/planner_layer.py` — new module.
- UI — the existing `write_log` is used to display the plan; no new UI components required.
- Dependencies: uses the existing `google.generativeai` / `core.gemini_compat` already used by `agent/planner.py` and `agent/react_loop.py`. No new packages.
- The legacy `agent/planner.py` (offline static planner) is left in place; the new `planner_layer` is additive and lives next to it.
