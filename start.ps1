# TradePilot Application PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "          TradePilot Application Launcher          " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $rootDir

if (-not (Test-Path "backend\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Backend virtual environment not found in backend\venv." -ForegroundColor Red
    exit 1
}

Write-Host "[1/2] Starting TradePilot Backend API (FastAPI on Port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\backend'; .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

Write-Host "[2/2] Starting TradePilot Frontend UI (Vite)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\frontend'; npm run dev -- --open"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "TradePilot launched successfully!" -ForegroundColor Green
Write-Host "Backend API : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "Frontend UI : http://localhost:5173" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan
