import { useEffect, useRef, useState, type ReactNode } from 'react';
import { motion } from 'motion/react';
import { Activity, Cpu, Database, Thermometer, RefreshCw } from 'lucide-react';
import { useApp } from '../context/AppContext';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

interface MetricCardProps {
  label: string;
  value: number;
  unit: string;
  color: string;
  icon: ReactNode;
  data: { t: number; v: number }[];
  display?: string;
}

function MetricCard({ label, value, unit, color, icon, data, display }: MetricCardProps) {
  return (
    <div
      className="rounded-xl p-3 flex flex-col gap-2"
      style={{
        background: 'rgba(0, 8, 20, 0.5)',
        border: `1px solid ${color}25`,
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div style={{ color }}>{icon}</div>
          <span style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '10px' }}>{label}</span>
        </div>
        <span style={{ ...orb, color, fontSize: '12px', textShadow: `0 0 8px ${color}` }}>
          {display || `${Math.round(value)}`}
          {!display && <span style={{ fontSize: '9px', opacity: 0.7 }}>{unit}</span>}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <motion.div
          className="h-full rounded-full"
          animate={{ width: `${value}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{ background: `linear-gradient(90deg, ${color}80, ${color})`, boxShadow: `0 0 6px ${color}` }}
        />
      </div>

      {/* Mini chart */}
      <div style={{ height: 36 }}>
        <Sparkline data={data} color={color} />
      </div>
    </div>
  );
}

function Sparkline({ data, color }: { data: { v: number }[]; color: string }) {
  if (data.length < 2) return null;
  const maxV = Math.max(...data.map(d => d.v));
  const minV = Math.min(...data.map(d => d.v));
  if (maxV === minV) {
    return (
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
        <line x1="0" y1="50" x2="100" y2="50" stroke={color} strokeWidth="1.5" opacity="0.5" />
      </svg>
    );
  }
  const range = maxV - minV;
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((d.v - minV) / range) * 100;
    return `${x}% ${y}%`;
  }).join(', ');
  const areaPoints = [`0% 100%`, ...points.split(', '), `100% 100%`].join(', ');
  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
      <defs>
        <linearGradient id={`spark-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="5%" stopColor={color} stopOpacity={0.25} />
          <stop offset="95%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#spark-${color})`} />
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
}

export function SystemMonitor() {
  const { stats, statsLoading: loading, statsError: error, refreshStats: retry } = useApp();
  const prevRef = useRef(stats);
  const [data, setData] = useState<Record<string, { t: number; v: number }[]>>({
    cpu: [], ram: [],
  });

  useEffect(() => {
    const prev = prevRef.current;
    if (prev.cpu !== stats.cpu || prev.ram !== stats.ram) {
      prevRef.current = stats;
      const t = Date.now();
      setData(d => ({
        cpu: [...d.cpu.slice(-24), { t, v: stats.cpu }],
        ram: [...d.ram.slice(-24), { t, v: stats.ram }],
      }));
    }
  }, [stats]);

  const fmtUptime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return `${h}h ${m}m`;
  };

  const temp = stats.tmp > 0 ? stats.tmp : null;
  const uptime = stats.uptime;

  const metrics = [
    { label: 'CPU', value: stats.cpu, unit: '%', color: '#00f5ff', icon: <Cpu className="w-3 h-3" />, data: data.cpu },
    { label: 'MEMORY', value: stats.ram, unit: '%', color: '#a855f7', icon: <Database className="w-3 h-3" />, data: data.ram },
  ];

  const getHealthColor = (v: number) => v < 60 ? '#22c55e' : v < 80 ? '#f59e0b' : '#ef4444';
  const overallHealth = Math.round((stats.cpu + stats.ram) / 2);

  return (
    <div className="flex flex-col h-full gap-3 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4" style={{ color: '#00f5ff' }} />
          <span style={{ ...orb, color: '#00f5ff', fontSize: '11px', letterSpacing: '0.15em' }}>SYSTEM MONITOR</span>
        </div>
        <div className="flex items-center gap-1.5">
          <motion.div
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: '#22c55e' }}
          />
          <span style={{ ...mono, color: '#22c55e', fontSize: '9px' }}>LIVE</span>
        </div>
      </div>

      {/* Health overview */}
      <div
        className="rounded-xl p-3 flex items-center gap-4 flex-shrink-0"
        style={{
          background: 'rgba(0,8,20,0.5)',
          border: `1px solid ${getHealthColor(overallHealth)}25`,
        }}
      >
        <div className="relative w-12 h-12 flex-shrink-0">
          <svg viewBox="0 0 48 48" className="w-full h-full -rotate-90">
            <circle cx="24" cy="24" r="20" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
            <motion.circle
              cx="24" cy="24" r="20"
              fill="none"
              stroke={getHealthColor(overallHealth)}
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 20}`}
              animate={{ strokeDashoffset: 2 * Math.PI * 20 * (1 - overallHealth / 100) }}
              transition={{ duration: 1, ease: 'easeOut' }}
              style={{ filter: `drop-shadow(0 0 4px ${getHealthColor(overallHealth)})` }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span style={{ ...orb, color: getHealthColor(overallHealth), fontSize: '10px' }}>
              {Math.round(overallHealth)}
            </span>
          </div>
        </div>
        <div className="flex flex-col gap-0.5">
          <span style={{ ...raj, color: 'rgba(255,255,255,0.7)', fontSize: '13px' }}>System Health</span>
          <span style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '10px' }}>
            UPTIME: {fmtUptime(uptime)}
          </span>
          {temp !== null && (
            <div className="flex items-center gap-2 mt-0.5">
              <Thermometer className="w-3 h-3" style={{ color: '#f59e0b' }} />
              <span style={{ ...mono, color: '#f59e0b', fontSize: '10px' }}>{Math.round(temp)}°C</span>
            </div>
          )}
        </div>
        <div className="ml-auto">
          <span style={{ ...raj, color: getHealthColor(overallHealth), fontSize: '12px' }}>
            {overallHealth < 60 ? 'OPTIMAL' : overallHealth < 80 ? 'MODERATE' : 'HIGH LOAD'}
          </span>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 gap-2 flex-1 overflow-y-auto">
        {loading ? (
          <>
            {[1, 2].map(i => (
              <div key={i} className="rounded-xl p-3 flex flex-col gap-2" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(0,245,255,0.1)' }}>
                <motion.div animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 1.5, repeat: Infinity }} className="h-3 rounded w-3/4" style={{ background: 'rgba(0,245,255,0.15)' }} />
                <motion.div animate={{ opacity: [0.2, 0.4, 0.2] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }} className="h-6 rounded" style={{ background: 'rgba(0,245,255,0.08)' }} />
                <motion.div animate={{ opacity: [0.2, 0.4, 0.2] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.1 }} className="h-20 rounded" style={{ background: 'rgba(0,245,255,0.05)' }} />
              </div>
            ))}
          </>
        ) : error ? (
          <div className="col-span-2 rounded-xl p-4 flex flex-col items-center justify-center gap-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(239,68,68,0.3)' }}>
            <span style={{ ...mono, color: '#ef4444', fontSize: '11px' }}>CONNECTION LOST</span>
            <span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '9px', textAlign: 'center' }}>{error}</span>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={retry}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg cursor-pointer"
              style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }}
            >
              <RefreshCw className="w-3 h-3" style={{ color: '#ef4444' }} />
              <span style={{ ...mono, color: '#ef4444', fontSize: '9px' }}>RETRY</span>
            </motion.button>
          </div>
        ) : (
          metrics.map(m => (
            <MetricCard key={m.label} {...m} />
          ))
        )}
      </div>
    </div>
  );
}
