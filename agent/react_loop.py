from __future__ import annotations

import json
import re
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable

from agent.config import ReactConfig, default_blocked_tool_names, default_config
from config.settings import GEMINI_API_KEY


@dataclass
class Action:
    type: str
    tool: str | None        = None
    parameters: dict        = field(default_factory=dict)
    summary: str            = ""
    answer: str             = ""
    raw: dict               = field(default_factory=dict)
    parse_error: str | None = None


@dataclass
class Observation:
    iteration:     int
    tool:          str
    parameters:    dict
    result:        str
    is_error:      bool = False
    blocked:       bool = False
    truncated:     bool = False
    parameters_summary: str = ""

    def to_prompt(self) -> str:
        status = "ERROR" if self.is_error else "OK"
        if self.blocked:
            status = "BLOCKED"
        head = f"Iteration {self.iteration} — {status} [{self.tool}]"
        body = f"Parameters: {self.parameters_summary}"
        tail = f"Result: {self.result}"
        return f"{head}\n{body}\n{tail}"


@dataclass
class ReactResult:
    status:       str
    answer:       str
    iterations:   int
    observations: list[Observation] = field(default_factory=list)

    @property
    def finished(self) -> bool:
        return self.status == "finished"


_JSON_FENCE_RE = re.compile(r"```(?:json)?", re.IGNORECASE)


def _strip_json_fence(text: str) -> str:
    text = _JSON_FENCE_RE.sub("", text).strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def parse_action(raw_text: str) -> Action:
    if raw_text is None:
        return Action(type="invalid", parse_error="Model returned no text")

    text = raw_text.strip()
    if not text:
        return Action(type="invalid", parse_error="Model returned empty text")

    cleaned = _strip_json_fence(text)

    candidate = cleaned
    if not (candidate.startswith("{") and candidate.endswith("}")):
        first = cleaned.find("{")
        last  = cleaned.rfind("}")
        if first != -1 and last != -1 and last > first:
            candidate = cleaned[first:last + 1]

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return Action(type="invalid", parse_error=f"Malformed JSON: {exc.msg}")

    if not isinstance(data, dict):
        return Action(type="invalid", parse_error="Top-level JSON must be an object")

    action_type = str(data.get("type", "")).strip().lower()

    if action_type == "finish":
        answer = data.get("answer", "")
        if not isinstance(answer, str):
            answer = str(answer)
        return Action(
            type="finish",
            answer=answer.strip(),
            raw=data,
        )

    if action_type == "tool":
        tool_name = str(data.get("tool", "")).strip()
        if not tool_name:
            return Action(type="invalid", parse_error="tool action missing 'tool' name", raw=data)

        params = data.get("parameters", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return Action(type="invalid", parse_error="tool parameters must be an object", raw=data)

        summary = str(data.get("summary", "")).strip()
        return Action(
            type="tool",
            tool=tool_name,
            parameters=params,
            summary=summary,
            raw=data,
        )

    return Action(type="invalid", parse_error=f"Unknown action type '{action_type}'", raw=data)


def summarize_parameters(parameters: dict, max_len: int = 200) -> str:
    try:
        text = json.dumps(parameters, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        text = str(parameters)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def truncate_observation(text: str, max_len: int) -> tuple[str, bool]:
    if text is None:
        return "", False
    if max_len <= 0 or len(text) <= max_len:
        return text, False
    head = text[: max_len // 2].rstrip()
    tail = text[-max_len // 2:].lstrip()
    note = f"\n\n[...truncated, original length {len(text)} chars...]"
    return f"{head}{note}{tail}", True


def format_observation(
    observation: str,
    *,
    max_len: int,
    is_error: bool = False,
) -> tuple[str, bool]:
    text, truncated = truncate_observation(observation, max_len)
    if is_error and not text.lower().startswith("error"):
        text = f"ERROR: {text}"
    return text, truncated


def build_tool_registry(
    declarations: Iterable[dict],
    blocked: Iterable[str] = (),
) -> list[dict]:
    blocked_set = {str(name).strip() for name in default_blocked_tool_names()}
    for name in blocked:
        blocked_set.add(str(name).strip())

    registry: list[dict] = []
    for decl in declarations:
        name = str(decl.get("name", "")).strip()
        if not name or name in blocked_set:
            continue
        registry.append({
            "name":        name,
            "description": decl.get("description", "").strip(),
            "parameters":  decl.get("parameters", {}),
        })
    return registry


def format_registry_for_prompt(registry: list[dict]) -> str:
    blocks: list[str] = []
    for tool in registry:
        params = tool.get("parameters", {})
        props = params.get("properties", {}) if isinstance(params, dict) else {}
        required = set(params.get("required", []) or []) if isinstance(params, dict) else set()
        if props:
            lines: list[str] = []
            for pname, pinfo in props.items():
                ptype = pinfo.get("type", "string") if isinstance(pinfo, dict) else "string"
                pdesc = pinfo.get("description", "") if isinstance(pinfo, dict) else ""
                mark  = " (required)" if pname in required else ""
                lines.append(f"    - {pname} ({ptype}){mark} — {pdesc}")
            params_block = "\n".join(lines)
        else:
            params_block = "    - (no parameters)"
        blocks.append(
            f"- {tool['name']}\n"
            f"  Description: {tool['description']}\n"
            f"  Parameters:\n{params_block}"
        )
    return "\n\n".join(blocks) if blocks else "(no tools available)"


REACT_SYSTEM_PROMPT = """You are the ReAct planning module of MARK XXV, a personal AI assistant.

You solve a single user goal by repeatedly choosing exactly ONE next action
based on the goal and every observation recorded so far. You never narrate
private chain-of-thought; you output ONLY a JSON object describing the next
action.

AVAILABLE TOOLS
{tool_registry}

STOP / SAFETY RULES (HARD CONSTRAINTS)
- You MUST NOT call `agent_task`, `save_memory`, or any other internal-only tool.
- If a tool is missing or its parameters don't match, pick a different tool
  that fits the goal. Do not invent new tool names.
- Never ask the user a question. The user is not in the loop; the system
  handles voice replies.
- Stop calling tools as soon as the user goal is satisfied. Calling extra
  tools wastes time and risks context overflow.

OUTPUT FORMAT (strict)
Return a single JSON object with no markdown, no commentary, no backticks:

For the next tool call:
{{
  "type": "tool",
  "tool": "<tool_name>",
  "parameters": {{ ... }},
  "summary": "<one short sentence on why this tool advances the goal>"
}}

When the goal is complete and you have enough information to answer:
{{
  "type": "finish",
  "answer": "<final user-facing result, concise and direct>"
}}
"""


def _build_user_message(goal: str, observations: list[Observation], plan_context: str | None = None) -> str:
    parts: list[str] = []
    if plan_context and plan_context.strip():
        parts.append(f"PLANNED APPROACH:\n{plan_context.strip()}")
    parts.append(f"USER GOAL:\n{goal.strip()}")
    if observations:
        history = "\n\n".join(obs.to_prompt() for obs in observations)
        parts.append(f"OBSERVATIONS SO FAR:\n{history}")
    else:
        parts.append("OBSERVATIONS SO FAR:\n(none — this is the first iteration)")
    parts.append(
        "Choose the next action. Output ONLY the JSON object described above."
    )
    return "\n\n".join(parts)


ToolExecutor = Callable[[str, dict], Awaitable[str]]
ModelCaller  = Callable[[str, str], Awaitable[str]]


def make_default_model_caller(
    model_name: str = "gemini-3.1-flash-lite",
) -> ModelCaller:
    async def call(system_prompt: str, user_message: str) -> str:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=model_name,
                contents=f"{system_prompt.strip()}\n\n---\n\n{user_message.strip()}",
            ),
        )
        return response.text

    return call


class ReactAgentLoop:

    def __init__(
        self,
        *,
        config:        ReactConfig | None = None,
        registry:      list[dict] | None  = None,
        model_caller:  ModelCaller | None = None,
        max_iterations: int | None        = None,
        observation_max_len: int | None   = None,
        max_parse_retries: int | None     = None,
        event_bus:     object | None      = None,
    ) -> None:
        self.config              = config or default_config()
        self.registry            = registry if registry is not None else []
        self.model_caller        = model_caller or make_default_model_caller()
        self.max_iterations      = (
            max_iterations if max_iterations is not None else self.config.max_iterations
        )
        self.observation_max_len = (
            observation_max_len if observation_max_len is not None
            else self.config.observation_max_len
        )
        self.max_parse_retries   = (
            max_parse_retries if max_parse_retries is not None
            else self.config.max_parse_retries
        )
        self._blocked_names      = set(self.config.blocked_tool_names)
        self._event_bus          = event_bus

    def is_blocked(self, tool_name: str) -> bool:
        return tool_name in self._blocked_names

    def _format_registry(self) -> str:
        return format_registry_for_prompt(self.registry)

    def _build_user_message(self, goal: str, observations: list[Observation], plan_context: str | None = None) -> str:
        return _build_user_message(goal, observations, plan_context)

    def _build_observation(
        self,
        *,
        iteration: int,
        tool:      str,
        parameters: dict,
        result:    str,
        is_error:  bool = False,
        blocked:   bool = False,
    ) -> Observation:
        formatted, truncated = format_observation(
            result,
            max_len=self.observation_max_len,
            is_error=is_error,
        )
        return Observation(
            iteration=iteration,
            tool=tool,
            parameters=dict(parameters),
            result=formatted,
            is_error=is_error,
            blocked=blocked,
            truncated=truncated,
            parameters_summary=summarize_parameters(parameters),
        )

    async def run(
        self,
        goal:         str,
        executor:     ToolExecutor,
        *,
        cancel_flag:  threading.Event | None = None,
        plan_context: str | None          = None,
    ) -> ReactResult:
        observations: list[Observation] = []
        iterations   = 0
        parse_failures = 0

        system_prompt = REACT_SYSTEM_PROMPT.format(
            tool_registry=self._format_registry(),
        )

        def _publish(event: dict):
            try:
                if self._event_bus is not None:
                    self._event_bus.publish(event)
            except Exception:
                pass

        _publish({"type": "react", "status": "running", "goal": goal, "step": 0, "total": self.max_iterations})

        while iterations < self.max_iterations:
            if cancel_flag is not None and cancel_flag.is_set():
                _publish({"type": "react", "status": "cancelled"})
                return ReactResult(
                    status="cancelled",
                    answer="Task cancelled.",
                    iterations=iterations,
                    observations=observations,
                )

            iterations += 1

            user_message = self._build_user_message(goal, observations, plan_context)
            try:
                raw = await self.model_caller(system_prompt, user_message)
            except (MemoryError, KeyboardInterrupt, SystemExit):
                raise
            except Exception as exc:
                return ReactResult(
                    status="error",
                    answer=f"Model call failed: {exc}",
                    iterations=iterations,
                    observations=observations,
                )

            action = parse_action(raw)

            if action.parse_error:
                parse_failures += 1
                observations.append(self._build_observation(
                    iteration=iterations,
                    tool="<model>",
                    parameters={"raw": raw or ""},
                    result=f"Malformed model output: {action.parse_error}",
                    is_error=True,
                ))
                if parse_failures > self.max_parse_retries:
                    _publish({"type": "react", "status": "completed"})
                    return ReactResult(
                        status="error",
                        answer="Model kept producing malformed actions; aborting.",
                        iterations=iterations,
                        observations=observations,
                    )
                continue

            if action.type == "finish":
                _publish({"type": "react", "status": "completed"})
                return ReactResult(
                    status="finished",
                    answer=action.answer or "Task complete.",
                    iterations=iterations,
                    observations=observations,
                )

            if action.type != "tool":
                observations.append(self._build_observation(
                    iteration=iterations,
                    tool="<model>",
                    parameters={"raw": action.raw},
                    result=f"Unsupported action: {action.type!r}",
                    is_error=True,
                ))
                continue

            tool_name = action.tool or ""
            if self.is_blocked(tool_name):
                observations.append(self._build_observation(
                    iteration=iterations,
                    tool=tool_name,
                    parameters=action.parameters,
                    result=(
                        f"Tool '{tool_name}' is blocked: recursive or "
                        f"internal-only tool cannot be called from inside ReAct."
                    ),
                    is_error=True,
                    blocked=True,
                ))
                continue

            if not any(t["name"] == tool_name for t in self.registry):
                observations.append(self._build_observation(
                    iteration=iterations,
                    tool=tool_name,
                    parameters=action.parameters,
                    result=(
                        f"Tool '{tool_name}' is not available. "
                        f"Pick a different tool from the registry."
                    ),
                    is_error=True,
                ))
                continue

            if cancel_flag is not None and cancel_flag.is_set():
                return ReactResult(
                    status="cancelled",
                    answer="Task cancelled.",
                    iterations=iterations,
                    observations=observations,
                )

            try:
                result_text = await executor(tool_name, action.parameters)
                is_error = False
                if isinstance(result_text, str) and result_text.lower().startswith("tool '"):
                    is_error = True
                if isinstance(result_text, str) and result_text.lower().startswith("error"):
                    is_error = True
            except (MemoryError, KeyboardInterrupt, SystemExit):
                raise
            except Exception as exc:
                result_text = f"{type(exc).__name__}: {exc}"
                is_error = True

            observations.append(self._build_observation(
                iteration=iterations,
                tool=tool_name,
                parameters=action.parameters,
                result=result_text,
                is_error=is_error,
            ))

            _publish({"type": "react", "status": "running", "goal": goal, "step": iterations, "total": self.max_iterations, "result": result_text[:200] if result_text else ""})

        _publish({"type": "react", "status": "completed"})
        return ReactResult(
            status="max_iterations",
            answer=(
                f"Task did not complete within {self.max_iterations} "
                f"iterations, sir."
            ),
            iterations=iterations,
            observations=observations,
        )
