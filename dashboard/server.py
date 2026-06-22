import asyncio
import json
import os
import sys
import threading
import time
from collections import deque
from pathlib import Path

try:
    import psutil
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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    _shutdown_cpu_updater()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:7070", "http://127.0.0.1:7070", "http://localhost:7073", "http://127.0.0.1:7073"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bus: DashboardEventBus | None = None
_ui_instance = None
_cryp_ws_clients: set = set()


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
    _cryp_ws_clients.add(websocket)
    if _ui_instance:
        _ui_instance.register_client(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "command":
                text = data.get("text", "").strip()
                if text == "__wake__":
                    if _ui_instance and _ui_instance.on_wake_request:
                        _ui_instance.on_wake_request()
                elif text == "__sleep__":
                    if _ui_instance and _ui_instance.on_sleep:
                        _ui_instance.on_sleep()
                elif text == "__shutdown__":
                    if _ui_instance and _ui_instance.on_shutdown:
                        _ui_instance.on_shutdown()
                elif text and _ui_instance:
                    _ui_instance.write_log(f"You: {text}")
                    if _ui_instance.on_text_command:
                        _ui_instance.on_text_command(text)

            elif msg_type == "mute_toggle":
                if _ui_instance:
                    _ui_instance.muted = not _ui_instance.muted

            elif msg_type == "shutdown":
                if _ui_instance and _ui_instance.on_shutdown:
                    _ui_instance.on_shutdown()

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        _cryp_ws_clients.discard(websocket)
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
        return FileResponse(index)
    return {"status": "React build not found. Run: npm run build"}


@app.get("/api/memory")
async def get_memory():
    try:
        from memory.memory_manager import load_memory, load_recent_episodes
        mem = load_memory()
        episodes = load_recent_episodes(n=20)
        categories = {}
        for cat, data in mem.items():
            if isinstance(data, dict):
                categories[cat] = len(data)
            elif isinstance(data, list):
                categories[cat] = len(data)
            else:
                categories[cat] = 1
        recent = [
            {
                "summary": ep.get("summary", ""),
                "timestamp": ep.get("timestamp", ""),
                "tools_used": ep.get("tools_used", [])[:5],
            }
            for ep in episodes[:5]
            if ep.get("summary") and "Session on" not in ep.get("summary", "")
        ]
        return {
            "success": True,
            "categories": categories,
            "total_facts": sum(categories.values()),
            "episode_count": len(episodes),
            "recent_episodes": recent,
            "raw": mem,
        }
    except Exception as e:
        log.warning("memory_api_error", error=str(e))
        return {
            "success": False,
            "categories": {},
            "total_facts": 0,
            "episode_count": 0,
            "recent_episodes": [],
            "raw": {},
        }


@app.post("/api/memory")
async def post_memory(body: dict):
    key = body.get("key", "").strip()
    value = body.get("value", "")
    if not key:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"success": False, "error": "key required"})
    try:
        from memory.memory_manager import update_memory, load_memory
        update_memory({"notes": {key: {"value": value}}})
        return {"success": True, "data": load_memory()}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@app.get("/api/processes")
async def get_processes():
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                procs.append({
                    "name": (info["name"] or "unknown")[:30],
                    "cpu": round(info["cpu_percent"] or 0, 1),
                    "mem": round(info["memory_percent"] or 0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x["cpu"], reverse=True)
        return {"success": True, "processes": procs[:3]}
    except Exception as e:
        log.warning("processes_api_error", error=str(e))
        return {"success": False, "processes": []}


@app.get("/api/stats")
async def get_stats():
    global _last_net, _cached_cpu
    import time as _time
    battery = psutil.sensors_battery()
    net = psutil.net_io_counters()
    net_speed = (net.bytes_recv - _last_net) / 1024 / 1024
    _last_net = net.bytes_recv
    return {
        "cpu": _cached_cpu,
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "battery_percent": battery.percent if battery else None,
        "battery_plugged": battery.power_plugged if battery else False,
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
    dest = upload_dir / Path(file.filename).name
    with open(dest, "wb") as f:
        f.write(await file.read())
    if _ui_instance:
        _ui_instance.current_file = str(dest.absolute())
    return {"path": str(dest), "name": file.filename}


def cleanup_uploads():
    upload_dir = Path("uploads")
    if not upload_dir.exists():
        return
    for f in upload_dir.iterdir():
        try:
            if f.is_file():
                f.unlink()
        except Exception:
            pass
    try:
        upload_dir.rmdir()
    except Exception:
        pass


LOG_PATH = BASE_DIR / "logs" / "cryp.log"
_last_net = psutil.net_io_counters().bytes_recv
_cached_cpu = 0.0
_cpu_stop = threading.Event()

def _cpu_updater():
    global _cached_cpu
    while not _cpu_stop.is_set():
        _cached_cpu = psutil.cpu_percent(interval=0.1)
        _cpu_stop.wait(2.0)

_cpu_thread = threading.Thread(target=_cpu_updater, daemon=True)
_cpu_thread.start()

def _shutdown_cpu_updater():
    _cpu_stop.set()
    _cpu_thread.join(timeout=3.0)


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


@app.get("/api/trading/summary")
async def trading_summary():
    from actions.trading.trade_journal import get_dashboard_summary
    try:
        return get_dashboard_summary()
    except Exception as e:
        log.warning("trading_summary_error", error=str(e))
        return {"error": str(e), "open_positions": [], "recent_closed": [],
                "equity_curve": [], "stats": {}, "exposure": {}}


@app.post("/api/trading/import")
async def trading_import(file: UploadFile = File(...)):
    from actions.trading.trade_journal import import_trades
    import tempfile, os
    from pathlib import Path
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        return import_trades(tmp_path)
    finally:
        os.unlink(tmp_path)


@app.get("/api/trading/import/template")
async def trading_import_template():
    from fastapi.responses import Response
    csv_content = (
        "symbol,side,entry_price,stop_loss,take_profit,size,setup,reasoning,fee,exit_price,exit_fee,opened_at,closed_at\n"
        "BTC,long,95000,92000,105000,0.1,breakout,Broke above resistance,0,97000,0,2026-05-01,2026-05-10\n"
        "ETH,short,3200,3300,,0.5,mean-reversion,Overbought on RSI,0,,,2026-06-01,\n"
    )
    return Response(content=csv_content, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=trade_import_template.csv"})


@app.get("/api/trading/export")
async def trading_export():
    try:
        from actions.trading.trade_journal import trade_journal
        from actions.trading.market_data import _base_dir
        from fastapi.responses import FileResponse
        trade_journal({"action": "export"})
        csv_path = _base_dir() / "memory" / "trades_export.csv"
        return FileResponse(str(csv_path), filename="trades_export.csv", media_type="text/csv")
    except Exception as e:
        log.warning("trading_export_error", error=str(e))
        return {"error": str(e)}


from pydantic import BaseModel
from typing import Optional


class TradeLogRequest(BaseModel):
    symbol: str
    side: str
    entry_price: float
    size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    setup: Optional[str] = None
    tags: Optional[str] = None
    reasoning: Optional[str] = None
    fee: Optional[float] = 0.0
    notes: Optional[str] = None


class TradeCloseRequest(BaseModel):
    trade_id: str
    exit_price: float
    size: Optional[float] = None
    fee: Optional[float] = 0.0
    notes: Optional[str] = None


class TradeEditRequest(BaseModel):
    trade_id: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    setup: Optional[str] = None
    tags: Optional[str] = None
    reasoning: Optional[str] = None
    notes: Optional[str] = None


@app.get("/api/trading/prices")
async def trading_prices():
    from actions.trading.market_data import get_prices
    try:
        return get_prices(("bitcoin", "ethereum"))
    except Exception as e:
        log.warning("trading_prices_error", error=str(e))
        return {"error": str(e)}


@app.post("/api/trading/log")
async def trading_log(req: TradeLogRequest):
    from actions.trading.trade_journal import trade_journal
    try:
        result = trade_journal({
            "action": "log",
            "symbol": req.symbol,
            "side": req.side,
            "entry_price": req.entry_price,
            "size": req.size,
            "stop_loss": req.stop_loss,
            "take_profit": req.take_profit,
            "setup": req.setup,
            "tags": req.tags,
            "reasoning": req.reasoning,
            "fee": req.fee,
            "notes": req.notes,
        })
        rejection_phrases = ("I need", "For a", "Entry price", "must be")
        if any(result.startswith(p) for p in rejection_phrases):
            return {"success": False, "message": result}
        return {"success": True, "message": result}
    except Exception as e:
        log.warning("trading_log_error", error=str(e))
        return {"success": False, "message": str(e)}


@app.post("/api/trading/close")
async def trading_close(req: TradeCloseRequest):
    from actions.trading.trade_journal import trade_journal, _load
    try:
        items = _load()
        trade = next((it for it in items if it["id"] == req.trade_id), None)
        if not trade:
            return {"success": False, "message": "Trade not found."}
        result = trade_journal({
            "action": "close",
            "symbol": trade["symbol"],
            "exit_price": req.exit_price,
            "size": req.size,
            "fee": req.fee,
            "notes": req.notes,
        })
        if "Couldn't" in result or "No open" in result:
            return {"success": False, "message": result}
        return {"success": True, "message": result}
    except Exception as e:
        log.warning("trading_close_error", error=str(e))
        return {"success": False, "message": str(e)}


@app.post("/api/trading/edit")
async def trading_edit(req: TradeEditRequest):
    from actions.trading.trade_journal import trade_journal
    try:
        result = trade_journal({
            "action": "edit",
            "id": req.trade_id,
            "stop_loss": req.stop_loss,
            "take_profit": req.take_profit,
            "setup": req.setup,
            "tags": req.tags,
            "reasoning": req.reasoning,
            "notes": req.notes,
        })
        if "Can't" in result or "Couldn't" in result:
            return {"success": False, "message": result}
        return {"success": True, "message": result}
    except Exception as e:
        log.warning("trading_edit_error", error=str(e))
        return {"success": False, "message": str(e)}


def start_dashboard(event_bus: DashboardEventBus):
    global _bus
    if FastAPI is None or uvicorn is None:
        log.info("dashboard_unavailable")
        return
    _bus = event_bus
    port = int(os.getenv("DASHBOARD_PORT", "7073"))
    try:
        t = threading.Thread(
            target=uvicorn.run,
            args=(app,),
            kwargs={"host": "127.0.0.1", "port": port, "log_level": "warning"},
            daemon=True,
        )
        t.start()
        log.info("dashboard_listening", port=port)
    except Exception:
        log.warning("dashboard_start_failed", port=port)