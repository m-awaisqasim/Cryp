# Code Standards — MARK-XXXIX

## General Principles

1. **One responsibility per file** — If a file exceeds 300 lines, split it. If a function exceeds 50 lines, extract helpers.
2. **Fix root causes, not symptoms** — Do not layer workarounds. If a bug exists, understand why before patching.
3. **No mixing unrelated concerns** — A service handles business logic. A route handles HTTP. A component handles UI. Never mix two.
4. **Explicit over implicit** — Type everything. Name everything clearly. No magic strings, no hidden defaults.
5. **Fail fast, fail loud** — Validate inputs at boundaries. Raise specific exceptions with context. Do not swallow errors.

## Python

### Type Hints
- All function parameters and return types must be typed
- Use `from __future__ import annotations` for forward references
- Prefer `dict[str, Any]` over `Dict[str, Any]` (Python 3.12 style)
- Use `|` union syntax: `str | None` instead of `Optional[str]`

### Pydantic
- All request/response schemas use Pydantic v2 BaseModel
- Use `Field(..., description="...")` for documentation
- Use `ConfigDict(strict=True)` for strict validation
- Environment config uses `pydantic-settings` with `SettingsConfigDict`

### Async
- All I/O operations are async: `async def`, `await`, `asyncio`
- Use `httpx` for HTTP clients — never `requests` in async code
- Database: `aiosqlite` for SQLite async operations
- ChromaDB: Use async client where available, wrap sync calls in `asyncio.to_thread`

### Error Handling
- Custom exception hierarchy in `app/core/exceptions.py`:
  - `AssistantException` (base)
  - `LLMError` (LLM failures)
  - `ToolError` (tool execution failures)
  - `MemoryError` (memory operation failures)
  - `ValidationError` (input validation failures)
- Log at appropriate levels: `DEBUG` for internals, `INFO` for flow, `ERROR` for failures
- Never catch `Exception` broadly — catch specific exceptions, log, re-raise if unrecoverable

### Imports
- Group: stdlib -> third-party -> local
- Absolute imports only: `from app.services.brain import BrainService`
- No circular imports — if tempted, extract shared types to `app/models/`

## FastAPI

### Route Structure
```python
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    # 1. Validate input (Pydantic does this)
    # 2. Call service layer
    # 3. Return response model
    # NO business logic here
```

### Rules
- One router per feature area: `chat.py`, `memory.py`, `tasks.py`, `voice.py`
- All routes have `response_model` and `status_code`
- Use `Depends()` for dependency injection (services, config)
- WebSocket routes: `websocket_endpoint` in `api/ws.py`, delegate to service immediately

## API Response Shapes

All API responses follow this envelope:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  ## Code Standards — MARK-XXXIX

  This doc provides concise, enforceable coding standards for the project.

  Principles
  - Single responsibility per file. If a file exceeds ~300 lines, split it.
  - Fail fast and fail loudly. Validate inputs at service boundaries.
  ## Code Standards — MARK-XXXIX

  This document provides concise, enforceable coding standards for the MARK-XXXIX project.

  Principles
  - Single responsibility per file. If a file exceeds ~300 lines, split it.
  - Fail fast and fail loudly. Validate inputs at service boundaries.
  ## Code Standards — MARK-XXXIX

  This document provides concise, enforceable coding standards for the MARK-XXXIX project.

  Principles
  - Single responsibility per file. If a file exceeds ~300 lines, split it.
  - Fail fast and fail loudly. Validate inputs at service boundaries.
  - Explicit typing for public functions and service interfaces.

  Python rules
  - Use type hints everywhere; prefer `from __future__ import annotations`.
  - Use `httpx` for async HTTP and `aiosqlite` or SQLAlchemy async for DB ops.
  - Keep blocking IO off the event loop via `asyncio.to_thread` when necessary.

  Pydantic / Settings
  - Use Pydantic v2 models for schema validation and `pydantic-settings` for config.

  Async and error handling
  - Prefer `async def` for I/O boundaries. Catch and raise specific exceptions, not `Exception`.
  - Define a small exception hierarchy in `app/core/exceptions.py` (LLMError, ToolError, MemoryError, ValidationError).

  Imports and formatting
  - Group imports: stdlib, third-party, local. Use absolute imports for local modules.
  - Format with `black` and lint with `ruff`/`flake8` rules.

  API design
  - Keep FastAPI routes thin: validation → call service → return response model.
  - Use `Depends` for DI and `response_model` for all HTTP routes.

  Frontend
  - Functional components only. Use Zustand for global state. Tailwind for styles, no inline styles.

  Testing
  - Unit tests for all service modules. Integration tests for WebSocket + brain flows with mocked LLMs.

  Git
  - Small commits, descriptive messages, no secrets in the repo.
