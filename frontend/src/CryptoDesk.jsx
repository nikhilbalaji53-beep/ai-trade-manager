import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import {
  Coins,
  TrendingUp,
  TrendingDown,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Clock,
  ShieldCheck,
  Zap,
  BarChart3,
  Globe,
  DollarSign,
  Maximize2,
  Minimize2,
  ChevronRight,
  Sparkles,
} from 'lucide-react'

// Base API URL — resolved from Vite env vars at build time.
// Development (.env.development): http://127.0.0.1:8000
// Production  (.env.production):  https://ai-trade-manager.onrender.com
// Fallback is the production URL so a misconfigured build never silently uses localhost.
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://ai-trade-manager.onrender.com'

const moneyINR = (val) => {
  if (val === null || val === undefined || isNaN(val)) return '—'
  return `₹${Math.abs(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const moneyUSD = (val) => {
  if (val === null || val === undefined || isNaN(val)) return '—'
  return `$${Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const formatVol = (val) => {
  if (!val || isNaN(val)) return '—'
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`
  if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`
  if (val >= 1e3) return `$${(val / 1e3).toFixed(1)}K`
  return `$${Number(val).toFixed(0)}`
}

const formatCandleTime = (ts, tf) => {
  if (!ts) return '—'
  try {
    const d = new Date(ts)
    if (['1d', '1D', '1w', '1W', '1mo', '1M', '6mo', '6M'].includes(tf)) {
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
    }
    return `${d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })} ${d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })}`
  } catch {
    return String(ts)
  }
}

// Crypto Icon mapping with brand colors
const CRYPTO_COLORS = {
  BTC: '#f7931a',
  ETH: '#627eea',
  SOL: '#14f195',
  BNB: '#f3ba2f',
  XRP: '#23292f',
  DOGE: '#c2a633',
  ADA: '#0033ad',
  AVAX: '#e84142',
  LINK: '#375bd2',
  DOT: '#e6007a',
}

export function CryptoDesk({
  cryptoQuotes = [],
  priceFlashMap = {},
  onConfigureTrade,
  onSelectForChart,
}) {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC')
  const [timeframe, setTimeframe] = useState('1h')
  const [currencyMode, setCurrencyMode] = useState('DUAL') // 'DUAL' | 'USD' | 'INR'
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('ALL')
  const [candles, setCandles] = useState([])
  const [chartLoading, setChartLoading] = useState(false)
  const [hoveredCandle, setHoveredCandle] = useState(null)
  const [mousePos, setMousePos] = useState({ x: null, y: null })

  // 6-Month Scrollback & Viewport Window State
  const [scrollOffset, setScrollOffset] = useState(0) // 0 = at live right edge, >0 = scrolled back in time
  const [windowSize, setWindowSize] = useState(50) // visible candles at once
  const [isDragging, setIsDragging] = useState(false)
  const [dragStartX, setDragStartX] = useState(0)
  const [dragStartOffset, setDragStartOffset] = useState(0)

  // Reset scrollback to live whenever symbol or timeframe changes
  useEffect(() => {
    setScrollOffset(0)
  }, [selectedSymbol, timeframe])

  // Find active quote
  const activeQuote = useMemo(() => {
    return cryptoQuotes.find((q) => q.symbol === selectedSymbol) || cryptoQuotes[0] || {
      symbol: 'BTC',
      name: 'Bitcoin',
      last_price: 76898.49,
      inr_price: 6678634.05,
      change: -367.93,
      change_percent: -0.48,
      high: 77308.94,
      low: 76503.83,
      open: 77270.22,
      volume: 13030958080,
      quote_volume: 1002340000,
      bid: 76897.5,
      ask: 76899.0,
      spread: 1.5,
      price_movement: 'UP',
      is_24_7: true,
      data_status: 'REAL_TIME_24_7',
    }
  }, [cryptoQuotes, selectedSymbol])

  // Fetch live candles
  const fetchCandles = useCallback(async () => {
    setChartLoading(true)
    try {
      const limit = ['6M', '6mo', '1D', '1d'].includes(timeframe) ? 184 : ['1W', '1w', '1M', '1mo'].includes(timeframe) ? 104 : 60
      const res = await fetch(`${API_BASE}/api/v1/crypto/candles/${selectedSymbol}?interval=${timeframe}&limit=${limit}`)
      if (res.ok) {
        const data = await res.json()
        if (data.candles && data.candles.length > 0) {
          setCandles(data.candles)
        }
      }
    } catch (e) {
      console.warn('Failed to load crypto candles', e)
    } finally {
      setChartLoading(false)
    }
  }, [selectedSymbol, timeframe])

  // Fetch candles on symbol or timeframe changes & regular 10s background interval
  useEffect(() => {
    fetchCandles()
    const interval = setInterval(fetchCandles, 10000)
    return () => clearInterval(interval)
  }, [fetchCandles])

  // Filtered quotes list
  const filteredList = useMemo(() => {
    const q = search.toLowerCase().trim()
    return cryptoQuotes.filter((item) => {
      const matchSearch =
        !q ||
        item.symbol.toLowerCase().includes(q) ||
        (item.name && item.name.toLowerCase().includes(q))
      const matchCat =
        selectedCategory === 'ALL' ||
        (item.category && item.category.toLowerCase().includes(selectedCategory.toLowerCase()))
      return matchSearch && matchCat
    })
  }, [cryptoQuotes, search, selectedCategory])

  // SVG Chart Dimensions & Calculations
  const chartWidth = 920
  const chartHeight = 320
  const padding = { top: 20, right: 70, bottom: 25, left: 10 }
  const innerWidth = chartWidth - padding.left - padding.right
  const innerHeight = chartHeight - padding.top - padding.bottom

  // 6-Month Viewport Slicing & Windowing
  const effectiveWindow = Math.min(candles.length, Math.max(15, windowSize))
  const maxOffset = Math.max(0, candles.length - effectiveWindow)
  const clampedOffset = Math.min(maxOffset, Math.max(0, scrollOffset))
  const endIndex = candles.length - clampedOffset
  const startIndex = Math.max(0, endIndex - effectiveWindow)
  const visibleCandles = useMemo(() => {
    return candles.slice(startIndex, endIndex)
  }, [candles, startIndex, endIndex])
  const isScrolledBack = clampedOffset > 0

  const { minPrice, maxPrice, priceRange } = useMemo(() => {
    if (!visibleCandles || visibleCandles.length === 0) {
      return { minPrice: 0, maxPrice: 100, priceRange: 100 }
    }
    const highs = visibleCandles.map((c) => c.high)
    const lows = visibleCandles.map((c) => c.low)
    const min = Math.min(...lows)
    const max = Math.max(...highs)
    const pad = (max - min) * 0.05 || 1
    return {
      minPrice: min - pad,
      maxPrice: max + pad,
      priceRange: (max + pad) - (min - pad),
    }
  }, [visibleCandles])

  const scaleY = (p) => {
    if (priceRange === 0) return chartHeight / 2
    return padding.top + (1 - (p - minPrice) / priceRange) * innerHeight
  }

  const handleChartMouseDown = (e) => {
    if (e.button !== 0) return
    setIsDragging(true)
    setDragStartX(e.clientX)
    setDragStartOffset(clampedOffset)
  }

  const handleChartMouseMove = (e) => {
    if (!visibleCandles.length) return
    const rect = e.currentTarget.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    setMousePos({ x: mouseX, y: mouseY })

    if (isDragging) {
      const deltaX = e.clientX - dragStartX
      const pixelsPerBar = (rect.width / Math.max(1, visibleCandles.length)) || 10
      const barDelta = Math.round(deltaX / pixelsPerBar)
      const newOffset = Math.min(maxOffset, Math.max(0, dragStartOffset + barDelta))
      setScrollOffset(newOffset)
    } else {
      const svgRelX = (mouseX / rect.width) * chartWidth
      const step = innerWidth / Math.max(1, visibleCandles.length - 1)
      const idx = Math.max(0, Math.min(visibleCandles.length - 1, Math.round((svgRelX - padding.left) / step)))
      setHoveredCandle(visibleCandles[idx])
    }
  }

  const handleChartMouseUp = () => {
    setIsDragging(false)
  }

  const handleChartMouseLeave = () => {
    setIsDragging(false)
    setHoveredCandle(null)
    setMousePos({ x: null, y: null })
  }

  const handleChartWheel = (e) => {
    if (maxOffset <= 0) return
    e.preventDefault()
    const delta = Math.sign(e.deltaX || e.deltaY)
    if (delta !== 0) {
      setScrollOffset((prev) => Math.min(maxOffset, Math.max(0, prev + (delta < 0 ? 3 : -3))))
    }
  }

  const currentDisplayCandle = hoveredCandle || (visibleCandles.length > 0 ? visibleCandles[visibleCandles.length - 1] : null)
  const isUp = (activeQuote?.change || 0) >= 0
  const brandColor = CRYPTO_COLORS[selectedSymbol] || '#38bdf8'

  return (
    <div className="crypto-desk-container" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* 24/7 Live Stream Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
          padding: '12px 18px',
          background: 'linear-gradient(90deg, rgba(245, 158, 11, 0.08) 0%, rgba(16, 185, 129, 0.08) 50%, rgba(56, 189, 248, 0.08) 100%)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 15px rgba(245, 158, 11, 0.4)',
            }}
          >
            <Coins size={24} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 900, color: '#f8fafc', letterSpacing: '-0.01em' }}>
                Crypto & Bitcoin 24/7 Live Trading Desk
              </h2>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 5,
                  padding: '2px 8px',
                  borderRadius: 12,
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  fontSize: 10.5,
                  fontWeight: 800,
                  color: '#34d399',
                }}
              >
                <span className="live-tick-pulse" style={{ width: 7, height: 7, background: '#10b981' }} />
                24/7/365 CONTINUOUS FEED (1s)
              </span>
            </div>
            <p style={{ margin: '2px 0 0 0', fontSize: 11.5, color: '#94a3b8' }}>
              Real-time exchange order books • Dual USD ($) & INR (₹) rates • Zero weekend downtime
            </p>
          </div>
        </div>

        {/* Currency Display Mode & Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(51, 65, 85, 0.6)',
              borderRadius: 8,
              padding: 2,
            }}
          >
            {[
              { id: 'DUAL', label: 'Dual $ / ₹' },
              { id: 'USD', label: 'USD ($)' },
              { id: 'INR', label: 'INR (₹)' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setCurrencyMode(m.id)}
                style={{
                  padding: '4px 10px',
                  fontSize: 11,
                  fontWeight: 700,
                  border: 'none',
                  borderRadius: 6,
                  cursor: 'pointer',
                  background: currencyMode === m.id ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                  color: currencyMode === m.id ? '#38bdf8' : '#94a3b8',
                  transition: 'all 0.2s ease',
                }}
              >
                {m.label}
              </button>
            ))}
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 12px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: 8,
              fontSize: 11,
              fontWeight: 700,
              color: '#38bdf8',
            }}
          >
            <Clock size={13} />
            <span>Tick Frequency: 1.0s</span>
          </div>
        </div>
      </div>

      {/* Top Hero Cards: Top 4 Crypto Giants (BTC, ETH, SOL, BNB) */}
      <div className="grid-4col" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
        {['BTC', 'ETH', 'SOL', 'BNB'].map((sym) => {
          const q = cryptoQuotes.find((item) => item.symbol === sym) || {}
          const isSelected = selectedSymbol === sym
          const p = q.last_price || 0
          const chgPct = q.change_percent || 0
          const pos = chgPct >= 0
          const flash = priceFlashMap[sym]
          const color = CRYPTO_COLORS[sym] || '#f59e0b'

          return (
            <div
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              style={{
                background: isSelected ? 'rgba(30, 41, 59, 0.95)' : 'rgba(15, 23, 42, 0.75)',
                border: isSelected ? `2px solid ${color}` : '1px solid rgba(51, 65, 85, 0.6)',
                borderRadius: 12,
                padding: '14px 16px',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: isSelected ? `0 0 20px ${color}25` : 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background: `${color}20`,
                      border: `1px solid ${color}50`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 900,
                      fontSize: 12,
                      color: color,
                    }}
                  >
                    {sym[0]}
                  </div>
                  <div>
                    <span style={{ fontWeight: 800, fontSize: 15, color: '#f8fafc' }}>{sym}</span>
                    <span style={{ fontSize: 10.5, color: '#94a3b8', marginLeft: 5 }}>/ USDT</span>
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 10.5,
                    fontWeight: 800,
                    padding: '2px 7px',
                    borderRadius: 6,
                    background: pos ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    color: pos ? '#10b981' : '#ef4444',
                  }}
                >
                  {pos ? '+' : ''}{chgPct.toFixed(2)}%
                </span>
              </div>

              {/* Live Price with Flash Animation */}
              <div
                className={flash?.dir === 'UP' ? 'price-flash-up' : flash?.dir === 'DOWN' ? 'price-flash-down' : ''}
                style={{
                  margin: '10px 0 4px 0',
                  borderRadius: 6,
                  padding: '2px 4px',
                  display: 'flex',
                  alignItems: 'baseline',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontSize: 22, fontWeight: 900, fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>
                  {moneyUSD(p)}
                </span>
                {q.price_movement && (
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 800,
                      color: q.price_movement === 'UP' ? '#10b981' : q.price_movement === 'DOWN' ? '#ef4444' : '#94a3b8',
                    }}
                  >
                    {q.price_movement === 'UP' ? '↑ 1s' : q.price_movement === 'DOWN' ? '↓ 1s' : '●'}
                  </span>
                )}
              </div>

              {/* INR Equivalent */}
              <div style={{ fontSize: 11.5, color: '#94a3b8', fontWeight: 600, display: 'flex', justifyContent: 'space-between' }}>
                <span>₹ Equivalent:</span>
                <span style={{ color: '#e2e8f0', fontFamily: 'var(--font-mono)' }}>{moneyINR(q.inr_price)}</span>
              </div>

              {/* Quick stats bottom */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginTop: 10,
                  paddingTop: 8,
                  borderTop: '1px solid rgba(51, 65, 85, 0.5)',
                  fontSize: 10,
                  color: '#64748b',
                }}
              >
                <span>24h Vol: {formatVol(q.volume || q.quote_volume)}</span>
                <span style={{ color: '#10b981' }}>● 24/7 LIVE</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Main Interactive Chart & Order Book View */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(300px, 1fr)', gap: 16 }}>
        {/* Left: Interactive 24/7 Candlestick Chart */}
        <div className="card" style={{ background: 'rgba(15, 23, 42, 0.85)', borderRadius: 12, padding: 16 }}>
          {/* Chart Header Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: `${brandColor}25`,
                  border: `1px solid ${brandColor}60`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 900,
                  color: brandColor,
                }}
              >
                {selectedSymbol[0]}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 18, fontWeight: 900, color: '#f8fafc' }}>
                    {activeQuote.name} ({selectedSymbol}/USDT)
                  </span>
                  <span className="badge badge-green" style={{ fontSize: 9.5 }}>
                    ● 24/7 REAL-TIME
                  </span>
                  {(activeQuote?.bias === 'BULLISH' || activeQuote?.trend === 'BULLISH' || activeQuote?.change_percent > 0.05) && (
                    <span className="badge badge-green" style={{ fontSize: 9.5, fontWeight: 700 }}>
                      ▲ BULLISH
                    </span>
                  )}
                  {(activeQuote?.bias === 'BEARISH' || activeQuote?.trend === 'BEARISH' || activeQuote?.change_percent < -0.05) && (
                    <span className="badge badge-red" style={{ fontSize: 9.5, fontWeight: 700 }}>
                      ▼ BEARISH
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2 }}>
                  <span style={{ fontSize: 17, fontWeight: 800, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                    {currencyMode === 'INR' ? moneyINR(activeQuote.inr_price) : moneyUSD(activeQuote.last_price)}
                  </span>
                  {currencyMode === 'DUAL' && (
                    <span style={{ fontSize: 12, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                      ({moneyINR(activeQuote.inr_price)})
                    </span>
                  )}
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      color: isUp ? '#10b981' : '#ef4444',
                    }}
                  >
                    {isUp ? '+' : ''}{activeQuote.change_percent?.toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Timeframe Selector */}
            <div style={{ display: 'flex', gap: 4, background: 'rgba(30, 41, 59, 0.8)', padding: 3, borderRadius: 8, flexWrap: 'wrap' }}>
              {[
                { id: '1m', label: '1m' },
                { id: '5m', label: '5m' },
                { id: '15m', label: '15m' },
                { id: '1h', label: '1h' },
                { id: '4h', label: '4h' },
                { id: '1D', label: '1 Day' },
                { id: '1W', label: '1 Week' },
                { id: '1M', label: '1 Month' },
                { id: '6M', label: '6 Months' },
              ].map((tf) => (
                <button
                  key={tf.id}
                  onClick={() => setTimeframe(tf.id)}
                  style={{
                    padding: '4px 8px',
                    fontSize: 10.5,
                    fontWeight: 700,
                    border: 'none',
                    borderRadius: 6,
                    cursor: 'pointer',
                    background: timeframe === tf.id ? brandColor : 'transparent',
                    color: timeframe === tf.id ? '#05090f' : '#94a3b8',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {tf.label}
                </button>
              ))}
            </div>
          </div>

          {/* Candle HUD (Hovered or Last Bar) */}
          {currentDisplayCandle && (
            <div
              style={{
                display: 'flex',
                gap: 16,
                padding: '6px 12px',
                background: 'rgba(30, 41, 59, 0.5)',
                borderRadius: 6,
                fontSize: 11,
                color: '#94a3b8',
                marginBottom: 10,
                fontFamily: 'var(--font-mono)',
                flexWrap: 'wrap',
              }}
            >
              <span>BAR: <b style={{ color: '#f8fafc' }}>{formatCandleTime(currentDisplayCandle.timestamp, timeframe)}</b></span>
              <span>O: <b style={{ color: '#f8fafc' }}>{moneyUSD(currentDisplayCandle.open)}</b></span>
              <span>H: <b style={{ color: '#10b981' }}>{moneyUSD(currentDisplayCandle.high)}</b></span>
              <span>L: <b style={{ color: '#ef4444' }}>{moneyUSD(currentDisplayCandle.low)}</b></span>
              <span>C: <b style={{ color: '#38bdf8' }}>{moneyUSD(currentDisplayCandle.close)}</b></span>
              <span>Vol: <b style={{ color: '#f8fafc' }}>{Number(currentDisplayCandle.volume || 0).toFixed(2)}</b></span>
            </div>
          )}

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
                  background: brandColor,
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

          {/* SVG Candlestick Canvas */}
          <div style={{ position: 'relative', width: '100%', height: chartHeight, overflow: 'hidden' }}>
            {chartLoading && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'rgba(15, 23, 42, 0.6)',
                  zIndex: 5,
                  fontSize: 12,
                  color: '#38bdf8',
                  fontWeight: 600,
                }}
              >
                <RefreshCw size={16} className="spin" style={{ marginRight: 8 }} /> Loading 24/7 Binance Klines...
              </div>
            )}

            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              style={{ width: '100%', height: '100%', cursor: isDragging ? 'grabbing' : 'crosshair', userSelect: 'none' }}
              onMouseDown={handleChartMouseDown}
              onMouseMove={handleChartMouseMove}
              onMouseUp={handleChartMouseUp}
              onMouseLeave={handleChartMouseLeave}
              onWheel={handleChartWheel}
            >
              {/* Horizontal Price Gridlines & Labels */}
              {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                const price = minPrice + (1 - ratio) * priceRange
                const y = padding.top + ratio * innerHeight
                return (
                  <g key={ratio}>
                    <line
                      x1={padding.left}
                      y1={y}
                      x2={chartWidth - padding.right}
                      y2={y}
                      stroke="rgba(51, 65, 85, 0.4)"
                      strokeDasharray="3 3"
                    />
                    <text
                      x={chartWidth - padding.right + 8}
                      y={y + 4}
                      fill="#64748b"
                      fontSize="10"
                      fontFamily="var(--font-mono)"
                    >
                      ${price >= 100 ? price.toFixed(1) : price.toFixed(3)}
                    </text>
                  </g>
                )
              })}

              {/* Candles */}
              {visibleCandles.map((candle, idx) => {
                const step = innerWidth / Math.max(1, visibleCandles.length - 1)
                const x = padding.left + idx * step
                const openY = scaleY(candle.open)
                const closeY = scaleY(candle.close)
                const highY = scaleY(candle.high)
                const lowY = scaleY(candle.low)
                const isGreen = candle.close >= candle.open
                const color = isGreen ? '#10b981' : '#ef4444'
                const candleWidth = Math.max(3, Math.min(16, step * 0.7))

                return (
                  <g key={idx}>
                    {/* Wick */}
                    <line
                      x1={x}
                      y1={highY}
                      x2={x}
                      y2={lowY}
                      stroke={color}
                      strokeWidth="1.2"
                    />
                    {/* Body */}
                    <rect
                      x={x - candleWidth / 2}
                      y={Math.min(openY, closeY)}
                      width={candleWidth}
                      height={Math.max(2, Math.abs(closeY - openY))}
                      fill={color}
                      rx={1}
                    />
                  </g>
                )
              })}

              {/* X-Axis Date / Time Markers */}
              {visibleCandles.length > 0 && (() => {
                const stepCount = Math.max(1, Math.floor(visibleCandles.length / 5))
                const indices = []
                for (let i = 0; i < visibleCandles.length; i += stepCount) {
                  indices.push(i)
                }
                if (indices[indices.length - 1] !== visibleCandles.length - 1) {
                  indices.push(visibleCandles.length - 1)
                }
                return indices.map((cIdx) => {
                  const c = visibleCandles[cIdx]
                  if (!c) return null
                  const step = innerWidth / Math.max(1, visibleCandles.length - 1)
                  const x = padding.left + cIdx * step
                  return (
                    <g key={`crypto-timeline-${cIdx}`}>
                      <line x1={x} y1={chartHeight - padding.bottom} x2={x} y2={chartHeight - padding.bottom + 5} stroke="rgba(255,255,255,0.2)" />
                      <text
                        x={x}
                        y={chartHeight - 4}
                        textAnchor={cIdx === 0 ? 'start' : cIdx === visibleCandles.length - 1 ? 'end' : 'middle'}
                        fill="#64748b"
                        fontSize="9"
                        fontFamily="var(--font-mono)"
                      >
                        {formatCandleTime(c.timestamp, timeframe)}
                      </text>
                    </g>
                  )
                })
              })()}

              {/* Crosshair when hovering */}
              {mousePos.x !== null && (
                <g pointerEvents="none">
                  <line
                    x1={mousePos.x}
                    y1={padding.top}
                    x2={mousePos.x}
                    y2={chartHeight - padding.bottom}
                    stroke="rgba(248, 250, 252, 0.4)"
                    strokeDasharray="2 2"
                  />
                  <line
                    x1={padding.left}
                    y1={mousePos.y}
                    x2={chartWidth - padding.right}
                    y2={mousePos.y}
                    stroke="rgba(248, 250, 252, 0.4)"
                    strokeDasharray="2 2"
                  />
                </g>
              )}
            </svg>
          </div>

          {/* 6-Month Timeline Scrubber & Scrollback Ribbon */}
          <div
            style={{
              marginTop: 10,
              padding: '8px 12px',
              background: 'rgba(30, 41, 59, 0.6)',
              borderRadius: 8,
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
              {/* Quick Jump Buttons */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 10.5, fontWeight: 700, color: '#94a3b8' }}>
                  Scrollback:
                </span>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '2px 8px', fontSize: 10.5, fontWeight: 700 }}
                  onClick={() => setScrollOffset(maxOffset)}
                  title="Jump to 6 Months Ago"
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
                    background: isScrolledBack ? brandColor : 'rgba(56, 189, 248, 0.15)',
                    color: isScrolledBack ? '#05090f' : brandColor,
                    borderColor: brandColor,
                  }}
                  onClick={() => setScrollOffset(0)}
                  title="Jump to Live Present"
                >
                  ▶▶ LIVE
                </button>
              </div>

              {/* Scrubber Slider */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 240, maxWidth: 460 }}>
                <span style={{ fontSize: 10, color: '#64748b', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                  {candles[0] ? formatCandleTime(candles[0].timestamp, timeframe) : '6M Ago'}
                </span>
                <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
                  <input
                    type="range"
                    min={0}
                    max={maxOffset}
                    value={maxOffset - clampedOffset}
                    onChange={(e) => setScrollOffset(maxOffset - Number(e.target.value))}
                    style={{
                      width: '100%',
                      accentColor: isScrolledBack ? '#fbbf24' : brandColor,
                      cursor: 'pointer',
                      height: 5,
                    }}
                    title={`Timeline Scrubber: Viewing ${visibleCandles.length} bars`}
                  />
                </div>
                <span style={{ fontSize: 10, color: '#64748b', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                  {candles[candles.length - 1] ? formatCandleTime(candles[candles.length - 1].timestamp, timeframe) : 'Live'}
                </span>
              </div>

              {/* Zoom Controls */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 10.5, color: '#94a3b8' }}>Zoom:</span>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '2px 7px', fontSize: 11, fontWeight: 800 }}
                  onClick={() => setWindowSize((w) => Math.min(candles.length, w + 15))}
                  title="Zoom Out"
                >
                  −
                </button>
                <span style={{ fontSize: 10.5, fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
                  {visibleCandles.length}b
                </span>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '2px 7px', fontSize: 11, fontWeight: 800 }}
                  onClick={() => setWindowSize((w) => Math.max(15, w - 10))}
                  title="Zoom In"
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
                  title="View All Historical Bars"
                >
                  Fit 6M
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Real-Time Order Book Depth & Asset Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Order Book Depth Card */}
          <div className="card" style={{ background: 'rgba(15, 23, 42, 0.85)', borderRadius: 12, padding: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontWeight: 800, fontSize: 13, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 6 }}>
                <Zap size={14} color="#f59e0b" /> 24/7 Exchange Spread
              </span>
              <span className="badge badge-blue" style={{ fontSize: 9.5 }}>
                BINANCE ORDERBOOK
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
              <div style={{ padding: '10px 12px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 8 }}>
                <div style={{ fontSize: 10.5, color: '#10b981', fontWeight: 700 }}>BEST BID</div>
                <div style={{ fontSize: 16, fontWeight: 900, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {moneyUSD(activeQuote.bid || activeQuote.last_price * 0.9999)}
                </div>
              </div>

              <div style={{ padding: '10px 12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 8 }}>
                <div style={{ fontSize: 10.5, color: '#ef4444', fontWeight: 700 }}>BEST ASK</div>
                <div style={{ fontSize: 16, fontWeight: 900, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {moneyUSD(activeQuote.ask || activeQuote.last_price * 1.0001)}
                </div>
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 11.5 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>Spread:</span>
                <span style={{ color: '#f8fafc', fontWeight: 700 }}>
                  ${(activeQuote.spread || 0.01).toFixed(4)} ({((((activeQuote.spread || 0.01) / (activeQuote.last_price || 1)) * 100)).toFixed(3)}%)
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>24h High:</span>
                <span style={{ color: '#10b981', fontWeight: 700 }}>{moneyUSD(activeQuote.high)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>24h Low:</span>
                <span style={{ color: '#ef4444', fontWeight: 700 }}>{moneyUSD(activeQuote.low)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>24h Open:</span>
                <span style={{ color: '#cbd5e1' }}>{moneyUSD(activeQuote.open)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>USD to INR Reference:</span>
                <span style={{ color: '#38bdf8', fontWeight: 700 }}>1 USD = ₹86.85</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>Category:</span>
                <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{activeQuote.category || 'Layer 1'}</span>
              </div>
            </div>

            {/* Quick Trade Action Buttons */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 16 }}>
              <button
                className="btn btn-primary"
                style={{ background: '#10b981', borderColor: '#10b981', fontSize: 12, fontWeight: 800 }}
                onClick={() => onConfigureTrade && onConfigureTrade({ symbol: activeQuote.symbol, side: 'BUY', price: activeQuote.last_price })}
              >
                BUY {selectedSymbol}
              </button>
              <button
                className="btn btn-danger"
                style={{ background: '#ef4444', borderColor: '#ef4444', fontSize: 12, fontWeight: 800 }}
                onClick={() => onConfigureTrade && onConfigureTrade({ symbol: activeQuote.symbol, side: 'SELL', price: activeQuote.last_price })}
              >
                SHORT {selectedSymbol}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Complete 24/7 Cryptocurrency Catalog Table */}
      <div className="card" style={{ background: 'rgba(15, 23, 42, 0.85)', borderRadius: 12, padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="card-title" style={{ fontSize: 15, fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Globe size={16} color="#38bdf8" /> All 24/7 Crypto Pairs ({filteredList.length})
            </span>
            <div style={{ display: 'flex', gap: 4 }}>
              {['ALL', 'Layer 1', 'DeFi', 'Ecosystem', 'Meme'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    padding: '3px 8px',
                    fontSize: 11,
                    fontWeight: 700,
                    border: 'none',
                    borderRadius: 6,
                    cursor: 'pointer',
                    background: selectedCategory === cat ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                    color: selectedCategory === cat ? '#38bdf8' : '#94a3b8',
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div style={{ width: 260, position: 'relative' }}>
            <input
              type="text"
              placeholder="Search Bitcoin, Ethereum, Solana..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 10px 6px 30px',
                fontSize: 12,
                borderRadius: 8,
                background: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid rgba(51, 65, 85, 0.6)',
                color: '#f8fafc',
              }}
            />
            <Search size={14} color="#94a3b8" style={{ position: 'absolute', left: 9, top: 9 }} />
          </div>
        </div>

        <div className="table-container">
          <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.6)', color: '#94a3b8', fontSize: 11.5 }}>
                <th style={{ padding: '10px 12px' }}>Asset</th>
                <th style={{ padding: '10px 12px' }}>Category</th>
                <th style={{ padding: '10px 12px' }}>Price (USD $)</th>
                <th style={{ padding: '10px 12px' }}>Price (INR ₹)</th>
                <th style={{ padding: '10px 12px' }}>24h Change</th>
                <th style={{ padding: '10px 12px' }}>24h High / Low</th>
                <th style={{ padding: '10px 12px' }}>24h Volume</th>
                <th style={{ padding: '10px 12px' }}>Spread</th>
                <th style={{ padding: '10px 12px' }}>Market Status</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredList.map((item) => {
                const flash = priceFlashMap[item.symbol]
                const isSelected = selectedSymbol === item.symbol
                const isUp = (item.change || 0) >= 0
                const color = CRYPTO_COLORS[item.symbol] || '#94a3b8'

                return (
                  <tr
                    key={item.symbol}
                    style={{
                      borderBottom: '1px solid rgba(51, 65, 85, 0.3)',
                      background: isSelected ? 'rgba(56, 189, 248, 0.08)' : 'transparent',
                      cursor: 'pointer',
                      transition: 'background 0.15s ease',
                    }}
                    onClick={() => setSelectedSymbol(item.symbol)}
                  >
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div
                          style={{
                            width: 24,
                            height: 24,
                            borderRadius: '50%',
                            background: `${color}25`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 800,
                            fontSize: 10.5,
                            color: color,
                          }}
                        >
                          {item.symbol[0]}
                        </div>
                        <div>
                          <b style={{ color: '#f8fafc' }}>{item.symbol}</b>
                          <div style={{ fontSize: 10.5, color: '#94a3b8' }}>{item.name}</div>
                        </div>
                      </div>
                    </td>

                    <td style={{ padding: '10px 12px' }}>
                      <span className="badge badge-blue" style={{ fontSize: 10 }}>{item.category || 'Crypto'}</span>
                    </td>

                    <td style={{ padding: '10px 12px' }}>
                      <div
                        className={flash?.dir === 'UP' ? 'price-flash-up' : flash?.dir === 'DOWN' ? 'price-flash-down' : ''}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 6px', borderRadius: 4 }}
                      >
                        <span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>
                          {moneyUSD(item.last_price)}
                        </span>
                        {item.price_movement === 'UP' && <span style={{ color: '#10b981', fontSize: 10 }}>↑</span>}
                        {item.price_movement === 'DOWN' && <span style={{ color: '#ef4444', fontSize: 10 }}>↓</span>}
                      </div>
                    </td>

                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
                      {moneyINR(item.inr_price)}
                    </td>

                    <td style={{ padding: '10px 12px', fontWeight: 700, color: isUp ? '#10b981' : '#ef4444' }}>
                      {isUp ? '+' : ''}{item.change_percent?.toFixed(2)}%
                    </td>

                    <td style={{ padding: '10px 12px', fontSize: 11, color: '#94a3b8' }}>
                      <span style={{ color: '#10b981' }}>{moneyUSD(item.high)}</span> / <span style={{ color: '#ef4444' }}>{moneyUSD(item.low)}</span>
                    </td>

                    <td style={{ padding: '10px 12px', fontSize: 11, color: '#cbd5e1', fontFamily: 'var(--font-mono)' }}>
                      {formatVol(item.volume || item.quote_volume)}
                    </td>

                    <td style={{ padding: '10px 12px', fontSize: 11, color: '#94a3b8' }}>
                      ${(item.spread || 0.01).toFixed(2)}
                    </td>

                    <td style={{ padding: '10px 12px' }}>
                      <span className="badge badge-green" style={{ fontSize: 9.5 }}>
                        ● 24/7 LIVE (1s)
                      </span>
                    </td>

                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: 6 }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '3px 8px', fontSize: 10.5 }}
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedSymbol(item.symbol)
                          }}
                        >
                          Chart
                        </button>
                        <button
                          className="btn btn-primary"
                          style={{ padding: '3px 8px', fontSize: 10.5, background: '#10b981', borderColor: '#10b981' }}
                          onClick={(e) => {
                            e.stopPropagation()
                            onConfigureTrade && onConfigureTrade({ symbol: item.symbol, side: 'BUY', price: item.last_price })
                          }}
                        >
                          Trade
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
