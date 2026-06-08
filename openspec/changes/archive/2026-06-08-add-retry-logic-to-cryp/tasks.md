## 1. Retry Utility Module

- [x] 1.1 Create `core/retry.py` with `is_transient_error()` function that checks exception type/message for timeout, 503, connection, deadline exceeded
- [x] 1.2 Implement `retry_with_backoff()` async wrapper: accepts a coroutine factory, retries up to `max_attempts` with exponential backoff (`base * 2^attempt + random jitter`), capped at `max_delay`
- [x] 1.3 Add `_env_float()` helper to `agent/config.py` and define `RetryConfig` dataclass with `max_attempts=3`, `base_delay=1.0`, `jitter=0.5`, `max_delay=10.0` read from env vars

## 2. Integrate Retry into Tool Dispatch

- [x] 2.1 In `main.py:_execute_tool()`, wrap each `run_in_executor` call (except `save_memory`, `screen_process`, `shutdown_jarvis`) with `retry_with_backoff()`
- [x] 2.2 Ensure `is_transient_error()` also inspects string error results (not just exceptions) for transient keywords
- [x] 2.3 After retries exhausted, fall through to existing error handling for non-fallback tools

## 3. browser_control → web_search Fallback

- [x] 3.1 After `browser_control` exhausts retries, inspect `fc.args`: if `action` is `search`, or `action` is `smart_click`/`smart_type` with a `description` present, reroute to `web_search` using the `query` or `description` arg
- [x] 3.2 If fallback succeeds, return `web_search` result transparently (same `FunctionResponse` format, same `fc.id`/`fc.name`)
- [x] 3.3 If fallback also fails, return the original `browser_control` error

## 4. Verify

- [x] 4.1 Run the existing test suite: 245 tests run, 31 new retry tests pass, 1 pre-existing failure in test_proactive (unrelated)
- [ ] 4.2 Manual smoke test: trigger a transient-style error and confirm retry count in logs
