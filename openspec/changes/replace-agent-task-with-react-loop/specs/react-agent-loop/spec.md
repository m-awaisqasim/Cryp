## ADDED Requirements

### Requirement: ReAct loop executes complex goals iteratively

The system SHALL execute high-level `agent_task` goals through an iterative ReAct loop that reasons over the goal, selects one concrete tool, observes the result, and repeats until the goal is complete or a bounded stop condition is reached.

#### Scenario: Multi-step goal adapts after observation

- **WHEN** the user submits an `agent_task` goal that requires multiple steps
- **THEN** the system SHALL select a concrete tool for the first step, record the observation, and use that observation when deciding the next step

#### Scenario: Goal completes with final answer

- **WHEN** the ReAct loop determines that the user goal is complete
- **THEN** the system SHALL return a final user-facing answer through the normal `agent_task` function response

### Requirement: ReAct loop uses existing tool declarations

The system SHALL derive the ReAct tool registry from existing `TOOL_DECLARATIONS` so tool names, descriptions, and parameter schemas remain centralized.

#### Scenario: Existing tool is available to ReAct

- **WHEN** a tool is declared in `TOOL_DECLARATIONS` and is safe for ReAct use
- **THEN** the ReAct loop SHALL include that tool in the available action list with its declared parameter schema

#### Scenario: Direct tool behavior is preserved

- **WHEN** Gemini calls a direct tool such as `browser_control`, `file_processor`, or `computer_control`
- **THEN** the system SHALL execute the tool through the existing direct path without requiring the ReAct loop

### Requirement: ReAct loop executes tools through existing executor behavior

The system SHALL execute ReAct-selected tools through the existing `_execute_tool` behavior or an equivalent adapter that preserves current tool side effects, UI logging, error handling, and result formatting.

#### Scenario: ReAct selects a normal tool

- **WHEN** the ReAct loop selects a tool with valid parameters
- **THEN** the system SHALL invoke the same implementation path used by direct tool calls and store the returned result as an observation

#### Scenario: Tool execution fails

- **WHEN** a ReAct-selected tool raises an error or returns a failure result
- **THEN** the system SHALL record the failure as an observation and allow the loop to choose a recovery action unless a stop condition is reached

### Requirement: ReAct loop prevents recursive agent tasks

The system SHALL prevent the ReAct loop from selecting `agent_task` as an action.

#### Scenario: Tool registry is built

- **WHEN** the ReAct loop builds its available tool list
- **THEN** the system SHALL exclude `agent_task` from the selectable tools

#### Scenario: Model requests recursive agent task

- **WHEN** the model output requests `agent_task` during a ReAct iteration
- **THEN** the system SHALL reject that action, record an observation explaining that recursive agent tasks are not allowed, and continue or fail safely

### Requirement: ReAct loop is bounded and cancellable

The system SHALL enforce a maximum iteration count and honor cancellation requests so ReAct execution cannot run indefinitely.

#### Scenario: Maximum iterations reached

- **WHEN** the ReAct loop reaches its configured maximum iteration count before completion
- **THEN** the system SHALL stop and return a clear message describing that the task did not complete within the allowed steps

#### Scenario: Task is cancelled

- **WHEN** a cancellation flag is set while the ReAct loop is running
- **THEN** the system SHALL stop before the next model or tool action and return a cancellation message

### Requirement: ReAct loop uses structured model actions

The system SHALL request and parse structured model actions for each ReAct iteration, distinguishing between tool actions and finish actions.

#### Scenario: Model chooses a tool

- **WHEN** the model returns a valid tool action with a tool name and parameters
- **THEN** the system SHALL execute that tool and append its result to the observation history

#### Scenario: Model finishes the task

- **WHEN** the model returns a valid finish action with an answer
- **THEN** the system SHALL stop the loop and return that answer

#### Scenario: Model returns malformed output

- **WHEN** the model returns malformed or unparseable action output
- **THEN** the system SHALL retry or convert the parsing failure into an observation without crashing the application

### Requirement: ReAct observations are concise

The system SHALL keep ReAct observation history concise by summarizing or truncating long tool outputs before feeding them into later model iterations.

#### Scenario: Tool returns long output

- **WHEN** a selected tool returns output longer than the configured observation limit
- **THEN** the system SHALL store a bounded observation that preserves the important result summary without exceeding the limit

### Requirement: ReAct loop handles parameter schema violations

The system SHALL validate tool parameters before execution and handle
schema mismatches gracefully.

#### Scenario: Model provides wrong parameter types

- **WHEN** the model returns a valid tool name but parameters that do
  not match the declared schema in `TOOL_DECLARATIONS`
- **THEN** the system SHALL record a descriptive observation explaining
  the mismatch and allow the loop to retry with corrected parameters

#### Scenario: API key is read correctly

- **WHEN** the ReAct runner initializes
- **THEN** it SHALL read `gemini_api_key` from `config/api_keys.json`
  and configure `google.generativeai` before making any model call