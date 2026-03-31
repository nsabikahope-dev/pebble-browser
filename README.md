# 🪨 Pebble Browser

A private, lightweight desktop web browser built with Python and PyQt5.

## Features

- **Tor routing** — all traffic routed through Tor (optional, toggleable without restart)
- **Private by default** — no history, cookies, or cache saved between sessions
- **Pebble Search** — built-in search proxy that fetches Brave Search results through Tor, strips all ads and tracking
- **Multiple search engines** — switch between Pebble Search, DuckDuckGo, Google, or a local SearXNG instance
- **KidShield** — optional content filter; keyword-based without an API key, AI-powered with one
- **Find in page** — Ctrl+F search within any open page
- **Zoom** — per-tab zoom with keyboard shortcuts
- **Fake user agent** — presents as Firefox on Windows to reduce fingerprinting
- **Permissions blocked** — geolocation, camera, microphone, and notifications are all denied

## Quick Install (Linux)

```bash
git clone https://github.com/your-username/pebble-browser.git
cd pebble-browser
./install.sh
```

`install.sh` handles everything: Python packages, system libraries, Tor, and an optional app-menu shortcut.

Then launch with:

```bash
./launch.sh
```

## Manual Install

```bash
pip install -r requirements.txt
```

On Linux you also need a few system libraries:

```bash
sudo apt install tor libxcb-xinerama0 libxkbcommon-x11-0 libegl1
```

On Windows, see [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md).

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+T` | New tab |
| `Ctrl+W` | Close tab |
| `Ctrl+L` / `F6` | Focus address bar |
| `Ctrl+R` / `F5` | Reload |
| `Ctrl+Shift+R` | Hard reload (bypass cache) |
| `Alt+Left` | Back |
| `Alt+Right` | Forward |
| `Ctrl+Tab` | Next tab |
| `Ctrl+Shift+Tab` | Previous tab |
| `Ctrl+F` | Find in page |
| `Enter` / `Shift+Enter` | Find next / previous |
| `Escape` | Close find bar |
| `Ctrl++` / `Ctrl+-` | Zoom in / out |
| `Ctrl+0` | Reset zoom |

## Search Engines

| Option | Description |
|---|---|
| **Brave — Full Privacy** | Local proxy → Brave Search via Tor. No browser fingerprint, no JS, no cookies exposed to Brave. Most private option. |
| **Brave Search** | Direct to Brave (routed through Tor if enabled) |
| **DuckDuckGo** | Direct (routed through Tor if enabled) |
| **Google** | Direct (routed through Tor if enabled) |
| **SearXNG** | Requires a local SearXNG instance on port 8080 |

Switch engines live from the toolbar — no restart needed.

## KidShield

Click **🛡 Kids** in the toolbar to configure. Two modes:

- **Keyword mode** (no API key) — blocks pages containing known harmful terms
- **AI mode** (Claude API key required) — full-page analysis covering violence, sexual content, hate speech, drugs, and more

## Configuration

Settings are saved to `config.json` (git-ignored). It is created on first run with safe defaults. You can also hand-edit it:

| Key | Values | Default |
|---|---|---|
| `tor_enabled` | `true` / `false` | `true` |
| `search_engine` | `pebble`, `ddg`, `google`, `searxng` | `pebble` |
| `kidshield.enabled` | `true` / `false` | `false` |
| `kidshield.apiKey` | Claude API key string | `""` |
| `kidshield.responseMode` | `overlay`, `blur`, `banner` | `overlay` |

## Troubleshooting

**`Could not load the Qt platform plugin "xcb"`**
Install missing system libraries:
```bash
sudo apt install libxcb-xinerama0 libxkbcommon-x11-0 libegl1
```

**`Tor is enabled but could not connect to port 9050`**
Start Tor:
```bash
sudo systemctl start tor
# or
sudo apt install tor && sudo systemctl enable --now tor
```

**`ModuleNotFoundError: No module named 'PyQt5'`**
Run `./install.sh` or `pip install -r requirements.txt`.

**App won't open when clicked from the application menu**
Run `./install.sh` — it creates a correct `.desktop` file with the right environment variables set.

## Privacy Notes

- All browser traffic is routed through Tor's SOCKS5 proxy when enabled — your IP is never seen by websites
- The built-in Pebble Search fetches results through Tor using Python's requests library
- The browser uses an off-the-record profile — nothing is written to disk between sessions
- DNS for browser pages is resolved through Tor internally
- No analytics, no telemetry, no update checks — Pebble makes no network requests of its own
