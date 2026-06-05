## Why

The PyQt6 HUD is rich but tethered to the local display. There's no way to glance at Jarvis's status, read the live transcript, or monitor system health from another device or a secondary monitor without the full desktop GUI. A lightweight web dashboard provides an always-visible, read-only window into the assistant's state — perfect for secondary screens, mobile browsers, or embedding in other tools.

## What Changes

- Add a **FastAPI + WebSocket server** listening on `localhost:7070`
- Introduce a lightweight **event bus** (`DashboardEventBus`) that `JarvisLive` pushes state updates into — live transcript lines, current state, ReAct task status, system metrics
- Serve a **single-page HTML dashboard** from the FastAPI server, updated in real-time via WebSocket
- Dashboard shows 4 panels: **live conversation transcript**, **memory explorer** (key-value facts), **active ReAct task status**, and **system stats** (CPU, RAM, disk, battery)
- The existing **PyQt6 UI** (`JarvisUI`/`MainWindow`) remains **completely unchanged**
- All existing **`JarvisLive` interfaces** (`_execute_tool`, tool signatures, threading model, state machine) remain **unchanged**
- No breaking changes to any existing capability

## Capabilities

### New Capabilities
- `web-dashboard`: FastAPI-based read-only web dashboard at localhost:7070 with live WebSocket updates showing conversation transcript, memory explorer, active ReAct task status, and system health metrics

### Modified Capabilities
- *(none — no existing spec behavior changes)*

## Impact

- **New files**: `dashboard/server.py` (FastAPI app + WebSocket manager), `dashboard/templates/index.html` (dashboard SPA), `dashboard/event_bus.py` (DashboardEventBus)
- **Modified files**: `main.py` (wire up event bus, start dashboard thread; no interface changes to `JarvisLive`), `requirements.txt` (fastapi, uvicorn, websockets already present — no new dependencies)
- **Dependencies**: None new — `fastapi`, `uvicorn`, and `websockets` are already in `requirements.txt`
- **Threading**: Dashboard server runs in a daemon thread started by `main()`, alongside existing threads
