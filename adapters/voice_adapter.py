from __future__ import annotations

import asyncio
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Callable, Optional

from google import genai
from google.genai import types


_OS = platform.system()

BASE_DIR = Path(__file__).resolve().parent.parent
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
GEMINI_TTS_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
EDGE_TTS_VOICE = os.environ.get("EDGE_TTS_VOICE", "en-US-GuyNeural")


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


def _is_gemini_unavailable(exc: Exception) -> bool:
    message = str(exc).lower()
    return "api key" in message or "gemini" in message


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


def _get_gemini_api_key() -> str | None:
    if "GEMINI_API_KEY" in os.environ:
        return os.environ.get("GEMINI_API_KEY")
    if API_CONFIG_PATH.exists():
        try:
            data = json.loads(API_CONFIG_PATH.read_text(encoding="utf-8"))
            return data.get("gemini_api_key")
        except Exception:
            return None
    return None


async def _gemini_audio_stream(text: str, on_chunk: Callable[[bytes], None]) -> None:
    api_key = _get_gemini_api_key()
    if not api_key:
        raise RuntimeError("Gemini API key is missing.")

    client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Charon"
                )
            )
        ),
    )

    async with client.aio.live.connect(model=GEMINI_TTS_MODEL, config=config) as session:
        await session.send_client_content(
            turns={"parts": [{"text": text}]},
            turn_complete=True,
        )

        async for response in session.receive():
            if response.data:
                on_chunk(response.data)
            if response.server_content and response.server_content.turn_complete:
                break


async def _edge_tts_stream(text: str, on_chunk: Callable[[bytes], None]) -> None:
    try:
        import edge_tts
    except Exception as exc:
        raise RuntimeError("edge-tts is not installed.") from exc

    communicator = edge_tts.Communicate(text, EDGE_TTS_VOICE)
    async for chunk in communicator.stream():
        if chunk.get("type") == "audio":
            on_chunk(chunk["data"])

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


class GeminiRelayVoiceAdapter(VoiceAdapter):
    """Gemini native audio first, then Edge TTS, then system TTS."""

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

        try:
            asyncio.run(_gemini_audio_stream(text, on_chunk))
            return
        except Exception as exc:
            if not (_is_rate_limit_error(exc) or _is_gemini_unavailable(exc)):
                raise

        try:
            asyncio.run(_edge_tts_stream(text, on_chunk))
            return
        except Exception:
            pass

        _system_tts(text)


_adapter_singleton: VoiceAdapter | None = None


def get_voice_adapter() -> VoiceAdapter:
    global _adapter_singleton
    if _adapter_singleton is None:
        _adapter_singleton = GeminiRelayVoiceAdapter()
    return _adapter_singleton
