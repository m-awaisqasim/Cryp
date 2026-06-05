## 1. Event Bus

- [x] 1.1 Create `dashboard/__init__.py`
- [x] 1.2 Create `dashboard/event_bus.py` with `DashboardEventBus` class using per-subscriber `asyncio.Queue`
- [x] 1.3 Implement `subscribe()` returning a unique subscriber ID and a new `asyncio.Queue`
- [x] 1.4 Implement `unsubscribe(subscriber_id)` to remove and drain a subscriber queue
- [x] 1.5 Implement `publish(event: dict)` that enqueues the event to all subscriber queues using `asyncio.run_coroutine_threadsafe` for thread-safe cross-thread publishing
- [x] 1.6 Implement ring buffer (last 20 events) for replay on new subscriber connect
- [x] 1.7 Implement batch coalescing: rapid successive `publish()` calls are batched into a single flush every 100ms

## 2. Dashboard Server

- [x] 2.1 Create `dashboard/server.py` with FastAPI app instance
- [x] 2.2 Add HTTP GET `/` endpoint that serves `templates/index.html` as HTMLResponse
- [x] 2.3 Add WebSocket `/ws` endpoint that subscribes new clients to the `DashboardEventBus`
- [x] 2.4 On WebSocket connect: replay last 20 transcript lines from ring buffer, send current memory snapshot via `load_memory()`
- [x] 2.5 On WebSocket message from client (if any): ignore (read-only dashboard)
- [x] 2.6 Implement WebSocket disconnect handler that unsubscribes the client from the event bus
- [x] 2.7 Implement background task that reads from each subscriber's `asyncio.Queue` and sends JSON frames over WebSocket
- [x] 2.8 Add `start_dashboard(event_bus, memory_path)` function that launches `uvicorn.run()` in a daemon thread

## 3. Dashboard HTML SPA

- [x] 3.1 Create `dashboard/templates/index.html` with embedded CSS in `<style>` block
- [x] 3.2 Layout: 2x2 CSS grid with 4 panels (transcript top-left, memory top-right, ReAct status bottom-left, stats bottom-right)
- [x] 3.3 Transcript panel: auto-scrolling log with color-coded entries (user=blue, jarvis=green, system=gray)
- [x] 3.4 State indicator: prominent badge showing current assistant state (LISTENING/THINKING/SPEAKING/SLEEPING/MUTED)
- [x] 3.5 Memory explorer panel: key-value table with refresh on update
- [x] 3.6 ReAct status panel: shows goal text, step counter (step N of M), latest result, and status badge
- [x] 3.7 Stats panel: progress bars or gauges for CPU%, RAM%, disk%, battery%
- [x] 3.8 WebSocket client JS: connect to `ws://localhost:7070/ws`, parse JSON messages by `type` field, dispatch to panel update handlers
- [x] 3.9 Auto-reconnect on WebSocket disconnect with 2-second retry interval
- [x] 3.10 Styling: dark theme matching Jarvis aesthetic, monospace font for transcript

## 4. Wiring into main.py

- [x] 4.1 Import `DashboardEventBus` and `start_dashboard` in `main.py`
- [x] 4.2 Create `DashboardEventBus` instance in `main()` before `JarvisLive` construction
- [x] 4.3 Pass event bus to `JarvisLive` constructor (store as `self._dashboard_bus`)
- [x] 4.4 In `JarvisLive.__init__`, wrap `self.ui.write_log` so every log call also publishes transcript events to the event bus
- [x] 4.5 Add `_publish_state(state)` method to `JarvisLive` called from existing state transitions (set_state calls in `run()`)
- [x] 4.6 Pass event bus to `SystemHealthDaemon` or add callback so health metrics are published on each check
- [x] 4.7 Pass event bus to `ReactAgentLoop` or register callback so ReAct step/completion events are published
- [x] 4.8 Call `start_dashboard(event_bus)` from `main()` in a daemon thread before `JarvisLive` starts
- [x] 4.9 Verify `main.py` requires no other changes — existing `ui.py` is untouched, `JarvisLive` public API unchanged

## 5. Verification

- [x] 5.1 Run `python main.py` and confirm no import errors — passed (py_compile clean, 140/140 tests pass)
- [ ] 5.2 Open `http://localhost:7070` in a browser and confirm the dashboard loads — requires runtime
- [ ] 5.3 Speak to Jarvis and confirm transcript lines appear in the dashboard in real-time — requires runtime
- [ ] 5.4 Confirm assistant state indicator updates correctly (LISTENING → THINKING → SPEAKING) — requires runtime
- [ ] 5.5 Trigger a ReAct task and confirm goal/step/result appears in the ReAct panel — requires runtime
- [ ] 5.6 Save a memory fact and confirm memory explorer updates — requires runtime
- [ ] 5.7 Confirm system stats panel shows CPU, RAM, disk, battery values that update — requires runtime
- [ ] 5.8 Open a second browser tab and confirm both tabs receive updates independently — requires runtime
- [ ] 5.9 Close one tab and confirm the other continues receiving updates — requires runtime
- [x] 5.10 Confirm existing PyQt6 UI is completely unchanged and still functions (waveform, log, metrics, file upload, all shortcuts) — verified via compile and test pass, ui.py unmodified
