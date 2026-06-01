## 1. ReAct Loop Foundation

- [ ] 1.1 Create `agent/react_loop.py` with a ReAct runner class and small data structures for actions, observations, and final results.
- [ ] 1.2 Add configuration defaults for maximum iterations, observation length, malformed-output retries, and blocked tool names.
- [ ] 1.3 Implement safe JSON action parsing for `tool` and `finish` actions.
- [ ] 1.4 Implement observation formatting and truncation for long tool outputs and tool errors.

## 2. Tool Registry and Execution Adapter

- [ ] 2.1 Build the ReAct tool registry from `TOOL_DECLARATIONS`.
- [ ] 2.2 Exclude `agent_task` and any other recursive/internal-only tools from ReAct selection.
- [ ] 2.3 Add an async executor callback in `main.py` that adapts ReAct tool requests into the existing `_execute_tool` path.
- [ ] 2.4 Ensure ReAct observations preserve the returned result string from `_execute_tool`.

## 3. Agent Task Integration

- [ ] 3.1 Replace the current `agent_task` branch in `JarvisLive._execute_tool` with ReAct loop execution.
- [ ] 3.2 Preserve the public `agent_task` tool declaration and input schema.
- [ ] 3.3 Return the ReAct final answer through the normal Gemini `FunctionResponse` shape.
- [ ] 3.4 Add cancellation checks before each model call and before each tool execution.

## 4. Model Prompting and Safety

- [ ] 4.1 Create a ReAct system prompt that includes the user goal, available tools, schema expectations, and finish criteria.
- [ ] 4.2 Keep internal reasoning out of UI logs and final user-facing output.
- [ ] 4.3 Convert invalid tool names, blocked recursive tool requests, and malformed model output into observations.
- [ ] 4.4 Stop with a clear partial/failure message when max iterations are reached.

## 5. Cleanup

- [ ] 5.1 Remove the body of `AgentExecutor` in `agent/task_queue.py`
      and replace it with a call to the new ReAct runner. Keep the
      class shell so no imports break.
- [ ] 5.2 Delete any dead planning/replanning logic that is no longer
      reachable after the ReAct integration.

## 6. Tests and Verification

- [ ] 6.1 Add unit tests for JSON action parsing, malformed output handling, and finish detection.
- [ ] 6.2 Add tests for tool registry filtering so `agent_task` cannot be selected recursively.
- [ ] 6.3 Add tests for observation truncation and error observation formatting.
- [ ] 6.4 Add an integration-style test using a fake model and fake tool executor to verify reason-act-observe-finish sequencing.
- [ ] 6.5 Run Python compile checks and existing smoke tests.
