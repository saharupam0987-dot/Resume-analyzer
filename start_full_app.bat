@echo off
title Evaluate Platform Launcher
setlocal EnableDelayedExpansion

cd /d "%~dp0"
call "%~dp0start_app.bat" %*
