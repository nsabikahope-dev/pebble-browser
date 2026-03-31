#!/usr/bin/env bash
# Pebble launcher — starts Tor if needed, then opens the browser.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure display/runtime env is set (needed when launched from app menu / .desktop file)
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Run ./install.sh first."
    exit 1
fi

# Start Tor in background if installed and not already running
if command -v tor &>/dev/null && ! ss -tln 2>/dev/null | grep -q ':9050'; then
    echo "Starting Tor..."
    tor &
    for i in $(seq 1 20); do
        sleep 1
        ss -tln 2>/dev/null | grep -q ':9050' && echo "Tor is ready." && break
    done
fi

cd "$SCRIPT_DIR"
python3 browser.py
