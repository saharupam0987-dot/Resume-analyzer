<#
.SYNOPSIS
    Launches Redis, Celery, FastAPI, and Vite Frontend in separate terminal windows and opens the app in the default browser.
#>

param(
    [switch]$BackendOnly = $false
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "      Student-Teacher Evaluation Platform - Master Launcher (PS)      " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start Redis
Write-Host "[1/3] Launching Redis Server on port 6379..." -ForegroundColor Yellow
$redisExe = Join-Path $scriptDir "redis_bin\redis-server.exe"
if (Test-Path $redisExe) {
    Start-Process cmd.exe -ArgumentList "/k cd /d `"$scriptDir\redis_bin`" && redis-server.exe redis.windows.conf"
} else {
    Start-Process cmd.exe -ArgumentList "/k wsl -u root service redis-server start"
}

Start-Sleep -Seconds 2

# 2. Start Celery Worker
Write-Host "[2/3] Launching Celery Background Worker (--pool=solo)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k cd /d `"$scriptDir`" && python -m celery -A tasks.celery_app worker --loglevel=info --pool=solo"

# 3. Start FastAPI Backend
Write-Host "[3/3] Launching FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k cd /d `"$scriptDir`" && python -m uvicorn api.main:app --reload --port 8000"

# 4. Optional Frontend
if (-not $BackendOnly) {
    $frontendPkg = Join-Path $scriptDir "frontend\package.json"
    if (Test-Path $frontendPkg) {
        Write-Host "[4/4] Launching Vite Frontend on http://localhost:5173..." -ForegroundColor Yellow
        Start-Process cmd.exe -ArgumentList "/k cd /d `"$scriptDir\frontend`" && npm run dev"
    }
}

Write-Host "`nWaiting 3 seconds for services to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Open Browser
if (-not $BackendOnly -and (Test-Path (Join-Path $scriptDir "frontend\package.json"))) {
    Write-Host "Opening Frontend App: http://localhost:5173" -ForegroundColor Green
    Start-Process "http://localhost:5173"
}

Write-Host "Opening FastAPI Interactive Docs: http://localhost:8000/docs" -ForegroundColor Green
Start-Process "http://localhost:8000/docs"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host " All services started in separate terminal windows!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
