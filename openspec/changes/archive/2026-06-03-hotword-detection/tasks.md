## 1. Setup & Dependencies

- [x] 1.1 Add `openwakeword` to `requirements.txt`
- [x] 1.2 `core/__init__.py` already existed
- [x] 1.3 Create `core/hotword.py` — openWakeWord wrapper module (named `hotword.py` not `hotword_detector.py`)
- [x] 1.4 Create `core/wake_config.py` — config dataclass (replaces separate sleep_manager.py, config is simpler)
- [x] 1.5 Define `WakeConfig` with env var / config fallback in `core/wake_config.py`

## 2. Hotword Detector (`core/hotword.py`)

- [x] 2.1 Implement `HotwordDetector` class with `__init__`, `start()`, `stop()`, `is_running`
- [x] 2.2 Open dedicated `sounddevice.InputStream` (16kHz, blocksize=1280) for hotword inference
- [x] 2.3 Initialize openWakeWord with `Model(wakeword_models=["hey_jarvis"])` and route audio chunks to inference
- [x] 2.4 Implement threshold-based detection — emit wake event when confidence > 0.5
- [x] 2.5 Callback-based wake signaling (simpler than asyncio.Event for thread → sync usage)
- [x] 2.6 Handle import/init failure gracefully — fall back to always-on mode (log warning, no crash)
- [x] 2.7 Add `stop()` method to cleanly close hotword stream and thread

## 3. Configuration (`core/wake_config.py`)

- [x] 3.1 `WakeConfig` dataclass with `enabled`, `threshold`, `wake_words`, `silence_timeout` fields
- [x] 3.2 Read from env vars `JARVIS_HOTWORD`, `JARVIS_HOTWORD_THRESHOLD`, `JARVIS_SILENCE_TIMEOUT`
- [x] 3.3 Default `wake_words = ["hey jarvis"]` in `__post_init__`
- [x] 3.4 `JARVIS_HOTWORD=0` env var disables hotword (restores always-on behavior)

## 4. JarvisLive Integration (`main.py`)

- [x] 4.1 Import `WakeConfig` from `core.wake_config`
- [x] 4.2 Add `_wake_config`, `_is_awake`, `_silence_timer`, `_hotword` fields to `JarvisLive.__init__`
- [x] 4.3 Start `HotwordDetector` in `run()` before the main loop if enabled
- [x] 4.4 Wake word starts session, silence timeout triggers sleep
- [x] 4.5 Cleanup hotword detector on shutdown in `main()` finally block
- [x] 4.6 `_on_wake_word_detected()` — sets `_is_awake`, starts silence timer
- [x] 4.7 `_go_to_sleep()` — clears `_is_awake`, sets UI state to SLEEPING
- [x] 4.8 `_listen_audio()` — guard: skip sending audio if hotword enabled and not awake
- [x] 4.9 UI state: `set_state("SLEEPING")` when sleeping, `"LISTENING"` on wake

## 5. Verification

- [x] 5.1 Unit tests in `tests/test_hotword.py` — `WakeConfig` defaults, env var overrides
- [x] 5.2 Unit tests — `HotwordDetector.start()` launches daemon thread
- [x] 5.3 Unit tests — `HotwordDetector.stop()` sets stop event
- [x] 5.4 Unit tests — `is_running()` returns correct state
- [x] 5.5 Unit tests — callback called above threshold, not called below threshold
- [x] 5.6 Manual: `JARVIS_HOTWORD=0` disables hotword, restores always-on
- [x] 5.7 `python3 -m py_compile` passes for core/hotword.py, core/wake_config.py, main.py
