from __future__ import annotations

import asyncio
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

import websockets

WEB_ROOT = Path(__file__).resolve().parent / "web"
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8766
WS_HOST = "127.0.0.1"
WS_PORT = 8765


def _start_http_server() -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=str(WEB_ROOT))
    server = ThreadingHTTPServer((HTTP_HOST, HTTP_PORT), handler)
    server.serve_forever()


async def _ws_handler(websocket, on_text: Callable[[str], None]) -> None:
    async for message in websocket:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            continue
        text = (payload.get("text") or "").strip()
        if text:
            on_text(text)


def start_stt_server(on_text: Callable[[str], None]) -> None:
    """Start a local Web Speech API page and websocket receiver."""
    if not WEB_ROOT.exists():
        WEB_ROOT.mkdir(parents=True, exist_ok=True)

    http_thread = threading.Thread(target=_start_http_server, daemon=True)
    http_thread.start()

    def _run_ws() -> None:
        async def _main() -> None:
            async with websockets.serve(
                lambda ws: _ws_handler(ws, on_text),
                WS_HOST,
                WS_PORT,
            ):
                await asyncio.Future()

        asyncio.run(_main())

    ws_thread = threading.Thread(target=_run_ws, daemon=True)
    ws_thread.start()
