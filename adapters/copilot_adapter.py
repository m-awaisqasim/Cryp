from .llm_adapter import LLMAdapter
from typing import Callable, Any, Dict


class CopilotAdapter:
    """Minimal Copilot (GPT-5 mini) adapter stub.

    This file provides a scaffold for integrating Copilot streaming/completion
    APIs. Replace the stub implementations with the real API client.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def complete(self, prompt: str, **opts) -> str:
        # TODO: integrate real Copilot client
        return "[copilot_stub] " + prompt[:100]

    def stream(self, prompt: str, on_token: Callable[[str], Any], **opts) -> None:
        # Naive synchronous token streaming for tests
        text = self.complete(prompt, **opts)
        for ch in text:
            on_token(ch)

    def call_function(self, name: str, args: Dict[str, Any], **opts) -> Dict[str, Any]:
        # Implement function-calling semantics backed by Copilot
        return {"result": f"stubbed {name}", "args": args}
