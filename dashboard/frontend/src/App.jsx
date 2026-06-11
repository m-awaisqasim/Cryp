import { useEffect, useRef } from 'react'
import { AppProvider, useApp } from './app/context/AppContext'
import { MainLayout } from './app/App'
import { useCrypWS } from './hooks/useCrypWS'
import { useStats } from './hooks/useStats'

function mapState(wsState) {
  switch (wsState) {
    case 'idle':
    case 'SLEEPING':
      return 'idle'
    case 'LISTENING':
      return 'listening'
    case 'THINKING':
      return 'processing'
    case 'SPEAKING':
      return 'responding'
    default:
      return 'idle'
  }
}

function DataBridge({ children }) {
  const ws = useCrypWS()
  const { setAiState, addMessage } = useApp()
  const transcriptLenRef = useRef(0)
  const prevStateRef = useRef('')

  useEffect(() => {
    const figmaState = mapState(ws.state)
    if (figmaState !== prevStateRef.current) {
      prevStateRef.current = figmaState
      setAiState(figmaState)
    }
  }, [ws.state, setAiState])

  useEffect(() => {
    const newItems = ws.transcript.slice(transcriptLenRef.current)
    if (newItems.length > 0) {
      transcriptLenRef.current = ws.transcript.length
      newItems.forEach(t => {
        const msgType = t.type === 'user' || t.type === 'command' ? 'user' : 'ai'
        addMessage({ type: msgType, text: t.text })
      })
    }
  }, [ws.transcript, addMessage])

  return children
}

export default function App() {
  return (
    <AppProvider>
      <DataBridge>
        <MainLayout />
      </DataBridge>
    </AppProvider>
  )
}
