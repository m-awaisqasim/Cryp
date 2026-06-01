from __future__ import annotations

import asyncio
import json
import re
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable


ToolExecutor = Callable[[str, dict[str, Any]], Awaitable[str]]


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


DEFAULT_BLOCKED_TOOLS = frozenset({"agent_task", "save_memory"})


@dataclass
class ReactConfig:
    max_iterations: int = 8
    observation_limit: int = 1800
    malformed_retries: int = 1
    blocked_tools: frozenset[str] = DEFAULT_BLOCKED_TOOLS
    model_name: str = "gemini-2.0-flash"


@dataclass
class ReactAction:
    type: str
    tool: str = ""
    parameters: dict[str, Any] | None = None
    answer: str = ""
    summary: str = ""


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def build_react_tool_registry(
    tool_declarations: list[dict[str, Any]],
    blocked_tools: set[str] | frozenset[str] = DEFAULT_BLOCKED_TOOLS,
) -> list[dict[str, Any]]:
    registry = []
    for declaration in tool_declarations:
        name = declaration.get("name", "")
        if not name or name in blocked_tools:
            continue
        registry.append(declaration)
    return registry


def truncate_observation(value: Any, limit: int = 1800) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= limit:
        return text
    return f"{text[:limit - 18].rstrip()}... [truncated]"


def parse_react_action(raw_text: str) -> ReactAction:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Model did not return a JSON object.")
        payload = json.loads(match.group(0))

    if not isinstance(payload, dict):
        raise ValueError("Model action must be a JSON object.")

    action_type = str(payload.get("type", "")).strip().lower()
    if action_type == "finish":
        answer = str(payload.get("answer", "")).strip()
        if not answer:
            raise ValueError("Finish action requires a non-empty answer.")
        return ReactAction(type="finish", answer=answer)

    if action_type == "tool":
        tool = str(payload.get("tool", "")).strip()
        parameters = payload.get("parameters", {})
        if not tool:
            raise ValueError("Tool action requires a tool name.")
        if not isinstance(parameters, dict):
            raise ValueError("Tool action parameters must be an object.")
        return ReactAction(
            type="tool",
            tool=tool,
            parameters=parameters,
            summary=str(payload.get("summary", "")).strip(),
        )

    raise ValueError("Action type must be either 'tool' or 'finish'.")


def _schema_type_matches(value: Any, schema_type: str) -> bool:
    schema_type = schema_type.upper()
    if schema_type == "STRING":
        return isinstance(value, str)
    if schema_type == "INTEGER":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "NUMBER":
        return (isinstance(value, int | float) and not isinstance(value, bool))
    if schema_type == "BOOLEAN":
        return isinstance(value, bool)
    if schema_type == "ARRAY":
        return isinstance(value, list)
    if schema_type == "OBJECT":
        return isinstance(value, dict)
    return True


def validate_tool_parameters(
    tool_name: str,
    parameters: dict[str, Any],
    tool_registry: list[dict[str, Any]],
) -> list[str]:
    declaration = next((d for d in tool_registry if d.get("name") == tool_name), None)
    if not declaration:
        return [f"Tool '{tool_name}' is not available."]

    schema = declaration.get("parameters", {}) or {}
    required = schema.get("required", []) or []
    properties = schema.get("properties", {}) or {}
    errors = []

    for key in required:
        if key not in parameters:
            errors.append(f"Missing required parameter '{key}'.")

    for key, value in parameters.items():
        prop_schema = properties.get(key)
        if not prop_schema:
            continue
        expected_type = prop_schema.get("type")
        if expected_type and not _schema_type_matches(value, expected_type):
            errors.append(
                f"Parameter '{key}' must be {expected_type}, got {type(value).__name__}."
            )

    return errors


class ReactAgentLoop:
    def __init__(
        self,
        tool_declarations: list[dict[str, Any]],
        config: ReactConfig | None = None,
        model: Any | None = None,
    ) -> None:
        self.config = config or ReactConfig()
        self.tool_registry = build_react_tool_registry(
            tool_declarations,
            blocked_tools=self.config.blocked_tools,
        )
        self._model = model

    async def run(
        self,
        goal: str,
        execute_tool: ToolExecutor,
        cancel_flag: threading.Event | None = None,
    ) -> str:
        observations: list[str] = []

        for iteration in range(1, self.config.max_iterations + 1):
            if cancel_flag and cancel_flag.is_set():
                return "Task cancelled."

            action = await self._next_action(goal, observations)

            if action.type == "finish":
                return action.answer

            if action.tool in self.config.blocked_tools:
                observations.append(
                    self._format_observation(
                        iteration,
                        action.tool,
                        "Blocked recursive or internal tool request.",
                        is_error=True,
                    )
                )
                continue

            validation_errors = validate_tool_parameters(
                action.tool,
                action.parameters or {},
                self.tool_registry,
            )
            if validation_errors:
                observations.append(
                    self._format_observation(
                        iteration,
                        action.tool,
                        "; ".join(validation_errors),
                        is_error=True,
                    )
                )
                continue

            if cancel_flag and cancel_flag.is_set():
                return "Task cancelled."

            try:
                result = await execute_tool(action.tool, action.parameters or {})
                observations.append(
                    self._format_observation(iteration, action.tool, result)
                )
            except Exception as e:
                observations.append(
                    self._format_observation(iteration, action.tool, str(e), is_error=True)
                )

        return (
            "I could not complete the task within the allowed reasoning steps. "
            "Please narrow the goal or try again."
        )

    async def _next_action(self, goal: str, observations: list[str]) -> ReactAction:
        last_error = ""
        for attempt in range(self.config.malformed_retries + 1):
            prompt = self._build_prompt(goal, observations, last_error=last_error)
            raw_text = await self._generate_text(prompt)
            try:
                return parse_react_action(raw_text)
            except Exception as e:
                last_error = (
                    f"Previous output was invalid JSON for the ReAct action schema: {e}"
                )
        return ReactAction(
            type="finish",
            answer="I could not continue because the reasoning model returned invalid action output.",
        )

    async def _generate_text(self, prompt: str) -> str:
        model = self._get_model()

        def _call_model() -> str:
            response = model.generate_content(prompt)
            return str(getattr(response, "text", "") or "").strip()

        return await asyncio.to_thread(_call_model)

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        try:
            import google.generativeai as genai

            genai.configure(api_key=_get_api_key())
            self._model = genai.GenerativeModel(self.config.model_name)
        except ImportError:
            from core import gemini_compat as genai

            genai.configure(api_key=_get_api_key())
            self._model = genai.GenerativeModel(self.config.model_name)
        return self._model

    def _build_prompt(
        self,
        goal: str,
        observations: list[str],
        last_error: str = "",
    ) -> str:
        tools_json = json.dumps(self.tool_registry, ensure_ascii=False, indent=2)
        observation_text = "\n".join(observations[-8:]) or "No observations yet."
        error_text = f"\nInvalid previous output: {last_error}\n" if last_error else ""

        return (
            "You are Cryp's internal ReAct controller for desktop automation.\n"
            "Use concise private reasoning, but output ONLY a valid JSON object.\n"
            "Do not include markdown, comments, or chain-of-thought.\n\n"
            f"Goal:\n{goal}\n\n"
            f"Available tools:\n{tools_json}\n\n"
            f"Observations:\n{observation_text}\n"
            f"{error_text}\n"
            "Choose exactly one next action.\n"
            "Tool action schema:\n"
            '{"type":"tool","tool":"<tool_name>","parameters":{},"summary":"brief reason"}\n'
            "Finish action schema:\n"
            '{"type":"finish","answer":"final user-facing result"}\n'
            "Use finish only when the goal is complete or cannot safely continue."
        )

    def _format_observation(
        self,
        iteration: int,
        tool_name: str,
        result: Any,
        is_error: bool = False,
    ) -> str:
        status = "ERROR" if is_error else "OK"
        text = truncate_observation(result, self.config.observation_limit)
        return f"{iteration}. {status} [{tool_name}] {text}"
