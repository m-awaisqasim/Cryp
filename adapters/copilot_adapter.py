from __future__ import annotations

import json
import os
from typing import Callable, Any, Dict, List

import requests


class CopilotAdapter:
    """Copilot (GPT-5 mini) adapter using an OpenAI-compatible endpoint.

    Configure via environment variables:
    - COPILOT_API_BASE: base URL, e.g. https://api.githubcopilot.com
    - COPILOT_API_KEY: bearer token (or set `COPILOT_GITHUB_TOKEN` when using GitHub Copilot token)
    - COPILOT_MODEL: model name (default: gpt-5-mini)
    """

    def __init__(self, api_key: str | None = None, api_base: str | None = None, model: str | None = None):
        # Accept either COPILOT_API_KEY or COPILOT_GITHUB_TOKEN for GitHub Copilot tokens
        self.api_key = api_key or os.environ.get("COPILOT_API_KEY") or os.environ.get("COPILOT_GITHUB_TOKEN")
        self.api_base = (api_base or os.environ.get("COPILOT_API_BASE") or "").rstrip("/")
        self.model = model or os.environ.get("COPILOT_MODEL", "gpt-5-mini")
        # Authentication header scheme. Options: 'bearer' (default), 'token', 'raw'.
        # If COPILOT_AUTH_SCHEME is set, it overrides detection. Otherwise auto-detect
        # GitHub Copilot endpoints and use raw token (Authorization: <token>).
        env_scheme = os.environ.get("COPILOT_AUTH_SCHEME")
        if env_scheme:
            self.auth_scheme = env_scheme.lower()
        else:
            self.auth_scheme = "raw" if "githubcopilot" in self.api_base else "bearer"

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("COPILOT_API_KEY is not set.")
        # Build Authorization header according to configured scheme
        if self.auth_scheme in ("bearer", "bearertoken"):
            auth_value = f"Bearer {self.api_key}"
        elif self.auth_scheme == "token":
            auth_value = f"token {self.api_key}"
        else:
            # raw / none: send the token value directly after 'Authorization:'
            auth_value = f"{self.api_key}"

        return {
            "Authorization": auth_value,
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        if not self.api_base:
            raise RuntimeError("COPILOT_API_BASE is not set.")
        return f"{self.api_base}{path}"

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None, **opts) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        payload.update(opts)

        response = requests.post(
            self._url("/chat/completions"),
            headers=self._headers(),
            data=json.dumps(payload),
            timeout=60,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Copilot API error {response.status_code}: {response.text[:300]}")

        data = response.json()
        message = data.get("choices", [{}])[0].get("message", {})
        return {
            "text": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []) or [],
            "raw": data,
        }

    def complete(self, prompt: str, **opts) -> str:
        messages = [{"role": "user", "content": prompt}]
        result = self.chat(messages, **opts)
        return result.get("text", "")

    def stream(self, prompt: str, on_token: Callable[[str], Any], **opts) -> None:
        text = self.complete(prompt, **opts)
        for ch in text:
            on_token(ch)

    def call_function(self, name: str, args: Dict[str, Any], **opts) -> Dict[str, Any]:
        return {"result": f"function_call:{name}", "args": args}
