# 🪨 Pebble Browser

A private, lightweight desktop web browser built with Python and PyQt5.

## Features

- **Tor routing** — all traffic routed through the Tor network (optional, toggleable)
- **Private by default** — no history, cookies, or cache saved to disk
- **Choice of search engines** — switch between Pebble Search (Brave, ad-stripped), DuckDuckGo, Google, or a local SearXNG instance
- **Pebble Search** — built-in local proxy that fetches Brave Search results through Tor, strips all ads and tracking scripts
- **KidShield** — optional AI-powered content filter (Claude Haiku) to protect children from harmful content; works with keyword filtering even without an API key
- **Fake user agent** — reports as Firefox on Windows to reduce browser fingerprinting
- **Permissions denied** — geolocation, camera, microphone, and notifications are all blocked

## Requirements

- Python 3.10+
- [Tor](https://www.torproject.org/) installed (`sudo apt install tor` on Ubuntu/Debian)

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/pebble-browser.git
cd pebble-browser
pip install -r requirements.txt
```

## Usage

```bash
./launch.sh
# or
python3 browser.py
```

## Search Engines

| Option | Description |
|--------|-------------|
| **Pebble Search** | Local proxy → Brave Search via Tor, ads and tracking stripped |
| **DuckDuckGo** | Direct (routed through Tor if enabled) |
| **Google** | Direct (routed through Tor if enabled) |
| **SearXNG** | Requires a local SearXNG instance running on port 8080 |

Switch engines live from the toolbar dropdown — no restart needed.

## KidShield

Click the **🛡 Kids** button in the toolbar to configure. Works in two modes:
- **Keyword mode** (no API key needed) — blocks pages whose titles/captions contain known harmful terms
- **AI mode** (Claude API key required) — full-page AI analysis covering violence, sexual content, hate speech, drugs, and more

## Configuration

Settings are stored in `config.json` (excluded from git). A fresh `config.json` is created on first run with safe defaults.

## Privacy Notes

- All traffic is routed through Tor when enabled — your IP is never exposed to search engines or websites
- The browser uses an off-the-record profile — nothing is written to disk between sessions
- DNS queries are resolved by Tor (`socks5h`) — your ISP cannot see what sites you visit
