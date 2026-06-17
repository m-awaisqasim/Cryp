export interface TranscriptEntry {
  type: string
  text: string
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
