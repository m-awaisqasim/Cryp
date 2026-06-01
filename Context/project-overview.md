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
6. MARK-XXXIX responds with Gemini Live audio (with transcript shown in UI)
7. MARK-XXXIX extracts and stores new facts to memory automatically

## Features

### Phase 1 — Brain & Memory (Active)

- **Conversational Brain**: Multi-turn dialogue with context awareness
- **Persistent Memory**: 4-tier memory (working, episodic, semantic, user profile)
- **Memory Extraction**: Auto-extracts facts from conversations and categorizes them
- **Tool Registry**: JSON function calling for web search, browser automation, file reading
- **Voice Interface**: Gemini Live audio input/output with transcripts
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
- Gemini Live for reasoning and audio I/O
- ChromaDB vector store for semantic memory
- SQLite for structured data (user profile, episodic memory, tasks)
- Gemini Live audio input/output
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
- Single-provider Gemini Live audio-to-audio flow.

Primary Goals
- Reliable conversational intelligence with streaming voice I/O and bilingual support (English/Urdu).
- Safe, auditable tool execution for browser automation, file operations, reminders, and limited system control.
- Layered memory: short-term session context, user profile, and searchable long-term memory for RAG.

Core User Flow (target)
1. User input: audio or text
2. Gemini Live receives audio input and streams transcription
3. Gemini Live reasons, calls tools when needed, and returns audio response
4. UI displays live transcripts and stores memory

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
- LLM: Gemini Live only
- Memory: SQLite + ChromaDB (semantic store)
- Voice: Gemini Live audio input/output (no external STT/TTS)
- Tools: existing `actions/` modules become registered capabilities behind a registry

Out of scope for Phase 1
- Multi-tenant deployments, trading/autotrading, heavy GPU infra

Immediate next steps
1. Keep Gemini Live audio-to-audio loop stable and robust.
2. Expand tool registry coverage and improve tool result logging.
3. Add tests for tool execution and memory updates.
