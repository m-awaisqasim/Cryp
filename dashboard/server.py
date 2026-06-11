import asyncio
import json
import os
import sys
import threading
from collections import deque
from pathlib import Path

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, UploadFile, File
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    FastAPI = None
    uvicorn = None

from dashboard.event_bus import DashboardEventBus
from core.logger import get_logger

log = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_PATH = BASE_DIR / "memory" / "long_term.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bus: DashboardEventBus | None = None
_ui_instance = None


def set_ui(ui):
    global _ui_instance
    _ui_instance = ui


def _load_memory():
    try:
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


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


@app.websocket("/ws/cryp")
async def cryp_ws(websocket: WebSocket):
    await websocket.accept()
    if _ui_instance:
        _ui_instance.register_client(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "command":
                text = data.get("text", "").strip()
                if text and _ui_instance:
                    if _ui_instance.on_text_command:
                        _ui_instance.on_text_command(text)

            elif msg_type == "mute_toggle":
                if _ui_instance:
                    _ui_instance.muted = not _ui_instance.muted

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        if _ui_instance:
            _ui_instance.unregister_client(websocket)


FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets"
    )


@app.get("/")
async def serve_react():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        from fastapi.responses import FileResponse
        return FileResponse(index)
    return {"status": "React build not found. Run: npm run build"}


@app.get("/api/stats")
async def get_stats():
    import psutil
    import time as _time
    battery = psutil.sensors_battery()
    net = psutil.net_io_counters()
    net_speed = (net.bytes_recv - getattr(get_stats, "_last_net", net.bytes_recv)) / 1024 / 1024
    get_stats._last_net = net.bytes_recv
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "battery_percent": battery.percent if battery else None,
        "battery_plugged": battery.power_plugged if battery else None,
        "net": max(0, net_speed),
        "gpu": -1,
        "tmp": -1,
        "uptime": _time.time() - psutil.boot_time(),
        "procCount": len(psutil.pids()),
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    dest = upload_dir / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())
    if _ui_instance:
        _ui_instance.current_file = str(dest)
    return {"path": str(dest), "name": file.filename}


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