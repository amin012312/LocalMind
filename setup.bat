@echo off
title LocalMind - Setup and Installation

echo ============================================
echo    LocalMind - Setup and Installation     
echo ============================================
echo.
echo This script will set up LocalMind with all dependencies.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ and add it to your PATH.
    echo.
    pause
    exit /b 1
)

echo Python found: 
python --version

echo.
echo Creating virtual environment...
if not exist "..\\.venv" (
    python -m venv "..\\.venv"
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.
echo Activating virtual environment...
call "..\\.venv\\Scripts\\activate.bat"

echo.
echo Installing required packages...
"..\\.venv\\Scripts\\python.exe" -m pip install --upgrade pip
"..\\.venv\\Scripts\\pip.exe" install -r requirements.txt

echo.
echo ============================================
echo Setup completed successfully!
echo ============================================
echo.
echo You can now run LocalMind using:
echo - LocalMind.bat (Quick launcher with menu)
echo - run_cli.bat (Direct CLI launch)
echo - run_gui.bat (Direct GUI launch)
echo.
pause
