## Context

Currently `JarvisLive._listen_audio()` opens a `sounddevice.InputStream` that captures 16kHz PCM from the mic and streams every chunk into the Gemini Live API session via `out_queue`. The session stays connected indefinitely — there is no silence timeout or sleep mode. This means:

- Continuous API billing (Gemini Live charges per audio second)
- Network bandwidth always consumed
- No privacy — mic is always "hot" to Google's servers
- Battery drain on laptops

The goal is to insert a local wake word layer so the mic only transmits to Gemini when the user explicitly invokes "Hey Jarvis".

## Goals / Non-Goals

**Goals:**
- Detect "Hey Jarvis" locally via openWakeWord before starting a Gemini session
- Transition `JarvisLive` between SLEEPING and ACTIVE states
- Configurable inactivity timeout (default 300s) to auto-sleep
- Re-establish Gemini session on wake word after sleep
- Keep hotword inference running on a separate low-power thread
- Integrate with existing `_listen_audio()` / `_play_audio()` pipeline with minimal disruption

**Non-Goals:**
- Custom wake word training or multiple wake words
- Voice activity detection (VAD) for endpointing — Gemini handles turn-taking
- Offline voice commands (wake word only triggers online session)
- Support for non-English wake words
- Hotword detection during an active session (Gemini handles mic while live)

## Decisions

### 1. openWakeWord over alternatives
- **openWakeWord**: Free, MIT license, ~50MB ONNX model, ~5% CPU on modern laptops, pre-built "hey jarvis" model available. No cloud dependency.
- **Porcupine (Picovoice)**: Excellent accuracy but proprietary, requires API key for "Hey Jarvis" (not in free tier), adds vendor lock-in.
- **Vosk**: Full speech-to-text is overkill — we only need a single wake word, not a full ASR pipeline.
- **Decision**: Use openWakeWord with the built-in `"hey jarvis"` model (`hey_jarvis_v0.1.tflite`, loaded via `wakeword_models=["hey jarvis"]`). Runs inference on 16kHz mono chunks matching existing `SEND_SAMPLE_RATE`.

### 2. Hotword thread vs asyncio task
- The hotword detector must process every audio chunk in real-time without gaps. If it runs inside the async `_listen_audio()` task, a slow Gemini API send could delay inference.
- **Decision**: Run openWakeWord inference on a **dedicated daemon thread** that reads from its own `sounddevice.InputStream`. When detection fires, it sets an `asyncio.Event` that the main loop awaits. This decouples hotword latency from API jitter.

### 3. Sleep/wake state machine
- Three states: `SLEEPING` (only hotword thread alive), `ACTIVE` (full Gemini session running), `TRIGGERED` (wake word heard, session starting).
- **Decision**: In `SLEEPING` state, `JarvisLive.run()` tears down the Gemini session (closes the `async with` block) but keeps the hotword thread. On wake event, it reconnects.
- In `ACTIVE` state, a watchdog task monitors the last user interaction timestamp. When `HOTWORD_TIMEOUT` seconds pass with no input or output, it initiates graceful sleep.

### 4. Audio pipeline split
- **Decision**: Two separate `sounddevice.InputStream` instances:
  1. **Hotword stream**: 16kHz, blocksize=1280 (80ms), routed to `openWakeWord` inference thread. Always open.
  2. **Session stream**: 16kHz, blocksize=1024, routed to `out_queue` → Gemini. Only open during ACTIVE state.
- Alternative (single stream + tee) was rejected because closing/reopening the stream on sleep would create audio gaps in the hotword detector.

### 5. Configuration
- **Decision**: `HOTWORD_TIMEOUT` environment variable with default 300 seconds. Read at startup, overridable in `config/api_keys.json` under a `hotword_timeout` key.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| openWakeWord false positives wake Jarvis at midnight | Set `HOTWORD_TIMEOUT` high (300s default). Consider a "double-tap" if false positives prove common. |
| Two mic streams may conflict on some ALSA/PulseAudio configs | Use `sounddevice` with explicit device ID (same as current). Test on Ubuntu 26.04 + PipeWire. Fallback: reopen single stream on error. |
| ONNX Runtime adds ~80MB to install size | Acceptable. openWakeWord is optional — if import fails, fall back to always-on legacy mode. |
| Hotword thread misses chunks during high CPU | openWakeWord inference is ~5ms per 80ms frame. Thread priority not adjusted unless needed. |
