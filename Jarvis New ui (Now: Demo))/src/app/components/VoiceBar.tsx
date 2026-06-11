import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Mic, MicOff, Type, Volume2 } from 'lucide-react';
import { useApp } from '../context/AppContext';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const BAR_COUNT = 32;

export function VoiceBar() {
  const { aiState, setAiState, addMessage, addNotification, setScanningActive, setSettingsOpen, setAppGridOpen } = useApp();
  const [textMode, setTextMode] = useState(false);
  const [input, setInput] = useState('');
  const [bars, setBars] = useState(() => Array(BAR_COUNT).fill(0.15));
  const [transcript, setTranscript] = useState('');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isListening = aiState === 'listening';
  const isProcessing = aiState === 'processing' || aiState === 'responding';

  // Animate waveform
  useEffect(() => {
    if (isListening) {
      intervalRef.current = setInterval(() => {
        setBars(Array(BAR_COUNT).fill(0).map((_, i) => {
          const center = BAR_COUNT / 2;
          const dist = Math.abs(i - center) / center;
          const base = 0.2 + Math.random() * 0.7 * (1 - dist * 0.5);
          return base;
        }));
      }, 80);
    } else if (isProcessing) {
      intervalRef.current = setInterval(() => {
        setBars(Array(BAR_COUNT).fill(0).map((_, i) => {
          const t = Date.now() / 200;
          return 0.2 + 0.4 * Math.abs(Math.sin(t + i * 0.3));
        }));
      }, 50);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
      setBars(Array(BAR_COUNT).fill(0.15));
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [aiState]);

  const MOCK_VOICE_COMMANDS = [
    'Run system diagnostics',
    'Show weather forecast',
    'Open settings panel',
    'Scan environment',
    'Deploy application',
    'Check memory status',
  ];

  const toggleListening = () => {
    if (isListening) {
      // Simulate voice command processing
      const cmd = MOCK_VOICE_COMMANDS[Math.floor(Math.random() * MOCK_VOICE_COMMANDS.length)];
      setTranscript(cmd);
      setAiState('processing');
      addMessage({ type: 'user', text: cmd });
      setTimeout(() => {
        setAiState('responding');
        const resp = `Voice command received: "${cmd}". Processing complete. Command executed successfully.`;
        addMessage({ type: 'ai', text: resp });
        if (cmd.toLowerCase().includes('scan')) setScanningActive(true);
        if (cmd.toLowerCase().includes('settings')) setSettingsOpen(true);
        setTimeout(() => {
          setAiState('idle');
          setTranscript('');
        }, 2000);
      }, 1500);
    } else if (!isProcessing) {
      setAiState('listening');
      setTranscript('');
      addNotification({ type: 'info', title: 'Voice Active', message: 'Listening for your command...' });
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
