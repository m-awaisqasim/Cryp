## ADDED Requirements

### Requirement: Retry transient tool failures
When a tool dispatch fails due to a transient error, the system SHALL retry automatically up to `RETRY_MAX_ATTEMPTS` times with exponential backoff before reporting failure.

#### Scenario: Transient timeout is retried
- **WHEN** a tool call raises `asyncio.TimeoutError` on first attempt
- **THEN** the system waits `RETRY_BASE_DELAY * 2^attempt` seconds and retries the call

#### Scenario: Success on second attempt
- **WHEN** a tool call fails on first attempt (transient error) and succeeds on second attempt
- **THEN** the system returns the successful result without any error indication

#### Scenario: Permanent error is not retried
- **WHEN** a tool call fails with an error unrelated to connectivity (e.g. invalid arguments, auth failure)
- **THEN** the system SHALL NOT retry and SHALL immediately return the error

### Requirement: Exponential backoff with jitter
The retry delay SHALL use exponential backoff with configurable jitter to avoid stampeding on network recovery.

#### Scenario: Backoff delay increases exponentially
- **WHEN** a tool call fails on attempt N (1-indexed)
- **THEN** the delay before attempt N+1 SHALL be `min(RETRY_BASE_DELAY * 2^(N-1) + random(0, RETRY_JITTER), RETRY_MAX_DELAY)` seconds

### Requirement: Configurable retry parameters
Retry behavior SHALL be configurable via environment variables without code changes.

#### Scenario: Custom retry count
- **WHEN** `RETRY_MAX_ATTEMPTS` is set to `5`
- **THEN** the system SHALL retry up to 5 times before reporting failure

#### Scenario: Custom delay values
- **WHEN** `RETRY_BASE_DELAY` is `2.0` and `RETRY_MAX_DELAY` is `30.0`
- **THEN** backoff SHALL start at 2s and cap at 30s

### Requirement: Fallback from browser_control to web_search
When `browser_control` exhausts all retries for a search-like action, the system SHALL automatically fall back to `web_search` with the same query parameters.

#### Scenario: browser_control search fails and falls back
- **WHEN** `browser_control` with action `search` or a navigation/click-by-description action fails after all retries
- **WHEN** the original query parameter is available
- **THEN** the system SHALL execute `web_search` with the same query and return its result

#### Scenario: Non-search browser action does not fall back
- **WHEN** `browser_control` with action `click` (using explicit selector, not description) fails after all retries
- **THEN** the system SHALL NOT fall back to `web_search` and SHALL return the error

### Requirement: Fallback is transparent
Fallback execution SHALL be invisible to the caller. The return format SHALL match a normal tool result.

#### Scenario: Fallback result returned as normal tool output
- **WHEN** a fallback to `web_search` occurs
- **THEN** the result SHALL be returned as if it came from the original tool call

### Requirement: Transience heuristics
The system SHALL determine whether an error is transient based on its type and message content.

#### Scenario: Recognized transient errors trigger retry
- **WHEN** the error is `TimeoutError`, `ConnectionError`, or the message contains `503`, `timeout`, `deadline exceeded`, or `connection`
- **THEN** the system SHALL classify the error as transient and retry

#### Scenario: Explicit error return from tool is also retried
- **WHEN** a tool returns a string result containing `timeout`, `503`, or `connection` (error returned as string, not exception)
- **THEN** the system SHALL classify it as transient and retry
