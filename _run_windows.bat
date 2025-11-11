@echo off
REM ============================================================
REM DMRScope - Windows Launch Script
REM ============================================================
REM This script activates the virtual environment and runs run.py
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║          DMRScope - Starting Application              ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if venv exists
if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo [INFO] Please run install_windows.bat first
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if run.py exists
if not exist run.py (
    echo [ERROR] run.py not found!
    echo [INFO] Make sure you are in the correct directory
    echo.
    pause
    exit /b 1
)

REM Run the application
echo [*] Starting DMRScope...
echo.
python run.py

REM If the script exits, show a message
echo.
echo [*] Application closed
pause
exit /b 0
