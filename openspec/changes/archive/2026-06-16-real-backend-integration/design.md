## Context

The Figma NEXUS AI dashboard was integrated in the prior change with WebSocket state/transcript hooks and stats polling, but five components still use hardcoded or simulated data:

| Component | Current behavior | Desired behavior |
|---|---|---|
| MemoryPanel | Hardcoded mock items | Fetch from `/api/memory`, show real key-value pairs |
| SystemMonitor process list | Random fake processes | Fetch from `/api/processes` (real psutil) |
| VoiceBar waveform | CSS keyframe animation | Web Audio API AnalyserNode reading |
| AppDock | Stub toast notifications | Launch real tools via WebSocket `sendCommand()` |
| All hooks | Plain `.js` files | TypeScript `.ts` with proper types |

Backend (`dashboard/server.py`) has WebSocket push for state/transcript/memory/stats but no REST endpoints. The `memory_manager` and `psutil` libraries are already available.

## Goals / Non-Goals

**Goals:**
- Replace all mock/hardcoded data in MemoryPanel, SystemMonitor (processes), VoiceBar, AppDock with real backend data or browser-native APIs
- Add REST endpoints to `server.py` for memory and process list
- Convert 3 hook files from JS to TypeScript with full type definitions
- Rename all NEXUS branding text to Cryp

**Non-Goals:**
- No changes to the AI state machine, tool dispatch, or CrypLive public API
- No new npm packages (Web Audio API is browser-native)
- No changes to the 4-state orb, TopBar, CommandConsole, or NotificationSystem (already wired)
- No microphone capture — VoiceBar oscillator is a visual indicator, not a voice recorder

## Decisions

**Decision 1: REST endpoints (not WebSocket-only) for memory and processes**
- `GET /api/memory` returns full memory dict via `load_memory()` — MemoryPanel fetches on mount, no polling needed because memory changes are already pushed via WebSocket `"memory"` events
- `POST /api/memory` accepts `{"key": "...", "value": "..."}` and calls `update_memory()` — the WebSocket broadcast then pushes the updated dict to all clients
- `GET /api/processes` returns psutil snapshot sorted by CPU descending — fetched every 5s by SystemMonitor with a `setInterval` in the component (not via WebSocket, since processes are high-frequency and polling is simpler)
- Rationale: Memory is already pushed via WebSocket on connect and update, so the REST endpoint is a fallback initial load. Processes change second-by-second and don't need event-bus integration.

**Decision 2: Web Audio API loopback oscillator for VoiceBar**
- Create `AudioContext` + `OscillatorNode` → `AnalyserNode` → `AudioContext.destination` chain
- Read `AnalyserNode.getByteTimeDomainData()` in a `requestAnimationFrame` loop and map samples to SVG path points
- Oscillator frequency sweeps slowly (440→880 Hz over 4s) for a natural look, wraps around
- When `muted` is true: stop oscillator, draw flat line. When unmuted: start oscillator, draw waveform
- Rationale: No browser microphone access needed; visual-only waveform analogous to "listening" activity. Fast Fourier Transform via AnalyserNode is zero-cost (browser-native) and produces a realistic waveform.

**Decision 3: AppDock buttons fire `sendCommand(overlayName)` via useCrypWS hook**
- Each AppDock icon maps to a tool name (e.g., `terminal` → `"open terminal"`, `files` → `"show files"`)
- On click, call `sendCommand(toolName)` which sends a `{"command": toolName}` WebSocket message
- Backend receives it as a regular user command and dispatches to CrypLive tool execution
- A loading spinner appears on the icon until a matching transcript line comes back
- Rationale: Reuses existing WebSocket command pipeline — no new backend endpoints needed for tool dispatch. The backend already handles free-form text commands.

**Decision 4: TypeScript hook conversion**
- Define `CrypWSState`, `StatsData`, `StatsHistoryEntry` interfaces in a shared `types.ts`
- `useCrypWS` returns typed state + functions
- `useStats` returns typed stats object with proper number types
- `useStatsHistory` types the history array
- Hook consumers (App.jsx, SystemMonitor.tsx, TopBar.tsx) remain `.jsx`/`.tsx` as-is — Vite handles mixed extensions
- Rationale: TypeScript catches NaN bugs and makes the data flow self-documenting. The Vite config already uses `@vitejs/plugin-react` which strips TS annotations from `.ts`/`.tsx` files without needing `tsc`.

## Risks / Trade-offs

- [Risk] Process list API `/api/processes` may be slow if many processes — mitigated by psutil cache (`percent_percpu` with interval=0) and 5s polling interval
- [Risk] Web Audio API requires user gesture to create AudioContext — mitigated by creating context lazily on first VoiceBar interaction (click or state change to LISTENING)
- [Risk] TypeScript conversion may introduce type errors in existing JS consumers — mitigated by keeping existing `.jsx` files unchanged and only converting the hook files; Vite handles the mixed extensions seamlessly
- [Trade-off] No microphone input for VoiceBar — the waveform is a visual metaphor for the listening state, not actual audio capture. Real mic input would add complexity (permissions, browser compat, echo cancellation) without clear user value at this stage.
