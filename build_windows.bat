@echo off
REM ============================================================
REM  Pebble Browser — Windows build script
REM  Requirements: Python 3.10+, pip install pyinstaller PyQt5 PyQtWebEngine requests[socks] beautifulsoup4
REM  Run this from the pebble-public folder on a Windows machine.
REM ============================================================

echo Installing build dependencies...
pip install pyinstaller PyQt5 PyQtWebEngine "requests[socks]" beautifulsoup4

echo.
echo Building Pebble...
pyinstaller ^
  --name "Pebble" ^
  --windowed ^
  --onedir ^
  --add-data "kidshield.js;." ^
  --add-data "search_server.py;." ^
  --hidden-import PyQt5.QtWebEngineWidgets ^
  --hidden-import PyQt5.QtWebEngineCore ^
  --hidden-import socks ^
  --hidden-import bs4 ^
  browser.py

echo.
echo Done! Installer is in dist\Pebble\
echo Share the dist\Pebble\ folder or zip it up for your team.
echo.
echo NOTE: Users will also need Tor for Windows:
echo   https://www.torproject.org/download/
pause
