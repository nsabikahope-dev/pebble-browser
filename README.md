# 🪨 Pebble Browser

A private, lightweight desktop web browser. No tracking. No ads. Routes through Tor.

---

## Download & Install

### Step 1 — Download

Click the green **Code** button at the top of this page → **Download ZIP**.

Unzip the file somewhere you'll remember (e.g. your Desktop).

---

### Step 2 — Install

**On Windows:**
1. Open the unzipped folder
2. Double-click **`install.bat`**
3. Follow the on-screen instructions

Once done, double-click **`Pebble.bat`** any time you want to open Pebble.

---

**On Linux / Ubuntu:**
1. Open the unzipped folder
2. Right-click **`install.sh`** → **Properties** → **Permissions** → tick **"Allow executing file as program"**
3. Double-click **`install.sh`** — a setup window will open automatically

Once done, search for **Pebble** in your app menu to open it.

---

## Features

- **Tor routing** — all traffic routed through Tor (optional, toggleable)
- **Private by default** — no history, cookies, or cache saved between sessions
- **Brave — Full Privacy** — fetches Brave Search results through Tor server-side so Brave never sees your browser at all
- **Multiple search engines** — Brave (full privacy), Brave Search, DuckDuckGo, Google, SearXNG
- **KidShield** — optional content filter; keyword-based without an API key, AI-powered with one
- **Find in page** — Ctrl+F to search within any open page
- **Zoom** — per-tab zoom
- **Permissions blocked** — geolocation, camera, microphone, and notifications are all denied

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

Settings are saved to `config.json` (git-ignored). Created on first run with safe defaults. You can hand-edit it:

| Key | Values | Default |
|---|---|---|
| `tor_enabled` | `true` / `false` | `true` |
| `search_engine` | `pebble`, `brave`, `ddg`, `google`, `searxng` | `brave` |
| `kidshield.enabled` | `true` / `false` | `false` |
| `kidshield.apiKey` | Claude API key string | `""` |
| `kidshield.responseMode` | `overlay`, `blur`, `banner` | `overlay` |

## Troubleshooting

**`Could not load the Qt platform plugin "xcb"`**
```bash
sudo apt install libxcb-xinerama0 libxkbcommon-x11-0 libegl1
```

**`Tor is enabled but could not connect to port 9050`**
```bash
sudo apt install tor && sudo systemctl enable --now tor
```

**`ModuleNotFoundError: No module named 'PyQt5'`**
Run `./install.sh` or `pip install -r requirements.txt`.

**App won't open from the application menu**
Run `./install.sh` — it creates the correct desktop entry.

## Privacy Notes

- All browser traffic is routed through Tor when enabled — your IP is never seen by websites
- The **Brave — Full Privacy** option fetches results server-side through Tor so Brave never fingerprints your browser
- The browser uses an off-the-record profile — nothing is written to disk between sessions
- No analytics, no telemetry, no update checks
