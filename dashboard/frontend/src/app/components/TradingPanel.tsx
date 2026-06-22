import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  X, TrendingUp, DollarSign, Percent, BarChart3,
  ArrowUpRight, ArrowDownRight, Download, Upload,
  Clock, AlertCircle, FileDown, Tag, Edit3, Loader2, ChevronDown,
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, ResponsiveContainer, Tooltip, ReferenceLine, Cell,
} from 'recharts';
import { useApp } from '../context/AppContext';

const orb = { fontFamily: 'Orbitron, sans-serif' };
const mono = { fontFamily: 'Share Tech Mono, monospace' };
const raj = { fontFamily: 'Rajdhani, sans-serif' };

interface Position {
  symbol: string; side: string; entry_price: number; current_price: number | null;
  unrealized_pnl_usd: number | null; holding_hours: number | null; remaining_size: number;
}

interface ClosedTrade {
  symbol: string; side: string; realized_pnl_usd: number; realized_r: number | null;
  setup: string; closed_at: string; holding_hours: number | null; tags?: string[];
}

interface EquityPoint { date: string; cumulative_pnl: number }
interface DrawdownPoint { date: string; drawdown: number }
interface RollingWinratePoint { date: string; win_rate: number; window: number }
interface MonthlyPnlPoint { month: string; pnl: number }
interface SetupBreakdownItem { setup: string; trades: number; win_rate: number; avg_r: number | null; total_pnl: number }
interface StatsStreaks { current_streak: number; current_streak_type: string | null; max_win_streak: number; max_loss_streak: number }

interface TradingSummary {
  open_positions: Position[];
  recent_closed: ClosedTrade[];
  equity_curve: EquityPoint[];
  drawdown_curve: DrawdownPoint[];
  rolling_winrate: RollingWinratePoint[];
  monthly_pnl: MonthlyPnlPoint[];
  setup_breakdown: SetupBreakdownItem[];
  stats: {
    total_trades: number; win_rate: number | null; avg_r: number | null;
    total_pnl: number; max_drawdown: number;
    profit_factor: number | null; expectancy: number | null;
    streaks: StatsStreaks;
  };
  exposure: { open_count: number; total_notional: number; total_risk: number };
  daily_activity: { date: string; trades: number; pnl: number }[];
  time_analysis: { by_weekday: any[]; by_hour: any[] };
}

const emptySummary: TradingSummary = {
  open_positions: [], recent_closed: [], equity_curve: [],
  drawdown_curve: [], rolling_winrate: [], monthly_pnl: [], setup_breakdown: [],
  stats: { total_trades: 0, win_rate: null, avg_r: null, total_pnl: 0, max_drawdown: 0, profit_factor: null, expectancy: null, streaks: { current_streak: 0, current_streak_type: null, max_win_streak: 0, max_loss_streak: 0 } },
  exposure: { open_count: 0, total_notional: 0, total_risk: 0 },
  daily_activity: [],
  time_analysis: { by_weekday: [], by_hour: [] },
};

function fmtUsd(n: number | null | undefined) {
  if (n === null || n === undefined) return '—';
  const abs = Math.abs(n);
  const s = abs >= 1000000
    ? `$${(abs / 1000000).toFixed(2)}M`
    : abs >= 1000
      ? `$${(abs / 1000).toFixed(1)}K`
      : `$${n.toFixed(2)}`;
  return n < 0 ? `-${s}` : s;
}

function StatCard({ label, value, color, prefix }: {
  label: string; value: string; color: string; prefix?: string;
}) {
  return (
    <div className="rounded-xl p-3 flex-1" style={{
      background: 'rgba(0,8,20,0.5)', border: `1px solid ${color}15`,
    }}>
      <div style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '8px', letterSpacing: '0.1em', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ ...raj, color, fontSize: '18px', fontWeight: 600 }}>
        {prefix}{value}
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: 'rgba(0,8,20,0.6)', border: '1px solid rgba(0,245,255,0.2)',
  borderRadius: '6px', padding: '6px 10px', color: 'rgba(255,255,255,0.8)',
  fontSize: '12px', width: '100%', outline: 'none', fontFamily: 'Share Tech Mono, monospace',
};
const labelStyle: React.CSSProperties = {
  fontFamily: 'Share Tech Mono, monospace', fontSize: '10px',
  color: 'rgba(255,255,255,0.35)', letterSpacing: '0.05em',
  marginBottom: '4px', display: 'block',
};

export function TradingPanel() {
  const { tradingOpen, setTradingOpen, addNotification } = useApp();
  const fileRef = useRef<HTMLInputElement>(null);
  const [summary, setSummary] = useState<TradingSummary>(emptySummary);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    try {
      const r = await fetch('/api/trading/summary');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      if (d.error) throw new Error(d.error);
      setSummary(d);
      setError(null);
      setLoading(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch');
      setLoading(false);
    }
  }, []);

  const handleImport = useCallback(async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    try {
      const r = await fetch('/api/trading/import', { method: 'POST', body: form });
      const data = await r.json();
      if (r.ok && !data.error) {
        addNotification({ type: 'success', title: 'Import Complete', message: `Imported ${data.imported} trade${data.imported !== 1 ? 's' : ''}.` });
        if (data.skipped > 0) {
          addNotification({ type: 'warning', title: 'Skipped Rows', message: `${data.skipped} row${data.skipped !== 1 ? 's were' : ' was'} skipped.` });
        }
        fetchSummary();
      } else {
        addNotification({ type: 'error', title: 'Import Failed', message: data.error || `HTTP ${r.status}` });
      }
    } catch (e) {
      addNotification({ type: 'error', title: 'Import Error', message: e instanceof Error ? e.message : 'Unknown error' });
    }
  }, [addNotification, fetchSummary]);

  useEffect(() => {
    if (!tradingOpen) return;
    fetchSummary();
    const id = setInterval(fetchSummary, 10000);
    return () => clearInterval(id);
  }, [tradingOpen, fetchSummary]);

  const [selectedTrade, setSelectedTrade] = useState<any | null>(null);
  const [filterSetup, setFilterSetup] = useState<string | null>(null);
  const [filterTag, setFilterTag] = useState<string | null>(null);
  const [hoveredCell, setHoveredCell] = useState<{ date: string; trades: number; pnl: number; x: number; y: number } | null>(null);

  // Entry modal
  const [entryModalOpen, setEntryModalOpen] = useState(false);
  const [entryForm, setEntryForm] = useState({
    symbol: '', side: 'long', entry_price: '', stop_loss: '',
    take_profit: '', size: '', setup: '', tags: '', reasoning: '', fee: '', notes: '',
  });
  const [entryError, setEntryError] = useState<string | null>(null);
  const [entryLoading, setEntryLoading] = useState(false);
  const [accountSize, setAccountSize] = useState('');
  const [riskPct, setRiskPct] = useState('1');
  const [calOpen, setCalOpen] = useState(false);

  const computedSize = useMemo(() => {
    const acc = parseFloat(accountSize);
    const ep = parseFloat(entryForm.entry_price);
    const sl = parseFloat(entryForm.stop_loss);
    const rp = parseFloat(riskPct);
    if (!acc || !ep || !sl || !rp || ep === sl) return null;
    const riskAmount = acc * (rp / 100);
    const perUnitRisk = Math.abs(ep - sl);
    return (riskAmount / perUnitRisk).toFixed(6);
  }, [accountSize, riskPct, entryForm.entry_price, entryForm.stop_loss]);

  // Close modal
  const [closeModalTrade, setCloseModalTrade] = useState<any | null>(null);
  const [closeForm, setCloseForm] = useState({ exit_price: '', size: '', fee: '', notes: '' });
  const [closeError, setCloseError] = useState<string | null>(null);
  const [closeLoading, setCloseLoading] = useState(false);
  const [livePrices, setLivePrices] = useState<Record<string, number>>({});

  const previewPnl = useMemo(() => {
    const ep = parseFloat(closeForm.exit_price);
    if (!closeModalTrade) return null;
    const sz = parseFloat(closeForm.size) || closeModalTrade.remaining_size;
    if (!ep || !sz) return null;
    const dir = closeModalTrade.side === 'long' ? 1 : -1;
    return ((ep - closeModalTrade.entry_price) * dir * sz).toFixed(2);
  }, [closeForm.exit_price, closeForm.size, closeModalTrade]);

  // Edit modal
  const [editModalTrade, setEditModalTrade] = useState<any | null>(null);
  const [editForm, setEditForm] = useState({
    stop_loss: '', take_profit: '', setup: '', tags: '', reasoning: '', notes: '',
  });
  const [editError, setEditError] = useState<string | null>(null);
  const [editLoading, setEditLoading] = useState(false);

  const fetchLivePrices = useCallback(async () => {
    try {
      const r = await fetch('/api/trading/prices');
      if (!r.ok) return;
      const d = await r.json();
      if (d.error) return;
      const out: Record<string, number> = {};
      if (d.bitcoin) out['BTC'] = d.bitcoin.usd;
      if (d.ethereum) out['ETH'] = d.ethereum.usd;
      setLivePrices(out);
    } catch { /* ignore */ }
  }, []);

  // Reset entry form on close
  useEffect(() => {
    if (!entryModalOpen) {
      setEntryForm({ symbol: '', side: 'long', entry_price: '', stop_loss: '', take_profit: '', size: '', setup: '', tags: '', reasoning: '', fee: '', notes: '' });
      setEntryError(null);
      setAccountSize('');
      setRiskPct('1');
      setCalOpen(false);
    }
  }, [entryModalOpen]);

  // Reset close form on close
  useEffect(() => {
    if (!closeModalTrade) {
      setCloseForm({ exit_price: '', size: '', fee: '', notes: '' });
      setCloseError(null);
    }
  }, [closeModalTrade]);

  // Pre-populate edit form
  useEffect(() => {
    if (editModalTrade) {
      setEditForm({
        stop_loss: editModalTrade.stop_loss ?? '',
        take_profit: editModalTrade.take_profit ?? '',
        setup: editModalTrade.setup ?? '',
        tags: (editModalTrade.tags ?? []).join(', '),
        reasoning: editModalTrade.reasoning ?? '',
        notes: editModalTrade.notes ?? '',
      });
      setEditError(null);
    }
  }, [editModalTrade]);

  const validateEntry = () => {
    if (!entryForm.symbol.trim()) return 'Symbol is required.';
    if (!['long', 'short'].includes(entryForm.side)) return 'Side must be long or short.';
    const ep = parseFloat(entryForm.entry_price);
    const sz = parseFloat(entryForm.size);
    if (!ep || ep <= 0) return 'Entry price must be a positive number.';
    if (!sz || sz <= 0) return 'Size must be a positive number.';
    const sl = parseFloat(entryForm.stop_loss);
    if (entryForm.stop_loss && !isNaN(sl)) {
      if (entryForm.side === 'long' && sl >= ep) return 'Stop loss must be below entry price for a long.';
      if (entryForm.side === 'short' && sl <= ep) return 'Stop loss must be above entry price for a short.';
    }
    return null;
  };

  const submitEntry = async () => {
    const err = validateEntry();
    if (err) { setEntryError(err); return; }
    setEntryLoading(true);
    setEntryError(null);
    try {
      const r = await fetch('/api/trading/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...entryForm,
          symbol: entryForm.symbol.trim().toUpperCase(),
          entry_price: parseFloat(entryForm.entry_price),
          size: parseFloat(entryForm.size),
          stop_loss: entryForm.stop_loss ? parseFloat(entryForm.stop_loss) : null,
          take_profit: entryForm.take_profit ? parseFloat(entryForm.take_profit) : null,
          fee: entryForm.fee ? parseFloat(entryForm.fee) : 0,
        }),
      });
      const data = await r.json();
      if (!data.success) {
        setEntryError(data.message);
      } else {
        addNotification({ type: 'success', title: 'Trade Logged', message: data.message });
        setEntryModalOpen(false);
        fetchSummary();
      }
    } catch {
      setEntryError('Network error — check the Cryp backend.');
    } finally {
      setEntryLoading(false);
    }
  };

  const submitClose = async () => {
    if (!closeModalTrade) return;
    setCloseLoading(true);
    setCloseError(null);
    try {
      const r = await fetch('/api/trading/close', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trade_id: closeModalTrade.id,
          exit_price: parseFloat(closeForm.exit_price),
          size: closeForm.size ? parseFloat(closeForm.size) : null,
          fee: closeForm.fee ? parseFloat(closeForm.fee) : 0,
          notes: closeForm.notes || null,
        }),
      });
      const data = await r.json();
      if (!data.success) {
        setCloseError(data.message);
      } else {
        addNotification({ type: 'success', title: 'Trade Closed', message: data.message });
        setCloseModalTrade(null);
        fetchSummary();
      }
    } catch {
      setCloseError('Network error — check the Cryp backend.');
    } finally {
      setCloseLoading(false);
    }
  };

  const submitEdit = async () => {
    if (!editModalTrade) return;
    setEditLoading(true);
    setEditError(null);
    try {
      const r = await fetch('/api/trading/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trade_id: editModalTrade.id,
          stop_loss: editForm.stop_loss ? parseFloat(editForm.stop_loss) : null,
          take_profit: editForm.take_profit ? parseFloat(editForm.take_profit) : null,
          setup: editForm.setup || null,
          tags: editForm.tags || null,
          reasoning: editForm.reasoning || null,
          notes: editForm.notes || null,
        }),
      });
      const data = await r.json();
      if (!data.success) {
        setEditError(data.message);
      } else {
        addNotification({ type: 'success', title: 'Trade Updated', message: data.message });
        setEditModalTrade(null);
        fetchSummary();
      }
    } catch {
      setEditError('Network error — check the Cryp backend.');
    } finally {
      setEditLoading(false);
    }
  };

  const allSetups = [...new Set(
    (summary?.recent_closed ?? [])
      .map((t: any) => t.setup)
      .filter((s: any) => s && s !== 'unspecified')
  )] as string[];
  const allTags = [...new Set(
    (summary?.recent_closed ?? []).flatMap((t: any) => t.tags ?? [])
  )] as string[];

  const hasFilters = allSetups.length > 0 || allTags.length > 0;

  const filteredClosed = (summary?.recent_closed ?? []).filter((t: any) => {
    const setupMatch = !filterSetup || t.setup === filterSetup;
    const tagMatch = !filterTag || (t.tags ?? []).includes(filterTag);
    return setupMatch && tagMatch;
  });
  const filteredOpen = (summary?.open_positions ?? []).filter((t: any) => {
    const setupMatch = !filterSetup || t.setup === filterSetup;
    const tagMatch = !filterTag || (t.tags ?? []).includes(filterTag);
    return setupMatch && tagMatch;
  });

  const s = summary.stats;
  const e = summary.exposure;

  return (
    <AnimatePresence>
      {tradingOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 flex items-center justify-center"
          style={{ zIndex: 180, background: 'rgba(0, 4, 12, 0.92)', backdropFilter: 'blur(12px)' }}
        >
          <motion.div
            initial={{ scale: 0.92, y: 16 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.92, y: 16 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="w-full max-w-4xl mx-6 rounded-2xl overflow-hidden flex flex-col"
            style={{
              maxHeight: '90vh',
              background: 'rgba(0, 10, 25, 0.95)',
              border: '1px solid rgba(0,245,255,0.2)',
              boxShadow: '0 0 60px rgba(0,245,255,0.1)',
            }}
          >
            {/* Header */}
              <div className="flex items-center justify-between px-8 py-5 flex-shrink-0" style={{ borderBottom: '1px solid rgba(0,245,255,0.12)' }}>
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5" style={{ color: '#00f5ff' }} />
                  <h2 style={{ ...orb, color: '#00f5ff', fontSize: '16px', letterSpacing: '0.2em', margin: 0 }}>
                    TRADING
                  </h2>
                  <span style={{ ...mono, color: 'rgba(0,245,255,0.3)', fontSize: '9px', marginTop: 4 }}>
                    QUANT INTELLIGENCE
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => setEntryModalOpen(true)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl cursor-pointer"
                    style={{ background: 'rgba(0,245,255,0.12)', border: '1px solid rgba(0,245,255,0.3)' }}
                  >
                    <TrendingUp className="w-3 h-3" style={{ color: '#00f5ff' }} />
                    <span style={{ ...mono, color: '#00f5ff', fontSize: '9px' }}>LOG TRADE</span>
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1, rotate: 90 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setTradingOpen(false)}
                    className="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer"
                    style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}
                  >
                    <X className="w-5 h-5" style={{ color: '#ef4444' }} />
                  </motion.button>
                </div>
              </div>

            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(0,245,255,0.2) transparent' }}>
              {loading ? (
                <div className="flex items-center justify-center py-16">
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }} className="w-8 h-8 rounded-full border-2 border-cyan-400 border-t-transparent" />
                </div>
              ) : error ? (
                <div className="flex flex-col items-center gap-3 py-16">
                  <AlertCircle className="w-10 h-10" style={{ color: '#ef4444' }} />
                  <span style={{ ...mono, color: '#ef4444', fontSize: '11px' }}>{error}</span>
                </div>
              ) : s.total_trades === 0 && e.open_count === 0 ? (
                <div className="flex flex-col items-center justify-center gap-3 py-16">
                  <TrendingUp className="w-12 h-12" style={{ color: 'rgba(0,245,255,0.2)' }} />
                  <span style={{ ...orb, color: 'rgba(0,245,255,0.4)', fontSize: '13px', letterSpacing: '0.15em' }}>NO TRADES YET</span>
                  <span style={{ ...mono, color: 'rgba(255,255,255,0.25)', fontSize: '10px' }}>
                    Log your first trade with the trade_journal tool to see data here.
                  </span>
                </div>
              ) : (
                <>
                  {/* Stats row 1 */}
                  <div className="flex gap-3">
                    <StatCard label="WIN RATE" value={s.win_rate !== null ? `${s.win_rate}%` : '—'} color="#22c55e" />
                    <StatCard label="AVG R" value={s.avg_r !== null ? `${s.avg_r}R` : '—'} color="#a855f7" />
                    <StatCard label="TOTAL P&L" value={fmtUsd(s.total_pnl)} color={s.total_pnl >= 0 ? '#22c55e' : '#ef4444'} />
                    <StatCard label="MAX DD" value={fmtUsd(s.max_drawdown)} color="#f59e0b" />
                  </div>
                  {/* Stats row 2 */}
                  <div className="flex gap-3">
                    <StatCard label="PROFIT FACTOR" value={s.profit_factor !== null ? `${s.profit_factor}` : '∞'} color="#06b6d4" />
                    <StatCard label="EXPECTANCY" value={s.expectancy !== null ? `${s.expectancy}R` : '—'} color="#a855f7" />
                    <StatCard label="STREAK" value={s.streaks.current_streak_type ? `${s.streaks.current_streak} ${s.streaks.current_streak_type}s` : '—'} color={s.streaks.current_streak_type === 'win' ? '#22c55e' : '#ef4444'} />
                    <StatCard label="MAX WIN/LOSS" value={`${s.streaks.max_win_streak} / ${s.streaks.max_loss_streak}`} color="#f59e0b" />
                  </div>

                  {/* Exposure line */}
                  <div className="rounded-xl p-3 flex items-center gap-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(0,245,255,0.1)' }}>
                    <DollarSign className="w-4 h-4" style={{ color: '#00f5ff' }} />
                    <span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '11px' }}>
                      {e.open_count} open position{ e.open_count !== 1 ? 's' : ''} —
                      <span style={{ color: '#00f5ff' }}> {fmtUsd(e.total_notional)}</span> notional,
                      <span style={{ color: '#f59e0b' }}> {fmtUsd(e.total_risk)}</span> at risk to stops
                    </span>
                  </div>

                  {/* Filter bar */}
                  {hasFilters && (
                    <div className="rounded-xl p-3 flex flex-col gap-2" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(0,245,255,0.1)' }}>
                      <div style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px', letterSpacing: '0.1em' }}>FILTER</div>
                      {allSetups.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span style={{ ...mono, color: 'rgba(255,255,255,0.25)', fontSize: '8px' }}>Setup:</span>
                          <span onClick={() => setFilterSetup(null)}
                            className="px-2 py-0.5 rounded cursor-pointer"
                            style={{ ...mono, fontSize: '8px', background: !filterSetup ? 'rgba(0,245,255,0.15)' : 'rgba(255,255,255,0.05)', color: !filterSetup ? '#00f5ff' : 'rgba(255,255,255,0.4)', border: `1px solid ${!filterSetup ? 'rgba(0,245,255,0.3)' : 'rgba(255,255,255,0.08)'}` }}>
                            All
                          </span>
                          {allSetups.map(s => (
                            <span key={s} onClick={() => setFilterSetup(filterSetup === s ? null : s)}
                              className="px-2 py-0.5 rounded cursor-pointer"
                              style={{ ...mono, fontSize: '8px', background: filterSetup === s ? 'rgba(0,245,255,0.15)' : 'rgba(255,255,255,0.05)', color: filterSetup === s ? '#00f5ff' : 'rgba(255,255,255,0.4)', border: `1px solid ${filterSetup === s ? 'rgba(0,245,255,0.3)' : 'rgba(255,255,255,0.08)'}` }}>
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                      {allTags.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span style={{ ...mono, color: 'rgba(255,255,255,0.25)', fontSize: '8px' }}>Tag:</span>
                          <span onClick={() => setFilterTag(null)}
                            className="px-2 py-0.5 rounded cursor-pointer"
                            style={{ ...mono, fontSize: '8px', background: !filterTag ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.05)', color: !filterTag ? '#f59e0b' : 'rgba(255,255,255,0.4)', border: `1px solid ${!filterTag ? 'rgba(245,158,11,0.3)' : 'rgba(255,255,255,0.08)'}` }}>
                            All
                          </span>
                          {allTags.map(t => (
                            <span key={t} onClick={() => setFilterTag(filterTag === t ? null : t)}
                              className="px-2 py-0.5 rounded cursor-pointer"
                              style={{ ...mono, fontSize: '8px', background: filterTag === t ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.05)', color: filterTag === t ? '#f59e0b' : 'rgba(255,255,255,0.4)', border: `1px solid ${filterTag === t ? 'rgba(245,158,11,0.3)' : 'rgba(255,255,255,0.08)'}` }}>
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                      {(filterSetup || filterTag) && (
                        <div className="flex items-center gap-2">
                          <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>
                            Showing {filteredClosed.length + filteredOpen.length} of {summary.recent_closed.length + summary.open_positions.length} trades
                          </span>
                          <span onClick={() => { setFilterSetup(null); setFilterTag(null); }}
                            className="px-2 py-0.5 rounded cursor-pointer"
                            style={{ ...mono, fontSize: '8px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.25)' }}>
                            Clear
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Open positions table */}
                  {filteredOpen.length > 0 && (
                    <div>
                      <div style={{ ...mono, color: '#00f5ff', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>OPEN POSITIONS</div>
                      <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(0,245,255,0.1)' }}>
                        <table className="w-full" style={{ borderCollapse: 'collapse' }}>
                          <thead>
                            <tr style={{ background: 'rgba(0,245,255,0.05)' }}>
                              {['Symbol', 'Side', 'Entry', 'Current', 'Unrealized', 'Holding', ''].map(h => (
                                <th key={h} style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px', padding: '8px 12px', textAlign: 'left', letterSpacing: '0.1em' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {filteredOpen.map((p, i) => {
                              const pnl = p.unrealized_pnl_usd;
                              const color = pnl !== null ? (pnl >= 0 ? '#22c55e' : '#ef4444') : 'rgba(255,255,255,0.4)';
                              const Icon = pnl !== null && pnl >= 0 ? ArrowUpRight : ArrowDownRight;
                              return (
                                <tr key={i} onClick={() => setSelectedTrade(p)} className="cursor-pointer" style={{ borderTop: '1px solid rgba(0,245,255,0.06)' }}>
                                  <td style={{ padding: '8px 12px' }}><span style={{ ...raj, color: '#00f5ff', fontSize: '13px' }}>{p.symbol}</span></td>
                                  <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: p.side === 'long' ? '#22c55e' : '#ef4444', fontSize: '10px' }}>{p.side}</span></td>
                                  <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>${p.entry_price?.toLocaleString()}</span></td>
                                  <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>{p.current_price ? `$${p.current_price.toLocaleString()}` : '—'}</span></td>
                                  <td style={{ padding: '8px 12px' }}>
                                    <span className="flex items-center gap-1" style={{ ...mono, color, fontSize: '10px' }}>
                                      {pnl !== null && <Icon className="w-3 h-3" />}{pnl !== null ? fmtUsd(pnl) : '—'}
                                    </span>
                                  </td>
                                  <td style={{ padding: '8px 12px' }}>
                                    <span className="flex items-center gap-1" style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '10px' }}>
                                      <Clock className="w-2.5 h-2.5" />{p.holding_hours !== null ? `${p.holding_hours}h` : '—'}
                                    </span>
                                  </td>
                                  <td style={{ padding: '8px 12px' }} onClick={e => e.stopPropagation()}>
                                    <div className="flex items-center gap-1">
                                      <motion.button
                                        whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
                                        onClick={() => { setCloseModalTrade(p); fetchLivePrices(); }}
                                        className="flex items-center justify-center w-6 h-6 rounded cursor-pointer"
                                        style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}
                                        title="Close trade"
                                      >
                                        <X className="w-3 h-3" style={{ color: '#ef4444' }} />
                                      </motion.button>
                                      <motion.button
                                        whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
                                        onClick={() => setEditModalTrade(p)}
                                        className="flex items-center justify-center w-6 h-6 rounded cursor-pointer"
                                        style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.25)' }}
                                        title="Edit trade"
                                      >
                                        <Edit3 className="w-3 h-3" style={{ color: '#00f5ff' }} />
                                      </motion.button>
                                    </div>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Equity curve */}
                  {summary.equity_curve.length > 1 && (
                    <div>
                      <div style={{ ...mono, color: '#a855f7', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>EQUITY CURVE</div>
                      <div className="rounded-xl p-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(168,85,247,0.15)' }}>
                        <ResponsiveContainer width="100%" height={180}>
                          <LineChart data={summary.equity_curve}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,85,247,0.08)" />
                            <XAxis dataKey="date" tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} tickFormatter={v => v?.slice(5) || ''} />
                            <YAxis tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} tickFormatter={v => `$${v}`} />
                            <Tooltip
                              contentStyle={{ background: 'rgba(0,10,25,0.95)', border: '1px solid rgba(168,85,247,0.3)', borderRadius: 8, fontFamily: 'Share Tech Mono', fontSize: 10 }}
                              labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                              formatter={(val: number) => [`$${val.toFixed(2)}`, 'P&L']}
                            />
                            <Line type="monotone" dataKey="cumulative_pnl" stroke="#a855f7" strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Rolling win rate */}
                  {summary.rolling_winrate.length >= 2 && (
                    <div>
                      <div style={{ ...mono, color: '#22c55e', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>ROLLING WIN RATE ({summary.rolling_winrate[summary.rolling_winrate.length - 1]?.window || 20}-TRADE)</div>
                      <div className="rounded-xl p-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(34,197,94,0.15)' }}>
                        <ResponsiveContainer width="100%" height={140}>
                          <LineChart data={summary.rolling_winrate}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(34,197,94,0.08)" />
                            <XAxis dataKey="date" tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} tickFormatter={v => v?.slice(5) || ''} />
                            <YAxis domain={[0, 100]} tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} tickFormatter={v => `${v}%`} />
                            <ReferenceLine y={50} stroke="rgba(255,255,255,0.15)" strokeDasharray="4 4" />
                            <Tooltip
                              contentStyle={{ background: 'rgba(0,10,25,0.95)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 8, fontFamily: 'Share Tech Mono', fontSize: 10 }}
                              labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                              formatter={(val: number, _name: string, props: any) => [`${val}% (last ${props.payload?.window || 20} trades)`, 'Win Rate']}
                            />
                            <Line type="monotone" dataKey="win_rate" stroke="#22c55e" strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Drawdown chart */}
                  {summary.drawdown_curve.length >= 2 && summary.drawdown_curve.some(d => d.drawdown > 0) && (
                    <div>
                      <div style={{ ...mono, color: '#ef4444', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>DRAWDOWN</div>
                      <div className="rounded-xl p-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(239,68,68,0.15)' }}>
                        <ResponsiveContainer width="100%" height={140}>
                          <AreaChart data={summary.drawdown_curve}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(239,68,68,0.08)" />
                            <XAxis dataKey="date" tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} tickFormatter={v => v?.slice(5) || ''} />
                            <YAxis tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} tickFormatter={v => `$${v}`} />
                            <Tooltip
                              contentStyle={{ background: 'rgba(0,10,25,0.95)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, fontFamily: 'Share Tech Mono', fontSize: 10 }}
                              labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                              formatter={(val: number) => [`$${val.toFixed(2)}`, 'Drawdown']}
                            />
                            <defs>
                              <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
                                <stop offset="100%" stopColor="#ef4444" stopOpacity={0.02} />
                              </linearGradient>
                            </defs>
                            <Area type="monotone" dataKey="drawdown" stroke="#ef4444" strokeWidth={1.5} fill="url(#ddGrad)" dot={false} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Monthly P&L bar chart */}
                  {summary.monthly_pnl.length >= 1 && (
                    <div>
                      <div style={{ ...mono, color: '#a855f7', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>MONTHLY P&L</div>
                      <div className="rounded-xl p-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(168,85,247,0.15)' }}>
                        <ResponsiveContainer width="100%" height={140}>
                          <BarChart data={summary.monthly_pnl}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,85,247,0.08)" />
                            <XAxis dataKey="month" tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} />
                            <YAxis tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} tickFormatter={v => `$${v}`} />
                            <Tooltip
                              contentStyle={{ background: 'rgba(0,10,25,0.95)', border: '1px solid rgba(168,85,247,0.3)', borderRadius: 8, fontFamily: 'Share Tech Mono', fontSize: 10 }}
                              labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                              formatter={(val: number) => [`$${val.toFixed(2)}`, 'P&L']}
                            />
                            <Bar dataKey="pnl" radius={[3, 3, 0, 0]}>
                              {summary.monthly_pnl.map((entry, i) => (
                                <Cell key={i} fill={entry.pnl >= 0 ? '#22c55e' : '#ef4444'} fillOpacity={0.7} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Calendar heatmap */}
                  {summary.daily_activity.length > 0 ? (() => {
                    const today = new Date();
                    const startDate = new Date(today);
                    startDate.setDate(today.getDate() - 363);
                    const dayOfWeek = startDate.getDay();
                    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
                    startDate.setDate(startDate.getDate() - daysToMonday);

                    const lookup: Record<string, { trades: number; pnl: number }> = {};
                    summary.daily_activity.forEach(d => { lookup[d.date] = d; });

                    const cells: { date: string; week: number; day: number }[] = [];
                    const cursor = new Date(startDate);
                    const monthLabels: { index: number; name: string }[] = [];
                    let prevMonth = -1;
                    for (let i = 0; i < 364; i++) {
                      const ds = cursor.toISOString().slice(0, 10);
                      cells.push({ date: ds, week: Math.floor(i / 7), day: i % 7 });
                      if (cursor.getMonth() !== prevMonth) {
                        monthLabels.push({ index: i % 7 === 0 ? i : i - (i % 7), name: cursor.toLocaleString('default', { month: 'short' }) });
                        prevMonth = cursor.getMonth();
                      }
                      cursor.setDate(cursor.getDate() + 1);
                    }

                    const cellSize = 10;
                    const cellGap = 2;
                    const step = cellSize + cellGap;
                    const svgW = 52 * step + 4;
                    const svgH = 7 * step + 26;

                    return (
                      <div>
                        <div style={{ ...mono, color: '#00f5ff', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>TRADING ACTIVITY</div>
                        <div className="rounded-xl p-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(0,245,255,0.1)', position: 'relative' }}>
                          <svg width={svgW} height={svgH} style={{ display: 'block' }}>
                            {/* Month labels */}
                            {monthLabels.map((m, i) => (
                              <text key={i} x={m.index / 7 * step + 2} y={10} style={{ fontFamily: 'Share Tech Mono', fontSize: 7, fill: 'rgba(255,255,255,0.3)' }}>{m.name}</text>
                            ))}
                            {/* Day labels */}
                            {['Mon', 'Wed', 'Fri'].map((d, i) => (
                              <text key={d} x={0} y={26 + [0, 2, 4][i] * step + 8} style={{ fontFamily: 'Share Tech Mono', fontSize: 6, fill: 'rgba(255,255,255,0.2)' }}>{d}</text>
                            ))}
                            {/* Cells */}
                            {cells.map(c => {
                              const d = lookup[c.date];
                              const x = c.week * step + 24;
                              const y = c.day * step + 22;
                              let fill = 'rgba(255,255,255,0.04)';
                              if (d) {
                                if (d.pnl > 0) {
                                  const op = d.trades >= 3 ? 1 : d.trades >= 2 ? 0.7 : 0.4;
                                  fill = `rgba(34,197,94,${op})`;
                                } else if (d.pnl < 0) {
                                  const op = d.trades >= 3 ? 1 : d.trades >= 2 ? 0.7 : 0.4;
                                  fill = `rgba(239,68,68,${op})`;
                                } else {
                                  fill = 'rgba(255,255,255,0.15)';
                                }
                              }
                              return (
                                <rect key={c.date} x={x} y={y} width={cellSize} height={cellSize} rx={2} fill={fill}
                                  onMouseEnter={e => {
                                    if (!d) return;
                                    const rect = (e.target as SVGRectElement).getBoundingClientRect();
                                    setHoveredCell({ date: c.date, trades: d.trades, pnl: d.pnl, x: rect.left, y: rect.top - 8 });
                                  }}
                                  onMouseLeave={() => setHoveredCell(null)}
                                />
                              );
                            })}
                          </svg>
                          {/* Tooltip */}
                          {hoveredCell && (
                            <div style={{ position: 'fixed', left: hoveredCell.x, top: hoveredCell.y, transform: 'translate(-50%, -100%)', pointerEvents: 'none', zIndex: 999, background: 'rgba(0,10,25,0.95)', border: '1px solid rgba(0,245,255,0.3)', borderRadius: 6, padding: '6px 10px', fontFamily: 'Share Tech Mono', fontSize: 9 }}>
                              <div style={{ color: 'rgba(255,255,255,0.6)' }}>{hoveredCell.date}</div>
                              <div style={{ color: 'rgba(255,255,255,0.5)' }}>{hoveredCell.trades} trade{hoveredCell.trades !== 1 ? 's' : ''}</div>
                              <div style={{ color: hoveredCell.pnl >= 0 ? '#22c55e' : '#ef4444' }}>{hoveredCell.pnl >= 0 ? '+' : ''}{fmtUsd(hoveredCell.pnl)}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })() : (
                    <div>
                      <div style={{ ...mono, color: '#00f5ff', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>TRADING ACTIVITY</div>
                      <div className="rounded-xl p-4 flex items-center justify-center" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(0,245,255,0.1)' }}>
                        <span style={{ ...mono, color: 'rgba(255,255,255,0.25)', fontSize: '9px' }}>No closed trades yet — activity will appear here.</span>
                      </div>
                    </div>
                  )}

                  {/* Time analysis */}
                  {summary.time_analysis?.by_weekday?.some((d: any) => d.trades > 0) && (
                    <div>
                      <div style={{ ...mono, color: '#a855f7', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>TIME ANALYSIS</div>

                      {/* Weekday chart */}
                      <div className="rounded-xl p-3 mb-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(168,85,247,0.15)' }}>
                        <div style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '8px', letterSpacing: '0.1em', marginBottom: 6 }}>BY WEEKDAY</div>
                        <ResponsiveContainer width="100%" height={180}>
                          <BarChart data={summary.time_analysis.by_weekday.map((d: any) => ({ ...d, shortName: d.name?.slice(0, 3) }))}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,85,247,0.08)" />
                            <XAxis dataKey="shortName" tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} />
                            <YAxis yAxisId="left" tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} />
                            <YAxis yAxisId="right" orientation="right" tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} />
                            <Tooltip
                              contentStyle={{ background: 'rgba(0,10,25,0.95)', border: '1px solid rgba(168,85,247,0.3)', borderRadius: 8, fontFamily: 'Share Tech Mono', fontSize: 10 }}
                              labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                              formatter={(val: any, name: string, props: any) => {
                                if (name === 'trades') return [val, 'Trades'];
                                const item = props.payload;
                                if (!item) return [val, 'Avg R'];
                                const note = item.avg_r !== null ? `${item.avg_r}R` : '— (< 2 trades)';
                                return [note, 'Avg R'];
                              }}
                            />
                            <Bar yAxisId="left" dataKey="trades" fill="rgba(255,255,255,0.15)" radius={[2, 2, 0, 0]} />
                            <Bar yAxisId="right" dataKey="avg_r" radius={[2, 2, 0, 0]}>
                              {summary.time_analysis.by_weekday.map((d: any, i: number) => (
                                <Cell key={i} fill={d.avg_r !== null && d.avg_r > 0 ? '#22c55e' : d.avg_r !== null && d.avg_r < 0 ? '#ef4444' : 'rgba(255,255,255,0.1)'} fillOpacity={0.7} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      {/* Hour chart */}
                      {(() => {
                        const activeHours = (summary.time_analysis?.by_hour ?? []).filter((h: any) => h.trades > 0);
                        if (activeHours.length < 2) return null;
                        return (
                          <div className="rounded-xl p-3" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(168,85,247,0.15)' }}>
                            <div style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '8px', letterSpacing: '0.1em', marginBottom: 6 }}>BY HOUR OF DAY</div>
                            <ResponsiveContainer width="100%" height={180}>
                              <BarChart data={activeHours}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,85,247,0.08)" />
                                <XAxis dataKey="label" tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} />
                                <YAxis tick={{ fontFamily: 'Share Tech Mono', fontSize: 8, fill: 'rgba(255,255,255,0.25)' }} />
                                <Tooltip
                                  contentStyle={{ background: 'rgba(0,10,25,0.95)', border: '1px solid rgba(168,85,247,0.3)', borderRadius: 8, fontFamily: 'Share Tech Mono', fontSize: 10 }}
                                  labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                                  formatter={(val: any, name: string, props: any) => {
                                    if (name === 'trades') return [val, 'Trades'];
                                    const item = props.payload;
                                    if (!item) return [val, 'Avg R'];
                                    const note = item.avg_r !== null ? `${item.avg_r}R` : '— (< 2 trades)';
                                    return [note, 'Avg R'];
                                  }}
                                />
                                <Bar dataKey="trades" radius={[2, 2, 0, 0]}>
                                  {activeHours.map((h: any, i: number) => (
                                    <Cell key={i} fill={h.avg_r !== null && h.avg_r > 0 ? '#22c55e' : h.avg_r !== null && h.avg_r < 0 ? '#ef4444' : 'rgba(255,255,255,0.15)'} fillOpacity={0.7} />
                                  ))}
                                </Bar>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        );
                      })()}
                    </div>
                  )}

                  {/* Setup breakdown table */}
                  {summary.setup_breakdown.filter(sb => sb.setup !== 'unspecified').length > 0 && (
                    <div>
                      <div style={{ ...mono, color: '#06b6d4', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>STRATEGY BREAKDOWN</div>
                      <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(6,182,212,0.12)' }}>
                        <table className="w-full" style={{ borderCollapse: 'collapse' }}>
                          <thead>
                            <tr style={{ background: 'rgba(6,182,212,0.05)' }}>
                              {['Setup', 'Trades', 'Win %', 'Avg R', 'P&L'].map(h => (
                                <th key={h} style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px', padding: '8px 12px', textAlign: 'left', letterSpacing: '0.1em' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {summary.setup_breakdown.filter(sb => sb.setup !== 'unspecified').map((sb, i) => (
                              <tr key={i} style={{ borderTop: '1px solid rgba(6,182,212,0.06)' }}>
                                <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: '#06b6d4', fontSize: '10px' }}>{sb.setup}</span></td>
                                <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>{sb.trades}</span></td>
                                <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: sb.win_rate >= 50 ? '#22c55e' : '#ef4444', fontSize: '10px' }}>{sb.win_rate}%</span></td>
                                <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: sb.avg_r !== null && sb.avg_r >= 0 ? '#a855f7' : '#ef4444', fontSize: '10px' }}>{sb.avg_r !== null ? `${sb.avg_r}R` : '—'}</span></td>
                                <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: sb.total_pnl >= 0 ? '#22c55e' : '#ef4444', fontSize: '10px' }}>{fmtUsd(sb.total_pnl)}</span></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Recent closed trades */}
                  {filteredClosed.length > 0 && (
                    <div>
                      <div style={{ ...mono, color: '#22c55e', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>RECENT CLOSED TRADES</div>
                      <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(34,197,94,0.12)' }}>
                        <table className="w-full" style={{ borderCollapse: 'collapse' }}>
                          <thead>
                            <tr style={{ background: 'rgba(34,197,94,0.05)' }}>
                              {['Symbol', 'Side', 'P&L', 'R', 'Setup', 'Holding'].map(h => (
                                <th key={h} style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px', padding: '8px 12px', textAlign: 'left', letterSpacing: '0.1em' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {filteredClosed.map((t, i) => {
                              const pnlColor = t.realized_pnl_usd >= 0 ? '#22c55e' : '#ef4444';
                              return (
                                <tr key={i} onClick={() => setSelectedTrade(t)} className="cursor-pointer" style={{ borderTop: '1px solid rgba(34,197,94,0.06)' }}>
                                  <td style={{ padding: '8px 12px' }}><span style={{ ...raj, color: '#22c55e', fontSize: '13px' }}>{t.symbol}</span></td>
                                  <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: t.side === 'long' ? '#22c55e' : '#ef4444', fontSize: '10px' }}>{t.side}</span></td>
                                  <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: pnlColor, fontSize: '10px' }}>{fmtUsd(t.realized_pnl_usd)}</span></td>
                                  <td style={{ padding: '8px 12px' }}><span style={{ ...mono, color: t.realized_r !== null && t.realized_r >= 0 ? '#22c55e' : '#ef4444', fontSize: '10px' }}>{t.realized_r !== null ? `${t.realized_r}R` : '—'}</span></td>
                                  <td style={{ padding: '8px 12px' }}>
                                    <span className="px-1.5 py-0.5 rounded" style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
                                      {t.setup || 'unspecified'}
                                    </span>
                                  </td>
                                  <td style={{ padding: '8px 12px' }}>
                                    <span className="flex items-center gap-1" style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '10px' }}>
                                      <Clock className="w-2.5 h-2.5" />{t.holding_hours !== null ? `${t.holding_hours}h` : '—'}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Import / Export row */}
                  <div className="flex items-center gap-3 flex-wrap">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => fileRef.current?.click()}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl cursor-pointer"
                      style={{ background: 'rgba(0,245,255,0.08)', border: '1px solid rgba(0,245,255,0.25)' }}
                    >
                      <Upload className="w-3.5 h-3.5" style={{ color: '#00f5ff' }} />
                      <span style={{ ...mono, color: '#00f5ff', fontSize: '10px' }}>IMPORT TRADES</span>
                    </motion.button>
                    <input
                      ref={fileRef}
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={e => { const f = e.target.files?.[0]; if (f) { handleImport(f); e.target.value = ''; } }}
                      style={{ display: 'none' }}
                    />
                    <motion.a
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      href="/api/trading/export"
                      target="_blank"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl cursor-pointer"
                      style={{ background: 'rgba(0,245,255,0.08)', border: '1px solid rgba(0,245,255,0.25)' }}
                    >
                      <Download className="w-3.5 h-3.5" style={{ color: '#00f5ff' }} />
                      <span style={{ ...mono, color: '#00f5ff', fontSize: '10px' }}>EXPORT CSV</span>
                    </motion.a>
                    <motion.a
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      href="/api/trading/import/template"
                      target="_blank"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl cursor-pointer"
                      style={{ background: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.25)' }}
                    >
                      <FileDown className="w-3.5 h-3.5" style={{ color: '#a855f7' }} />
                      <span style={{ ...mono, color: '#a855f7', fontSize: '10px' }}>TEMPLATE</span>
                    </motion.a>
                  </div>

                  {/* Entry modal */}
                  <AnimatePresence>
                    {entryModalOpen && (
                      <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        style={{
                          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
                          zIndex: 190, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}
                        onClick={() => setEntryModalOpen(false)}
                      >
                        <motion.div
                          initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }}
                          onClick={e => e.stopPropagation()}
                          className="rounded-2xl p-6"
                          style={{ background: 'rgba(0,10,30,0.97)', border: '1px solid rgba(0,245,255,0.2)', maxWidth: 520, width: '90%', maxHeight: '90vh', overflowY: 'auto' }}
                        >
                          <div className="flex items-center justify-between mb-5">
                            <h3 style={{ ...mono, color: '#00f5ff', fontSize: '13px', letterSpacing: '0.15em', margin: 0 }}>LOG NEW TRADE</h3>
                            <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }} onClick={() => setEntryModalOpen(false)} className="cursor-pointer" style={{ background: 'none', border: 'none', color: '#ef4444' }}>
                              <X className="w-4 h-4" />
                            </motion.button>
                          </div>
                          <div className="flex flex-col gap-3">
                            <div className="flex gap-3">
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>SYMBOL</label>
                                <div style={{ position: 'relative' }}>
                                  <input style={inputStyle} placeholder="e.g. BTC" value={entryForm.symbol} onChange={e => setEntryForm(f => ({ ...f, symbol: e.target.value }))} />
                                </div>
                              </div>
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>SIDE</label>
                                <div style={{ display: 'flex', gap: 6 }}>
                                  {['long', 'short'].map(s => (
                                    <motion.button
                                      key={s} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                                      onClick={() => setEntryForm(f => ({ ...f, side: s }))}
                                      className="cursor-pointer"
                                      style={{
                                        flex: 1, padding: '6px 0', borderRadius: 6, border: `1px solid ${entryForm.side === s ? (s === 'long' ? '#22c55e' : '#ef4444') : 'rgba(255,255,255,0.12)'}`,
                                        background: entryForm.side === s ? (s === 'long' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)') : 'transparent',
                                        ...mono, fontSize: '10px', color: entryForm.side === s ? (s === 'long' ? '#22c55e' : '#ef4444') : 'rgba(255,255,255,0.3)',
                                        textTransform: 'uppercase',
                                      }}
                                    >{s}</motion.button>
                                  ))}
                                </div>
                              </div>
                            </div>
                            <div className="flex gap-3">
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>ENTRY PRICE</label>
                                <input style={inputStyle} placeholder="0.00" type="number" step="any" value={entryForm.entry_price} onChange={e => setEntryForm(f => ({ ...f, entry_price: e.target.value }))} />
                              </div>
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>SIZE</label>
                                <input style={inputStyle} placeholder="Units" type="number" step="any" value={entryForm.size} onChange={e => setEntryForm(f => ({ ...f, size: e.target.value }))} />
                              </div>
                            </div>
                            <div className="flex gap-3">
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>STOP LOSS</label>
                                <input style={inputStyle} placeholder="Optional" type="number" step="any" value={entryForm.stop_loss} onChange={e => setEntryForm(f => ({ ...f, stop_loss: e.target.value }))} />
                              </div>
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>TAKE PROFIT</label>
                                <input style={inputStyle} placeholder="Optional" type="number" step="any" value={entryForm.take_profit} onChange={e => setEntryForm(f => ({ ...f, take_profit: e.target.value }))} />
                              </div>
                            </div>
                            <div>
                              <label style={labelStyle}>SETUP</label>
                              <input style={inputStyle} placeholder="e.g. Breakout, Reversal" value={entryForm.setup} onChange={e => setEntryForm(f => ({ ...f, setup: e.target.value }))} />
                            </div>
                            <div>
                              <label style={labelStyle}>TAGS (comma-separated)</label>
                              <input style={inputStyle} placeholder="e.g. high_volume, trend" value={entryForm.tags} onChange={e => setEntryForm(f => ({ ...f, tags: e.target.value }))} />
                            </div>
                            <div>
                              <label style={labelStyle}>REASONING</label>
                              <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 48 }} placeholder="Trade rationale" value={entryForm.reasoning} onChange={e => setEntryForm(f => ({ ...f, reasoning: e.target.value }))} />
                            </div>
                            <div className="flex gap-3">
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>FEE</label>
                                <input style={inputStyle} placeholder="0" type="number" step="any" value={entryForm.fee} onChange={e => setEntryForm(f => ({ ...f, fee: e.target.value }))} />
                              </div>
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>NOTES</label>
                                <input style={inputStyle} placeholder="Optional notes" value={entryForm.notes} onChange={e => setEntryForm(f => ({ ...f, notes: e.target.value }))} />
                              </div>
                            </div>
                            {/* Position calculator */}
                            <div className="rounded-xl p-3" style={{ background: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.2)' }}>
                              <div style={{ ...mono, color: '#a855f7', fontSize: '9px', letterSpacing: '0.1em', marginBottom: 8 }}>POSITION CALCULATOR</div>
                              <div className="flex gap-3 mb-2">
                                <div style={{ flex: 1 }}>
                                  <label style={{ ...labelStyle, color: 'rgba(168,85,247,0.6)' }}>ACCOUNT SIZE</label>
                                  <input style={{ ...inputStyle, borderColor: 'rgba(168,85,247,0.3)' }} placeholder="e.g. 10000" type="number" step="any" value={accountSize} onChange={e => setAccountSize(e.target.value)} />
                                </div>
                                <div style={{ flex: 1 }}>
                                  <label style={{ ...labelStyle, color: 'rgba(168,85,247,0.6)' }}>RISK %</label>
                                  <div style={{ position: 'relative' }}>
                                    <input style={{ ...inputStyle, borderColor: 'rgba(168,85,247,0.3)', paddingRight: 20 }} placeholder="1" type="number" step="0.1" min="0" max="100" value={riskPct} onChange={e => setRiskPct(e.target.value)} />
                                    <span style={{ position: 'absolute', right: 8, top: 7, ...mono, fontSize: 10, color: 'rgba(168,85,247,0.5)' }}>%</span>
                                  </div>
                                </div>
                              </div>
                              {(() => {
                                const acc = parseFloat(accountSize);
                                const ep = parseFloat(entryForm.entry_price);
                                const sl = parseFloat(entryForm.stop_loss);
                                const rp = parseFloat(riskPct);
                                if (acc && ep && sl && rp && ep !== sl) {
                                  const riskAmount = acc * (rp / 100);
                                  const perUnit = Math.abs(ep - sl);
                                  const posSize = riskAmount / perUnit;
                                  return (
                                    <div className="flex gap-3">
                                      <div style={{ flex: 1 }}><span style={{ ...mono, fontSize: 9, color: 'rgba(168,85,247,0.5)' }}>RISK $</span><br /><span style={{ ...mono, fontSize: 11, color: '#a855f7' }}>${riskAmount.toFixed(2)}</span></div>
                                      <div style={{ flex: 1 }}><span style={{ ...mono, fontSize: 9, color: 'rgba(168,85,247,0.5)' }}>POSITION SIZE</span><br /><span style={{ ...mono, fontSize: 11, color: '#a855f7' }}>{posSize.toFixed(6)}</span></div>
                                    </div>
                                  );
                                }
                                return <span style={{ ...mono, fontSize: 9, color: 'rgba(168,85,247,0.3)' }}>Enter account size, entry price, stop loss, and risk % to calculate.</span>;
                              })()}
                            </div>
                          </div>
                          {entryError && (
                            <div className="flex items-center gap-2 mt-3 p-2 rounded-lg" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}>
                              <AlertCircle className="w-3 h-3" style={{ color: '#ef4444', flexShrink: 0 }} />
                              <span style={{ ...mono, fontSize: 9, color: '#ef4444' }}>{entryError}</span>
                            </div>
                          )}
                          <div className="flex gap-3 mt-4">
                            <motion.button
                              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                              onClick={submitEntry} disabled={entryLoading}
                              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl cursor-pointer disabled:opacity-50"
                              style={{ background: 'rgba(0,245,255,0.12)', border: '1px solid rgba(0,245,255,0.3)' }}
                            >
                              {entryLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: '#00f5ff' }} /> : <TrendingUp className="w-3.5 h-3.5" style={{ color: '#00f5ff' }} />}
                              <span style={{ ...mono, color: '#00f5ff', fontSize: '10px' }}>{entryLoading ? 'LOGGING...' : 'LOG TRADE'}</span>
                            </motion.button>
                            <motion.button
                              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                              onClick={() => setEntryModalOpen(false)}
                              className="px-4 py-2.5 rounded-xl cursor-pointer"
                              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                            >
                              <span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>CANCEL</span>
                            </motion.button>
                          </div>
                        </motion.div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Close modal */}
                  <AnimatePresence>
                    {closeModalTrade && (
                      <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        style={{
                          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
                          zIndex: 190, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}
                        onClick={() => setCloseModalTrade(null)}
                      >
                        <motion.div
                          initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }}
                          onClick={e => e.stopPropagation()}
                          className="rounded-2xl p-6"
                          style={{ background: 'rgba(0,10,30,0.97)', border: '1px solid rgba(239,68,68,0.3)', maxWidth: 480, width: '90%' }}
                        >
                          <div className="flex items-center justify-between mb-4">
                            <h3 style={{ ...mono, color: '#ef4444', fontSize: '13px', letterSpacing: '0.15em', margin: 0 }}>CLOSE TRADE</h3>
                            <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }} onClick={() => setCloseModalTrade(null)} className="cursor-pointer" style={{ background: 'none', border: 'none', color: '#ef4444' }}>
                              <X className="w-4 h-4" />
                            </motion.button>
                          </div>
                          <div className="rounded-xl p-3 mb-4" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(239,68,68,0.15)' }}>
                            <div className="flex gap-4 mb-2">
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>SYMBOL</span><br /><span style={{ ...raj, fontSize: 15, color: '#00f5ff' }}>{closeModalTrade.symbol}</span></div>
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>SIDE</span><br /><span style={{ ...mono, fontSize: 11, color: closeModalTrade.side === 'long' ? '#22c55e' : '#ef4444' }}>{closeModalTrade.side.toUpperCase()}</span></div>
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>ENTRY</span><br /><span style={{ ...mono, fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>${closeModalTrade.entry_price?.toLocaleString()}</span></div>
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>SIZE</span><br /><span style={{ ...mono, fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>{closeModalTrade.remaining_size}</span></div>
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>LIVE</span><br /><span style={{ ...mono, fontSize: 11, color: livePrices[closeModalTrade.symbol] ? '#22c55e' : 'rgba(255,255,255,0.3)' }}>{livePrices[closeModalTrade.symbol] ? `$${livePrices[closeModalTrade.symbol]}` : '—'}</span></div>
                            </div>
                            <div style={{ width: '100%', height: 1, background: 'rgba(255,255,255,0.06)', margin: '8px 0' }} />
                            <div className="flex gap-3">
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>EXIT PRICE</label>
                                <input style={inputStyle} placeholder="0.00" type="number" step="any" value={closeForm.exit_price} onChange={e => setCloseForm(f => ({ ...f, exit_price: e.target.value }))} />
                              </div>
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>SIZE (leave empty for full)</label>
                                <input style={inputStyle} placeholder={`${closeModalTrade.remaining_size}`} type="number" step="any" value={closeForm.size} onChange={e => setCloseForm(f => ({ ...f, size: e.target.value }))} />
                              </div>
                            </div>
                          </div>
                          {previewPnl !== null && (
                            <div className="flex items-center gap-2 mb-3 p-2 rounded-lg" style={{ background: parseFloat(previewPnl) >= 0 ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)', border: `1px solid ${parseFloat(previewPnl) >= 0 ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}` }}>
                              {parseFloat(previewPnl) >= 0 ? <ArrowUpRight className="w-3 h-3" style={{ color: '#22c55e' }} /> : <ArrowDownRight className="w-3 h-3" style={{ color: '#ef4444' }} />}
                              <span style={{ ...mono, fontSize: 11, color: parseFloat(previewPnl) >= 0 ? '#22c55e' : '#ef4444' }}>P&L Preview: {fmtUsd(parseFloat(previewPnl))}</span>
                            </div>
                          )}
                          <div className="flex gap-3">
                            <div style={{ flex: 1 }}>
                              <label style={labelStyle}>FEE</label>
                              <input style={inputStyle} placeholder="0" type="number" step="any" value={closeForm.fee} onChange={e => setCloseForm(f => ({ ...f, fee: e.target.value }))} />
                            </div>
                            <div style={{ flex: 1 }}>
                              <label style={labelStyle}>NOTES</label>
                              <input style={inputStyle} placeholder="Exit notes" value={closeForm.notes} onChange={e => setCloseForm(f => ({ ...f, notes: e.target.value }))} />
                            </div>
                          </div>
                          {closeError && (
                            <div className="flex items-center gap-2 mt-3 p-2 rounded-lg" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}>
                              <AlertCircle className="w-3 h-3" style={{ color: '#ef4444', flexShrink: 0 }} />
                              <span style={{ ...mono, fontSize: 9, color: '#ef4444' }}>{closeError}</span>
                            </div>
                          )}
                          <div className="flex gap-3 mt-4">
                            <motion.button
                              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                              onClick={submitClose} disabled={closeLoading}
                              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl cursor-pointer disabled:opacity-50"
                              style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)' }}
                            >
                              {closeLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: '#ef4444' }} /> : <X className="w-3.5 h-3.5" style={{ color: '#ef4444' }} />}
                              <span style={{ ...mono, color: '#ef4444', fontSize: '10px' }}>{closeLoading ? 'CLOSING...' : 'CLOSE TRADE'}</span>
                            </motion.button>
                            <motion.button
                              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                              onClick={() => setCloseForm(f => ({ ...f, exit_price: livePrices[closeModalTrade.symbol]?.toString() || f.exit_price }))}
                              className="px-4 py-2.5 rounded-xl cursor-pointer"
                              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                            >
                              <span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>USE LIVE</span>
                            </motion.button>
                          </div>
                        </motion.div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Edit modal */}
                  <AnimatePresence>
                    {editModalTrade && (
                      <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        style={{
                          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
                          zIndex: 190, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}
                        onClick={() => setEditModalTrade(null)}
                      >
                        <motion.div
                          initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }}
                          onClick={e => e.stopPropagation()}
                          className="rounded-2xl p-6"
                          style={{ background: 'rgba(0,10,30,0.97)', border: '1px solid rgba(0,245,255,0.2)', maxWidth: 480, width: '90%' }}
                        >
                          <div className="flex items-center justify-between mb-4">
                            <h3 style={{ ...mono, color: '#00f5ff', fontSize: '13px', letterSpacing: '0.15em', margin: 0 }}>EDIT TRADE</h3>
                            <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }} onClick={() => setEditModalTrade(null)} className="cursor-pointer" style={{ background: 'none', border: 'none', color: '#ef4444' }}>
                              <X className="w-4 h-4" />
                            </motion.button>
                          </div>
                          <div className="rounded-xl p-3 mb-4" style={{ background: 'rgba(0,8,20,0.5)', border: '1px solid rgba(0,245,255,0.1)' }}>
                            <div className="flex gap-4 mb-2">
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>SYMBOL</span><br /><span style={{ ...raj, fontSize: 15, color: '#00f5ff' }}>{editModalTrade.symbol}</span></div>
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>SIDE</span><br /><span style={{ ...mono, fontSize: 11, color: editModalTrade.side === 'long' ? '#22c55e' : '#ef4444' }}>{editModalTrade.side.toUpperCase()}</span></div>
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>ENTRY</span><br /><span style={{ ...mono, fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>${editModalTrade.entry_price?.toLocaleString()}</span></div>
                              <div><span style={{ ...mono, fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>SIZE</span><br /><span style={{ ...mono, fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>{editModalTrade.remaining_size}</span></div>
                            </div>
                            <div style={{ width: '100%', height: 1, background: 'rgba(255,255,255,0.06)', margin: '8px 0' }} />
                            <div className="flex gap-3">
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>STOP LOSS</label>
                                <input style={inputStyle} placeholder="No change" type="number" step="any" value={editForm.stop_loss} onChange={e => setEditForm(f => ({ ...f, stop_loss: e.target.value }))} />
                              </div>
                              <div style={{ flex: 1 }}>
                                <label style={labelStyle}>TAKE PROFIT</label>
                                <input style={inputStyle} placeholder="No change" type="number" step="any" value={editForm.take_profit} onChange={e => setEditForm(f => ({ ...f, take_profit: e.target.value }))} />
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-col gap-3">
                            <div>
                              <label style={labelStyle}>SETUP</label>
                              <input style={inputStyle} placeholder="No change" value={editForm.setup} onChange={e => setEditForm(f => ({ ...f, setup: e.target.value }))} />
                            </div>
                            <div>
                              <label style={labelStyle}>TAGS (comma-separated)</label>
                              <input style={inputStyle} placeholder="No change" value={editForm.tags} onChange={e => setEditForm(f => ({ ...f, tags: e.target.value }))} />
                            </div>
                            <div>
                              <label style={labelStyle}>REASONING</label>
                              <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 48 }} placeholder="No change" value={editForm.reasoning} onChange={e => setEditForm(f => ({ ...f, reasoning: e.target.value }))} />
                            </div>
                            <div>
                              <label style={labelStyle}>NOTES</label>
                              <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 48 }} placeholder="No change" value={editForm.notes} onChange={e => setEditForm(f => ({ ...f, notes: e.target.value }))} />
                            </div>
                          </div>
                          {editError && (
                            <div className="flex items-center gap-2 mt-3 p-2 rounded-lg" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}>
                              <AlertCircle className="w-3 h-3" style={{ color: '#ef4444', flexShrink: 0 }} />
                              <span style={{ ...mono, fontSize: 9, color: '#ef4444' }}>{editError}</span>
                            </div>
                          )}
                          <div className="flex gap-3 mt-4">
                            <motion.button
                              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                              onClick={submitEdit} disabled={editLoading}
                              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl cursor-pointer disabled:opacity-50"
                              style={{ background: 'rgba(0,245,255,0.12)', border: '1px solid rgba(0,245,255,0.3)' }}
                            >
                              {editLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: '#00f5ff' }} /> : <Edit3 className="w-3.5 h-3.5" style={{ color: '#00f5ff' }} />}
                              <span style={{ ...mono, color: '#00f5ff', fontSize: '10px' }}>{editLoading ? 'SAVING...' : 'SAVE CHANGES'}</span>
                            </motion.button>
                            <motion.button
                              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                              onClick={() => setEditModalTrade(null)}
                              className="px-4 py-2.5 rounded-xl cursor-pointer"
                              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                            >
                              <span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>CANCEL</span>
                            </motion.button>
                          </div>
                        </motion.div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Trade detail modal */}
                  <AnimatePresence>
                    {selectedTrade && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 flex items-center justify-center"
                        style={{ zIndex: 190, background: 'rgba(0, 4, 12, 0.88)', backdropFilter: 'blur(8px)' }}
                        onClick={() => setSelectedTrade(null)}
                      >
                        <motion.div
                          initial={{ scale: 0.92, y: 16 }}
                          animate={{ scale: 1, y: 0 }}
                          exit={{ scale: 0.92, y: 16 }}
                          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
                          className="w-full max-w-lg mx-4 rounded-2xl overflow-hidden flex flex-col"
                          style={{
                            maxHeight: '85vh',
                            background: 'rgba(0, 10, 25, 0.96)',
                            border: '1px solid rgba(0,245,255,0.2)',
                            boxShadow: '0 0 60px rgba(0,245,255,0.1)',
                          }}
                          onClick={e => e.stopPropagation()}
                        >
                          {/* Modal header */}
                          <div className="flex items-center justify-between px-6 py-4 flex-shrink-0" style={{ borderBottom: '1px solid rgba(0,245,255,0.12)' }}>
                            <div className="flex items-center gap-3">
                              <span style={{ ...raj, color: '#00f5ff', fontSize: '18px', fontWeight: 600 }}>
                                {selectedTrade.symbol}
                              </span>
                              <span style={{ ...mono, color: selectedTrade.side === 'long' ? '#22c55e' : '#ef4444', fontSize: '10px' }}>
                                {selectedTrade.side?.toUpperCase()}
                              </span>
                              <span className="px-2 py-0.5 rounded" style={{ ...mono, fontSize: '8px', background: selectedTrade.status === 'open' ? 'rgba(0,245,255,0.1)' : 'rgba(34,197,94,0.1)', color: selectedTrade.status === 'open' ? '#00f5ff' : '#22c55e', border: `1px solid ${selectedTrade.status === 'open' ? 'rgba(0,245,255,0.25)' : 'rgba(34,197,94,0.25)'}` }}>
                                {selectedTrade.status?.toUpperCase()}
                              </span>
                            </div>
                            <motion.button
                              whileHover={{ scale: 1.1, rotate: 90 }}
                              whileTap={{ scale: 0.9 }}
                              onClick={() => setSelectedTrade(null)}
                              className="w-8 h-8 rounded-xl flex items-center justify-center cursor-pointer"
                              style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}
                            >
                              <X className="w-4 h-4" style={{ color: '#ef4444' }} />
                            </motion.button>
                          </div>

                          {/* Modal body */}
                          <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(0,245,255,0.2) transparent' }}>

                            {/* Trade summary */}
                            <div>
                              <div style={{ ...mono, color: '#00f5ff', fontSize: '9px', letterSpacing: '0.1em', marginBottom: 6 }}>TRADE SUMMARY</div>
                              <div className="grid grid-cols-2 gap-2">
                                <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>ID</span><br /><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>{selectedTrade.id || '—'}</span></div>
                                <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>SETUP</span><br /><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>{selectedTrade.setup || 'unspecified'}</span></div>
                                <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>OPENED</span><br /><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>{selectedTrade.opened_at ? new Date(selectedTrade.opened_at).toLocaleString() : '—'}</span></div>
                                <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>CLOSED</span><br /><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>{selectedTrade.closed_at ? new Date(selectedTrade.closed_at).toLocaleString() : '—'}</span></div>
                              </div>
                            </div>

                            {/* Entry details */}
                            <div>
                              <div style={{ ...mono, color: '#a855f7', fontSize: '9px', letterSpacing: '0.1em', marginBottom: 6 }}>ENTRY DETAILS</div>
                              <div className="grid grid-cols-2 gap-2">
                                <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>ENTRY PRICE</span><br /><span style={{ ...raj, color: '#00f5ff', fontSize: '15px' }}>${selectedTrade.entry_price?.toLocaleString()}</span></div>
                                <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>SIZE</span><br /><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>{selectedTrade.size} {selectedTrade.remaining_size !== undefined && selectedTrade.remaining_size !== null && selectedTrade.remaining_size !== selectedTrade.size && `(${selectedTrade.remaining_size} remaining)`}</span></div>
                                {selectedTrade.stop_loss !== null && selectedTrade.stop_loss !== undefined && (
                                  <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>STOP LOSS</span><br /><span style={{ ...mono, color: '#ef4444', fontSize: '10px' }}>${selectedTrade.stop_loss.toLocaleString()}</span></div>
                                )}
                                {selectedTrade.take_profit !== null && selectedTrade.take_profit !== undefined && (
                                  <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>TAKE PROFIT</span><br /><span style={{ ...mono, color: '#22c55e', fontSize: '10px' }}>${selectedTrade.take_profit.toLocaleString()}</span></div>
                                )}
                                {selectedTrade.entry_fee > 0 && (
                                  <div><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>ENTRY FEE</span><br /><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>${selectedTrade.entry_fee.toFixed(2)}</span></div>
                                )}
                              </div>
                              {selectedTrade.reasoning && (
                                <div className="mt-2"><span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px' }}>REASONING</span><br /><span style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '9px', fontStyle: 'italic' }}>"{selectedTrade.reasoning}"</span></div>
                              )}
                            </div>

                            {/* Tags */}
                            {selectedTrade.tags && selectedTrade.tags.length > 0 && (
                              <div>
                                <div style={{ ...mono, color: '#f59e0b', fontSize: '9px', letterSpacing: '0.1em', marginBottom: 6 }}>TAGS</div>
                                <div className="flex flex-wrap gap-1.5">
                                  {selectedTrade.tags.map((tag: string, i: number) => (
                                    <span key={i} className="px-2 py-0.5 rounded" style={{ ...mono, fontSize: '8px', background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.25)' }}>
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Notes */}
                            {selectedTrade.notes && (
                              <div>
                                <div style={{ ...mono, color: '#a855f7', fontSize: '9px', letterSpacing: '0.1em', marginBottom: 6 }}>NOTES</div>
                                <div className="rounded-lg p-3" style={{ background: 'rgba(168,85,247,0.06)', border: '1px solid rgba(168,85,247,0.15)' }}>
                                  <span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>{selectedTrade.notes}</span>
                                </div>
                              </div>
                            )}

                            {/* Market context */}
                            <div>
                              <div style={{ ...mono, color: '#00f5ff', fontSize: '9px', letterSpacing: '0.1em', marginBottom: 6 }}>MARKET CONTEXT AT ENTRY</div>
                              {selectedTrade.market_context ? (
                                <div className="flex gap-3">
                                  <span className="px-2 py-0.5 rounded" style={{ ...mono, fontSize: '8px', background: 'rgba(0,245,255,0.08)', color: '#00f5ff', border: '1px solid rgba(0,245,255,0.15)' }}>
                                    F&G: {selectedTrade.market_context.fear_greed} ({selectedTrade.market_context.fear_greed_label})
                                  </span>
                                  {selectedTrade.market_context.btc_24h_change !== null && selectedTrade.market_context.btc_24h_change !== undefined && (
                                    <span className="px-2 py-0.5 rounded" style={{ ...mono, fontSize: '8px', background: 'rgba(245,158,11,0.08)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.15)' }}>
                                      BTC 24h: {selectedTrade.market_context.btc_24h_change > 0 ? '+' : ''}{selectedTrade.market_context.btc_24h_change}%
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <span style={{ ...mono, color: 'rgba(255,255,255,0.25)', fontSize: '9px' }}>No market context captured at entry.</span>
                              )}
                            </div>

                            {/* Exit log */}
                            <div>
                              <div style={{ ...mono, color: selectedTrade.status === 'open' ? '#00f5ff' : '#22c55e', fontSize: '9px', letterSpacing: '0.1em', marginBottom: 6 }}>
                                {selectedTrade.status === 'open' ? 'LIVE POSITION' : 'EXIT LOG'}
                              </div>
                              {selectedTrade.status === 'open' ? (
                                <div className="rounded-lg p-3 flex items-center gap-3" style={{ background: 'rgba(0,245,255,0.06)', border: '1px solid rgba(0,245,255,0.15)' }}>
                                  {selectedTrade.current_price !== null && selectedTrade.current_price !== undefined ? (
                                    <>
                                      <span style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '9px' }}>Current:</span>
                                      <span style={{ ...mono, color: '#00f5ff', fontSize: '11px' }}>${selectedTrade.current_price.toLocaleString()}</span>
                                      <span className="flex items-center gap-1" style={{ ...mono, color: selectedTrade.unrealized_pnl_usd >= 0 ? '#22c55e' : '#ef4444', fontSize: '10px' }}>
                                        {selectedTrade.unrealized_pnl_usd !== null && (selectedTrade.unrealized_pnl_usd >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />)}
                                        {selectedTrade.unrealized_pnl_usd !== null ? fmtUsd(selectedTrade.unrealized_pnl_usd) : '—'} unrealized
                                      </span>
                                    </>
                                  ) : (
                                    <span style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '9px' }}>Position still open — no live price available.</span>
                                  )}
                                </div>
                              ) : selectedTrade.exits && selectedTrade.exits.length > 0 ? (
                                <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(34,197,94,0.12)' }}>
                                  <table className="w-full" style={{ borderCollapse: 'collapse' }}>
                                    <thead>
                                      <tr style={{ background: 'rgba(34,197,94,0.05)' }}>
                                        {['Price', 'Size', 'Fee', 'Time', 'Type'].map(h => (
                                          <th key={h} style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px', padding: '6px 10px', textAlign: 'left', letterSpacing: '0.1em' }}>{h}</th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {selectedTrade.exits.map((ex: any, i: number) => {
                                        const eColor = ex.exit_type === 'stopped_out' ? '#ef4444' : ex.exit_type === 'hit_target' ? '#22c55e' : 'rgba(255,255,255,0.4)';
                                        return (
                                          <tr key={i} style={{ borderTop: '1px solid rgba(34,197,94,0.06)' }}>
                                            <td style={{ padding: '6px 10px' }}><span style={{ ...mono, color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>${ex.price?.toLocaleString()}</span></td>
                                            <td style={{ padding: '6px 10px' }}><span style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '10px' }}>{ex.size}</span></td>
                                            <td style={{ padding: '6px 10px' }}><span style={{ ...mono, color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}>${ex.fee?.toFixed(2) || '0.00'}</span></td>
                                            <td style={{ padding: '6px 10px' }}><span style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '8px' }}>{ex.timestamp ? new Date(ex.timestamp).toLocaleString() : '—'}</span></td>
                                            <td style={{ padding: '6px 10px' }}>
                                              <span className="px-1.5 py-0.5 rounded" style={{ ...mono, fontSize: '8px', background: `${eColor}15`, color: eColor, border: `1px solid ${eColor}30` }}>
                                                {ex.exit_type || 'manual'}
                                              </span>
                                            </td>
                                          </tr>
                                        );
                                      })}
                                    </tbody>
                                  </table>
                                </div>
                              ) : (
                                <span style={{ ...mono, color: 'rgba(255,255,255,0.35)', fontSize: '9px' }}>Position still open.</span>
                              )}
                            </div>

                            {/* P&L Summary */}
                            <div>
                              <div style={{ ...mono, color: '#22c55e', fontSize: '9px', letterSpacing: '0.1em', marginBottom: 6 }}>P&L SUMMARY</div>
                              <div className="flex gap-3 flex-wrap">
                                <span className="px-3 py-1.5 rounded-lg" style={{ background: (selectedTrade.realized_pnl_usd || 0) >= 0 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', border: `1px solid ${(selectedTrade.realized_pnl_usd || 0) >= 0 ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)'}` }}>
                                  <span style={{ ...mono, color: (selectedTrade.realized_pnl_usd || 0) >= 0 ? '#22c55e' : '#ef4444', fontSize: '13px' }}>
                                    {fmtUsd(selectedTrade.realized_pnl_usd || 0)}
                                  </span>
                                  <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px', marginLeft: 4 }}>realized</span>
                                </span>
                                {selectedTrade.realized_r !== null && selectedTrade.realized_r !== undefined && (
                                  <span className="px-3 py-1.5 rounded-lg" style={{ background: selectedTrade.realized_r >= 0 ? 'rgba(168,85,247,0.1)' : 'rgba(239,68,68,0.1)', border: `1px solid ${selectedTrade.realized_r >= 0 ? 'rgba(168,85,247,0.25)' : 'rgba(239,68,68,0.25)'}` }}>
                                    <span style={{ ...mono, color: selectedTrade.realized_r >= 0 ? '#a855f7' : '#ef4444', fontSize: '13px' }}>{selectedTrade.realized_r}R</span>
                                    <span style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px', marginLeft: 4 }}>avg</span>
                                  </span>
                                )}
                                {selectedTrade.holding_hours !== null && selectedTrade.holding_hours !== undefined && (
                                  <span className="px-3 py-1.5 rounded-lg flex items-center gap-1.5" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                                    <Clock className="w-3 h-3" style={{ color: 'rgba(255,255,255,0.35)' }} />
                                    <span style={{ ...mono, color: 'rgba(255,255,255,0.5)', fontSize: '10px' }}>{selectedTrade.holding_hours}h</span>
                                  </span>
                                )}
                              </div>
                            </div>

                          </div>
                        </motion.div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
