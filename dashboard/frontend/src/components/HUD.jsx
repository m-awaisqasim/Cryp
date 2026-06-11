import { useState, useEffect } from 'react'
import OrbHUD from './OrbHUD'
import LeftPanel from './LeftPanel'
import RightPanel from './RightPanel'

export default function HUD({ state, muted, transcript, reactTasks, connected, sendCommand, toggleMute, stats, history, addToast }) {
  const now = new Date()
  const [timeStr, setTimeStr] = useState(now.toLocaleTimeString())
  const [dateStr, setDateStr] = useState(now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }))
  const [colonPulse, setColonPulse] = useState(true)
  const [headerTick, setHeaderTick] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      const n = new Date()
      setTimeStr(n.toLocaleTimeString())
      setDateStr(n.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }))
      setColonPulse(prev => !prev)
    }, 1000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    const id = setInterval(() => setHeaderTick(t => t + 1), 600)
    return () => clearInterval(id)
  }, [])

  const speaking = state === 'speaking'
  const dotColor = muted ? '#ff3366' : '#00ff88'
  const dotPulse = 0.6 + 0.4 * Math.sin(headerTick * 0.5)
  const titleGlow = 180 + Math.floor(75 * dotPulse)

  return (
    <div className="h-screen w-full flex flex-col bg-[#00060a] overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 flex items-center px-4"
        style={{
          height: 56,
          background: 'linear-gradient(to bottom, #011520, #000d14)',
          borderBottom: '1px solid #1a5c7a',
        }}
      >
        <div className="flex items-center gap-1">
          <span className="text-lg" style={{ color: dotColor }}>●</span>
          <span className="text-[8px] font-mono" style={{ color: '#007a99' }}>Cryp v2</span>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center">
          <span className="text-[17px] font-bold font-mono tracking-wider"
            style={{
              color: '#00d4ff',
              textShadow: `0 0 ${10 + titleGlow * 0.05}px rgba(0,212,255,${0.3 + dotPulse * 0.2})`,
            }}
          >
            J.A.R.V.I.S
          </span>
          <span className="text-[7px] font-mono" style={{ color: '#007a99' }}>
            Just A Rather Very Intelligent System
          </span>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-[14px] font-bold font-mono" style={{ color: '#00d4ff' }}>
            {colonPulse ? timeStr : timeStr.replace(/:/g, ' ')}
          </span>
          <span className="text-[7px] font-mono" style={{ color: '#3a8a9a' }}>
            {dateStr}
          </span>
        </div>
      </header>

      {/* Body */}
      <main className="flex-1 flex min-h-0">
        <LeftPanel stats={stats} history={history} />

        <div className="flex-1 min-w-0">
          <OrbHUD state={state} muted={muted} speaking={speaking} />
        </div>

        <RightPanel
          transcript={transcript}
          reactTasks={reactTasks}
          sendCommand={sendCommand}
          toggleMute={toggleMute}
          muted={muted}
          addToast={addToast}
        />
      </main>

      {/* Status bar */}
      <footer
        className="flex-shrink-0 flex items-center px-4"
        style={{
          height: 24,
          background: 'linear-gradient(to bottom, #000d14, #00060a)',
          borderTop: '1px solid #0f4060',
        }}
      >
        <span className="text-[7px] font-mono" style={{ color: '#3a8a9a' }}>F4 Mute  ·  F11 Fullscreen</span>
        <span className="flex-1 text-center text-[7px] font-mono" style={{ color: '#3a8a9a' }}>
          Awais Project  ·  Cryp v2  ·  CLASSIFIED
        </span>
        <span className="text-[7px] font-mono" style={{ color: '#007a99' }}>
          © Cryp
        </span>
      </footer>
    </div>
  )
}
