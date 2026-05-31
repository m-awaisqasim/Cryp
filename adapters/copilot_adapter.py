from __future__ import annotations

import json
import os
from typing import Callable, Any, Dict, List

import requests
import logging
import time
import random


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

    def _request_with_retries(self, method: str, path: str, **kwargs) -> requests.Response:
        logger = logging.getLogger("adapters.copilot_adapter")
        max_retries = int(os.environ.get("COPILOT_MAX_RETRIES", "4"))
        base_delay = float(os.environ.get("COPILOT_BACKOFF_BASE", "0.5"))
        timeout = kwargs.pop("timeout", 60)

        url = self._url(path)
        attempt = 0
        while True:
            attempt += 1
            try:
                logger.debug("Copilot request attempt %d to %s", attempt, url)
                resp = requests.request(method, url, headers=self._headers(), timeout=timeout, **kwargs)
            except requests.RequestException as e:
                logger.warning("Network error on attempt %d: %s", attempt, e)
                if attempt >= max_retries:
                    logger.error("Max retries reached for network error")
                    raise
                sleep_time = base_delay * (2 ** (attempt - 1)) * (0.5 + random.random())
                time.sleep(sleep_time)
                continue

            # If server error or rate limited, retry
            if resp.status_code in (429,) or 500 <= resp.status_code < 600:
                logger.warning("Server/rate error %d on attempt %d", resp.status_code, attempt)
                if attempt >= max_retries:
                    logger.error("Max retries reached; returning last response")
                    return resp
                sleep_time = base_delay * (2 ** (attempt - 1)) * (0.5 + random.random())
                time.sleep(sleep_time)
                continue

            return resp

    def _url(self, path: str) -> str:
        if not self.api_base:
            raise RuntimeError("COPILOT_API_BASE is not set.")
        return f"{self.api_base}{path}"

    def _normalize_schema_types(self, obj):
        """Recursively normalize JSON Schema 'type' values to lowercase expected by the API.

        This converts common uppercase values produced in the codebase (e.g. 'STRING', 'OBJECT',
        'ARRAY', 'INTEGER', 'NUMBER', 'BOOLEAN') into the JSON Schema lowercase equivalents.
        """
        if isinstance(obj, dict):
            new = {}
            for k, v in obj.items():
                if k == "type" and isinstance(v, str):
                    mapping = {
                        "STRING": "string",
                        "OBJECT": "object",
                        "ARRAY": "array",
                        "INTEGER": "integer",
                        "NUMBER": "number",
                        "BOOLEAN": "boolean",
                    }
                    new[k] = mapping.get(v, v).lower() if isinstance(v, str) else v
                else:
                    new[k] = self._normalize_schema_types(v)
            return new
        elif isinstance(obj, list):
            return [self._normalize_schema_types(v) for v in obj]
        else:
            return obj

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None, **opts) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            # Normalize any uppercase JSON Schema type names in tool declarations
            try:
                normalized = [self._normalize_schema_types(t) for t in tools]
            except Exception:
                normalized = tools
            payload["tools"] = normalized
            payload["tool_choice"] = "auto"
        payload.update(opts)

        logger = logging.getLogger("adapters.copilot_adapter")
        response = self._request_with_retries("POST", "/chat/completions", data=json.dumps(payload), timeout=opts.get("timeout", 60))
        if response.status_code >= 400:
            # For client errors, include body for diagnostics
            logger.error("Copilot API error %d: %s", response.status_code, response.text[:400])
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
