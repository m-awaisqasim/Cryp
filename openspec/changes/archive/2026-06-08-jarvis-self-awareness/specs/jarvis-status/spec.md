## ADDED Requirements

### Requirement: Status query
The `cryp_status` tool SHALL answer "status" queries by returning Cryp's current state (LISTENING/THINKING/SPEAKING), session uptime, and a human-readable status summary.

#### Scenario: User asks for status
- **WHEN** the user asks "What's your status?" or similar
- **THEN** Cryp calls `cryp_status` with `query="status"`
- **THEN** the tool returns current runtime state, uptime string, and session duration

### Requirement: Version query
The `cryp_status` tool SHALL answer "version" queries by returning the version string, model name, and build date from `core/version.py`.

#### Scenario: User asks for version
- **WHEN** the user asks "What version are you?" or similar
- **THEN** Cryp calls `cryp_status` with `query="version"`
- **THEN** the tool returns the version string and model identifier

### Requirement: Memory stats query
The `cryp_status` tool SHALL answer "memory" queries by returning counts of long-term facts, episodic sessions, and pattern entries.

#### Scenario: User asks about memory
- **WHEN** the user asks "How's your memory?" or "What do you remember?" or similar
- **THEN** Cryp calls `cryp_status` with `query="memory"`
- **THEN** the tool returns counts of stored facts, sessions, and patterns

### Requirement: Activity query
The `cryp_status` tool SHALL answer "activity" queries by returning in-memory metrics for the current session: tools used (with counts), total turns, and agent_task invocations.

#### Scenario: User asks about today's activity
- **WHEN** the user asks "What have you done today?" or "What tools did you use?" or similar
- **THEN** Cryp calls `cryp_status` with `query="activity"`
- **THEN** the tool returns a summary of tool calls, turn count, and task count for the session

### Requirement: System health query
The `cryp_status` tool SHALL answer "system" queries by returning CPU, RAM, and disk usage from the system health daemon or psutil fallback.

#### Scenario: User asks about system resources
- **WHEN** the user asks "How are your system resources?" or "What's the CPU usage?" or similar
- **THEN** Cryp calls `cryp_status` with `query="system"`
- **THEN** the tool returns CPU, RAM, and disk usage metrics

### Requirement: No agent_task delegation
The `cryp_status` tool SHALL NEVER delegate to `agent_task`. All self-awareness queries MUST be answered directly from in-memory metrics, file reads, and process state.

#### Scenario: Self-awareness bypasses agent_task
- **WHEN** Cryp receives a self-awareness query matching the `cryp_status` tool description
- **THEN** Cryp calls `cryp_status` directly instead of `agent_task`
- **THEN** the response is returned without invoking the Planner or ReAct loop

### Requirement: Accurate real-time data
The `cryp_status` tool SHALL return accurate, real-time data. It MUST NOT hallucinate, guess, or fabricate metrics. If data is unavailable (e.g., psutil not installed), the tool SHALL return a clear "unavailable" message without erroring.

#### Scenario: Missing dependency handled gracefully
- **WHEN** `psutil` is not installed and the user asks about system resources
- **THEN** the tool returns "System resource data unavailable" instead of crashing or fabricating data
