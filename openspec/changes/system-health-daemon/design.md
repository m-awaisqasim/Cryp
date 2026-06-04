## Context

Cryp already displays real-time system metrics (CPU, memory, network, GPU, temperature) in the PyQt6 HUD via `_SysMetrics` in `ui.py`. However, this is purely passive — the user must look at the display to notice problems. There is no proactive voice alerting.

The codebase uses `psutil` extensively for metric collection (already in `requirements.txt`). The async architecture uses `asyncio.TaskGroup` with 5 concurrent tasks inside `JarvisLive.run()`. Voice output is handled through `JarvisLive.speak()`, which sends text as a client content turn through the Gemini Live session, and the AI speaks the response via the Charon voice.

The Phase 2 roadmap in `openspec/context.md` already lists "Background daemon — core/daemon.py monitoring battery, calendar, system events" as a planned goal.

## Goals / Non-Goals

**Goals:**
- Create a non-blocking async background task that monitors CPU, RAM, disk, and battery at a configurable interval
- Speak voice alerts when thresholds are exceeded (battery low, CPU high, RAM high, disk full)
- Debounce alerts to avoid repeated interruptions (cooldown per metric)
- Wire into `JarvisLive.run()` as a 6th `tg.create_task()` inside the existing `TaskGroup`
- Handle clean cancellation when the session disconnects/reconnects
- Log alert events to the UI transcript via `write_log()`
- Make all thresholds configurable with sensible defaults

**Non-Goals:**
- Not modifying any existing tools or tool declarations
- Not adding UI metrics display (already exists in `_SysMetrics`)
- Not monitoring network, GPU, or temperature (those are UI-only for now)
- Not persisting alert history to disk
- Not adding calendar/event monitoring (future work)
- Not creating a standalone CLI or systemd service

## Decisions

1. **New `core/daemon.py` module** — keeps the daemon logic separate from `main.py`. The class `SystemHealthDaemon` is instantiated by `JarvisLive` and its `run()` method is passed as a task to `TaskGroup`. This keeps `main.py` surgical (a 3-line addition: import, init, create_task).

2. **Threshold config as a plain dict with env overrides** — avoids adding a YAML dependency. Defaults hardcoded in the class, each overridable via environment variable (e.g., `HEALTH_CPU_THRESHOLD=90`, `HEALTH_CHECK_INTERVAL=30`). Keeps the optional `config/health_daemon.yaml` as a potential future enhancement.

3. **Async monitoring loop using `asyncio.sleep()`** — the daemon is a true async coroutine, not a thread. It `await asyncio.sleep(interval)` between checks so it never blocks the event loop. Each metric check uses `psutil` calls that return near-instantly (interval=0 for cpu_percent).

4. **Per-metric debounce cooldown** — after an alert fires for a given metric, the same metric won't alert again for `DEBOUNCE_SECONDS` (default 300s / 5 min). This prevents Jarvis from repeatedly nagging about the same high CPU condition.

5. **Battery alert only when discharging** — uses `psutil.sensors_battery()` and only alerts on low percent when `power_plugged` is `False`. When plugged in, no alert is raised even if percent is low (charging is expected).

6. **Calling `speak()` for voice + `write_log()` for UI** — the daemon receives a `speak` callback function and a `write_log` callback. It uses `speak()` to proactively alert via voice and `write_log()` to record the event in the UI transcript. Both are thread-safe (`speak()` uses `run_coroutine_threadsafe` internally; `write_log()` is a synchronous UI call).

7. **No new Python dependencies** — `psutil` is already in `requirements.txt` and used by `ui.py`. `asyncio` is stdlib.

## Risks / Trade-offs

- **Alert fatigue** → mitigated by per-metric debounce cooldown (5 min default)
- **speak() during active conversation** → acceptable; Jarvis can interrupt with a brief alert. The daemon produces short, single-sentence alerts (~5 words) that don't derail conversation.
- **False positives during short spikes** → mitigated by checking that the metric exceeds threshold for 2 consecutive samples before alerting (smoothing)
- **psutil.sensors_battery() returns None on desktops without battery** → handled gracefully — if no battery detected, silently skip battery checks
- **speak() requires an active session** → the daemon catches `AttributeError`/`RuntimeError` if `speak` is called when no session is connected; it falls back to `write_log` only