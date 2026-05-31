# Progress Tracker — MARK-XXXIX

Update this file after every meaningful implementation change.

## Progress Tracker — MARK-XXXIX

Purpose: track work items, blockers, and short-term plans.

Completed
- Updated `Context/project-overview.md`, `Context/architecture.md`, `Context/ai-workflow-rules.md`, `Context/code-standards.md` to JARVIS spec.
- Patched `requirements.txt` and `setup.py` for cross-platform installs.
- Added lazy imports to GUI-related `actions/` to avoid headless crashes.
- Improved reconnect/backoff behavior in `main.py`.
- Separated voice relay from the main loop: `adapters/voice_adapter.py` now attempts the Gemini/live send path first and falls back to local system TTS or text-only mode when Gemini is unavailable or rate-limited.
- `main.py` now propagates voice-send failures into the adapter instead of swallowing them, so fallback behavior can actually trigger.
- Implemented a Copilot (GPT-5 mini) adapter using an OpenAI-compatible endpoint with env-configured base URL and token.
- Replaced the Gemini Live brain loop with a text-based Copilot orchestration loop and retained audio playback for TTS.
- Added a local Web Speech API page and websocket receiver for STT (optional, auto-start via `ENABLE_WEB_STT=1`).
- Added Edge TTS dependency for online fallback.

In progress
- `adapters/llm_adapter.py` scaffold (still only a protocol interface)
- Voice adapter uses Gemini native audio with Edge TTS + system TTS fallback; verify audio playback formats and tune voices.
- Tool registry refactor in `agent/executor.py`
- Memory layering and retrieval tuning in `memory/memory_manager.py`

Open questions
- Should Phase 1 include email notifications for deadline alerts?
- Chroma vs FAISS for production semantic store?
- Role of Gemma4:e2b: local reasoning only or also transcription?

Immediate next actions
1. Replace the Gemini-live brain with a real Copilot/GPT-5 mini adapter behind `LLMAdapter`.
2. Add an explicit audio playback backend for Edge TTS if you want that as the primary non-Gemini fallback.
3. Replace inline tool routing with `tools/registry.py` and adapt `agent/executor.py`.

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

