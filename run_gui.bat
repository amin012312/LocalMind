@echo off
title LocalMind - GUI Interface

echo ============================================
echo    LocalMind - LIVE-OFFLINE AI Assistant  
echo ============================================
echo.
echo Starting GUI Interface...
echo.

REM Check if virtual environment exists
if not exist "..\\.venv\\Scripts\\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM Start LocalMind GUI
"..\\.venv\\Scripts\\python.exe" localmind.py --gui

echo.
echo LocalMind GUI has exited.
pause
