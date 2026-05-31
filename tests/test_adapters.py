import pytest

from adapters.copilot_adapter import CopilotAdapter
from adapters.voice_adapter import get_voice_adapter


def test_copilot_adapter_streaming():
    adapter = CopilotAdapter()
    tokens = []

    def on_token(t):
        tokens.append(t)

    adapter.stream("hello world", on_token=on_token)
    assert len(tokens) > 0
    assert "hello" in "".join(tokens)


def test_voice_adapter_dummy_send():
    adapter = get_voice_adapter()
    sent = {}

    def fake_send(**kwargs):
        sent.update(kwargs)

    # Dummy adapter should call the provided send function
    adapter.synthesize_stream("Test message", lambda chunk: None, send_client_content_fn=lambda **kw: fake_send(**kw))
    assert sent != {}
    assert "turns" in sent


def test_voice_adapter_text_only_fallback_without_send_fn():
    adapter = get_voice_adapter()
    adapter.synthesize_stream("Fallback test", lambda chunk: None)