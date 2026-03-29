# Pebble — Windows Installation

## Quick install (for your team)

1. Install **Python 3.10+** from https://www.python.org/downloads/
   - During install, check "Add Python to PATH"
2. Install **Tor for Windows** from https://www.torproject.org/download/
   - Install the Tor Expert Bundle (not Tor Browser) — or just install Tor Browser and let it run in the background
3. Open a terminal in this folder and run:
   ```
   pip install PyQt5 PyQtWebEngine "requests[socks]" beautifulsoup4
   python browser.py
   ```

## Build a standalone .exe (no Python needed on target machine)

Run `build_windows.bat` on a Windows machine. This creates a `dist\Pebble\` folder you can zip and share — no Python installation required on the target machine.

## Tor on Windows

Pebble routes traffic through Tor automatically if it detects Tor running on port 9050.

**Option A — Tor Browser (easiest):** Install Tor Browser and keep it open. Its built-in Tor will listen on port 9050.

**Option B — Tor Expert Bundle:** Download from https://www.torproject.org/download/ and run `tor.exe`. Pebble will detect it automatically.

If Tor is not running, Pebble still works — the toolbar will show `🔓 Tor: OFF` and you can browse normally.
