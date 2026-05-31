# AI Agent Entry Point — MARK-XXXIX

> **Read this file first.** It defines the order of operations for every AI agent working on MARK-XXXIX.

## Agent Identity
You are an expert software engineer building **MARK-XXXIX** — a JARVIS-like AI assistant for a BS-Fintech student and aspiring quant trader. You work within a spec-driven development (SDD) workflow where context files are the single source of truth.

## Mandatory Reading Order
Before writing or modifying ANY code, read these files in this exact order:

1. `Context/project-overview.md` — What MARK-XXXIX is, who it's for, goals, features, scope
2. `Context/architecture.md` — System structure, tech stack, boundaries, storage, invariants
3. `Context/ui-context.md` — Visual design system, colors, typography, component rules
4. `Context/code-standards.md` — Implementation conventions, file organization, API rules
5. `Context/ai-workflow-rules.md` — Development workflow, scoping, delivery approach
6. `Context/progress-tracker.md` — Current state, completed work, next tasks, open questions

## After Reading
- Check `progress-tracker.md` for the current goal and next task
- Do NOT implement anything outside the current scope
- Do NOT invent features not defined in `project-overview.md`
- Do NOT use technologies not listed in `architecture.md`
- Do NOT violate invariants defined in `architecture.md`

## Before Submitting Code
- Verify the implementation matches the spec in context files
- Update `progress-tracker.md` with what was completed
- If your change affects architecture or scope, update the relevant context file FIRST

## MARK-XXXIX-Specific Rules
- Always use Pakistan timezone (`Asia/Karachi`) for all datetime operations
- All API keys load from `.env` via Pydantic Settings — never hardcode
- Every tool call must be logged for audit trail
- Student persona is active in Phase 1 — Trader and Quant personas are dormant
- Bilingual support: English and Urdu (including Roman Urdu) — design for this from day one
