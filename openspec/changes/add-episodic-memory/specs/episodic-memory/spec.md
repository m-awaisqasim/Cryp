## ADDED Requirements

### Requirement: Episode Persistence

The system SHALL persist every Jarvis conversation session as a structured JSON file in `memory/episodic/` so that past conversations can be recalled in future sessions.

Each episode file MUST contain at minimum: a unique `id`, ISO-8601 `started_at` and `ended_at` timestamps, an English-language `summary`, an array of `topics`, and counters for `user_turns` and `assistant_turns`. Episodes MUST be writable from any thread or async task without corruption.

#### Scenario: Session ends and episode is saved
- **WHEN** the user shuts down Jarvis via the `shutdown_jarvis` tool or the process exits cleanly
- **THEN** a file `memory/episodic/<YYYY-MM-DD_HHMMSS>.json` is written containing the session summary, topics, decisions, turn counts, and start/end timestamps

#### Scenario: Periodic rollover during long sessions
- **WHEN** an active session has accumulated 20 or more captured turns and 30 minutes have passed since the last flush
- **THEN** a partial episode is written to disk and the in-memory turn buffer is cleared without disconnecting the live session

#### Scenario: Empty session is not persisted
- **WHEN** a session ends with zero captured user turns
- **THEN** no episode file is written

#### Scenario: Summarization API failure
- **WHEN** the Gemini summarization call raises an exception during finalization
- **THEN** the system writes a fallback episode containing the first user turn, the last assistant turn, and the list of tools used, instead of dropping the episode

### Requirement: Episode Retrieval at Session Start

The system SHALL load the most recent episode summaries on every connection and make them available to the Gemini Live system instruction via `_build_config()` so Jarvis can reference past conversations.

The number of episodes loaded MUST default to 5 and MUST be overridable via the `EPISODIC_RECENT_COUNT` environment variable. The formatted episode block MUST be hard-capped at 1500 characters; if exceeded, oldest entries MUST be dropped first.

#### Scenario: Recent episodes are injected into system prompt
- **WHEN** Jarvis connects to Gemini Live and `_build_config()` runs
- **THEN** the system instruction contains a "Recent conversations" section listing the 5 newest episode summaries with their dates

#### Scenario: No prior episodes exist
- **WHEN** `memory/episodic/` is empty or missing on connection
- **THEN** `_build_config()` succeeds and the system instruction omits the episodes section entirely (no header, no placeholder)

#### Scenario: Episodes block exceeds character budget
- **WHEN** the formatted episode block would exceed 1500 characters
- **THEN** the oldest episodes are dropped one at a time until the block fits, and the remaining block is included verbatim

#### Scenario: Override via environment variable
- **WHEN** `EPISODIC_RECENT_COUNT=10` is set in the environment
- **THEN** up to 10 most recent episodes are loaded instead of the default 5

### Requirement: Episode Search

The system SHALL provide a `search_episodes(query, limit)` helper that performs case-insensitive substring matching across each episode's `summary` and `topics` fields and returns matching episodes ordered by recency (newest first).

#### Scenario: Keyword match across multiple episodes
- **WHEN** the user asks "what did we discuss about websockets?" and `search_episodes("websocket", limit=3)` is called
- **THEN** up to 3 episodes whose `summary` or `topics` contain "websocket" (case-insensitive) are returned, newest first

#### Scenario: No matching episodes
- **WHEN** the search query does not match any stored episode
- **THEN** an empty list is returned (no error raised)

#### Scenario: Limit is respected
- **WHEN** `search_episodes("python", limit=2)` matches 10 episodes
- **THEN** only the 2 newest matching episodes are returned

### Requirement: Backward Compatibility With Flat Key-Value Memory

The existing flat key-value memory API in `memory/memory_manager.py` SHALL continue to function unchanged. Specifically, `load_memory()`, `update_memory()`, `save_memory()`, `format_memory_for_prompt()`, `remember()`, and `forget()` MUST retain their current signatures, behavior, and the on-disk format of `memory/long_term.json`.

The episodic memory feature MUST be implemented additively — no existing function may be renamed, removed, or have its return type changed.

#### Scenario: Existing save_memory tool still writes flat facts
- **WHEN** the Gemini model invokes the `save_memory` tool with `category="identity"`, `key="city"`, `value="Lahore"`
- **THEN** `memory/long_term.json` is updated exactly as before, and no episode file is created or modified as a side effect

#### Scenario: long_term.json schema is preserved
- **WHEN** the episodic memory feature is enabled and a session ends
- **THEN** `memory/long_term.json` retains its existing six categories (`identity`, `preferences`, `projects`, `relationships`, `wishes`, `notes`) with no new top-level keys added

#### Scenario: load_memory return shape unchanged
- **WHEN** `load_memory()` is called after the feature is deployed
- **THEN** the return value is a dict with the same six category keys and entry format (`{value, updated}`) used before the change

### Requirement: Configurable Recall Tool

The system SHALL expose an optional `recall_episodes` tool declaration to the Gemini Live model, gated by a configuration flag. When enabled, the model can explicitly query past sessions during a conversation.

The tool MUST accept a `query` string and an optional `limit` integer, MUST delegate to `search_episodes()`, and MUST return formatted episode summaries in the function response. When the flag is disabled, the tool MUST NOT appear in `TOOL_DECLARATIONS`.

#### Scenario: Tool is registered when flag is enabled
- **WHEN** `ENABLE_RECALL_TOOL` is set to a truthy value in the configuration or environment
- **THEN** `recall_episodes` appears in `TOOL_DECLARATIONS` passed to `client.aio.live.connect`

#### Scenario: Model invokes recall_episodes
- **WHEN** the user asks "what did we talk about last week?" and the model calls `recall_episodes(query="last week", limit=3)`
- **THEN** the executor returns a string containing up to 3 matching episode summaries with their dates

#### Scenario: Tool is hidden when flag is disabled
- **WHEN** `ENABLE_RECALL_TOOL` is unset or falsy
- **THEN** `recall_episodes` is absent from `TOOL_DECLARATIONS` and the model cannot invoke it

### Requirement: Disk Footprint Bounded

The system SHALL keep episodic storage bounded by pruning old episode files on startup so that long-term disk usage does not grow without limit.

A `prune_episodes(keep_last=500)` helper MUST run once during application startup. When the number of files in `memory/episodic/` exceeds the limit, the oldest files (by `started_at` timestamp) MUST be deleted until the count is at or below the limit.

#### Scenario: Pruning under limit is a no-op
- **WHEN** `memory/episodic/` contains 100 files and `prune_episodes(keep_last=500)` runs
- **THEN** no files are deleted

#### Scenario: Pruning enforces the cap
- **WHEN** `memory/episodic/` contains 600 files and `prune_episodes(keep_last=500)` runs
- **THEN** the 100 oldest files (by `started_at`) are deleted and 500 newest files remain
