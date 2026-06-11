## Why

Cryp/Cryp currently only remembers flat key-value facts about the user (name, preferences, projects) but has no memory of past conversations. Each session starts fresh — Cryp cannot recall "what we discussed yesterday", continue a multi-day debugging effort, or build on prior context. Adding episodic memory turns Cryp into a continuous companion that remembers conversation history across sessions, not just isolated facts.

## What Changes

- Add a new `episodic` memory layer alongside the existing flat key-value memory in `memory/long_term.json`.
- Persist each session as a dated JSON file under `memory/episodic/YYYY-MM-DD_HHMMSS.json`, containing a summary, key topics, decisions, and timestamps.
- Summarize the ongoing session automatically at session end (and periodically during long sessions) using the Gemini model.
- On startup, load the N most recent episode summaries and inject them into the system prompt via `_build_config()` in `main.py`, so Cryp can answer questions about previous conversations.
- Add a retrieval helper that surfaces relevant past episodes when the user asks about prior chats (e.g., "what did we discuss last week?").
- Extend `memory_manager.py` with episodic helpers (`save_episode`, `load_recent_episodes`, `format_episodes_for_prompt`, `search_episodes`) without breaking the existing `load_memory` / `update_memory` / `format_memory_for_prompt` API.

## Capabilities

### New Capabilities
- `episodic-memory`: Persistent per-session conversation summaries that are written to disk, retrieved at startup, and injected into Cryp's system prompt so it can recall and reason about past conversations across sessions.

### Modified Capabilities
<!-- No existing capability specs are changing requirements. The current flat key-value memory continues to behave exactly as before; episodic memory is purely additive. -->

## Impact

- **Code**:
  - `memory/memory_manager.py` — adds episodic helpers; existing functions untouched.
  - `memory/episodic/` — new directory holding dated session JSON files (gitignored by default).
  - `main.py` — `_build_config()` injects episode summaries into the system prompt; the live session loop calls a new `_finalize_session_episode()` hook on disconnect/shutdown and at periodic intervals.
  - Optional new tool declaration `recall_episodes` so the model can explicitly search past sessions.
- **APIs / dependencies**: No new third-party dependencies. Reuses the existing `google.genai` client for summarization.
- **Data**: New on-disk directory `memory/episodic/`. Existing `memory/long_term.json` schema is unchanged.
- **Performance**: One extra short Gemini call per session-end (and per rollover). Startup adds ~1–3 KB to the system prompt depending on episode count.
- **Privacy**: Conversation summaries are stored locally only; nothing is uploaded beyond what Gemini already receives during normal calls.
