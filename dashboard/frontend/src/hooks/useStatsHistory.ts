import { useState, useEffect, useRef } from 'react'
import type { StatsData } from '../types'

export function useStatsHistory(stats: StatsData): Record<string, number[]> {
  const [history, setHistory] = useState<Record<string, number[]>>({})
  const prevRef = useRef<Partial<StatsData>>({})

  useEffect(() => {
    const prev = prevRef.current
    const changed =
      prev.cpu !== stats.cpu ||
      prev.ram !== stats.ram ||
      prev.disk !== stats.disk ||
      prev.battery_percent !== stats.battery_percent

    if (changed) {
      prevRef.current = { ...stats }
      setHistory(h => {
        const next = { ...h }
        for (const key of ['cpu', 'ram', 'disk', 'battery_percent'] as const) {
          const val = stats[key]
          if (val !== null && val !== undefined) {
            next[key] = [...(next[key] || []).slice(-59), val as number]
          }
        }
        return next
      })
    }
  }, [stats])

  return history
}
