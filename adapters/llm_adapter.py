from typing import Callable, Any, AsyncIterator, Protocol, Dict

class LLMAdapter(Protocol):
    """Interface for LLM providers.

    Implementations must provide synchronous and streaming methods.
    """

    def complete(self, prompt: str, **opts) -> str:
        ...

    def stream(self, prompt: str, on_token: Callable[[str], Any], **opts) -> None:
        ...

    def call_function(self, name: str, args: Dict[str, Any], **opts) -> Dict[str, Any]:
        ...
