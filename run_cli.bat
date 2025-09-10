@echo off
title LocalMind - CLI Interface

echo ============================================
echo    LocalMind - LIVE-OFFLINE AI Assistant  
echo ============================================
echo.
echo Starting CLI Interface...
echo.

REM Check if virtual environment exists
if not exist "..\\.venv\\Scripts\\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM Start LocalMind CLI
"..\\.venv\\Scripts\\python.exe" localmind.py --cli

echo.
echo LocalMind CLI has exited.
pause
