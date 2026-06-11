## Why

Cryp currently answers questions about the user and the outside world, but cannot answer questions about itself — its own status, version, uptime, memory usage, or what it has done today. Users naturally ask "What's your status?", "How long have you been running?", "What did I ask you today?" — and Cryp currently has no way to answer without calling the heavy `agent_task` tool. A lightweight, dedicated self-awareness tool gives Cryp real-time introspection without unnecessary overhead.

## What Changes

- Add a **`cryp_status`** tool that handles all self-awareness queries: status, version, memory stats, today's activity, tool usage counts, and uptime
- The tool responds with accurate real-time information sourced from process state, memory files, and in-memory counters — never from hallucinated or guessed data
- All self-awareness queries are handled **without calling `agent_task`** (the Planner + ReAct loop) — they go through a direct, synchronous path
- Track per-session metrics in `CrypLive`: start time, tool call counts, total turns, uptime counter
- Expose version string from a single source of truth (`__version__` in `core/version.py` or similar)

## Capabilities

### New Capabilities
- `cryp-status`: Real-time self-awareness tool that answers queries about Cryp's own state — status (listening/thinking/speaking), version, uptime, memory stats (long-term + episodic counts), today's activity (tools used, turns taken, tasks completed), and system health snapshot

### Modified Capabilities
<!-- No existing capability specs have requirement changes — this is a new tool, not a modification to existing spec-level behavior -->

## Impact

- **Code**: New `actions/cryp_status.py` tool file. Additions to `main.py`: import, TOOL_DECLARATIONS entry, dispatch branch in `_execute_tool()`, and in-memory metrics tracking (start_time, call_counters, turn_count)
- **Dependencies**: No new external dependencies — all data sources are stdlib (datetime, os, psutil already present or optional) or existing files (memory JSON, session files)
- **Configuration**: `core/prompt.txt` should mention the new `cryp_status` capability so Cryp knows it can answer self-awareness questions directly
- **Existing spec modifications**: None
