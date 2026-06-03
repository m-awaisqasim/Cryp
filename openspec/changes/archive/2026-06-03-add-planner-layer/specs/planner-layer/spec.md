## ADDED Requirements

### Requirement: Planner Layer intercepts agent_task before ReAct execution

The system SHALL route every `agent_task` call through a Planner Layer that generates a numbered, human-readable plan, speaks it to the user, waits a short configurable pause, and then hands execution off to the existing `ReactAgentLoop` in `agent/react_loop.py`.

#### Scenario: Complex goal receives an announced plan

- **WHEN** the user submits an `agent_task` goal that the planner heuristic classifies as complex
- **THEN** the system SHALL call Gemini with a planning prompt, obtain a numbered plan, speak the plan via the existing `speak` path, write the plan to the UI log, wait the configured pause, and then call `ReactAgentLoop.run` with the original goal

#### Scenario: Simple goal skips the planner

- **WHEN** the user submits an `agent_task` goal that the planner heuristic classifies as simple
- **THEN** the system SHALL bypass the Planner Layer and call `ReactAgentLoop.run` directly with the original goal

#### Scenario: Planner is disabled

- **WHEN** `PlannerConfig.enabled` is `False`
- **THEN** the system SHALL call `ReactAgentLoop.run` directly with no plan announcement, mirroring prior behavior

### Requirement: Planner Layer uses gemini-2.0-flash by default

The system SHALL generate the announced plan by calling Gemini with the model name from `PlannerConfig.model_name`, defaulting to `gemini-2.0-flash`.

#### Scenario: Default model is used

- **WHEN** no override is supplied for `PlannerConfig.model_name`
- **THEN** the Planner Layer SHALL call Gemini with `gemini-2.0-flash` to produce the plan

#### Scenario: Override model is honored

- **WHEN** `PlannerConfig.model_name` is set to a non-default value
- **THEN** the Planner Layer SHALL call Gemini with that model name instead of the default

### Requirement: Planner Layer produces a human-readable numbered plan

The system SHALL prompt Gemini to return a numbered, prose plan suitable for being spoken aloud (for example: `"Step 1: ... Step 2: ..."`), and SHALL refuse to invent tools or reference internal tool internals.

#### Scenario: Plan contains numbered steps

- **WHEN** the Planner Layer receives a non-empty plan string from Gemini
- **THEN** the announced plan SHALL contain a numbered sequence of steps derived from the model output

#### Scenario: Plan is truncated to a maximum length

- **WHEN** the Gemini response is longer than `PlannerConfig.max_plan_chars`
- **THEN** the Planner Layer SHALL truncate the announced plan to that length and append an ellipsis marker

### Requirement: Planner Layer speaks and logs the plan

The system SHALL deliver the plan to the user through both the existing voice path (`speak`) and the existing UI log path (`write_log`), using the same primitives used by direct tool calls.

#### Scenario: Plan is spoken once

- **WHEN** a non-empty plan is produced
- **THEN** the Planner Layer SHALL invoke `speak` exactly once with the plan as a single string

#### Scenario: Plan is written to the UI log

- **WHEN** a non-empty plan is produced
- **THEN** the Planner Layer SHALL invoke `ui.write_log` with a labeled line containing the plan

#### Scenario: Empty plan is not announced

- **WHEN** Gemini returns an empty or whitespace-only plan
- **THEN** the Planner Layer SHALL NOT call `speak` or `write_log` with a plan and SHALL fall through to direct ReAct execution

### Requirement: Planner Layer waits before execution

After producing a plan, the system SHALL pause for `PlannerConfig.speak_wait_seconds` (default 1.5s) so the user has time to react before execution begins.

#### Scenario: Wait is applied after speaking

- **WHEN** a non-empty plan is announced
- **THEN** the Planner Layer SHALL wait at least `PlannerConfig.speak_wait_seconds` seconds before invoking `ReactAgentLoop.run`

#### Scenario: No wait when planner is bypassed

- **WHEN** the Planner Layer is disabled or bypasses planning for a simple goal
- **THEN** the system SHALL NOT insert a planning wait before `ReactAgentLoop.run`

### Requirement: Planner Layer falls back gracefully on failure

The system SHALL treat any planning failure (model error, empty output, parse error, `speak` failure) as a non-fatal condition and SHALL fall through to direct `ReactAgentLoop.run` execution of the original goal.

#### Scenario: Model call raises

- **WHEN** the Gemini planning call raises an exception
- **THEN** the Planner Layer SHALL log a warning, skip announcement, and call `ReactAgentLoop.run` with the original goal

#### Scenario: Model returns empty plan

- **WHEN** the Gemini planning call returns empty or whitespace-only text
- **THEN** the Planner Layer SHALL log a warning, skip announcement, and call `ReactAgentLoop.run` with the original goal

#### Scenario: Speak raises

- **WHEN** `speak(plan)` raises an exception
- **THEN** the Planner Layer SHALL log a warning and still call `ReactAgentLoop.run` with the original goal

### Requirement: Planner Layer does not break direct tool calls

The system SHALL leave all non-`agent_task` tool paths (`browser_control`, `file_processor`, `computer_control`, `game_updater`, `flight_finder`, `web_search`, etc.) untouched and SHALL NOT introduce any new tool names or modify `TOOL_DECLARATIONS`.

#### Scenario: Direct tool call is unchanged

- **WHEN** Gemini calls a direct tool such as `browser_control` or `computer_control`
- **THEN** the system SHALL execute it through the existing direct path and SHALL NOT call the Planner Layer

#### Scenario: TOOL_DECLARATIONS is unchanged

- **WHEN** the Planner Layer is added
- **THEN** the `TOOL_DECLARATIONS` list in `main.py` SHALL remain byte-identical and SHALL NOT include the planner or any new tool name

### Requirement: Planner Layer respects cancellation

The system SHALL honor the existing cancellation event for `agent_task` (already created in `main.py` and stored on `self._react_cancel_event`) during both the planning call and the post-plan wait, so a "stop" command can abort planning cleanly.

#### Scenario: Cancel during planning call

- **WHEN** the cancellation flag is set while Gemini is producing the plan
- **THEN** the Planner Layer SHALL abort planning and SHALL NOT invoke `ReactAgentLoop.run`

#### Scenario: Cancel during wait

- **WHEN** the cancellation flag is set during the post-plan wait
- **THEN** the Planner Layer SHALL abort the wait and SHALL NOT invoke `ReactAgentLoop.run`

### Requirement: Planner Layer passes announced plan to the ReAct loop

The system SHALL pass the announced plan to `ReactAgentLoop` as a non-binding hint so the loop can incorporate it as context, but the loop SHALL still choose concrete tools from the registry and SHALL retain all existing guarantees (bounded iterations, blocked `agent_task`, etc.).

#### Scenario: Plan reaches the first ReAct user message

- **WHEN** a non-empty plan is produced and the ReAct loop is started
- **THEN** the announced plan SHALL appear in the first user message passed to the ReAct model as a "PLANNED APPROACH" block

#### Scenario: ReAct loop behavior is unchanged

- **WHEN** the Planner Layer passes a plan to `ReactAgentLoop.run`
- **THEN** the loop SHALL still execute the existing iteration model, tool registry, blocked-tool rules, observation handling, and cancellation semantics described in `openspec/specs/react-agent-loop/spec.md`
