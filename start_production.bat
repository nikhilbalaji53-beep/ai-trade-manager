@echo off
title TradePilot Production Launcher
echo ===================================================
echo     TradePilot Production Application Launcher      
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking backend virtual environment...
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Backend virtual environment not found in backend\venv.
    echo Please set up the backend virtual environment first:
    echo   cd backend ^&^& python -m venv venv ^&^& .\venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo [2/3] Starting Production Backend Server (Port 8000)...
start "TradePilot Production Backend (8000)" cmd /k "cd backend && venv\Scripts\python.exe start_production.py"

echo [3/3] Starting Production Frontend Dev Server (Port 5173)...
start "TradePilot Frontend (5173)" cmd /k "cd frontend && npm run dev -- --open"

echo.
echo ===================================================
echo TradePilot Production Servers Running!
echo Frontend Application UI : http://localhost:5173
echo Backend API Server     : http://127.0.0.1:8000
echo OpenAPI Swagger Docs   : http://127.0.0.1:8000/docs
echo ===================================================
echo.
