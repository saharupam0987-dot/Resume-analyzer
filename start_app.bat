@echo off
title Student-Teacher Evaluation Platform Launcher
setlocal EnableDelayedExpansion

echo ======================================================================
echo       Student-Teacher Evaluation Platform - Master Launcher
echo ======================================================================
echo.

:: Change directory to the repository root where this script resides
cd /d "%~dp0"

:: -----------------------------------------------------------------------------
:: Configuration Options
:: -----------------------------------------------------------------------------
:: Set to 1 to also launch the React/Vite UI in an extra terminal (Port 5173)
:: Set to 0 if you only want the 3 backend terminals (Redis + Celery + FastAPI)
set LAUNCH_FRONTEND=1

:: Check if user passed arguments like --backend-only or -3
if "%1"=="--backend-only" set LAUNCH_FRONTEND=0
if "%1"=="-3" set LAUNCH_FRONTEND=0

:: -----------------------------------------------------------------------------
:: [Terminal 1] Redis Server (Port 6379)
:: -----------------------------------------------------------------------------
echo [1/3] Launching Redis Server on port 6379...
if exist "%~dp0redis_bin\redis-server.exe" (
    start "1. Redis Server (Port 6379)" /d "%~dp0redis_bin" cmd /k "redis-server.exe redis.windows.conf"
) else (
    start "1. Redis Server (Port 6379)" /d "%~dp0" cmd /k "wsl -u root service redis-server start"
)

:: Brief pause so Redis initializes before Celery worker attempts to connect
timeout /t 2 /nobreak >nul

:: -----------------------------------------------------------------------------
:: [Terminal 2] Celery Background Worker
:: -----------------------------------------------------------------------------
echo [2/3] Launching Celery Background Worker (--pool=solo)...
start "2. Celery Worker" /d "%~dp0" cmd /k "python -m celery -A tasks.celery_app worker --loglevel=info --pool=solo"

:: -----------------------------------------------------------------------------
:: [Terminal 3] FastAPI Backend (Port 8000)
:: -----------------------------------------------------------------------------
echo [3/3] Launching FastAPI Backend on http://localhost:8000...
start "3. FastAPI Backend (Port 8000)" /d "%~dp0" cmd /k "python -m uvicorn api.main:app --reload --port 8000"

:: -----------------------------------------------------------------------------
:: [Optional Terminal 4] Vite Frontend (Port 5173)
:: -----------------------------------------------------------------------------
if "%LAUNCH_FRONTEND%"=="1" (
    if exist "%~dp0frontend\package.json" (
        echo [4/4] Launching Vite Frontend on http://localhost:5173...
        start "4. Vite Frontend (Port 5173)" /d "%~dp0frontend" cmd /k "npm run dev"
    )
)

:: -----------------------------------------------------------------------------
:: Open Browser
:: -----------------------------------------------------------------------------
echo.
echo Waiting for services to initialize...
timeout /t 3 /nobreak >nul

if "%LAUNCH_FRONTEND%"=="1" (
    if exist "%~dp0frontend\package.json" (
        echo Opening Frontend App (http://localhost:5173)...
        start http://localhost:5173
    )
)

echo Opening FastAPI Interactive Docs (http://localhost:8000/docs)...
start http://localhost:8000/docs

echo.
echo ======================================================================
echo  All services have been launched in separate terminal windows!
echo  - Redis:    Port 6379
echo  - Celery:   Worker running in solo pool
echo  - Backend:  http://localhost:8000 (Docs: http://localhost:8000/docs)
if "%LAUNCH_FRONTEND%"=="1" echo  - Frontend: http://localhost:5173
echo ======================================================================
echo.
echo You can close this launcher window now, or press any key to exit.
pause >nul
