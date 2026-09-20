# TradePilot — AI-Powered Real-Time Trading & Risk Manager

TradePilot is an enterprise-grade real-time market analysis, quantitative AI prediction, and paper trading management system built with **FastAPI**, **Machine Learning Engines**, **NSE/BSE & 24/7 Crypto Market Data Providers**, **Risk Management Controls**, and an interactive **React + Vite Frontend**.

---

## 📁 Repository Structure

```
ai-trade-manager/
├── backend/                  # FastAPI Backend API & Quantitative Engine
│   ├── app/                  # Application Core, Routes, Services, Schemas
│   │   ├── api/routes/       # REST API Endpoints (v1_market, v1_crypto, v1_ai, etc.)
│   │   ├── services/         # Market Data Managers, Indicators, Scanners, AI Engine
│   │   ├── config.py         # Application & Environment Settings
│   │   ├── database.py       # Portfolio Store & Audit Log Engine
│   │   └── main.py           # FastAPI Application Entry Point & WebSockets
│   ├── tests/                # Automated System & API Test Suite
│   ├── start_production.py   # Uvicorn Production Launch Script
│   ├── Dockerfile            # Production Docker Container Specification
│   ├── docker-compose.yml    # Docker Service Orchestration
│   └── requirements.txt      # Python Dependencies
├── frontend/                 # React + Vite Interactive Web Console
│   ├── src/                  # React Components (App.jsx, CryptoDesk.jsx, etc.)
│   ├── public/               # Static Assets & Icons
│   ├── vite.config.js        # Vite Build & Development Proxy Configuration
│   └── package.json          # Node Dependencies & Scripts
├── .gitignore                # Production Version Control Ignore Rules
├── start.bat                 # 1-Click Windows Batch Development Launcher
├── start.ps1                 # 1-Click Windows PowerShell Development Launcher
├── start_production.bat      # 1-Click Windows Batch Production Launcher
├── start_production.ps1      # 1-Click Windows PowerShell Production Launcher
└── README.md                 # Project Overview & Operating Guide
```

---

## ⚡ Quick Start (1-Click Launchers)

### 🚀 Production Mode Launch
Double-click `start_production.bat` or execute in terminal:

```cmd
start_production.bat
```

Or via PowerShell:
```powershell
.\start_production.ps1
```

### 🛠 Development Mode Launch
```cmd
start.bat
```
Or via PowerShell:
```powershell
.\start.ps1
```

Both launchers concurrently initialize:
1. **TradePilot Backend API**: [`http://127.0.0.1:8000`](http://127.0.0.1:8000) (Interactive Swagger docs at `/docs`)
2. **TradePilot Web Console**: [`http://localhost:5173`](http://localhost:5173)

---

## 🛠 Manual Setup & Execution

### 1. Backend Setup (FastAPI & ML Engine)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Development Mode (with hot reload)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production Mode (with GZip compression, security headers & production logging)
python start_production.py
```

### 2. Frontend Setup (React + Vite)

```powershell
cd frontend
npm install

# Development Mode
npm run dev

# Production Build
npm run build
npm run preview
```

---

## 🐳 Docker Deployment

To containerize and run the backend using Docker Compose:

```bash
cd backend
docker-compose up --build -d
```

Check health status:
```bash
docker-compose ps
```

---

## 🌟 Key Platform Capabilities

- **Multi-Timeframe Candlestick Engine**: `1m`, `5m`, `15m`, `1h`, `1 Day`, `1 Week`, `1 Month`, and **`6 Months`** (140 to 184 daily bars).
- **6-Month Interactive Chart Scrollback**: Click-and-drag panning, mouse wheel scrolling, bottom timeline scrubber track, zoom `[+]`/`[-]` controls, and `[⏮ 6M Ago]`, `[◀ -1M]`, `[+1M ▶]`, `[▶▶ LIVE]` quick jump buttons.
- **24/7 Cryptocurrency Trading Desk**: Real-time continuous streaming for `BTC`, `ETH`, `SOL`, `BNB`, `XRP`, `DOGE`, `ADA`, `AVAX`, `LINK`, `DOT`.
- **Dynamic Technical Indicators & Pivots**: Real-time SMA (20), EMA (21), Bollinger Bands, VWAP, Classical Pivots (R2, R1, P, S1, S2).
- **Hardened Production Backend**: Configured CORS middleware, GZip payload compression (>1KB), security headers (`nosniff`, `DENY`, `XSS-Protection`), and production telemetry.

---

## 🧪 Testing

Execute automated unit tests for market data providers, indicator engines, and REST endpoints:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests
```
