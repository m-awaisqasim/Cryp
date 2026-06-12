import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Search, Globe, FileText, Clock, TrendingUp, X, ExternalLink } from 'lucide-react';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const TRENDING = ['cpu', 'memory', 'network', 'error', 'warning'];

const typeColors: Record<string, string> = {
  info: '#00f5ff',
  warning: '#f59e0b',
  error: '#ef4444',
  debug: '#a855f7',
};

export function SearchPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<{ title: string; snippet: string; source: string; type: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'all' | 'info' | 'docs'>('all');
  const [history, setHistory] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem('cryp_search_history') || '[]'); }
    catch { return ['system', 'memory', 'error']; }
  });

  const search = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); return; }
    setLoading(true);
    try {
      const r = await fetch(`/api/logs?lines=200`)
      const d = await r.json()
      const lines: string[] = d.lines || []
      const ql = q.toLowerCase()
      const matched = lines
        .filter(l => l.toLowerCase().includes(ql))
        .slice(0, 20)
        .map(l => {
          const type = l.includes('ERROR') || l.includes('error') ? 'error'
            : l.includes('WARN') || l.includes('warning') ? 'warning'
            : l.includes('DEBUG') ? 'debug' : 'info'
          const snippet = l.length > 120 ? l.slice(0, 120) + '...' : l
          return {
            title: l.split('|')[0]?.trim()?.slice(0, 50) || 'Log entry',
            snippet,
            source: new Date().toLocaleTimeString(),
            type,
          }
        })
      setResults(matched.length > 0 ? matched : [{ title: 'No Results', snippet: `No log entries matching "${q}"`, source: '', type: 'info' }])
      setHistory(h => {
        const next = [q, ...h.filter(x => x !== q)].slice(0, 5)
        try { localStorage.setItem('cryp_search_history', JSON.stringify(next)) } catch {}
        return next
      })
    } catch {
      setResults([{ title: 'Search Error', snippet: 'Failed to fetch logs from backend', source: '', type: 'error' }])
    }
    setLoading(false)
  }, [])

  const handleSubmit = () => {
    if (query.trim()) search(query);
  };

  return (
    <div className="flex flex-col h-full gap-3 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4" style={{ color: '#0ea5e9' }} />
          <span style={{ ...orb, color: '#0ea5e9', fontSize: '11px', letterSpacing: '0.15em' }}>DATA SEARCH</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#22c55e', boxShadow: '0 0 4px #22c55e' }} />
          <span style={{ ...mono, color: 'rgba(34,197,94,0.7)', fontSize: '9px' }}>LOG SEARCH</span>
        </div>
      </div>

      {/* Search bar */}
      <div
        className="flex items-center gap-2 rounded-xl px-3 py-2.5 flex-shrink-0"
        style={{
          background: 'rgba(0,8,25,0.7)',
          border: '1px solid rgba(14,165,233,0.25)',
        }}
      >
        <Search className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'rgba(14,165,233,0.6)' }} />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          placeholder="Search the datastream..."
          className="flex-1 outline-none bg-transparent"
          style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}
        />
        {query && (
          <button onClick={() => { setQuery(''); setResults([]); }} className="cursor-pointer">
            <X className="w-3.5 h-3.5" style={{ color: 'rgba(255,255,255,0.3)' }} />
          </button>
        )}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handleSubmit}
          className="px-2.5 py-1.5 rounded-lg cursor-pointer"
          style={{ background: 'rgba(14,165,233,0.2)', border: '1px solid rgba(14,165,233,0.4)' }}
        >
          <span style={{ ...mono, color: '#0ea5e9', fontSize: '10px' }}>GO</span>
        </motion.button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-shrink-0">
        {[
          { id: 'all', icon: Globe, label: 'ALL' },
          { id: 'info', icon: Globe, label: 'SYSTEM' },
          { id: 'docs', icon: FileText, label: 'DOCS' },
        ].map(({ id, icon: Icon, label }) => (
          <motion.button
            key={id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setTab(id as typeof tab)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg cursor-pointer"
            style={{
              background: tab === id ? 'rgba(14,165,233,0.15)' : 'rgba(14,165,233,0.04)',
              border: `1px solid ${tab === id ? 'rgba(14,165,233,0.4)' : 'rgba(14,165,233,0.12)'}`,
            }}
          >
            <Icon className="w-3 h-3" style={{ color: tab === id ? '#0ea5e9' : 'rgba(14,165,233,0.4)' }} />
            <span style={{ ...mono, color: tab === id ? '#0ea5e9' : 'rgba(14,165,233,0.4)', fontSize: '9px' }}>
              {label}
            </span>
          </motion.button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(14,165,233,0.2) transparent' }}>
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col gap-2">
              {[1, 2, 3].map(i => (
                <div key={i} className="rounded-xl p-3" style={{ background: 'rgba(0,8,25,0.5)', border: '1px solid rgba(14,165,233,0.1)' }}>
                  <div className="flex gap-2 mb-2">
                    <motion.div animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 1.5, repeat: Infinity }} className="h-3 rounded" style={{ background: 'rgba(14,165,233,0.2)', width: '60%' }} />
                    <motion.div animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }} className="h-3 rounded" style={{ background: 'rgba(14,165,233,0.1)', width: '20%' }} />
                  </div>
                  <motion.div animate={{ opacity: [0.2, 0.4, 0.2] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.1 }} className="h-2 rounded mb-1" style={{ background: 'rgba(14,165,233,0.15)', width: '90%' }} />
                  <motion.div animate={{ opacity: [0.2, 0.4, 0.2] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.15 }} className="h-2 rounded" style={{ background: 'rgba(14,165,233,0.1)', width: '75%' }} />
                </div>
              ))}
            </motion.div>
          ) : results.length > 0 ? (
            <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-2">
              <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '9px' }}>
                {results.length} RESULTS FOR "{query.toUpperCase()}"
              </span>
              {results.map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="rounded-xl p-3 group cursor-pointer"
                  style={{
                    background: 'rgba(0,8,25,0.5)',
                    border: '1px solid rgba(14,165,233,0.1)',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(14,165,233,0.3)';
                    (e.currentTarget as HTMLElement).style.boxShadow = '0 0 12px rgba(14,165,233,0.06)';
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(14,165,233,0.1)';
                    (e.currentTarget as HTMLElement).style.boxShadow = 'none';
                  }}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span style={{ ...raj, color: 'rgba(220,240,255,0.9)', fontSize: '13px' }}>{r.title}</span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span
                        className="px-1.5 py-0.5 rounded"
                        style={{
                          background: `${typeColors[r.type]}15`,
                          border: `1px solid ${typeColors[r.type]}30`,
                          ...mono,
                          color: typeColors[r.type],
                          fontSize: '8px',
                        }}
                      >
                        {r.type.toUpperCase()}
                      </span>
                      <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: '#0ea5e9' }} />
                    </div>
                  </div>
                  <p style={{ ...raj, color: 'rgba(255,255,255,0.45)', fontSize: '11px', lineHeight: '1.5' }}>
                    {r.snippet}
                  </p>
                  <div className="flex items-center gap-1 mt-1.5">
                    <Globe className="w-2.5 h-2.5" style={{ color: 'rgba(14,165,233,0.5)' }} />
                    <span style={{ ...mono, color: 'rgba(14,165,233,0.6)', fontSize: '9px' }}>{r.source}</span>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-3">
              {/* Trending */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-3 h-3" style={{ color: 'rgba(14,165,233,0.6)' }} />
                  <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '9px' }}>TRENDING IN DATASTREAM</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {TRENDING.map(t => (
                    <motion.button
                      key={t}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => { setQuery(t); search(t); }}
                      className="px-2.5 py-1.5 rounded-lg cursor-pointer"
                      style={{ background: 'rgba(14,165,233,0.06)', border: '1px solid rgba(14,165,233,0.15)' }}
                    >
                      <span style={{ ...mono, color: 'rgba(14,165,233,0.7)', fontSize: '10px' }}>{t}</span>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* History */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-3 h-3" style={{ color: 'rgba(255,255,255,0.3)' }} />
                  <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '9px' }}>RECENT SEARCHES</span>
                </div>
                {history.map(h => (
                  <motion.button
                    key={h}
                    whileHover={{ x: 4 }}
                    onClick={() => { setQuery(h); search(h); }}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer text-left"
                    style={{ background: 'transparent' }}
                  >
                    <Clock className="w-3 h-3" style={{ color: 'rgba(255,255,255,0.2)' }} />
                    <span style={{ ...raj, color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>{h}</span>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
