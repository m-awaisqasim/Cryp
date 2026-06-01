"""Compatibility wrapper that mimics google.generativeai on top of google-genai."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from google import genai

_API_KEY: str | None = None
_CLIENTS: dict[str | None, genai.Client] = {}


def configure(*, api_key: str | None = None) -> None:
    """Store API key for later model instantiation."""
    global _API_KEY
    if api_key:
        _API_KEY = api_key


def _get_client(api_key: str | None) -> genai.Client:
    if api_key not in _CLIENTS:
        _CLIENTS[api_key] = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1beta"},
        )
    return _CLIENTS[api_key]


@dataclass
class _TextResponse:
    text: str


class GenerativeModel:
    """Shim with a generate_content API similar to google.generativeai."""

    def __init__(self, model_name: str):
        self._model_name = model_name

    def generate_content(self, contents: Any) -> _TextResponse:
        api_key = _API_KEY
        if not api_key:
            raise ValueError("Gemini API key not configured. Call configure(api_key=...).")
        client = _get_client(api_key)
        response = client.models.generate_content(
            model=self._model_name,
            contents=contents,
        )
        text = getattr(response, "text", None)
        if text is None:
            text = ""
        return _TextResponse(text=text)
