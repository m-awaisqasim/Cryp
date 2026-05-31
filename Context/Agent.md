## Agent Entry and Handoff — MARK-XXXIX (JARVIS roadmap)

This file defines how AI agents (human or automated) should approach the repository and its spec files. The `Context/` folder is the source of truth. Read its files in order before making changes.

Required reading order (first to last):
1. `Context/project-overview.md` — project vision, scope, and phases
2. `Context/architecture.md` — system boundaries, storage, and invariants
3. `Context/code-standards.md` — implementation conventions
4. `Context/ai-workflow-rules.md` — development workflow and delivery rules
5. `Context/progress-tracker.md` — current sprint/goal and next tasks
6. `Context/ui-context.md` — UI tokens and component guidance (frontend only)

Agent rules
- Always implement one feature unit at a time (see `ai-workflow-rules.md`).
- Do not add features outside the current phase documented in `progress-tracker.md`.
- Update `progress-tracker.md` after completing any unit (include commit link).
- Commit small, testable changes and include tests where feasible.

Handoff protocol
- Before handing off, commit changes and write a short handoff note in the PR description and `progress-tracker.md`.
- The next agent must read the same Context files before editing code.

Safety and invariants
- No secrets in code. Use env vars and a secrets manager for production.
- All tool calls must be logged to `audit_log` (SQLite) with inputs, outputs, and decision metadata.
- Any destructive action (file delete, system shutdown, email send) requires an explicit two-step confirmation.

Use this document as your checklist before writing code.
```
Read context files: project-overview.md, architecture.md, code-standards.md, ai-workflow-rules.md, progress-tracker.md.

You are Claude Code, MARK-XXXIX's architecture lead. Implement the backend for: [feature unit].

Focus on:
- Clean service-layer architecture
- Proper error handling with custom exceptions
- Type hints and Pydantic schemas
- Async/await throughout
- Follow file organization in code-standards.md

Do not touch frontend code. Update progress-tracker.md when done.
```

**Special instructions:**
- Always ask "what am I missing?" before finishing a service
- Prefer composition over inheritance
- When in doubt, add a test
- Flag any architectural inconsistency with context files

---

## Github Copilot

**Role:** Frontend Lead + UI/UX Specialist

**Strengths:**
- React components and hooks
- Tailwind CSS and design system implementation
- WebSocket real-time integration
- Voice integration (Web Speech API, audio handling)
- Animation and interaction design
- Responsive layouts

**When to use:**
- Building React components (chat, sidebar, voice orb)
- Implementing WebSocket client and real-time updates
- Voice input/output UI and state management
- Dark theme and design token implementation
- Mobile-responsive layouts

**Prompt template:**
```
Read context files: project-overview.md, ui-context.md, code-standards.md, ai-workflow-rules.md, progress-tracker.md.

You are Kimi Code, MARK-XXXIX's frontend lead. Build the React component: [component name].

Focus on:
- Tailwind CSS with MARK-XXXIX color tokens (no hardcoded hex)
- shadcn/ui base components (use npx shadcn add)
- Zustand for state management
- Responsive design (mobile-first)
- Accessibility (aria-labels, focus rings, reduced motion)

Do not touch backend code. Update progress-tracker.md when done.
```

**Special instructions:**
- Always check `ui-context.md` for exact color values and border radius
- Test components at 320px width (minimum mobile)
- Voice components must show clear state (idle/listening/thinking/speaking)
- Prefer `useCallback` and `useMemo` for performance-critical components

---

## GitHub Copilot Pro

**Role:** Inline Assistant + Boilerplate Generator

**Strengths:**
- Fast inline completions
- Boilerplate code generation
- Test scaffolding
- Repetitive pattern implementation
- Docstring and comment generation
- Type annotation suggestions

**When to use:**
- Writing repetitive code (Pydantic models, API routes, test cases)
- Filling in missing type hints
- Generating docstrings
- Creating test fixtures and mocks
- Implementing CRUD operations
- Writing SQLAlchemy/aiosqlite models

**Prompt template:**
```
You are GitHub Copilot. I am working on MARK-XXXIX, a FastAPI + React AI assistant.

Current file: [file path]
Current function: [function name]

Complete the implementation following these patterns:
- [pattern 1]
- [pattern 2]

Context: [brief description of what this function should do]
```

**Special instructions:**
- Tab-complete is your primary mode — do not write full files
- When suggesting imports, prefer the aliases defined in code-standards.md
- For test files, use pytest fixtures and parametrize where possible
- Suggest type hints even when not explicitly asked

---

## Antigravity

**Role:** [To be defined based on user preference]

**Strengths:** [User to specify]

**When to use:** [User to specify]

**Prompt template:** [User to specify]

**Special instructions:** [User to specify]

> **Note:** Antigravity is listed as one of your AI agents. Please define its role, strengths, and when to use it. Update this section accordingly.

---

## Agent Handoff Protocol

When switching from one agent to another:

1. **Commit current work** — `git add . && git commit -m "[area]: [description]"`
2. **Update progress-tracker.md** — Mark completed, update in-progress
3. **Write handoff note** — In session notes, describe:
   - What was completed
   - What was partially done
   - Known issues or TODOs
   - What the next agent should do
4. **Switch agent** — Open new chat/context with next agent
5. **New agent reads context** — Must read all context files before starting

### Example Handoff Note

```
## Handoff: Codex -> Copilot

**Completed:**
- FastAPI skeleton with /health endpoint
- Config system with Pydantic Settings
- Sentry integration

**Partially done:**
- LLM client structure started but Groq connection not tested

**Known issues:**
- None

**Next task for Kimi:**
- Build React App.tsx with dark theme
- Create ChatContainer component
- Set up Zustand stores
```

---

## Conflict Resolution

If two agents disagree on implementation:

1. **Default to context files** — The spec is the source of truth
2. **If spec is ambiguous** — Human decides, updates context file, agents follow
3. **If both approaches are valid** — Prefer the simpler one (fewer dependencies, less code)
4. **Never let agents debate** — Human arbitrates, agents implement

---

## Quality Gates

Before any agent's work is considered complete:

- [ ] Code follows `code-standards.md`
- [ ] No TypeScript `any` types (frontend) / all Python functions typed (backend)
- [ ] Error handling present and specific
- [ ] Logging added for debugging
- [ ] No secrets in code
- [ ] `progress-tracker.md` updated
- [ ] Human review completed
