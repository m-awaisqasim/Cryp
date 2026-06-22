import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  X, TrendingUp, DollarSign, Percent, BarChart3,
  ArrowUpRight, ArrowDownRight, Download, Upload,
  Clock, AlertCircle, FileDown,
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
  setup: string; closed_at: string; holding_hours: number | null;
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
}

const emptySummary: TradingSummary = {
  open_positions: [], recent_closed: [], equity_curve: [],
  drawdown_curve: [], rolling_winrate: [], monthly_pnl: [], setup_breakdown: [],
  stats: { total_trades: 0, win_rate: null, avg_r: null, total_pnl: 0, max_drawdown: 0, profit_factor: null, expectancy: null, streaks: { current_streak: 0, current_streak_type: null, max_win_streak: 0, max_loss_streak: 0 } },
  exposure: { open_count: 0, total_notional: 0, total_risk: 0 },
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

                  {/* Open positions table */}
                  {summary.open_positions.length > 0 && (
                    <div>
                      <div style={{ ...mono, color: '#00f5ff', fontSize: '10px', letterSpacing: '0.1em', marginBottom: 8 }}>OPEN POSITIONS</div>
                      <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(0,245,255,0.1)' }}>
                        <table className="w-full" style={{ borderCollapse: 'collapse' }}>
                          <thead>
                            <tr style={{ background: 'rgba(0,245,255,0.05)' }}>
                              {['Symbol', 'Side', 'Entry', 'Current', 'Unrealized', 'Holding'].map(h => (
                                <th key={h} style={{ ...mono, color: 'rgba(255,255,255,0.3)', fontSize: '8px', padding: '8px 12px', textAlign: 'left', letterSpacing: '0.1em' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {summary.open_positions.map((p, i) => {
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
                  {summary.recent_closed.length > 0 && (
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
                            {summary.recent_closed.map((t, i) => {
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
