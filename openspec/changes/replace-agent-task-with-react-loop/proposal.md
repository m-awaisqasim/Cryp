## Why

The current `agent_task` path relies on up-front planning and step execution, which can be brittle when tool results change the next best action. A ReAct-style loop will let Cryp reason, choose a tool, observe the result, and adapt until the user goal is complete.

## What Changes

- Replace the current `agent_task` execution path with an iterative ReAct reasoning loop.
- Add a ReAct controller that repeatedly produces a thought, selects one existing tool, executes it, records the observation, and decides whether to continue or finish.
- Integrate the loop with the existing `TOOL_DECLARATIONS` contract so available tools and parameter schemas remain centralized in `main.py`.
- Route ReAct tool execution through the existing `_execute_tool` behavior so current tools keep their existing side effects, UI logging, error handling, and return shape.
- Preserve all existing direct tool calls such as `open_app`, `browser_control`, `file_processor`, `computer_control`, `game_updater`, and `save_memory`.
- Add bounded iteration, clear completion criteria, error observations, and cancellation handling to avoid infinite loops.
- No breaking changes to user-facing tool names except the internal behavior of `agent_task`.

## Capabilities

### New Capabilities

- `react-agent-loop`: Defines the behavior for iterative goal execution through reason, act, observe, and finish cycles.

### Modified Capabilities

- None.

## Impact

- Affected code:
  - `main.py`: `agent_task` handling, tool declaration guidance, and ReAct integration point.
  - `agent/`: new or updated ReAct loop module that can call existing tools through a provided executor callback.
  - `agent/task_queue.py`: may continue to queue long-running goals, but queued work should execute through the ReAct loop instead of the current static planner path.
  - Existing `actions/*` modules: no behavior changes expected.
- APIs and contracts:
  - `TOOL_DECLARATIONS` remains the source of truth for model-visible tools.
  - `_execute_tool` remains the main implementation path for executing existing tools.
  - `agent_task` remains available as the high-level user-facing goal tool.
- Risks:
  - The loop must not recursively call `agent_task`.
  - The loop must avoid unbounded execution.
  - Tool observations must be concise enough to fit model context while preserving useful state.
