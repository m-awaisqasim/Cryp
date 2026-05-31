from typing import Callable, Iterable, Optional

class VoiceAdapter:
    """Abstract, minimal voice adapter.

    Implementations should provide streaming synthesis and file-based synth.
    For now this adapter exposes a simple `synthesize_stream` API that can
    accept an optional `send_client_content_fn` which the legacy `main.py`
    used to send messages to the realtime session.
    """

    def synthesize_stream(self, text: str, on_chunk: Callable[[bytes], None], *, send_client_content_fn: Optional[Callable] = None) -> None:
        """Synthesize `text` and call `on_chunk(bytes)` for each audio chunk.

        If `send_client_content_fn` is provided, the adapter MAY use it to send
        text-based client content (legacy behavior). Implementations should
        prefer producing raw audio chunks.
        """
        raise NotImplementedError()


class DummyVoiceAdapter(VoiceAdapter):
    def synthesize_stream(self, text: str, on_chunk: Callable[[bytes], None], *, send_client_content_fn: Optional[Callable] = None) -> None:
        # Backwards-compatible: if send_client_content_fn provided, use it to send the text as before
        if send_client_content_fn is not None:
            try:
                send_client_content_fn(turns={"parts": [{"text": text}]}, turn_complete=True)
            except Exception:
                pass
        # No audio chunks produced by dummy adapter
        return


_adapter_singleton: VoiceAdapter | None = None


def get_voice_adapter() -> VoiceAdapter:
    global _adapter_singleton
    if _adapter_singleton is None:
        _adapter_singleton = DummyVoiceAdapter()
    return _adapter_singleton
