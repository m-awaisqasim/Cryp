import { useState, useEffect, useRef, useCallback } from 'react'

export function useCrypWS() {
  const [state, setState] = useState('idle')
  const [muted, setMuted] = useState(false)
  const [transcript, setTranscript] = useState([])
  const [reactTasks, setReactTasks] = useState([])
  const [connected, setConnected] = useState(false)
  const ws = useRef(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/cryp`
    ws.current = new WebSocket(url)

    ws.current.onopen = () => setConnected(true)
    ws.current.onclose = () => {
      setConnected(false)
      setTimeout(connect, 3000)
    }
    ws.current.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'state') setState(data.state)
      if (data.type === 'mute') setMuted(data.value)
      if (data.type === 'transcript') {
        setTranscript(prev => [...prev.slice(-100), data])
      }
      if (data.type === 'react_task') {
        setReactTasks(prev => {
          const exists = prev.find(t => t.id === data.id)
          if (exists) return prev.map(t => t.id === data.id ? data : t)
          return [...prev.slice(-10), data]
        })
      }
      if (data.type === 'init') {
        setState(data.state)
        setMuted(data.muted)
        setTranscript(data.log || [])
      }
    }
  }, [])

  useEffect(() => { connect(); return () => ws.current?.close() }, [connect])

  const sendCommand = useCallback((text) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'command', text }))
    }
  }, [])

  const toggleMute = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'mute_toggle' }))
    }
  }, [])

  return { state, muted, transcript, reactTasks, connected, sendCommand, toggleMute }
}