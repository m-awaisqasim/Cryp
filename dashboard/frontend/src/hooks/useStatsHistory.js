import { useState, useEffect, useRef } from 'react'

export function useStatsHistory(stats) {
  const [history, setHistory] = useState({})
  const prevRef = useRef({})

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
        for (const key of ['cpu', 'ram', 'disk', 'battery_percent']) {
          const val = stats[key]
          if (val !== null && val !== undefined) {
            next[key] = [...(next[key] || []).slice(-59), val]
          }
        }
        return next
      })
    }
  }, [stats])

  return history
}
