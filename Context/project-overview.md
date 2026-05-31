# Project Overview — MARK-XXXIX

## Overview

MARK-XXXIX is a personal AI assistant inspired by JARVIS from Iron Man, customized for a BS-Fintech student and active crypto trader. It combines persistent long-term memory, proactive intelligence, and multimodal interaction (text + voice) to serve as a thinking partner, academic assistant, and future quant research companion. MARK-XXXIX remembers who you are, what you are working on, and anticipates your needs — not just responds to commands.

The assistant operates in scoped personas (Student, Trader, Quant) with a shared memory layer. Phase 1 activates the Student persona only, building the brain and memory foundation that later phases will extend.

## Goals

1. **Persistent Memory**: MARK-XXXIX remembers facts, preferences, conversations, and context across sessions — no amnesia on refresh or restart
2. **Proactive Intelligence**: Delivers morning briefings, deadline alerts, and suggestions before being asked
3. **Multimodal Interaction**: Seamless text and voice input/output with bilingual English/Urdu support
4. **Tool-Augmented Reasoning**: Uses function calling (not regex) to invoke tools — web search, browser automation, file reading, calendar access
5. **Safety First**: Every action is logged, destructive operations require confirmation, financial tools are gated

## Core User Flow

1. User opens MARK-XXXIX in browser (or speaks "Hey MARK-XXXIX" in voice mode)
2. MARK-XXXIX loads user profile and recent memory context silently
3. User speaks or types a request
4. MARK-XXXIX classifies intent, retrieves relevant memory, plans response
5. MARK-XXXIX executes tool calls if needed (search, read file, check calendar)
6. MARK-XXXIX generates response — text displayed in UI, voice spoken via TTS
7. MARK-XXXIX extracts and stores new facts to memory automatically

## Features

### Phase 1 — Brain & Memory (Active)

- **Conversational Brain**: Multi-turn dialogue with context awareness
- **Persistent Memory**: 4-tier memory (working, episodic, semantic, user profile)
- **Memory Extraction**: Auto-extracts facts from conversations and categorizes them
- **Tool Registry**: JSON function calling for web search, browser automation, file reading
- **Voice Interface**: Web Speech API (STT) + Edge-TTS (TTS) with Urdu/English
- **Safety Layer**: Critic guard, confirmation gates, audit logging
- **Morning Brief**: Proactive daily summary (schedule, deadlines, priorities)
- **Deadline Guardian**: Tracks assignments, quizzes, projects; alerts before due dates
- **Assignment Planner**: Breaks large assignments into daily chunks and schedules them

### Phase 2 — Student Intelligence (Planned)

- **Lecture Companion**: Ingests slides/PDFs, answers questions, links concepts
- **Research Digest**: Summarizes papers, flags relevance, suggests follow-ups
- **Weakness Tracker**: Identifies struggling topics, generates practice questions
- **Communication Assistant**: Drafts emails, summarizes group chats, presentation prep

### Phase 3+ — Trading & Quant (Future)

- Market data ingestion, backtesting engine, signal pipeline, paper trading
- (Explicitly out of scope for Phase 1 — see below)

## Scope

### In Scope (Phase 1)

- FastAPI backend with service-oriented architecture
- React + Vite frontend with dark JARVIS-inspired UI
- Groq LLM primary (Llama 3.3 70B) + OpenRouter fallback
- ChromaDB vector store for semantic memory
- SQLite for structured data (user profile, episodic memory, tasks)
- Web Speech API for STT, Edge-TTS for TTS
- Tavily web search + Jina AI Reader
- Playwright browser automation
- Sentry error tracking
- Local development (deploy later)

### Out of Scope (Phase 1)

- Trading, market data, backtesting, live execution
- Multi-user authentication
- Cloud deployment
## Project Overview — MARK-XXXIX (JARVIS Assistant Roadmap)

MARK-XXXIX is a working multimodal assistant foundation. The goal is to evolve it into a robust JARVIS-like assistant that is stateful, safe, and proactive. The files in `Context/` are the single source of truth for planning, implementation, and handoffs.

Vision
- A personal assistant that listens, reasons, acts safely on the user's behalf, and remembers across sessions.
- Hybrid architecture: cloud reasoning (Copilot/GPT-5 mini) with local/offline fallback models (Gemma4:e2b) and swappable TTS.

Primary Goals
- Reliable conversational intelligence with streaming voice I/O and bilingual support (English/Urdu).
- Safe, auditable tool execution for browser automation, file operations, reminders, and limited system control.
- Layered memory: short-term session context, user profile, and searchable long-term memory for RAG.

Core User Flow (target)
1. User input: audio or text
2. Edge STT (or browser STT) → transcript
3. Copilot (GPT-5 mini) for reasoning and planning → text response
4. Voice output: Gemini Live audio if available and under quota
5. Fallback voice: Edge TTS or Piper (offline)
6. If voice unavailable, show text-only response
7. Extract facts and update layered memory

Phases
- Phase 1 (MVP, 2–6 weeks): Stabilize core loop, implement `llm_adapter` scaffold, add tool registry, and make voice output provider-agnostic. Add basic layered memory (session + profile + episodic).
- Phase 2 (1–3 months): Full RAG with Chroma, safety policy engine, tool permissioning, proactive automation (task queue follow-ups, morning briefs).
- Phase 3 (production): Optional self-hosted inference, quantized models, autoscaling deployment, advanced multimodal agents.

Success Criteria
- Maintain context across a 20-turn conversation with relevant memory recall.
- Tool calls execute with appropriate confirmations and are auditable via `audit_log`.
- Voice output is natural using Gemini where possible; fallback keeps assistant usable.

Scope — Phase 1
- Backend: Python FastAPI orchestration (existing `main.py`) and services expansion
- LLM: Copilot primary + Gemma4:e2b local fallback adapter
- Memory: SQLite + ChromaDB (semantic store)
- Voice: STT via browser or local STT; TTS via Gemini Live, Edge TTS, Piper fallback
- Tools: existing `actions/` modules become registered capabilities behind a registry

Out of scope for Phase 1
- Multi-tenant deployments, trading/autotrading, heavy GPU infra

Immediate next steps
1. Replace Context templates with this JARVIS spec set.
2. Implement `adapters/llm_adapter.py` scaffold and provider adapters.
3. Add `voice_adapter.py` to encapsulate Gemini audio + fallback TTS.
4. Refactor `main.py` to use adapter interfaces and an orchestrator.
5. Add tests and metrics for fallback behavior and tool success.
