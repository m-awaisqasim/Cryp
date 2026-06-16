## Why

The Figma NEXUS AI UI was integrated in the previous change, but all data is still mock/simulated — MemoryPanel shows hardcoded items, SystemMonitor process list is fake, VoiceBar waveform is CSS-animated, AppDock buttons show stub notifications, and all hooks are plain JS. To make the interface functional, each component must be wired to the real Cryp backend.

## What Changes

- Rename all "NEXUS" text labels and "NEXUS AI" branding to "Cryp" across the UI
- Add `/api/memory` GET/POST endpoints to `dashboard/server.py` for reading/writing long-term memory
- Add `/api/processes` endpoint returning real psutil process list
- Connect `MemoryPanel` to real memory data via `/api/memory`
- Connect `SystemMonitor` process list to real data via `/api/processes`
- Replace fake CSS-animated VoiceBar waveform with real `Web Audio API` `AnalyserNode` driven by a loopback oscillator
- Connect `AppDock` icon clicks to real Cryp tool invocations via WebSocket `command` messages
- Convert `useCrypWS.js`, `useStats.js`, and `useStatsHistory.js` from plain JS to TypeScript (`.ts`)
- Remove all remaining mock/hardcoded data in wired components

## Capabilities

### New Capabilities
- `rename-nexus-to-cryp`: Update all branding text from NEXUS/NEXUS AI to Cryp
- `memory-panel-data`: Serve real memory data through REST API and display in MemoryPanel
- `system-monitor-processes`: Serve real psutil process list through REST API and display in SystemMonitor
- `voicebar-audio`: Replace CSS waveform animation with real Web Audio API AnalyserNode
- `appdock-tools`: Launch real Cryp tools when AppDock icons are clicked
- `typescript-hooks`: Migrate useCrypWS, useStats, useStatsHistory from JS to TS

### Modified Capabilities
- `web-dashboard`: Add new REST endpoints (`/api/memory`, `/api/processes`); the existing spec assumed PyQt6-era architecture and needs to reflect that the frontend is now React

## Impact

- `dashboard/server.py`: New REST endpoints for memory and processes
- `dashboard/frontend/src/app/components/MemoryPanel.tsx`: Wire to real API
- `dashboard/frontend/src/app/components/SystemMonitor.tsx`: Process list from API
- `dashboard/frontend/src/app/components/VoiceBar.tsx`: Web Audio API integration
- `dashboard/frontend/src/app/components/AppDock.tsx`: Tool launch via WebSocket
- `dashboard/frontend/src/hooks/`: Convert 3 files from `.js` to `.ts`
- `dashboard/frontend/package.json`: No new deps needed (Web Audio API is browser-native)
