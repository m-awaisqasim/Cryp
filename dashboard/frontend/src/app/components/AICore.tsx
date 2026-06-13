import { motion, AnimatePresence } from 'motion/react';
import { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useStats } from '../../hooks/useStats';
import { useCrypWS } from '../../hooks/useCrypWS';
import { Send, MicOff } from 'lucide-react';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const stateConfig = {
  idle: {
    color: '#00f5ff',
    glow: 'rgba(0, 245, 255, 0.5)',
    label: 'STANDBY',
    subLabel: 'CRYP CORE ONLINE',
    pulseSpeed: 3,
    ringColor: 'rgba(0,245,255,0.4)',
  },
  listening: {
    color: '#22c55e',
    glow: 'rgba(34, 197, 94, 0.6)',
    label: 'LISTENING',
    subLabel: 'VOICE RECOGNITION ACTIVE',
    pulseSpeed: 0.8,
    ringColor: 'rgba(34,197,94,0.5)',
  },
  processing: {
    color: '#f59e0b',
    glow: 'rgba(245, 158, 11, 0.6)',
    label: 'PROCESSING',
    subLabel: 'NEURAL ANALYSIS IN PROGRESS',
    pulseSpeed: 0.4,
    ringColor: 'rgba(245,158,11,0.5)',
  },
  responding: {
    color: '#a855f7',
    glow: 'rgba(168, 85, 247, 0.6)',
    label: 'RESPONDING',
    subLabel: 'GENERATING OUTPUT STREAM',
    pulseSpeed: 0.6,
    ringColor: 'rgba(168,85,247,0.5)',
  },
};

function Ring({
  size, thickness, color, duration, direction = 1, dashed = false, tilt = 0,
}: {
  size: number; thickness: number; color: string; duration: number;
  direction?: number; dashed?: boolean; tilt?: number;
}) {
  return (
    <motion.div
      animate={{ rotate: direction * 360 }}
      transition={{ duration, repeat: Infinity, ease: 'linear' }}
      className="absolute rounded-full"
      style={{
        width: size, height: size,
        left: '50%', top: '50%',
        marginLeft: -size / 2, marginTop: -size / 2,
        border: `${thickness}px ${dashed ? 'dashed' : 'solid'} ${color}`,
        boxShadow: `0 0 8px ${color.replace('0.', '0.3')}`,
        transform: `rotateX(${tilt}deg)`,
        transformStyle: 'preserve-3d',
      }}
    />
  );
}

function ExpandedOverlay({ onClose, muted }: { onClose: () => void; muted: boolean }) {
  const { aiState, addMessage, addNotification } = useApp();
  const cfg = stateConfig[aiState];
  const activeCfg = muted
    ? { ...cfg, color: '#94a3b8', glow: 'rgba(148,163,184,0.5)', ringColor: 'rgba(148,163,184,0.4)', pulseSpeed: 3 }
    : cfg;
  const [cmd, setCmd] = useState('');

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const send = () => {
    if (!cmd.trim()) return;
    addMessage({ type: 'user', text: cmd.trim() });
    addNotification({ type: 'info', title: 'Command Sent', message: `Executing: ${cmd.trim()}` });
    setCmd('');
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.2 } }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,5,20,0.94)', backdropFilter: 'blur(30px)' }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.85, opacity: 0 }}
        className="flex flex-col items-center gap-8"
        onClick={e => e.stopPropagation()}
      >
        <div className="relative" style={{ width: 440, height: 440 }}>
          <Ring size={400} thickness={1} color="rgba(0,245,255,0.08)" duration={50} dashed />
          <Ring size={360} thickness={1} color={`${activeCfg.color}20`} duration={24} direction={1} tilt={15} />
          <Ring size={310} thickness={1.5} color={`${activeCfg.color}30`} duration={16} direction={-1} tilt={-10} />
          <Ring size={250} thickness={1} color={`${activeCfg.color}50`} duration={10} direction={1} />
          <motion.div
            animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: activeCfg.pulseSpeed * 2, repeat: Infinity }}
            className="absolute rounded-full"
            style={{
              width: 220, height: 220,
              left: '50%', top: '50%',
              marginLeft: -110, marginTop: -110,
              border: `1px solid ${activeCfg.color}`,
            }}
          />
          <motion.div
            animate={muted ? { opacity: [1, 0.2, 1] } : {}}
            transition={muted ? { duration: 2, repeat: Infinity } : {}}
            className="absolute rounded-full flex items-center justify-center"
            style={{
              width: 200, height: 200,
              left: '50%', top: '50%',
              marginLeft: -100, marginTop: -100,
              background: `radial-gradient(circle at 35% 35%, ${activeCfg.color}25 0%, rgba(0,5,20,0.9) 60%, rgba(0,2,10,1) 100%)`,
              border: `2px solid ${activeCfg.color}`,
              boxShadow: `0 0 40px ${activeCfg.glow}, 0 0 80px ${activeCfg.glow.replace('0.5', '0.2')}, inset 0 0 40px ${activeCfg.glow.replace('0.5', '0.15')}`,
            }}
          >
            <motion.div
              animate={{ scale: [1, 1.12, 1], opacity: [0.8, 1, 0.8] }}
              transition={{ duration: activeCfg.pulseSpeed, repeat: Infinity }}
              className="rounded-full flex items-center justify-center flex-col gap-1"
              style={{
                width: 150, height: 150,
                background: `radial-gradient(circle, ${activeCfg.color}20 0%, transparent 70%)`,
              }}
            >
              <motion.div
                animate={{ rotate: aiState === 'processing' ? 360 : 0 }}
                transition={{ duration: 1.5, repeat: aiState === 'processing' ? Infinity : 0, ease: 'linear' }}
              >
                {muted ? (
                  <MicOff className="w-6 h-6" style={{ color: activeCfg.color }} />
                ) : (
                  <svg width="44" height="44" viewBox="0 0 36 36" fill="none">
                    <circle cx="18" cy="18" r="16" stroke={activeCfg.color} strokeWidth="1" opacity="0.5" />
                    <circle cx="18" cy="18" r="10" stroke={activeCfg.color} strokeWidth="1.5" opacity="0.8" />
                    <circle cx="18" cy="18" r="4" fill={activeCfg.color} />
                    <line x1="18" y1="2" x2="18" y2="8" stroke={activeCfg.color} strokeWidth="1.5" />
                    <line x1="18" y1="28" x2="18" y2="34" stroke={activeCfg.color} strokeWidth="1.5" />
                    <line x1="2" y1="18" x2="8" y2="18" stroke={activeCfg.color} strokeWidth="1.5" />
                    <line x1="28" y1="18" x2="34" y2="18" stroke={activeCfg.color} strokeWidth="1.5" />
                  </svg>
                )}
              </motion.div>
              <span style={{ ...orb, color: activeCfg.color, fontSize: muted ? '9px' : '10px', letterSpacing: '0.1em', opacity: 0.9 }}>
                {muted ? 'MUTED' : 'Cryp'}
              </span>
            </motion.div>
          </motion.div>
        </div>

        <div className="flex items-center gap-3">
          <input
            value={cmd}
            onChange={e => setCmd(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') send(); }}
            placeholder="Type a command..."
            autoFocus
            className="w-80 px-4 py-3 rounded-xl outline-none"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(0,245,255,0.25)',
              color: '#fff',
              fontFamily: 'Share Tech Mono, monospace',
              fontSize: '13px',
            }}
          />
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={send}
            className="px-4 py-3 rounded-xl flex items-center gap-2 cursor-pointer"
            style={{
              background: 'rgba(0,245,255,0.12)',
              border: '1px solid rgba(0,245,255,0.35)',
              color: '#00f5ff',
            }}
          >
            <Send className="w-3.5 h-3.5" />
            <span style={{ ...mono, fontSize: '10px', letterSpacing: '0.08em' }}>SEND</span>
          </motion.button>
        </div>

        <span style={{ ...raj, color: 'rgba(255,255,255,0.3)', fontSize: '11px' }}>
          Click outside or press <span style={{ ...mono, color: 'rgba(255,255,255,0.5)' }}>ESC</span> to close
        </span>
      </motion.div>
    </motion.div>
  );
}

export function AICore() {
  const { aiState } = useApp();
  const { stats } = useStats();
  const { ram, tmp } = stats;
  const { muted, toggleMute } = useCrypWS();

  const [expanded, setExpanded] = useState(false);

  const cfg = stateConfig[aiState];

  const activeCfg = muted
    ? { ...cfg, color: '#94a3b8', glow: 'rgba(148,163,184,0.5)', ringColor: 'rgba(148,163,184,0.4)', pulseSpeed: 3 }
    : cfg;

  const pressure = Math.min(1, Math.max(0, (tmp - 40) / 50)) * 0.6
                + Math.min(1, Math.max(0, (ram - 50) / 50)) * 0.4;

  const pressureGlow = pressure > 0.5
    ? `rgba(239, 68, 68, ${(pressure - 0.5) * 0.4})`
    : cfg.glow;

  return (
    <>
      <motion.div
        className="flex flex-col items-center justify-center gap-6 select-none"
        style={{ perspective: '600px' }}
        drag="y"
        dragConstraints={{ top: -150, bottom: 0 }}
        dragSnapToOrigin
        onDragEnd={(_, info) => { if (info.offset.y < -100) setExpanded(true); }}
        whileDrag={{ scale: 0.97, opacity: 0.85 }}
      >
        {/* Orb container */}
        <div className="relative" style={{ width: 380, height: 380 }}>
          {/* Outer dashed ring */}
          <Ring size={340} thickness={1} color="rgba(0,245,255,0.1)" duration={40} dashed />

          {/* Decorative orbit rings */}
          <Ring size={300} thickness={1} color={activeCfg.ringColor.replace('0.5', '0.2')} duration={20} direction={1} tilt={20} />
          <Ring size={260} thickness={1.5} color={activeCfg.ringColor.replace('0.5', '0.3')} duration={14} direction={-1} tilt={-15} />
          <Ring size={210} thickness={1} color={activeCfg.ringColor} duration={8} direction={1} />

          {/* Pulse wave rings */}
          <motion.div
            animate={{ scale: [1, 1.4, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: activeCfg.pulseSpeed * 2, repeat: Infinity }}
            className="absolute rounded-full"
            style={{
              width: 180, height: 180,
              left: '50%', top: '50%',
              marginLeft: -90, marginTop: -90,
              border: `1px solid ${activeCfg.color}`,
            }}
          />
          <motion.div
            animate={{ scale: [1, 1.6, 1], opacity: [0.2, 0, 0.2] }}
            transition={{ duration: activeCfg.pulseSpeed * 2, repeat: Infinity, delay: 0.4 }}
            className="absolute rounded-full"
            style={{
              width: 180, height: 180,
              left: '50%', top: '50%',
              marginLeft: -90, marginTop: -90,
              border: `1px solid ${activeCfg.color}`,
            }}
          />

          {/* Core Orb — clickable */}
          <motion.div
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleMute}
            animate={muted ? { opacity: [1, 0.25, 1] } : {}}
            transition={muted ? { duration: 2, repeat: Infinity } : {}}
            className="absolute rounded-full flex items-center justify-center cursor-pointer"
            style={{
              width: 160, height: 160,
              left: '50%', top: '50%',
              marginLeft: -80, marginTop: -80,
              background: `radial-gradient(circle at 35% 35%, ${activeCfg.color}25 0%, rgba(0,5,20,0.9) 60%, rgba(0,2,10,1) 100%)`,
              border: `2px solid ${activeCfg.color}`,
              boxShadow: `0 0 30px ${activeCfg.glow}, 0 0 60px ${activeCfg.glow.replace('0.5', '0.2')}, inset 0 0 30px ${activeCfg.glow.replace('0.5', '0.15')}`,
              transition: 'box-shadow 0.5s, border-color 0.5s, background 0.5s',
            }}
          >
            <motion.div
              animate={{ scale: [1, 1.15, 1], opacity: [0.8, 1, 0.8] }}
              transition={{ duration: activeCfg.pulseSpeed, repeat: Infinity }}
              className="rounded-full flex items-center justify-center flex-col gap-1"
              style={{
                width: 120, height: 120,
                background: `radial-gradient(circle, ${activeCfg.color}20 0%, transparent 70%)`,
              }}
            >
              <motion.div
                animate={{ rotate: aiState === 'processing' ? 360 : 0 }}
                transition={{ duration: 1.5, repeat: aiState === 'processing' ? Infinity : 0, ease: 'linear' }}
              >
                {muted ? (
                  <MicOff className="w-5 h-5" style={{ color: activeCfg.color }} />
                ) : (
                  <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                    <circle cx="18" cy="18" r="16" stroke={activeCfg.color} strokeWidth="1" opacity="0.5" />
                    <circle cx="18" cy="18" r="10" stroke={activeCfg.color} strokeWidth="1.5" opacity="0.8" />
                    <circle cx="18" cy="18" r="4" fill={activeCfg.color} />
                    <line x1="18" y1="2" x2="18" y2="8" stroke={activeCfg.color} strokeWidth="1.5" />
                    <line x1="18" y1="28" x2="18" y2="34" stroke={activeCfg.color} strokeWidth="1.5" />
                    <line x1="2" y1="18" x2="8" y2="18" stroke={activeCfg.color} strokeWidth="1.5" />
                    <line x1="28" y1="18" x2="34" y2="18" stroke={activeCfg.color} strokeWidth="1.5" />
                  </svg>
                )}
              </motion.div>
              <span style={{ ...orb, color: activeCfg.color, fontSize: muted ? '7px' : '8px', letterSpacing: '0.1em', textAlign: 'center', opacity: 0.9 }}>
                {muted ? 'MUTED' : 'Cryp'}
              </span>
            </motion.div>
          </motion.div>
        </div>

        {/* State label */}
        <div className="flex flex-col items-center gap-2">
          <AnimatePresence mode="wait">
            <motion.div
              key={aiState}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col items-center gap-1"
            >
              <span
                style={{
                  ...orb, color: activeCfg.color, fontSize: '16px',
                  letterSpacing: '0.25em',
                  textShadow: `0 0 15px ${activeCfg.glow}`,
                }}
              >
                {activeCfg.label}
              </span>
              <span style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '10px', letterSpacing: '0.12em' }}>
                {cfg.subLabel}
              </span>
            </motion.div>
          </AnimatePresence>

          <motion.p
            animate={{ opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 3, repeat: Infinity }}
            style={{ ...raj, color: 'rgba(0,245,255,0.4)', fontSize: '11px', marginTop: 4 }}
          >
            CLICK ORB TO {muted ? 'UNMUTE' : 'MUTE'} · DRAG UP TO EXPAND
          </motion.p>
        </div>
      </motion.div>

      {/* Full-screen overlay */}
      <AnimatePresence>
        {expanded && <ExpandedOverlay onClose={() => setExpanded(false)} muted={muted} />}
      </AnimatePresence>
    </>
  );
}
