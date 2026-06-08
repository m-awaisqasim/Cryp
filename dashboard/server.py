import asyncio
import json
import os
import sys
import threading
from collections import deque
from pathlib import Path

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
    from fastapi.responses import HTMLResponse, FileResponse
    import uvicorn
except ImportError:
    FastAPI = None
    uvicorn = None

from dashboard.event_bus import DashboardEventBus
from core.logger import get_logger

log = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_PATH = BASE_DIR / "memory" / "long_term.json"
TEMPLATE_PATH = BASE_DIR / "dashboard" / "templates" / "index.html"

app = FastAPI()
_bus: DashboardEventBus | None = None


def _load_memory():
    try:
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


@app.get("/")
async def get_index():
    try:
        html = TEMPLATE_PATH.read_text(encoding="utf-8")
    except Exception:
        html = "<html><body><h1>Dashboard not found</h1></body></html>"
    return HTMLResponse(html)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    sid, queue = _bus.subscribe()
    try:
        memory = _load_memory()
        await ws.send_text(json.dumps({"type": "memory", "data": memory}))
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                await ws.send_text(json.dumps(event))
            except asyncio.TimeoutError:
                try:
                    _ = await ws.receive_text()
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        _bus.unsubscribe(sid)


LOG_PATH = BASE_DIR / "logs" / "cryp.log"


@app.get("/api/logs")
async def get_logs(lines: int = Query(100, ge=1, le=1000)):
    try:
        if not LOG_PATH.exists():
            return {"lines": [], "total": 0}
        text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
        all_lines = text.splitlines()
        last_n = all_lines[-lines:] if lines < len(all_lines) else all_lines
        return {"lines": last_n, "total": len(all_lines)}
    except Exception:
        return {"lines": [], "total": 0}


@app.get("/api/logs/download")
async def download_logs():
    if LOG_PATH.exists():
        return FileResponse(str(LOG_PATH), filename="cryp.log")
    return HTMLResponse("No log file available", status_code=404)


def start_dashboard(event_bus: DashboardEventBus):
    global _bus
    if FastAPI is None or uvicorn is None:
        log.info("dashboard_unavailable")
        return
    _bus = event_bus
    port = int(os.getenv("DASHBOARD_PORT", "7070"))
    for attempt in range(3):
        try:
            t = threading.Thread(
                target=uvicorn.run,
                args=(app,),
                kwargs={"host": "127.0.0.1", "port": port + attempt, "log_level": "warning"},
                daemon=True,
            )
            t.start()
            log.info("dashboard_listening", port=port + attempt)
            return
        except Exception:
            continue
    log.warning("dashboard_start_failed")
