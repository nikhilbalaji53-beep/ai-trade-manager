@echo off
title TradePilot App Launcher
echo ===================================================
echo           TradePilot Application Launcher          
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking environment...
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Backend virtual environment not found in backend\venv.
    echo Please set up the backend virtual environment first.
    pause
    exit /b 1
)

echo [2/3] Starting TradePilot Backend API (FastAPI)...
start "TradePilot Backend (Port 8000)" cmd /k "cd backend && venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [3/3] Starting TradePilot Frontend UI (Vite)...
start "TradePilot Frontend (Vite)" cmd /k "cd frontend && npm run dev -- --open"

echo.
echo ===================================================
echo TradePilot is launching!
echo Backend API : http://127.0.0.1:8000 (Swagger docs at /docs)
echo Frontend UI : http://localhost:5173
echo ===================================================
echo Keep the backend and frontend terminal windows open.
echo.
