import HUD from './components/HUD'
import { ToastProvider, useToast } from './components/Toast'
import { useJarvisWS } from './hooks/useJarvisWS'
import { useStats } from './hooks/useStats'
import { useStatsHistory } from './hooks/useStatsHistory'

function AppInner() {
  const ws = useJarvisWS()
  const stats = useStats()
  const history = useStatsHistory(stats)
  const addToast = useToast()

  return <HUD {...ws} stats={stats} history={history} addToast={addToast} />
}

export default function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  )
}
