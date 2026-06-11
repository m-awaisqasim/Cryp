import { useState, useRef, useEffect } from 'react'

const LOG_COLORS = {
  SYS: '#5ab8cc',
  YOU: '#00d4ff',
  Cryp: '#00ff88',
  FILE: '#ffcc00',
  CMD: '#ff6b00',
  ERR: '#ff3355',
}

export default function RightPanel({ transcript, reactTasks, sendCommand, toggleMute, muted, addToast }) {
  const [input, setInput] = useState('')
  const [history, setHistory] = useState([])
  const [histIdx, setHistIdx] = useState(-1)
  const [uploading, setUploading] = useState(false)
  const [log, setLog] = useState([])
  const logEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [log])

  useEffect(() => {
    if (transcript.length > 0) {
      const last = transcript[transcript.length - 1]
      setLog(prev => [...prev.slice(-200), {
        text: last.text,
        time: new Date().toLocaleTimeString(),
        type: last.text.startsWith('You:') ? 'YOU' :
              last.text.startsWith('Cryp:') ? 'Cryp' : 'SYS',
      }])
    }
  }, [transcript])

  const handleSend = () => {
    if (input.trim()) {
      sendCommand(input.trim())
      setLog(prev => [...prev.slice(-200), {
        text: `CMD: ${input.trim()}`,
        time: new Date().toLocaleTimeString(),
        type: 'CMD',
      }])
      setHistory(prev => [input.trim(), ...prev.slice(0, 49)])
      setHistIdx(-1)
      setInput('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSend()
    else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (history.length > 0) {
        const next = Math.min(histIdx + 1, history.length - 1)
        setHistIdx(next)
        setInput(history[next])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (histIdx > 0) {
        setHistIdx(histIdx - 1)
        setInput(history[histIdx - 1])
      } else {
        setHistIdx(-1)
        setInput('')
      }
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch('/api/upload', { method: 'POST', body: formData })
      const data = await res.json()
      setLog(prev => [...prev.slice(-200), {
        text: `FILE: ${file.name} (${(file.size / 1024).toFixed(1)}KB) loaded`,
        time: new Date().toLocaleTimeString(),
        type: 'FILE',
      }])
      addToast?.('File uploaded: ' + file.name, 'success')
    } catch {
      setLog(prev => [...prev.slice(-200), {
        text: 'FILE: Upload failed',
        time: new Date().toLocaleTimeString(),
        type: 'ERR',
      }])
      addToast?.('Upload failed', 'error')
    }
    setUploading(false)
    e.target.value = ''
  }

  return (
    <aside className="flex-shrink-0 flex flex-col px-2 py-2 gap-1.5 overflow-hidden"
      style={{
        width: 340,
        background: 'linear-gradient(to left, #000d14 0%, #000b14 80%, #000d14 100%)',
        borderLeft: '1px solid #0d3347',
      }}
    >
      {/* Activity Log */}
      <div className="text-[7px] font-bold font-mono" style={{ color: '#5ab8cc' }}>▸ ACTIVITY LOG</div>
      <div className="flex-1 overflow-y-auto font-mono text-[7px] leading-relaxed space-y-0.5"
        style={{
          background: 'transparent',
          scrollbarWidth: 'thin',
          scrollbarColor: '#0f4060 transparent',
        }}
      >
        {log.length === 0 ? (
          <div className="text-center py-8" style={{ color: '#3a8a9a33' }}>[ NO ACTIVITY ]</div>
        ) : (
          log.map((entry, i) => (
            <div key={i}>
              <span style={{ color: '#3a8a9a' }}>[{entry.time}] </span>
              <span style={{ color: LOG_COLORS[entry.type] || '#5ab8cc' }}>{entry.text}</span>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>

      <div style={{ borderTop: '1px solid #0f4060', margin: '2px 0' }} />

      {/* File Upload */}
      <div className="text-[7px] font-bold font-mono" style={{ color: '#5ab8cc' }}>▸ FILE UPLOAD</div>
      <div
        className="relative flex items-center justify-center py-4 cursor-pointer border border-dashed text-center text-[7px] font-mono transition-colors hover:opacity-80"
        style={{
          borderColor: '#0f4060',
          color: '#5ab8cc',
          background: uploading ? 'rgba(255,107,0,0.1)' : 'transparent',
          minHeight: 48,
        }}
        onClick={() => document.getElementById('file-upload-right')?.click()}
        onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = '#00d4ff' }}
        onDragLeave={(e) => { e.currentTarget.style.borderColor = '#0f4060' }}
        onDrop={(e) => {
          e.preventDefault()
          e.currentTarget.style.borderColor = '#0f4060'
          const file = e.dataTransfer.files[0]
          if (file) {
            const input = document.getElementById('file-upload-right')
            const dt = new DataTransfer()
            dt.items.add(file)
            input.files = dt.files
            input.dispatchEvent(new Event('change'))
          }
        }}
      >
        {uploading ? 'UPLOADING...' : '⬆  Drop file here or click to browse'}
      </div>
      <input type="file" id="file-upload-right" className="hidden" onChange={handleFileUpload} />

      <div style={{ borderTop: '1px solid #0f4060', margin: '2px 0' }} />

      {/* Command Input */}
      <div className="text-[7px] font-bold font-mono" style={{ color: '#5ab8cc' }}>▸ COMMAND INPUT</div>
      <div className="flex gap-1">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a command or question…"
          className="flex-1 font-mono text-[9px] px-2 outline-none"
          style={{
            height: 30,
            background: '#000d14',
            color: '#d8f8ff',
            border: '1px solid #0d3347',
            borderRadius: 4,
          }}
          onFocus={(e) => e.target.style.borderColor = '#00d4ff'}
          onBlur={(e) => e.target.style.borderColor = '#0d3347'}
        />
        <button
          onClick={handleSend}
          className="flex items-center justify-center text-[11px] font-bold"
          style={{
            width: 30, height: 30,
            background: '#001f2e',
            color: '#00d4ff',
            border: '1px solid #007a99',
            borderRadius: 4,
            cursor: 'pointer',
          }}
          onMouseEnter={(e) => { e.target.style.background = '#007a99'; e.target.style.color = '#00060a' }}
          onMouseLeave={(e) => { e.target.style.background = '#001f2e'; e.target.style.color = '#00d4ff' }}
        >
          ▸
        </button>
      </div>

      {/* Buttons */}
      <button
        onClick={toggleMute}
        className="font-mono text-[8px] font-bold tracking-wider"
        style={{
          height: 30,
          cursor: 'pointer',
          border: 'none',
          borderRadius: 4,
          ...(muted
            ? {
                background: 'linear-gradient(to bottom right, #1a0008, #140006)',
                color: '#ff3366',
              }
            : {
                background: 'linear-gradient(to bottom right, #001a0d, #001105)',
                color: '#00ff88',
              }),
        }}
      >
        {muted ? '\uD83D\uDD07  MICROPHONE MUTED' : '\uD83C\uDF99  MICROPHONE ACTIVE'}
      </button>

      <button
        onClick={() => {
          sendCommand?.('__wake__')
          addToast?.('Wake signal sent', 'info', 1500)
        }}
        className="font-mono text-[7px] font-bold"
        style={{
          height: 26,
          background: 'transparent',
          color: '#5ab8cc',
          border: '1px solid #0d3347',
          borderRadius: 3,
          cursor: 'pointer',
        }}
        onMouseEnter={(e) => { e.target.style.color = '#00d4ff'; e.target.style.border = '1px solid #007a99'; e.target.style.background = '#001f2e' }}
        onMouseLeave={(e) => { e.target.style.color = '#5ab8cc'; e.target.style.border = '1px solid #0d3347'; e.target.style.background = 'transparent' }}
      >
        🔊  WAKE Cryp
      </button>
    </aside>
  )
}
