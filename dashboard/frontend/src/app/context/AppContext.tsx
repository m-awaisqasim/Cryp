import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

export type AIState = 'idle' | 'listening' | 'processing' | 'responding';

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

interface AppContextType {
  aiState: AIState;
  setAiState: (s: AIState) => void;
  messages: Message[];
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
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
  refreshMemory: () => void;
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

  const refreshMemory = useCallback(async () => {
    try {
      const r = await fetch('/api/memory')
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
    } catch {}
  }, [])

  useEffect(() => { refreshMemory() }, [refreshMemory])

  const addMessage = useCallback((msg: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages(prev => [...prev, { ...msg, id: Date.now().toString(), timestamp: new Date() }]);
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
      messages, addMessage,
      notifications, addNotification, removeNotification,
      scanningActive, setScanningActive,
      appGridOpen, setAppGridOpen,
      settingsOpen, setSettingsOpen,
      leftPanel, setLeftPanel,
      rightPanel, setRightPanel,
      memories, refreshMemory,
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
