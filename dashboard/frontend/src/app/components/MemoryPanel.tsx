import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Brain, Search, Cloud, HardDrive, GitBranch, Tag, Clock, Plus, RefreshCw, AlertCircle } from 'lucide-react';
import { useApp } from '../context/AppContext';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

export function MemoryPanel() {
  const { memories, memoriesLoading, memoriesError, refreshMemory, addNotification } = useApp();
  const [query, setQuery] = useState('');
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const allTags = [...new Set(memories.flatMap(m => m.tags))];

  const filtered = memories.filter(m => {
    const matchQuery = !query || m.title.toLowerCase().includes(query.toLowerCase()) || m.content.toLowerCase().includes(query.toLowerCase());
    const matchTag = !activeTag || m.tags.includes(activeTag);
    return matchQuery && matchTag;
  });

  const fmtTime = (d: Date) => {
    const diff = Date.now() - d.getTime();
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  };

  return (
    <div className="flex flex-col h-full gap-3 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4" style={{ color: '#a855f7' }} />
          <span style={{ ...orb, color: '#a855f7', fontSize: '11px', letterSpacing: '0.15em' }}>MEMORY CORE</span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1">
            <Cloud className="w-3 h-3" style={{ color: '#00f5ff' }} />
            <span style={{ ...mono, color: 'rgba(0,245,255,0.6)', fontSize: '9px' }}>CLOUD SYNC</span>
          </div>
          <div className="flex items-center gap-1">
            <GitBranch className="w-3 h-3" style={{ color: '#22c55e' }} />
            <span style={{ ...mono, color: 'rgba(34,197,94,0.6)', fontSize: '9px' }}>GIT BACKUP</span>
          </div>
        </div>
      </div>

      {/* Sync status */}
      <div
        className="rounded-xl p-2.5 flex items-center gap-3 flex-shrink-0"
        style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(168,85,247,0.15)' }}
      >
        {[
          { icon: HardDrive, label: 'LOCAL', status: 'SYNCED', color: '#22c55e', count: memories.filter(m => m.synced).length },
          { icon: Cloud, label: 'CLOUD', status: 'ACTIVE', color: '#00f5ff', count: memories.filter(m => m.synced).length },
          { icon: GitBranch, label: 'GIT', status: 'PUSHED', color: '#a855f7', count: memories.filter(m => m.synced).length },
        ].map(({ icon: Icon, label, status, color, count }) => (
          <div key={label} className="flex items-center gap-2 flex-1">
            <Icon className="w-3 h-3" style={{ color }} />
            <div>
              <div style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '8px' }}>{label}</div>
              <div style={{ ...mono, color, fontSize: '9px' }}>{status} ({count})</div>
            </div>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="relative flex-shrink-0">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5" style={{ color: 'rgba(168,85,247,0.6)' }} />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search memories..."
          className="w-full rounded-lg pl-9 pr-4 py-2.5 outline-none"
          style={{
            background: 'rgba(0,8,25,0.6)',
            border: '1px solid rgba(168,85,247,0.2)',
            color: 'rgba(255,255,255,0.8)',
            fontFamily: 'Rajdhani, sans-serif',
            fontSize: '13px',
          }}
        />
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5 flex-shrink-0">
        {allTags.map(tag => (
          <motion.button
            key={tag}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveTag(activeTag === tag ? null : tag)}
            className="flex items-center gap-1 px-2 py-1 rounded-md cursor-pointer"
            style={{
              background: activeTag === tag ? 'rgba(168,85,247,0.25)' : 'rgba(168,85,247,0.08)',
              border: `1px solid ${activeTag === tag ? 'rgba(168,85,247,0.5)' : 'rgba(168,85,247,0.15)'}`,
            }}
          >
            <Tag className="w-2.5 h-2.5" style={{ color: '#a855f7' }} />
            <span style={{ ...mono, color: activeTag === tag ? '#a855f7' : 'rgba(168,85,247,0.7)', fontSize: '9px' }}>
              {tag}
            </span>
          </motion.button>
        ))}
      </div>

      {/* Memory timeline */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(168,85,247,0.3) transparent' }}>
        {memoriesLoading && memories.length === 0 ? (
          <div className="flex flex-col gap-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="rounded-xl p-3" style={{ background: 'rgba(0,8,25,0.5)', border: '1px solid rgba(168,85,247,0.1)' }}>
                <motion.div animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 1.5, repeat: Infinity }} className="h-3 rounded w-2/3 mb-2" style={{ background: 'rgba(168,85,247,0.15)' }} />
                <motion.div animate={{ opacity: [0.2, 0.4, 0.2] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.1 }} className="h-2 rounded w-full mb-1" style={{ background: 'rgba(168,85,247,0.08)' }} />
                <motion.div animate={{ opacity: [0.2, 0.4, 0.2] }} transition={{ duration: 1.5, repeat: Infinity, delay: 0.15 }} className="h-2 rounded w-3/4" style={{ background: 'rgba(168,85,247,0.08)' }} />
              </div>
            ))}
          </div>
        ) : memoriesError ? (
          <div className="flex flex-col items-center justify-center gap-3 py-8">
            <AlertCircle className="w-8 h-8" style={{ color: '#ef4444' }} />
            <span style={{ ...mono, color: '#ef4444', fontSize: '11px' }}>SYNC ERROR</span>
            <span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '9px', textAlign: 'center' }}>{memoriesError}</span>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={refreshMemory}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg cursor-pointer"
              style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }}
            >
              <RefreshCw className="w-3 h-3" style={{ color: '#ef4444' }} />
              <span style={{ ...mono, color: '#ef4444', fontSize: '9px' }}>RETRY</span>
            </motion.button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-8">
            <Brain className="w-8 h-8" style={{ color: 'rgba(168,85,247,0.3)' }} />
            <span style={{ ...mono, color: 'rgba(168,85,247,0.5)', fontSize: '11px' }}>NO MEMORIES FOUND</span>
            <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '9px' }}>
              {query ? `No results matching "${query}"` : 'Memory core is empty'}
            </span>
          </div>
        ) : (
          <AnimatePresence>
            {filtered.map((mem, i) => (
              <motion.div
                key={mem.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ delay: i * 0.05 }}
                className="rounded-xl p-3 cursor-pointer group"
                style={{
                  background: 'rgba(0,8,25,0.5)',
                  border: '1px solid rgba(168,85,247,0.12)',
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(168,85,247,0.35)';
                  (e.currentTarget as HTMLElement).style.boxShadow = '0 0 15px rgba(168,85,247,0.1)';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(168,85,247,0.12)';
                  (e.currentTarget as HTMLElement).style.boxShadow = 'none';
                }}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <span style={{ ...raj, color: 'rgba(255,255,255,0.85)', fontSize: '13px' }}>{mem.title}</span>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {mem.synced ? (
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#22c55e' }} />
                    ) : (
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#f59e0b' }} />
                    )}
                  </div>
                </div>
                <p style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px', lineHeight: '1.5' }} className="line-clamp-2 mb-2">
                  {mem.content}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {mem.tags.map(tag => (
                      <span
                        key={tag}
                        className="px-1.5 py-0.5 rounded"
                        style={{
                          background: 'rgba(168,85,247,0.12)',
                          border: '1px solid rgba(168,85,247,0.2)',
                          ...mono,
                          color: '#a855f7',
                          fontSize: '8px',
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-2.5 h-2.5" style={{ color: 'rgba(255,255,255,0.25)' }} />
                    <span style={{ ...mono, color: 'rgba(255,255,255,0.25)', fontSize: '9px' }}>
                      {fmtTime(mem.timestamp)}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Add memory button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => addNotification({ type: 'info', title: 'Memory Editor', message: 'Memory creation coming soon.' })}
        className="w-full py-2 rounded-xl flex items-center justify-center gap-2 cursor-pointer flex-shrink-0"
        style={{
          background: 'rgba(168,85,247,0.08)',
          border: '1px dashed rgba(168,85,247,0.3)',
        }}
      >
        <Plus className="w-3.5 h-3.5" style={{ color: '#a855f7' }} />
        <span style={{ ...mono, color: 'rgba(168,85,247,0.7)', fontSize: '10px' }}>ADD MEMORY</span>
      </motion.button>
    </div>
  );
}
