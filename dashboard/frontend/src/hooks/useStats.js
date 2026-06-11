import { useState, useEffect } from 'react'

export function useStats() {
  const [stats, setStats] = useState({
    cpu: 0, ram: 0, disk: 0, battery_percent: null, battery_plugged: false,
    net: 0, gpu: -1, tmp: -1, uptime: 0, procCount: 0,
  })

  useEffect(() => {
    const poll = async () => {
      try {
        const r = await fetch('/api/stats')
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
      } catch {}
    }
    poll()
    const id = setInterval(poll, 2000)
    return () => clearInterval(id)
  }, [])

  return stats
}
