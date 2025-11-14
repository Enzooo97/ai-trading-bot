@echo off
REM Quick setup launcher - runs PowerShell setup script
REM Double-click this file to start setup

echo ========================================
echo Trading Bot - Python 3.11 Setup Launcher
echo ========================================
echo.
echo This will launch the PowerShell setup script.
echo.
pause

PowerShell -ExecutionPolicy Bypass -File "%~dp0setup_python311.ps1"

pause
