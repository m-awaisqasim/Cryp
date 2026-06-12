export interface TranscriptEntry {
  type: string
  text: string
}

export interface CrypWSReturn {
  state: string
  muted: boolean
  transcript: TranscriptEntry[]
  reactTasks: { id: string; name?: string; status?: string }[]
  connected: boolean
  memoryVersion: number
  sendCommand: (text: string) => void
  toggleMute: () => void
}

export interface StatsData {
  cpu: number
  ram: number
  disk: number
  battery_percent: number | null
  battery_plugged: boolean
  net: number
  gpu: number
  tmp: number
  uptime: number
  procCount: number
}

export interface MemoryCategory {
  name: string
  count: number
}

export interface ProcessEntry {
  name: string
  cpu: number
  mem: number
}
