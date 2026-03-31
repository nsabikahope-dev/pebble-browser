#!/usr/bin/env bash
# Pebble Browser — installer
# Installs system dependencies, Python packages, and optionally adds a desktop entry.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Pebble Browser Installer ==="
echo

# ── Python check ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 is required."
    echo "Install from https://python.org or via your package manager."
    exit 1
fi

PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "ERROR: Python 3.10+ is required (found $PY_MAJOR.$PY_MINOR)."
    exit 1
fi
echo "✓ Python $PY_MAJOR.$PY_MINOR"

# ── System packages (Linux only) ──────────────────────────────────────────────
if [[ "$OSTYPE" == "linux"* ]]; then
    MISSING=()

    # Libraries required by PyQt5's xcb platform plugin
    for pkg in libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                libxcb-randr0 libxcb-render-util0 libxkbcommon-x11-0 libegl1; do
        dpkg -l "$pkg" 2>/dev/null | grep -q "^ii" || MISSING+=("$pkg")
    done

    # Tor (optional but recommended)
    if ! command -v tor &>/dev/null; then
        MISSING+=("tor")
        echo "  (Tor not found — will install. Pebble also works without it.)"
    else
        echo "✓ Tor installed"
    fi

    if [ ${#MISSING[@]} -gt 0 ]; then
        echo
        echo "Missing system packages: ${MISSING[*]}"
        read -rp "Install them now? (requires sudo) [Y/n] " REPLY
        if [[ "$REPLY" != "n" && "$REPLY" != "N" ]]; then
            sudo apt-get install -y "${MISSING[@]}"
        fi
    else
        echo "✓ System libraries OK"
    fi
fi

# ── Python packages ───────────────────────────────────────────────────────────
echo
echo "Installing Python packages..."
pip install -q --upgrade pip
pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Python packages installed"

# ── Permissions ───────────────────────────────────────────────────────────────
chmod +x "$SCRIPT_DIR/launch.sh"
echo "✓ launch.sh is executable"

# ── Desktop entry (Linux) ─────────────────────────────────────────────────────
if [[ "$OSTYPE" == "linux"* ]]; then
    echo
    read -rp "Add Pebble to your application menu? [Y/n] " REPLY
    if [[ "$REPLY" != "n" && "$REPLY" != "N" ]]; then
        DESKTOP_DIR="$HOME/.local/share/applications"
        mkdir -p "$DESKTOP_DIR"
        cat > "$DESKTOP_DIR/pebble.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Pebble
GenericName=Private Web Browser
Comment=Private browser with Tor routing and KidShield content filtering
Exec=$SCRIPT_DIR/launch.sh
Terminal=false
Categories=Network;WebBrowser;
Keywords=browser;web;private;tor;search;privacy;
StartupWMClass=Pebble
EOF
        chmod +x "$DESKTOP_DIR/pebble.desktop"
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
        echo "✓ Pebble added to application menu"
    fi
fi

echo
echo "=== Done! ==="
echo
echo "Run:  cd \"$SCRIPT_DIR\" && ./launch.sh"
