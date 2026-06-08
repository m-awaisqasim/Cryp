## Context

Cryp currently runs 4 concurrent tasks in `JarvisLive._run()`: listen, send, receive, play. The `system-health-daemon` (Phase 2) already added a background monitoring task. The proactive intelligence feature extends this pattern — adding a new background engine that orchestrates briefing, pattern detection, anomaly detection, and suggestions. The engine must be a non-blocking async task that respects conversation state and never interrupts the user mid-speech.

Episodic memory (Phase 1) stores conversation summaries. Live context (Phase 4) provides active window, clipboard, and battery. Both are read-only inputs to the proactive engine. The engine writes detected patterns back into memory as procedural memory entries.

## Goals / Non-Goals

**Goals:**
- Deliver a spoken daily briefing on the first Jarvis startup of each calendar day
- Detect behavioral patterns across sessions by querying episodic memory
- Detect system anomalies (resource, timing, app behavior) by comparing live data with stored patterns
- Offer unsolicited help suggestions during natural conversation pauses (5+ seconds of silence)
- Respect conversation state: never speak while Jarvis is in an active tool call, mid-response, or user is speaking
- All proactive features must work offline (no external API calls for the core engine)

**Non-Goals:**
- No ML model training — patterns are rule-based (time-of-day, day-of-week, frequency analysis)
- No speech recognition during silence — pause detection uses existing audio stream silence
- No GUI changes — all proactive output uses existing `speak()` and `write_log()`
- No personalized learning of user preferences beyond what already exists in episodic memory
- No proactive actions that require confirmation (suggestions are spoken, not executed)

## Decisions

1. **One proactive engine task, not many**. A single `ProactiveEngine` async task owns all proactive features. It has internal timers and state machines for briefing, pattern scans, anomaly checks, and suggestions. This avoids race conditions between multiple proactive sources and keeps coordination simple. The engine reads from a shared `conversation_state` object (thread-safe) to know if the user is in conversation.

2. **Proactive output uses existing speech pipeline**. The engine writes to a `proactive_queue: asyncio.Queue` that `JarvisLive` drains during natural pauses. When `_receive_audio` detects a turn-end (Gemini `TurnComplete` or 5+ seconds of silence on the mic input), it checks the proactive queue and speaks any pending items. This guarantees non-interruption without modifying the core audio loop.

3. **Daily briefing persists last-briefing date**. A simple file `memory/last_briefing_date.txt` stores the last date a briefing was delivered. On engine startup, if today != last date, the briefing fires. No calendar introspection — the engine queries the existing `live-context` snapshot for the date.

4. **Pattern detection runs on a timer (hourly, debounced)**. Once per hour (configurable), the engine queries episodic memory for summaries from the last N days. It applies rule-based heuristics: time-based patterns (same app same time), frequency patterns (top 3 apps by day of week). Results are stored as procedural memory entries under `patterns/` namespace in memory_manager.

5. **Anomaly detection compares live vs. baseline**. The engine maintains a lightweight rolling baseline of system metrics (CPU, RAM, active app at each hour). An anomaly is a metric that deviates >2σ from the baseline for that hour. Results are logged and optionally spoken if the anomaly is significant (e.g., CPU at 95% when it's usually 20% at this hour).

6. **Contextual suggestions use if-then rules**. The engine maintains a small list of suggestion rules: "if active_window is terminal and time is morning → suggest running updates", "if clipboard contains a git conflict → suggest opening VS Code". Rules live in a config file `config/proactive_rules.json` for easy customization.

## Risks / Trade-offs

- **[Risk] Proactive speech is annoying** → Conservative defaults: briefing only once/day, patterns detected but only spoken if user has a pattern of ignoring them (learned from responses), suggestions capped at 1 per 30 minutes. All features toggleable via config.
- **[Risk] Pause detection is inaccurate** → The current 5-second silence heuristic is coarse. If false positives trigger mid-thought, we add a debounce window: only trigger suggestions after 5s silence AND no audio output for 3s. Fine-tune during testing.
- **[Risk] Pattern detection on large episodic memory is slow** → Pattern queries are limited to the last 7 days by default and use the existing vector search (chromadb). If the memory store grows large (>10k entries), add a time-bounded query parameter.
- **[Risk] Modified specs could conflict with existing implementation** → Delta specs are additive only (ADDED requirements). No existing spec requirements are modified — only extended. This ensures backward compatibility with the already-implemented Phase 1/2 code.
- **[Risk] Background engine task could drain battery** → Proactive engine is an async task that sleeps most of the time. CPU impact is negligible. Pattern detection runs hourly and is a lightweight query, not a batch ML job.
