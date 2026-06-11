## Context

Cryp currently has zero situational awareness — it doesn't know what the user is doing, what's on their clipboard, or the system state. The `_build_config()` method assembles system prompt parts (time, memory, episodes, personality) but has no live context block. Phase 4 roadmap explicitly calls for this feature.

## Goals / Non-Goals

**Goals:**
- Inject a LIVE CONTEXT block into every Gemini session system instruction
- Include: active window title, clipboard preview (first 200 chars), battery status (percentage + charging), CPU usage %, RAM usage (used/total), current date/time
- Gather all data fresh on each `_build_config()` call (every session connect/reconnect)
- Work on Linux (primary), with fallbacks/stubs for Windows/macOS
- Zero impact on session reliability — failure to read any sensor silently degrades (omit that field) instead of crashing

**Non-Goals:**
- Real-time context streaming during a session — snapshot only at session start
- Persistent storage of context history
- GUI display of context data
- Cross-platform parity on first pass — Linux primary, others best-effort

## Decisions

1. **Single file `core/context_collector.py`** over inline helpers — keeps `_build_config()` clean, unit-testable, and easy to maintain/extend.
2. **`psutil` for CPU/RAM** — already common, avoids reinventing `/proc/stat` parsing. Add to `requirements.txt`.
3. **`pyperclip` for clipboard** — cross-platform clipboard access via a single call (`pyperclip.paste()`). Add to `requirements.txt`.
4. **`Xlib` / `python-xlib` for active window** on Linux — standard approach via `xprop -root _NET_ACTIVE_WINDOW` or python-xlib. Falls back to reading `/proc` or `os.environ` on other platforms.
5. **`/sys/class/power_supply/` for battery** — no extra dependency on Linux. Use `psutil.sensors_battery()` as cross-platform fallback.
6. **Fail-soft pattern** — each sensor function is a separate try/except returning `None` on failure. The `gather_live_context()` function filters out Nones and only includes available fields. No crash propagates to session start.
7. **Single synchronous function** `gather_live_context() -> str` — called inside `_build_config()` before the `parts` list is built. The result is prepended as the first `parts` element.

## Risks / Trade-offs

- [**Clipboard clears after copy**] → pyperclip reads current clipboard content; if user copies sensitive data, it will be sent to Gemini. Mitigation: limit preview to first 200 chars, and the context block is only sent at session start (not continuously).
- [**X11 dependency on Linux**] → If running under Wayland, `_NET_ACTIVE_WINDOW` via xprop may fail. Mitigation: add Wayland fallback using `ydotool` or `wlrctl` if available; otherwise omit the field.
- [**CPU/RAM sampling is a snapshot**] → A single `psutil.cpu_percent(interval=0.1)` may not reflect sustained load. Acceptable for a session-start snapshot.
- [**Extra latency at session start**] → All sensors are fast (<50ms total). If any sensor blocks (e.g., CPU sampling), use a short timeout. Not expected to be noticeable.
