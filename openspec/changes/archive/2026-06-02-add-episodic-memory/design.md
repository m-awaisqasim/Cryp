## Context

Cryp/Cryp uses Gemini Live for real-time audio conversations. Today, persistent memory is a single flat JSON file (`memory/long_term.json`) with six categories (identity, preferences, projects, relationships, wishes, notes) managed by `memory/memory_manager.py`. On every connect, `CrypLive._build_config()` in `main.py:603` loads that file, formats it via `format_memory_for_prompt()`, and injects the result into the system instruction.

There is no record of *what was said* in previous sessions — only distilled facts that the model chose to save via the `save_memory` tool. Users who want continuity ("continue where we left off", "what did you suggest yesterday?") get a blank slate every session.

Constraints that shaped this design:
- Must NOT break the existing flat key-value memory (other code paths read `long_term.json` directly).
- Must keep system-prompt growth bounded (current cap is `MEMORY_MAX_CHARS = 2200`; episodes need their own bounded budget).
- The Gemini Live model used (`models/gemini-2.5-flash-native-audio-preview-12-2025`) is audio-first and does not return arbitrary text on demand mid-stream — summarization must use a separate, simple text-generation call via `google.genai`.
- Session boundaries are implicit. `CrypLive.run()` enters a reconnect loop; we need an explicit "session" concept that survives transient reconnects but closes on real shutdown.
- Filesystem must be the source of truth (offline-friendly, easy to inspect, no DB).

## Goals / Non-Goals

**Goals:**
- Persist a structured summary of each user-Cryp session to `memory/episodic/`.
- Make the last N (default 5) episode summaries available to Cryp at session start via the system prompt.
- Provide a retrieval helper so Cryp (or future tools) can pull older episodes by date / keyword.
- Keep the public surface of `memory_manager.py` backward compatible: `load_memory`, `update_memory`, `format_memory_for_prompt`, `remember`, `forget` keep their current signatures and behavior.
- Bound memory growth: per-episode JSON ≤ ~2 KB, recent-episode prompt block ≤ ~1.5 KB.

**Non-Goals:**
- Full conversational replay (we store summaries, not raw transcripts).
- Vector/embedding-based semantic search. Retrieval is date-ordered + simple substring keyword match for now.
- Multi-user isolation. Cryp is a single-user assistant.
- Cloud sync or encryption-at-rest.
- Changing the existing `save_memory` tool's behavior — it still writes flat facts.

## Decisions

### 1. Storage layout: one JSON file per session

Each session writes to `memory/episodic/<YYYY-MM-DD_HHMMSS>.json` with this shape:

```json
{
  "id": "2026-06-01_142355",
  "started_at": "2026-06-01T14:23:55",
  "ended_at":   "2026-06-01T14:58:12",
  "duration_minutes": 34,
  "summary": "User asked Cryp to fix a Python bug in the websocket handler...",
  "topics": ["websocket bug", "python debugging", "deployment"],
  "decisions": ["Use exponential backoff in reconnect loop"],
  "user_turns": 18,
  "assistant_turns": 19,
  "tools_used": ["code_helper", "file_controller"]
}
```

**Alternative considered:** single rolling `episodes.jsonl` file. Rejected because per-file storage makes it trivial to delete/inspect a single session, plays nicely with git, and avoids file-locking concerns when summarization writes overlap with retrieval reads.

### 2. Summarization: secondary text-only Gemini call

When a session ends (or rolls over), we collect the transcript buffer maintained in `_receive_audio()` (already accumulated in `in_buf`/`out_buf` per turn), and send it to a cheap text model (`gemini-2.0-flash`) with a strict JSON-output prompt asking for `{summary, topics, decisions}`. The Live session itself is not used for this — Live is audio-bidirectional and not designed for synchronous structured output.

**Alternative considered:** local heuristic summarization (first/last N turns + keyword extraction). Rejected because the resulting summaries would be too low-quality for Cryp to reason over later. The extra ~1 second of latency at session end is acceptable since it runs in the background after disconnect.

### 3. Transcript capture in-process

`_receive_audio()` already builds `in_buf` / `out_buf` lists per turn and writes them to the UI log. We will add a `self._episode_turns: list[dict]` ring buffer (cap 200 turns) that accumulates `{role, text, ts}` entries each time a turn completes. This avoids re-reading the UI log file and keeps capture independent of UI presence.

### 4. Session lifecycle

A "session" begins on the first successful `client.aio.live.connect(...)` and ends on **explicit shutdown** (`shutdown_cryp` tool, KeyboardInterrupt, or `os._exit`). Transient reconnects (handled by `ReconnectRequested`) do NOT close a session — they belong to the same conversation from the user's POV.

A periodic rollover runs every 30 minutes inside an asyncio task: if `len(self._episode_turns) >= 20`, flush a partial episode and clear the buffer. This protects against losing context on a hard crash and keeps individual episode JSON files small.

On shutdown, `_finalize_session_episode()` is called from `shutdown_cryp` (before `os._exit`) and registered with `atexit` as a safety net.

**Alternative considered:** treat each reconnect as a new episode. Rejected because Live disconnects can happen mid-sentence; that would fragment a single user thought across multiple episode files.

### 5. Prompt injection: append to existing `_build_config()`

In `main.py:603` (`_build_config`), after the existing memory block is built, we append a new "Recent conversations" block produced by `format_episodes_for_prompt(load_recent_episodes(n=5))`. The block is hard-capped at 1500 chars and trimmed oldest-first.

The resulting system prompt order becomes: time context → known facts → recent episodes → core protocol prompt. Each block is clearly delimited so the model treats them as separate contexts.

### 6. Public API of `memory_manager.py` (additive only)

New functions (all live in the same module; no new files):

| Function | Purpose |
| --- | --- |
| `save_episode(episode: dict) -> Path` | Validates shape, writes to `memory/episodic/<id>.json`. |
| `load_recent_episodes(n: int = 5) -> list[dict]` | Returns the `n` newest episodes sorted by `started_at` desc. |
| `search_episodes(query: str, limit: int = 5) -> list[dict]` | Case-insensitive substring match over summary + topics. |
| `format_episodes_for_prompt(episodes: list[dict], max_chars: int = 1500) -> str` | Produces the bullet-list block injected into the system prompt. |
| `summarize_session(turns: list[dict], api_key: str) -> dict` | Calls Gemini text model and returns the structured summary. |

Existing functions remain unchanged. `_empty_memory()` is NOT extended (episodes are stored separately, not inside `long_term.json`).

### 7. Optional `recall_episodes` tool

We add a new tool declaration so the model can explicitly query past sessions when the user asks ("what did we talk about last Tuesday?"):

```python
{
  "name": "recall_episodes",
  "description": "Searches past conversation summaries by keyword or date range. Use when user asks about previous chats.",
  "parameters": {
    "type": "OBJECT",
    "properties": {
      "query": {"type": "STRING", "description": "Keyword to search summaries/topics"},
      "limit": {"type": "INTEGER", "description": "Max episodes to return (default 3)"}
    },
    "required": []
  }
}
```

`_execute_tool` dispatches this to `search_episodes()` and returns formatted results as the function response.

## Risks / Trade-offs

- **Summarization failure / API outage** → Mitigation: wrap `summarize_session()` in try/except; on failure fall back to a deterministic local summary (first user turn + last assistant turn + topic-by-frequency).
- **Disk growth over months** → Mitigation: episodes are tiny (~1–2 KB). At 5 sessions/day × 1.5 KB × 365 = ~2.7 MB/year. Add a `prune_episodes(keep_last=500)` helper called once on startup.
- **Prompt bloat hurting model latency** → Mitigation: hard cap of 1500 chars for the episodes block, default n=5; user can override `EPISODIC_RECENT_COUNT` env var.
- **Stale or wrong summaries leaking into future context** → Mitigation: include `started_at` in each formatted line so the model can weigh recency; user can manually delete bad episodes (they are plain JSON).
- **Race between rollover task and shutdown** → Mitigation: `save_episode` uses the existing module `_lock`; rollover task and shutdown both await the same lock.
- **Transcript capture missing tool-driven output** (e.g., `screen_process` speaks via vision module, not Live stream) → Accepted limitation for v1; tool calls themselves are recorded in `tools_used` so context is not entirely lost.

## Migration Plan

No data migration is needed. On first launch after this change:
1. `memory/episodic/` directory is created lazily.
2. `_build_config()` produces an empty "Recent conversations" block until the first session ends.
3. The existing `long_term.json` is untouched.

Rollback: delete `memory/episodic/`, revert the `memory_manager.py` and `main.py` diff. No schema changes to undo.

## Open Questions

- Should `recall_episodes` be exposed as a tool from day one, or only after we verify summary quality? **Tentative decision:** ship it disabled-by-default behind a `ENABLE_RECALL_TOOL` flag in `main.py` so it can be flipped on without redeploying.
- What is the right rollover interval? 30 minutes is a guess; we may need to tune after observing real session lengths.
