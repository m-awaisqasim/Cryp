import { useState, useEffect } from 'react'
import type { StatsData } from '../types'

export function useStats() {
  const [stats, setStats] = useState<StatsData>({
    cpu: 0, ram: 0, disk: 0, battery_percent: null, battery_plugged: false,
    net: 0, gpu: -1, tmp: -1, uptime: 0, procCount: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const poll = async () => {
    try {
      const r = await fetch('/api/stats')
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      setStats(prev => ({
        ...prev,
        ...d,
        net: d.net ?? prev.net,
        gpu: d.gpu ?? prev.gpu,
        tmp: d.tmp ?? prev.tmp,
        uptime: d.uptime ?? prev.uptime,
        procCount: d.procCount ?? prev.procCount,
      }))
      setError(null)
      setLoading(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch stats')
      setLoading(false)
    }
  }

  const retry = () => {
    setLoading(true)
    setError(null)
    poll()
  }

  useEffect(() => {
    poll()
    const id = setInterval(poll, 2000)
    return () => clearInterval(id)
  }, [])

  return { stats, loading, error, retry }
}
