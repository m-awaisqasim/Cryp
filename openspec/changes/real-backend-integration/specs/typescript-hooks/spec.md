## ADDED Requirements

### Requirement: Hook files use TypeScript
The hook files SHALL be converted from JavaScript to TypeScript with proper type definitions.

#### Scenario: useCrypWS is a typed .ts file
- **WHEN** `useCrypWS.ts` is imported
- **THEN** it exports a typed interface `CrypWSState` with fields: `state: string`, `muted: boolean`, `transcript: TranscriptEntry[]`, `connected: boolean`
- **AND** the return type is `{ state, muted, transcript, connected, sendCommand, toggleMute }` with correct types

#### Scenario: useStats is a typed .ts file
- **WHEN** `useStats.ts` is imported
- **THEN** it exports a typed interface `StatsData` with numeric fields: `cpu`, `ram`, `disk`, `net`, `gpu`, `tmp`, `uptime`, `procCount`
- **AND** the return type `{ stats, loading, error }` is typed

#### Scenario: useStatsHistory is a typed .ts file
- **WHEN** `useStatsHistory.ts` is imported
- **THEN** it exports `StatsHistoryEntry` interface with `timestamp: number` and stat fields
- **AND** the hook properly types the history array

#### Scenario: Shared types in single file
- **WHEN** any hook imports types
- **THEN** common types (`CrypWSState`, `StatsData`, `TranscriptEntry`) are defined in a shared `types.ts` file
- **AND** all hooks import from `../types`
