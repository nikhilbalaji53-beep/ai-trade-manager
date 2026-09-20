import React, { useState, useEffect, useMemo, useRef } from 'react'
import {
  Flame,
  Bot,
  Target,
  Gauge,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ArrowUpRight,
  TrendingUp,
  RefreshCw,
  CheckCircle2,
  Zap,
  Search,
  X,
  Sparkles,
  Globe,
} from 'lucide-react'

export function MarketScannerTab({ apiBase, onSelectTradeSymbol, money, signedMoney, pct }) {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('ALL')
  const [market, setMarket] = useState('ALL')
  const [minConf, setMinConf] = useState(60)

  const fetchScanner = () => {
    setLoading(true)
    const url = `${apiBase}/api/v1/market/scanner?category=${category}&market=${market}&min_confidence=${minConf}`
    fetch(url)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setResults(data || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchScanner()
  }, [category, market, minConf])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Flame color="#f59e0b" size={24} /> Real-Time Live Market Scanner
          </h1>
          <p>Scans Indian (NSE/BSE) and US (NASDAQ/NYSE) stocks across Breakouts, Momentum, Candlesticks, and Mean Reversion.</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchScanner} disabled={loading}>
          <RefreshCw size={14} /> Refresh Scanner
        </button>
      </div>

      <div className="card" style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap', padding: '12px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 700 }}>Market:</span>
          <select value={market} onChange={(e) => setMarket(e.target.value)} style={{ padding: '6px 12px', background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--border-subtle)', borderRadius: 6 }}>
            <option value="ALL">Global (NSE + US)</option>
            <option value="IN">Indian Equities (NSE)</option>
            <option value="US">US Equities (NASDAQ/NYSE)</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 700 }}>Pattern Category:</span>
          <select value={category} onChange={(e) => setCategory(e.target.value)} style={{ padding: '6px 12px', background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--border-subtle)', borderRadius: 6 }}>
            <option value="ALL">All Technical Categories</option>
            <option value="BREAKOUT">High-Volume Breakouts</option>
            <option value="MOMENTUM">Momentum & Trend Flips</option>
            <option value="CANDLESTICK">Candlestick Reversals</option>
            <option value="GAINER">Top Session Gainers</option>
            <option value="LOSER">Top Session Losers</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 700 }}>Min Confidence:</span>
          <span style={{ fontSize: 12, color: 'var(--accent-blue)', fontWeight: 800 }}>{minConf}%</span>
          <input type="range" min={50} max={90} step={5} value={minConf} onChange={(e) => setMinConf(Number(e.target.value))} style={{ width: 100 }} />
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title"><Flame size={16} color="#f59e0b" /> Detected Technical Setups ({results.length})</span>
          <span className="badge badge-green">Real Live Feeds Only</span>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Market</th>
                <th>Pattern Detected</th>
                <th>Category</th>
                <th>Signal</th>
                <th>Confidence</th>
                <th>LTP</th>
                <th>Session Change</th>
                <th>Risk Score</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, idx) => (
                <tr key={idx}>
                  <td><b>{r.symbol}</b></td>
                  <td><span className={`badge ${r.market === 'IN' ? 'badge-blue' : 'badge-purple'}`}>{r.market}</span></td>
                  <td><span style={{ fontWeight: 600 }}>{r.pattern}</span></td>
                  <td><span className="badge badge-blue" style={{ fontSize: 10 }}>{r.category}</span></td>
                  <td>
                    <span className={`badge ${r.signal_type === 'BUY' ? 'badge-green' : r.signal_type === 'SELL' ? 'badge-red' : 'badge-amber'}`}>
                      {r.signal_type}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ width: 50, height: 6, background: 'var(--border-subtle)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ width: `${r.confidence}%`, height: '100%', background: r.confidence >= 75 ? 'var(--accent-green)' : 'var(--accent-blue)' }} />
                      </div>
                      <span style={{ fontSize: 11, fontWeight: 700 }}>{r.confidence}%</span>
                    </div>
                  </td>
                  <td style={{ fontWeight: 800 }}>{r.current_price ? `${r.currency_symbol}${r.current_price.toFixed(2)}` : '—'}</td>
                  <td className={(r.change_percent || 0) >= 0 ? 'positive' : 'negative'}>{pct(r.change_percent)}</td>
                  <td>
                    <span className={`badge ${r.risk_score <= 4 ? 'badge-green' : r.risk_score <= 7 ? 'badge-amber' : 'badge-red'}`}>
                      Risk {r.risk_score}/10
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-primary" style={{ padding: '3px 8px', fontSize: 11 }} onClick={() => onSelectTradeSymbol(r.symbol)}>
                      Trade
                    </button>
                  </td>
                </tr>
              ))}
              {results.length === 0 && (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: 24, color: 'var(--text-dim)' }}>
                    {loading ? 'Scanning market instruments...' : 'No patterns matched the active filter criteria.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── Universal Real-Time Symbol Search Bar & Autocomplete ──
export function SymbolSearchBar({ symbol, onSelectSymbol, apiBase, placeholder = "Search Indian (NSE) or US (NASDAQ) symbol (e.g. RELIANCE, TCS, AAPL)..." }) {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [instruments, setInstruments] = useState([])
  const wrapperRef = useRef(null)

  const quickPicks = [
    { sym: 'RELIANCE', name: 'Reliance Industries', market: 'NSE', flag: '🇮🇳' },
    { sym: 'TCS', name: 'Tata Consultancy Services', market: 'NSE', flag: '🇮🇳' },
    { sym: 'INFY', name: 'Infosys Limited', market: 'NSE', flag: '🇮🇳' },
    { sym: 'HDFCBANK', name: 'HDFC Bank', market: 'NSE', flag: '🇮🇳' },
    { sym: 'TITAN', name: 'Titan Company', market: 'NSE', flag: '🇮🇳' },
    { sym: 'AAPL', name: 'Apple Inc.', market: 'NASDAQ', flag: '🇺🇸' },
    { sym: 'NVDA', name: 'NVIDIA Corp.', market: 'NASDAQ', flag: '🇺🇸' },
    { sym: 'TSLA', name: 'Tesla Inc.', market: 'NASDAQ', flag: '🇺🇸' },
  ]

  useEffect(() => {
    let active = true
    if (apiBase) {
      fetch(`${apiBase}/api/v1/market/instruments`)
        .then(res => res.ok ? res.json() : [])
        .then(data => {
          if (active && Array.isArray(data)) setInstruments(data)
        })
        .catch(() => {})
    }
    return () => { active = false }
  }, [apiBase])

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filtered = useMemo(() => {
    if (!query.trim()) return []
    const q = query.trim().toUpperCase()
    const matches = instruments.filter(i => 
      i.symbol?.toUpperCase().includes(q) || 
      (i.name && i.name.toUpperCase().includes(q))
    ).slice(0, 8)
    if (matches.length > 0) return matches
    return quickPicks.filter(p => p.sym.includes(q) || p.name.toUpperCase().includes(q))
  }, [query, instruments])

  const handlePick = (sym) => {
    onSelectSymbol(sym.toUpperCase())
    setQuery('')
    setIsOpen(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (filtered.length > 0) {
        handlePick(filtered[0].symbol || filtered[0].sym)
      } else if (query.trim()) {
        handlePick(query.trim())
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%', background: 'var(--bg-card)', padding: '14px 18px', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
      <div ref={wrapperRef} style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        {/* Search Input Box */}
        <div style={{
          position: 'relative',
          flex: '1 1 340px',
          display: 'flex',
          alignItems: 'center',
          background: 'var(--bg-main, #0b1120)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 8,
          padding: '0 12px',
          boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.3)',
        }}>
          <Search size={16} color="var(--text-dim)" style={{ marginRight: 8, flexShrink: 0 }} />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setIsOpen(true)
            }}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            style={{
              width: '100%',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-main)',
              fontSize: 13,
              padding: '10px 0',
              fontWeight: 600,
            }}
          />
          {query && (
            <button
              type="button"
              onClick={() => { setQuery(''); setIsOpen(false) }}
              style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: 2 }}
            >
              <X size={14} />
            </button>
          )}

          {/* Autocomplete Dropdown */}
          {isOpen && filtered.length > 0 && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              marginTop: 6,
              background: 'var(--bg-card, #131d33)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8,
              boxShadow: '0 12px 30px rgba(0,0,0,0.5)',
              zIndex: 100,
              overflow: 'hidden',
              maxHeight: 280,
              overflowY: 'auto',
            }}>
              {filtered.map((item, idx) => {
                const s = item.symbol || item.sym
                const n = item.name || s
                const ex = item.exchange || item.market || 'NSE'
                const isUS = ex.includes('NASDAQ') || ex.includes('NYSE') || item.market === 'US'
                return (
                  <div
                    key={idx}
                    onClick={() => handlePick(s)}
                    style={{
                      padding: '10px 14px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      borderBottom: '1px solid var(--border-subtle)',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-card-hover, rgba(255,255,255,0.06))'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    <div>
                      <span style={{ fontWeight: 800, color: 'var(--text-main)', marginRight: 8 }}>{s}</span>
                      <span style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>{n}</span>
                    </div>
                    <span className={`badge ${isUS ? 'badge-purple' : 'badge-blue'}`} style={{ fontSize: 10 }}>
                      {isUS ? '🇺🇸 ' + ex : '🇮🇳 ' + ex}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Selected Symbol Display Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          background: 'rgba(56, 189, 248, 0.1)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          padding: '8px 16px',
          borderRadius: 8,
        }}>
          <span style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.04em' }}>Selected:</span>
          <span style={{ fontSize: 16, fontWeight: 900, color: '#38bdf8', letterSpacing: '0.02em' }}>{symbol}</span>
          <span className="badge badge-green" style={{ fontSize: 10, padding: '2px 6px' }}>● LIVE QUOTE</span>
        </div>
      </div>

      {/* Quick Picks Carousel / Pills */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', paddingTop: 2 }}>
        <span style={{ fontSize: 11.5, color: 'var(--text-dim)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 5 }}>
          <Sparkles size={13} color="var(--accent-amber)" /> Quick Select:
        </span>
        {quickPicks.map((qp) => {
          const active = symbol.toUpperCase() === qp.sym
          return (
            <button
              key={qp.sym}
              type="button"
              onClick={() => handlePick(qp.sym)}
              style={{
                background: active ? 'rgba(56, 189, 248, 0.22)' : 'var(--bg-card-hover, #1e293b)',
                border: `1px solid ${active ? '#38bdf8' : 'var(--border-subtle)'}`,
                color: active ? '#38bdf8' : 'var(--text-main)',
                borderRadius: 6,
                padding: '4px 10px',
                fontSize: 11.5,
                fontWeight: active ? 800 : 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                transition: 'all 0.15s ease',
              }}
            >
              <span>{qp.flag}</span>
              <span>{qp.sym}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function MultiAgentConsensusTab({ apiBase, onSelectTradeSymbol, money }) {
  const [symbol, setSymbol] = useState('RELIANCE')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchConsensus = () => {
    setLoading(true)
    fetch(`${apiBase}/api/v1/ai/agents/consensus/${symbol}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((d) => {
        setData(d)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchConsensus()
  }, [symbol])

  // Extract agent ballots array safely whether backend returns dict or array
  const agentBallots = useMemo(() => {
    if (!data || !data.agent_votes) return []
    if (Array.isArray(data.agent_votes)) return data.agent_votes
    return Object.values(data.agent_votes)
  }, [data])

  const rec = data?.overall_recommendation || data?.consensus_action || 'HOLD'
  const isBuy = rec.includes('BUY')
  const isSell = rec.includes('SELL')
  const isVetoed = Boolean(data?.is_vetoed || data?.veto_triggered)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Bot color="#8b5cf6" size={24} /> AI Multi-Agent Consensus Architecture
          </h1>
          <p>4 Specialized Autonomous Agents vote with consensus aggregation. Risk Agent possesses strict VETO authority.</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchConsensus} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh Vote
        </button>
      </div>

      {/* Interactive Symbol Search Bar */}
      <SymbolSearchBar
        symbol={symbol}
        onSelectSymbol={(s) => setSymbol(s)}
        apiBase={apiBase}
        placeholder="Search any stock for AI Multi-Agent Consensus..."
      />

      <div style={{ padding: '10px 14px', background: 'rgba(59, 130, 246, 0.08)', borderLeft: '4px solid var(--accent-blue)', borderRadius: 6, fontSize: 12, color: 'var(--text-muted)' }}>
        <b>Notice:</b> {data?.disclaimer || 'AI predictions and agent consensus are probabilistic assessments and do not guarantee future returns.'}
      </div>

      {loading && !data && (
        <div className="card" style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={20} className="spin" style={{ marginRight: 10 }} />
          Computing 4-Agent Consensus for {symbol}...
        </div>
      )}

      {data && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card" style={{ borderTop: `3px solid ${isBuy ? 'var(--accent-green)' : isSell ? 'var(--accent-red)' : 'var(--accent-amber)'}` }}>
              <div className="kpi-top"><span>Consensus Recommendation</span><Bot size={16} color="#8b5cf6" /></div>
              <div className="kpi-value" style={{ fontSize: 22, fontWeight: 900, color: isBuy ? 'var(--accent-green)' : isSell ? 'var(--accent-red)' : 'var(--accent-amber)' }}>
                {rec.replace('_', ' ')}
              </div>
              <div className="kpi-sub">Score: {data.consensus_score ?? data.conviction ?? 0}/100</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Aggregate Confidence</span><Gauge size={16} color="var(--accent-blue)" /></div>
              <div className="kpi-value">{data.confidence_pct ?? data.conviction ?? 75}%</div>
              <div className="kpi-sub">Weighted Agent Confidence</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Risk Agent VETO</span><ShieldAlert size={16} color={isVetoed ? 'var(--accent-red)' : 'var(--accent-green)'} /></div>
              <div className="kpi-value" style={{ fontSize: 20, color: isVetoed ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                {isVetoed ? 'VETO ACTIVE' : 'PASSED'}
              </div>
              <div className="kpi-sub">{isVetoed ? (data.veto_reason || 'Risk threshold exceeded') : 'Risk governance satisfied'}</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Risk Score</span><TrendingUp size={16} color="var(--accent-green)" /></div>
              <div className="kpi-value" style={{ color: (data.risk_score || 0) > 7 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                {data.risk_score ?? 4.0}/10
              </div>
              <div className="kpi-sub">Execution Tier: {data.execution_tier || (data.consensus_score >= 80 ? 'HIGH CONVICTION' : 'STANDARD')}</div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title"><Bot size={16} color="#8b5cf6" /> Individual Agent Ballots ({agentBallots.length})</span>
              <span className="badge badge-purple">4-Agent Weighted Voting</span>
            </div>
            <div className="grid-2col" style={{ padding: 16, gap: 16 }}>
              {agentBallots.map((v, i) => {
                const decision = v.decision || v.signal_vote || 'NEUTRAL'
                const decIsBuy = decision.includes('BUY')
                const decIsSell = decision.includes('SELL')
                const conf = v.conviction_pct ?? v.confidence ?? 0
                const reasons = Array.isArray(v.reasons) ? v.reasons : (v.rationale ? [v.rationale] : ['Conditions satisfied'])

                return (
                  <div key={i} style={{ padding: 14, background: 'var(--bg-card-hover)', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontWeight: 800, fontSize: 14 }}>{v.agent_name || v.name}</span>
                        {v.role && <span style={{ fontSize: 10.5, color: 'var(--text-dim)', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: 4 }}>{v.role}</span>}
                        {v.veto_exercised && <span className="badge badge-red" style={{ fontSize: 9 }}>VETO APPLIED</span>}
                      </div>
                      <span className={`badge ${decIsBuy ? 'badge-green' : decIsSell ? 'badge-red' : 'badge-amber'}`}>
                        {decision} ({conf}%)
                      </span>
                    </div>
                    <ul style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 8px 0', paddingLeft: 18 }}>
                      {reasons.map((r, rIdx) => (
                        <li key={rIdx} style={{ marginBottom: 2 }}>{r}</li>
                      ))}
                    </ul>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: 6, marginTop: 6 }}>
                      <span>Weight: {Math.round((v.weight ?? 0.25) * 100)}%</span>
                      <span>Risk: {v.risk_score ?? data.risk_score ?? '—'}/10</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {onSelectTradeSymbol && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-card)', padding: '14px 20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div>
                <b style={{ fontSize: 14 }}>Execute AI Multi-Agent Recommendation</b>
                <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                  Consensus Action: <b style={{ color: isBuy ? 'var(--accent-green)' : isSell ? 'var(--accent-red)' : 'var(--accent-amber)' }}>{rec.replace('_', ' ')}</b> (Score: {data.consensus_score ?? data.conviction ?? 0}/100)
                </div>
              </div>
              <button
                className={`btn ${isBuy ? 'btn-primary' : isSell ? 'btn-danger' : 'btn-secondary'}`}
                style={{ padding: '8px 20px', fontSize: 13, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 6 }}
                onClick={() => onSelectTradeSymbol(symbol, {
                  side: isSell ? 'SELL' : 'BUY',
                  price: data.current_price,
                  conviction: data.consensus_score || data.conviction || 75,
                })}
              >
                <Zap size={16} /> Trade {symbol} ({isSell ? 'SELL' : 'BUY'}) in OMS
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export function TradePlanTab({ apiBase, onSelectTradeSymbol }) {
  const [symbol, setSymbol] = useState('RELIANCE')
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchPlan = () => {
    setLoading(true)
    fetch(`${apiBase}/api/v1/ai/trade-plan/${symbol}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((d) => {
        setPlan(d)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchPlan()
  }, [symbol])

  const curr = plan?.currency_symbol || '₹'
  const isBuy = plan?.direction === 'BUY'
  const entryStr = plan?.entry_zone || (plan?.entry_zone_low ? `${curr}${plan.entry_zone_low} – ${curr}${plan.entry_zone_high}` : 'Market Entry')
  const qty = plan?.suggested_quantity || plan?.position_sizing?.recommended_quantity || 10
  const maxRisk = plan?.max_capital_risk || plan?.position_sizing?.max_capital_allocated || 1500

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Target color="var(--accent-blue)" size={24} /> Autonomous AI Trade Plan Generation Engine
          </h1>
          <p>Produces mathematically rigorous trade setups with tiered targets (1.5R, 2.5R, 3.5R runner), position sizing, and invalidation triggers.</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchPlan} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Generate Plan
        </button>
      </div>

      {/* Interactive Symbol Search Bar */}
      <SymbolSearchBar
        symbol={symbol}
        onSelectSymbol={(s) => setSymbol(s)}
        apiBase={apiBase}
        placeholder="Search any stock for Autonomous AI Trade Plan..."
      />

      {loading && !plan && (
        <div className="card" style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={20} className="spin" style={{ marginRight: 10 }} />
          Generating Autonomous AI Trade Plan for {symbol}...
        </div>
      )}

      {plan && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-top"><span>Direction</span><Target size={16} color="var(--accent-blue)" /></div>
              <div className="kpi-value" style={{ color: isBuy ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                {plan.direction}
              </div>
              <div className="kpi-sub">Score: {plan.trade_score ?? plan.conviction_score ?? 80}%</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Optimal Entry Zone</span><ArrowUpRight size={16} color="var(--accent-green)" /></div>
              <div className="kpi-value" style={{ fontSize: 20 }}>
                {entryStr}
              </div>
              <div className="kpi-sub">LTP: {curr}{plan.current_price}</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Hard Stop Loss</span><ShieldAlert size={16} color="var(--accent-red)" /></div>
              <div className="kpi-value" style={{ color: 'var(--accent-red)', fontSize: 20 }}>
                {curr}{plan.stop_loss}
              </div>
              <div className="kpi-sub">R:R Ratio: 1:{plan.risk_reward_ratio || 2.5}</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Position Sizing (Risk Capped)</span><Gauge size={16} color="var(--accent-blue)" /></div>
              <div className="kpi-value" style={{ fontSize: 20 }}>
                {qty} Units
              </div>
              <div className="kpi-sub">Max Risk: {curr}{maxRisk.toLocaleString()}</div>
            </div>
          </div>

          <div className="grid-2col">
            <div className="card">
              <div className="card-header">
                <span className="card-title"><TrendingUp size={16} color="var(--accent-green)" /> Tiered Profit Realization Targets</span>
                <span className="badge badge-green">R-Multiple Scaled</span>
              </div>
              <div style={{ padding: 16 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ padding: 10, background: 'var(--bg-card-hover)', borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <b>TP1 (1.5R - 50% Exit):</b>
                      <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Lock gains & ratchet stop to Breakeven</div>
                    </div>
                    <span style={{ fontSize: 16, fontWeight: 900, color: 'var(--accent-green)' }}>
                      {curr}{plan.target_1 || plan.target_tier_1_price}
                    </span>
                  </div>

                  <div style={{ padding: 10, background: 'var(--bg-card-hover)', borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <b>TP2 (2.5R - 30% Exit):</b>
                      <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Core momentum objective</div>
                    </div>
                    <span style={{ fontSize: 16, fontWeight: 900, color: 'var(--accent-green)' }}>
                      {curr}{plan.target_2 || plan.target_tier_2_price}
                    </span>
                  </div>

                  <div style={{ padding: 10, background: 'var(--bg-card-hover)', borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <b>TP3 Runner (3.5R - 20% Exit):</b>
                      <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Trail with step-ladder profit protector</div>
                    </div>
                    <span style={{ fontSize: 16, fontWeight: 900, color: 'var(--accent-green)' }}>
                      {curr}{plan.target_3 || plan.target_tier_3_runner_price}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <span className="card-title"><ShieldCheck size={16} color="var(--accent-blue)" /> Pre-Trade Conditions & Invalidation</span>
              </div>
              <div style={{ padding: 16, fontSize: 12.5, color: 'var(--text-muted)' }}>
                <b>Entry Checklist:</b>
                <ul style={{ margin: '6px 0 14px 0', paddingLeft: 18 }}>
                  {(plan.buy_conditions || []).map((c, i) => (
                    <li key={i} style={{ marginBottom: 4 }}>{c}</li>
                  ))}
                  {(!plan.buy_conditions || plan.buy_conditions.length === 0) && (
                    <li style={{ color: 'var(--text-dim)' }}>Confirm volume expansion and price alignment above entry trigger.</li>
                  )}
                </ul>

                <div style={{ padding: 10, background: 'rgba(239, 68, 68, 0.08)', borderRadius: 6, borderLeft: '4px solid var(--accent-red)' }}>
                  <b>Invalidation Level / Conditions:</b>
                  <ul style={{ margin: '4px 0 0 0', paddingLeft: 18, fontSize: 11.5 }}>
                    {(plan.do_not_buy_conditions || []).map((c, i) => (
                      <li key={i} style={{ marginBottom: 2 }}>{c}</li>
                    ))}
                    {(!plan.do_not_buy_conditions || plan.do_not_buy_conditions.length === 0) && (
                      <li>Price breaches stop loss ({curr}{plan.stop_loss}) prior to target fill.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {onSelectTradeSymbol && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-card)', padding: '14px 20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', marginTop: 8 }}>
              <div>
                <b style={{ fontSize: 14 }}>Execute AI Trade Plan in OMS</b>
                <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                  Direction: <b style={{ color: isBuy ? 'var(--accent-green)' : 'var(--accent-red)' }}>{plan.direction}</b> | Entry: {entryStr} | Stop Loss: {curr}{plan.stop_loss} | Target 1: {curr}{plan.target_1} | Qty: {qty}
                </div>
              </div>
              <button
                className={`btn ${isBuy ? 'btn-primary' : 'btn-danger'}`}
                style={{ padding: '8px 20px', fontSize: 13, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 6 }}
                onClick={() => onSelectTradeSymbol(symbol, {
                  side: plan.direction,
                  entry: plan.entry_zone_low || plan.current_price,
                  sl: plan.stop_loss,
                  target: plan.target_1,
                  qty: qty,
                })}
              >
                <Zap size={16} /> Execute {plan.direction} with AI Plan in OMS
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export function BacktestLabTab({ apiBase, pct }) {
  const [strategy, setStrategy] = useState('Supertrend Trend Rider')
  const [symbol, setSymbol] = useState('RELIANCE')
  const [timeframe, setTimeframe] = useState('1h')
  const [days, setDays] = useState(60)
  const [capital, setCapital] = useState(100000)
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)

  const runBacktest = (e) => {
    e.preventDefault()
    setLoading(true)
    fetch(`${apiBase}/api/analytics/backtest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        strategy_name: strategy,
        symbol: symbol,
        timeframe: timeframe,
        days_lookback: Number(days),
        starting_capital: Number(capital),
        risk_per_trade_pct: 2.0,
        slippage_pct: 0.05,
        commission_per_trade: 20.0,
        stop_loss_pct: 2.5,
        take_profit_pct: 5.0,
        trailing_stop: true,
      }),
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        setRes(d)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Gauge color="var(--accent-blue)" size={24} /> Interactive Strategy Backtesting Lab
          </h1>
          <p>Replay historical candlestick feeds with slippage, statutory transaction fees, and trailing stops.</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={runBacktest} style={{ display: 'flex', gap: 14, alignItems: 'flex-end', flexWrap: 'wrap', padding: 16 }}>
          <div>
            <label style={{ fontSize: 11, fontWeight: 700, display: 'block', marginBottom: 4 }}>Strategy</label>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)} style={{ padding: '8px 12px', background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--border-subtle)', borderRadius: 6 }}>
              <option value="Supertrend Trend Rider">Supertrend Trend Rider</option>
              <option value="AI Momentum Ensemble">AI Momentum Ensemble</option>
              <option value="Bollinger Mean Reversion">Bollinger Mean Reversion</option>
              <option value="Breakout Volatility">Breakout Volatility</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: 11, fontWeight: 700, display: 'block', marginBottom: 4 }}>Symbol</label>
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)} style={{ padding: '8px 12px', background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--border-subtle)', borderRadius: 6 }}>
              <option value="RELIANCE">RELIANCE (NSE)</option>
              <option value="TCS">TCS (NSE)</option>
              <option value="INFY">INFY (NSE)</option>
              <option value="AAPL">AAPL (NASDAQ)</option>
              <option value="NVDA">NVDA (NASDAQ)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: 11, fontWeight: 700, display: 'block', marginBottom: 4 }}>Lookback (Days)</label>
            <input type="number" value={days} onChange={(e) => setDays(e.target.value)} style={{ width: 80, padding: '8px 10px' }} />
          </div>

          <div>
            <label style={{ fontSize: 11, fontWeight: 700, display: 'block', marginBottom: 4 }}>Capital (₹)</label>
            <input type="number" value={capital} onChange={(e) => setCapital(e.target.value)} style={{ width: 110, padding: '8px 10px' }} />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ padding: '8px 16px' }}>
            {loading ? 'Simulating...' : 'Run Simulation'}
          </button>
        </form>
      </div>

      {res && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-top"><span>Total Return</span><TrendingUp size={16} color="var(--accent-green)" /></div>
              <div className={`kpi-value ${res.total_return_pct >= 0 ? 'positive' : 'negative'}`}>
                {pct(res.total_return_pct)}
              </div>
              <div className="kpi-sub">Benchmark: {pct(res.benchmark_return_pct)}</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Win Rate</span><CheckCircle2 size={16} color="var(--accent-green)" /></div>
              <div className="kpi-value">{res.win_rate_pct}%</div>
              <div className="kpi-sub">{res.winning_trades} Wins / {res.losing_trades} Losses</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Profit Factor</span><Gauge size={16} color="var(--accent-blue)" /></div>
              <div className="kpi-value">{res.profit_factor}</div>
              <div className="kpi-sub">Trades: {res.total_trades}</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top"><span>Max Drawdown</span><AlertTriangle size={16} color="var(--accent-red)" /></div>
              <div className="kpi-value negative">-{res.max_drawdown_pct}%</div>
              <div className="kpi-sub">Sharpe: {res.sharpe_ratio}</div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Executed Backtest Trades ({res.trades ? res.trades.length : 0})</span>
            </div>
            <div className="table-container" style={{ maxHeight: 300, overflowY: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Side</th>
                    <th>Entry</th>
                    <th>Exit</th>
                    <th>P&L</th>
                    <th>Return %</th>
                    <th>Exit Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {(res.trades || []).map((t, idx) => (
                    <tr key={idx}>
                      <td><b>{t.id}</b></td>
                      <td><span className={`badge ${t.side === 'BUY' ? 'badge-green' : 'badge-red'}`}>{t.side}</span></td>
                      <td>{t.entry_price}</td>
                      <td>{t.exit_price}</td>
                      <td className={t.pnl >= 0 ? 'positive' : 'negative'}>₹{t.pnl.toFixed(2)}</td>
                      <td className={t.pnl_percent >= 0 ? 'positive' : 'negative'}>{pct(t.pnl_percent)}</td>
                      <td><span className="badge badge-blue" style={{ fontSize: 10 }}>{t.exit_reason}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
