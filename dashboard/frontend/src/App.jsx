import { useEffect, useRef } from 'react'
import { AppProvider, useApp } from './app/context/AppContext'
import { MainLayout } from './app/App'

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
  const { wsState, wsTranscript, wsMemoryVersion, setAiState, addMessage, refreshMemory } = useApp()
  const transcriptLenRef = useRef(0)
  const prevStateRef = useRef('')

  useEffect(() => {
    const figmaState = mapState(wsState.state)
    if (figmaState !== prevStateRef.current) {
      prevStateRef.current = figmaState
      setAiState(figmaState)
    }
  }, [wsState.state, setAiState])

  useEffect(() => {
    const newItems = wsTranscript.slice(transcriptLenRef.current)
    if (newItems.length > 0) {
      transcriptLenRef.current = wsTranscript.length
      newItems.forEach(t => {
        const msgType = t.type === 'user' || t.type === 'command' ? 'user' : 'ai'
        addMessage({ type: msgType, text: t.text })
      })
    }
  }, [wsTranscript, addMessage])

  useEffect(() => {
    if (wsMemoryVersion > 0) refreshMemory()
  }, [wsMemoryVersion, refreshMemory])

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
