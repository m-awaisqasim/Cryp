"""Planner Layer — intercepts agent_task, announces a plan, then hands off to ReAct."""
from __future__ import annotations

import asyncio
import re
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

from agent.config import PlannerConfig
from config.settings import GEMINI_API_KEY

_FENCE_RE = re.compile(r"```(?:json)?", re.IGNORECASE)


PLANNER_PROMPT = (
    "You are the announcement planner for MARK XXV. Produce a short, numbered, "
    "human-readable plan that the assistant will speak aloud BEFORE executing a "
    "complex user goal. Output numbered prose only (e.g. 'Step 1: ... Step 2: ...'). "
    "3-5 short steps. No invented tools, no internal tool names, no JSON, no markdown."
)


def is_complex_goal(goal: str, config: PlannerConfig) -> bool:
    if config.planner_always_on:
        return True
    text = (goal or "").strip()
    if len(text) >= config.min_goal_chars:
        return True
    lowered = f" {text.lower()} "
    return any(tok in lowered for tok in config.coordination_words)


def truncate_plan(plan: str, max_chars: int) -> str:
    if not plan or max_chars <= 0 or len(plan) <= max_chars:
        return plan
    return plan[: max_chars - 1].rstrip() + "…"

async def generate_plan(goal: str, config: PlannerConfig) -> Optional[str]:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=config.model_name,
                contents=f"User goal: {goal}",
                config=types.GenerateContentConfig(
                    system_instruction=PLANNER_PROMPT,
                ),
            ),
        )
        text = (getattr(response, "text", "") or "").strip()
        text = _FENCE_RE.sub("", text).strip().strip("`").strip()
        return text or None
    except Exception:
        return None


class PlannerLayer:

    def __init__(self, config: PlannerConfig) -> None:
        self.config = config

    async def announce(
        self,
        goal: str,
        *,
        speak: Callable[[str], None],
        write_log: Callable[[str], None],
        cancel_flag: Optional[threading.Event] = None,
    ) -> Optional[str]:
        try:
            cfg = self.config
            if not cfg.enabled or (cancel_flag is not None and cancel_flag.is_set()):
                return None
            if not is_complex_goal(goal, cfg):
                return None
            plan = await generate_plan(goal, cfg)
            if not plan or (cancel_flag is not None and cancel_flag.is_set()):
                return plan or None
            plan = truncate_plan(plan, cfg.max_plan_chars)
            try:
                speak(plan)
            except Exception:
                return None
            try:
                write_log(f"PLAN: {plan}")
            except Exception:
                pass
            if cfg.speak_wait_seconds > 0:
                await asyncio.sleep(cfg.speak_wait_seconds)
            if cancel_flag is not None and cancel_flag.is_set():
                return None
            return plan
        except Exception:
            return None


