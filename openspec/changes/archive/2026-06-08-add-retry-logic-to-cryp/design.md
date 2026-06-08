## Context

Tools are dispatched through a single `_execute_tool()` method in `main.py:917` which runs each tool via `loop.run_in_executor()`. Errors propagate to a single try/except that speaks the failure aloud. There is no retry mechanism — a transient network blip or 503 from Gemini causes an audible error. The ReAct loop (`react_loop.py`) uses string prefix matching (`"tool '"` or `"error"`) to detect failures but never retries automatically. An orphaned `error_handler.py` has retry/skip/replan logic but is not wired in.

The existing ad-hoc retries (web_search falling back to DuckDuckGo, browser_control retrying blank pages) are scattered, inconsistent, and lack exponential backoff.

## Goals / Non-Goals

**Goals:**
- Automatically retry transient tool failures (timeouts, 503s, connection drops) up to 3 times with exponential backoff
- Add jitter to prevent thundering herd after network recovery
- On exhausting retries for `browser_control`, fall back to `web_search` for query-based actions
- Keep retry invisible to tools — no signature changes, no behavioral changes
- Make retry count and backoff configurable via environment variables

**Non-Goals:**
- No changes to any tool's internal implementation or return format
- No GUI or voice notification changes (retries are silent)
- No retry for non-transient errors (bad arguments, auth failures, invalid selectors)
- No retry for `screen_process` (runs outside the main dispatch path)
- No changes to the ReAct loop's error detection logic

## Decisions

**Decision 1: Add retry wrapper in `_execute_tool()` rather than per-tool**
Every tool call passes through `_execute_tool()`. Wrapping the dispatch there gives universal coverage without modifying any tool function. Alternatives considered: per-tool decorators (too invasive, violates no-interface-change constraint), monkey-patching the executor (fragile, hard to debug).

**Decision 2: Exponential backoff with jitter**
Formula: `min(base * 2^attempt + random(0, jitter_max), max_delay)`. Default base=1s, jitter=0.5s, max=10s, attempts=3. This is the standard approach used by AWS SDKs and avoids stampeding on recovery.

**Decision 3: Fallback via action introspection**
Only `browser_control` with action `search` or `smart_click` (by description) falls back to `web_search`. The wrapper inspects `fc.args` after exhausting retries — if tool name is `browser_control` and the action is search-like, reroute to `web_search` with the same `query` parameter.

**Decision 4: Config via env vars**
`RETRY_MAX_ATTEMPTS=3`, `RETRY_BASE_DELAY=1.0`, `RETRY_JITTER=0.5`, `RETRY_MAX_DELAY=10.0`. Picked env vars over config file because Cryp already uses env vars extensively (see `agent/config.py`).

**Decision 5: Determine transience heuristically**
A tool failure is "retryable" if: the exception or result string contains `TimeoutError`, `ConnectionError`, `503`, `timeout`, `deadline exceeded`, or `connection`. All other errors (invalid args, auth failures) pass through immediately.

## Risks / Trade-offs

- [Masking permanent errors] → The retry count is low (3) and backoff is fast (<5s total). Transient failures are retried; persistent ones surface quickly.
- [Latency] → In the worst case, 3 failed retries add ~7s before fallback/kaboom. This is acceptable for tool operations that already take seconds.
- [Fallback to web_search may return different results] → This is intentional: degraded-but-functional is better than a spoken error. The ReAct model can reconcile differences.
- [Env var proliferation] → 4 new vars, aligned with existing pattern in `agent/config.py`.
