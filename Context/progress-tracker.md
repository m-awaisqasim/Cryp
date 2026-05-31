# Progress Tracker — MARK-XXXIX

Update this file after every meaningful implementation change.

## Progress Tracker — MARK-XXXIX

Purpose: track work items, blockers, and short-term plans.

Completed
- Updated `Context/project-overview.md`, `Context/architecture.md`, `Context/ai-workflow-rules.md`, `Context/code-standards.md` to JARVIS spec.
- Patched `requirements.txt` and `setup.py` for cross-platform installs.
- Added lazy imports to GUI-related `actions/` to avoid headless crashes.
- Improved reconnect/backoff behavior in `main.py`.

In progress
- `adapters/llm_adapter.py` scaffold and `adapters/copilot_adapter.py` stub
- `voice_adapter.py` scaffold (Gemini Live + Edge/Piper fallback)
- Tool registry refactor in `agent/executor.py`
- Memory layering and retrieval tuning in `memory/memory_manager.py`

Open questions
- Should Phase 1 include email notifications for deadline alerts?
- Chroma vs FAISS for production semantic store?
- Role of Gemma4:e2b: local reasoning only or also transcription?

Immediate next actions
1. Create `adapters/llm_adapter.py` and `adapters/copilot_adapter.py` stubs and unit tests for the adapter contract.
2. Implement `voice_adapter.py` with streaming synth and fallback.
3. Wire `main.py` to call `voice_adapter.synthesize_stream` from `speak()`.
4. Replace inline tool routing with `tools/registry.py` and adapt `agent/executor.py`.

Changelog
- 2026-05-17: Spec files updated; cross-platform install fixes; reconnect/backoff added to main loop.


## Open Questions

- [ ] What is the exact user profile schema? (name, courses, preferences, etc.)
- [ ] Should morning brief trigger at fixed time (8 AM) or user-defined wake time?
- [ ] How does Deadline Guardian ingest deadlines? (manual input, email parsing, LMS scraping?)
- [ ] Should assignment chunks be stored as sub-tasks or just generated on demand?
- [ ] What is the voice wake phrase? ("Hey MARK-XXXIX", "MARK-XXXIX", custom?)
- [ ] Should Roman Urdu be handled as a separate language mode or mixed within English?
- [ ] What is the maximum context window before compression/summarization kicks in?

## Architecture Decisions

- **One brain, scoped personas** — Single reasoning core with Student/Trader/Quant modes. Student active now, others dormant. (Decision date: 2026-05-16)
- **Local development first** — Deploy to cloud only after Phase 1 works locally. (Decision date: 2026-05-16)
- **ChromaDB over FAISS** — Persistent vector store that updates at runtime, unlike old JARVIS stale FAISS index. (Decision date: 2026-05-16)
- **Function calling over regex** — LLM-native tool registry replaces regex routing from old JARVIS. (Decision date: 2026-05-16)
- **Edge-TTS over Piper** — Better Urdu voice quality, acceptable tradeoff of requiring internet. (Decision date: 2026-05-16)
- **Web Speech API over Whisper** — Zero setup, instant Urdu support, no Python audio dependencies. (Decision date: 2026-05-16)

## Session Notes

- **2026-05-16**: Project conception, Phase 1 scope defined, tech stack selected, SDD methodology adopted from JSMastery video
- **2026-05-17**: SDD context files created. Ready to begin implementation. First unit: FastAPI skeleton.
- **2026-05-17**: FastAPI skeleton implemented, health endpoint verified
- **2026-05-17**: Sentry captured Asia/Karachi tzdata error; tzdata added to requirements for Windows timezone support
- **2026-05-17**: Sentry verification completed after tzdata install
- **2026-05-17**: FastAPI skeleton done. Sentry verified. tzdata installed for Windows.
- **2026-05-17**: LLM client implemented with Groq primary + OpenRouter failover
- **2026-05-17**: Tool registry implemented with 3 Phase 1 tool schemas (web_search, browser, file_read)
- **2026-05-17**: Integration test between LLM client and tool registry added. Registry singleton removed in favor of factory pattern.
- **2026-05-17**: Memory service implemented with 4-tier architecture: working (LLM context), episodic (SQLite), semantic (ChromaDB + SQLite), procedural (user profile + habits)
- **2026-05-17**: Chat API route implemented with BrainService orchestration, memory injection, tool calling, session persistence, and context compression at 20-turn limit

- **2026-05-17**: React frontend skeleton built — dark theme, chat interface, sidebar, Zustand stores, Axios API client wired to backend
- **2026-05-20**: Fixed 3 P0 bugs — memory_extracted now returns true, session_id added to ChatResponseData, session persistence verified with lucky number test, timing instrumentation added to BrainService, latency reduced to under 2162ms
- **2026-05-20**: Fixed async ChromaDB call in health.py (BUG-1)
- **2026-05-20**: Fixed async ChromaDB call in health.py (BUG-1). Confirmed memory extraction storing facts with DEDUP_DISTANCE_THRESHOLD=0.0
- **2026-05-20**: Refreshed frontend chat UI styling (sidebar, header, chat bubbles, input, background)
- **2026-05-21**: Wire frontend to backend — connect chat input to POST /api/v1/chat
- **2026-05-21**: Added `/api/v1/memory/recent` endpoint to fetch recent semantic facts for sidebar preview
- **2026-05-21**: Implemented Phase 1 voice integration: backend language auto-detection + Edge-TTS streaming route, markdown stripping utility, voice tests passing (12/12), frontend STT hook (Chrome/Edge), streaming TTS hook with per-chunk decode resilience, mic input integration, and top-bar speaker toggle with non-blocking text-only fallback.
- **2026-05-21**: Stabilized voice UX: TTS fetch now targets backend base URL in dev, assistant message dedupe prevents repeated speak() calls, STT got EN/UR toggle and more robust speech recognition lifecycle/error handling.
- **2026-05-21**: Added user-switchable response tone preference (`Friendly`, `JARVIS`, `Direct`) with backend persistence, prompt-level style control for chat and websocket responses, top-bar selector UI, frontend build passing, and backend test suite passing (`58 passed`).
- **2026-05-21**: Completed Module 1 — Deadline Guardian: tasks schema + migration path (legacy `deadline/priority` to `due_datetime`), `TaskManager` CRUD/upcoming APIs, `tasks(due_datetime,status)` index, scheduler with 24h/4h checks, DB-backed `alert_log` dedupe, and WebSocket `alert` push support.
- **2026-05-21**: Completed Module 2 — Morning Brief: `/api/v1/brief/morning` endpoint, `BrainService.generate_morning_brief()` summary generation, optional scheduled brief flag (`enable_scheduled_brief`, default false), and WebSocket `morning_brief` message handling.
- **2026-05-21**: Completed Module 3 — Assignment Planner: `POST /api/v1/tasks/plan`, LLM-driven subtask breakdown with validation loop + malformed JSON fallback path, and parent/child task persistence via `parent_task_id`.
- **2026-05-21**: Frontend integration added: new `taskStore`, sidebar Upcoming Deadlines panel (collapsible, expanded by default, max 5 with scroll), task action controls (complete/edit/delete), and `Add Deadline` / `Plan Assignment` / `Morning Brief` actions that feed assistant chat updates.
- **2026-05-21**: Added backend test coverage for tasks/brief/planner/scheduler modules. Full `pytest -q` output is currently blocked in sandbox session output; Python module compile checks passed for all changed backend files.
