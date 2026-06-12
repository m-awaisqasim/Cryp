import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Mic, MicOff, Type, Volume2 } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { useCrypWS } from '../../hooks/useCrypWS';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const BAR_COUNT = 32;

export function VoiceBar() {
  const { aiState, addMessage, messages } = useApp();
  const { sendCommand, toggleMute, muted } = useCrypWS();
  const [textMode, setTextMode] = useState(false);
  const [input, setInput] = useState('');
  const [bars, setBars] = useState(() => Array(BAR_COUNT).fill(0.15));
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number>(0);
  const oscRef = useRef<OscillatorNode | null>(null);

  const isListening = aiState === 'listening';
  const isProcessing = aiState === 'processing' || aiState === 'responding';

  // Animate waveform with Web Audio API
  useEffect(() => {
    if (!isListening && !isProcessing) {
      oscRef.current?.stop()
      oscRef.current = null
      audioCtxRef.current?.close()
      audioCtxRef.current = null
      cancelAnimationFrame(rafRef.current)
      setBars(Array(BAR_COUNT).fill(0.15))
      return
    }
    try {
      const ctx = new AudioContext()
      audioCtxRef.current = ctx
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 128
      analyserRef.current = analyser
      const osc = ctx.createOscillator()
      oscRef.current = osc
      osc.frequency.setValueAtTime(440, ctx.currentTime)
      osc.frequency.linearRampToValueAtTime(880, ctx.currentTime + 4)
      const gain = ctx.createGain()
      gain.gain.value = 0
      osc.connect(analyser)
      analyser.connect(gain)
      gain.connect(ctx.destination)
      osc.start()
      const dataArray = new Uint8Array(analyser.frequencyBinCount)
      const draw = () => {
        analyser.getByteTimeDomainData(dataArray)
        const newBars = Array(BAR_COUNT).fill(0).map((_, i) => {
          const idx = Math.floor(i * dataArray.length / BAR_COUNT)
          const v = (dataArray[idx] - 128) / 128
          return Math.max(0.08, Math.abs(v) + (isListening ? 0.3 : 0.15))
        })
        setBars(newBars)
        rafRef.current = requestAnimationFrame(draw)
      }
      draw()
    } catch {
      if (intervalRef.current) clearInterval(intervalRef.current)
      intervalRef.current = setInterval(() => {
        setBars(Array(BAR_COUNT).fill(0).map(() => 0.15 + Math.random() * 0.4))
      }, 80)
    }
    return () => {
      cancelAnimationFrame(rafRef.current)
      oscRef.current?.stop()
      audioCtxRef.current?.close().catch(() => {})
    }
  }, [isListening, isProcessing])

  const latestUserMsg = [...messages].reverse().find(m => m.type === 'user');
  const transcript = aiState === 'listening' ? 'Listening...' : (latestUserMsg?.text || '');

  const toggleListening = () => {
    toggleMute();
  };

  const handleTextSubmit = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim()) {
      addMessage({ type: 'user', text: input.trim() });
      sendCommand(input.trim());
      setInput('');
    }
  };

  const stateColor = {
    idle: '#00f5ff',
    listening: '#22c55e',
    processing: '#f59e0b',
    responding: '#a855f7',
  }[aiState];

  return (
    <div
      className="fixed left-0 right-0 flex items-center px-6 gap-4"
      style={{
        bottom: 72,
        height: 72,
        zIndex: 60,
        background: 'rgba(1, 8, 20, 0.85)',
        backdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(0, 245, 255, 0.1)',
        borderBottom: '1px solid rgba(0, 245, 255, 0.06)',
      }}
    >
      {/* Mode toggle */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setTextMode(!textMode)}
        className="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer flex-shrink-0"
        style={{
          background: textMode ? 'rgba(168,85,247,0.15)' : 'rgba(0,245,255,0.05)',
          border: `1px solid ${textMode ? 'rgba(168,85,247,0.4)' : 'rgba(0,245,255,0.15)'}`,
        }}
      >
        {textMode ? (
          <Type className="w-4 h-4" style={{ color: '#a855f7' }} />
        ) : (
          <Volume2 className="w-4 h-4" style={{ color: '#00f5ff' }} />
        )}
      </motion.button>

      {/* Voice control */}
      <AnimatePresence mode="wait">
        {!textMode ? (
          <motion.div
            key="voice"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex items-center gap-4"
          >
            {/* Waveform */}
            <div className="flex-1 flex items-center justify-center gap-0.5 h-12 overflow-hidden">
              {bars.map((h, i) => (
                <motion.div
                  key={i}
                  animate={{ scaleY: h }}
                  transition={{ duration: 0.08, ease: 'linear' }}
                  className="rounded-full origin-center flex-shrink-0"
                  style={{
                    width: 2.5,
                    height: '100%',
                    background: isListening
                      ? `rgba(34, 197, 94, ${0.4 + h * 0.6})`
                      : isProcessing
                      ? `rgba(245, 158, 11, ${0.3 + h * 0.5})`
                      : `rgba(0, 245, 255, ${0.1 + h * 0.3})`,
                    boxShadow: isListening ? `0 0 3px rgba(34,197,94,${h * 0.6})` : 'none',
                  }}
                />
              ))}
            </div>

            {/* Transcript */}
            <AnimatePresence>
              {transcript && (
                <motion.div
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 4 }}
                  className="flex-shrink-0 max-w-48"
                >
                  <span style={{ ...raj, color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>{transcript}</span>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ) : (
          <motion.div
            key="text"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex items-center gap-2"
          >
            <div
              className="flex-1 flex items-center gap-2 rounded-xl px-4 py-2"
              style={{ background: 'rgba(0,8,25,0.6)', border: '1px solid rgba(168,85,247,0.2)' }}
            >
              <span style={{ ...mono, color: 'rgba(168,85,247,0.5)', fontSize: '12px' }}>{'>'}</span>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleTextSubmit}
                placeholder="Type a command..."
                className="flex-1 outline-none bg-transparent"
                style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mic / Status indicator */}
      <div className="flex flex-col items-center gap-1 flex-shrink-0">
        {/* State label */}
        <span style={{ ...mono, color: stateColor, fontSize: '8px', letterSpacing: '0.1em' }}>
          {aiState.toUpperCase()}
        </span>

        {/* Mic button */}
        <motion.button
          onClick={toggleListening}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.9 }}
          className="relative w-12 h-12 rounded-full flex items-center justify-center cursor-pointer"
          style={{
            background: isListening
              ? 'rgba(34, 197, 94, 0.15)'
              : isProcessing
              ? 'rgba(245, 158, 11, 0.1)'
              : 'rgba(0, 245, 255, 0.08)',
            border: `2px solid ${stateColor}`,
            boxShadow: `0 0 20px ${stateColor}40, 0 0 40px ${stateColor}15`,
          }}
        >
          {/* Pulse rings when listening */}
          {isListening && (
            <>
              <motion.div
                animate={{ scale: [1, 1.8, 1], opacity: [0.4, 0, 0.4] }}
                transition={{ duration: 1.2, repeat: Infinity }}
                className="absolute inset-0 rounded-full"
                style={{ border: `2px solid rgba(34,197,94,0.5)` }}
              />
              <motion.div
                animate={{ scale: [1, 2.4, 1], opacity: [0.2, 0, 0.2] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0.3 }}
                className="absolute inset-0 rounded-full"
                style={{ border: `1px solid rgba(34,197,94,0.3)` }}
              />
            </>
          )}

          {isListening ? (
            <Mic className="w-5 h-5" style={{ color: '#22c55e' }} />
          ) : isProcessing ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              <div className="w-4 h-4 rounded-full border-2 border-transparent" style={{ borderTopColor: '#f59e0b', borderRightColor: '#f59e0b40' }} />
            </motion.div>
          ) : (
            <Mic className="w-5 h-5" style={{ color: '#00f5ff' }} />
          )}
        </motion.button>
      </div>
    </div>
  );
}
