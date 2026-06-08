## Why

Transient tool failures (network timeouts, 503 errors, connection drops) currently fail immediately and are spoken aloud to the user, creating a poor experience. No retry or degradation mechanism exists, so a brief network hiccup or temporary API outage causes unnecessary interruptions.

## What Changes

- Add a central `retry_with_backoff` utility that wraps any async/sync tool call with up to 3 retries, exponential backoff (1s, 2s, 4s), and optional jitter
- Integrate retry into `_execute_tool()` in `main.py` so all tools transparently benefit
- On exhausting retries for `browser_control`, automatically fall back to `web_search` for query-based actions
- Add configurable retry counts via environment variables
- No change to any tool's external interface, function signature, or return format

## Capabilities

### New Capabilities
- `tool-execution`: Unified retry layer for tool dispatch with exponential backoff, jitter, configurable max attempts, and fallback routing between browser_control and web_search

### Modified Capabilities
<!-- No existing specs change requirement-level behavior -->

## Impact

- `main.py`: `_execute_tool()` gets retry/failover wrapper
- `actions/browser_control.py`: No interface change; retry handled upstream
- `actions/web_search.py`: No interface change; becomes implicit fallback target
- `agent/react_loop.py`: No interface change; retry is transparent
