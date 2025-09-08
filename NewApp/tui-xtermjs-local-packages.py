#!/usr/bin/env python3
# tui-xtermjs.py — Qt (PySide6) GUI with left-rail setup + embedded xterm.js (local assets w/ CDN fallback)

import asyncio
import json
import signal
import sys
import threading
import time
import os

import serial
import serial.tools.list_ports
import websockets

from PySide6.QtCore import Qt, QSize, QEvent, QUrl
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QCheckBox, QSpinBox, QFrame
)
from PySide6.QtWebEngineWidgets import QWebEngineView
try:
    # Qt ≥ 6.6 exposes ShowScrollBars via QWebEngineSettings (widgets)
    from PySide6.QtWebEngineCore import QWebEngineSettings
except Exception:
    QWebEngineSettings = None

# ---------------- Config ----------------
WS_HOST = "127.0.0.1"
WS_PORT = 8765
FIXED_BAUD = 115200

# Local assets directory (created by get_xterm_assets.py)
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "xterm")
REQUIRED_ASSETS = ["xterm.js", "xterm.css", "xterm-addon-fit.js"]

def have_local_assets() -> bool:
    try:
        for n in REQUIRED_ASSETS:
            if not os.path.isfile(os.path.join(ASSETS_DIR, n)):
                return False
        return True
    except Exception:
        return False

# ---------------- Serial bridge ----------------
class SerialBridge:
    def __init__(self):
        self.ser = None
        self.lock = threading.Lock()
        self.reader_th = None
        self.stop_ev = threading.Event()
        self.loop = None
        self.clients = set()

    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def open(self, port: str, baud: int):
        with self.lock:
            if self.is_open():
                try: self.ser.close()
                except Exception: pass
                self.ser = None
            self.stop_ev.clear()
            try:
                self.ser = serial.Serial(port=port, baudrate=baud, timeout=0)
                # DTR/RTS nudge + wake with CR (best-effort)
                try:
                    self.ser.setDTR(False); self.ser.setRTS(False); time.sleep(0.05)
                    self.ser.setDTR(True);  self.ser.setRTS(True)
                    self.ser.write(b"\r"); self.ser.flush()
                except Exception:
                    pass
            except Exception as e:
                self.ser = None
                raise e
            self.reader_th = threading.Thread(target=self._reader_loop, daemon=True)
            self.reader_th.start()

    def close(self):
        with self.lock:
            self.stop_ev.set()
            if self.reader_th and self.reader_th.is_alive():
                self.reader_th.join(timeout=0.2)
            self.reader_th = None
            if self.ser:
                try: self.ser.close()
                except Exception: pass
            self.ser = None

    def write(self, data: bytes):
        with self.lock:
            if not self.is_open():
                return
            try:
                self.ser.write(data); self.ser.flush()
            except Exception:
                pass

    async def broadcast(self, payload: bytes):
        if not self.clients:
            return
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send(payload)  # binary
            except Exception:
                dead.append(ws)
        for d in dead:
            self.clients.discard(d)

    def _reader_loop(self):
        while not self.stop_ev.is_set():
            try:
                if not self.is_open():
                    time.sleep(0.01); continue
                data = self.ser.read(4096)
                if data and self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.broadcast(data), self.loop)
                else:
                    time.sleep(0.002)
            except Exception:
                time.sleep(0.02)

SER = SerialBridge()

# ---------------- WebSocket server ----------------
async def _ws_handler_impl(websocket):
    SER.clients.add(websocket)
    try:
        await websocket.send(json.dumps({"type": "status", "message": "WS connected", "connected": SER.is_open()}))
        async for msg in websocket:
            if isinstance(msg, (bytes, bytearray)):
                if SER.is_open(): SER.write(bytes(msg))
                continue
            try:
                obj = json.loads(msg)
            except Exception:
                if SER.is_open(): SER.write(msg.replace("\n", "\r").encode("utf-8", "ignore"))
                continue
            t = obj.get("type")
            if t == "tx":
                data = obj.get("data", "")
                if SER.is_open() and data:
                    SER.write(data.replace("\n", "\r").encode("utf-8", "ignore"))
            elif t == "resize":
                pass
    finally:
        SER.clients.discard(websocket)

async def ws_handler(*args):
    websocket = args[0]
    return await _ws_handler_impl(websocket)

def start_ws_server(loop_ready_evt: threading.Event):
    async def runner():
        SER.loop = asyncio.get_running_loop()
        async with websockets.serve(ws_handler, WS_HOST, WS_PORT, max_size=None):
            loop_ready_evt.set()
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                pass
    asyncio.run(runner())

# ---------------- xterm.js HTML ----------------
def index_html(use_local: bool):
    """
    If use_local=True: expect 'xterm.css', 'xterm.js', 'xterm-addon-fit.js' to be served from baseUrl.
    Otherwise: use CDN URLs.
    """
    if use_local:
        css_href  = "xterm.css"
        js_xterm  = "xterm.js"
        js_fit    = "xterm-addon-fit.js"
        js_image  = "xterm-addon-image.js"
    else:
        css_href  = "https://unpkg.com/xterm@5.3.0/css/xterm.css"
        js_xterm  = "https://unpkg.com/xterm@5.3.0/lib/xterm.js"
        js_fit    = "https://unpkg.com/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"
        js_image  = "https://unpkg.com/xterm-addon-image@0.1.0/lib/xterm-addon-image.js"
    
    # Generate font face definitions for local fonts
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    font_faces = ""
    if os.path.exists(fonts_dir):
        try:
            # Map filenames to their actual font family names
            font_mapping = {
                "BerkeleyMono-Regular.ttf": "BerkeleyMonoTrial Nerd Font Mono",
                "BerkeleyMono.ttf": "Berkeley Mono Trial", 
                "IntoneMonoNerdFontMono-Light.ttf": "IntoneMono Nerd Font Mono",
                "IosevkaSS08-Regular.ttf": "Iosevka SS08",
                "Jokerman.ttf": "Jokerman",
                "SpaceMonoNerdFontMono-Regular.ttf": "SpaceMono Nerd Font Mono"
            }
            
            for filename in os.listdir(fonts_dir):
                if filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                    # Use the actual font family name if we have a mapping, otherwise fall back to filename
                    font_family_name = font_mapping.get(filename, os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title())
                    # Create font face definition
                    font_faces += f"""
    @font-face {{
        font-family: '{font_family_name}';
        src: url('../fonts/{filename}');
        font-display: swap;
    }}"""
        except Exception:
            pass
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Jumperless – xterm.js</title>
<link rel="stylesheet" href="{css_href}">
<style>
{font_faces}
  html, body {{
    height:100%; width:100%; margin:0; padding:0; background:#0f1115; color:#e6e6e6;
    overflow:hidden !important;
  }}
  /* Hide Chromium/WebKit scrollbars just in case */
  *::-webkit-scrollbar {{ width:0 !important; height:0 !important; display:none !important; }}
  * {{ scrollbar-width:none !important; }}
  #termwrap {{
    position:fixed; inset:0; padding:0; box-sizing:border-box; overflow:hidden !important;
  }}
  #terminal {{ width:100%; height:100%; overflow:hidden !important; }}
  .xterm .xterm-viewport {{ overflow:hidden !important; }}
  .xterm .xterm-viewport::-webkit-scrollbar {{
    width:0 !important; height:0 !important; display:none !important;
  }}
</style>
</head>
<body>
  <div id="termwrap"><div id="terminal"></div></div>

  <script src="{js_xterm}"></script>
  <script src="{js_fit}"></script>
  <script>
    const WS_URL = "ws://{WS_HOST}:{WS_PORT}";
    const term = new Terminal({{
      cursorBlink: true,
      fontFamily: "Iosevka SS08, JetBrains Mono, 'DejaVu Sans Mono', Menlo, Consolas, monospace",
      fontSize: 14,
      letterSpacing: 0,
      lineHeight: 1.0,
      theme: {{
        background: "#0f1115",
        foreground: "#e6e6e6",
        cursor: "#8ab4f8",
        selectionBackground: "#244580",
      }},
      scrollback: 5000,
      convertEol: false
    }});
    const fitAddon = new FitAddon.FitAddon();
    window.term = term;
    window.fitAddon = fitAddon;
    term.loadAddon(fitAddon);
    term.open(document.getElementById("terminal"));
    fitAddon.fit();

    let ws = null;

    function connectWS() {{
      if (ws && ws.readyState === WebSocket.OPEN) return;
      ws = new WebSocket(WS_URL);
      ws.binaryType = "arraybuffer";
      const utf8 = new TextDecoder('utf-8', {{ fatal: false }});

      ws.onmessage = (ev) => {{
        if (ev.data instanceof ArrayBuffer) {{
          const s = utf8.decode(new Uint8Array(ev.data), {{ stream: true }});
          if (s) term.write(s);
          return;
        }}
      }};
      ws.onopen = () => {{}};
      ws.onclose = () => {{
        try {{ const tail = utf8.decode(); if (tail) term.write(tail); }} catch(_) {{}}
      }};
      ws.onerror = () => {{}};

      term.onData(data => {{
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        ws.send(JSON.stringify({{type:"tx", data}}));
      }});

      const refit = () => {{
        if (window.fitAddon) window.fitAddon.fit();
        term.refresh(0, term.rows - 1);
      }};
      window.addEventListener("resize", refit);
      new ResizeObserver(refit).observe(document.getElementById("termwrap"));

      term.onResize(e => {{
        if (ws && ws.readyState === WebSocket.OPEN) {{
          ws.send(JSON.stringify({{type:"resize", cols:e.cols, rows:e.rows}}));
        }}
      }});
    }}

    connectWS();
    term.focus();
  </script>
</body>
</html>
"""

# ---------------- Qt UI ----------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jumperless – Qt + xterm.js")
        self.resize(1200, 800)

        # Start WS server thread
        ready = threading.Event()
        t = threading.Thread(target=start_ws_server, args=(ready,), daemon=True)
        t.start()
        ready.wait(timeout=3.0)

        # Central split: left rail (setup), right (webview)
        root = QWidget(self)
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(10, 10, 10, 10)
        h.setSpacing(10)

        # ---- Left sidebar (compact) ----
        rail = QFrame(self)
        rail.setFrameShape(QFrame.StyledPanel)
        rail.setProperty("role", "rail")  # for stylesheet targeting
        rail.setMinimumWidth(210)
        rail.setMaximumWidth(260)
        v = QVBoxLayout(rail)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        title = QLabel("Setup", rail)
        title.setObjectName("title")
        v.addWidget(title)

        # Port row
        port_lbl = QLabel("Port:", rail)
        self.port_combo = QComboBox(rail)
        self.port_combo.setMinimumContentsLength(16)
        port_bar = QHBoxLayout()
        port_bar.setSpacing(6)
        port_bar.addWidget(port_lbl)
        port_bar.addWidget(self.port_combo, 1)
        v.addLayout(port_bar)

        # Buttons
        btn_row_top = QHBoxLayout()
        self.btn_rescan = QPushButton("Rescan", rail); self.btn_rescan.setObjectName("rescan")
        btn_row_top.addWidget(self.btn_rescan)
        v.addLayout(btn_row_top)

        btn_row = QHBoxLayout()
        self.btn_connect = QPushButton("Connect", rail);   self.btn_connect.setObjectName("connect")
        self.btn_disconnect = QPushButton("Disconnect", rail); self.btn_disconnect.setObjectName("disconnect")
        # Wider Disconnect
        fm = self.btn_disconnect.fontMetrics()
        self.btn_disconnect.setMinimumWidth(fm.horizontalAdvance("Disconnect") + 12)
        # Uniform heights
        for b in (self.btn_rescan, self.btn_connect, self.btn_disconnect):
            b.setMinimumHeight(30)
        btn_row.addWidget(self.btn_connect)
        btn_row.addWidget(self.btn_disconnect)
        v.addLayout(btn_row)

        # Toggle size (maximize/restore)
        self.btn_toggle = QPushButton("Toggle Size", rail); self.btn_toggle.setObjectName("toggle")
        self.btn_toggle.setToolTip("Toggle maximize/restore (like double-clicking the title bar)")
        v.addWidget(self.btn_toggle)

        # Toggles
        self.chk_app_dark  = QCheckBox("App dark theme", rail);   self.chk_app_dark.setChecked(True)
        self.chk_term_dark = QCheckBox("Terminal dark", rail);    self.chk_term_dark.setChecked(True)
        v.addWidget(self.chk_app_dark)
        v.addWidget(self.chk_term_dark)

        # Font size
        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font Size:", rail))
        self.spin_font = QSpinBox(rail)
        self.spin_font.setRange(8, 26)
        self.spin_font.setValue(14)
        self.spin_font.setSingleStep(1)
        self.spin_font.setFixedWidth(84)
        font_row.addWidget(self.spin_font)
        font_row.addStretch()
        v.addLayout(font_row)

        # Font family
        font_family_row = QHBoxLayout()
        font_family_row.addWidget(QLabel("Font Family:", rail))
        self.combo_font_family = QComboBox(rail)
        self.combo_font_family.setMinimumContentsLength(20)
        font_family_row.addWidget(self.combo_font_family, 1)
        v.addLayout(font_family_row)

        v.addStretch()

        # Status
        self.lbl_status = QLabel("Ready", rail)
        self.lbl_status.setObjectName("status")
        self.lbl_status.setWordWrap(True)
        v.addWidget(self.lbl_status)

        # ---- Right: xterm.js view ----
        self.view = QWebEngineView(self)
        # Try to disable Chromium scrollbars at the engine level (Qt 6.6+)
        try:
            if QWebEngineSettings is not None and hasattr(QWebEngineSettings, "ShowScrollBars"):
                QWebEngineSettings.defaultSettings().setAttribute(QWebEngineSettings.ShowScrollBars, False)
                self.view.page().settings().setAttribute(QWebEngineSettings.ShowScrollBars, False)
        except Exception:
            pass

        h.addWidget(rail)
        h.addWidget(self.view, 1)

        # Decide local vs CDN and load terminal page
        self._use_local = have_local_assets()
        html = index_html(self._use_local)
        if self._use_local:
            base = QUrl.fromLocalFile(os.path.abspath(ASSETS_DIR) + os.sep)
        else:
            base = QUrl("https://local/")
        self.view.setHtml(html, baseUrl=base)
        self.view.loadFinished.connect(self._after_page_loaded)

        # Wire up actions
        self.btn_rescan.clicked.connect(self._rescan_ports)
        self.btn_connect.clicked.connect(self._connect_serial)
        self.btn_disconnect.clicked.connect(self._disconnect_serial)
        self.btn_toggle.clicked.connect(self._toggle_titlebar_action)

        self.chk_app_dark.toggled.connect(self._apply_app_theme)
        self.chk_term_dark.toggled.connect(self._apply_term_theme)
        self.spin_font.valueChanged.connect(self._apply_term_font)
        self.combo_font_family.currentTextChanged.connect(self._apply_term_font_family)

        # Initial ports fill
        self._rescan_ports()

        # Populate font family dropdown
        self._populate_font_families()

        # Apply initial app theme
        self._apply_app_theme(self.chk_app_dark.isChecked())

        # Let user know which asset source we used
        src = "local assets" if self._use_local else "CDN"
        self._set_status(f"Terminal assets: {src}")

    # ---------- helpers ----------
    def _run_js(self, script: str):
        try:
            self.view.page().runJavaScript(script)
        except Exception:
            pass

    def _set_status(self, msg: str, ok: bool | None = None):
        if ok is True:
            self.lbl_status.setStyleSheet("color:#98e6a7;")
        elif ok is False:
            self.lbl_status.setStyleSheet("color:#ff9aa2;")
        else:
            # keep theme color via stylesheet; avoid overriding too much
            pass
        self.lbl_status.setText(msg)

    def _rescan_ports(self):
        items = []
        try:
            for p in serial.tools.list_ports.comports():
                items.append((p.device, p.description or ""))
        except Exception:
            items = []
        self.port_combo.clear()
        for dev, desc in items:
            text = f"{dev} — {desc}" if desc else dev
            self.port_combo.addItem(text, userData=dev)
        if self.port_combo.count() == 0:
            self.port_combo.addItem("(no ports)", userData=None)

    def _connect_serial(self):
        dev = self.port_combo.currentData()
        if not dev:
            self._set_status("No serial ports found.", ok=False)
            return
        try:
            SER.open(dev, FIXED_BAUD)
            self._set_status(f"Connected: {dev} @ {FIXED_BAUD}", ok=True)
            self._run_js("if (window.term) term.focus();")
        except Exception as e:
            self._set_status(f"Open failed: {e}", ok=False)

    def _disconnect_serial(self):
        try:
            SER.close()
            self._set_status("Serial disconnected.", ok=False)
        except Exception:
            pass

    def _toggle_titlebar_action(self):
        # Emulate title-bar double-click: maximize <-> restore
        ws = self.windowState()
        if ws & Qt.WindowMaximized or ws & Qt.WindowFullScreen:
            self.showNormal()
        else:
            self.showMaximized()
        # Nudge xterm.js to refit and repaint
        self._run_js("""
            (function(){
              if (window.fitAddon) window.fitAddon.fit();
              if (window.term) term.refresh(0, term.rows - 1);
            })();
        """)

    def _after_page_loaded(self, ok: bool):
        # Apply initial terminal theme & font
        self._apply_term_theme(self.chk_term_dark.isChecked())
        self._apply_term_font(self.spin_font.value())
        self._apply_term_font_family(self.combo_font_family.currentText())
        # Ensure terminal is focused
        self._run_js("if (window.term) term.focus();")

    def _apply_term_theme(self, checked: bool):
        if checked:
            js = """
              (function(){
                if (window.term) {
                  term.options.theme = {
                    background: '#0f1115',
                    foreground: '#e6e6e6',
                    cursor: '#8ab4f8',
                    selectionBackground: '#244580'
                  };
                  if (window.fitAddon) window.fitAddon.fit();
                  term.refresh(0, term.rows - 1);
                }
              })();
            """
        else:
            js = """
              (function(){
                if (window.term) {
                  term.options.theme = {
                    background: '#ffffff',
                    foreground: '#0b0d12',
                    cursor: '#333333',
                    selectionBackground: '#cfe3ff'
                  };
                  if (window.fitAddon) window.fitAddon.fit();
                  term.refresh(0, term.rows - 1);
                }
              })();
            """
        self._run_js(js)

    def _apply_term_font(self, size: int):
        js = f"""
          (function(){{
            if (window.term) {{
              term.options.fontSize = {int(size)};
              if (window.fitAddon) window.fitAddon.fit();
              term.refresh(0, term.rows - 1);
            }}
          }})();
        """
        self._run_js(js)

    def _populate_font_families(self):
        """Populate the font family dropdown with local fonts and system defaults."""
        fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
        
        # Add system default fonts first
        default_fonts = [
            "DejaVu Sans Mono", 
            "Menlo",
            "monospace"
        ]
        
        for font in default_fonts:
            self.combo_font_family.addItem(font)
        
        # Add local fonts if they exist
        if os.path.exists(fonts_dir):
            try:
                # Map filenames to their actual font family names
                font_mapping = {
                    "IntoneMonoNerdFontMono-Light.ttf": "IntoneMono Nerd Font Mono",
                    "IosevkaSS08-Regular.ttf": "Iosevka SS08",
                    "Jokerman.ttf": "Jokerman",
                    "SpaceMonoNerdFontMono-Regular.ttf": "SpaceMono Nerd Font Mono"
                }
                
                for filename in os.listdir(fonts_dir):
                    if filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        # Use the actual font family name if we have a mapping, otherwise fall back to filename
                        font_name = font_mapping.get(filename, os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title())
                        self.combo_font_family.addItem(font_name)
            except Exception:
                pass
        
        # Set default selection to Iosevka SS08
        default_index = self.combo_font_family.findText("Iosevka SS08")
        if default_index >= 0:
            self.combo_font_family.setCurrentIndex(default_index)

    def _apply_term_font_family(self, font_family: str):
        """Apply the selected font family to the terminal."""
        js = f"""
          (function(){{
            if (window.term) {{
              term.options.fontFamily = "{font_family}";
              if (window.fitAddon) window.fitAddon.fit();
              term.refresh(0, term.rows - 1);
            }}
          }})();
        """
        self._run_js(js)

    def _apply_app_theme(self, dark: bool):
        # Modern, readable UI + visible spin arrows
        if dark:
            sheet = """
                QWidget { background:#0f1115; color:#e6e6e6; }
                QFrame[role="rail"] { background:#151821; border:1px solid #22252f; border-radius:8px; }
                QLabel#title { font-weight:600; }
                QLabel#status { color:#8ab4f8; }
                QComboBox, QLineEdit {
                    background:#0f1115; color:#e6e6e6;
                    border:1px solid #333844; border-radius:6px; padding:6px;
                }
                QComboBox QAbstractItemView {
                    background:#151821; color:#e6e6e6; selection-background-color:#244580;
                    border:1px solid #333844;
                }
                QPushButton {
                    background:#2a2f3a; color:#e6e6e6;
                    border:1px solid #333844; border-radius:6px; padding:6px 10px;
                }
                QPushButton:hover { border-color:#4b9cff; }
                QPushButton#rescan { background:#2b7cff; color:#fff; border:none; }
                QPushButton#connect { background:#4caf50; color:#fff; border:none; }
                QPushButton#disconnect { background:#e74c3c; color:#fff; border:none; }
                QPushButton#toggle { background:#8a64ff; color:#fff; border:none; }

                QCheckBox::indicator { width:16px; height:16px; }

                QSpinBox {
                    background:#0f1115; color:#e6e6e6;
                    border:1px solid #333844; border-radius:6px;
                    padding-left:8px; padding-right:30px; min-height:28px;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    width:22px; border:1px solid #333844; background:#2a2f3a;
                    subcontrol-origin: border; border-radius:5px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover { background:#3a4250; }
            """
        else:
            sheet = """
                QWidget { background:#f6f7fb; color:#0b0d12; }
                QFrame[role="rail"] { background:#ffffff; border:1px solid #dcdfe6; border-radius:8px; }
                QLabel#title { font-weight:600; }
                QLabel#status { color:#1665d8; }
                QComboBox, QLineEdit {
                    background:#ffffff; color:#0b0d12;
                    border:1px solid #c7ccd8; border-radius:6px; padding:6px;
                }
                QComboBox QAbstractItemView {
                    background:#ffffff; color:#0b0d12; selection-background-color:#dfeaff;
                    border:1px solid #c7ccd8;
                }
                QPushButton {
                    background:#ffffff; color:#0b0d12;
                    border:1px solid #c7ccd8; border-radius:6px; padding:6px 10px;
                }
                QPushButton:hover { border-color:#1665d8; }
                QPushButton#rescan { background:#2b7cff; color:#fff; border:none; }
                QPushButton#connect { background:#4caf50; color:#fff; border:none; }
                QPushButton#disconnect { background:#e74c3c; color:#fff; border:none; }
                QPushButton#toggle { background:#8a64ff; color:#fff; border:none; }

                QCheckBox::indicator { width:16px; height:16px; }

                QSpinBox {
                    background:#ffffff; color:#0b0d12;
                    border:1px solid #c7ccd8; border-radius:6px;
                    padding-left:8px; padding-right:30px; min-height:28px;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    width:22px; border:1px solid #c7ccd8; background:#eef2f9;
                    subcontrol-origin: border; border-radius:5px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover { background:#e2ebff; }
            """
        self.setStyleSheet(sheet)

    def closeEvent(self, ev):
        try: SER.close()
        except Exception: pass
        super().closeEvent(ev)

# ---------------- bootstrap ----------------
def main():
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Jumperless – Qt + xterm.js")
    # IMPORTANT: No deprecated AA_UseHighDpiPixmaps here.

    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
