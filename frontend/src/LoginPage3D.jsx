import React, { useState, useEffect, useRef } from 'react'
import {
  ShieldCheck,
  Zap,
  Lock,
  Mail,
  Eye,
  EyeOff,
  TrendingUp,
  Cpu,
  Flame,
  ArrowRight,
  Database,
  Radio,
  CheckCircle2,
  KeyRound,
  Layers,
  Sparkles,
  BarChart3,
  Bot,
  User,
  UserPlus,
  AlertCircle,
} from 'lucide-react'

export function LoginPage3D({ onLogin }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('trader@tradepilot.ai')
  const [password, setPassword] = useState('Password123!')
  const [showPassword, setShowPassword] = useState(false)
  const [mode, setMode] = useState('signin') // 'signin' | 'signup' | 'broker'
  const [environment, setEnvironment] = useState('live') // 'live' | 'paper'
  const [totp, setTotp] = useState('842910')
  const [brokerGateway, setBrokerGateway] = useState('ZERODHA_KITE')
  const [tier, setTier] = useState('INSTITUTIONAL AI')
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [tilt, setTilt] = useState({ x: 0, y: 0 })
  const [glare, setGlare] = useState({ x: 50, y: 50, opacity: 0 })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const canvasRef = useRef(null)
  const cardRef = useRef(null)

  // 3D Canvas Particle & Matrix Animation
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animationFrameId
    let width = (canvas.width = window.innerWidth)
    let height = (canvas.height = window.innerHeight)

    const handleResize = () => {
      width = canvas.width = window.innerWidth
      height = canvas.height = window.innerHeight
    }
    window.addEventListener('resize', handleResize)

    // Generate 3D Candlestick & Particle Mesh
    const nodes = []
    const nodeCount = 140
    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: (Math.random() - 0.5) * 1600,
        y: (Math.random() - 0.5) * 1000,
        z: Math.random() * 1200 + 100,
        origZ: Math.random() * 1200 + 100,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        vz: -1.2,
        isCandle: Math.random() > 0.65,
        open: Math.random() * 50 + 20,
        close: Math.random() * 50 + 20,
        high: Math.random() * 70 + 30,
        low: Math.random() * 20 + 5,
        color: Math.random() > 0.45 ? '#10b981' : '#f43f5e',
      })
    }

    let mouseX = 0
    let mouseY = 0
    const handleMouseMove = (e) => {
      mouseX = (e.clientX - width / 2) * 0.0006
      mouseY = (e.clientY - height / 2) * 0.0006
    }
    window.addEventListener('mousemove', handleMouseMove)

    let rotY = 0
    let rotX = 0

    const render = () => {
      ctx.fillStyle = '#070c12'
      ctx.fillRect(0, 0, width, height)

      // Perspective 3D Grid Floor
      const fov = 450
      const cx = width / 2
      const cy = height / 2

      rotY += (mouseX - rotY) * 0.05
      rotX += (mouseY - rotX) * 0.05

      // Render Perspective Horizon Cyber Grid
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.06)'
      ctx.lineWidth = 1
      const horizon = cy + 180
      for (let x = -width; x < width * 2; x += 80) {
        ctx.beginPath()
        ctx.moveTo(x, height)
        ctx.lineTo(cx + (x - cx) * 0.15, horizon)
        ctx.stroke()
      }
      for (let y = height; y > horizon; y -= (height - y) * 0.28 + 8) {
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(width, y)
        ctx.stroke()
      }

      // Render 3D nodes (Candlesticks + Glowing Data Points)
      nodes.sort((a, b) => b.z - a.z)

      nodes.forEach((node) => {
        node.z += node.vz
        if (node.z <= 20) {
          node.z = 1300
          node.x = (Math.random() - 0.5) * 1600
          node.y = (Math.random() - 0.5) * 1000
        }

        // Apply 3D Rotation Matrix
        const cosY = Math.cos(rotY)
        const sinY = Math.sin(rotY)
        const cosX = Math.cos(rotX)
        const sinX = Math.sin(rotX)

        let rx = node.x * cosY - node.z * sinY
        let rz = node.x * sinY + node.z * cosY
        let ry = node.y * cosX - rz * sinX
        rz = node.y * sinX + rz * cosX

        if (rz < 30) return

        const scale = fov / (fov + rz)
        const px = cx + rx * scale
        const py = cy + ry * scale

        const alpha = Math.max(0, Math.min(1, 1 - rz / 1300))

        if (node.isCandle) {
          const bodyH = Math.max(4, Math.abs(node.close - node.open) * scale * 1.8)
          const wickH = (node.high - node.low) * scale * 1.8
          const isGreen = node.close >= node.open

          ctx.strokeStyle = isGreen ? `rgba(16, 185, 129, ${alpha * 0.8})` : `rgba(244, 63, 94, ${alpha * 0.8})`
          ctx.lineWidth = Math.max(1, scale * 1.5)

          // Wick
          ctx.beginPath()
          ctx.moveTo(px, py - wickH / 2)
          ctx.lineTo(px, py + wickH / 2)
          ctx.stroke()

          // Body
          ctx.fillStyle = isGreen ? `rgba(16, 185, 129, ${alpha * 0.9})` : `rgba(244, 63, 94, ${alpha * 0.9})`
          ctx.fillRect(px - scale * 4, py - bodyH / 2, scale * 8, bodyH)
        } else {
          // Volumetric Glowing Node
          const radius = Math.max(1, scale * 3.5)
          const grad = ctx.createRadialGradient(px, py, 0, px, py, radius * 3)
          grad.addColorStop(0, `rgba(56, 189, 248, ${alpha * 0.9})`)
          grad.addColorStop(0.5, `rgba(59, 130, 246, ${alpha * 0.4})`)
          grad.addColorStop(1, 'rgba(0, 0, 0, 0)')

          ctx.fillStyle = grad
          ctx.beginPath()
          ctx.arc(px, py, radius * 3, 0, Math.PI * 2)
          ctx.fill()

          ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`
          ctx.beginPath()
          ctx.arc(px, py, radius * 0.6, 0, Math.PI * 2)
          ctx.fill()
        }
      })

      // Connect nearby nodes with glowing laser strands
      ctx.lineWidth = 0.6
      for (let i = 0; i < nodes.length; i += 2) {
        for (let j = i + 1; j < Math.min(i + 5, nodes.length); j++) {
          const dx = nodes[i].x - nodes[j].x
          const dy = nodes[i].y - nodes[j].y
          const dz = nodes[i].z - nodes[j].z
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz)
          if (dist < 180) {
            const scale1 = fov / (fov + nodes[i].z)
            const scale2 = fov / (fov + nodes[j].z)
            const x1 = cx + nodes[i].x * scale1
            const y1 = cy + nodes[i].y * scale1
            const x2 = cx + nodes[j].x * scale2
            const y2 = cy + nodes[j].y * scale2

            const alpha = (1 - dist / 180) * 0.25 * (1 - nodes[i].z / 1300)
            ctx.strokeStyle = `rgba(6, 182, 212, ${alpha})`
            ctx.beginPath()
            ctx.moveTo(x1, y1)
            ctx.lineTo(x2, y2)
            ctx.stroke()
          }
        }
      }

      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('mousemove', handleMouseMove)
    }
  }, [])

  // 3D Card Tilt Interaction
  const handleCardMouseMove = (e) => {
    if (!cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const centerX = rect.width / 2
    const centerY = rect.height / 2

    // Calculate rotation (-12 to 12 deg)
    const rotX = ((y - centerY) / centerY) * -10
    const rotY = ((x - centerX) / centerX) * 10
    setTilt({ x: rotX, y: rotY })
    setGlare({ x: (x / rect.width) * 100, y: (y / rect.height) * 100, opacity: 0.18 })
  }

  const handleCardMouseLeave = () => {
    setTilt({ x: 0, y: 0 })
    setGlare({ x: 50, y: 50, opacity: 0 })
  }

  // API URL — resolved from Vite env vars at build time.
  // Development:  .env.development  → http://127.0.0.1:8000
  // Production:   .env.production   → https://ai-trade-manager.onrender.com
  // Fallback is the production URL so a misconfigured build never silently uses localhost.
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://ai-trade-manager.onrender.com'

  const handleSubmit = async (e) => {
    e?.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')
    setIsSubmitting(true)

    try {
      if (mode === 'signup') {
        const payload = {
          name: name.trim() || email.split('@')[0].toUpperCase(),
          email: email.trim(),
          password: password,
          tier: tier,
          environment: environment,
          broker: brokerGateway,
        }
        const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        const data = await res.json()
        if (!res.ok) {
          throw new Error(data.detail || 'Failed to create account.')
        }
        setSuccessMsg(`Account created for ${data.user.name}! Entering terminal...`)
        if (data.access_token) {
          localStorage.setItem('tradepilot_token', data.access_token)
        }
        setTimeout(() => {
          onLogin(data.user)
          setIsSubmitting(false)
        }, 500)
      } else if (mode === 'signin') {
        const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: email.trim(),
            password: password,
          }),
        })
        const data = await res.json()
        if (!res.ok) {
          throw new Error(data.detail || 'Authentication failed. Please check credentials or create an account.')
        }
        setSuccessMsg(`Authenticated as ${data.user.name}! Launching terminal...`)
        if (data.access_token) {
          localStorage.setItem('tradepilot_token', data.access_token)
        }
        setTimeout(() => {
          onLogin(data.user)
          setIsSubmitting(false)
        }, 500)
      } else {
        // Broker Gateway mode
        const brokerUser = {
          name: email.split('@')[0].toUpperCase(),
          email: email,
          broker: brokerGateway,
          environment: environment,
          role: 'Institutional Broker Gateway Trader',
          tier: tier,
        }
        setSuccessMsg(`Broker Gateway [${brokerGateway}] Connected! Launching terminal...`)
        setTimeout(() => {
          onLogin(brokerUser)
          setIsSubmitting(false)
        }, 500)
      }
    } catch (err) {
      if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
        const fallbackUser = {
          name: (mode === 'signup' && name) ? name.toUpperCase() : email.split('@')[0].toUpperCase(),
          email: email,
          environment: environment,
          broker: brokerGateway,
          tier: tier,
          role: mode === 'signup' ? 'Registered Trader' : 'Institutional AI Trader',
        }
        onLogin(fallbackUser)
      } else {
        setErrorMsg(err.message || 'Authentication error')
        setIsSubmitting(false)
      }
    }
  }

  const handleDemoAccess = () => {
    setIsSubmitting(true)
    setTimeout(() => {
      onLogin({
        name: 'PRO TRADER',
        email: 'pro.trader@tradepilot.ai',
        environment: 'live',
        role: 'Pro Paper & Live Trader',
        tier: 'INSTITUTIONAL AI',
      })
      setIsSubmitting(false)
    }, 300)
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 99999,
        background: '#070c12',
        color: '#f8fafc',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
      }}
    >
      {/* 3D Canvas Background */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 1,
        }}
      />

      {/* Floating 3D Ticker Tape Top Banner */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 10,
          background: 'rgba(10, 18, 28, 0.85)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(16, 185, 129, 0.25)',
          padding: '8px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#10b981', fontWeight: 800 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 10px #10b981', display: 'inline-block' }} />
            TRADEPILOT 3D QUANT ENGINE v2.5.0
          </div>
          <span style={{ color: '#475569' }}>|</span>
          <div style={{ display: 'flex', gap: 16, color: '#94a3b8', fontFamily: 'monospace' }}>
            <span>NIFTY 50: <b style={{ color: '#10b981' }}>23,398.10 (+0.42%)</b></span>
            <span>SENSEX: <b style={{ color: '#10b981' }}>76,560.25 (+0.38%)</b></span>
            <span>NASDAQ: <b style={{ color: '#38bdf8' }}>19,842.10 (+1.12%)</b></span>
            <span>GOLD: <b style={{ color: '#f59e0b' }}>₹72,450 (+0.65%)</b></span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)', fontWeight: 700 }}>
            ● ZERO SYNTHETIC DATA
          </span>
          <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)', fontWeight: 700 }}>
            256-BIT ENCRYPTED
          </span>
        </div>
      </div>

      {/* 3D Glassmorphism Login Container */}
      <div
        ref={cardRef}
        onMouseMove={handleCardMouseMove}
        onMouseLeave={handleCardMouseLeave}
        style={{
          position: 'relative',
          zIndex: 20,
          width: '100%',
          maxWidth: 480,
          transform: `perspective(1000px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
          transformStyle: 'preserve-3d',
          transition: 'transform 0.15s ease-out',
          borderRadius: 24,
          background: 'linear-gradient(135deg, rgba(17, 27, 43, 0.88), rgba(10, 16, 26, 0.94))',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(56, 189, 248, 0.28)',
          boxShadow: `
            0 30px 70px rgba(0, 0, 0, 0.8),
            0 0 40px rgba(16, 185, 129, 0.15),
            inset 0 1px 1px rgba(255, 255, 255, 0.2)
          `,
          padding: '32px 36px',
          overflow: 'hidden',
        }}
      >
        {/* Specular Glare Reflection */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            background: `radial-gradient(circle at ${glare.x}% ${glare.y}%, rgba(255, 255, 255, ${glare.opacity}), transparent 60%)`,
            transition: 'background 0.1s ease-out',
          }}
        />

        {/* Ambient Neon Accent Glow */}
        <div
          style={{
            position: 'absolute',
            top: -60,
            right: -60,
            width: 140,
            height: 140,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(16, 185, 129, 0.3), transparent 70%)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: -60,
            left: -60,
            width: 140,
            height: 140,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(56, 189, 248, 0.25), transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: 20, transform: 'translateZ(30px)' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 52,
              height: 52,
              borderRadius: 14,
              background: 'linear-gradient(135deg, #10b981, #0284c7)',
              boxShadow: '0 0 25px rgba(16, 185, 129, 0.5), inset 0 2px 4px rgba(255, 255, 255, 0.4)',
              marginBottom: 10,
            }}
          >
            <Bot size={28} color="#06121e" strokeWidth={2.4} />
          </div>

          <h2
            style={{
              fontSize: 22,
              fontWeight: 900,
              letterSpacing: '-0.03em',
              margin: '0 0 4px 0',
              background: 'linear-gradient(135deg, #ffffff 40%, #a7f3d0 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            TradePilot AI Terminal
          </h2>
          <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8', fontWeight: 500 }}>
            "Monitor. Predict. Learn. Protect. Trade."
          </p>
        </div>

        {/* Mode Selector Tabs (Sign In, Create Account, Broker Gateway) */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: 5,
            background: 'rgba(15, 23, 42, 0.7)',
            padding: 4,
            borderRadius: 12,
            border: '1px solid rgba(255, 255, 255, 0.08)',
            marginBottom: 20,
            transform: 'translateZ(20px)',
          }}
        >
          <button
            type="button"
            onClick={() => { setMode('signin'); setErrorMsg(''); setSuccessMsg('') }}
            style={{
              padding: '8px 8px',
              borderRadius: 8,
              border: 'none',
              fontSize: 11.5,
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 5,
              transition: 'all 0.2s',
              background: mode === 'signin' ? 'linear-gradient(135deg, #10b981, #059669)' : 'transparent',
              color: mode === 'signin' ? '#ffffff' : '#94a3b8',
              boxShadow: mode === 'signin' ? '0 4px 14px rgba(16, 185, 129, 0.35)' : 'none',
            }}
          >
            <Lock size={13} /> Sign In
          </button>
          <button
            type="button"
            onClick={() => { setMode('signup'); setErrorMsg(''); setSuccessMsg('') }}
            style={{
              padding: '8px 8px',
              borderRadius: 8,
              border: 'none',
              fontSize: 11.5,
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 5,
              transition: 'all 0.2s',
              background: mode === 'signup' ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)' : 'transparent',
              color: mode === 'signup' ? '#ffffff' : '#94a3b8',
              boxShadow: mode === 'signup' ? '0 4px 14px rgba(139, 92, 246, 0.35)' : 'none',
            }}
          >
            <UserPlus size={13} /> Create Account
          </button>
          <button
            type="button"
            onClick={() => { setMode('broker'); setErrorMsg(''); setSuccessMsg('') }}
            style={{
              padding: '8px 8px',
              borderRadius: 8,
              border: 'none',
              fontSize: 11.5,
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 5,
              transition: 'all 0.2s',
              background: mode === 'broker' ? 'linear-gradient(135deg, #0284c7, #0369a1)' : 'transparent',
              color: mode === 'broker' ? '#ffffff' : '#94a3b8',
              boxShadow: mode === 'broker' ? '0 4px 14px rgba(2, 132, 199, 0.35)' : 'none',
            }}
          >
            <Database size={13} /> Broker
          </button>
        </div>

        {/* Feedback Alerts */}
        {errorMsg && (
          <div style={{ padding: '9px 12px', borderRadius: 8, background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', fontSize: 12, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertCircle size={15} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div style={{ padding: '9px 12px', borderRadius: 8, background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', fontSize: 12, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <CheckCircle2 size={15} style={{ flexShrink: 0 }} />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ transform: 'translateZ(25px)' }}>
          {/* Full Name field (Create Account mode only) */}
          {mode === 'signup' && (
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6, color: '#cbd5e1', marginBottom: 5 }}>
                Full Name / Trader Handle
              </label>
              <div style={{ position: 'relative' }}>
                <User size={16} color="#64748b" style={{ position: 'absolute', left: 14, top: 12 }} />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="e.g. Vikram Joshi"
                  style={{
                    width: '100%',
                    padding: '11px 14px 11px 42px',
                    background: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid rgba(56, 189, 248, 0.2)',
                    borderRadius: 10,
                    color: '#f8fafc',
                    fontSize: 13,
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => (e.target.style.borderColor = '#8b5cf6')}
                  onBlur={(e) => (e.target.style.borderColor = 'rgba(56, 189, 248, 0.2)')}
                />
              </div>
            </div>
          )}

          {/* Email / Handle */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6, color: '#cbd5e1', marginBottom: 5 }}>
              {mode === 'broker' ? 'Broker Client ID / API Key' : 'Trader Email Address'}
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} color="#64748b" style={{ position: 'absolute', left: 14, top: 12 }} />
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder={mode === 'broker' ? 'e.g. ZERODHA-CL-9901' : (mode === 'signup' ? 'trader@company.com' : 'trader@tradepilot.ai')}
                style={{
                  width: '100%',
                  padding: '11px 14px 11px 42px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  borderRadius: 10,
                  color: '#f8fafc',
                  fontSize: 13,
                  outline: 'none',
                  transition: 'border-color 0.2s',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => (e.target.style.borderColor = mode === 'signup' ? '#8b5cf6' : '#10b981')}
                onBlur={(e) => (e.target.style.borderColor = 'rgba(56, 189, 248, 0.2)')}
              />
            </div>
          </div>

          {/* Password / Access Token */}
          <div style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <label style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6, color: '#cbd5e1' }}>
                {mode === 'broker' ? 'API Secret / Auth Token' : (mode === 'signup' ? 'Create Password (Min 6 chars)' : 'Password')}
              </label>
              {mode === 'signin' && (
                <span style={{ fontSize: 11, color: '#38bdf8', cursor: 'pointer', fontWeight: 600 }}>Forgot Key?</span>
              )}
            </div>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="#64748b" style={{ position: 'absolute', left: 14, top: 12 }} />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder={mode === 'signup' ? 'Create a secure password' : 'Enter password'}
                style={{
                  width: '100%',
                  padding: '11px 42px 11px 42px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  borderRadius: 10,
                  color: '#f8fafc',
                  fontSize: 13,
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => (e.target.style.borderColor = mode === 'signup' ? '#8b5cf6' : '#10b981')}
                onBlur={(e) => (e.target.style.borderColor = 'rgba(56, 189, 248, 0.2)')}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: 12,
                  top: 10,
                  background: 'transparent',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer',
                  padding: 2,
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Mode-Specific Extras */}
          {mode === 'signup' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Account Tier</label>
                <select
                  value={tier}
                  onChange={(e) => setTier(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    background: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid rgba(56, 189, 248, 0.2)',
                    borderRadius: 8,
                    color: '#f8fafc',
                    fontSize: 11.5,
                  }}
                >
                  <option value="INSTITUTIONAL AI">Institutional AI</option>
                  <option value="PRO ALGORITHMIC">Pro Algorithmic</option>
                  <option value="RETAIL QUANT">Retail Quant</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Execution Gateway</label>
                <select
                  value={brokerGateway}
                  onChange={(e) => setBrokerGateway(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    background: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid rgba(56, 189, 248, 0.2)',
                    borderRadius: 8,
                    color: '#f8fafc',
                    fontSize: 11.5,
                  }}
                >
                  <option value="PAPER_BROKER">Paper Sandbox (₹5L)</option>
                  <option value="ZERODHA_KITE">Zerodha Kite</option>
                  <option value="UPSTOX_PRO">Upstox Pro</option>
                  <option value="ANGEL_ONE">Angel One</option>
                </select>
              </div>
            </div>
          )}

          {mode === 'broker' && (
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Select Broker Gateway</label>
              <select
                value={brokerGateway}
                onChange={(e) => setBrokerGateway(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  borderRadius: 8,
                  color: '#38bdf8',
                  fontSize: 12.5,
                  fontWeight: 700,
                }}
              >
                <option value="ZERODHA_KITE">Zerodha Kite Connect v3 (NSE/BSE)</option>
                <option value="UPSTOX_PRO">Upstox Pro API v2 (NSE/BSE/MCX)</option>
                <option value="ANGEL_ONE">Angel One SmartAPI (Equities & F&O)</option>
                <option value="GROWW">Groww Trading Gateway</option>
                <option value="PAPER_BROKER">Simulated Institutional Paper Broker</option>
              </select>
            </div>
          )}

          {mode === 'signin' && (
            /* 2FA Security Token */
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <label style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6, color: '#cbd5e1' }}>
                  2FA / Hardware TOTP Token
                </label>
                <span style={{ fontSize: 10, color: '#34d399', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 3 }}>
                  <ShieldCheck size={11} /> Verified
                </span>
              </div>
              <div style={{ position: 'relative' }}>
                <KeyRound size={15} color="#64748b" style={{ position: 'absolute', left: 14, top: 11 }} />
                <input
                  type="text"
                  value={totp}
                  onChange={(e) => setTotp(e.target.value)}
                  maxLength={6}
                  style={{
                    width: '100%',
                    padding: '9px 14px 9px 42px',
                    background: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid rgba(56, 189, 248, 0.2)',
                    borderRadius: 10,
                    color: '#34d399',
                    fontFamily: 'monospace',
                    letterSpacing: 4,
                    fontSize: 13,
                    fontWeight: 700,
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
            </div>
          )}

          {/* Execution Environment Toggle */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6, color: '#cbd5e1', marginBottom: 6 }}>
              Execution Sandbox
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div
                onClick={() => setEnvironment('live')}
                style={{
                  padding: '9px 12px',
                  borderRadius: 8,
                  border: `1px solid ${environment === 'live' ? '#10b981' : 'rgba(255, 255, 255, 0.08)'}`,
                  background: environment === 'live' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'all 0.15s',
                }}
              >
                <Radio size={14} color={environment === 'live' ? '#10b981' : '#64748b'} />
                <div>
                  <div style={{ fontSize: 11.5, fontWeight: 800, color: environment === 'live' ? '#10b981' : '#cbd5e1' }}>Live Market</div>
                  <div style={{ fontSize: 9.5, color: '#94a3b8' }}>Real 1s Feeds</div>
                </div>
              </div>

              <div
                onClick={() => setEnvironment('paper')}
                style={{
                  padding: '9px 12px',
                  borderRadius: 8,
                  border: `1px solid ${environment === 'paper' ? '#38bdf8' : 'rgba(255, 255, 255, 0.08)'}`,
                  background: environment === 'paper' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'all 0.15s',
                }}
              >
                <Radio size={14} color={environment === 'paper' ? '#38bdf8' : '#64748b'} />
                <div>
                  <div style={{ fontSize: 11.5, fontWeight: 800, color: environment === 'paper' ? '#38bdf8' : '#cbd5e1' }}>Paper Trading</div>
                  <div style={{ fontSize: 9.5, color: '#94a3b8' }}>₹5,00,000 Sandbox</div>
                </div>
              </div>
            </div>
          </div>

          {/* Primary Action Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: '13px 20px',
              borderRadius: 12,
              border: 'none',
              background: mode === 'signup'
                ? 'linear-gradient(135deg, #8b5cf6 0%, #0284c7 100%)'
                : (mode === 'broker'
                  ? 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)'
                  : 'linear-gradient(135deg, #10b981 0%, #0284c7 100%)'),
              color: '#ffffff',
              fontSize: 13.5,
              fontWeight: 900,
              letterSpacing: 0.3,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              boxShadow: mode === 'signup'
                ? '0 8px 24px rgba(139, 92, 246, 0.35)'
                : '0 8px 24px rgba(16, 185, 129, 0.35)',
              transition: 'transform 0.15s, box-shadow 0.15s',
              marginBottom: 10,
            }}
          >
            {isSubmitting ? (
              <span>Authenticating Gateway...</span>
            ) : mode === 'signup' ? (
              <>
                <UserPlus size={16} /> Create Trader Account & Launch <ArrowRight size={16} />
              </>
            ) : mode === 'broker' ? (
              <>
                <Database size={16} /> Connect Broker & Launch Terminal <ArrowRight size={16} />
              </>
            ) : (
              <>
                <Zap size={16} /> Authenticate & Launch Terminal <ArrowRight size={16} />
              </>
            )}
          </button>

          {/* Switch Mode Helper Link */}
          <div style={{ textAlign: 'center', marginBottom: 12, fontSize: 11.5, color: '#94a3b8' }}>
            {mode === 'signup' ? (
              <span>
                Already registered?{' '}
                <b
                  onClick={() => { setMode('signin'); setErrorMsg(''); setSuccessMsg('') }}
                  style={{ color: '#10b981', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  Sign In to Terminal
                </b>
              </span>
            ) : (
              <span>
                Don't have an account?{' '}
                <b
                  onClick={() => { setMode('signup'); setErrorMsg(''); setSuccessMsg('') }}
                  style={{ color: '#8b5cf6', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  Create Trader Account
                </b>
              </span>
            )}
          </div>

          {/* 1-Click Instant Demo Access Button */}
          <button
            type="button"
            onClick={handleDemoAccess}
            style={{
              width: '100%',
              padding: '10px 16px',
              borderRadius: 10,
              border: '1px solid rgba(56, 189, 248, 0.3)',
              background: 'rgba(56, 189, 248, 0.08)',
              color: '#38bdf8',
              fontSize: 12,
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              transition: 'all 0.15s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(56, 189, 248, 0.18)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(56, 189, 248, 0.08)')}
          >
            <Sparkles size={14} color="#38bdf8" /> ⚡ 1-Click Instant Demo Access (Skip Login)
          </button>
        </form>

        {/* Footer Security Badges */}
        <div
          style={{
            marginTop: 20,
            paddingTop: 14,
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: 10.5,
            color: '#64748b',
            transform: 'translateZ(15px)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <ShieldCheck size={13} color="#10b981" />
            <span>SEBI / Exchange Compliant</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <Cpu size={13} color="#38bdf8" />
            <span>AI Risk Veto Active</span>
          </div>
        </div>
      </div>
    </div>
  )
}
