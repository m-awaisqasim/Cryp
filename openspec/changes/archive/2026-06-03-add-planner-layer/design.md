## Context

Cryp routes any tool call from Gemini through `main.py` `_execute_tool`. For the `agent_task` tool, the current code (around `main.py:800`) builds a tool registry and invokes `ReactAgentLoop.run()` directly, with no narration before execution. The user only hears the final answer.

Two planner-like artifacts already exist in the codebase:
- `agent/planner.py` — a static, prompt-only "planner" that emits a JSON list of steps for the goal. It is **not imported anywhere** in `main.py` or the agent modules. We keep it untouched.
- `agent/react_loop.py` — the live ReAct executor used today.

The ReAct loop has well-defined requirements (`openspec/specs/react-agent-loop/spec.md`): bounded iterations, structured tool/finish actions, concise observations, recursive `agent_task` blocked, cancellation honored. None of those may change. The new Planner Layer must wrap — not replace — that loop.

The UI/voice path is `self.speak(text)` (`main.py:631`) which posts to the Gemini live session, plus `self.ui.write_log(line)` for the on-screen log. Both are already used throughout the codebase and are safe to call from inside the `agent_task` branch.

Model access: `config/api_keys.json` holds `gemini_api_key`, and `core/gemini_compat.py` provides a thin compat shim. `make_default_model_caller` in `react_loop.py` already shows the canonical pattern: configure once, then call `model.generate_content` inside `run_in_executor`.

## Goals / Non-Goals

**Goals:**
- Add a clearly-named `PlannerLayer` (in `agent/planner_layer.py`) that sits between `agent_task` entry and `ReactAgentLoop.run`.
- Generate a numbered, human-readable plan using `gemini-2.0-flash` (configurable).
- Speak the plan via `self.speak` and log it via `self.ui.write_log`.
- Wait a short, configurable pause (~1.5s default) before starting execution.
- Hand off to the **existing** `ReactAgentLoop` unchanged in behavior; only an optional `plan_context` string is added to its first user message so the loop is aware of the announced plan.
- Be a no-op (skip planning) for goals that fail a "complexity" heuristic, and a clean fallback if Gemini errors.
- Preserve all direct tool calls (`browser_control`, `file_processor`, `computer_control`, `game_updater`, etc.) completely.

**Non-Goals:**
- Replacing or rewriting the ReAct loop.
- Changing the ReAct iteration model, blocked-tool set, or observation handling.
- Adding new UI components (just use `write_log`).
- Modifying `agent/planner.py` (the legacy static planner).
- Replanning mid-execution (the existing `replan` in `agent/planner.py` is left as-is; out of scope for this change).
- Streaming the plan token-by-token — we wait for the full plan, then speak it.

## Decisions

### 1. New module `agent/planner_layer.py` rather than extending `agent/planner.py`

`agent/planner.py` is a static prompt-driven planner that returns a JSON plan but is never invoked. Folding the new behavior in would change its API and create confusion about which is "the planner". A new file makes intent obvious (`planner_layer` = the runtime interceptor in front of `agent_task`) and keeps the legacy file as a pure utility.

Alternatives considered:
- Reuse `agent/planner.py` directly → rejected: its prompt returns a JSON plan for execution, not a human-readable narration; its model is `gemini-2.5-flash-lite` which is the wrong model per the change description; and it's not currently wired in.
- Inline planning inside `main.py` → rejected: pollutes the orchestrator and is hard to test.

### 2. Synchronous planning call (no streaming)

The Planner Layer calls Gemini once, awaits the full plan, then speaks it as one block. Streaming would complicate TTS handoff (the live `speak` path uses `send_client_content` with `turn_complete=True`, which is not designed for incremental chunks) and risks a plan that "drifts" mid-speech if the model is cut off.

### 3. Plan prompt asks for prose, not JSON

The planner prompt asks Gemini to return a numbered, prose plan (e.g. `"1. Search the web for ... 2. Save the result to a notepad file on the desktop."`). This is the natural unit for `speak()`. The legacy `agent/planner.py` keeps its JSON format because it targets execution, not narration.

### 4. Optional `plan_context` argument on `ReactAgentLoop.run`

The ReAct loop's first user message is built by `_build_user_message(goal, observations)`. We extend it to accept an optional `plan_context: str | None = None` that gets prepended as a `PLANNED APPROACH` block. This is the **only** change to `react_loop.py`. The model can use it as a hint but is still required to pick concrete tools from the registry; nothing about iteration, blocked tools, or observation handling changes.

### 5. Complexity heuristic to decide when to plan

We don't want to plan a one-shot goal like "open the clock app". Default heuristic: plan when the goal is longer than N characters **or** contains coordination words (`and`, `then`, `after`, `;`). Both threshold and the word list live in `agent/config.py` under a new `PlannerConfig` dataclass. The check is opt-out — there is also a `planner_always_on` flag for users who want every `agent_task` announced.

### 6. Configuration via `agent/config.py` `PlannerConfig`

A small `PlannerConfig` dataclass alongside `ReactConfig`:

```python
@dataclass
class PlannerConfig:
    enabled: bool = True
    model_name: str = "gemini-2.0-flash"
    speak_wait_seconds: float = 1.5
    min_goal_chars: int = 40
    coordination_words: tuple[str, ...] = (" and ", " then ", " after ", ";", " plus ")
    max_plan_chars: int = 800
```

Read at runtime; toggling `enabled = False` short-circuits the planner to the existing ReAct path so users and tests can disable it.

### 7. Cancellation flows through

The existing `cancel_event` is created in `main.py:805` and stored on `self._react_cancel_event`. The Planner Layer checks the event while waiting and while waiting for the Gemini call, so a user "stop" command aborts planning cleanly.

### 8. Fallback on any planning failure

If Gemini returns empty text, the model call raises, the JSON-ish fence stripping fails, the plan is empty, or `speak` raises, the Planner Layer logs a warning and proceeds straight to `ReactAgentLoop.run`. The user-facing behavior must be no worse than today.

## Risks / Trade-offs

- **Extra latency on `agent_task`** → ~1 model round-trip (typical <2s) + 1.5s wait. *Mitigation*: gated by heuristic; can be disabled via `PlannerConfig.enabled`; complex goals already take longer than that, so the relative cost is small.
- **Plan may diverge from actual execution** → the ReAct model might pick different tools than the announced plan. *Mitigation*: announce the plan as a "here's what I'm going to do" not "I will definitely do"; allow ReAct to deviate. Documented in the planner prompt.
- **Live session TTS queueing** → `speak()` posts to the live session; if the user is mid-utterance, queuing multiple plan lines could pile up. *Mitigation*: collapse the plan into a single string (one `speak` call), not one speak per step. If the model returns very long text, truncate at `max_plan_chars` with an ellipsis.
- **Heuristic misclassification** → a one-step goal may be planned unnecessarily, or a complex one skipped. *Mitigation*: defaults are conservative (plan when in doubt); expose `planner_always_on` for users who prefer the announcement; log the decision in `write_log`.
- **Model dependency for the planner** → if the Gemini API is down, every `agent_task` would be delayed. *Mitigation*: full try/except fallback to direct ReAct execution. Planning never blocks execution; worst case, behavior is identical to today.

## Migration Plan

This is an additive change behind a feature flag.

1. Ship `agent/planner_layer.py` and `PlannerConfig` with `enabled=True` default.
2. Wire the layer into the `agent_task` branch of `main.py` `_execute_tool`:
   - Build planner.
   - If disabled or goal fails heuristic → call existing ReAct path unchanged.
   - Else call `planner.announce(goal, ...)`, then call existing ReAct path.
3. Add a single opt-out: setting `PlannerConfig.enabled = False` (or via env var `CRYP_PLANNER=off`) restores the previous behavior with zero other changes.
4. Rollback: set `enabled=False`. No DB or schema migrations.

## Open Questions

- Should the spoken plan include estimated timing ("this should take about 10 seconds")? Leaning no for v1 — adds prompt complexity without clear value.
- Should the planner respect a user-specific "skip planning for goal X" memory entry? Not in scope; can be added later.
- Should the plan be saved to episodic memory? Useful for later recall, but adds a write path. Defer to a follow-up change.
