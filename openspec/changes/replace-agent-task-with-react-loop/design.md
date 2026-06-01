## Context

`main.py` currently exposes `agent_task` as the high-level tool for complex goals. When Gemini calls it, the code submits the goal to `agent.task_queue`, which eventually executes `AgentExecutor`. `AgentExecutor` creates an up-front plan, runs each planned step, optionally retries or replans, then summarizes the result.

That approach works for predictable workflows but is not ideal for open-ended desktop tasks where observations from one tool call should determine the next action. The new design introduces a ReAct loop: reason about the current state, act with one allowed tool, observe the result, and repeat until the goal is done.

The implementation must preserve existing direct tool behavior. Existing tools already have routing and UI side effects in `JarvisLive._execute_tool`; the ReAct loop should reuse that route rather than duplicate action-module dispatch logic.

## Goals / Non-Goals

**Goals:**

- Replace `agent_task` execution with an iterative ReAct loop.
- Keep `agent_task` as the public high-level goal tool.
- Use `TOOL_DECLARATIONS` as the source of available tool names, descriptions, and parameter schemas.
- Execute selected tools through the existing `_execute_tool` path so current logging, player/UI handling, and action behavior remain intact.
- Prevent recursive calls to `agent_task`.
- Bound the loop with max iterations, error observations, cancellation, and explicit finish output.
- Preserve direct tool calls outside `agent_task`.

**Non-Goals:**

- Do not rewrite existing `actions/*` tools.
- Do not remove task queue support unless it is no longer needed after implementation.
- Do not add a new external LLM provider or dependency.
- Do not change the user-facing names of existing tools.
- Do not expose private chain-of-thought in UI logs or final responses.

## Decisions

### Decision: Add a dedicated ReAct loop module under `agent/`

Create a new module such as `agent/react_loop.py` containing a `ReactAgentLoop` class or equivalent async runner. The runner owns iteration state, observation history, prompt construction, model calls, and finish detection.

Rationale: keeping ReAct orchestration outside `main.py` avoids turning `_execute_tool` into a large agent controller while still allowing `main.py` to provide the tool executor callback.

Alternative considered: embed the full loop inside `JarvisLive._execute_tool`. This keeps everything local but makes `main.py` harder to test and maintain.

### Decision: Inject an async tool executor callback

The ReAct runner should accept a callback that receives a selected tool name and parameters and returns an observation string. In `main.py`, that callback should create a lightweight function-call adapter and delegate to `_execute_tool`.

Rationale: `_execute_tool` already knows how to run all existing tools with the right `player`, `speak`, UI state, and error behavior. Reusing it prevents a second, divergent tool router.

Alternative considered: reuse `agent.executor._call_tool`. That function directly imports action modules and does not preserve all UI/session behavior from `main.py`.

### Decision: Filter available tools for ReAct

The ReAct prompt should include all normal tools from `TOOL_DECLARATIONS` except `agent_task` and any internal-only tool that would cause recursion or silent memory writes unless explicitly needed.

Rationale: recursive `agent_task` calls can create nested loops and runaway execution. The loop should decide between concrete tools.

Alternative considered: allow all tools and rely on prompting to avoid recursion. That is weaker than enforcing the rule in code.

### Decision: Use structured JSON actions from the model

Each iteration should ask the model for a strict JSON object with one of two actions:

- `{"type": "tool", "tool": "<name>", "parameters": {...}, "summary": "<brief rationale>"}`
- `{"type": "finish", "answer": "<final user-facing result>"}`

The implementation should parse JSON defensively, retry once for malformed output, and convert model/tool errors into observations.

Rationale: structured output makes tool selection testable and prevents fragile free-form parsing.

Alternative considered: parse classic `Thought/Action/Observation` text. This is easier to read but more error-prone in code.

### Decision: Store concise observations

The loop should store observations as bounded text records containing iteration number, tool name, parameters summary, and result/error summary. Long tool outputs should be truncated before being sent back into the model.

Rationale: many tools can return large web, file, or transcript content. Bounded observations protect model context and keep the loop responsive.

Alternative considered: keep full observations. This improves fidelity but risks context overflow and slower response.

### Decision: Preserve public result behavior

When `agent_task` finishes, `_execute_tool` should return a normal `FunctionResponse` containing the final ReAct answer. If the loop cancels, times out, or reaches max iterations, return a clear failure or partial-completion message.

Rationale: callers already expect `_execute_tool` to produce a result string. Keeping that shape avoids breaking Gemini Live tool response handling.

### Decision: Use gemini-2.0-flash for ReAct reasoning calls

Internal ReAct reasoning calls SHALL use `gemini-2.0-flash` (not the
live audio model). The live session model handles voice I/O; the ReAct
loop needs fast synchronous text completions. Use `google.generativeai`
with `model="gemini-2.0-flash"` and read the API key from
`config/api_keys.json` under the key `gemini_api_key`.

Rationale: separates voice session concerns from agent reasoning.
Using the live audio model for text-only reasoning is wasteful and
slower.

## Risks / Trade-offs

- ReAct loop selects the wrong tool -> constrain the available tool list, include schemas, and feed back errors as observations.
- Loop runs too long -> enforce max iterations and support cancellation.
- Tool output is too large -> truncate observations and keep a final summary.
- Model emits malformed JSON -> add repair/retry logic and fail with a clear observation if parsing still fails.
- Recursive `agent_task` call -> remove `agent_task` from the ReAct tool registry.
- Private reasoning leakage -> log only concise action summaries and final answers, not hidden reasoning text.
- Existing task queue assumptions break -> keep the public `agent_task` interface and update queue execution to call the new ReAct runner if queue-based execution remains.

## Migration Plan

1. Add `agent/react_loop.py` with the ReAct runner and small data structures for steps/observations.
2. Update `main.py` so `agent_task` invokes the ReAct runner instead of the static planner path.
3. Build the allowed ReAct tool list from `TOOL_DECLARATIONS` minus recursive/internal tools.
4. Add an adapter that lets the runner call `_execute_tool` and receive a plain observation string.
5. Keep old planner files in place during the first implementation unless they become unused and safe to remove.
6. Add focused tests for JSON parsing, max-iteration behavior, recursion filtering, and callback execution.
7. Verify direct tool calls still work and `agent_task` returns a normal function response.
