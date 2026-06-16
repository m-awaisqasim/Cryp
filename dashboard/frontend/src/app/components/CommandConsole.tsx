import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Terminal, Send } from 'lucide-react';
import { useApp } from '../context/AppContext';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const SUGGESTIONS = ['scan', 'status', 'weather', 'help'];

function TypingText({ text, onDone }: { text: string; onDone?: () => void }) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    setDisplayed('');
    setDone(false);
    let i = 0;
    const speed = Math.max(15, 35 - text.length * 0.1);
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        setDone(true);
        clearInterval(interval);
        onDone?.();
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text]);

  return (
    <span>
      {displayed}
      {!done && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.5, repeat: Infinity }}
          style={{ color: '#00f5ff' }}
        >
          ▋
        </motion.span>
      )}
    </span>
  );
}

export function CommandConsole() {
  const { wsTranscript, aiState, setScanningActive, setSettingsOpen, setAppGridOpen, wsSendCommand } = useApp();
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isTyping = aiState === 'processing' || aiState === 'responding';

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [wsTranscript, isTyping]);

  const handleSubmit = () => {
    if (!input.trim() || isTyping) return;
    const text = input.trim();
    setInput('');

    wsSendCommand(text);

    const lower = text.toLowerCase();
    if (lower.includes('scan')) setScanningActive(true);
    else if (lower.includes('settings')) setSettingsOpen(true);
    else if (lower.includes('apps')) setAppGridOpen(true);
  };

  return (
    <div className="flex flex-col h-full gap-3 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4" style={{ color: '#00f5ff' }} />
          <span style={{ ...orb, color: '#00f5ff', fontSize: '11px', letterSpacing: '0.15em' }}>
            COMMAND CONSOLE
          </span>
        </div>

      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto flex flex-col gap-3 pr-1"
        style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(0,245,255,0.2) transparent' }}
      >
        {wsTranscript.map((entry, i) => {
          const isUser = entry.text?.startsWith('You: ');
          const text = isUser ? entry.text.slice(4) : entry.text;
          return (
            <div
              key={i}
              className={`flex gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{
                    background: 'rgba(0,245,255,0.1)',
                    border: '1px solid rgba(0,245,255,0.3)',
                    boxShadow: '0 0 8px rgba(0,245,255,0.2)',
                  }}
                >
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#00f5ff' }} />
                </div>
              )}

              <div
                className="max-w-[85%] rounded-2xl px-3.5 py-2.5"
                style={
                  !isUser
                    ? {
                        background: 'rgba(0, 245, 255, 0.05)',
                        border: '1px solid rgba(0,245,255,0.2)',
                        boxShadow: '0 0 12px rgba(0,245,255,0.05)',
                        borderRadius: '4px 16px 16px 16px',
                      }
                    : {
                        background: 'rgba(168, 85, 247, 0.12)',
                        border: '1px solid rgba(168,85,247,0.3)',
                        boxShadow: '0 0 12px rgba(168,85,247,0.08)',
                        borderRadius: '16px 4px 16px 16px',
                      }
                }
              >
                {!isUser ? (
                  <p style={{ ...raj, color: 'rgba(220,240,255,0.9)', fontSize: '13px', lineHeight: '1.6' }}>
                    <TypingText text={text} />
                  </p>
                ) : (
                  <p style={{ ...raj, color: 'rgba(220,200,255,0.9)', fontSize: '13px', lineHeight: '1.6' }}>
                    {text}
                  </p>
                )}
              </div>

              {isUser && (
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{
                    background: 'rgba(168,85,247,0.15)',
                    border: '1px solid rgba(168,85,247,0.4)',
                    boxShadow: '0 0 8px rgba(168,85,247,0.2)',
                  }}
                >
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#a855f7' }} />
                </div>
              )}
            </div>
          );
        })}

        {/* Typing indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="flex gap-2 items-center"
            >
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.3)' }}
              >
                <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#00f5ff' }} />
              </div>
              <div
                className="px-3 py-2 rounded-2xl flex items-center gap-1.5"
                style={{ background: 'rgba(0,245,255,0.05)', border: '1px solid rgba(0,245,255,0.15)' }}
              >
                {[0, 1, 2].map(i => (
                  <motion.div
                    key={i}
                    animate={{ y: [-2, 2, -2] }}
                    transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ background: '#00f5ff' }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endRef} />
      </div>

      {/* Suggestions */}
      <div className="flex flex-wrap gap-1.5 flex-shrink-0">
        {SUGGESTIONS.map(s => (
          <motion.button
            key={s}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => { setInput(s); inputRef.current?.focus(); }}
            className="px-2.5 py-1 rounded-lg cursor-pointer"
            style={{
              background: 'rgba(0,245,255,0.04)',
              border: '1px solid rgba(0,245,255,0.15)',
            }}
          >
            <span style={{ ...mono, color: 'rgba(0,245,255,0.6)', fontSize: '9px' }}>{s}</span>
          </motion.button>
        ))}
      </div>

      {/* Input */}
      <div
        className="flex items-center gap-2 rounded-xl px-3 py-2.5 flex-shrink-0"
        style={{
          background: 'rgba(0,8,25,0.7)',
          border: '1px solid rgba(0,245,255,0.2)',
          boxShadow: '0 0 10px rgba(0,245,255,0.04)',
        }}
      >
        <span style={{ ...mono, color: 'rgba(0,245,255,0.5)', fontSize: '12px' }}>{'>'}</span>
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          placeholder="Enter command or speak..."
          className="flex-1 outline-none bg-transparent"
          style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}
        />
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handleSubmit}
          disabled={!input.trim() || isTyping}
          className="w-7 h-7 rounded-lg flex items-center justify-center cursor-pointer"
          style={{
            background: input.trim() && !isTyping ? 'rgba(0,245,255,0.2)' : 'rgba(0,245,255,0.04)',
            border: `1px solid ${input.trim() && !isTyping ? 'rgba(0,245,255,0.5)' : 'rgba(0,245,255,0.1)'}`,
          }}
        >
          <Send className="w-3.5 h-3.5" style={{ color: input.trim() && !isTyping ? '#00f5ff' : 'rgba(0,245,255,0.3)' }} />
        </motion.button>
      </div>
    </div>
  );
}
