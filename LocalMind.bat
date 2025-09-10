@echo off
title LocalMind - Quick Launcher

:menu
cls
echo ============================================
echo    LocalMind - LIVE-OFFLINE AI Assistant  
echo ============================================
echo.
echo Please select an interface:
echo.
echo [1] CLI Interface (Command Line)
echo [2] GUI Interface (Graphical)
echo [3] Setup/Install Dependencies
echo [4] Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto cli
if "%choice%"=="2" goto gui
if "%choice%"=="3" goto setup
if "%choice%"=="4" goto exit
echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:cli
echo.
echo Starting CLI Interface...
call run_cli.bat
goto menu

:gui
echo.
echo Starting GUI Interface...
call run_gui.bat
goto menu

:setup
echo.
echo Running setup...
call setup.bat
goto menu

:exit
echo.
echo Thank you for using LocalMind!
timeout /t 2 >nul
exit
