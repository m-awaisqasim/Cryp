import { useState, useEffect, useRef, useCallback } from 'react'
import type { CrypWSReturn, TranscriptEntry } from '../types'

export function useCrypWS(): CrypWSReturn {
  const [state, setState] = useState('idle')
  const [muted, setMuted] = useState(false)
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [memoryVersion, setMemoryVersion] = useState(0)
  const ws = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/cryp`
    ws.current = new WebSocket(url)

    ws.current.onmessage = (e: MessageEvent) => {
      const data = JSON.parse(e.data)
      if (data.type === 'state') setState(data.state)
      if (data.type === 'mute') setMuted(data.value)
      if (data.type === 'transcript') {
        setTranscript(prev => [...prev.slice(-100), data])
      }
      if (data.type === 'memory') {
        setMemoryVersion(v => v + 1)
      }
      if (data.type === 'init') {
        setState(data.state)
        setMuted(data.muted)
        setTranscript(data.log || [])
      }
    }
  }, [])

  useEffect(() => { connect(); return () => ws.current?.close() }, [connect])

  const sendCommand = useCallback((text: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'command', text }))
    }
  }, [])

  const toggleMute = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'mute_toggle' }))
    }
  }, [])

  return { state, muted, transcript, sendCommand, toggleMute, memoryVersion }
}
