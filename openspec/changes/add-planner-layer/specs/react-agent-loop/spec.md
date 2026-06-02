## ADDED Requirements

### Requirement: ReAct loop accepts optional planner context

The system SHALL allow `ReactAgentLoop.run` to accept an optional `plan_context: str | None` argument. When provided, the loop SHALL prepend the plan as a `PLANNED APPROACH` block to the first user message passed to the model. The loop SHALL NOT change its iteration model, tool registry, blocked-tool rules, observation handling, or cancellation semantics when `plan_context` is supplied.

#### Scenario: Plan is included in the first user message

- **WHEN** `ReactAgentLoop.run` is called with a non-empty `plan_context`
- **THEN** the first user message passed to the model SHALL contain the plan content under a `PLANNED APPROACH` heading before the goal

#### Scenario: Plan is omitted when not provided

- **WHEN** `ReactAgentLoop.run` is called without a `plan_context` (or with `None`)
- **THEN** the first user message SHALL be identical to the pre-existing format and SHALL NOT include a `PLANNED APPROACH` block

#### Scenario: Plan is a non-binding hint

- **WHEN** the planner-supplied plan mentions a tool that is not in the tool registry
- **THEN** the ReAct loop SHALL still reject that tool with an "is not available" observation and SHALL continue iterating exactly as it does today
