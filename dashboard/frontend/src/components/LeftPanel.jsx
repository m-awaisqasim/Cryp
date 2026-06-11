import MetricBar from './MetricBar'

const OS_MAP = { Windows: 'WIN', Darwin: 'macOS', Linux: 'LINUX' }
const OS_NAME = OS_MAP[window.navigator.platform] || window.navigator.platform.toUpperCase()

export default function LeftPanel({ stats, history }) {
  const uptime = stats.uptime || 0
  const h = Math.floor(uptime / 3600)
  const m = Math.floor((uptime % 3600) / 60)

  return (
    <aside className="flex-shrink-0 flex flex-col px-2 py-2.5 gap-1.5 overflow-y-auto"
      style={{
        width: 148,
        background: 'linear-gradient(to right, #000d14 0%, #000b14 80%, #000d14 100%)',
        borderRight: '1px solid #0d3347',
      }}
    >
      {/* Header */}
      <div className="text-[7px] font-bold font-mono tracking-wider pb-1"
        style={{ color: '#00d4ff', borderBottom: '1px solid #0d3347' }}
      >
        ◈ SYS MONITOR
      </div>

      {/* Metric bars */}
      <MetricBar label="CPU" value={stats.cpu || 0} color="#00d4ff" />
      <MetricBar label="MEM" value={stats.ram || 0} color="#ffcc00" />
      <MetricBar label="NET" value={stats.net || 0} color="#00ff88" />
      <MetricBar label="GPU" value={stats.gpu >= 0 ? stats.gpu : 0} color="#ff6b00" />
      <MetricBar label="TMP" value={stats.tmp >= 0 ? stats.tmp : 0} color="#ff6688" />

      {/* Info panel */}
      <div
        className="px-1.5 py-1 space-y-0.5"
        style={{
          background: 'linear-gradient(to bottom right, #021018, #010f18)',
          border: '1px solid #0f4060',
          borderRadius: 5,
        }}
      >
        <div className="text-[8px] font-bold font-mono" style={{ color: '#00ff88' }}>
          UP {String(h).padStart(2, '0')}:{String(m).padStart(2, '0')}
        </div>
        <div className="text-[8px] font-mono" style={{ color: '#5ab8cc' }}>
          PROC {stats.procCount || '--'}
        </div>
        <div className="text-[8px] font-mono" style={{ color: '#ffcc00' }}>
          OS {OS_NAME}
        </div>
      </div>

      {/* Status badges */}
      {[
        { text: 'AI CORE\nACTIVE', col: '#00ff88', glow: '#005533' },
        { text: 'SEC\nCLEARED', col: '#00d4ff', glow: '#001f2e' },
        { text: 'PROTOCOL\nV2', col: '#3a8a9a', glow: '#000a14' },
      ].map((b, i) => (
        <div
          key={i}
          className="text-[7px] font-bold font-mono text-center px-2 py-1.5 leading-tight"
          style={{
            color: b.col,
            background: `linear-gradient(to bottom, #010f18, ${b.glow})`,
            border: `1px solid ${b.col}`,
            borderRadius: 4,
          }}
        >
          {b.text}
        </div>
      ))}

      <div className="flex-1" />
    </aside>
  )
}
