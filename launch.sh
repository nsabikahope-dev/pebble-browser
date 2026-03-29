#!/usr/bin/env bash
# Pebble launcher — starts Tor if needed, then opens the browser.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found."
    exit 1
fi

# Start Tor in background if not already running and tor is installed
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
