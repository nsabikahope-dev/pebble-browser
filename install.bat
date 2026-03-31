@echo off
title Pebble Browser — Installer
echo.
echo  ========================================
echo   Pebble Browser — Installer
echo  ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python is not installed on this computer.
    echo.
    echo  Please do the following:
    echo.
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Download and install Python
    echo   3. IMPORTANT: tick "Add Python to PATH" during install
    echo   4. Come back and double-click this file again
    echo.
    pause
    exit /b 1
)

echo  Python found. Installing Pebble dependencies...
echo.
pip install PyQt5 PyQtWebEngine "requests[socks]" beautifulsoup4

if errorlevel 1 (
    echo.
    echo  Something went wrong during install.
    echo  Please take a screenshot of this window and send it for help.
    echo.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   Installation complete!
echo  ========================================
echo.
echo  To open Pebble, double-click "Pebble.bat" in this folder.
echo.
pause
