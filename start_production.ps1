# TradePilot Production PowerShell Launcher

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    TradePilot Production Application Launcher     " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check backend environment
if (-not (Test-Path "backend\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Backend virtual environment not found in backend\venv." -ForegroundColor Red
    Write-Host "Run setup in backend directory first." -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/2] Starting TradePilot Production Backend (FastAPI)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir\backend'; .\venv\Scripts\python.exe start_production.py"

Write-Host "[2/2] Starting TradePilot Frontend UI (Vite)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir\frontend'; npm run dev -- --open"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "TradePilot Production System Active!" -ForegroundColor Green
Write-Host "Frontend Application UI : http://localhost:5173" -ForegroundColor White
Write-Host "Backend API Server     : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "OpenAPI Swagger Docs   : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan
