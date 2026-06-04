## 1. Core Daemon Module

- [x] 1.1 Create `core/daemon.py` with `SystemHealthDaemon` class
- [x] 1.2 Implement `__init__` with config loading from env vars (check interval, CPU/RAM/disk/battery thresholds, debounce seconds)
- [x] 1.3 Implement `run()` async coroutine with `asyncio.sleep(interval)` loop and `CancelledError` handling
- [x] 1.4 Implement CPU monitoring: `psutil.cpu_percent(interval=0)` with 2-consecutive-check smoothing and threshold comparison
- [x] 1.5 Implement RAM monitoring: `psutil.virtual_memory().percent` with smoothing and threshold comparison
- [x] 1.6 Implement disk monitoring: `psutil.disk_usage('/').percent` with smoothing and threshold comparison
- [x] 1.7 Implement battery monitoring: `psutil.sensors_battery()` with plugged-in guard and threshold comparison
- [x] 1.8 Implement per-metric debounce tracking using timestamps (skip alert if within `DEBOUNCE_SECONDS`)
- [x] 1.9 Implement alert dispatch: calls `speak(text)` callback for voice and `write_log(text)` callback for UI transcript
- [x] 1.10 Gracefully handle missing battery (desktop), no active session (`speak` fails), and `psutil` import errors

## 2. Wiring into JarvisLive

- [x] 2.1 Import `SystemHealthDaemon` in `main.py`
- [x] 2.2 Add `self._health_daemon = SystemHealthDaemon(speak=self.speak, write_log=self.ui.write_log)` in `JarvisLive.__init__`
- [x] 2.3 Add `tg.create_task(self._health_daemon.run())` alongside the other 5 tasks in `JarvisLive.run()`
- [x] 2.4 Verify daemon starts/stops cleanly on session connect/disconnect/reconnect without blocking voice or tools

## 3. Verification

- [x] 3.1 Run `python main.py` and confirm no import errors
- [x] 3.2 Confirm daemon task runs without breaking voice session (speak/listen/play still work)
- [x] 3.3 Temporarily lower `HEALTH_CPU_THRESHOLD=5` and confirm Jarvis speaks the alert
- [x] 3.4 Confirm debounce works: repeated high CPU does not re-trigger within cooldown
- [x] 3.5 Confirm daemon survives session reconnect without errors
- [x] 3.6 Confirm desktop without battery sees no battery errors (graceful skip)
