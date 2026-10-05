@echo off
echo Starting standalone Redis Server on port 6379...
if exist "%~dp0redis_bin\redis-server.exe" (
    "%~dp0redis_bin\redis-server.exe"
) else (
    echo redis-server.exe not found in redis_bin directory!
)
