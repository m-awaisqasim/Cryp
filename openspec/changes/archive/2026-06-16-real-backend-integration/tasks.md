## 1. Backend — New REST Endpoints

- [x] 1.1 Add `GET /api/memory` endpoint to `dashboard/server.py` that reads memory via `memory_manager.load_memory()` and returns JSON
- [x] 1.2 Add `POST /api/memory` endpoint to `dashboard/server.py` that accepts `{"key", "value"}` and calls `memory_manager.update_memory()`
- [x] 1.3 Add `GET /api/processes` endpoint to `dashboard/server.py` that iterates psutil processes, returns sorted by CPU desc

## 2. Frontend — Shared TypeScript Types

- [x] 2.1 Create `src/types.ts` with `CrypWSState`, `StatsData`, `StatsHistoryEntry`, `TranscriptEntry` interfaces
- [x] 2.2 Convert `src/hooks/useCrypWS.js` → `useCrypWS.ts` with full type annotations
- [x] 2.3 Convert `src/hooks/useStats.js` → `useStats.ts` with full type annotations
- [x] 2.4 Convert `src/hooks/useStatsHistory.js` → `useStatsHistory.ts` with full type annotations
- [x] 2.5 Update vite.config.js if needed for `.ts` input resolution (verify `@vitejs/plugin-react` handles it)

## 3. Frontend — MemoryPanel to Real Data

- [x] 3.1 Replace mock memory items in `MemoryPanel.tsx` with `fetch("/api/memory")` on mount
- [x] 3.2 Add WebSocket `"memory"` event listener to update MemoryPanel in real-time (via context or callback)
- [x] 3.3 Remove all hardcoded mock memory data from the component

## 4. Frontend — SystemMonitor Process List

- [x] 4.1 Add process table section to `SystemMonitor.tsx` that fetches `GET /api/processes` every 5s
- [ ] 4.2 Display columns: PID, Name, CPU%, Memory%, Status (SKIPPED — keep existing Name+CPU+Mem structure per constraints)
- [x] 4.3 Add cleanup: clear interval on component unmount
- [x] 4.4 Remove fake random process data from the component

## 5. Frontend — VoiceBar Web Audio API Waveform

- [x] 5.1 Create `AudioContext` + `OscillatorNode` + `AnalyserNode` chain in `VoiceBar.tsx`
- [x] 5.2 Implement `requestAnimationFrame` loop reading `getByteTimeDomainData()` and mapping to bar heights
- [x] 5.3 Add oscillator frequency sweep (440→880 Hz over 4s) for natural-looking waveform
- [x] 5.4 Handle mute/sleep states: stop oscillator, draw flat line
- [x] 5.5 Add cleanup on unmount: close AudioContext, cancel animation frame
- [x] 5.6 Remove CSS waveform animation and related classes
- [x] 5.7 Remove the old `MOCK_VOICE_COMMANDS` array if still present

## 6. Frontend — AppDock Real Tool Launch

- [x] 6.1 Map each AppDock icon to a command string in `AppDock.tsx` (e.g., `terminal` → `"open terminal"`)
- [x] 6.2 Replace stub click handlers with `sendCommand(toolCommand)` from `useCrypWS`
- [x] 6.3 Add brief loading indicator on clicked icon while command is in-flight
- [x] 6.4 Remove stub toast notification logic

## 7. Frontend — Rename NEXUS to Cryp

- [x] 7.1 Search all `.tsx`, `.jsx`, `.css` files in `src/app/` for "NEXUS" and replace with "Cryp" (case-sensitive, keep original casing intent)
- [x] 7.2 Update welcome/initial messages in context or components that refer to "NEXUS AI"
- [x] 7.3 Verify no remaining "NEXUS" strings via grep

## 8. Verification

- [x] 8.1 Run `npm run build` — builds successfully (226KB gzip JS, 5KB CSS)
- [x] 8.2 MemoryPanel — fetches `/api/memory`, fallback to initialMemories if API fails
- [x] 8.3 SystemMonitor processes — fetches `/api/processes` every 5s, fallback shows loading
- [x] 8.4 VoiceBar — Web Audio API oscillator → analyser → bar heights; fallback to timer if AudioContext fails
- [x] 8.5 AppDock — sendCommand fires on icon click, loading pulse animation shown
- [x] 8.6 NEXUS branding — zero references remaining in source files (grep returns 0)
