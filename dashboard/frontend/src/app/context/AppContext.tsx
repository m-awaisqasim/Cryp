import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import type { StatsData } from '../../types';

export type AIState = 'idle' | 'listening' | 'processing' | 'responding';

interface WSState {
  state: string;
  muted: boolean;
}

export interface Message {
  id: string;
  type: 'user' | 'ai';
  text: string;
  timestamp: Date;
}

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error';
  title: string;
  message: string;
}

export interface MemoryItem {
  id: string;
  title: string;
  content: string;
  tags: string[];
  timestamp: Date;
  synced: boolean;
}

import type { TranscriptEntry } from '../../types';

interface AppContextType {
  aiState: AIState;
  setAiState: (s: AIState) => void;
  messages: Message[];
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;
  notifications: Notification[];
  addNotification: (n: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  scanningActive: boolean;
  setScanningActive: (v: boolean) => void;
  appGridOpen: boolean;
  setAppGridOpen: (v: boolean) => void;
  settingsOpen: boolean;
  setSettingsOpen: (v: boolean) => void;
  leftPanel: 'monitor' | 'memory';
  setLeftPanel: (v: 'monitor' | 'memory') => void;
  rightPanel: 'console' | 'search';
  setRightPanel: (v: 'console' | 'search') => void;
  memories: MemoryItem[];
  memoriesLoading: boolean;
  memoriesError: string | null;
  refreshMemory: () => void;
  stats: StatsData;
  statsLoading: boolean;
  statsError: string | null;
  refreshStats: () => void;
  statsVersion: number;
  wsState: WSState;
  wsMuted: boolean;
  wsSendCommand: (text: string) => void;
  wsToggleMute: () => void;
  wsTranscript: TranscriptEntry[];
  wsMemoryVersion: number;
}

const AppContext = createContext<AppContextType | null>(null);

const initialMessages: Message[] = [
  {
    id: '1',
    type: 'ai',
    text: 'Cryp online. All systems operational. Say Hey Jarvis to begin, sir.',
    timestamp: new Date(Date.now() - 8000),
  },
  {
    id: '2',
    type: 'user',
    text: 'Run system diagnostics.',
    timestamp: new Date(Date.now() - 5000),
  },
  {
    id: '3',
    type: 'ai',
    text: 'Diagnostics complete. CPU: 42% nominal. Memory: 6.2GB/16GB. Network: 847ms latency. Security: All encryption layers intact. No anomalies detected.',
    timestamp: new Date(Date.now() - 3000),
  },
];

const initialMemories: MemoryItem[] = [
  {
    id: '1',
    title: 'System Configuration',
    content: 'Primary interface configured with Gemini 2.5 model. Performance mode: Ultra. Voice recognition sensitivity: 0.92.',
    tags: ['system', 'config'],
    timestamp: new Date(Date.now() - 86400000 * 2),
    synced: true,
  },
  {
    id: '2',
    title: 'Voice Command Macro',
    content: 'Created shortcut: "Deploy" = git push origin main && run deploy --production',
    tags: ['voice', 'dev'],
    timestamp: new Date(Date.now() - 86400000),
    synced: true,
  },
  {
    id: '3',
    title: 'Research: Quantum Computing',
    content: 'Summarized 14 papers on quantum decoherence and error correction. Key finding: surface codes most viable for near-term QC implementation.',
    tags: ['research', 'quantum'],
    timestamp: new Date(Date.now() - 3600000 * 5),
    synced: false,
  },
  {
    id: '4',
    title: 'API Integration Log',
    content: 'OpenWeather API integrated. Custom Search Engine ID configured. Gemini 2.5 API key stored in secure vault.',
    tags: ['api', 'config'],
    timestamp: new Date(Date.now() - 3600000 * 2),
    synced: true,
  },
  {
    id: '5',
    title: 'User Preference Update',
    content: 'Dark mode holographic theme selected. Response verbosity: detailed. Gesture sensitivity calibrated to user profile.',
    tags: ['preferences', 'ui'],
    timestamp: new Date(Date.now() - 1800000),
    synced: true,
  },
];

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [aiState, setAiState] = useState<AIState>('idle');
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [scanningActive, setScanningActive] = useState(false);
  const [appGridOpen, setAppGridOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [leftPanel, setLeftPanel] = useState<'monitor' | 'memory'>('monitor');
  const [rightPanel, setRightPanel] = useState<'console' | 'search'>('console');
  const [memories, setMemories] = useState<MemoryItem[]>(initialMemories);
  const [memoriesLoading, setMemoriesLoading] = useState(false);
  const [memoriesError, setMemoriesError] = useState<string | null>(null);

  const [stats, setStats] = useState<StatsData>({
    cpu: 0, ram: 0, disk: 0, battery_percent: null, battery_plugged: false,
    net: 0, gpu: -1, tmp: -1, uptime: 0, procCount: 0,
  });
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [statsVersion, setStatsVersion] = useState(0);

  const refreshStats = useCallback(async () => {
    setStatsLoading(true);
    setStatsError(null);
    try {
      const r = await fetch('/api/stats');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setStats(prev => ({
        ...prev, ...d,
        net: d.net !== undefined ? d.net : prev.net,
        gpu: d.gpu !== undefined ? d.gpu : prev.gpu,
        tmp: d.tmp !== undefined ? d.tmp : prev.tmp,
        uptime: d.uptime !== undefined ? d.uptime : prev.uptime,
        procCount: d.procCount !== undefined ? d.procCount : prev.procCount,
      }));
      setStatsVersion(v => v + 1);
      setStatsError(null);
      setStatsLoading(false);
    } catch (e) {
      setStatsError(e instanceof Error ? e.message : 'Failed to fetch stats');
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => { refreshStats(); const id = setInterval(refreshStats, 2000); return () => clearInterval(id); }, [refreshStats]);

  const [wsState, setWsState] = useState<WSState>({ state: 'idle', muted: false });
  const [wsTranscript, setWsTranscript] = useState<TranscriptEntry[]>([]);
  const [wsMemoryVersion, setWsMemoryVersion] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const mountedRef = useRef(true);

  const connectWS = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/cryp`;
    wsRef.current = new WebSocket(url);

    wsRef.current.onmessage = (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      if (data.type === 'state') setWsState(s => ({ ...s, state: data.state }));
      if (data.type === 'mute') setWsState(s => ({ ...s, muted: data.value }));
      if (data.type === 'transcript') {
        setWsTranscript(prev => [...prev.slice(-100), data.entry ?? data]);
      }
      if (data.type === 'memory') {
        setWsMemoryVersion(v => v + 1);
      }
      if (data.type === 'init') {
        setWsState({ state: data.state, muted: data.muted });
        setWsTranscript(data.log || []);
      }
    };

    wsRef.current.onclose = () => {
      if (mountedRef.current) setTimeout(connectWS, 1000);
    };
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connectWS();
    return () => {
      mountedRef.current = false;
      wsRef.current?.close();
    };
  }, [connectWS]);

  const wsSendCommand = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'command', text }));
    }
  }, []);

  const wsToggleMute = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'mute_toggle' }));
    }
  }, []);

  const refreshMemory = useCallback(async () => {
    setMemoriesLoading(true);
    setMemoriesError(null);
    try {
      const r = await fetch('/api/memory')
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      if (d.success && d.raw) {
        const items: MemoryItem[] = []
        for (const [cat, data] of Object.entries(d.categories)) {
          items.push({
            id: `cat-${cat}`,
            title: cat.charAt(0).toUpperCase() + cat.slice(1),
            content: `${data} stored facts`,
            tags: [cat],
            timestamp: new Date(),
            synced: true,
          })
        }
        for (const ep of d.recent_episodes || []) {
          items.push({
            id: `ep-${items.length}`,
            title: 'Session: ' + (ep.summary || '').slice(0, 40),
            content: ep.summary || '',
            tags: ['episode', ...(ep.tools_used || []).slice(0, 2)],
            timestamp: new Date(ep.timestamp || Date.now()),
            synced: true,
          })
        }
        if (items.length > 0) setMemories(items)
      }
      setMemoriesLoading(false);
    } catch (e) {
      setMemoriesError(e instanceof Error ? e.message : 'Failed to fetch memories');
      setMemoriesLoading(false);
    }
  }, [])

  useEffect(() => { refreshMemory() }, [refreshMemory])

  const addMessage = useCallback((msg: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages(prev => [...prev, { ...msg, id: Date.now().toString(), timestamp: new Date() }]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([{
      id: 'welcome',
      type: 'ai',
      text: 'Cryp online. All systems operational. Say Hey Jarvis to begin, sir.',
      timestamp: new Date(),
    }]);
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const addNotification = useCallback((n: Omit<Notification, 'id'>) => {
    const id = Date.now().toString();
    setNotifications(prev => [...prev, { ...n, id }]);
    setTimeout(() => removeNotification(id), 6000);
  }, [removeNotification]);

  return (
    <AppContext.Provider value={{
      aiState, setAiState,
      messages, addMessage, clearMessages,
      notifications, addNotification, removeNotification,
      scanningActive, setScanningActive,
      appGridOpen, setAppGridOpen,
      settingsOpen, setSettingsOpen,
      leftPanel, setLeftPanel,
      rightPanel, setRightPanel,
      memories, memoriesLoading, memoriesError, refreshMemory,
      stats, statsLoading, statsError, refreshStats, statsVersion,
      wsState, wsMuted: wsState.muted, wsSendCommand, wsToggleMute,
      wsTranscript, wsMemoryVersion,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
