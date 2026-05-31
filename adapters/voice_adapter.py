from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Callable, Optional


_OS = platform.system()


def _is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "rate limit",
            "quota",
            "resource_exhausted",
            "429",
            "deadline expired",
        )
    )


def _system_tts(text: str) -> bool:
    text = text.strip()
    if not text:
        return True

    commands: list[list[str]]
    if _OS == "Linux":
        commands = [["spd-say", text], ["espeak-ng", text], ["espeak", text]]
    elif _OS == "Darwin":
        commands = [["say", text]]
    else:
        commands = [[
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Add-Type -AssemblyName System.Speech; "
                f"$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak('{text.replace("'", "''")}')"
            ),
        ]]

    for command in commands:
        try:
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            return True
        except FileNotFoundError:
            continue
        except Exception:
            continue

    return False

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
    def synthesize_stream(
        self,
        text: str,
        on_chunk: Callable[[bytes], None],
        *,
        send_client_content_fn: Optional[Callable] = None,
    ) -> None:
        if send_client_content_fn is not None:
            try:
                send_client_content_fn(turns={"parts": [{"text": text}]}, turn_complete=True)
                return
            except Exception as exc:
                if not _is_rate_limit_error(exc):
                    raise

        if not _system_tts(text):
            return

        return


class GeminiRelayVoiceAdapter(DummyVoiceAdapter):
    """Voice adapter that prefers the Gemini live relay and falls back locally."""

    pass


_adapter_singleton: VoiceAdapter | None = None


def get_voice_adapter() -> VoiceAdapter:
    global _adapter_singleton
    if _adapter_singleton is None:
        _adapter_singleton = GeminiRelayVoiceAdapter()
    return _adapter_singleton
