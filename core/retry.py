from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    retry_if_result,
)

from agent.config import RetryConfig

TRANSIENT_KEYWORDS = [
    "timeout",
    "503",
    "connection",
    "unavailable",
    "deadline exceeded",
    "429",
    "reset by peer",
    "broken pipe",
    "connectionerror",
    "timeouterror",
]


def is_transient_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in TRANSIENT_KEYWORDS)


def is_transient_result(result: str) -> bool:
    if not isinstance(result, str):
        return False
    result_lower = result.lower()
    return any(k in result_lower for k in TRANSIENT_KEYWORDS)


def make_retry_decorator(cfg: RetryConfig):
    return retry(
        stop=stop_after_attempt(cfg.max_attempts + 1),
        wait=wait_exponential(
            multiplier=cfg.base_delay,
            max=cfg.max_delay,
        ),
        retry=(
            retry_if_exception(is_transient_error)
            | retry_if_result(is_transient_result)
        ),
        reraise=True,
    )
