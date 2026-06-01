# AI Workflow Rules — MARK-XXXIX

## Approach

Build MARK-XXXIX incrementally using a spec-driven workflow. Context files define what to build, how to build it, and the current state of progress. Always implement against these specs — do not infer or invent behavior from scratch.

The AI agent reads the context files, understands the current state, and produces code that fits the existing architecture. The human reviews, tests, and approves before merging.

## Scoping Rules

- **Work on one feature unit at a time.** A feature unit is a single, end-to-end verifiable capability.
- **Prefer small, verifiable increments over large speculative changes.** If you cannot test it in 5 minutes, the scope is too big.
- **Do not combine unrelated system boundaries in a single implementation step.**

### Feature Unit Examples (Phase 1)

| Unit | Scope | Verifiable In |
|------|-------|---------------|
| FastAPI skeleton | `main.py` + `config.py` + `/health` endpoint | 5 min — curl returns JSON |
| LLM client | `llm.py` service, Groq connection, single prompt | 10 min — API returns text |
| Tool registry | `registry.py` with 3 tools, function calling | 15 min — tool executes via API |
| Memory write | `memory.py` saves fact to SQLite + ChromaDB | 10 min — query returns fact |
| Memory read | `memory.py` retrieves relevant facts for prompt | 10 min — context includes fact |
| Morning brief | Scheduled agent reads tasks, generates brief | 15 min — brief appears at 8 AM |
| Deadline guardian | Task tracking, 24h alert, escalation | 20 min — alert fires before deadline |
| Assignment planner | Break assignment into chunks, schedule | 20 min — chunks appear in task list |
| Voice I/O | Gemini Live audio input/output | 15 min — speech in/out works with transcripts |

## When to Split Work

Split an implementation step if it combines:

- **UI changes and backend changes** — These are separate units. Backend first, UI second.
- **Multiple unrelated API routes** — One route per unit.
- **Behavior not clearly defined in context files** — Go back to the spec, define it, then implement.
- **Database schema changes and business logic changes** — Schema first (migration), logic second.

### Split Example

BAD: "Build the chat system" (includes WebSocket, UI, memory, voice — too big)

GOOD:
1. "Add `/chat` HTTP route with basic response"
2. "Add WebSocket endpoint for streaming"
3. "Add memory injection to chat context"
4. "Add voice input/output to chat"
5. "Build React chat UI component"

## Handling Missing Requirements

- **Do not invent product behavior not defined in the context files.** If the spec does not say it, do not build it.
- **If a requirement is ambiguous, resolve it in the relevant context file before implementing.** Update `project-overview.md` or `architecture.md`, then code.
- **If a requirement is missing, add it as an open question in `progress-tracker.md` before continuing.** Example: "Should deadline alerts include email notifications?" — add to open questions, do not guess.

## Protected Files

Do not modify the following unless explicitly instructed:

- `frontend/src/components/ui/*` — shadcn/ui generated components. Use `npx shadcn add` to add new ones.
- `backend/app/core/config.py` — Only modify env var schema, not loading logic.
- `Context/*.md` — Modify only when the human explicitly updates the spec.
- `.env` and `.env.example` — Never commit real values.

## Keeping Docs in Sync

Update the relevant context file whenever implementation changes:

| Change Type | Update This File |
|-------------|-----------------|
| New feature added | `project-overview.md` (Features section), `progress-tracker.md` |
| Architecture change | `architecture.md`, `progress-tracker.md` |
| New tech added to stack | `architecture.md` (Stack table) |
| New code convention | `code-standards.md` |
| UI change | `ui-context.md`, `progress-tracker.md` |
| Scope change | `project-overview.md` (In/Out of Scope), `progress-tracker.md` |

## Before Moving to the Next Unit

1. The current unit works end to end within its defined scope
2. No invariant defined in `architecture.md` was violated

# AI Workflow Rules — MARK-XXXIX

This project uses a Spec-Driven Development (SDD) workflow: Context/ files are the canonical spec and must be consulted before implementation.

Principles
- Work on a single feature unit at a time (small, verifiable). Break larger efforts into sequential units.
- Keep changes minimal and testable. If it cannot be validated in ~10 minutes, split the unit.
- Backend first, then frontend for features touching both.

Feature-unit examples (Phase 1)
- Gemini Live audio loop — streaming input/output with tool calls.
- Tool registry refactor — move inline router to capability registry (verifiable: same behavior, new registration API).

Splitting rules
- Separate DB migrations from logic changes.
- Split UI and API changes into separate PRs unless tightly coupled and small.

Missing requirements
- If the spec lacks clarity, add an open question in `Context/progress-tracker.md` and stop until clarified.

Protected files
- `Context/*.md` (the spec) — only change when the human approves.
- `frontend/src/components/ui/*` — shadcn-generated components; modify via `npx shadcn add`.

Before marking a unit complete
1. Tests for the unit pass locally.
2. Progress-tracker updated with what changed and verification steps.
3. Human review requested and basic QA done (voice checks for Gemini audio changes).

Human review checklist
- Code follows `Context/code-standards.md`.
- No secrets in code.
- Logging and error handling present.
- `progress-tracker.md` updated.
