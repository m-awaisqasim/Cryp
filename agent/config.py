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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off")


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class ReactConfig:
    max_iterations:      int                  = _env_int("REACT_MAX_ITERATIONS", 10)
    observation_max_len: int                  = _env_int("REACT_OBS_MAX_LEN", 1500)
    max_parse_retries:   int                  = _env_int("REACT_MAX_PARSE_RETRIES", 2)
    blocked_tool_names:  tuple[str, ...]      = field(
        default_factory=default_blocked_tool_names,
    )
    model_name:          str                  = os.environ.get("REACT_MODEL", "gemini-3.1-flash-lite")


def default_config() -> ReactConfig:
    return ReactConfig()


@dataclass
class PlannerConfig:
    enabled:              bool               = _env_bool("JARVIS_PLANNER", True)
    model_name:           str                = os.environ.get("PLANNER_MODEL", "gemini-3.1-flash-lite")
    speak_wait_seconds:   float              = _env_float("PLANNER_WAIT_SECONDS", 1.5)
    min_goal_chars:       int                = _env_int("PLANNER_MIN_GOAL_CHARS", 40)
    coordination_words:   tuple[str, ...]    = _env_str_list(
        "PLANNER_COORD_WORDS",
        (" and ", " then ", " after ", ";", " plus "),
    )
    max_plan_chars:       int                = _env_int("PLANNER_MAX_CHARS", 800)
    planner_always_on:    bool               = _env_bool("PLANNER_ALWAYS_ON", False)


def default_planner_config() -> PlannerConfig:
    return PlannerConfig()
