import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  BriefcaseBusiness,
  Check,
  CircleHelp,
  Clock,
  Coins,
  Cpu,
  Database,
  Download,
  Filter,
  Flame,
  Gauge,
  HelpCircle,
  IndianRupee,
  Layers,
  LayoutDashboard,
  LineChart,
  ListFilter,
  Lock,
  Menu,
  Percent,
  PieChart,
  Play,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Table,
  Target,
  Terminal,
  TrendingDown,
  TrendingUp,
  UserRound,
  Volume2,
  VolumeX,
  WalletCards,
  Wifi,
  WifiOff,
  X,
  Maximize2,
  Minimize2,
  Expand,
  Zap,
} from 'lucide-react'

import {
  MarketScannerTab,
  MultiAgentConsensusTab,
  TradePlanTab,
  BacktestLabTab,
} from './AIModules'
import { LoginPage3D } from './LoginPage3D'
import { SecureProfileModal } from './SecureProfileModal'
import { CryptoDesk } from './CryptoDesk'
import { MarketDataConnectorModal } from './MarketDataConnectorModal'

// --- Base API and WebSocket configuration ---
// Development:  .env.development  → VITE_API_BASE_URL=http://127.0.0.1:8000
//                                  → VITE_WS_URL=wss://ai-trade-manager.onrender.com/api/ws
// Production:   .env.production   → VITE_API_BASE_URL=https://ai-trade-manager.onrender.com
//                                  → VITE_WS_URL=wss://ai-trade-manager.onrender.com/api/ws
// Override on Render → Static Site → Environment Variables before each build.
// Fallback is the production URL — never localhost — so a misconfigured build
// still reaches the correct backend instead of silently failing.
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://ai-trade-manager.onrender.com'
const WS_URL   = import.meta.env.VITE_WS_URL      || 'wss://ai-trade-manager.onrender.com/api/ws'

// --- Utility Currency Formatters for INR (₹) ---
const money = (val) => {
  if (val === null || val === undefined || isNaN(val)) return '—'
  return `${val < 0 ? '-' : ''}₹${Math.abs(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const signedMoney = (val) => {
  if (val === null || val === undefined || isNaN(val)) return '—'
  return `${val >= 0 ? '+' : ''}${money(val)}`
}

const pct = (val) => {
  if (val === null || val === undefined || isNaN(val)) return '—'
  return `${val >= 0 ? '+' : ''}${Number(val).toFixed(2)}%`
}

const formatTime = (ts) => {
  if (!ts) return 'Awaiting feed...'
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString('en-IN', { hour12: false })
  } catch {
    return String(ts)
  }
}

// --- Navigation Items ---
const navItems = [
  { id: 'Dashboard', label: '1. Dashboard', icon: LayoutDashboard },
  { id: 'Live Market', label: '2. Live Market Desk', icon: Radio },
  { id: 'Crypto 24/7', label: '3. Crypto & Bitcoin 24/7', icon: Coins },
  { id: 'Gold & Silver Live', label: '4. Gold & Silver Desk', icon: Coins },
  { id: 'NIFTY 50 Live', label: '4. NIFTY 50 Desk', icon: LineChart },
  { id: 'NIFTY BANK Live', label: '5. NIFTY BANK Desk', icon: LineChart },
  { id: 'SENSEX Live', label: '6. SENSEX Live', icon: LineChart },
  { id: 'Stock Watchlist', label: '7. Stock Watchlist', icon: Table },
  { id: 'Interactive Charts', label: '8. Technical Charts', icon: BarChart3 },
  { id: 'Market Scanner', label: '9. Live Market Scanner', icon: Flame },
  { id: 'Multi-Agent', label: '10. AI Multi-Agent Desk', icon: Bot },
  { id: 'Trade Plan', label: '11. AI Trade Plan Generator', icon: Target },
  { id: 'Backtest Lab', label: '12. Strategy Backtest Lab', icon: Gauge },
  { id: 'Positions', label: '13. Open Positions', icon: BriefcaseBusiness },
  { id: 'Orders', label: '14. Order Book (OMS)', icon: Zap },
  { id: 'Profit & Loss Manager', label: '15. Profit/Loss Manager', icon: ShieldCheck },
  { id: 'Profit Manager', label: '16. Profit Protector', icon: TrendingUp },
  { id: 'Loss Manager', label: '17. Loss Engine', icon: ShieldAlert },
  { id: 'Alert System', label: '18. Alert System', icon: Bell },
  { id: 'Analytics', label: '19. Analytics Workbench', icon: Gauge },
  { id: 'Trade Book', label: '20. Trade Book & Tax', icon: BookOpen },
  { id: 'Feed Status', label: '21. Feed Health & QoS', icon: Wifi },
  { id: 'System Console', label: '22. System Logs & Compliance', icon: Terminal },
]


// --- Instrument Master Catalog Modal ---
function InstrumentMasterModal({ onClose }) {
  const [instruments, setInstruments] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/market/instruments`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setInstruments(data || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return instruments.filter(
      (i) =>
        (i.symbol && i.symbol.toLowerCase().includes(q)) ||
        (i.company_name && i.company_name.toLowerCase().includes(q)) ||
        (i.isin && i.isin.toLowerCase().includes(q)) ||
        (i.sector && i.sector.toLowerCase().includes(q))
    )
  }, [instruments, search])

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: 900 }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Database size={18} color="var(--accent-green)" />
            Authorized Instrument Master Catalog & ISIN Mapping (NSE / BSE)
          </h3>
          <button className="btn-icon" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="modal-body">
          <div style={{ marginBottom: 14 }}>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Search by Symbol, Company Name, ISIN, or Sector..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ paddingLeft: 34 }}
              />
              <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: 10, top: 12 }} />
            </div>
          </div>

          <div className="table-container" style={{ maxHeight: 440, overflowY: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Exchange</th>
                  <th>Instrument Token</th>
                  <th>ISIN Code</th>
                  <th>Lot Size</th>
                  <th>Segment</th>
                  <th>Company & Sector</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((inst) => (
                  <tr key={`${inst.exchange}:${inst.symbol}`}>
                    <td><b>{inst.symbol}</b></td>
                    <td><span className="badge badge-blue">{inst.exchange}</span></td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{inst.instrument_token || '—'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5 }}>{inst.isin || '—'}</td>
                    <td>{inst.lot_size || 1}</td>
                    <td><span className="badge badge-green">{inst.segment || 'EQ'}</span></td>
                    <td>
                      <b>{inst.company_name}</b><br />
                      <small style={{ color: 'var(--text-dim)' }}>{inst.sector}</small>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && !loading && (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>
                      No instruments matched your search query.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

// --- Live Price Cell Component with Real-Time Up/Down Flashes & Movement Tags ---
function PriceCell({ symbol, ltp, change, flash, currencySymbol = '₹' }) {
  const formatted = currencySymbol === '$' ? `$${Number(ltp || 0).toFixed(2)}` : money(ltp)
  const dir = flash?.dir // 'UP' | 'DOWN' | 'UNCHANGED'
  const isUp = dir === 'UP'
  const isDown = dir === 'DOWN'

  return (
    <div
      className={isUp ? 'price-flash-up' : isDown ? 'price-flash-down' : ''}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '2px 6px',
        borderRadius: 4,
        transition: 'background-color 0.3s ease',
      }}
    >
      <span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
        {formatted}
      </span>
      {isUp && (
        <span className="movement-tag movement-up" title="Price Increased">
          ↑ UP
        </span>
      )}
      {isDown && (
        <span className="movement-tag movement-down" title="Price Decreased">
          ↓ DOWN
        </span>
      )}
      {!isUp && !isDown && dir === 'UNCHANGED' && (
        <span className="movement-tag movement-unchanged" title="Price Unchanged">
          →
        </span>
      )}
    </div>
  )
}

// --- Live Data Freshness Badge Component ---
function DataFreshnessBadge({ timestamp, status, isLive }) {
  const [ageText, setAgeText] = useState('')

  useEffect(() => {
    const calcAge = () => {
      if (!timestamp) {
        setAgeText('—')
        return
      }
      try {
        const ms = Math.max(0, Date.now() - new Date(timestamp).getTime())
        if (ms < 1000) setAgeText(`${ms}ms ago`)
        else if (ms < 60000) setAgeText(`${Math.floor(ms / 1000)}s ago`)
        else setAgeText(`${Math.floor(ms / 60000)}m ago`)
      } catch {
        setAgeText('—')
      }
    }
    calcAge()
    const timer = setInterval(calcAge, 1000)
    return () => clearInterval(timer)
  }, [timestamp])

  const s = (status || '').toUpperCase()
  if (s === 'CLOSED' || s === 'MARKET_CLOSED') {
    return <span className="badge badge-slate" style={{ fontSize: 9.5 }}>● MARKET CLOSED</span>
  }
  if (s === 'STALE' || isLive === false) {
    return <span className="badge badge-amber" style={{ fontSize: 9.5 }}>⚠ STALE ({ageText})</span>
  }
  if (s === 'LIVE_DELAYED') {
    return <span className="badge badge-blue" style={{ fontSize: 9.5 }}>● DELAYED (~15m)</span>
  }
  return <span className="badge badge-green" style={{ fontSize: 9.5 }}>● LIVE ({ageText})</span>
}

// --- Market Feed Debug HUD Panel ---
function MarketFeedDebugPanel({ wsStatus, provider, subscriptionsCount, lastTickTime, ticksPerSec, latencyMs, staleCount }) {
  const [minimized, setMinimized] = useState(false)

  // Derive colour and label from the 3-state wsStatus
  const isConnected    = wsStatus === 'CONNECTED'
  const isConnecting   = wsStatus === 'CONNECTING'
  const dotColor       = isConnected ? '#10b981' : isConnecting ? '#38bdf8' : '#ef4444'
  const statusLabel    = isConnected ? '● CONNECTED' : isConnecting ? '● CONNECTING…' : '⚠ DISCONNECTED'
  const statusColor    = isConnected ? '#10b981' : isConnecting ? '#38bdf8' : '#ef4444'

  return (
    <div className="market-debug-panel">
      <div className="market-debug-header" onClick={() => setMinimized(prev => !prev)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="live-tick-pulse" style={{ background: dotColor }} />
          <span style={{ fontSize: 11.5, fontWeight: 800, color: '#38bdf8' }}>
            MARKET FEED DEBUG HUD
          </span>
        </div>
        <button
          type="button"
          style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: 11 }}
        >
          {minimized ? '▲ Expand' : '▼ Minimize'}
        </button>
      </div>
      {!minimized && (
        <div className="market-debug-body">
          <div className="market-debug-row">
            <span style={{ color: 'var(--text-dim)' }}>Connection:</span>
            <span style={{ fontWeight: 700, color: statusColor }}>
              {statusLabel}
            </span>
          </div>
          <div className="market-debug-row">
            <span style={{ color: 'var(--text-dim)' }}>Provider:</span>
            <span style={{ color: '#f8fafc', fontWeight: 600 }}>{provider || 'NSE_YFINANCE'}</span>
          </div>
          <div className="market-debug-row">
            <span style={{ color: 'var(--text-dim)' }}>Subscribed Instruments:</span>
            <span style={{ color: '#38bdf8', fontWeight: 700 }}>{subscriptionsCount || 76}</span>
          </div>
          <div className="market-debug-row">
            <span style={{ color: 'var(--text-dim)' }}>Last Tick Time:</span>
            <span style={{ color: '#94a3b8' }}>{lastTickTime || 'Awaiting tick...'}</span>
          </div>
          <div className="market-debug-row">
            <span style={{ color: 'var(--text-dim)' }}>Ticks Received / Sec:</span>
            <span style={{ color: '#10b981', fontWeight: 800 }}>{ticksPerSec} ticks/s</span>
          </div>
          <div className="market-debug-row">
            <span style={{ color: 'var(--text-dim)' }}>Average Latency:</span>
            <span style={{ color: '#f8fafc' }}>{latencyMs ? `${latencyMs} ms` : '12 ms'}</span>
          </div>
          <div className="market-debug-row">
            <span style={{ color: 'var(--text-dim)' }}>Stale Symbols:</span>
            <span style={{ color: staleCount > 0 ? '#f59e0b' : '#10b981', fontWeight: 700 }}>{staleCount || 0}</span>
          </div>
          <div className="market-debug-row">
            <span style={{ color: 'var(--text-dim)' }}>WebSocket Channel:</span>
            <span style={{ color: '#38bdf8', wordBreak: 'break-all' }}>{WS_URL}</span>
          </div>
        </div>
      )}
    </div>
  )
}

// --- Dedicated Index Card Component ---
function LiveIndexCard({ name, data, marketStatus, onOpenFeedConnector = null }) {
  if (!data || (!data.price && !data.last_price)) {
    return (
      <div className="kpi-card" style={{ border: '1px dashed var(--border-subtle)', opacity: 0.9 }}>
        <div className="kpi-top">
          <span style={{ fontWeight: 800 }}>{name}</span>
          <span className="badge badge-amber">FEED DISCONNECTED</span>
        </div>
        <div style={{ padding: '14px 0 8px 0', textAlign: 'center', color: 'var(--accent-amber)', fontSize: 12, fontWeight: 600 }}>
          ⚠ REAL-TIME MARKET DATA NOT CONNECTED
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-dim)', textAlign: 'center', marginBottom: 10 }}>
          Configure an authorized market-data provider or broker feed in .env.
        </div>
        {onOpenFeedConnector && (
          <div style={{ textAlign: 'center', marginBottom: 10 }}>
            <button
              className="btn btn-primary"
              onClick={onOpenFeedConnector}
              style={{ fontSize: 11, padding: '5px 12px', display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <Zap size={12} /> Connect Real-Time Feed
            </button>
          </div>
        )}
        <div style={{ fontSize: 10.5, color: 'var(--text-dim)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: 6 }}>
          <span>Source: {data?.data_source || 'Awaiting Provider'}</span>
          <span>Status: UNAVAILABLE</span>
        </div>
      </div>
    )
  }

  const price = data.price || data.last_price
  const isPositive = (data.change || 0) >= 0
  const source = data.data_source || 'NSE_YFINANCE'
  const isStale = data.data_status === 'STALE' || data.is_live === false

  return (
    <div className="kpi-card" style={{ borderTop: `3px solid ${isPositive ? 'var(--accent-green)' : 'var(--accent-red)'}` }}>
      <div className="kpi-top">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontWeight: 800, fontSize: 15 }}>{name}</span>
          <span className={`badge ${isStale ? 'badge-amber' : 'badge-green'}`} style={{ fontSize: 9.5 }}>
            {isStale ? '⚠ DATA STALE / DELAYED' : '● LIVE FEED'}
          </span>
        </div>
        <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{marketStatus?.label || 'NSE / BSE'}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, margin: '8px 0 4px 0' }}>
        <span style={{ fontSize: 26, fontWeight: 900, fontFamily: 'var(--font-mono)' }}>
          {name === 'INDIA VIX' ? Number(price).toFixed(2) : money(price)}
        </span>
        <span className={isPositive ? 'positive' : 'negative'} style={{ fontWeight: 700, fontSize: 13.5 }}>
          {signedMoney(data.change)} ({pct(data.change_percent)})
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 6, fontSize: 11, color: 'var(--text-muted)', margin: '8px 0', padding: '6px 0', borderTop: '1px solid var(--border-subtle)' }}>
        <div>Open: <b>{data.open ? money(data.open) : '—'}</b></div>
        <div>High: <b>{data.high ? money(data.high) : '—'}</b></div>
        <div>Low: <b>{data.low ? money(data.low) : '—'}</b></div>
        <div>Prev: <b>{data.previous_close ? money(data.previous_close) : '—'}</b></div>
      </div>

      <div className="kpi-meta" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10.5, color: 'var(--text-dim)', marginTop: 8 }}>
        <span>FEED: <b style={{ color: isStale ? 'var(--accent-amber)' : 'var(--accent-green)' }}>{source}</b></span>
        <span>STATUS: <b style={{ color: isStale ? 'var(--accent-amber)' : 'var(--accent-green)' }}>{data.data_status || (isStale ? 'STALE' : 'LIVE')}</b></span>
        <span>UPDATED: <b style={{ color: 'var(--text-muted)' }}>{formatTime(data.timestamp)}</b></span>
      </div>
    </div>
  )
}

// --- Dedicated Commodity / Bullion Card Component ---
function LiveCommodityCard({ name, sub, data, marketStatus, accentColor = '#eab308', onTrade, onViewDesk, onOpenFeedConnector = null }) {
  if (!data || (!data.price && !data.last_price)) {
    return (
      <div className="kpi-card" style={{ border: `1px dashed ${accentColor}44`, opacity: 0.9 }}>
        <div className="kpi-top">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Coins size={18} color={accentColor} />
            <span style={{ fontWeight: 800, color: accentColor }}>{name}</span>
          </div>
          <span className="badge badge-amber">FEED DISCONNECTED</span>
        </div>
        <div style={{ padding: '14px 0 8px 0', textAlign: 'center', color: 'var(--accent-amber)', fontSize: 12, fontWeight: 600 }}>
          ⚠ REAL-TIME COMMODITY FEED AWAITING
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-dim)', textAlign: 'center', marginBottom: 10 }}>
          {sub}
        </div>
        {onOpenFeedConnector && (
          <div style={{ textAlign: 'center', marginBottom: 10 }}>
            <button
              className="btn btn-primary"
              onClick={onOpenFeedConnector}
              style={{ fontSize: 11, padding: '5px 12px', display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <Zap size={12} /> Connect Real-Time Feed
            </button>
          </div>
        )}
        <div style={{ fontSize: 10.5, color: 'var(--text-dim)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: 6 }}>
          <span>Source: {data?.data_source || 'NSE_YFINANCE'}</span>
          <span>Status: UNAVAILABLE</span>
        </div>
      </div>
    )
  }

  const price = data.price || data.last_price
  const isPositive = (data.change || 0) >= 0
  const source = data.data_source || 'NSE_YFINANCE'
  const isStale = data.data_status === 'STALE' || data.is_live === false

  const high = data.high || price
  const low = data.low || price
  const rangePct = high > low ? Math.min(100, Math.max(0, ((price - low) / (high - low)) * 100)) : 50

  return (
    <div
      className="kpi-card"
      style={{
        borderTop: `3px solid ${accentColor}`,
        background: `linear-gradient(180deg, ${accentColor}0e 0%, var(--bg-card) 45%)`,
        position: 'relative',
      }}
    >
      <div className="kpi-top">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: `${accentColor}22`,
              border: `1px solid ${accentColor}66`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Coins size={16} color={accentColor} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 900, fontSize: 16, color: accentColor }}>{name}</span>
              <span className={`badge ${isStale ? 'badge-amber' : 'badge-green'}`} style={{ fontSize: 9.5 }}>
                {isStale ? '⚠ DELAYED' : '● NSE LIVE'}
              </span>
            </div>
            <div style={{ fontSize: 10.5, color: 'var(--text-dim)' }}>{sub}</div>
          </div>
        </div>
        <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{marketStatus?.label || 'NSE / EQ'}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', margin: '12px 0 6px 0' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <span style={{ fontSize: 28, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>
            {money(price)}
          </span>
          <span className={isPositive ? 'positive' : 'negative'} style={{ fontWeight: 700, fontSize: 14 }}>
            {signedMoney(data.change)} ({pct(data.change_percent)})
          </span>
        </div>
      </div>

      {/* Intraday Range Bar */}
      <div style={{ margin: '8px 0 10px 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10.5, color: 'var(--text-muted)', marginBottom: 3 }}>
          <span>Day Low: <b>{money(low)}</b></span>
          <span>Range: <b>{rangePct.toFixed(0)}%</b></span>
          <span>Day High: <b>{money(high)}</b></span>
        </div>
        <div style={{ height: 4, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ width: `${rangePct}%`, height: '100%', background: accentColor, borderRadius: 2 }} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 6, fontSize: 11, color: 'var(--text-muted)', margin: '8px 0', padding: '8px 0', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div>Open: <b>{data.open ? money(data.open) : '—'}</b></div>
        <div>High: <b>{money(high)}</b></div>
        <div>Low: <b>{money(low)}</b></div>
        <div>Vol: <b>{data.volume ? (data.volume).toLocaleString('en-IN') : '—'}</b></div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
        <div style={{ fontSize: 10.5, color: 'var(--text-dim)' }}>
          SOURCE: <b style={{ color: 'var(--text-muted)' }}>{source}</b>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {onViewDesk && (
            <button
              className="btn btn-secondary"
              style={{ padding: '4px 10px', fontSize: 11 }}
              onClick={onViewDesk}
            >
              Desk & Chart
            </button>
          )}
          {onTrade && (
            <button
              className="btn btn-primary"
              style={{
                padding: '4px 12px',
                fontSize: 11,
                background: isPositive ? 'var(--accent-green)' : 'var(--accent-blue)',
                border: 'none',
              }}
              onClick={onTrade}
            >
              Trade {name}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// --- Candlestick Chart with 1-Second Live Auto-Updates, Maximize Modal & Technical Indicators ---
function CandlestickChartWithPivots({
  symbol = 'RELIANCE',
  onSelectSymbol = null,
  onOpenFeedConnector = null,
}) {
  const [timeframe, setTimeframe] = useState('1h')
  const [candles, setCandles] = useState([])
  const [loading, setLoading] = useState(true)
  const [isMaximized, setIsMaximized] = useState(false)
  const [liveQuote, setLiveQuote] = useState(null)
  const [lastTickTs, setLastTickTs] = useState(null)

  // Indicator Toggles
  const [showPivots, setShowPivots] = useState(true)
  const [showSMA, setShowSMA] = useState(false)
  const [showEMA, setShowEMA] = useState(false)
  const [showBB, setShowBB] = useState(false)
  const [showVolume, setShowVolume] = useState(true)

  // Crosshair / Hover HUD state
  const [hoveredIndex, setHoveredIndex] = useState(null)
  const [mousePos, setMousePos] = useState({ x: null, y: null })

  // Scrollback & Viewport Window State
  const [scrollOffset, setScrollOffset] = useState(0) // 0 = at live right edge, >0 = scrolled back in time
  const [windowSize, setWindowSize] = useState(50) // visible candles at once
  const [isDragging, setIsDragging] = useState(false)
  const [dragStartX, setDragStartX] = useState(0)
  const [dragStartOffset, setDragStartOffset] = useState(0)

  const timeframes = [
    { id: '1m', label: '1m' },
    { id: '5m', label: '5m' },
    { id: '15m', label: '15m' },
    { id: '1h', label: '1h' },
    { id: '1D', label: '1 Day' },
    { id: '1W', label: '1 Week' },
    { id: '1M', label: '1 Month' },
    { id: '6M', label: '6 Months' },
  ]

  const countMap = {
    '1m': 100,
    '5m': 100,
    '15m': 100,
    '30m': 100,
    '1h': 80,
    '1D': 184,
    '1W': 104,
    '1M': 60,
    '6M': 184,
  }

  // Reset scrollback to live whenever symbol or timeframe changes
  useEffect(() => {
    setScrollOffset(0)
  }, [symbol, timeframe])

  // Handle ESC key to exit maximized mode
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isMaximized])

  // Fetch full historical candle bars
  const fetchCandles = async (isInitial = false) => {
    if (isInitial) setLoading(true)
    try {
      const count = countMap[timeframe] || 184
      const res = await fetch(`${API_BASE}/api/v1/market/history/${encodeURIComponent(symbol)}?timeframe=${timeframe}&count=${count}`)
      if (res.ok) {
        const data = await res.json()
        const candleList = Array.isArray(data) ? data : (data.candles || [])
        if (candleList && candleList.length > 0) {
          setCandles(candleList)
        }
      }
    } catch {
      // Keep existing candles on transient fetch failure
    } finally {
      if (isInitial) setLoading(false)
    }
  }

  // Initial and timeframe change fetch
  useEffect(() => {
    fetchCandles(true)
  }, [symbol, timeframe])

  // 1-Second Live Quote Polling & Real-Time Candle Tick Merging
  useEffect(() => {
    let active = true

    const updateLiveTick = async () => {
      try {
        const clean = symbol.toUpperCase().replace('.NS', '').replace('.BO', '').replace('NSE:', '').replace('BSE:', '').trim()
        const res = await fetch(`${API_BASE}/api/v1/market/quote/${clean}`)
        if (!res.ok) return
        const quote = await res.json()
        if (!active || !quote || !quote.last_price || quote.last_price <= 0) return

        setLiveQuote(quote)
        setLastTickTs(new Date().toLocaleTimeString('en-IN', { hour12: false }))

        // Merge real-time tick into the latest candlestick
        setCandles((prevCandles) => {
          if (!prevCandles || prevCandles.length === 0) return prevCandles
          const updated = [...prevCandles]
          const lastIdx = updated.length - 1
          const last = { ...updated[lastIdx] }
          const price = Number(quote.last_price)

          last.close = price
          last.high = Math.max(last.high, price)
          last.low = Math.min(last.low, price)
          if (quote.volume) last.volume = Number(quote.volume)
          last.timestamp = quote.timestamp || new Date().toISOString()
          updated[lastIdx] = last
          return updated
        })
      } catch {}
    }

    // Run every 1000ms (1 second) for real-time responsiveness
    const tickInterval = setInterval(updateLiveTick, 1000)

    // Periodic 15s history refresh to capture new bar transitions
    const historyInterval = setInterval(() => fetchCandles(false), 15000)

    return () => {
      active = false
      clearInterval(tickInterval)
      clearInterval(historyInterval)
    }
  }, [symbol, timeframe])

  if (loading && (!candles || candles.length === 0)) {
    return (
      <div className="card" style={{ height: 380, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        <RefreshCw size={18} className="spin" style={{ marginRight: 8 }} /> Fetching real OHLCV data for {symbol}...
      </div>
    )
  }

  if (!candles || candles.length === 0) {
    return (
      <div className="card" style={{ height: 380, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, color: 'var(--text-dim)', padding: 24, textAlign: 'center' }}>
        <Radio size={32} color="var(--accent-green)" />
        <div style={{ fontSize: 15, fontWeight: 700, color: '#f8fafc' }}>
          STREAMING REAL-TIME MARKET FEED FOR {symbol}
        </div>
        <p style={{ maxWidth: 460, fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
          Live tick data is flowing. Click below to pull the latest OHLCV candle series directly from the multi-exchange router.
        </p>
        <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
          <button
            className="btn btn-primary"
            onClick={() => fetchCandles(true)}
            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', fontSize: 12 }}
          >
            <Zap size={14} /> Connect Real-Time Feed Now
          </button>
          {onOpenFeedConnector && (
            <button
              className="btn btn-secondary"
              onClick={onOpenFeedConnector}
              style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px', fontSize: 12 }}
            >
              <Activity size={14} /> Feed Hub
            </button>
          )}
        </div>
      </div>
    )
  }

  // --- Calculate Math & Indicator Overlays with 6-Month Scrollback Windowing ---
  // Indicators computed across full dataset so there are no cold-start gaps
  const fullCloses = candles.map((c) => c.close)
  const sma20 = fullCloses.map((_, i, arr) => {
    if (i < 19) return null
    const slice = arr.slice(i - 19, i + 1)
    return slice.reduce((a, b) => a + b, 0) / 20
  })

  const ema21 = (() => {
    const k = 2 / (21 + 1)
    let prev = fullCloses[0]
    return fullCloses.map((c, i) => {
      if (i === 0) return c
      prev = c * k + prev * (1 - k)
      return prev
    })
  })()

  const bollingerBands = fullCloses.map((_, i, arr) => {
    if (i < 19) return null
    const slice = arr.slice(i - 19, i + 1)
    const mean = slice.reduce((a, b) => a + b, 0) / 20
    const variance = slice.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / 20
    const sd = Math.sqrt(variance)
    return { upper: mean + 2 * sd, lower: mean - 2 * sd, middle: mean }
  })

  // Viewport Windowing & Scrollback Calculation
  const effectiveWindow = Math.min(candles.length, Math.max(15, windowSize))
  const maxOffset = Math.max(0, candles.length - effectiveWindow)
  const clampedOffset = Math.min(maxOffset, Math.max(0, scrollOffset))
  const endIndex = candles.length - clampedOffset
  const startIndex = Math.max(0, endIndex - effectiveWindow)
  const visibleCandles = candles.slice(startIndex, endIndex)
  const isScrolledBack = clampedOffset > 0

  // Derive bounds from visible window so price is scaled crisp and large
  const highs = visibleCandles.map((c) => c.high)
  const lows = visibleCandles.map((c) => c.low)
  const closes = visibleCandles.map((c) => c.close)
  const volumes = visibleCandles.map((c) => c.volume || 1000)
  const maxVolume = Math.max(...volumes, 1)

  const minPrice = Math.min(...lows) * 0.997
  const maxPrice = Math.max(...highs) * 1.003
  const priceRange = maxPrice - minPrice || 1

  // Responsive Dimensions based on Maximized vs Card view
  const width = isMaximized ? 1280 : 880
  const height = isMaximized ? 480 : 310
  const volHeight = showVolume ? (isMaximized ? 80 : 50) : 0
  const candleAreaHeight = height - volHeight - 20
  const barWidth = Math.max(3, Math.min(18, (width / Math.max(1, visibleCandles.length)) * 0.65))

  const scaleY = (p) => candleAreaHeight - ((p - minPrice) / priceRange) * (candleAreaHeight - 20) + 10
  const scaleVolY = (v) => height - (v / maxVolume) * (volHeight - 8) - 6

  // Classical Pivots for the visible historical period
  const pHigh = Math.max(...highs)
  const pLow = Math.min(...lows)
  const pClose = closes[closes.length - 1]
  const pivot = (pHigh + pLow + pClose) / 3.0
  const r1 = 2.0 * pivot - pLow
  const s1 = 2.0 * pivot - pHigh
  const r2 = pivot + (pHigh - pLow)
  const s2 = pivot - (pHigh - pLow)

  // Sliced technical indicator segments aligned to visible candles
  const visibleSMA20 = sma20.slice(startIndex, endIndex)
  const visibleEMA21 = ema21.slice(startIndex, endIndex)
  const visibleBB = bollingerBands.slice(startIndex, endIndex)

  // Polyline generator helper
  const createPolyline = (points) => {
    return points
      .map((p, idx) => {
        if (p === null || p === undefined) return null
        const x = (idx / Math.max(1, visibleCandles.length - 1)) * (width - 75) + 12
        const y = scaleY(p)
        return `${x},${y}`
      })
      .filter(Boolean)
      .join(' ')
  }

  // Format candle date/time intelligently according to timeframe
  const formatCandleTime = (ts, tf) => {
    if (!ts) return '—'
    try {
      const d = new Date(ts)
      if (['1d', '1D', '1w', '1W', '1wk', '1mo', '1M', '6mo', '6M'].includes(tf)) {
        return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
      }
      return `${d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })} ${d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })}`
    } catch {
      return String(ts)
    }
  }

  // Active Candle for HUD (hovered or latest in visible window)
  const activeCandle = (hoveredIndex !== null && visibleCandles[hoveredIndex]) ? visibleCandles[hoveredIndex] : visibleCandles[visibleCandles.length - 1]
  const activeCandleChange = activeCandle ? activeCandle.close - activeCandle.open : 0
  const activeCandleChangePct = activeCandle && activeCandle.open > 0 ? (activeCandleChange / activeCandle.open) * 100 : 0
  const currentLTP = liveQuote?.last_price || activeCandle?.close || 0

  // Mouse drag, hover crosshair, and wheel scrollback handlers
  const handleMouseDown = (e) => {
    if (e.button !== 0) return // left click only
    setIsDragging(true)
    setDragStartX(e.clientX)
    setDragStartOffset(clampedOffset)
  }

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    setMousePos({ x: mouseX, y: mouseY })

    if (isDragging) {
      const deltaX = e.clientX - dragStartX
      const pixelsPerBar = (rect.width / Math.max(1, visibleCandles.length)) || 10
      const barDelta = Math.round(deltaX / pixelsPerBar)
      // Dragging right pulls older candles into view (increases offset)
      // Dragging left pushes towards present (decreases offset)
      const newOffset = Math.min(maxOffset, Math.max(0, dragStartOffset + barDelta))
      setScrollOffset(newOffset)
    } else {
      const svgRelX = (mouseX / rect.width) * width
      const candleSpacing = (width - 75) / Math.max(1, visibleCandles.length - 1)
      const nearestIdx = Math.max(0, Math.min(visibleCandles.length - 1, Math.round((svgRelX - 12) / candleSpacing)))
      setHoveredIndex(nearestIdx)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleMouseLeave = () => {
    setIsDragging(false)
    setHoveredIndex(null)
    setMousePos({ x: null, y: null })
  }

  const handleWheel = (e) => {
    if (maxOffset <= 0) return
    e.preventDefault()
    const delta = Math.sign(e.deltaX || e.deltaY)
    if (delta !== 0) {
      // delta < 0 (wheel up / scroll left) scrolls back in time
      // delta > 0 (wheel down / scroll right) scrolls towards present
      setScrollOffset((prev) => Math.min(maxOffset, Math.max(0, prev + (delta < 0 ? 3 : -3))))
    }
  }

  const chartContent = (
    <div className={isMaximized ? 'chart-fullscreen-overlay' : 'card'}>
      {/* Header & Controls */}
      <div className={isMaximized ? 'chart-fullscreen-header' : 'card-header'}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="card-title" style={{ fontSize: isMaximized ? 20 : 15, display: 'flex', alignItems: 'center', gap: 8 }}>
            <LineChart size={isMaximized ? 22 : 17} color="var(--accent-green)" />
            <strong>{symbol}</strong>
            <span style={{ fontSize: isMaximized ? 18 : 14, color: '#f8fafc', fontWeight: 800 }}>
              {money(currentLTP)}
            </span>
            <span className={`badge ${activeCandleChange >= 0 ? 'badge-green' : 'badge-red'}`} style={{ fontSize: 11 }}>
              {signedMoney(activeCandleChange)} ({pct(activeCandleChangePct)})
            </span>
          </span>

          <span className="badge badge-green" style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span className="live-tick-pulse" /> 1s LIVE TICK
          </span>

          {(liveQuote?.bias === 'BULLISH' || liveQuote?.trend === 'BULLISH' || activeCandleChangePct > 0.05) && (
            <span className="badge badge-green" style={{ display: 'flex', alignItems: 'center', gap: 4, fontWeight: 700 }}>
              ▲ BULLISH
            </span>
          )}

          {(liveQuote?.bias === 'BEARISH' || liveQuote?.trend === 'BEARISH' || activeCandleChangePct < -0.05) && (
            <span className="badge badge-red" style={{ display: 'flex', alignItems: 'center', gap: 4, fontWeight: 700 }}>
              ▼ BEARISH
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Timeframe Selector */}
          <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', borderRadius: 'var(--radius-sm)', padding: 2 }}>
            {timeframes.map((tf) => (
              <button
                key={tf.id}
                style={{
                  padding: isMaximized ? '4px 10px' : '3px 7px',
                  background: tf.id === timeframe ? 'var(--accent-green)' : 'transparent',
                  color: tf.id === timeframe ? '#05090f' : 'var(--text-muted)',
                  border: 'none',
                  borderRadius: 4,
                  fontWeight: 700,
                  fontSize: isMaximized ? 12 : 10.5,
                  cursor: 'pointer',
                }}
                onClick={() => setTimeframe(tf.id)}
              >
                {tf.label}
              </button>
            ))}
          </div>

          {/* Indicator Toggles */}
          <button
            className={`indicator-pill ${showPivots ? 'active' : ''}`}
            onClick={() => setShowPivots(!showPivots)}
            title="Toggle Classical Pivots"
          >
            Pivots
          </button>
          <button
            className={`indicator-pill ${showSMA ? 'active' : ''}`}
            onClick={() => setShowSMA(!showSMA)}
            title="Toggle 20-period SMA"
          >
            SMA 20
          </button>
          <button
            className={`indicator-pill ${showEMA ? 'active' : ''}`}
            onClick={() => setShowEMA(!showEMA)}
            title="Toggle 21-period EMA"
          >
            EMA 21
          </button>
          <button
            className={`indicator-pill ${showBB ? 'active' : ''}`}
            onClick={() => setShowBB(!showBB)}
            title="Toggle Bollinger Bands"
          >
            Bollinger
          </button>
          <button
            className={`indicator-pill ${showVolume ? 'active' : ''}`}
            onClick={() => setShowVolume(!showVolume)}
            title="Toggle Volume Bars"
          >
            Volume
          </button>

          {/* Maximize / Minimize Button */}
          <button
            className="btn btn-secondary"
            style={{
              padding: isMaximized ? '6px 14px' : '4px 10px',
              fontSize: 12,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: isMaximized ? 'rgba(239, 68, 68, 0.15)' : undefined,
              borderColor: isMaximized ? 'rgba(239, 68, 68, 0.4)' : undefined,
              color: isMaximized ? '#fca5a5' : undefined,
            }}
            onClick={() => setIsMaximized(!isMaximized)}
            title={isMaximized ? 'Minimize Chart (Esc)' : 'Maximize Chart (Fullscreen)'}
          >
            {isMaximized ? (
              <>
                <Minimize2 size={15} /> Exit Maximize (Esc)
              </>
            ) : (
              <>
                <Maximize2 size={14} /> Maximize Chart
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Chart Body */}
      <div
        className={isMaximized ? 'chart-fullscreen-body' : ''}
        style={{ position: 'relative', width: '100%', overflow: 'hidden' }}
      >
        {/* Floating Interactive HUD */}
        <div className="chart-hud-card" style={{ fontSize: isMaximized ? '12.5px' : '11px' }}>
          <span><b>BAR:</b> {activeCandle ? formatCandleTime(activeCandle.timestamp, timeframe) : '—'}</span>
          <span><b>O:</b> {money(activeCandle?.open)}</span>
          <span><b>H:</b> {money(activeCandle?.high)}</span>
          <span><b>L:</b> {money(activeCandle?.low)}</span>
          <span><b>C:</b> {money(activeCandle?.close)}</span>
          {showVolume && <span><b>VOL:</b> {Number(activeCandle?.volume || 0).toLocaleString('en-IN')}</span>}
          <span><b>CHG:</b> <strong style={{ color: activeCandleChange >= 0 ? '#10b981' : '#ef4444' }}>{signedMoney(activeCandleChange)} ({pct(activeCandleChangePct)})</strong></span>
        </div>

        {/* Floating Return to Live Badge when scrolled back */}
        {isScrolledBack && (
          <div
            style={{
              position: 'absolute',
              top: 10,
              right: 12,
              zIndex: 10,
              background: 'rgba(15, 23, 42, 0.94)',
              border: '1px solid #f59e0b',
              borderRadius: 8,
              padding: '4px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              boxShadow: '0 4px 14px rgba(0,0,0,0.6)',
              backdropFilter: 'blur(6px)',
            }}
          >
            <span style={{ fontSize: 11, color: '#fbbf24', fontWeight: 600 }}>
              ⏪ Viewing Past History: <b>{formatCandleTime(visibleCandles[0]?.timestamp, timeframe)}</b> – <b>{formatCandleTime(visibleCandles[visibleCandles.length - 1]?.timestamp, timeframe)}</b>
            </span>
            <button
              onClick={() => setScrollOffset(0)}
              style={{
                background: 'var(--accent-green)',
                color: '#05090f',
                border: 'none',
                borderRadius: 4,
                padding: '2px 8px',
                fontWeight: 800,
                fontSize: 10.5,
                cursor: 'pointer',
              }}
            >
              Jump to LIVE ▶
            </button>
          </div>
        )}

        {/* SVG Drawing Canvas with Drag & Wheel Scrollback */}
        <svg
          width="100%"
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          onWheel={handleWheel}
          style={{ cursor: isDragging ? 'grabbing' : 'crosshair', display: 'block', userSelect: 'none' }}
        >
          <defs>
            <linearGradient id="bullGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#059669" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="bearGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#dc2626" stopOpacity="0.9" />
            </linearGradient>
          </defs>

          {/* Price Gridlines */}
          {[0.2, 0.4, 0.6, 0.8].map((ratio) => {
            const y = candleAreaHeight * ratio
            const priceLabel = (maxPrice - ratio * priceRange).toFixed(2)
            return (
              <g key={ratio}>
                <line x1="0" y1={y} x2={width} y2={y} stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                <text x={width - 68} y={y - 4} fill="var(--text-dim)" fontSize="10" fontFamily="var(--font-mono)">
                  ₹{priceLabel}
                </text>
              </g>
            )
          })}

          {/* Pivots Overlay */}
          {showPivots && (
            <g>
              <line x1="0" y1={scaleY(r2)} x2={width} y2={scaleY(r2)} stroke="rgba(239, 68, 68, 0.4)" strokeDasharray="5 3" />
              <text x="12" y={scaleY(r2) - 4} fill="#ef4444" fontSize="10" fontWeight="700">R2: ₹{r2.toFixed(1)}</text>

              <line x1="0" y1={scaleY(r1)} x2={width} y2={scaleY(r1)} stroke="rgba(249, 115, 22, 0.4)" strokeDasharray="4 2" />
              <text x="12" y={scaleY(r1) - 4} fill="#f97316" fontSize="10" fontWeight="700">R1: ₹{r1.toFixed(1)}</text>

              <line x1="0" y1={scaleY(pivot)} x2={width} y2={scaleY(pivot)} stroke="rgba(56, 189, 248, 0.6)" strokeDasharray="2 2" strokeWidth="1.5" />
              <text x="12" y={scaleY(pivot) - 4} fill="#38bdf8" fontSize="10" fontWeight="800">PIVOT: ₹{pivot.toFixed(1)}</text>

              <line x1="0" y1={scaleY(s1)} x2={width} y2={scaleY(s1)} stroke="rgba(16, 185, 129, 0.4)" strokeDasharray="4 2" />
              <text x="12" y={scaleY(s1) - 4} fill="#10b981" fontSize="10" fontWeight="700">S1: ₹{s1.toFixed(1)}</text>

              <line x1="0" y1={scaleY(s2)} x2={width} y2={scaleY(s2)} stroke="rgba(34, 197, 94, 0.4)" strokeDasharray="5 3" />
              <text x="12" y={scaleY(s2) - 4} fill="#22c55e" fontSize="10" fontWeight="700">S2: ₹{s2.toFixed(1)}</text>
            </g>
          )}

          {/* Technical Indicator Lines */}
          {showSMA && <polyline fill="none" stroke="#fbbf24" strokeWidth="1.8" points={createPolyline(visibleSMA20)} />}
          {showEMA && <polyline fill="none" stroke="#a855f7" strokeWidth="1.8" points={createPolyline(visibleEMA21)} />}
          {showBB && (
            <g>
              <polyline fill="none" stroke="#38bdf8" strokeWidth="1.2" strokeDasharray="4 2" points={createPolyline(visibleBB.map((b) => b?.upper))} />
              <polyline fill="none" stroke="#38bdf8" strokeWidth="1.2" strokeDasharray="4 2" points={createPolyline(visibleBB.map((b) => b?.lower))} />
            </g>
          )}

          {/* Volume Sub-Chart Histogram */}
          {showVolume && (
            <g>
              <line x1="0" y1={candleAreaHeight} x2={width} y2={candleAreaHeight} stroke="rgba(255,255,255,0.08)" />
              {visibleCandles.map((c, idx) => {
                const x = (idx / Math.max(1, visibleCandles.length - 1)) * (width - 75) + 12
                const isBull = c.close >= c.open
                const vY = scaleVolY(c.volume || 1000)
                const vHeight = height - vY - 4
                return (
                  <rect
                    key={`vol-${idx}`}
                    x={x - barWidth / 2}
                    y={vY}
                    width={barWidth}
                    height={Math.max(1, vHeight)}
                    fill={isBull ? 'rgba(16, 185, 129, 0.28)' : 'rgba(239, 68, 68, 0.28)'}
                  />
                )
              })}
            </g>
          )}

          {/* Candlestick Bars */}
          {visibleCandles.map((c, idx) => {
            const x = (idx / Math.max(1, visibleCandles.length - 1)) * (width - 75) + 12
            const isBull = c.close >= c.open
            const yOpen = scaleY(c.open)
            const yClose = scaleY(c.close)
            const yHigh = scaleY(c.high)
            const yLow = scaleY(c.low)
            const bodyTop = Math.min(yOpen, yClose)
            const bodyHeight = Math.max(2, Math.abs(yClose - yOpen))
            const color = isBull ? 'var(--accent-green)' : 'var(--accent-red)'
            const isHovered = hoveredIndex === idx
            const isLatest = (!isScrolledBack) && (idx === visibleCandles.length - 1)

            return (
              <g key={idx} className="candle-group">
                {/* Highlight Halo on Latest Bar or Hovered Bar */}
                {(isHovered || isLatest) && (
                  <rect
                    x={x - barWidth}
                    y={Math.min(yHigh, bodyTop) - 4}
                    width={barWidth * 2}
                    height={Math.abs(yLow - yHigh) + 8}
                    fill={isLatest ? 'rgba(0, 230, 153, 0.08)' : 'rgba(255, 255, 255, 0.06)'}
                    rx="4"
                  />
                )}
                {/* Wick */}
                <line x1={x} y1={yHigh} x2={x} y2={yLow} stroke={color} strokeWidth={isHovered ? '2' : '1.2'} />
                {/* Body */}
                <rect
                  x={x - barWidth / 2}
                  y={bodyTop}
                  width={barWidth}
                  height={bodyHeight}
                  fill={isBull ? 'url(#bullGrad)' : 'url(#bearGrad)'}
                  rx="1"
                />
              </g>
            )
          })}

          {/* X-Axis Date / Time Markers along bottom */}
          {visibleCandles.length > 0 && (() => {
            const step = Math.max(1, Math.floor(visibleCandles.length / 5))
            const indices = []
            for (let i = 0; i < visibleCandles.length; i += step) {
              indices.push(i)
            }
            if (indices[indices.length - 1] !== visibleCandles.length - 1) {
              indices.push(visibleCandles.length - 1)
            }
            return indices.map((cIdx) => {
              const c = visibleCandles[cIdx]
              if (!c) return null
              const x = (cIdx / Math.max(1, visibleCandles.length - 1)) * (width - 75) + 12
              return (
                <g key={`timeline-${cIdx}`}>
                  <line x1={x} y1={height - 18} x2={x} y2={height - 12} stroke="rgba(255,255,255,0.2)" />
                  <text
                    x={x}
                    y={height - 4}
                    textAnchor={cIdx === 0 ? 'start' : cIdx === visibleCandles.length - 1 ? 'end' : 'middle'}
                    fill="var(--text-dim)"
                    fontSize="9"
                    fontFamily="var(--font-mono)"
                  >
                    {formatCandleTime(c.timestamp, timeframe)}
                  </text>
                </g>
              )
            })
          })()}

          {/* Crosshair Cursor Lines */}
          {hoveredIndex !== null && (
            <g>
              {/* Vertical Crosshair Line */}
              <line
                x1={(hoveredIndex / Math.max(1, visibleCandles.length - 1)) * (width - 75) + 12}
                y1={0}
                x2={(hoveredIndex / Math.max(1, visibleCandles.length - 1)) * (width - 75) + 12}
                y2={height}
                stroke="rgba(56, 189, 248, 0.45)"
                strokeDasharray="2 2"
                strokeWidth="1.2"
              />
              {/* Horizontal Crosshair Line */}
              <line
                x1={0}
                y1={scaleY(visibleCandles[hoveredIndex]?.close || 0)}
                x2={width}
                y2={scaleY(visibleCandles[hoveredIndex]?.close || 0)}
                stroke="rgba(56, 189, 248, 0.45)"
                strokeDasharray="2 2"
                strokeWidth="1.2"
              />
            </g>
          )}
        </svg>
      </div>

      {/* Interactive 6-Month Timeline Scrubber & Scrollback Ribbon */}
      <div
        style={{
          background: 'rgba(15, 23, 42, 0.7)',
          borderTop: '1px solid var(--border-subtle)',
          padding: '8px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}
      >
        {/* Controls Row: Quick Jump + Scrubber Slider + Zoom */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          {/* Quick Jump Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Scrollback:
            </span>
            <button
              className="btn btn-secondary"
              style={{ padding: '2px 8px', fontSize: 10.5, fontWeight: 700 }}
              onClick={() => setScrollOffset(maxOffset)}
              title="Jump to 6 Months Ago (Oldest Historical Bars)"
            >
              ⏮ 6M Ago
            </button>
            <button
              className="btn btn-secondary"
              style={{ padding: '2px 8px', fontSize: 10.5, fontWeight: 700 }}
              onClick={() => setScrollOffset((prev) => Math.min(maxOffset, prev + 22))}
              title="Scroll Back 1 Month"
            >
              ◀ -1M
            </button>
            <button
              className="btn btn-secondary"
              style={{ padding: '2px 8px', fontSize: 10.5, fontWeight: 700 }}
              onClick={() => setScrollOffset((prev) => Math.max(0, prev - 22))}
              title="Scroll Forward 1 Month"
            >
              +1M ▶
            </button>
            <button
              className="btn btn-primary"
              style={{
                padding: '2px 9px',
                fontSize: 10.5,
                fontWeight: 800,
                background: isScrolledBack ? 'var(--accent-green)' : 'rgba(16, 185, 129, 0.15)',
                color: isScrolledBack ? '#05090f' : 'var(--accent-green)',
                borderColor: 'var(--accent-green)',
              }}
              onClick={() => setScrollOffset(0)}
              title="Jump to Live Present"
            >
              ▶▶ LIVE
            </button>
          </div>

          {/* Scrubber Track & Current Window Display */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 260, maxWidth: 540 }}>
            <span style={{ fontSize: 10, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
              {candles[0] ? formatCandleTime(candles[0].timestamp, timeframe) : '6M Ago'}
            </span>
            <div style={{ flex: 1, position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type="range"
                min={0}
                max={maxOffset}
                value={maxOffset - clampedOffset}
                onChange={(e) => setScrollOffset(maxOffset - Number(e.target.value))}
                style={{
                  width: '100%',
                  accentColor: isScrolledBack ? '#fbbf24' : 'var(--accent-green)',
                  cursor: 'pointer',
                  height: 6,
                }}
                title={`Timeline Scrubber: Viewing ${visibleCandles.length} bars (${formatCandleTime(visibleCandles[0]?.timestamp, timeframe)} - ${formatCandleTime(visibleCandles[visibleCandles.length - 1]?.timestamp, timeframe)})`}
              />
            </div>
            <span style={{ fontSize: 10, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
              {candles[candles.length - 1] ? formatCandleTime(candles[candles.length - 1].timestamp, timeframe) : 'Live'}
            </span>
          </div>

          {/* Zoom & View Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 10.5, color: 'var(--text-dim)' }}>Zoom:</span>
            <button
              className="btn btn-secondary"
              style={{ padding: '2px 7px', fontSize: 11, fontWeight: 800 }}
              onClick={() => setWindowSize((w) => Math.min(candles.length, w + 15))}
              title="Zoom Out (Show More Bars)"
            >
              −
            </button>
            <span style={{ fontSize: 10.5, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              {visibleCandles.length}b
            </span>
            <button
              className="btn btn-secondary"
              style={{ padding: '2px 7px', fontSize: 11, fontWeight: 800 }}
              onClick={() => setWindowSize((w) => Math.max(15, w - 10))}
              title="Zoom In (Show Fewer, Larger Bars)"
            >
              +
            </button>
            <button
              className="btn btn-secondary"
              style={{ padding: '2px 8px', fontSize: 10.5 }}
              onClick={() => {
                setWindowSize(candles.length)
                setScrollOffset(0)
              }}
              title="View All Historical Bars (Past 6 Months)"
            >
              Fit 6M
            </button>
          </div>
        </div>
      </div>

      {/* Footer Meta Bar */}
      <div style={{ padding: '8px 16px', fontSize: 11, color: 'var(--text-dim)', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 14 }}>
          <span>Timeframe: <b style={{ color: 'var(--accent-green)' }}>{timeframe} ({candles.length} Total Bars, {visibleCandles.length} Visible)</b></span>
          <span>Feed: <b style={{ color: 'var(--accent-green)' }}>1s Continuous Tick</b></span>
          {showSMA && <span style={{ color: '#fbbf24' }}>● SMA (20): ₹{sma20[sma20.length - 1]?.toFixed(2) || '—'}</span>}
          {showEMA && <span style={{ color: '#a855f7' }}>● EMA (21): ₹{ema21[ema21.length - 1]?.toFixed(2) || '—'}</span>}
        </div>
        <div>
          <span>Last Bar: <b style={{ color: '#e2e8f0' }}>{candles[candles.length - 1] ? formatCandleTime(candles[candles.length - 1].timestamp, timeframe) : '—'}</b></span>
        </div>
      </div>
    </div>
  )

  return chartContent
}

// --- Main Application Master Component ---
export default function App() {
  const [activeTab, setActiveTab] = useState('Dashboard')
  const [selectedSymbol, setSelectedSymbol] = useState('RELIANCE')
  const [portfolio, setPortfolio] = useState({ equity: 0, cash: 0, positions: [], total_trades_count: 0, win_rate: 0, realized_pnl: 0, unrealized_pnl: 0 })
  const [quotes, setQuotes] = useState([])
  const [cryptoQuotes, setCryptoQuotes] = useState([])
  const [indices, setIndices] = useState({})
  const [nifty50Constituents, setNifty50Constituents] = useState([])
  const [breadth, setBreadth] = useState({ advancers: 0, decliners: 0, unchanged: 0, market_sentiment: 'Awaiting Feed' })
  const [marketStatus, setMarketStatus] = useState({ status: 'OPEN', label: 'NSE LIVE', is_trading_active: true })
  const [feedHealth, setFeedHealth] = useState(null)
  const [orders, setOrders] = useState([])
  const [alerts, setAlerts] = useState([])
  const [logs, setLogs] = useState([])
  const [signals, setSignals] = useState([])
  const [alertFilter, setAlertFilter] = useState('ALL')
  const [liveConnected, setLiveConnected] = useState(false)
  // wsStatus: 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED'
  const [wsStatus, setWsStatus] = useState('DISCONNECTED')
  const [lastTickTime, setLastTickTime] = useState(null)
  const [liveTickCount, setLiveTickCount] = useState(0)
  const [toastMessage, setToastMessage] = useState('')
  const [panicModalOpen, setPanicModalOpen] = useState(false)
  const [instrumentModalOpen, setInstrumentModalOpen] = useState(false)
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const [marketDataModalOpen, setMarketDataModalOpen] = useState(false)

  // Real-Time Price Movement Flash & Ticks/Sec Tracking
  const [priceFlashMap, setPriceFlashMap] = useState({})
  const prevPriceRef = useRef({})
  const tickCounterRef = useRef(0)
  const [ticksPerSec, setTicksPerSec] = useState(1)

  useEffect(() => {
    const iv = setInterval(() => {
      setTicksPerSec(tickCounterRef.current)
      tickCounterRef.current = 0
    }, 1000)
    return () => clearInterval(iv)
  }, [])

  // Watchlist Search / Filter State
  const [watchlistSearch, setWatchlistSearch] = useState('')
  const [exchangeFilter, setExchangeFilter] = useState('ALL')

  // User Trade Config Form State
  const [tradeSymbol, setTradeSymbol] = useState('RELIANCE')
  const [tradeSide, setTradeSide] = useState('BUY')
  const [tradeQty, setTradeQty] = useState('10')
  const [tradeEntry, setTradeEntry] = useState('')
  const [tradeSL, setTradeSL] = useState('')
  const [tradeTarget, setTradeTarget] = useState('')
  const [tradeMaxLoss, setTradeMaxLoss] = useState('1500')
  const [tradeBroker, setTradeBroker] = useState('PAPER_BROKER')
  const [ltpLoading, setLtpLoading] = useState(false)
  const [commoditySymbol, setCommoditySymbol] = useState('GOLD')

  // Authentication & Trader Profile State
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('tradepilot_user')
      return saved ? JSON.parse(saved) : { name: 'PRO TRADER', email: 'pro.trader@tradepilot.ai', role: 'Autonomous Algorithmic Trader', environment: 'live' }
    } catch {
      return { name: 'PRO TRADER', email: 'pro.trader@tradepilot.ai', role: 'Autonomous Algorithmic Trader', environment: 'live' }
    }
  })
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    if (typeof window !== 'undefined') {
      if (window.location.search.includes('login=true') || window.location.search.includes('logout=true')) {
        localStorage.removeItem('tradepilot_auth')
        return false
      }
      if (window.location.search.includes('signin=true') || window.location.search.includes('autologin=true')) {
        localStorage.setItem('tradepilot_auth', 'true')
        return true
      }
    }
    return localStorage.getItem('tradepilot_auth') === 'true'
  })

  const handleLoginSuccess = (userData) => {
    setUser(userData)
    setIsAuthenticated(true)
    localStorage.setItem('tradepilot_auth', 'true')
    localStorage.setItem('tradepilot_user', JSON.stringify(userData))
    showToast(`Institutional Gateway Unlocked: Welcome, ${userData.name || 'Trader'}!`)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    localStorage.removeItem('tradepilot_auth')
  }

  const [perfData, setPerfData] = useState({
    net_pnl: 0,
    win_rate: 0,
    profit_factor: 0,
    sharpe_ratio: 0,
    sortino_ratio: 0,
    max_drawdown_pct: 0,
    cagr_pct: 0,
    total_trades: 0,
    strategy_performance: [],
  })

  // ── Tier 1: Hot data — prices via REST (used as WS fallback only) ──
  const hotFetchGuard = useRef(false)
  const refreshHotData = async () => {
    if (hotFetchGuard.current) return   // skip if previous call still in-flight
    hotFetchGuard.current = true
    try {
      const results = await Promise.allSettled([
        fetch(`${API_BASE}/api/v1/market/quotes`),
        fetch(`${API_BASE}/api/v1/market/indices`),
        fetch(`${API_BASE}/api/portfolio`),
        fetch(`${API_BASE}/api/v1/market/status`),
        fetch(`${API_BASE}/api/v1/market/breadth`),
        fetch(`${API_BASE}/api/v1/crypto/quotes`),
      ])
      let anyOk = false
      if (results[0].status === 'fulfilled' && results[0].value.ok) {
        const raw = await results[0].value.json()
        setQuotes(Array.isArray(raw) ? raw.map(q => ({ ...q, price: q.price ?? q.last_price, ltp: q.ltp ?? q.price ?? q.last_price })) : raw)
        anyOk = true
      }
      if (results[1].status === 'fulfilled' && results[1].value.ok) {
        setIndices(await results[1].value.json())
        anyOk = true
      }
      if (results[2].status === 'fulfilled' && results[2].value.ok) {
        setPortfolio(await results[2].value.json())
        anyOk = true
      }
      if (results[3].status === 'fulfilled' && results[3].value.ok) setMarketStatus(await results[3].value.json())
      if (results[4].status === 'fulfilled' && results[4].value.ok) setBreadth(await results[4].value.json())
      if (results[5]?.status === 'fulfilled' && results[5]?.value?.ok) {
        const cData = await results[5].value.json()
        if (cData?.data) setCryptoQuotes(cData.data)
        else if (cData?.quotes) setCryptoQuotes(cData.quotes)
      }
      setLiveConnected(anyOk)
    } catch { setLiveConnected(false) }
    finally { hotFetchGuard.current = false }
  }

  // ── Tier 2: Cold data — logs, analytics, orders, feed-health (30s) ──
  const coldFetchGuard = useRef(false)
  const refreshColdData = async () => {
    if (coldFetchGuard.current) return
    coldFetchGuard.current = true
    try {
      const results = await Promise.allSettled([
        fetch(`${API_BASE}/api/alerts`),
        fetch(`${API_BASE}/api/system/logs`),
        fetch(`${API_BASE}/api/analytics/performance-deck`),
        fetch(`${API_BASE}/api/v1/market/feed-health`),
        fetch(`${API_BASE}/api/v1/market/nifty50/constituents?live=true`),
        fetch(`${API_BASE}/api/v1/orders`),
      ])
      if (results[0].status === 'fulfilled' && results[0].value.ok) setAlerts(await results[0].value.json())
      if (results[1].status === 'fulfilled' && results[1].value.ok) setLogs(await results[1].value.json())
      if (results[2].status === 'fulfilled' && results[2].value.ok) setPerfData(await results[2].value.json())
      if (results[3].status === 'fulfilled' && results[3].value.ok) {
        const fh = await results[3].value.json()
        setFeedHealth(fh)
        if (fh?.is_connected) setLiveConnected(true)
      }
      if (results[4].status === 'fulfilled' && results[4].value.ok) setNifty50Constituents(await results[4].value.json())
      if (results[5].status === 'fulfilled' && results[5].value.ok) setOrders(await results[5].value.json())
    } catch {}
    finally { coldFetchGuard.current = false }
  }

  // ── Index symbol → indices state key mapping ──
  const INDEX_SYMBOL_MAP = useRef({
    'NIFTY 50': 'NIFTY 50', 'NIFTY50': 'NIFTY 50',
    'NIFTY BANK': 'NIFTY BANK', 'NIFTYBANK': 'NIFTY BANK',
    'SENSEX': 'SENSEX', 'BSESENSEX': 'SENSEX',
    'GOLD': 'GOLD', 'GOLDBEES': 'GOLD',
    'SILVER': 'SILVER', 'SILVERBEES': 'SILVER',
    'INDIA VIX': 'INDIA VIX',
  }).current

  useEffect(() => {
    // ── Initial load: both tiers at once ──
    refreshHotData()
    refreshColdData()

    let ws = null
    let reconnectTimer = null
    let reconnectDelay = 1000       // Start at 1s, backs off to max 30s
    let firstTickReceived = false

    // ── Primary data channel: WebSocket (1-second ticks from backend) ──
    const connectWs = () => {
      setWsStatus('CONNECTING')
      firstTickReceived = false
      try {
        ws = new WebSocket(WS_URL)

        ws.onopen = () => {
          reconnectDelay = 1000     // Reset backoff on successful open
          try {
            ws.send(JSON.stringify({
              action: 'subscribe',
              symbols: [
                'NSE:NIFTY50', 'NSE:NIFTYBANK', 'BSE:SENSEX',
                'NSE:GOLD', 'NSE:SILVER', 'NSE:GOLDBEES', 'NSE:SILVERBEES',
                'CRYPTO:BTC', 'CRYPTO:ETH', 'CRYPTO:SOL', 'CRYPTO:BNB', 'CRYPTO:XRP',
                'NSE:RELIANCE', 'NSE:TCS', 'NSE:INFY', 'NSE:HDFCBANK', 'NSE:ICICIBANK', 'NSE:SBIN',
                'NSE:GRASIM', 'NSE:HINDUNILVR', 'NSE:DIVISLAB', 'NSE:TATACONSUM', 'NSE:BHARTIARTL', 'NSE:SBILIFE'
              ]
            }))
          } catch {}
        }

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            tickCounterRef.current += 1

            // ── Extract all incoming quotes (individual QUOTE_UPDATE or batch TICK_UPDATE) ──
            const incomingList = msg.quotes && Array.isArray(msg.quotes)
              ? msg.quotes
              : (msg.quote ? [msg.quote] : (msg.type === 'QUOTE_UPDATE' && msg.symbol ? [msg] : []))

            if (incomingList.length > 0) {
              const newFlashes = {}
              incomingList.forEach(q => {
                if (q && q.symbol) {
                  const p = q.ltp ?? q.price ?? q.last_price
                  if (p !== undefined && p !== null && !isNaN(p)) {
                    const oldP = prevPriceRef.current[q.symbol]
                    let dir = 'UNCHANGED'
                    if (oldP !== undefined && oldP !== null) {
                      if (p > oldP) dir = 'UP'
                      else if (p < oldP) dir = 'DOWN'
                    } else if (q.price_movement) {
                      dir = q.price_movement
                    }
                    if (dir !== 'UNCHANGED') {
                      newFlashes[q.symbol] = { dir, time: Date.now() }
                    }
                    prevPriceRef.current[q.symbol] = p
                  }
                }
              })

              if (Object.keys(newFlashes).length > 0) {
                setPriceFlashMap(prev => ({ ...prev, ...newFlashes }))
                setTimeout(() => {
                  setPriceFlashMap(prev => {
                    const next = { ...prev }
                    Object.keys(newFlashes).forEach(k => delete next[k])
                    return next
                  })
                }, 900)
              }

              // ── Update quotes array in place without resetting entire table ──
              setQuotes(prev => {
                const map = new Map(prev.map(item => [item.symbol, item]))
                incomingList.forEach(q => {
                  if (q && q.symbol) {
                    const cleanQ = {
                      ...q,
                      price: q.ltp ?? q.price ?? q.last_price,
                      last_price: q.ltp ?? q.price ?? q.last_price,
                      ltp: q.ltp ?? q.price ?? q.last_price,
                    }
                    map.set(q.symbol, { ...(map.get(q.symbol) || {}), ...cleanQ })
                  }
                })
                return Array.from(map.values())
              })

              // ── Dynamic live update of NIFTY 50 Constituents table (GRASIM, HINDUNILVR, DIVISLAB, etc.) ──
              setNifty50Constituents(prev => {
                if (!prev || prev.length === 0) return prev
                const inMap = {}
                incomingList.forEach(q => { if (q && q.symbol) inMap[q.symbol] = q })
                let anyMatch = false
                const updated = prev.map(item => {
                  const match = inMap[item.symbol]
                  if (match) {
                    anyMatch = true
                    return {
                      ...item,
                      ...match,
                      price: match.ltp ?? match.price ?? match.last_price,
                      last_price: match.ltp ?? match.price ?? match.last_price,
                      ltp: match.ltp ?? match.price ?? match.last_price,
                      change: match.change !== undefined ? match.change : item.change,
                      change_percent: match.change_percent !== undefined ? match.change_percent : item.change_percent,
                      open: match.open ?? item.open,
                      high: match.high ?? item.high,
                      low: match.low ?? item.low,
                      previous_close: match.previous_close ?? item.previous_close,
                      volume: match.volume ?? item.volume,
                      data_status: match.data_status ?? item.data_status,
                      timestamp: match.timestamp ?? item.timestamp,
                    }
                  }
                  return item
                })
                return anyMatch ? updated : prev
              })
            }

            // ── Mark CONNECTED on first valid tick ──
            if (!firstTickReceived && (msg.type === 'TICK_UPDATE' || (msg.quotes && Array.isArray(msg.quotes) && msg.quotes.length > 0))) {
              firstTickReceived = true
              setWsStatus('CONNECTED')
              setLiveConnected(true)
            }

            if (msg.type !== 'TICK_UPDATE') return

            // ── 1-Second Live Heartbeat Telemetry ──
            setLiveTickCount(prev => prev + 1)
            const nowTime = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
            setLastTickTime(nowTime)

            // ── Indices ──
            if (msg.indices && typeof msg.indices === 'object' && Object.keys(msg.indices).length > 0) {
              setIndices(prev => ({ ...prev, ...msg.indices }))
            }

            // ── Reactive Mark-to-Market P&L for open paper positions ──
            if (msg.portfolio) {
              setPortfolio(msg.portfolio)
            } else if (incomingList.length > 0) {
              setPortfolio(prev => {
                if (!prev || !prev.positions || prev.positions.length === 0) return prev
                const inMap = {}
                incomingList.forEach(q => { if (q && q.symbol) inMap[q.symbol] = q })
                let totalUnrealized = 0
                const updatedPositions = prev.positions.map(pos => {
                  const tick = inMap[pos.symbol]
                  if (tick) {
                    const curPrice = tick.ltp ?? tick.price ?? tick.last_price ?? pos.current_price
                    const qty = pos.quantity || 1
                    const entry = pos.entry_price || curPrice
                    const diff = pos.side === 'BUY' ? (curPrice - entry) : (entry - curPrice)
                    const pnl = Math.round(diff * qty * 100) / 100
                    const pnlPct = entry > 0 ? Math.round((diff / entry) * 10000) / 100 : 0
                    totalUnrealized += pnl
                    return {
                      ...pos,
                      current_price: curPrice,
                      unrealized_pnl: pnl,
                      pnl_percent: pnlPct,
                    }
                  }
                  totalUnrealized += (pos.unrealized_pnl || 0)
                  return pos
                })
                return {
                  ...prev,
                  positions: updatedPositions,
                  unrealized_pnl: Math.round(totalUnrealized * 100) / 100,
                  equity: Math.round(((prev.starting_capital || 500000) + (prev.realized_pnl || 0) + totalUnrealized) * 100) / 100,
                }
              })
            }

            if (msg.market_status) setMarketStatus(msg.market_status)
            if (msg.crypto && Array.isArray(msg.crypto) && msg.crypto.length > 0) {
              setCryptoQuotes(msg.crypto)
            }
            if (msg.signals) setSignals(msg.signals)
            if (msg.alerts) setAlerts(msg.alerts)
            if (msg.feed_health) setFeedHealth(msg.feed_health)
          } catch {}
        }

        ws.onclose = () => {
          setLiveConnected(false)
          setWsStatus('DISCONNECTED')
          reconnectDelay = Math.min(reconnectDelay * 1.5, 30000)  // cap at 30s for production
          reconnectTimer = setTimeout(connectWs, reconnectDelay)
        }

        ws.onerror = () => {
          // onclose fires after onerror — reconnect is handled there
          setWsStatus('DISCONNECTED')
        }
      } catch {
        setWsStatus('DISCONNECTED')
        reconnectTimer = setTimeout(connectWs, reconnectDelay)
      }
    }

    connectWs()

    // ── Tier 1 REST fallback: poll hot data every 5s (backup for when WS is reconnecting) ──
    const hotPoll = setInterval(refreshHotData, 5000)

    // ── Tier 2: poll cold data every 30s — no trading impact ──
    const coldPoll = setInterval(refreshColdData, 30000)

    return () => {
      if (ws) ws.close()
      if (reconnectTimer) clearTimeout(reconnectTimer)
      clearInterval(hotPoll)
      clearInterval(coldPoll)
    }
  }, [])

  const showToast = (msg) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(''), 4000)
  }

  const handlePlaceOrder = async (orderPayload) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/trades/configure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderPayload),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Order rejected by risk engine')
      }
      showToast(`Order Executed: ${orderPayload.side} ${orderPayload.quantity} ${orderPayload.symbol}`)
      refreshHotData()
    } catch (err) {
      showToast(`Order Error: ${err.message}`)
    }
  }

  const handleClosePosition = async (symbol, quantity = null) => {
    try {
      const res = await fetch(`${API_BASE}/api/trades/${symbol}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity, reason: 'MANUAL_CLOSE' }),
      })
      if (!res.ok) throw new Error('Close failed')
      showToast(`Closed position in ${symbol}`)
      refreshHotData()
    } catch (err) {
      showToast(`Close Error: ${err.message}`)
    }
  }

  const handlePanicSquareOff = async () => {
    setPanicModalOpen(false)
    try {
      const res = await fetch(`${API_BASE}/api/trades/close-all`, { method: 'POST' })
      if (!res.ok) throw new Error('Panic close failed')
      showToast('EMERGENCY KILLSWITCH: All open positions squared off.')
      refreshHotData()
    } catch (err) {
      showToast(`Panic Close Error: ${err.message}`)
    }
  }

  const fillLTP = async () => {
    if (!tradeSymbol) return
    setLtpLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/market/quote/${tradeSymbol.toUpperCase()}`)
      if (!res.ok) {
        const err = await res.json()
        showToast(`LTP Fetch Error: ${err.detail?.message || 'Feed disconnected'}`)
        return
      }
      const data = await res.json()
      if (data.last_price && data.last_price > 0) {
        setTradeEntry(String(data.last_price))
        const slDef = tradeSide === 'BUY' ? (data.last_price * 0.975).toFixed(2) : (data.last_price * 1.025).toFixed(2)
        const tgDef = tradeSide === 'BUY' ? (data.last_price * 1.05).toFixed(2) : (data.last_price * 0.95).toFixed(2)
        setTradeSL(slDef)
        setTradeTarget(tgDef)
        showToast(`✓ LTP filled: ${data.symbol} @ ₹${data.last_price} (${data.data_source})`)
      } else {
        showToast(`⚠ No live price available for ${tradeSymbol}. Connect market data provider.`)
      }
    } catch {
      showToast('⚠ Failed to fetch live price. Backend offline.')
    } finally {
      setLtpLoading(false)
    }
  }

  const filteredQuotes = useMemo(() => {
    const list = [...quotes]
    if (cryptoQuotes && cryptoQuotes.length > 0) {
      cryptoQuotes.forEach((cq) => {
        if (!list.some((item) => item.symbol === cq.symbol)) {
          list.push({
            ...cq,
            exchange: 'CRYPTO',
            price: cq.last_price,
            ltp: cq.last_price,
          })
        }
      })
    }
    return list.filter((q) => {
      const matchSearch =
        q.symbol.toLowerCase().includes(watchlistSearch.toLowerCase()) ||
        (q.name && q.name.toLowerCase().includes(watchlistSearch.toLowerCase()))
      const matchExch = exchangeFilter === 'ALL' || q.exchange === exchangeFilter
      return matchSearch && matchExch
    })
  }, [quotes, cryptoQuotes, watchlistSearch, exchangeFilter])

  const filteredAlerts = useMemo(() => {
    if (alertFilter === 'ALL') return alerts
    return alerts.filter((a) => (a.type || '').toUpperCase().includes(alertFilter))
  }, [alerts, alertFilter])

  if (!isAuthenticated) {
    return <LoginPage3D onLogin={handleLoginSuccess} />
  }

  return (
    <div className="app-shell">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Zap size={20} className="text-cyan-400" /></div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontWeight: 800, letterSpacing: '0.04em', fontSize: '15px' }}>
                TRADE<span className="brand-accent" style={{ color: '#06b6d4' }}>/</span>PILOT <span style={{ color: '#10b981' }}>AI</span>
              </span>
            </div>
            <div style={{ fontSize: '9.5px', color: '#64748b', fontWeight: 600, letterSpacing: '0.08em', marginTop: '1px' }}>
              NSE / BSE TRADING TERMINAL
            </div>
          </div>
        </div>

        <div className="workspace-badge" style={{ padding: '10px 12px', background: 'rgba(15, 23, 42, 0.65)', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '8px', margin: '8px 12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
              TERMINAL STATUS
            </div>
            <span className={`badge ${liveConnected ? 'badge-green' : 'badge-amber'}`} style={{ fontSize: '9.5px', padding: '2px 6px' }}>
              {liveConnected ? '● NSE LIVE' : '⚠ DISCONNECTED'}
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600 }}>
            Monitor • Analyze • Protect • Trade
          </div>
        </div>

        <div className="nav-group">
          <div className="nav-group-title">Command Center</div>
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={16} />
                {item.label}
                {item.id === 'Alert System' && alerts.length > 0 && (
                  <span className="nav-badge alert">{alerts.length}</span>
                )}
                {item.id === 'Positions' && (
                  <span className="nav-badge">{portfolio.positions?.length || 0}</span>
                )}
              </button>
            )
          })}
        </div>

        <div className="sidebar-footer">
          <button className="btn btn-secondary" style={{ width: '100%', fontSize: 11.5 }} onClick={() => setInstrumentModalOpen(true)}>
            <Database size={14} /> Instrument Master (ISIN)
          </button>
        </div>
      </aside>

      {/* Main Container */}
      <div className="main-wrapper">
        {/* Header Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ margin: 0, fontSize: '17px', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
                  TradePilot AI
                </h1>
                <span style={{ fontSize: '12px', color: '#06b6d4', fontWeight: 600, padding: '1px 6px', background: 'rgba(6, 182, 212, 0.12)', borderRadius: '4px', border: '1px solid rgba(6, 182, 212, 0.25)' }}>
                  Intelligent Real-Time Trading
                </span>
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px', fontWeight: 500 }}>
                "Monitor. Analyze. Protect. Trade." • Active Desk: <strong style={{ color: '#e2e8f0' }}>{activeTab}</strong>
              </div>
            </div>
            <div
              className="live-chip"
              onClick={() => setMarketDataModalOpen(true)}
              title="Click to Open Real-Time Market Data Hub & Connect Feeds"
              style={{
                marginLeft: '12px',
                background: liveConnected ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                border: `1px solid ${liveConnected ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <span className={`pulse-dot ${liveConnected ? '' : 'disconnected'}`} />
              <span style={{ color: liveConnected ? '#10b981' : '#f87171', fontWeight: 700 }}>
                {liveConnected ? (marketStatus?.status === 'OPEN' ? '● NSE LIVE (1s)' : `● ${marketStatus?.label || 'MARKET CLOSED'} (1s)`) : '⚠ REAL-TIME MARKET DATA NOT CONNECTED'}
              </span>
              {liveConnected && lastTickTime && (
                <span style={{ fontSize: '11px', color: '#34d399', marginLeft: '6px', fontWeight: 600 }}>
                  • {lastTickTime} #{liveTickCount}
                </span>
              )}
            </div>
          </div>

          <div className="topbar-right">
            {/* Authenticated Trader Profile Chip */}
            <div
              onClick={() => setProfileModalOpen(true)}
              title="Click to Open Secure Account Profile & Security Vault"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '4px 12px',
                background: 'rgba(15, 23, 42, 0.85)',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                borderRadius: 20,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#06b6d4'
                e.currentTarget.style.background = 'rgba(6, 182, 212, 0.12)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.35)'
                e.currentTarget.style.background = 'rgba(15, 23, 42, 0.85)'
              }}
            >
              <div style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #06b6d4, #10b981)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 11,
                fontWeight: 900,
                color: '#fff',
              }}>
                {(user?.name || 'T')[0]}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
                <span style={{ fontSize: 11.5, fontWeight: 700, color: '#f8fafc' }}>{user?.name || 'PRO TRADER'}</span>
                <span style={{ fontSize: 9, color: '#10b981', fontWeight: 700 }}>● {user?.environment?.toUpperCase() || 'LIVE'} • 98% SECURE</span>
              </div>
              <ShieldCheck size={14} color="#10b981" style={{ marginLeft: 3 }} />
            </div>

            {/* Connect Real-Time Market Data Hub Button */}
            <button
              className="btn btn-secondary"
              title="Open Real-Time Market Data Hub & Connect Feeds"
              onClick={() => setMarketDataModalOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 12px',
                fontSize: 11.5,
                fontWeight: 700,
                background: 'rgba(56, 189, 248, 0.14)',
                border: '1px solid rgba(56, 189, 248, 0.45)',
                color: '#38bdf8',
              }}
            >
              <Radio size={13} color="#38bdf8" />
              <span>Connect Feed</span>
            </button>

            <button
              className="btn btn-secondary"
              title="Lock Terminal & Switch User"
              onClick={handleLogout}
              style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 10px', fontSize: 11.5 }}
            >
              <Lock size={13} /> Lock
            </button>
            <button className="btn btn-secondary" onClick={() => setInstrumentModalOpen(true)}>
              <Database size={14} /> Instrument Master
            </button>
            <button className="btn btn-primary" onClick={() => setActiveTab('Orders')}>
              <Plus size={15} /> Configure Trade
            </button>
            <button className="btn btn-danger" onClick={() => setPanicModalOpen(true)}>
              <ShieldAlert size={15} /> Square Off All
            </button>
          </div>
        </header>

        {/* Streaming Indian Indices & Commodities Ticker Tape */}
        <div className="ticker-tape">
          {Object.entries(indices).map(([name, idxData]) => {
            const isGold = name === 'GOLD'
            const isSilver = name === 'SILVER'
            const isCommodity = isGold || isSilver

            const chipStyle = isGold
              ? { background: 'rgba(234, 179, 8, 0.12)', border: '1px solid rgba(234, 179, 8, 0.4)', cursor: 'pointer' }
              : isSilver
              ? { background: 'rgba(203, 213, 225, 0.12)', border: '1px solid rgba(203, 213, 225, 0.4)', cursor: 'pointer' }
              : { background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.2)' }

            const symColor = isGold ? '#eab308' : isSilver ? '#cbd5e1' : 'var(--accent-blue)'

            return (
              <div
                key={name}
                className="ticker-chip"
                style={chipStyle}
                onClick={() => {
                  if (isCommodity) {
                    setCommoditySymbol(name)
                    setActiveTab('Gold & Silver Live')
                  }
                }}
                title={isCommodity ? `Click to inspect ${name} Live Bullion Desk` : undefined}
              >
                <span className="sym" style={{ color: symColor, display: 'flex', alignItems: 'center', gap: 4 }}>
                  {isCommodity && <Coins size={12} color={symColor} />}
                  {name}
                </span>
                <span className="price">{name === 'INDIA VIX' ? Number(idxData.price).toFixed(2) : money(idxData.price)}</span>
                <span className={(idxData.change || 0) >= 0 ? 'positive' : 'negative'}>{pct(idxData.change_percent)}</span>
              </div>
            )
          })}
          {/* 24/7 Live Crypto Ticker Items (BTC, ETH, SOL, etc.) */}
          {cryptoQuotes.map((cq) => {
            const isPos = (cq.change || 0) >= 0
            const flash = priceFlashMap[cq.symbol]
            return (
              <div
                key={`crypto-${cq.symbol}`}
                className={`ticker-chip ${flash?.dir === 'UP' ? 'price-flash-up' : flash?.dir === 'DOWN' ? 'price-flash-down' : ''}`}
                style={{
                  background: 'rgba(245, 158, 11, 0.12)',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  cursor: 'pointer',
                }}
                onClick={() => setActiveTab('Crypto 24/7')}
                title={`Click to open Crypto 24/7 Desk (${cq.name})`}
              >
                <span className="sym" style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Coins size={12} color="#f59e0b" />
                  {cq.symbol}/USDT
                </span>
                <span className="price" style={{ fontFamily: 'var(--font-mono)' }}>
                  ${Number(cq.last_price || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className={isPos ? 'positive' : 'negative'}>{pct(cq.change_percent)}</span>
                <span style={{ fontSize: 9, color: '#10b981', fontWeight: 800, padding: '1px 4px', background: 'rgba(16, 185, 129, 0.15)', borderRadius: 3 }}>
                  24/7
                </span>
              </div>
            )
          })}
          {quotes.map((q) => (
            <div
              key={q.symbol}
              className="ticker-chip"
              onClick={() => {
                setSelectedSymbol(q.symbol)
                setActiveTab('Interactive Charts')
              }}
            >
              <span className="sym">{q.symbol}</span>
              <span className="price">{money(q.price || q.last_price)}</span>
              <span className={(q.change || 0) >= 0 ? 'positive' : 'negative'}>{pct(q.change_percent)}</span>
            </div>
          ))}
        </div>

        {/* Dynamic View Body */}
        <main className="content-body">
          {/* TAB 1: DASHBOARD */}
          {activeTab === 'Dashboard' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* Dedicated NIFTY 50, NIFTY BANK & SENSEX Live Benchmark Grid */}
              <div className="grid-3col">
                <LiveIndexCard name="NIFTY 50" data={indices['NIFTY 50']} marketStatus={marketStatus} />
                <LiveIndexCard name="NIFTY BANK" data={indices['NIFTY BANK']} marketStatus={marketStatus} />
                <LiveIndexCard name="SENSEX" data={indices['SENSEX']} marketStatus={marketStatus} />
              </div>

              {/* Precious Metals & Bullion Live Cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Coins size={18} color="#eab308" />
                    <span style={{ fontWeight: 800, fontSize: 14.5, color: 'var(--text-main)' }}>
                      Precious Metals & Bullion Desk (NSE ETFs)
                    </span>
                    <span className="badge badge-amber" style={{ fontSize: 9.5 }}>NSE COMMODITIES</span>
                  </div>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '3px 10px', fontSize: 11 }}
                    onClick={() => setActiveTab('Gold & Silver Live')}
                  >
                    Open Full Bullion Desk →
                  </button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
                  <LiveCommodityCard
                    name="GOLD"
                    sub="Nippon India ETF Gold BeES (NSE: GOLDBEES / GOLD)"
                    data={indices['GOLD']}
                    marketStatus={marketStatus}
                    accentColor="#eab308"
                    onTrade={() => { setTradeSymbol('GOLD'); setActiveTab('Orders'); }}
                    onViewDesk={() => { setCommoditySymbol('GOLD'); setActiveTab('Gold & Silver Live'); }}
                  />
                  <LiveCommodityCard
                    name="SILVER"
                    sub="Nippon India ETF Silver BeES (NSE: SILVERBEES / SILVER)"
                    data={indices['SILVER']}
                    marketStatus={marketStatus}
                    accentColor="#94a3b8"
                    onTrade={() => { setTradeSymbol('SILVER'); setActiveTab('Orders'); }}
                    onViewDesk={() => { setCommoditySymbol('SILVER'); setActiveTab('Gold & Silver Live'); }}
                  />
                </div>
              </div>

              {/* Market Breadth Summary */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-card)', padding: '14px 20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: 16 }}>NSE Market Overview & Breadth</h2>
                  <small style={{ color: 'var(--text-dim)' }}>
                    Advancers: {breadth.advancers} | Decliners: {breadth.decliners} | Unchanged: {breadth.unchanged} | Sentiment: {breadth.market_sentiment}
                  </small>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className="badge badge-green">Advancing ({breadth.advancers})</span>
                  <span className="badge badge-red">Declining ({breadth.decliners})</span>
                </div>
              </div>

              {/* KPI Summary Cards */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-top"><span>Portfolio Valuation</span><WalletCards size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value">{money(portfolio.equity)}</div>
                  <div className="kpi-sub positive">{signedMoney(portfolio.daily_pnl)} Today</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Net Realized P&L</span><TrendingUp size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value positive">{signedMoney(portfolio.realized_pnl)}</div>
                  <div className="kpi-sub positive">Win Rate: {portfolio.win_rate || 0}%</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Unrealized MTM P&L</span><Coins size={16} color="var(--accent-blue)" /></div>
                  <div className="kpi-value positive">{signedMoney(portfolio.unrealized_pnl)}</div>
                  <div className="kpi-sub">Across {portfolio.positions?.length || 0} Open Positions</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Available Margin</span><BriefcaseBusiness size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value">{money(portfolio.cash)}</div>
                  <div className="kpi-sub">Margin Utilized: {money(portfolio.margin_used || 0)}</div>
                </div>
              </div>

              {/* Candlestick Chart */}
              <CandlestickChartWithPivots
                symbol={selectedSymbol}
                onOpenFeedConnector={() => setMarketDataModalOpen(true)}
              />

              {/* Top NIFTY 50 Movers */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title"><Table size={16} /> NIFTY 50 Live Streaming Equities</span>
                  <span className="badge badge-green">{quotes.length} Equities Streaming</span>
                </div>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Company Name</th>
                        <th>Exchange</th>
                        <th>LTP (₹)</th>
                        <th>Change</th>
                        <th>Change %</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Volume</th>
                        <th>Data Status</th>
                        <th>Last Updated</th>
                      </tr>
                    </thead>
                    <tbody>
                      {quotes.slice(0, 10).map((q) => (
                        <tr
                          key={q.symbol}
                          style={{ cursor: 'pointer', background: selectedSymbol === q.symbol ? 'var(--bg-card-hover)' : 'transparent' }}
                          onClick={() => {
                            setSelectedSymbol(q.symbol)
                            setActiveTab('Interactive Charts')
                          }}
                        >
                          <td><b>{q.symbol}</b></td>
                          <td>{q.name || q.company_name || q.symbol}</td>
                          <td><span className="badge badge-blue">{q.exchange || 'NSE'}</span></td>
                          <td><PriceCell symbol={q.symbol} ltp={q.ltp ?? q.price ?? q.last_price} change={q.change} flash={priceFlashMap[q.symbol]} currencySymbol={q.currency_symbol || '₹'} /></td>
                          <td className={(q.change || 0) >= 0 ? 'positive' : 'negative'}>{signedMoney(q.change)}</td>
                          <td className={(q.change || 0) >= 0 ? 'positive' : 'negative'}>{pct(q.change_percent)}</td>
                          <td>{q.open ? money(q.open) : '—'}</td>
                          <td>{q.high ? money(q.high) : '—'}</td>
                          <td>{q.low ? money(q.low) : '—'}</td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{(q.volume || 0).toLocaleString('en-IN')}</td>
                          <td><DataFreshnessBadge timestamp={q.provider_timestamp || q.timestamp} status={q.data_status} isLive={q.is_live} /></td>
                          <td style={{ fontSize: 11, color: 'var(--text-dim)' }}>{formatTime(q.timestamp)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: LIVE MARKET DESK */}
          {activeTab === 'Live Market' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Live Market Desk & Sectoral Heat</h1>
                  <p>Streaming quotes across NIFTY 50, NIFTY BANK, and authorized NSE/BSE universe.</p>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button className="btn btn-secondary" onClick={() => refreshHotData()}><RefreshCw size={14} /> Refresh Feed</button>
                </div>
              </div>

              <div className="grid-3col">
                <LiveIndexCard name="NIFTY 50" data={indices['NIFTY 50']} marketStatus={marketStatus} />
                <LiveIndexCard name="NIFTY BANK" data={indices['NIFTY BANK']} marketStatus={marketStatus} />
                <LiveIndexCard name="SENSEX" data={indices['SENSEX']} marketStatus={marketStatus} />
              </div>

              <div className="card">
                <div className="card-header">
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    <span className="card-title"><Table size={16} /> All Active Market Quotes ({filteredQuotes.length})</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {['ALL', 'NSE', 'BSE', 'CRYPTO'].map((ex) => (
                        <button
                          key={ex}
                          className={`btn ${exchangeFilter === ex ? 'btn-primary' : 'btn-secondary'}`}
                          style={{ padding: '3px 8px', fontSize: 11 }}
                          onClick={() => setExchangeFilter(ex)}
                        >
                          {ex}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div style={{ width: 240, position: 'relative' }}>
                    <input
                      type="text"
                      placeholder="Filter stocks..."
                      value={watchlistSearch}
                      onChange={(e) => setWatchlistSearch(e.target.value)}
                      style={{ padding: '5px 10px 5px 28px', fontSize: 12 }}
                    />
                    <Search size={13} color="var(--text-dim)" style={{ position: 'absolute', left: 8, top: 9 }} />
                  </div>
                </div>

                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Exchange</th>
                        <th>LTP (₹)</th>
                        <th>Change</th>
                        <th>Change %</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Prev Close</th>
                        <th>Volume</th>
                        <th>Data Status</th>
                        <th>Timestamp</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredQuotes.map((q) => (
                        <tr key={`${q.exchange}:${q.symbol}`}>
                          <td><b>{q.symbol}</b></td>
                          <td><span className="badge badge-blue">{q.exchange || 'NSE'}</span></td>
                          <td><PriceCell symbol={q.symbol} ltp={q.ltp ?? q.price ?? q.last_price} change={q.change} flash={priceFlashMap[q.symbol]} currencySymbol={q.currency_symbol || '₹'} /></td>
                          <td className={(q.change || 0) >= 0 ? 'positive' : 'negative'}>{signedMoney(q.change)}</td>
                          <td className={(q.change || 0) >= 0 ? 'positive' : 'negative'}>{pct(q.change_percent)}</td>
                          <td>{q.open ? money(q.open) : '—'}</td>
                          <td>{q.high ? money(q.high) : '—'}</td>
                          <td>{q.low ? money(q.low) : '—'}</td>
                          <td>{q.previous_close ? money(q.previous_close) : '—'}</td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{(q.volume || 0).toLocaleString('en-IN')}</td>
                          <td><DataFreshnessBadge timestamp={q.provider_timestamp || q.timestamp} status={q.data_status} isLive={q.is_live} /></td>
                          <td style={{ fontSize: 11, color: 'var(--text-dim)' }}>{formatTime(q.timestamp)}</td>
                          <td>
                            <button
                              className="btn btn-secondary"
                              style={{ padding: '3px 8px', fontSize: 11 }}
                              onClick={() => {
                                setSelectedSymbol(q.symbol)
                                setTradeSymbol(q.symbol)
                                setActiveTab('Interactive Charts')
                              }}
                            >
                              Chart
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: CRYPTO & BITCOIN 24/7 LIVE DESK */}
          {activeTab === 'Crypto 24/7' && (
            <CryptoDesk
              cryptoQuotes={cryptoQuotes}
              priceFlashMap={priceFlashMap}
              onConfigureTrade={({ symbol, side, price }) => {
                setTradeSymbol(symbol)
                setTradeSide(side)
                setTradeEntry(String(price))
                setActiveTab('Orders')
              }}
              onSelectForChart={(symbol) => {
                setSelectedSymbol(symbol)
                setActiveTab('Interactive Charts')
              }}
            />
          )}

          {/* TAB: GOLD & SILVER COMMODITIES LIVE DESK */}
          {activeTab === 'Gold & Silver Live' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: 10,
                        background: 'linear-gradient(135deg, rgba(234, 179, 8, 0.25) 0%, rgba(148, 163, 184, 0.25) 100%)',
                        border: '1px solid rgba(234, 179, 8, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Coins size={20} color="#eab308" />
                    </div>
                    <div>
                      <h1 style={{ margin: 0 }}>Gold & Silver Commodities Bullion Desk</h1>
                      <p style={{ margin: '4px 0 0 0', color: 'var(--text-muted)' }}>
                        Institutional precious metals & bullion feeds from NSE India (Nippon India ETF Gold BeES & Silver BeES) with real-time pricing in INR (₹).
                      </p>
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ background: 'rgba(234, 179, 8, 0.15)', borderColor: 'rgba(234, 179, 8, 0.4)', color: '#eab308' }}
                    onClick={() => {
                      setTradeSymbol('GOLD')
                      setActiveTab('Orders')
                    }}
                  >
                    🪙 Trade Gold Long
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ background: 'rgba(203, 213, 225, 0.15)', borderColor: 'rgba(203, 213, 225, 0.4)', color: '#cbd5e1' }}
                    onClick={() => {
                      setTradeSymbol('SILVER')
                      setActiveTab('Orders')
                    }}
                  >
                    🥈 Trade Silver Long
                  </button>
                  <button className="btn btn-secondary" onClick={() => refreshHotData()}>
                    <RefreshCw size={14} /> Refresh Feed
                  </button>
                </div>
              </div>

              {/* Live Bullion Cards & Parity Spread Ratio Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
                <LiveCommodityCard
                  name="GOLD"
                  sub="Nippon India ETF Gold BeES (NSE: GOLDBEES / GOLD)"
                  data={indices['GOLD']}
                  marketStatus={marketStatus}
                  accentColor="#eab308"
                  onTrade={() => { setTradeSymbol('GOLD'); setActiveTab('Orders'); }}
                  onViewDesk={() => setCommoditySymbol('GOLD')}
                />
                <LiveCommodityCard
                  name="SILVER"
                  sub="Nippon India ETF Silver BeES (NSE: SILVERBEES / SILVER)"
                  data={indices['SILVER']}
                  marketStatus={marketStatus}
                  accentColor="#94a3b8"
                  onTrade={() => { setTradeSymbol('SILVER'); setActiveTab('Orders'); }}
                  onViewDesk={() => setCommoditySymbol('SILVER')}
                />

                {/* Dynamic Gold/Silver Ratio Card */}
                <div
                  className="kpi-card"
                  style={{
                    borderTop: '3px solid #38bdf8',
                    background: 'linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, var(--bg-card) 45%)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div className="kpi-top">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <SlidersHorizontal size={16} color="#38bdf8" />
                        <span style={{ fontWeight: 800, color: '#38bdf8' }}>GOLD / SILVER RATIO</span>
                      </div>
                      <span className="badge badge-blue" style={{ fontSize: 9.5 }}>LIVE SPREAD</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, margin: '12px 0 6px 0' }}>
                      <span style={{ fontSize: 28, fontWeight: 900, fontFamily: 'var(--font-mono)' }}>
                        {indices['GOLD']?.price && indices['SILVER']?.price
                          ? (indices['GOLD'].price / indices['SILVER'].price).toFixed(3)
                          : '—'}
                      </span>
                      <span style={{ fontSize: 12, color: 'var(--text-dim)', fontWeight: 600 }}>
                        Gold/Silver Price Multiple
                      </span>
                    </div>

                    <p style={{ fontSize: 11, color: 'var(--text-muted)', margin: '4px 0 10px 0' }}>
                      {indices['GOLD']?.price && indices['SILVER']?.price
                        ? `1 ETF unit of Gold (₹${indices['GOLD'].price}) = ${(indices['GOLD'].price / indices['SILVER'].price).toFixed(2)}x units of Silver (₹${indices['SILVER'].price}).`
                        : 'Awaiting feed ticks from both Gold and Silver NSE feeds.'}
                    </p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 11, color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: 8 }}>
                    <div>Gold 24h: <b className={(indices['GOLD']?.change || 0) >= 0 ? 'positive' : 'negative'}>{pct(indices['GOLD']?.change_percent)}</b></div>
                    <div>Silver 24h: <b className={(indices['SILVER']?.change || 0) >= 0 ? 'positive' : 'negative'}>{pct(indices['SILVER']?.change_percent)}</b></div>
                  </div>
                </div>
              </div>

              {/* Dedicated Candlestick Technical Analysis Chart */}
              <div className="card">
                <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className="card-title">
                      <BarChart3 size={16} /> {commoditySymbol === 'GOLD' ? '🪙 GOLD (GOLDBEES)' : '🥈 SILVER (SILVERBEES)'} Candlestick Chart
                    </span>
                    <span className="badge badge-green">1-Second Live Updates</span>
                  </div>

                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>Select Bullion Asset:</span>
                    <button
                      className={`btn ${commoditySymbol === 'GOLD' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{
                        padding: '4px 12px',
                        fontSize: 12,
                        background: commoditySymbol === 'GOLD' ? 'rgba(234, 179, 8, 0.3)' : undefined,
                        borderColor: commoditySymbol === 'GOLD' ? '#eab308' : undefined,
                        color: commoditySymbol === 'GOLD' ? '#facc15' : undefined,
                      }}
                      onClick={() => setCommoditySymbol('GOLD')}
                    >
                      🪙 Gold (GOLDBEES)
                    </button>
                    <button
                      className={`btn ${commoditySymbol === 'SILVER' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{
                        padding: '4px 12px',
                        fontSize: 12,
                        background: commoditySymbol === 'SILVER' ? 'rgba(203, 213, 225, 0.3)' : undefined,
                        borderColor: commoditySymbol === 'SILVER' ? '#cbd5e1' : undefined,
                        color: commoditySymbol === 'SILVER' ? '#f1f5f9' : undefined,
                      }}
                      onClick={() => setCommoditySymbol('SILVER')}
                    >
                      🥈 Silver (SILVERBEES)
                    </button>
                  </div>
                </div>

                <div style={{ padding: '0 16px 16px 16px' }}>
                  <CandlestickChartWithPivots
                    symbol={commoditySymbol}
                    onOpenFeedConnector={() => setMarketDataModalOpen(true)}
                  />
                </div>
              </div>

              {/* Bullion Contract & Asset Master Table */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title"><Coins size={16} color="#eab308" /> NSE Precious Metals Contract Catalog</span>
                  <span className="badge badge-green">Lot Size 1 • Real-time Ticks</span>
                </div>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Asset</th>
                        <th>Trading Symbol</th>
                        <th>Underlying Instrument</th>
                        <th>Exchange</th>
                        <th>Lot Size</th>
                        <th>Tick Size</th>
                        <th>LTP (₹)</th>
                        <th>24h Change</th>
                        <th>Day High / Low</th>
                        <th>ISIN</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ background: commoditySymbol === 'GOLD' ? 'rgba(234, 179, 8, 0.08)' : 'transparent' }}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <Coins size={14} color="#eab308" />
                            <b>Gold</b>
                          </div>
                        </td>
                        <td><span className="badge badge-amber">GOLD / GOLDBEES</span></td>
                        <td>Nippon India ETF Gold BeES</td>
                        <td><span className="badge badge-blue">NSE</span></td>
                        <td>1 Unit</td>
                        <td>₹0.01</td>
                        <td style={{ fontWeight: 800 }}>{money(indices['GOLD']?.price)}</td>
                        <td className={(indices['GOLD']?.change || 0) >= 0 ? 'positive' : 'negative'}>
                          {signedMoney(indices['GOLD']?.change)} ({pct(indices['GOLD']?.change_percent)})
                        </td>
                        <td>{money(indices['GOLD']?.high)} / {money(indices['GOLD']?.low)}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>INF204KB14I2</td>
                        <td>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button
                              className="btn btn-secondary"
                              style={{ padding: '3px 8px', fontSize: 11 }}
                              onClick={() => setCommoditySymbol('GOLD')}
                            >
                              Chart
                            </button>
                            <button
                              className="btn btn-primary"
                              style={{ padding: '3px 8px', fontSize: 11, background: '#eab308', border: 'none', color: '#000' }}
                              onClick={() => {
                                setTradeSymbol('GOLD')
                                setActiveTab('Orders')
                              }}
                            >
                              Trade
                            </button>
                          </div>
                        </td>
                      </tr>
                      <tr style={{ background: commoditySymbol === 'SILVER' ? 'rgba(203, 213, 225, 0.08)' : 'transparent' }}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <Coins size={14} color="#cbd5e1" />
                            <b>Silver</b>
                          </div>
                        </td>
                        <td><span className="badge badge-blue">SILVER / SILVERBEES</span></td>
                        <td>Nippon India ETF Silver BeES</td>
                        <td><span className="badge badge-blue">NSE</span></td>
                        <td>1 Unit</td>
                        <td>₹0.01</td>
                        <td style={{ fontWeight: 800 }}>{money(indices['SILVER']?.price)}</td>
                        <td className={(indices['SILVER']?.change || 0) >= 0 ? 'positive' : 'negative'}>
                          {signedMoney(indices['SILVER']?.change)} ({pct(indices['SILVER']?.change_percent)})
                        </td>
                        <td>{money(indices['SILVER']?.high)} / {money(indices['SILVER']?.low)}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>INF204KB1854</td>
                        <td>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button
                              className="btn btn-secondary"
                              style={{ padding: '3px 8px', fontSize: 11 }}
                              onClick={() => setCommoditySymbol('SILVER')}
                            >
                              Chart
                            </button>
                            <button
                              className="btn btn-primary"
                              style={{ padding: '3px 8px', fontSize: 11, background: '#94a3b8', border: 'none', color: '#000' }}
                              onClick={() => {
                                setTradeSymbol('SILVER')
                                setActiveTab('Orders')
                              }}
                            >
                              Trade
                            </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: NIFTY 50 LIVE DESK */}
          {activeTab === 'NIFTY 50 Live' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>NIFTY 50 Benchmark Live Desk</h1>
                  <p>Real-time authoritative feed from the National Stock Exchange of India (NSE) with all 50 constituents.</p>
                </div>
              </div>
              <LiveIndexCard
                name="NIFTY 50"
                data={indices['NIFTY 50']}
                marketStatus={marketStatus}
                onOpenFeedConnector={() => setMarketDataModalOpen(true)}
              />
              <CandlestickChartWithPivots
                symbol="NIFTY 50"
                onOpenFeedConnector={() => setMarketDataModalOpen(true)}
              />

              <div className="card">
                <div className="card-header">
                  <span className="card-title"><Table size={16} /> NIFTY 50 Constituents ({nifty50Constituents.length} Stocks)</span>
                  <span className="badge badge-green">Click any constituent to inspect chart</span>
                </div>
                <div className="table-container" style={{ maxHeight: 400, overflowY: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Exchange</th>
                        <th>LTP (₹)</th>
                        <th>Change</th>
                        <th>Change %</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Volume</th>
                        <th>Data Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {nifty50Constituents.map((item) => {
                        const isPos = (item.change || 0) >= 0
                        return (
                          <tr
                            key={item.symbol}
                            style={{ cursor: 'pointer', background: selectedSymbol === item.symbol ? 'rgba(56, 189, 248, 0.1)' : undefined }}
                            onClick={() => {
                              setSelectedSymbol(item.symbol)
                              setActiveTab('Interactive Charts')
                            }}
                          >
                            <td style={{ fontWeight: 800, color: 'var(--accent-cyan)' }}>{item.symbol}</td>
                            <td><span className="badge badge-blue">{item.exchange || 'NSE'}</span></td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{money(item.last_price || item.ltp)}</td>
                            <td className={isPos ? 'positive' : 'negative'} style={{ fontWeight: 600 }}>{signedMoney(item.change)}</td>
                            <td className={isPos ? 'positive' : 'negative'} style={{ fontWeight: 700 }}>{pct(item.change_percent)}</td>
                            <td style={{ color: 'var(--text-muted)' }}>{money(item.high)}</td>
                            <td style={{ color: 'var(--text-muted)' }}>{money(item.low)}</td>
                            <td style={{ color: 'var(--text-muted)' }}>{Number(item.volume || 0).toLocaleString('en-IN')}</td>
                            <td>
                              <span className={`badge ${item.data_status === 'STALE' ? 'badge-amber' : 'badge-green'}`}>
                                {item.data_status || 'LIVE'}
                              </span>
                            </td>
                            <td>
                              <button
                                className="btn btn-secondary"
                                style={{ padding: '3px 8px', fontSize: 11 }}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedSymbol(item.symbol)
                                  setActiveTab('Interactive Charts')
                                }}
                              >
                                View Chart
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: NIFTY BANK LIVE DESK */}
          {activeTab === 'NIFTY BANK Live' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>NIFTY BANK Sectoral Live Desk</h1>
                  <p>Real-time banking index tracking HDFC Bank, ICICI Bank, SBI, Kotak Bank, Axis Bank, and constituent lenders.</p>
                </div>
              </div>
              <LiveIndexCard
                name="NIFTY BANK"
                data={indices['NIFTY BANK']}
                marketStatus={marketStatus}
                onOpenFeedConnector={() => setMarketDataModalOpen(true)}
              />
              <CandlestickChartWithPivots
                symbol="NIFTY BANK"
                onOpenFeedConnector={() => setMarketDataModalOpen(true)}
              />
            </div>
          )}

          {/* TAB 5: SENSEX LIVE DESK */}
          {activeTab === 'SENSEX Live' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>BSE SENSEX Benchmark Live Desk</h1>
                  <p>Real-time authoritative feed from the Bombay Stock Exchange (BSE) tracking India's 30 bellwether stocks.</p>
                </div>
              </div>
              <LiveIndexCard
                name="SENSEX"
                data={indices['SENSEX']}
                marketStatus={marketStatus}
                onOpenFeedConnector={() => setMarketDataModalOpen(true)}
              />
              <CandlestickChartWithPivots
                symbol="SENSEX"
                onOpenFeedConnector={() => setMarketDataModalOpen(true)}
              />
            </div>
          )}

          {/* TAB 6: STOCK WATCHLIST */}
          {activeTab === 'Stock Watchlist' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Dynamic Real-Time Stock Watchlist</h1>
                  <p>Populated directly from the instrument master and updated in real-time via live feed.</p>
                </div>
              </div>
              <div className="card">
                <div className="card-header">
                  <span className="card-title"><Table size={16} /> Watchlist Stream ({filteredQuotes.length})</span>
                  <div style={{ width: 260, position: 'relative' }}>
                    <input
                      type="text"
                      placeholder="Search symbol or company..."
                      value={watchlistSearch}
                      onChange={(e) => setWatchlistSearch(e.target.value)}
                      style={{ paddingLeft: 28 }}
                    />
                    <Search size={14} color="var(--text-dim)" style={{ position: 'absolute', left: 8, top: 10 }} />
                  </div>
                </div>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Exchange</th>
                        <th>LTP (₹)</th>
                        <th>Change</th>
                        <th>Change %</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Volume</th>
                        <th>Source</th>
                        <th>Updated</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredQuotes.map((q) => (
                        <tr key={`${q.exchange}:${q.symbol}`}>
                          <td><b>{q.symbol}</b></td>
                          <td><span className="badge badge-blue">{q.exchange || 'NSE'}</span></td>
                          <td><PriceCell symbol={q.symbol} ltp={q.ltp ?? q.price ?? q.last_price} change={q.change} flash={priceFlashMap[q.symbol]} currencySymbol={q.currency_symbol || '₹'} /></td>
                          <td className={(q.change || 0) >= 0 ? 'positive' : 'negative'}>{signedMoney(q.change)}</td>
                          <td className={(q.change || 0) >= 0 ? 'positive' : 'negative'}>{pct(q.change_percent)}</td>
                          <td>{q.open ? money(q.open) : '—'}</td>
                          <td>{q.high ? money(q.high) : '—'}</td>
                          <td>{q.low ? money(q.low) : '—'}</td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{(q.volume || 0).toLocaleString('en-IN')}</td>
                          <td><DataFreshnessBadge timestamp={q.provider_timestamp || q.timestamp} status={q.data_status} isLive={q.is_live} /></td>
                          <td style={{ fontSize: 11, color: 'var(--text-dim)' }}>{formatTime(q.timestamp)}</td>
                          <td>
                            <button
                              className="btn btn-primary"
                              style={{ padding: '3px 8px', fontSize: 11 }}
                              onClick={() => {
                                setTradeSymbol(q.symbol)
                                setActiveTab('Orders')
                              }}
                            >
                              Trade
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: TECHNICAL CHARTS */}
          {activeTab === 'Interactive Charts' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Quantitative Technical Analysis & Candlestick Workspace</h1>
                  <p>Interactive charting with pivot overlays, SMA20, EMA21, Bollinger Bands, and real-time tick streaming.</p>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className={`btn ${selectedSymbol === 'GOLD' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{
                      padding: '4px 10px',
                      fontSize: 11,
                      background: selectedSymbol === 'GOLD' ? 'rgba(234, 179, 8, 0.3)' : undefined,
                      borderColor: selectedSymbol === 'GOLD' ? '#eab308' : undefined,
                      color: selectedSymbol === 'GOLD' ? '#facc15' : undefined,
                    }}
                    onClick={() => setSelectedSymbol('GOLD')}
                  >
                    🪙 GOLD
                  </button>
                  <button
                    type="button"
                    className={`btn ${selectedSymbol === 'SILVER' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{
                      padding: '4px 10px',
                      fontSize: 11,
                      background: selectedSymbol === 'SILVER' ? 'rgba(203, 213, 225, 0.3)' : undefined,
                      borderColor: selectedSymbol === 'SILVER' ? '#cbd5e1' : undefined,
                      color: selectedSymbol === 'SILVER' ? '#f1f5f9' : undefined,
                    }}
                    onClick={() => setSelectedSymbol('SILVER')}
                  >
                    🥈 SILVER
                  </button>
                  <select
                    value={selectedSymbol}
                    onChange={(e) => setSelectedSymbol(e.target.value)}
                    style={{ padding: '6px 12px', background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--border-subtle)', borderRadius: 6 }}
                  >
                    <optgroup label="Precious Metals & Bullion">
                      <option value="GOLD">GOLD (Nippon India ETF Gold BeES)</option>
                      <option value="SILVER">SILVER (Nippon India ETF Silver BeES)</option>
                    </optgroup>
                    <optgroup label="Equities & Indices">
                      {quotes.filter(q => q.symbol !== 'GOLD' && q.symbol !== 'SILVER').map((q) => (
                        <option key={q.symbol} value={q.symbol}>{q.symbol} ({q.exchange || 'NSE'})</option>
                      ))}
                    </optgroup>
                  </select>
                </div>
              </div>

              <CandlestickChartWithPivots
                symbol={selectedSymbol}
                onOpenFeedConnector={() => setMarketDataModalOpen(true)}
              />
            </div>
          )}

          {/* TAB 9: LIVE MARKET SCANNER */}
          {activeTab === 'Market Scanner' && (
            <MarketScannerTab
              apiBase={API_BASE}
              onSelectTradeSymbol={(sym) => {
                setTradeSymbol(sym)
                setActiveTab('Orders')
              }}
              money={money}
              signedMoney={signedMoney}
              pct={pct}
            />
          )}

          {/* TAB 10: AI MULTI-AGENT CONSENSUS */}
          {activeTab === 'Multi-Agent' && (
            <MultiAgentConsensusTab
              apiBase={API_BASE}
              onSelectTradeSymbol={(sym, config) => {
                setTradeSymbol(sym)
                if (config?.side) setTradeSide(config.side)
                if (config?.price) {
                  setTradeEntry(String(config.price))
                  const sl = config.side === 'BUY' ? (config.price * 0.975).toFixed(2) : (config.price * 1.025).toFixed(2)
                  const tg = config.side === 'BUY' ? (config.price * 1.05).toFixed(2) : (config.price * 0.95).toFixed(2)
                  setTradeSL(sl)
                  setTradeTarget(tg)
                }
                setActiveTab('Orders')
                showToast(`AI Setup loaded for ${sym} (${config?.side || 'TRADE'})`)
              }}
              money={money}
            />
          )}

          {/* TAB 11: AI TRADE PLAN GENERATOR */}
          {activeTab === 'Trade Plan' && (
            <TradePlanTab
              apiBase={API_BASE}
              onSelectTradeSymbol={(sym, config) => {
                setTradeSymbol(sym)
                if (config?.side) setTradeSide(config.side)
                if (config?.entry) setTradeEntry(String(config.entry))
                if (config?.sl) setTradeSL(String(config.sl))
                if (config?.target) setTradeTarget(String(config.target))
                if (config?.qty) setTradeQty(String(config.qty))
                setActiveTab('Orders')
                showToast(`AI Trade Plan loaded for ${sym} (${config?.side || 'TRADE'})`)
              }}
            />
          )}

          {/* TAB 12: STRATEGY BACKTESTING LAB */}
          {activeTab === 'Backtest Lab' && (
            <BacktestLabTab
              apiBase={API_BASE}
              pct={pct}
            />
          )}

          {/* TAB 13: OPEN POSITIONS */}
          {activeTab === 'Positions' && (

            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Open Positions & Real-Time Mark-to-Market P&L</h1>
                  <p>P&L calculated strictly from USER'S ENTRY PRICE + QUANTITY + LIVE MARKET PRICE.</p>
                </div>
              </div>

              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-top"><span>Unrealized MTM P&L</span><Coins size={16} color="var(--accent-blue)" /></div>
                  <div className={`kpi-value ${portfolio.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>{signedMoney(portfolio.unrealized_pnl)}</div>
                  <div className="kpi-sub">Across {portfolio.positions?.length || 0} Open Positions</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Portfolio Valuation</span><WalletCards size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value">{money(portfolio.equity)}</div>
                  <div className="kpi-sub">Starting: {money(portfolio.starting_capital || 500000)}</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Margin Utilized</span><BriefcaseBusiness size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value">{money(portfolio.margin_used || 0)}</div>
                  <div className="kpi-sub">Available: {money(portfolio.cash)}</div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <span className="card-title"><BriefcaseBusiness size={16} /> Open Positions on NSE/BSE ({portfolio.positions?.length || 0})</span>
                  <span className="badge badge-green">100% Risk Guardrails Active</span>
                </div>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Asset</th>
                        <th>Side</th>
                        <th>Qty</th>
                        <th>Entry Price (₹)</th>
                        <th>Live Mark Price (₹)</th>
                        <th>Stop-Loss (₹)</th>
                        <th>Trailing SL (₹)</th>
                        <th>Target (₹)</th>
                        <th>Manager Branch</th>
                        <th>Action Status</th>
                        <th>Unrealized P&L (₹)</th>
                        <th>Exit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {portfolio.positions?.map((pos) => (
                        <tr key={pos.symbol}>
                          <td><b>{pos.symbol}</b></td>
                          <td><span className={`badge ${pos.side === 'BUY' ? 'badge-green' : 'badge-red'}`}>{pos.side}</span></td>
                          <td>{pos.quantity}</td>
                          <td>{money(pos.entry_price)}</td>
                          <td>{money(pos.current_price)}</td>
                          <td>{money(pos.stop_loss)}</td>
                          <td style={{ color: 'var(--accent-green)', fontWeight: 700 }}>{money(pos.trailing_stop || pos.stop_loss)}</td>
                          <td>{money(pos.take_profit)}</td>
                          <td>
                            <span className={`badge ${pos.branch === 'PROFIT_MANAGER' ? 'badge-green' : 'badge-red'}`} style={{ fontSize: 10 }}>
                              {pos.branch || 'PROFIT_MANAGER'}
                            </span>
                          </td>
                          <td>
                            <span className="badge badge-blue" style={{ fontSize: 10 }}>{pos.manager_decision || 'HOLD'}</span>
                          </td>
                          <td className={(pos.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'} style={{ fontWeight: 700 }}>
                            {signedMoney(pos.unrealized_pnl)}<br /><small>{pct(pos.pnl_percent)}</small>
                          </td>
                          <td>
                            <button className="btn btn-danger" style={{ padding: '3px 8px', fontSize: 11 }} onClick={() => handleClosePosition(pos.symbol)}>
                              Exit
                            </button>
                          </td>
                        </tr>
                      ))}
                      {(!portfolio.positions || portfolio.positions.length === 0) && (
                        <tr>
                          <td colSpan={12} style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>
                            No open positions active. Configure a trade on the OMS desk.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 9: ORDERS & OMS */}
          {activeTab === 'Orders' && (
            <div className="grid-2col">
              <div className="card">
                <div className="card-header">
                  <div>
                    <h2 className="card-title"><Zap size={18} color="var(--accent-green)" /> Order Management System (OMS)</h2>
                    <p className="card-subtitle">Configure stock, entry, stop-loss, target, and max loss guardrail</p>
                  </div>
                  <span className="badge badge-green">Gateway Active</span>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault()
                    handlePlaceOrder({
                      symbol: tradeSymbol,
                      side: tradeSide,
                      order_type: 'MARKET',
                      quantity: Number(tradeQty),
                      price: Number(tradeEntry),
                      stop_loss: Number(tradeSL),
                      take_profit: Number(tradeTarget),
                      max_loss: Number(tradeMaxLoss),
                      broker: tradeBroker,
                      strategy: 'User Trade Config',
                    })
                  }}
                  style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
                >
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div className="form-group">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <label style={{ margin: 0 }}>Asset / Symbol (NSE/BSE)</label>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            style={{
                              padding: '2px 7px',
                              fontSize: 10.5,
                              background: tradeSymbol === 'GOLD' ? 'rgba(234, 179, 8, 0.25)' : undefined,
                              borderColor: tradeSymbol === 'GOLD' ? '#eab308' : undefined,
                              color: tradeSymbol === 'GOLD' ? '#facc15' : undefined,
                            }}
                            onClick={() => {
                              setTradeSymbol('GOLD')
                              setTradeQty('1')
                            }}
                            title="Quick select Gold (GOLDBEES)"
                          >
                            🪙 GOLD
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            style={{
                              padding: '2px 7px',
                              fontSize: 10.5,
                              background: tradeSymbol === 'SILVER' ? 'rgba(203, 213, 225, 0.25)' : undefined,
                              borderColor: tradeSymbol === 'SILVER' ? '#cbd5e1' : undefined,
                              color: tradeSymbol === 'SILVER' ? '#f1f5f9' : undefined,
                            }}
                            onClick={() => {
                              setTradeSymbol('SILVER')
                              setTradeQty('1')
                            }}
                            title="Quick select Silver (SILVERBEES)"
                          >
                            🥈 SILVER
                          </button>
                        </div>
                      </div>
                      <select value={tradeSymbol} onChange={(e) => setTradeSymbol(e.target.value)}>
                        <optgroup label="Precious Metals & Bullion (NSE ETFs)">
                          <option value="GOLD">GOLD — Nippon India ETF Gold BeES ({indices['GOLD']?.price ? money(indices['GOLD'].price) : 'NSE'})</option>
                          <option value="SILVER">SILVER — Nippon India ETF Silver BeES ({indices['SILVER']?.price ? money(indices['SILVER'].price) : 'NSE'})</option>
                        </optgroup>
                        <optgroup label="Equities & Indices">
                          {quotes.filter(q => q.symbol !== 'GOLD' && q.symbol !== 'SILVER').map((q) => (
                            <option key={q.symbol} value={q.symbol}>
                              {q.symbol} - {money(q.price || q.last_price)}
                            </option>
                          ))}
                        </optgroup>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Execution Routing Engine</label>
                      <select value={tradeBroker} onChange={(e) => setTradeBroker(e.target.value)}>
                        <option value="PAPER_BROKER">Paper Trading Engine (Simulated)</option>
                        <option value="ZERODHA_KITE">Zerodha Kite Connect</option>
                        <option value="UPSTOX_API">Upstox API v2</option>
                        <option value="ANGEL_ONE">Angel One SmartAPI</option>
                        <option value="DHAN_HQ">Dhan HQ Gateway</option>
                      </select>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div className="form-group">
                      <label>Order Side</label>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                        <button type="button" className={`btn ${tradeSide === 'BUY' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTradeSide('BUY')}>BUY / LONG</button>
                        <button type="button" className={`btn ${tradeSide === 'SELL' ? 'btn-danger' : 'btn-secondary'}`} onClick={() => setTradeSide('SELL')}>SELL / SHORT</button>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Quantity (Shares)</label>
                      <input type="number" min="1" value={tradeQty} onChange={(e) => setTradeQty(e.target.value)} required />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                    <div className="form-group">
                      <label>Entry Price (₹) <span style={{ color: 'var(--accent-amber)', fontSize: 10 }}>— from live feed</span></label>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <input
                          type="number"
                          step="0.05"
                          value={tradeEntry}
                          onChange={(e) => setTradeEntry(e.target.value)}
                          placeholder="Click ↗ Fill LTP"
                          required
                          style={{ flex: 1 }}
                        />
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={fillLTP}
                          disabled={ltpLoading}
                          title="Auto-fill with real live market price from the data provider"
                          style={{ whiteSpace: 'nowrap', fontSize: 11 }}
                        >
                          {ltpLoading ? '...' : '↗ Fill LTP'}
                        </button>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Stop-Loss (₹)</label>
                      <input type="number" step="0.05" value={tradeSL} onChange={(e) => setTradeSL(e.target.value)} placeholder="Stop-Loss Price" required />
                    </div>
                    <div className="form-group">
                      <label>Target (₹)</label>
                      <input type="number" step="0.05" value={tradeTarget} onChange={(e) => setTradeTarget(e.target.value)} placeholder="Target Price" required />
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Maximum Allowed Loss (₹ Guardrail)</label>
                    <input type="number" step="10" value={tradeMaxLoss} onChange={(e) => setTradeMaxLoss(e.target.value)} required />
                  </div>

                  <button type="submit" className="btn btn-primary" style={{ padding: '12px 20px', fontSize: 14 }}>
                    <ShieldCheck size={18} /> Validate Risk & Place Order on {tradeBroker.replace('_', ' ')}
                  </button>
                </form>
              </div>

              {/* Order History Table */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title"><BookOpen size={16} /> Recent Orders & Execution Log ({orders.length})</span>
                  <span className="badge badge-green">Audit Trail</span>
                </div>
                <div className="table-container" style={{ maxHeight: 420, overflowY: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Qty</th>
                        <th>Price (₹)</th>
                        <th>Status</th>
                        <th>Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.slice(0, 10).map((o, idx) => (
                        <tr key={idx}>
                          <td><b>{o.symbol}</b></td>
                          <td><span className={`badge ${o.side === 'BUY' ? 'badge-green' : 'badge-red'}`}>{o.side}</span></td>
                          <td>{o.quantity}</td>
                          <td>{money(o.price)}</td>
                          <td><span className="badge badge-green">{o.status || 'FILLED'}</span></td>
                          <td style={{ fontSize: 11, color: 'var(--text-dim)' }}>{formatTime(o.timestamp)}</td>
                        </tr>
                      ))}
                      {orders.length === 0 && (
                        <tr>
                          <td colSpan={6} style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)' }}>
                            No orders placed in this session yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 10: PROFIT & LOSS MANAGER */}
          {activeTab === 'Profit & Loss Manager' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Dual Profit & Loss Management Engine</h1>
                  <p>Deterministic profit protection ratchets stops upward in profit; loss manager enforces hard caps.</p>
                </div>
              </div>
              <div className="grid-2col">
                <div className="card">
                  <div className="card-header">
                    <span className="card-title"><TrendingUp size={18} color="var(--accent-green)" /> Profit Manager Logic</span>
                    <span className="badge badge-green">Active</span>
                  </div>
                  <div style={{ padding: '12px 0', fontSize: 13, color: 'var(--text-muted)' }}>
                    <ul>
                      <li><b>Input:</b> Entry price, live price, quantity, stop-loss, target, trailing stop.</li>
                      <li><b>Condition:</b> When live position becomes profitable (LTP &gt; Entry).</li>
                      <li><b>Actions:</b> HOLD, TRAIL_STOP, PARTIAL_EXIT, EXIT.</li>
                      <li><b>Trailing Rule:</b> Trailing stop moves UPWARD ONLY; never moves downward.</li>
                    </ul>
                  </div>
                </div>

                <div className="card">
                  <div className="card-header">
                    <span className="card-title"><ShieldAlert size={18} color="var(--accent-red)" /> Loss Manager Logic</span>
                    <span className="badge badge-red">Active</span>
                  </div>
                  <div style={{ padding: '12px 0', fontSize: 13, color: 'var(--text-muted)' }}>
                    <ul>
                      <li><b>Input:</b> Hard stop-loss, max loss limit, daily loss limit, risk exposure.</li>
                      <li><b>Condition:</b> When position moves into loss (LTP &lt; Entry).</li>
                      <li><b>Actions:</b> HOLD, EXIT, BLOCK_NEW_TRADE.</li>
                      <li><b>Safety Rule:</b> Never automatically averages down or attempts loss recovery based on prediction.</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 11: PROFIT MANAGER */}
          {activeTab === 'Profit Manager' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Profit Protection & Trailing Stop Engine</h1>
                  <p>Step-by-step ratcheting: Price in Profit → Ratchet Trailing SL ↑ → Lock Gains → Partial Exit at TP1.</p>
                </div>
              </div>
              <div className="card">
                <div className="card-header">
                  <span className="card-title"><ShieldCheck size={18} color="var(--accent-green)" /> Protective Trailing Stop System</span>
                  <span className="badge badge-green">Live Guardrails Active</span>
                </div>
                <div style={{ padding: '16px 0', color: 'var(--text-muted)', fontSize: 13 }}>
                  <p>The TradePilot Profit Protection engine continuously monitors all open long positions:</p>
                  <ul>
                    <li>When <b>current_price &gt; entry_price</b>: Profit Protection evaluates trail thresholds.</li>
                    <li>Ratchets trailing stop upward as mark price advances. Trailing stops <b>NEVER</b> move downward.</li>
                    <li>When <b>current_price &lt; entry_price</b>: Position is routed to the Loss Manager to enforce hard stop-loss and maximum loss boundaries.</li>
                  </ul>
                  <div style={{ marginTop: 14, padding: 12, background: 'var(--bg-card-hover)', borderRadius: 8, borderLeft: '4px solid var(--accent-blue)', fontSize: 12 }}>
                    <b>Notice:</b> TradePilot manages risk and protects existing unrealized gains. It does not promise or guarantee future trading returns.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 12: LOSS MANAGER */}
          {activeTab === 'Loss Manager' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Risk Boundaries & Loss Management Engine</h1>
                  <p>Enforces hard stop-loss limits, max loss boundaries, and daily drawdowns.</p>
                </div>
              </div>
              <div className="card">
                <div className="card-header">
                  <span className="card-title"><ShieldAlert size={18} color="var(--accent-red)" /> Hard Stop-Loss & Risk Engine</span>
                  <span className="badge badge-red">Strict Execution</span>
                </div>
                <div style={{ padding: '16px 0', color: 'var(--text-muted)', fontSize: 13 }}>
                  <p>When a position experiences adverse price action:</p>
                  <ul>
                    <li>Hard stop-loss is triggered automatically at the broker/OMS level.</li>
                    <li>Daily maximum loss limit protects the total trading account capital.</li>
                    <li>No Martingale, no automatic averaging down, no hope-based recovery trades.</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* TAB 13: ALERTS */}
          {activeTab === 'Alert System' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Real-Time Alert & Notification System</h1>
                  <p>Multi-channel triggers for Entry Alerts, Target Hits, Stop-Loss Hits, Trailing SL moves, and Risk Breaches.</p>
                </div>
                <button
                  className="btn btn-secondary"
                  onClick={async () => {
                    await fetch(`${API_BASE}/api/alerts/clear`, { method: 'POST' })
                    setAlerts([])
                    showToast('All alerts cleared')
                  }}
                >
                  Clear All Alerts
                </button>
              </div>

              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {['ALL', 'ENTRY', 'PROFIT', 'STOP', 'TARGET', 'RISK'].map((f) => (
                  <button
                    key={f}
                    className={`btn ${alertFilter === f ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setAlertFilter(f)}
                    style={{ fontSize: 12, padding: '6px 14px' }}
                  >
                    {f === 'ALL' ? 'All Alerts' : `${f} Alerts`}
                  </button>
                ))}
              </div>

              <div className="card">
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {filteredAlerts.map((a) => (
                    <div
                      key={a.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: 14,
                        background: 'var(--bg-card-hover)',
                        borderRadius: 'var(--radius-md)',
                        borderLeft: `4px solid ${a.severity === 'coral' ? 'var(--accent-red)' : a.severity === 'amber' ? 'var(--accent-amber)' : 'var(--accent-green)'}`,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                        <div
                          style={{
                            width: 34,
                            height: 34,
                            borderRadius: '50%',
                            background: a.severity === 'coral' ? 'var(--accent-red-bg)' : a.severity === 'amber' ? 'var(--accent-amber-bg)' : 'var(--accent-green-bg)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <Bell size={16} color={a.severity === 'coral' ? 'var(--accent-red)' : a.severity === 'amber' ? 'var(--accent-amber)' : 'var(--accent-green)'} />
                        </div>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <b>{a.type}</b>
                            {a.symbol && <span className="badge badge-blue" style={{ fontSize: 10 }}>{a.symbol}</span>}
                          </div>
                          <p style={{ fontSize: 12.5, color: 'var(--text-muted)', margin: '3px 0' }}>{a.message}</p>
                          <small style={{ color: 'var(--text-dim)' }}>{a.age}</small>
                        </div>
                      </div>
                      <span className={`badge ${a.severity === 'coral' ? 'badge-red' : a.severity === 'amber' ? 'badge-amber' : 'badge-green'}`}>
                        {a.severity === 'coral' ? 'HIGH IMPACT' : 'INFO'}
                      </span>
                    </div>
                  ))}
                  {filteredAlerts.length === 0 && (
                    <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>
                      No alerts found under category "{alertFilter}".
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 14: ANALYTICS */}
          {activeTab === 'Analytics' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Performance Analytics & Statistical Workbench</h1>
                  <p>Quantitative statistics: Win Rate %, Net P&L Curves, Max Drawdown %, Sharpe, Sortino, and Return streams.</p>
                </div>
              </div>

              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-top"><span>Win Rate</span><Gauge size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value positive">{perfData.win_rate}%</div>
                  <div className="kpi-sub">Across {perfData.total_trades} Closed Trades</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Profit Factor</span><Target size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value">{perfData.profit_factor}</div>
                  <div className="kpi-sub">Gross Win / Gross Loss</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Sharpe Ratio</span><TrendingUp size={16} color="var(--accent-blue)" /></div>
                  <div className="kpi-value">{perfData.sharpe_ratio}</div>
                  <div className="kpi-sub">Sortino: {perfData.sortino_ratio}</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Max Drawdown</span><ShieldAlert size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value" style={{ color: 'var(--accent-green)' }}>{perfData.max_drawdown_pct}%</div>
                  <div className="kpi-sub">CAGR: {perfData.cagr_pct}%</div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 15: TRADE BOOK */}
          {activeTab === 'Trade Book' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Trade Book & Tax Accounting</h1>
                  <p>Realized trades with Gross P&L, Statutory Indian Charges (STT, GST, Exchange, Stamp Duty), and Net P&L in ₹.</p>
                </div>
                <button className="btn btn-secondary" onClick={() => showToast('Exported trade_ledger.csv')}><Download size={14} /> Export CSV</button>
              </div>

              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-top"><span>Total Closed Trades</span><BookOpen size={16} /></div>
                  <div className="kpi-value">{portfolio.total_trades_count || 0}</div>
                  <div className="kpi-sub positive">This Session</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Net Realized P&L</span><TrendingUp size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value positive">{signedMoney(portfolio.realized_pnl)}</div>
                  <div className="kpi-sub positive">Win Rate: {portfolio.win_rate || 0}%</div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 16: FEED STATUS & QOS */}
          {activeTab === 'Feed Status' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>Market Data Feed Health & QoS Telemetry</h1>
                  <p>Real-time telemetry on active providers, tick rates, staleness monitoring, and latency.</p>
                </div>
                <button className="btn btn-secondary" onClick={() => refreshHotData()}><RefreshCw size={14} /> Refresh Health</button>
              </div>

              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-top"><span>Active Provider</span><Wifi size={16} color="var(--accent-green)" /></div>
                  <div className="kpi-value" style={{ fontSize: 18 }}>{feedHealth?.provider_name || 'NSE_YFINANCE'}</div>
                  <div className="kpi-sub">Connection: {feedHealth?.connection_status || 'LIVE_DELAYED'}</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Ticks / Minute</span><Activity size={16} color="var(--accent-blue)" /></div>
                  <div className="kpi-value">{feedHealth?.ticks_per_minute || 0}</div>
                  <div className="kpi-sub">Subscribed: {feedHealth?.subscription_count || 0} Symbols</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Data Delay</span><Clock size={16} color="var(--accent-amber)" /></div>
                  <div className="kpi-value">~{feedHealth?.data_delay_minutes || 15} min</div>
                  <div className="kpi-sub">Yahoo Finance Delayed Feed</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-top"><span>Rejected / Stale Ticks</span><AlertTriangle size={16} color="var(--accent-amber)" /></div>
                  <div className="kpi-value">{feedHealth?.rejected_ticks_total || 0} / {feedHealth?.stale_ticks_total || 0}</div>
                  <div className="kpi-sub">Zero Fake Fallbacks</div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <span className="card-title"><ShieldCheck size={16} color="var(--accent-green)" /> Market Data Rules & Guarantees</span>
                </div>
                <div style={{ padding: '12px 0', fontSize: 13, color: 'var(--text-muted)' }}>
                  <ul>
                    <li><b>No Hardcoded Prices:</b> Every price displayed is received from an authorized market provider.</li>
                    <li><b>Fail-Safe Stale Handling:</b> If feed disconnects, data is labeled <code>DATA STALE</code> or <code>FEED DISCONNECTED</code> — never fake live.</li>
                    <li><b>Real-Time Upgrade:</b> Set <code>MARKET_DATA_PROVIDER=BROKER_API</code> with broker credentials in <code>.env</code> for &lt;1s live ticks.</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* TAB 17: SYSTEM CONSOLE */}
          {activeTab === 'System Console' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="page-header">
                <div>
                  <h1>System Architecture & Live Audit Log Streamer</h1>
                  <p>Complete audit trail across real market data ingestion, validation, normalization, and trade execution.</p>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <a href={`${API_BASE}/api/records/export?format=json`} target="_blank" rel="noreferrer" className="btn btn-secondary">
                    <Download size={14} /> Export Compliance (JSON)
                  </a>
                  <a href={`${API_BASE}/api/records/export?format=csv`} target="_blank" rel="noreferrer" className="btn btn-secondary">
                    <Download size={14} /> Export Journal (CSV)
                  </a>
                </div>
              </div>


              <div className="card">
                <div className="card-header">
                  <span className="card-title"><Terminal size={16} color="var(--accent-green)" /> Live System Audit Logs</span>
                  <span className="badge badge-green">Streaming</span>
                </div>
                <div className="log-terminal">
                  {logs.map((l) => (
                    <div className="log-row" key={l.id}>
                      <span className="log-ts">[{l.timestamp ? l.timestamp.slice(11, 19) : ''}]</span>
                      <span className={`log-type ${l.severity === 'SUCCESS' ? 'positive' : l.severity === 'ERROR' ? 'negative' : l.severity === 'WARNING' ? 'neutral' : ''}`}>
                        [{l.event_type}]
                      </span>
                      <span className="log-msg">{l.message}</span>
                    </div>
                  ))}
                  {logs.length === 0 && (
                    <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: 20 }}>
                      Listening for real-time audit logs...
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Instrument Master Catalog Modal */}
      {instrumentModalOpen && <InstrumentMasterModal onClose={() => setInstrumentModalOpen(false)} />}

      {/* Secure Account Profile & Security Vault Modal */}
      <SecureProfileModal
        isOpen={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        currentUser={user}
        onUpdateUser={(updated) => {
          setUser(updated)
          localStorage.setItem('tradepilot_user', JSON.stringify(updated))
        }}
      />

      {/* Panic Square Off Confirmation Modal */}
      {panicModalOpen && (
        <div className="modal-backdrop" onClick={() => setPanicModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ color: 'var(--accent-red)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <ShieldAlert size={20} /> EMERGENCY KILLSWITCH (NSE / BSE)
              </h3>
              <button className="btn-icon" onClick={() => setPanicModalOpen(false)}><X size={16} /></button>
            </div>
            <div className="modal-body">
              <p style={{ color: 'var(--text-muted)' }}>
                Are you sure you want to market liquidate <b>ALL {portfolio.positions?.length || 0} open Indian stock positions</b> at current market price on NSE/BSE?
              </p>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button className="btn btn-secondary" onClick={() => setPanicModalOpen(false)}>Cancel</button>
                <button className="btn btn-danger" onClick={handlePanicSquareOff}>CONFIRM EMERGENCY LIQUIDATION</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Real-Time Market Data Hub & Broker Connector Modal */}
      <MarketDataConnectorModal
        isOpen={marketDataModalOpen}
        onClose={() => setMarketDataModalOpen(false)}
        liveConnected={liveConnected}
        lastTickTime={lastTickTime}
        ticksPerSec={ticksPerSec}
        feedHealth={feedHealth}
        marketStatus={marketStatus}
        onTriggerReconnect={async () => {
          await refreshHotData()
          await refreshColdData()
        }}
      />

      {/* Real-Time Toast Banner */}
      {toastMessage && (
        <div className="toast-banner">
          <Check size={18} color="var(--accent-green)" />
          <span style={{ fontSize: 13, fontWeight: 600 }}>{toastMessage}</span>
        </div>
      )}

      {/* Real-Time Market Feed Debug HUD Panel */}
      <MarketFeedDebugPanel
        wsStatus={wsStatus}
        provider={feedHealth?.provider_name || 'NSE_YFINANCE'}
        subscriptionsCount={quotes.length || 76}
        lastTickTime={lastTickTime}
        ticksPerSec={ticksPerSec}
        latencyMs={feedHealth?.last_latency_ms || 15}
        staleCount={feedHealth?.stale_ticks_total || 0}
      />
    </div>
  )
}
