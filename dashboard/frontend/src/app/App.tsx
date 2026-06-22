import React, { Suspense, lazy } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Brain, Terminal, Search, Activity } from 'lucide-react';

import { useApp } from './context/AppContext';
import { Background } from './components/Background';
import { TopBar } from './components/TopBar';
import { AICore } from './components/AICore';
import { SystemMonitor } from './components/SystemMonitor';
import { MemoryPanel } from './components/MemoryPanel';
import { CommandConsole } from './components/CommandConsole';
import { SearchPanel } from './components/SearchPanel';
import { AppDock } from './components/AppDock';
import { NotificationSystem } from './components/NotificationSystem';

const SettingsPanel = lazy(() => import('./components/SettingsPanel').then(m => ({ default: m.SettingsPanel })));
const ScanningPanel = lazy(() => import('./components/ScanningPanel').then(m => ({ default: m.ScanningPanel })));
const TradingPanel = lazy(() => import('./components/TradingPanel').then(m => ({ default: m.TradingPanel })));
const AppGrid = lazy(() => import('./components/AppGrid').then(m => ({ default: m.AppGrid })));

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

const glassPanel = (accent = '#00f5ff') => ({
  background: 'rgba(0, 10, 28, 0.65)',
  backdropFilter: 'blur(20px)',
  border: `1px solid ${accent}20`,
  borderRadius: '16px',
  boxShadow: `0 0 30px rgba(0,0,0,0.4), inset 0 0 20px rgba(0,0,0,0.3)`,
});

function PanelTab({
  id, label, icon: Icon, active, color, onClick,
}: {
  id: string; label: string; icon: React.ElementType;
  active: boolean; color: string; onClick: () => void;
}) {
  const dimColor = color + '18';
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 rounded-xl cursor-pointer"
      style={{
        background: active ? `${color}20` : dimColor,
        border: `1px solid ${active ? `${color}50` : `${color}30`}`,
        transition: 'all 0.2s',
        boxShadow: active ? `0 0 8px ${color}20` : 'none',
      }}
    >
      <Icon className="w-3.5 h-3.5" style={{ color: active ? color : `${color}99` }} />
      <span style={{ ...mono, color: active ? color : `${color}aa`, fontSize: '9px', letterSpacing: '0.08em' }}>
        {label}
      </span>
    </motion.button>
  );
}

export function MainLayout() {
  const { leftPanel, setLeftPanel, rightPanel, setRightPanel } = useApp();

  return (
    <div
      className="fixed inset-0 flex flex-col overflow-hidden"
      style={{ fontFamily: 'Rajdhani, sans-serif' }}
    >
      <Background />

      {/* Top Bar */}
      <TopBar />

      {/* Main 3-column layout */}
      <div
        className="flex flex-1 gap-4 px-4 overflow-hidden"
        style={{ marginTop: 56, marginBottom: 0 }}
      >
        {/* LEFT PANEL */}
        <div
          className="w-72 flex-shrink-0 flex flex-col overflow-hidden pt-4 pb-2"
          style={{ maxHeight: 'calc(100vh - 230px)' }}
        >
          {/* Panel content with embedded tabs */}
          <div
            className="flex-1 p-4 overflow-hidden flex flex-col min-h-0"
            style={glassPanel(leftPanel === 'monitor' ? '#00f5ff' : '#a855f7')}
          >
            {/* Tabs inside the panel */}
            <div className="flex gap-2 mb-3 flex-shrink-0">
              <PanelTab
                id="monitor" label="MONITOR" icon={Activity}
                active={leftPanel === 'monitor'} color="#00f5ff"
                onClick={() => setLeftPanel('monitor')}
              />
              <PanelTab
                id="memory" label="MEMORY" icon={Brain}
                active={leftPanel === 'memory'} color="#a855f7"
                onClick={() => setLeftPanel('memory')}
              />
            </div>

            <AnimatePresence mode="wait">
              {leftPanel === 'monitor' ? (
                <motion.div key="monitor" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 min-h-0">
                  <SystemMonitor />
                </motion.div>
              ) : (
                <motion.div key="memory" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 min-h-0">
                  <MemoryPanel />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* CENTER — AI Core */}
        <div className="flex-1 flex flex-col items-center overflow-hidden -mt-4">
          {/* AI Core orb */}
          <div className="flex items-center justify-center w-full flex-shrink-0">
            <AICore />
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="w-72 flex-shrink-0 flex flex-col overflow-hidden pt-4 pb-2"
             style={{ maxHeight: 'calc(100vh - 130px)' }}>
          {/* Panel content with embedded tabs */}
          <div
            className="flex-1 p-4 overflow-hidden flex flex-col"
            style={glassPanel(rightPanel === 'console' ? '#00f5ff' : '#0ea5e9')}
          >
            {/* Tabs inside the panel */}
            <div className="flex gap-2 mb-3 flex-shrink-0">
              <PanelTab
                id="console" label="CONSOLE" icon={Terminal}
                active={rightPanel === 'console'} color="#00f5ff"
                onClick={() => setRightPanel('console')}
              />
              <PanelTab
                id="search" label="SEARCH" icon={Search}
                active={rightPanel === 'search'} color="#0ea5e9"
                onClick={() => setRightPanel('search')}
              />
            </div>

            <AnimatePresence mode="wait">
              {rightPanel === 'console' ? (
                <motion.div key="console" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 min-h-0">
                  <CommandConsole />
                </motion.div>
              ) : (
                <motion.div key="search" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 min-h-0">
                  <SearchPanel />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* App Dock */}
      <AppDock />

      {/* Overlays */}
      <Suspense fallback={
        <div className="fixed inset-0 flex items-center justify-center" style={{ zIndex: 150, background: 'rgba(0,4,12,0.9)' }}>
          <div className="flex flex-col items-center gap-3">
            <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }} className="w-8 h-8 rounded-full border-2 border-cyan-400 border-t-transparent" />
            <span style={{ fontFamily: 'Share Tech Mono, monospace', color: 'rgba(0,245,255,0.7)', fontSize: '11px' }}>LOADING...</span>
          </div>
        </div>
      }>
        <ScanningPanel />
        <AppGrid />
        <SettingsPanel />
        <TradingPanel />
      </Suspense>
      <NotificationSystem />
    </div>
  );
}



