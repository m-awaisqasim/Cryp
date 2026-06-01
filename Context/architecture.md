## Architecture — MARK-XXXIX (current + target)

This document summarizes the practical architecture for evolving MARK-XXXIX into a JARVIS-style assistant while reusing the existing codebase.

Core layers
- **Orchestrator / API**: FastAPI entrypoints and a lightweight orchestrator responsible for session lifecycle, adapter selection, and routing to services.
- **Brain (LLM layer)**: Gemini Live (audio-to-audio) for reasoning, tool calls, and responses.
- **Voice layer**: Gemini Live audio input/output with transcript streams.
- **Tools layer**: A registry of capability-driven modules (`actions/`) exposed via JSON function schemas. A `tool_registry` maps capabilities to safe executors with permission checks.
- **Memory layer**: Layered memory service: short-term session, user profile, episodic, and semantic (vector store). Retrieval and summarization happen in `memory_service`.

Storage
- **Structured**: SQLite for profiles, tasks, audit logs, and session metadata.
- **Semantic**: ChromaDB (or local FAISS) for embeddings and RAG.
- **Files**: `uploads/` for temporary content; persistent data stored in `data/`.

Service boundaries
- `api/` (FastAPI) owns HTTP and WebSocket transport only.
- `services/` owns business logic: `brain`, `memory`, `voice`, `tools`.
- Provider integrations are centralized in the Gemini Live client.

Key interfaces
- Gemini Live handles LLM + voice in a single session.
- `ToolExecutor` — model-safe execution wrapper with `simulate()`, `execute()`, `confirm()` hooks.

Invariants
1. All tool calls are explicit, schema-driven, and logged in `audit_log`.
2. Destructive operations require explicit confirmation flows.
3. The orchestrator handles provider failover and adapts timeouts per provider.
4. The voice layer is swappable; the brain must not depend on audio internals.

