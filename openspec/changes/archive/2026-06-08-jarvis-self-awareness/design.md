## Context

Cryp has 21 tools for interacting with the outside world but no way to introspect itself. When asked "What's your status?", "How long have you been running?", or "What version are you?", Cryp must either guess, call the heavy `agent_task` tool (Planner + ReAct loop) with `web_search`, or avoid answering. This is a poor user experience for an AI assistant modeled after CRYP — which should have effortless self-knowledge.

The solution is a lightweight, dedicated `cryp_status` tool that reads from in-memory counters and process state. It is a synchronous function (no async needed) that runs in the existing thread pool executor alongside every other tool. It must never block, never call external APIs, and never delegate to `agent_task`.

## Goals / Non-Goals

**Goals:**
- Answer "What's your status?" — current state (LISTENING/THINKING/SPEAKING), uptime, active session duration
- Answer "What version are you?" — version string, build date, model name
- Answer "How's your memory?" — count of long-term facts, episodic sessions, pattern entries
- Answer "What have you done today?" — tools used (with counts), total turns, tasks completed via agent_task
- Answer "How are your system resources?" — CPU, RAM, disk usage summary (delegate to system health daemon if available)
- All answers are accurate real-time data, never hallucinated or guessed
- Self-awareness queries are handled WITHOUT calling `agent_task`

**Non-Goals:**
- No persistent metrics database — metrics are ephemeral per-session (reset on restart)
- No historical cross-session analytics — only current session + last N days from episodic memory
- No mood, emotion, or subjective state reporting
- No UI changes — all output is spoken and logged through existing pipeline
- No configuration file changes — the tool is self-contained

## Decisions

1. **Single tool with parameter modes, not many tools**. A single `cryp_status` tool accepts a `query` string parameter ("status", "version", "memory", "activity", "system"). This keeps TOOL_DECLARATIONS clean and gives Cryp flexibility to ask any self-awareness question. The tool function dispatches to internal handlers based on the query parameter.

2. **In-memory metrics tracked in CrypLive**. `CrypLive` gains an `_metrics` dict (`SimpleNamespace` or `dataclass`) with: `start_time`, `tool_call_counts: dict[str, int]`, `turn_count`, `agent_task_count`. These are updated in `_execute_tool()` after each tool call and in `_receive_audio()` on each turn. This is the single source of truth for activity queries.

3. **Version from `core/version.py`**. A new `core/version.py` file holds `__version__ = "2.0.0"` as the single source of truth. Both `cryp_status` and the dashboard server read from this file. No more hardcoded version strings in prompts or UI.

4. **Memory stats from existing memory system**. The tool reads `memory/long_term.json` (fact count), `memory/episodic/` (session files count via os.listdir), and `memory_manager`'s `query_patterns()` (pattern count). No new storage or indices needed.

5. **System health from existing daemon**. If `system_health_daemon` is running and exposes `get_health_snapshot()`, the tool delegates to it for CPU/RAM/disk. If unavailable, it falls back to `psutil` directly (or returns "unavailable"). No new monitoring infrastructure.

6. **Sync function in thread pool, not async**. The tool follows the existing pattern: synchronous function called via `loop.run_in_executor()`. All data sources are file reads or in-memory dict lookups — no blocking I/O that would warrant async.

## Risks / Trade-offs

- **[Risk] In-memory metrics are lost on crash/restart** → Acceptable. This is a per-session feature. For cross-session awareness, the user can query episodic memory via `recall_episodes`. No persistence overhead.
- **[Risk] `psutil` may not be installed** → Make `psutil` an optional import with graceful fallback. The tool returns "System resource data unavailable" if psutil is missing, without erroring.
- **[Risk] Large episodic memory directory slows file count** → Cache the episodic file count with a 30-second TTL. The count is an approximation anyway — it doesn't need to be exact on every call.
- **[Risk] Tool description encourages overuse** → Keep the description precise: "Answers questions about Cryp's own status, version, memory stats, today's activity, and system resources." This limits Gemini's tendency to call it for unrelated queries.
