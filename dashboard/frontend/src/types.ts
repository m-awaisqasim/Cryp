export interface TranscriptEntry {
  type: string
  text: string
}

export interface CrypWSReturn {
  state: string
  muted: boolean
  transcript: TranscriptEntry[]
  memoryVersion: number
  sendCommand: (text: string) => void
  toggleMute: () => void
}

export interface StatsData {
