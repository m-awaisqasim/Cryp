## Architecture — MARK-XXXIX (current + target)

This document summarizes the practical architecture for evolving MARK-XXXIX into a JARVIS-style assistant while reusing the existing codebase.

Core layers
- **Orchestrator / API**: FastAPI entrypoints and a lightweight orchestrator responsible for session lifecycle, adapter selection, and routing to services.
- **Brain (LLM layer)**: Provider-agnostic adapters (Cloud Copilot / local Gemma) that produce text outputs and structured tool calls. Implement an `llm_adapter` interface.
- **Voice layer**: `voice_adapter` encapsulates STT and TTS providers (Gemini Live audio, Edge TTS, Piper fallback). Voice is a transport, not the brain.
- **Tools layer**: A registry of capability-driven modules (`actions/`) exposed via JSON function schemas. A `tool_registry` maps capabilities to safe executors with permission checks.
- **Memory layer**: Layered memory service: short-term session, user profile, episodic, and semantic (vector store). Retrieval and summarization happen in `memory_service`.

Storage
- **Structured**: SQLite for profiles, tasks, audit logs, and session metadata.
- **Semantic**: ChromaDB (or local FAISS) for embeddings and RAG.
- **Files**: `uploads/` for temporary content; persistent data stored in `data/`.

Service boundaries
- `api/` (FastAPI) owns HTTP and WebSocket transport only.
- `services/` owns business logic: `brain`, `memory`, `voice`, `tools`.
- `adapters/` contains provider-specific code (`copilot_adapter`, `gemma_adapter`, `edge_tts_adapter`, `piper_adapter`).

Key interfaces
- `LLMAdapter` — methods: `complete(prompt, params)`, `stream(prompt, on_token)`, `call_function(schema, args)`.
- `VoiceAdapter` — methods: `synthesize_stream(text)`, `synthesize_file(text, out_path)`, `transcribe_stream(stream)`.
- `ToolExecutor` — model-safe execution wrapper with `simulate()`, `execute()`, `confirm()` hooks.

Invariants
1. All tool calls are explicit, schema-driven, and logged in `audit_log`.
2. Destructive operations require explicit confirmation flows.
3. The orchestrator handles provider failover and adapts timeouts per provider.
4. The voice layer is swappable; the brain must not depend on audio internals.

