"""
Pebble Search — local search proxy server.
Listens on 127.0.0.1:7777.
Fetches Brave Search HTML anonymously through Tor, returns clean results.
"""

import html as htmllib
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
from bs4 import BeautifulSoup

PORT    = 7777
HOST    = "127.0.0.1"
PROXY   = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT":             "1",
}

# ---------------------------------------------------------------------------
# Fetch & parse Brave Search HTML
# ---------------------------------------------------------------------------

def fetch_results(query: str, use_tor: bool) -> list[dict]:
    url  = f"https://search.brave.com/search?q={urllib.parse.quote(query)}&source=web&spellcheck=0"
    proxies = PROXY if use_tor else {}
    try:
        resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=25)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        if use_tor:
            raise RuntimeError("Cannot reach Brave Search through Tor. Is Tor running?") from e
        raise RuntimeError(f"Cannot reach Brave Search: {e}") from e
    except requests.exceptions.Timeout:
        raise RuntimeError("Brave Search timed out (Tor can be slow — try again).")
    return parse_results(resp.text)


def parse_results(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for item in soup.select("div.snippet"):
        # URL — first real http link in the snippet
        link = item.select_one("a[href^='http']")
        if not link:
            continue
        url = link.get("href", "").strip()

        # Title — prefer dedicated title element, fall back to link text
        title_el = (
            item.select_one(".title")
            or item.select_one("[class*='title']")
            or item.select_one(".heading-serpresult")
        )
        title = (title_el or link).get_text(strip=True)

        # Description
        desc_el = (
            item.select_one(".snippet-description")
            or item.select_one("[class*='description']")
            or item.select_one("p")
        )
        desc = desc_el.get_text(strip=True) if desc_el else ""

        # Display URL (hostname + path, stripped of tracking params)
        parsed  = urllib.parse.urlparse(url)
        display = parsed.netloc + (parsed.path if parsed.path != "/" else "")

        if title and url:
            results.append({"title": title, "url": url, "display": display, "desc": desc})

        if len(results) >= 10:
            break

    return results


# ---------------------------------------------------------------------------
# HTML templates
# ---------------------------------------------------------------------------

PAGE_CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f8f8f8; color: #222; min-height: 100vh;
  }
  header {
    background: #fff; border-bottom: 1px solid #e0e0e0;
    padding: 14px 24px; display: flex; align-items: center; gap: 16px;
  }
  .logo { font-size: 22px; font-weight: 700; color: #1a56db; text-decoration: none; }
  .logo span { color: #555; font-weight: 400; }
  form { display: flex; gap: 8px; flex: 1; max-width: 600px; }
  input[type=text] {
    flex: 1; padding: 9px 14px; border: 1px solid #ccc; border-radius: 24px;
    font-size: 15px; outline: none; background: #fff; color: #222;
    -webkit-appearance: none; appearance: none;
  }
  input[type=text]:focus { border-color: #1a56db; box-shadow: 0 0 0 2px #dbeafe; }
  button[type=submit] {
    background: #1a56db; color: #fff; border: none; border-radius: 20px;
    padding: 9px 20px; font-size: 14px; cursor: pointer; font-weight: 500;
  }
  button[type=submit]:hover { background: #1447c2; }
  .main { max-width: 720px; margin: 0 auto; padding: 24px 16px; }
  .meta { font-size: 13px; color: #777; margin-bottom: 18px; }
  .result { background: #fff; border-radius: 10px; padding: 16px 18px;
            margin-bottom: 12px; border: 1px solid #e8e8e8; }
  .result:hover { border-color: #b0c4f8; }
  .result-title a {
    font-size: 17px; font-weight: 600; color: #1a56db; text-decoration: none;
  }
  .result-title a:hover { text-decoration: underline; }
  .result-url { font-size: 12px; color: #28a745; margin: 3px 0 6px; }
  .result-desc { font-size: 14px; color: #444; line-height: 1.5; }
  .no-results { text-align: center; padding: 60px 20px; color: #777; }
  .error-box {
    background: #fff3cd; border: 1px solid #ffc107; border-radius: 10px;
    padding: 16px 18px; margin-bottom: 20px; font-size: 14px; color: #856404;
  }
  .badge {
    font-size: 11px; background: #e8f4fd; color: #1a56db; border-radius: 12px;
    padding: 2px 9px; margin-left: 8px; vertical-align: middle;
  }
  .home-hero { text-align: center; padding: 80px 20px 40px; }
  .home-hero .big-logo { font-size: 48px; font-weight: 700; color: #1a56db; margin-bottom: 8px; }
  .home-hero .tagline { color: #777; margin-bottom: 28px; font-size: 15px; }
  .home-hero form { justify-content: center; margin: 0 auto; }
  .home-hero input[type=text] { max-width: 460px; font-size: 16px; padding: 12px 18px; }
  .home-hero button[type=submit] { padding: 12px 26px; font-size: 15px; }
  .privacy-note { margin-top: 16px; font-size: 12px; color: #aaa; }
"""


def render_home() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Pebble Search</title>
  <style>{PAGE_CSS}</style>
</head>
<body>
  <div class="home-hero">
    <div class="big-logo">🪨 Pebble Search</div>
    <p class="tagline">Private search — your queries are yours alone</p>
    <form action="/search" method="get">
      <input type="text" name="q" placeholder="Search the web…" autofocus autocomplete="off">
      <button type="submit">Search</button>
    </form>
    <p class="privacy-note">🧅 All requests routed through Tor &nbsp;·&nbsp; No history saved &nbsp;·&nbsp; No tracking</p>
  </div>
</body>
</html>"""


def render_results(query: str, results: list[dict], error: str = "") -> str:
    escaped_q = htmllib.escape(query)
    items_html = ""

    if error:
        items_html += f'<div class="error-box">⚠ {htmllib.escape(error)}</div>'

    if results:
        count_label = f"{len(results)} result{'s' if len(results) != 1 else ''}"
        items_html += f'<p class="meta">{count_label} for <strong>{escaped_q}</strong> <span class="badge">🧅 via Tor</span></p>'
        for r in results:
            title  = htmllib.escape(r["title"])
            url    = htmllib.escape(r["url"])
            disp   = htmllib.escape(r["display"])
            desc   = htmllib.escape(r["desc"])
            items_html += f"""
<div class="result">
  <div class="result-title"><a href="{url}" target="_self">{title}</a></div>
  <div class="result-url">{disp}</div>
  {'<div class="result-desc">' + desc + '</div>' if desc else ''}
</div>"""
    elif not error:
        items_html += '<div class="no-results">No results found. Try different keywords.</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{escaped_q} — Pebble Search</title>
  <style>{PAGE_CSS}</style>
</head>
<body>
  <header>
    <a class="logo" href="/">🪨 Pebble<span> Search</span></a>
    <form action="/search" method="get">
      <input type="text" name="q" value="{escaped_q}" autocomplete="off">
      <button type="submit">Search</button>
    </form>
  </header>
  <div class="main">{items_html}</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

# Set by start_server() so handler knows whether Tor is active
_use_tor = True


class SearchHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass   # silence default access log

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/":
            self._send_html(render_home())

        elif parsed.path == "/search":
            query = params.get("q", [""])[0].strip()
            if not query:
                self._redirect("/")
                return
            try:
                results = fetch_results(query, use_tor=_use_tor)
                body    = render_results(query, results)
            except RuntimeError as e:
                body = render_results(query, [], error=str(e))
            self._send_html(body)

        elif parsed.path == "/health":
            self._send_html("ok", content_type="text/plain")

        else:
            self._send_html("<h2>404 Not Found</h2>", status=404)

    def _send_html(self, body: str, status: int = 200, content_type: str = "text/html; charset=utf-8"):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _redirect(self, location: str):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_server(use_tor: bool = True) -> ThreadingHTTPServer:
    global _use_tor
    _use_tor = use_tor
    server   = ThreadingHTTPServer((HOST, PORT), SearchHandler)
    thread   = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
