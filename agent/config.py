from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_str_list(name: str, default: Iterable[str]) -> tuple[str, ...]:
    raw = os.environ.get(name)
    if not raw:
        return tuple(default)
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return tuple(parts) or tuple(default)


def default_blocked_tool_names() -> tuple[str, ...]:
    return _env_str_list("REACT_BLOCKED_TOOLS", ("agent_task", "save_memory"))


@dataclass
class ReactConfig:
    max_iterations:      int                  = _env_int("REACT_MAX_ITERATIONS", 10)
    observation_max_len: int                  = _env_int("REACT_OBS_MAX_LEN", 1500)
    max_parse_retries:   int                  = _env_int("REACT_MAX_PARSE_RETRIES", 2)
    blocked_tool_names:  tuple[str, ...]      = field(
        default_factory=default_blocked_tool_names,
    )
    model_name:          str                  = os.environ.get("REACT_MODEL", "gemini-2.0-flash")


def default_config() -> ReactConfig:
    return ReactConfig()
