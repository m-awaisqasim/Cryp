## Why

Cryp's mic streams audio to Gemini Live 24/7 during a session, wasting bandwidth, API quota, and battery. Hotword detection with `openWakeWord` lets the assistant listen locally for "Hey Jarvis" and only activate the live session when invoked — enabling always-on presence without the constant resource drain.

## What Changes

- New `core/hotword_detector.py` — wraps openWakeWord to detect "Hey Jarvis" from mic audio
- New `core/sleep_manager.py` — sleep/wake state machine with configurable inactivity timeout
- Modify `JarvisLive` in `main.py` — add sleep mode that pauses `_listen_audio()` and the Gemini session when idle, resumes on wake word
- New config `HOTWORD_TIMEOUT` env var / config setting for idle seconds before sleep
- Add `openwakeword` to `requirements.txt`
- Add `core/` package `__init__.py` if not present

## Capabilities

### New Capabilities
- `hotword-detection`: Local wake word engine using openWakeWord. Listens on a slim audio stream, detects "Hey Jarvis", emits a wake event. Runs independently of the main Gemini session.
- `sleep-timeout`: Idle timeout manager. When the user stops speaking for N seconds (configurable), transitions JarvisLive to sleep mode. On wake word, re-establishes the Gemini session.

### Modified Capabilities
<!-- No existing specs are changing at the requirement level. -->

## Impact

- **Audio pipeline**: Mic stream is split — low-power openWakeWord inference runs continuously; full Gemini audio stream only during active sessions
- **JarvisLive**: Gains `sleeping` state, `wake()`/`sleep()` methods, modified `run()` loop with sleep/awake transitions
- **Dependencies**: +`openwakeword` (+ its ONNX Runtime dependency chain)
- **Config**: +`HOTWORD_TIMEOUT` (seconds, default 300)
- **UI**: May add new "SLEEPING" / "HOTWORD_ACTIVE" state visualization
