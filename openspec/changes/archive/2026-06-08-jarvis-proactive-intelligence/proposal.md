## Why

Cryp (V2) has all the building blocks — episodic memory, live context, system health monitoring, and a ReAct agent — but Cryp is entirely reactive. It only responds to explicit commands. To truly become a CRYP-like assistant, it needs proactive intelligence: noticing patterns across sessions, offering timely suggestions, briefing the user at startup, and detecting anomalies without being asked.

## What Changes

- Add a **Proactive Engine** background task that decides when to speak unsolicited (startup, natural pauses, never during active conversation)
- Add **Daily Briefing** — Cryp greets the user at first startup of the day with context (time, weather, calendar, reminders, memory highlights, system health)
- Add **Pattern Detection** — Cryp analyzes episodic memory to find behavioral patterns (e.g., "You always open VS Code at 9am on weekdays") and stores them as procedural memory
- Add **Anomaly Detection** — Cryp detects deviations from normal system behavior (unusual resource spikes, forgotten processes, abnormal app launch times)
- Add **Contextual Suggestions** — Cryp proactively suggests actions based on current context (active window, time, day, recent patterns)
- All proactive speech must respect the **non-interruption rule** — never speak while the user is in an active conversation. Only speak at startup or during natural 5+ second pauses

## Capabilities

### New Capabilities
- `proactive-engine`: Core orchestration layer that decides WHEN to trigger proactive actions. Manages wake-up timeline, pause detection, and cooldown/debounce to prevent annoyance
- `daily-briefing`: Generates and delivers a spoken briefing at first daily startup. Combines time-aware greeting, weather, calendar events, reminders, recent memory updates, and system health snapshot
- `pattern-detection`: Analyzes episodic memory across sessions to identify recurring user behaviors. Stores detected patterns as procedural memory for later reference
- `anomaly-detection`: Monitors for deviations from normal patterns in system metrics, app launch timing, and session behavior. Triggers proactive alerts for unusual observations
- `contextual-suggestions`: Composes actionable suggestions based on current real-time context (active window, clipboard, time, day, past patterns) and presents them during natural pauses

### Modified Capabilities
- `episodic-memory`: Add query interfaces to retrieve behavioral patterns and cross-session summaries needed by the pattern detector
- `live-context`: Expand context snapshot to include session timestamps, app launch events, and daily aggregations needed by the proactive engine
- `system-health-daemon`: Expose alert history and current health snapshot to the proactive engine for anomaly cross-referencing and inclusion in daily briefings

## Impact

- **Code**: New `proactive/` directory with engine, briefing, pattern, anomaly, and suggestion modules. Modifications to `main.py` (_build_config and TaskGroup to launch engine). Minor additions to `memory/memory_manager.py` for pattern storage/query. Minor additions to `core/daemon.py` (system-health-daemon) for health snapshot API
- **Dependencies**: `sqlite3` (stdlib — already used? check), `json` (stdlib). No new external dependencies expected. Pattern detection uses existing episodic memory vector store (chromadb/faiss from Phase 1)
- **Configuration**: `core/prompt.txt` updated to inform Cryp of its proactive capabilities and when/how to be proactive. New config section for proactive engine (cooldown, pause threshold, briefing enabled/disabled)
- **Existing spec modifications**: `episodic-memory/spec.md`, `live-context/spec.md`, `system-health-daemon/spec.md` need delta requirements added
