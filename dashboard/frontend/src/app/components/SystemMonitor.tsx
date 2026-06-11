import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'motion/react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { Activity, Cpu, Database, Wifi, Thermometer, Zap } from 'lucide-react';
import { useStats } from '../../hooks/useStats';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

interface MetricCardProps {
  label: string;
  value: number;
  unit: string;
  color: string;
  icon: React.ReactNode;
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
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={`grad-${label}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.25} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="v"
              stroke={color}
              strokeWidth={1.5}
              fill={`url(#grad-${label})`}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function SystemMonitor() {
  const stats = useStats();
  const prevRef = useRef(stats);
  const [data, setData] = useState<Record<string, { t: number; v: number }[]>>({
    cpu: [], ram: [], net: [], gpu: [],
  });

  useEffect(() => {
    const prev = prevRef.current;
    if (prev.cpu !== stats.cpu || prev.ram !== stats.ram) {
      prevRef.current = stats;
      const t = Date.now();
      setData(d => ({
        cpu: [...d.cpu.slice(-24), { t, v: stats.cpu }],
        ram: [...d.ram.slice(-24), { t, v: stats.ram }],
        net: [...d.net.slice(-24), { t, v: Math.min(100, Math.max(0, stats.net * 8)) }],
        gpu: [...d.gpu.slice(-24), { t, v: stats.gpu > 0 ? stats.gpu : 5 }],
      }));
    }
  }, [stats]);

  const fmtUptime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return `${h}h ${m}m`;
  };

  const temp = stats.tmp > 0 ? stats.tmp : 45;
  const uptime = stats.uptime;
  const netDisplay = stats.net < 1 ? `${(stats.net * 1024).toFixed(0)} KB/s` : `${stats.net.toFixed(1)} MB/s`;

  const metrics = [
    { label: 'CPU', value: stats.cpu, unit: '%', color: '#00f5ff', icon: <Cpu className="w-3 h-3" />, data: data.cpu },
    { label: 'MEMORY', value: stats.ram, unit: '%', color: '#a855f7', icon: <Database className="w-3 h-3" />, data: data.ram },
    { label: 'NETWORK', value: stats.net, unit: ' MB/s', color: '#0ea5e9', icon: <Wifi className="w-3 h-3" />, data: data.net, display: netDisplay },
    { label: 'GPU', value: stats.gpu > 0 ? stats.gpu : 0, unit: stats.gpu > 0 ? '%' : '', color: '#f59e0b', icon: <Zap className="w-3 h-3" />, data: data.gpu },
  ];

  const getHealthColor = (v: number) => v < 60 ? '#22c55e' : v < 80 ? '#f59e0b' : '#ef4444';
  const overallHealth = Math.round((stats.cpu + stats.ram + Math.min(100, stats.net * 8) + (stats.gpu > 0 ? stats.gpu : 20)) / 4);

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
          <div className="flex items-center gap-2 mt-0.5">
            <Thermometer className="w-3 h-3" style={{ color: '#f59e0b' }} />
            <span style={{ ...mono, color: '#f59e0b', fontSize: '10px' }}>{Math.round(temp)}°C</span>
          </div>
        </div>
        <div className="ml-auto">
          <span style={{ ...raj, color: getHealthColor(overallHealth), fontSize: '12px' }}>
            {overallHealth < 60 ? 'OPTIMAL' : overallHealth < 80 ? 'MODERATE' : 'HIGH LOAD'}
          </span>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 gap-2 flex-1 overflow-y-auto">
        {metrics.map(m => (
          <MetricCard key={m.label} {...m} />
        ))}
      </div>

      {/* Process list */}
      <div
        className="rounded-xl p-3 flex-shrink-0"
        style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(0,245,255,0.08)' }}
      >
        <div className="flex items-center justify-between mb-2">
          <span style={{ ...mono, color: 'rgba(0,245,255,0.6)', fontSize: '10px' }}>TOP PROCESSES</span>
        </div>
        {[
          { name: 'nexus-core.exe', cpu: 12.4, mem: 842 },
          { name: 'neural-net.dll', cpu: 8.1, mem: 1240 },
          { name: 'voice-engine', cpu: 4.2, mem: 256 },
          { name: 'render-host', cpu: 3.8, mem: 512 },
        ].map(p => (
          <div key={p.name} className="flex items-center justify-between py-1" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
            <span style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '9px' }}>{p.name}</span>
            <div className="flex gap-3">
              <span style={{ ...mono, color: '#00f5ff', fontSize: '9px' }}>{p.cpu}%</span>
              <span style={{ ...mono, color: '#a855f7', fontSize: '9px' }}>{p.mem}MB</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
