#!/usr/bin/env python3
"""
Pebble — Private browser.
Features: Tor routing (optional), KidShield content filter (optional),
          choice of search engine (Pebble/Brave, DuckDuckGo, Google, SearXNG).
"""

import json
import os
import sys
import socket
import subprocess
import time

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE     = os.path.join(BASE_DIR, "config.json")
KIDSHIELD_JS    = os.path.join(BASE_DIR, "kidshield.js")

# ── Search engine definitions ─────────────────────────────────────────────────
SEARCH_ENGINES = {
    "pebble":  {
        "label":      "Brave — Full Privacy",
        "home":       "http://localhost:7777/",
        "search_url": "http://localhost:7777/search?q={}",
        "local":      True,
        "port":       7777,
    },
    "brave":   {
        "label":      "Brave Search",
        "home":       "https://search.brave.com",
        "search_url": "https://search.brave.com/search?q={}",
        "local":      False,
    },
    "ddg":     {
        "label":      "DuckDuckGo",
        "home":       "https://duckduckgo.com",
        "search_url": "https://duckduckgo.com/?q={}",
        "local":      False,
    },
    "google":  {
        "label":      "Google",
        "home":       "https://www.google.com",
        "search_url": "https://www.google.com/search?q={}",
        "local":      False,
    },
    "searxng": {
        "label":      "SearXNG (local)",
        "home":       "http://localhost:8080/",
        "search_url": "http://localhost:8080/search?q={}",
        "local":      True,
        "port":       8080,
    },
}

DEFAULT_CONFIG = {
    "tor_enabled":   True,
    "search_engine": "brave",
    "kidshield": {
        "enabled":       False,
        "apiKey":        "",
        "responseMode":  "overlay",
        "categories": {
            "violence":    True,
            "sexual":      True,
            "profanity":   False,
            "drugs":       True,
            "gambling":    False,
            "horror":      True,
            "selfHarm":    True,
            "hateSpeech":  True,
            "adultThemes": True,
            "weapons":     False,
        },
        "customKeywords": [],
    },
}

CATEGORY_META = {
    "violence":    "Violence & Gore",
    "sexual":      "Sexual Content",
    "profanity":   "Profanity & Strong Language",
    "drugs":       "Drug & Alcohol Use",
    "gambling":    "Gambling",
    "horror":      "Horror & Frightening Content",
    "selfHarm":    "Self-Harm & Suicide",
    "hateSpeech":  "Hate Speech & Discrimination",
    "adultThemes": "Adult Themes",
    "weapons":     "Weapons & Explosives",
}


# ── Config helpers ────────────────────────────────────────────────────────────

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                stored = json.load(f)
            cfg = json.loads(json.dumps(DEFAULT_CONFIG))
            cfg.update({k: v for k, v in stored.items() if k != "kidshield"})
            if "kidshield" in stored:
                cfg["kidshield"].update(stored["kidshield"])
                if "categories" in stored["kidshield"]:
                    cfg["kidshield"]["categories"].update(stored["kidshield"]["categories"])
            return cfg
        except (json.JSONDecodeError, OSError):
            pass
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def load_kidshield_js() -> str:
    try:
        with open(KIDSHIELD_JS) as f:
            return f.read()
    except OSError:
        return ""


config        = load_config()
KIDSHIELD_SRC = load_kidshield_js()

# ── Chromium flags — must be set before QApplication ─────────────────────────
_local_ports = [str(e["port"]) for e in SEARCH_ENGINES.values() if e.get("local") and "port" in e]
_bypass      = ";".join(f"localhost:{p}" for p in _local_ports) + ";127.0.0.1"

if config.get("tor_enabled", True):
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        f"--proxy-server=socks5://127.0.0.1:9050 "
        f"--proxy-bypass-list={_bypass}"
    )
else:
    os.environ.pop("QTWEBENGINE_CHROMIUM_FLAGS", None)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit,
    QTabWidget, QStatusBar, QMessageBox, QSizePolicy,
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
    QCheckBox, QComboBox, QGroupBox, QScrollArea, QWidget,
    QFormLayout, QPushButton, QLabel, QShortcut, QProgressBar,
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEngineProfile, QWebEngineSettings, QWebEnginePage,
)
from PyQt5.QtCore import QUrl, Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QKeySequence

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0"


# ── Pebble Search server (full-privacy local proxy) ──────────────────────────
_pebble_server = None

def _ensure_pebble_server(tor_ok: bool):
    global _pebble_server
    if _pebble_server is None:
        from search_server import start_server
        _pebble_server = start_server(use_tor=tor_ok)


# ── Tor helpers ───────────────────────────────────────────────────────────────

def check_tor() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 9050), timeout=2):
            return True
    except OSError:
        return False


def ensure_tor() -> bool:
    if check_tor():
        return True
    try:
        subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            time.sleep(1)
            if check_tor():
                return True
    except FileNotFoundError:
        pass
    return False


# ── Web profile ───────────────────────────────────────────────────────────────

def make_private_profile() -> QWebEngineProfile:
    profile = QWebEngineProfile()
    profile.setHttpUserAgent(USER_AGENT)
    s = profile.settings()
    s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
    s.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
    s.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, False)
    s.setAttribute(QWebEngineSettings.WebGLEnabled, False)
    s.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
    s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
    s.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, False)
    s.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
    s.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, False)
    s.setAttribute(QWebEngineSettings.AutoLoadImages, True)
    return profile


# ── Page / tab ────────────────────────────────────────────────────────────────

class PrivatePage(QWebEnginePage):
    def __init__(self, profile, window, parent=None):
        super().__init__(profile, parent)
        self._window = window
        self.featurePermissionRequested.connect(
            lambda url, feat: self.setFeaturePermission(url, feat, QWebEnginePage.PermissionDeniedByUser)
        )

    def createWindow(self, _):
        return self._window.new_tab().page()


class BrowserTab(QWebEngineView):
    def __init__(self, profile, window, home_url: str, parent=None):
        super().__init__(parent)
        self._window = window
        self.setPage(PrivatePage(profile, window, self))
        self.load(QUrl(home_url))

    def navigate(self, text: str, search_url: str):
        text = text.strip()
        if not text:
            return
        if " " in text or ("." not in text and ":" not in text and not text.startswith("http")):
            url = QUrl(search_url.format(text.replace(" ", "+")))
        else:
            if not text.startswith(("http://", "https://")):
                text = "https://" + text
            url = QUrl(text)
        self.load(url)

    def contextMenuEvent(self, event):
        menu = self.page().createStandardContextMenu()
        data = self.page().contextMenuData()
        if data.linkUrl().isValid():
            link_url = data.linkUrl()
            act = QAction("Open Link in New Tab", self)
            act.triggered.connect(lambda: self._window.open_in_new_tab(link_url))
            first = menu.actions()[0] if menu.actions() else None
            menu.insertAction(first, act)
            menu.insertSeparator(first)
        menu.exec_(event.globalPos())


# ── KidShield settings dialog ─────────────────────────────────────────────────

class KidShieldDialog(QDialog):
    def __init__(self, ks_cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KidShield Settings")
        self.setMinimumWidth(440)
        self._cfg = json.loads(json.dumps(ks_cfg))
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        self.enabled_cb = QCheckBox("Enable KidShield content filtering")
        f = self.enabled_cb.font(); f.setBold(True); self.enabled_cb.setFont(f)
        self.enabled_cb.setChecked(self._cfg.get("enabled", False))
        root.addWidget(self.enabled_cb)

        api_group  = QGroupBox("Claude API Key (enables AI scanning — optional)")
        api_layout = QHBoxLayout(api_group)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_key.setText(self._cfg.get("apiKey", ""))
        self.api_key.setPlaceholderText("sk-ant-… (keyword filtering works without it)")
        toggle_btn = QPushButton("Show"); toggle_btn.setFixedWidth(50)
        toggle_btn.clicked.connect(lambda: (
            self.api_key.setEchoMode(
                QLineEdit.Normal if self.api_key.echoMode() == QLineEdit.Password else QLineEdit.Password
            ),
            toggle_btn.setText("Hide" if self.api_key.echoMode() == QLineEdit.Normal else "Show")
        ))
        api_layout.addWidget(self.api_key); api_layout.addWidget(toggle_btn)
        root.addWidget(api_group)

        mode_group  = QGroupBox("Response when harmful content is detected")
        mode_layout = QFormLayout(mode_group)
        self.mode_combo = QComboBox()
        for label, data in [
            ("Overlay — full-screen block",    "overlay"),
            ("Blur   — page blurred with banner", "blur"),
            ("Banner — top warning bar only",  "banner"),
        ]:
            self.mode_combo.addItem(label, data)
        idx = self.mode_combo.findData(self._cfg.get("responseMode", "overlay"))
        self.mode_combo.setCurrentIndex(max(idx, 0))
        mode_layout.addRow("Mode:", self.mode_combo)
        root.addWidget(mode_group)

        cats_group = QGroupBox("Filter categories")
        cats_outer = QVBoxLayout(cats_group)
        scroll     = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFixedHeight(200); scroll.setFrameShape(QScrollArea.NoFrame)
        cw = QWidget(); cl = QVBoxLayout(cw); cl.setSpacing(4)
        saved = self._cfg.get("categories", {})
        self.cat_checks = {}
        for key, label in CATEGORY_META.items():
            cb = QCheckBox(label)
            cb.setChecked(saved.get(key, DEFAULT_CONFIG["kidshield"]["categories"].get(key, False)))
            self.cat_checks[key] = cb; cl.addWidget(cb)
        scroll.setWidget(cw); cats_outer.addWidget(scroll)
        br = QHBoxLayout()
        ab = QPushButton("Select All");  ab.clicked.connect(lambda: [c.setChecked(True)  for c in self.cat_checks.values()])
        nb = QPushButton("Select None"); nb.clicked.connect(lambda: [c.setChecked(False) for c in self.cat_checks.values()])
        br.addWidget(ab); br.addWidget(nb); br.addStretch()
        cats_outer.addLayout(br); root.addWidget(cats_group)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def get_settings(self) -> dict:
        return {
            "enabled":        self.enabled_cb.isChecked(),
            "apiKey":         self.api_key.text().strip(),
            "responseMode":   self.mode_combo.currentData(),
            "categories":     {k: cb.isChecked() for k, cb in self.cat_checks.items()},
            "customKeywords": self._cfg.get("customKeywords", []),
        }


# ── Main window ───────────────────────────────────────────────────────────────

class Pebble(QMainWindow):
    def __init__(self, tor_enabled: bool, tor_ok: bool):
        super().__init__()
        self._tor_enabled = tor_enabled
        self._tor_ok      = tor_ok
        self.config       = config
        self.setWindowTitle("Pebble")
        self.resize(1280, 800)
        self.profile = make_private_profile()
        self._build_ui()

        if tor_enabled and not tor_ok:
            QMessageBox.warning(self, "Tor Not Available",
                "Tor is enabled but could not connect to port 9050.\n\n"
                "Traffic is NOT anonymized.\n\n"
                "Install/start Tor, then restart Pebble, or disable Tor via the toolbar.")

    @property
    def _engine(self) -> dict:
        return SEARCH_ENGINES.get(self.config.get("search_engine", "pebble"), SEARCH_ENGINES["pebble"])

    def _build_ui(self):
        # ── Navigation toolbar ────────────────────────────────────────────────
        nav = QToolBar("Navigation")
        nav.setIconSize(QSize(18, 18))
        nav.setMovable(False)
        nav.setStyleSheet("QToolBar { spacing: 4px; padding: 2px; }")
        self.addToolBar(nav)

        for sym, tip, slot in [
            ("◀", "Back (Alt+Left)",     self._go_back),
            ("▶", "Forward (Alt+Right)", self._go_forward),
            ("⟳", "Reload (Ctrl+R/F5)", self._reload),
            ("⌂", "Home",               self._go_home),
        ]:
            a = QAction(sym, self); a.setToolTip(tip); a.triggered.connect(slot); nav.addAction(a)

        nav.addSeparator()
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter a URL…  (Ctrl+L)")
        self.url_bar.returnPressed.connect(self._navigate_from_bar)
        self.url_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        nav.addWidget(self.url_bar)
        nav.addSeparator()

        new_tab_act = QAction("＋", self)
        new_tab_act.setToolTip("New Tab (Ctrl+T)")
        new_tab_act.triggered.connect(self.new_tab)
        nav.addAction(new_tab_act)

        self.engine_combo = QComboBox()
        for key, eng in SEARCH_ENGINES.items():
            self.engine_combo.addItem(eng["label"], key)
        saved_key = self.config.get("search_engine", "pebble")
        idx = self.engine_combo.findData(saved_key)
        self.engine_combo.setCurrentIndex(max(idx, 0))
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        self.engine_combo.setToolTip("Select search engine")
        nav.addWidget(self.engine_combo)

        self.ks_act = QAction(self._ks_label(), self)
        self.ks_act.setToolTip("KidShield content filter — click to configure")
        self.ks_act.triggered.connect(self._open_ks_settings)
        nav.addAction(self.ks_act)

        self.tor_act = QAction(self._tor_label(), self)
        self.tor_act.setToolTip("Toggle Tor routing (requires restart)")
        self.tor_act.triggered.connect(self._toggle_tor)
        nav.addAction(self.tor_act)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # ── Find bar ──────────────────────────────────────────────────────────
        self._find_bar = self._make_find_bar()

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.tabs)
        lay.addWidget(self._find_bar)
        self.setCentralWidget(container)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setFixedWidth(120)
        self._progress.setMaximumHeight(14)
        self._progress.setTextVisible(False)
        self._progress.hide()
        self.status.addPermanentWidget(self._progress)
        self._update_status()

        # ── Keyboard shortcuts ────────────────────────────────────────────────
        for key, slot in [
            ("Ctrl+T",         self.new_tab),
            ("Ctrl+W",         self._close_current_tab),
            ("Ctrl+L",         self._focus_url_bar),
            ("F6",             self._focus_url_bar),
            ("Ctrl+R",         self._reload),
            ("F5",             self._reload),
            ("Ctrl+Shift+R",   self._hard_reload),
            ("Alt+Left",       self._go_back),
            ("Alt+Right",      self._go_forward),
            ("Ctrl+Tab",       self._next_tab),
            ("Ctrl+Shift+Tab", self._prev_tab),
            ("Ctrl+F",         self._show_find_bar),
            ("Ctrl+=",         self._zoom_in),
            ("Ctrl++",         self._zoom_in),
            ("Ctrl+-",         self._zoom_out),
            ("Ctrl+0",         self._zoom_reset),
        ]:
            QShortcut(QKeySequence(key), self, slot)

        self.new_tab()

    # ── Find bar ──────────────────────────────────────────────────────────────

    def _make_find_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(
            "QWidget { background: #f0f0f0; border-top: 1px solid #ccc; }"
            "QLineEdit { background: #fff; border: 1px solid #bbb; border-radius: 3px; padding: 2px 6px; }"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(4)

        lay.addWidget(QLabel("Find:"))

        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText("Search in page…")
        self._find_input.setFixedWidth(220)
        self._find_input.textChanged.connect(self._find_text)
        self._find_input.returnPressed.connect(self._find_next)
        self._find_input.keyPressEvent = self._find_key_press
        lay.addWidget(self._find_input)

        for label, tip, slot in [
            ("▲", "Previous (Shift+Enter)", self._find_prev),
            ("▼", "Next (Enter)",           self._find_next),
        ]:
            btn = QPushButton(label)
            btn.setFixedWidth(28); btn.setToolTip(tip)
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        self._find_status = QLabel("")
        self._find_status.setStyleSheet("color: #888; font-size: 12px;")
        lay.addWidget(self._find_status)
        lay.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(28)
        close_btn.setToolTip("Close (Escape)")
        close_btn.clicked.connect(self._hide_find_bar)
        lay.addWidget(close_btn)

        bar.hide()
        return bar

    def _find_key_press(self, event):
        if event.key() == Qt.Key_Escape:
            self._hide_find_bar()
        elif event.key() == Qt.Key_Return and (event.modifiers() & Qt.ShiftModifier):
            self._find_prev()
        else:
            QLineEdit.keyPressEvent(self._find_input, event)

    def _show_find_bar(self):
        self._find_bar.show()
        self._find_input.setFocus()
        self._find_input.selectAll()

    def _hide_find_bar(self):
        self._find_bar.hide()
        self._find_input.clear()
        self._find_status.setText("")
        v = self._current_view()
        if v:
            v.findText("")
            v.setFocus()

    def _find_text(self, text: str):
        v = self._current_view()
        if v:
            v.findText(text)
            self._find_status.setText("")

    def _find_next(self):
        v = self._current_view()
        if v:
            v.findText(self._find_input.text())

    def _find_prev(self):
        v = self._current_view()
        if v:
            v.findText(self._find_input.text(), QWebEnginePage.FindBackward)

    # ── Zoom ──────────────────────────────────────────────────────────────────

    def _zoom_in(self):
        v = self._current_view()
        if v:
            v.setZoomFactor(min(round(v.zoomFactor() + 0.1, 1), 3.0))
            self.status.showMessage(f"Zoom: {int(v.zoomFactor() * 100)}%", 2000)

    def _zoom_out(self):
        v = self._current_view()
        if v:
            v.setZoomFactor(max(round(v.zoomFactor() - 0.1, 1), 0.3))
            self.status.showMessage(f"Zoom: {int(v.zoomFactor() * 100)}%", 2000)

    def _zoom_reset(self):
        v = self._current_view()
        if v:
            v.setZoomFactor(1.0)
            self.status.showMessage("Zoom: 100%", 2000)

    # ── Tab helpers ───────────────────────────────────────────────────────────

    def _next_tab(self):
        self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % self.tabs.count())

    def _prev_tab(self):
        self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % self.tabs.count())

    # ── Labels ────────────────────────────────────────────────────────────────

    def _tor_label(self):
        if self._tor_enabled and self._tor_ok: return "🧅 Tor: ON"
        if self._tor_enabled:                  return "⚠ Tor: ERROR"
        return "🔓 Tor: OFF"

    def _ks_label(self):
        return "🛡 Kids: ON" if self.config.get("kidshield", {}).get("enabled") else "🛡 Kids: OFF"

    def _update_status(self):
        parts = ["Private mode"]
        if self._tor_enabled and self._tor_ok:
            parts.append("Tor active")
        elif self._tor_enabled:
            parts.append("Tor FAILED")
        if self.config.get("kidshield", {}).get("enabled"):
            parts.append("KidShield ON")
        parts.append(self._engine["label"])
        self.status.showMessage(" — ".join(parts))

    # ── Search engine switching ───────────────────────────────────────────────

    def _on_engine_changed(self, _):
        key = self.engine_combo.currentData()
        self.config["search_engine"] = key
        save_config(self.config)
        if key == "pebble":
            _ensure_pebble_server(self._tor_ok)
        self._update_status()

    # ── KidShield ─────────────────────────────────────────────────────────────

    def _open_ks_settings(self):
        dlg = KidShieldDialog(self.config.get("kidshield", DEFAULT_CONFIG["kidshield"]), self)
        if dlg.exec_() == QDialog.Accepted:
            self.config["kidshield"] = dlg.get_settings()
            save_config(self.config)
            self.ks_act.setText(self._ks_label())
            self._update_status()

    def _inject_kidshield(self, view: BrowserTab, reset: bool = False):
        ks = self.config.get("kidshield", {})
        if not ks.get("enabled") or not KIDSHIELD_SRC:
            return
        js = f"window.__pebbleKidshield = {json.dumps(ks)};"
        if reset:
            js += "window.__kidshieldActive=false;if(window.__kidshieldClear)window.__kidshieldClear();"
        view.page().runJavaScript(js + KIDSHIELD_SRC)

    def _schedule_ks(self, view: BrowserTab):
        if hasattr(view, "_ks_timer") and view._ks_timer:
            view._ks_timer.stop()
        t = QTimer(self); t.setSingleShot(True)
        t.timeout.connect(lambda: self._inject_kidshield(view, reset=True))
        t.start(1800); view._ks_timer = t

    # ── Tabs ──────────────────────────────────────────────────────────────────

    def new_tab(self) -> BrowserTab:
        view = BrowserTab(self.profile, self, self._engine["home"])
        idx  = self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentIndex(idx)
        view._ks_timer = None
        view.titleChanged.connect(lambda t, v=view: self._update_tab_title(v, t))
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(v, u))
        view.loadStarted.connect(lambda v=view: self._on_load_started(v))
        view.loadProgress.connect(lambda p, v=view: self._on_load_progress(v, p))
        view.loadFinished.connect(lambda ok, v=view: self._on_load_finished(v, ok))
        return view

    def open_in_new_tab(self, url):
        view = self.new_tab()
        view.load(url if isinstance(url, QUrl) else QUrl(url))

    def _current_view(self):
        return self.tabs.currentWidget()

    def _update_tab_title(self, view, title):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            self.tabs.setTabText(idx, (title[:28] + "…") if len(title) > 30 else (title or "New Tab"))
            if view is self._current_view():
                self.setWindowTitle(f"{title} — Pebble")

    def _on_url_changed(self, view, url):
        if view is self._current_view():
            self.url_bar.setText(url.toString())
        self._schedule_ks(view)

    def _on_load_started(self, view):
        if view is self._current_view():
            self.status.showMessage("Loading…")
            self._progress.setValue(0)
            self._progress.show()

    def _on_load_progress(self, view, progress):
        if view is self._current_view():
            self._progress.setValue(progress)

    def _on_load_finished(self, view, ok):
        if view is self._current_view():
            self._progress.hide()
            self._update_status()
            self.status.showMessage(view.url().toString())
        if ok:
            if hasattr(view, "_ks_timer") and view._ks_timer:
                view._ks_timer.stop()
            self._inject_kidshield(view)

    def _on_tab_changed(self, idx):
        view = self.tabs.widget(idx)
        if view:
            self.url_bar.setText(view.url().toString())
            self.setWindowTitle(f"{view.title() or 'New Tab'} — Pebble")
            self._progress.hide()
            self._update_status()

    def _close_tab(self, idx):
        if self.tabs.count() > 1:
            self.tabs.removeTab(idx)
        else:
            self._current_view().load(QUrl(self._engine["home"]))

    def _close_current_tab(self):
        self._close_tab(self.tabs.currentIndex())

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate_from_bar(self):
        v = self._current_view()
        if v: v.navigate(self.url_bar.text(), self._engine["search_url"])

    def _focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def _go_back(self):
        v = self._current_view()
        if v: v.back()

    def _go_forward(self):
        v = self._current_view()
        if v: v.forward()

    def _reload(self):
        v = self._current_view()
        if v: v.reload()

    def _hard_reload(self):
        v = self._current_view()
        if v: v.page().triggerAction(QWebEnginePage.ReloadAndBypassCache)

    def _go_home(self):
        v = self._current_view()
        if v: v.load(QUrl(self._engine["home"]))

    # ── Tor toggle ────────────────────────────────────────────────────────────

    def _toggle_tor(self):
        new_state = not self._tor_enabled
        reply = QMessageBox.question(self, "Toggle Tor",
            f"Turn Tor {'ON' if new_state else 'OFF'}?\n\nPebble will restart to apply this change.",
            QMessageBox.Ok | QMessageBox.Cancel)
        if reply != QMessageBox.Ok: return
        self.config["tor_enabled"] = new_state
        save_config(self.config)
        os.execv(sys.executable, [sys.executable] + sys.argv)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    tor_enabled = config.get("tor_enabled", True)
    tor_ok      = ensure_tor() if tor_enabled else False

    if config.get("search_engine", "brave") == "pebble":
        _ensure_pebble_server(tor_ok)

    app = QApplication(sys.argv)
    app.setApplicationName("Pebble")
    app.setFont(QFont("Sans", 11))
    w = Pebble(tor_enabled=tor_enabled, tor_ok=tor_ok)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
