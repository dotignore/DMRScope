@echo off
REM ============================================================
REM DMRScope Installation Script for Windows
REM ============================================================
REM This script sets up the environment for running DMRScope
REM It will:
REM - Check if Python is installed
REM - Create a virtual environment (venv)
REM - Activate the virtual environment
REM - Install all required packages from requirements.txt
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║        DMRScope - Windows Installation Script         ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
echo [*] Checking if Python is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo [INFO] Please install Python 3.8+ from https://www.python.org/
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo [OK] Python found!
echo.

REM Check if venv directory already exists
if exist venv (
    echo [*] Virtual environment already exists. Skipping creation...
    echo.
) else (
    echo [*] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created!
    echo.
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo [OK] Virtual environment activated!
echo.

REM Upgrade pip
echo [*] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install required packages
echo [*] Installing required packages from requirements.txt...
echo [*] This may take several minutes...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements!
    pause
    exit /b 1
)
echo.
echo [OK] All packages installed successfully!
echo.

REM Final message
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║     Installation Complete!                            ║
echo ║                                                        ║
echo ║  To start the application, run:                       ║
echo ║  - Double-click: run_windows.bat                      ║
echo ║  - Or from command line: run_windows.bat              ║
echo ╚════════════════════════════════════════════════════════╝
echo.
pause
exit /b 0
