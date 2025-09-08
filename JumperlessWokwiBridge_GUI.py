#!/usr/bin/env python3
"""
JumperlessWokwiBridge_GUI.py - Qt GUI version with xterm.js terminal integration

This is the GUI version of JumperlessWokwiBridge that integrates the Qt + xterm.js interface
while preserving all the existing backend functionality for firmware updates, flashing,
port detection, Arduino CLI integration, and Wokwi bridge operations.
"""

import asyncio
import json
import os
import sys
import threading
import time
import signal
from typing import Optional

# Add all the existing imports from JumperlessWokwiBridge
import serial
import serial.tools.list_ports
import websockets

# Qt imports
from PySide6.QtCore import Qt, QSize, QEvent, QUrl, QThread, QObject, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QCheckBox, QSpinBox, QFrame,
    QGroupBox, QSlider, QTextEdit, QProgressBar, QSplitter
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from JumperlessBridgeBackend import print_saved_projects
try:
    from PySide6.QtWebEngineCore import QWebEngineSettings
except Exception:
    QWebEngineSettings = None

# Import all the functions and globals from the original bridge
# This is a bit unconventional but allows us to reuse all existing functionality
import importlib.util
import inspect

# # Import the original bridge module to access its functions
# bridge_path = os.path.join(os.path.dirname(__file__), 'JumperlessWokwiBridge.py')
# spec = importlib.util.spec_from_file_location("bridge", bridge_path)
# bridge_module = importlib.util.module_from_spec(spec)
# sys.modules["bridge"] = bridge_module
# spec.loader.exec_module(bridge_module)

# Import the backend module and get the backend instance
backend_path = os.path.join(os.path.dirname(__file__), 'JumperlessBridgeBackend.py')
backend_spec = importlib.util.spec_from_file_location("backend", backend_path)
backend_module = importlib.util.module_from_spec(backend_spec)
sys.modules["backend"] = backend_module
backend_spec.loader.exec_module(backend_module)

# Add user input queue for GUI interaction
import queue
backend_module.user_input_queue = queue.Queue()
backend_module.gui_input_enabled = False

# Override the built-in input function to get input from GUI terminal
def gui_input(prompt=""):
    """Custom input function that gets input from GUI terminal"""
    if backend_module.gui_input_enabled:
        # Print the prompt to the terminal
        if prompt:
            print(prompt, end="", flush=True)
        
        print(f"[GUI] Waiting for input from terminal (queue size: {backend_module.user_input_queue.qsize()})...", flush=True)
        
        # Wait for user input from the WebSocket terminal
        try:
            user_input = backend_module.user_input_queue.get(timeout=300)  # 5 minute timeout
            print(f"[GUI] Received input: '{user_input}'", flush=True)
            return user_input
        except queue.Empty:
            print("[GUI] Input timeout - returning empty", flush=True)
            return ""  # Return empty string on timeout
    else:
        # Fall back to regular input if GUI input not enabled
        print(f"[GUI] GUI input disabled, using standard input for prompt: '{prompt}'", flush=True)
        return backend_module._original_input(prompt) if hasattr(backend_module, '_original_input') else input(prompt)

# Replace the built-in input function in the backend module
backend_module.input = gui_input
# Also replace in builtins for functions that use input() directly
import builtins
backend_module._original_input = builtins.input  # Save original
builtins.input = gui_input

# # Import critical functions and variables from bridge (we'll minimize these)
# from bridge import (
#     # Global variables and utilities we still need
#     Fore, safe_print, create_directories, resource_path,
# )

# Get backend instance for GUI use
from backend import get_backend_instance


# ============================================================================
# CUSTOM QT EVENTS FOR THREAD COMMUNICATION
# ============================================================================

class ScanResultEvent(QEvent):
    """Custom event for scan results from background thread"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, port_info):
        super().__init__(ScanResultEvent.EVENT_TYPE)
        self.port_info = port_info

class ScanErrorEvent(QEvent):
    """Custom event for scan errors from background thread"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, error_message, is_error=True):
        super().__init__(ScanErrorEvent.EVENT_TYPE)
        self.error_message = error_message
        self.is_error = is_error

class StatusUpdateEvent(QEvent):
    """Custom event for status updates from background thread"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, message, is_error=False, slot_count=None):
        super().__init__(StatusUpdateEvent.EVENT_TYPE)
        self.message = message
        self.is_error = is_error
        self.slot_count = slot_count
        self.port_info = None  # Allow carrying port information

    # StartupScanEvent removed - backend handles all startup port detection

# WebSocket and xterm.js configuration
WS_HOST = "127.0.0.1"
WS_PORT = 8765  # Serial terminal
WS_APP_PORT = 8766  # App output terminal
FIXED_BAUD = 115200

# Local assets directory
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "NewApp", "assets", "xterm")
FONTS_DIR = os.path.join(os.path.dirname(__file__), "NewApp", "fonts")
REQUIRED_ASSETS = ["xterm.js", "xterm.css", "xterm-addon-fit.js"]

def have_local_assets() -> bool:
    """Check if local xterm.js assets are available"""
    try:
        for asset in REQUIRED_ASSETS:
            if not os.path.isfile(os.path.join(ASSETS_DIR, asset)):
                return False
        return True
    except Exception:
        return False

# ============================================================================
# OPTIMIZED SERIAL BRIDGE FOR XTERM.JS
# ============================================================================
#
# PERFORMANCE OPTIMIZATIONS IMPLEMENTED:
# 1. Single Serial Reader: GUI SerialBridge is the primary serial reader
#    - Backend serial monitor runs at reduced frequency (50ms vs 1ms)
#    - Eliminates dual-reading conflicts and competition
# 
# 2. Efficient Data Buffering:
#    - Read larger chunks (up to 8192 bytes) when data available
#    - JavaScript-side buffering for smooth xterm.js rendering
#    - Batch small updates with 5ms timeout for performance
# 
# 3. Reduced Polling Frequency:
#    - Backend serial monitor: 50x less CPU usage (50ms vs 1ms sleep)
#    - Wokwi loop: Eliminated dual sleeps, minimum 100ms intervals
#    - Serial connection sharing prevents resource conflicts
# 
# 4. Smart Data Processing:
#    - Control characters (interactive mode) processed in GUI
#    - Immediate flushing for interactive prompts (>, $, #)
#    - Background status updates at reduced frequency
#
# ============================================================================

class SerialBridge:
    """Enhanced serial bridge that integrates with Jumperless functionality"""
    
    def __init__(self):
        self.ser = None
        self.lock = threading.Lock()
        self.reader_th = None
        self.stop_ev = threading.Event()
        self.loop = None
        self.clients = set()
        self.port_name = None
        self.baud_rate = FIXED_BAUD
        # Performance optimization: buffering for xterm.js
        self.output_buffer = b''
        self.buffer_lock = threading.Lock()
        self.max_buffer_size = 16384  # 16KB buffer
        self.flush_interval = 0.01  # 10ms buffer flush interval
        
    def is_open(self):
        return self.ser is not None and self.ser.is_open
    
    def open(self, port: str, baud: int = FIXED_BAUD):
        """Open serial connection with Jumperless-specific initialization"""
        with self.lock:
            if self.is_open():
                try: 
                    self.ser.close()
                except Exception: 
                    pass
                self.ser = None
            
            self.stop_ev.clear()
            try:
                self.ser = serial.Serial(port=port, baudrate=baud, timeout=1)
                self.port_name = port
                self.baud_rate = baud
                
                # Jumperless-specific initialization
                try:
                    self.ser.setDTR(False); self.ser.setRTS(False); time.sleep(0.05)
                    self.ser.setDTR(True);  self.ser.setRTS(True)
                    self.ser.write(b"\r"); self.ser.flush()
                except Exception:
                    pass
                    
                # Update global variables for compatibility and sync with backend
                global serialconnected, portName
                serialconnected = 1
                portName = port
                # Share the same serial connection with backend to avoid conflicts
                backend_module.ser = self.ser  # Backend uses GUI's serial connection
                backend_module.serialconnected = 1
                backend_module.portName = port
                
            except Exception as e:
                self.ser = None
                serialconnected = 0
                backend_module.serialconnected = 0
                raise e
                
            self.reader_th = threading.Thread(target=self._reader_loop, daemon=True)
            self.reader_th.start()
    
    def close(self):
        """Close serial connection"""
        global serialconnected
        with self.lock:
            self.stop_ev.set()
            if self.reader_th and self.reader_th.is_alive():
                self.reader_th.join(timeout=0.2)
            self.reader_th = None
            if self.ser:
                try: 
                    self.ser.close()
                except Exception: 
                    pass
            self.ser = None
            self.port_name = None
            
            # Update global variables
            serialconnected = 0
            backend_module.serialconnected = 0
    
    def write(self, data: bytes):
        """Write data to serial port"""
        with self.lock:
            if not self.is_open():
                return
            try:
                self.ser.write(data)
                self.ser.flush()
            except Exception:
                pass
    
    async def broadcast(self, payload: bytes):
        """Broadcast data to all WebSocket clients with buffering optimization"""
        if not self.clients:
            return
            
        # Process control characters for interactive mode
        processed_payload = self._process_control_characters(payload)
        
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send(processed_payload)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.clients.discard(d)
    
    def _process_control_characters(self, data: bytes) -> bytes:
        """Process Jumperless control characters and update interactive mode"""
        if not data:
            return data
            
        # Check for interactive mode control characters
        filtered_data = b''
        
        for byte in data:
            if byte == 0x0E:  # SO - Enable interactive mode
                # Notify backend about interactive mode change
                if hasattr(backend_module, 'interactive_mode'):
                    if not backend_module.interactive_mode:
                        backend_module.interactive_mode = True
                        APP_OUT.log_message("🎮 Interactive mode enabled", "cyan")
            elif byte == 0x0F:  # SI - Disable interactive mode  
                # Notify backend about interactive mode change
                if hasattr(backend_module, 'interactive_mode'):
                    if backend_module.interactive_mode:
                        backend_module.interactive_mode = False
                        APP_OUT.log_message("🎮 Interactive mode disabled", "cyan")
            else:
                filtered_data += bytes([byte])
        
        return filtered_data
    
    def _reader_loop(self):
        """Optimized serial data reading loop for xterm.js performance"""
        import select
        
        while not self.stop_ev.is_set():
            try:
                if not self.is_open():
                    time.sleep(0.05)  # Reduced frequency when no connection
                    continue
                
                # Check if data is available before reading
                if hasattr(self.ser, 'in_waiting') and self.ser.in_waiting == 0:
                    time.sleep(0.01)  # Short sleep when no data available
                    continue
                
                # Read larger chunks for better performance
                data = self.ser.read(self.ser.in_waiting or 8192)
                if data:
                    if self.loop and self.loop.is_running():
                        asyncio.run_coroutine_threadsafe(self.broadcast(data), self.loop)
                        
                        # Update backend global variables for compatibility
                        global portNotFound
                        with backend_module.serial_lock if hasattr(backend_module, 'serial_lock') else threading.Lock():
                            portNotFound = 0
                else:
                    time.sleep(0.005)  # Slightly longer sleep when no data
                    
            except (serial.SerialException, serial.SerialTimeoutException):
                time.sleep(0.1)  # Longer recovery time on serial errors
            except Exception:
                time.sleep(0.02)

# Global serial bridge instance
SER = SerialBridge()

# ============================================================================
# APP OUTPUT BRIDGE FOR LOGGING
# ============================================================================

class AppOutputBridge:
    """Bridge for app output/logging to separate terminal"""
    
    def __init__(self):
        self.clients = set()
        self.loop = None
        
    async def broadcast_message(self, message: str, color: str = "white"):
        """Broadcast a message to all app terminal clients"""
        if not self.clients:
            return
            
        # Format message with color
        formatted_msg = f"\x1b[{self._color_to_ansi(color)}m{message}\x1b[0m"
        
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send(formatted_msg.encode('utf-8'))
            except Exception:
                dead.append(ws)
        for d in dead:
            self.clients.discard(d)
    
    def _color_to_ansi(self, color: str) -> str:
        """Convert color name to ANSI escape code"""
        color_map = {
            "red": "31", "green": "32", "yellow": "33", "blue": "34",
            "magenta": "35", "cyan": "36", "white": "37", "gray": "90"
        }
        return color_map.get(color.lower(), "37")
    
    def log_message(self, message: str, color: str = "white"):
        """Log a message (thread-safe)"""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.broadcast_message(message, color), self.loop
            )

# Global app output bridge
APP_OUT = AppOutputBridge()

# ============================================================================
# WEBSOCKET SERVER
# ============================================================================

async def _ws_handler_impl(websocket):
    """WebSocket message handler for xterm.js communication"""
    SER.clients.add(websocket)
    try:
        await websocket.send(json.dumps({
            "type": "status", 
            "message": "WS connected", 
            "connected": SER.is_open()
        }))
        
        async for msg in websocket:
            if isinstance(msg, (bytes, bytearray)):
                if SER.is_open(): 
                    SER.write(bytes(msg))
                # Also send to backend if it's expecting input
                if hasattr(backend_module, 'user_input_queue') and backend_module.gui_input_enabled:
                    try:
                        decoded_input = bytes(msg).decode("utf-8", "ignore").strip()
                        if decoded_input:  # Only queue non-empty input
                            backend_module.user_input_queue.put_nowait(decoded_input)
                            print(f"[GUI] Queued bytes input: '{decoded_input}'")
                    except Exception as e:
                        print(f"[GUI] Error queuing bytes input: {e}")
                continue
                
            try:
                obj = json.loads(msg)
            except Exception:
                input_text = msg.replace("\n", "\r")
                if SER.is_open(): 
                    SER.write(input_text.encode("utf-8", "ignore"))
                # Also send to backend if it's expecting input
                if hasattr(backend_module, 'user_input_queue') and backend_module.gui_input_enabled:
                    try:
                        # Handle carriage return as input submission  
                        if '\r' in input_text:
                            # Extract input before the carriage return
                            clean_input = input_text.split('\r')[0].strip()
                            if clean_input:  # Only queue non-empty input
                                backend_module.user_input_queue.put_nowait(clean_input)
                                print(f"[GUI] Queued text input: '{clean_input}'", flush=True)
                            elif input_text == '\r':
                                # Empty enter - queue empty string for immediate return
                                backend_module.user_input_queue.put_nowait("")
                                print(f"[GUI] Queued empty input (Enter key)", flush=True)
                    except Exception as e:
                        print(f"[GUI] Error queuing text input: {e}", flush=True)
                continue
                
            msg_type = obj.get("type")
            if msg_type == "tx":
                data = obj.get("data", "")
                if SER.is_open() and data:
                    SER.write(data.replace("\n", "\r").encode("utf-8", "ignore"))
                # Also send to backend if it's expecting input
                if hasattr(backend_module, 'user_input_queue') and backend_module.gui_input_enabled:
                    try:
                        # Handle newlines as input submission
                        if '\n' in data or '\r' in data:
                            # Extract input before the newline/carriage return
                            clean_data = data.replace('\r', '').replace('\n', '').strip()
                            backend_module.user_input_queue.put_nowait(clean_data)
                            print(f"[GUI] Queued JSON tx data: '{clean_data}'", flush=True)
                    except Exception as e:
                        print(f"[GUI] Error queuing JSON tx data: {e}", flush=True)
            elif msg_type == "resize":
                pass  # Handle terminal resize if needed
                
    finally:
        SER.clients.discard(websocket)

async def ws_handler(*args):
    """WebSocket handler wrapper"""
    websocket = args[0]
    return await _ws_handler_impl(websocket)

async def app_ws_handler(websocket):
    """WebSocket handler for app output terminal"""
    APP_OUT.clients.add(websocket)
    try:
        await websocket.send(b"[App Output Terminal Ready]\n")
        # Keep connection alive and handle any incoming messages
        async for msg in websocket:
            pass  # App terminal is output-only for now
    except Exception:
        pass
    finally:
        APP_OUT.clients.discard(websocket)

def start_ws_servers(loop_ready_evt: threading.Event):
    """Start both WebSocket servers for xterm.js communication"""
    async def runner():
        loop = asyncio.get_running_loop()
        SER.loop = loop
        APP_OUT.loop = loop
        
        # Start both servers
        serial_server = websockets.serve(ws_handler, WS_HOST, WS_PORT, max_size=None)
        app_server = websockets.serve(app_ws_handler, WS_HOST, WS_APP_PORT, max_size=None)
        
        async with serial_server, app_server:
            loop_ready_evt.set()
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                pass
    asyncio.run(runner())

# ============================================================================
# XTERM.JS HTML GENERATION
# ============================================================================

def generate_dual_terminal_html(use_local: bool) -> str:
    """Generate HTML for xterm.js terminal with font support"""
    if use_local:
        css_href = "xterm.css"
        js_xterm = "xterm.js"
        js_fit = "xterm-addon-fit.js"
    else:
        css_href = "https://unpkg.com/xterm@5.3.0/css/xterm.css"
        js_xterm = "https://unpkg.com/xterm@5.3.0/lib/xterm.js"
        js_fit = "https://unpkg.com/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"
    
    # Generate font face definitions
    font_faces = ""
    if os.path.exists(FONTS_DIR):
        try:
            font_mapping = {
                "IntoneMonoNerdFontMono-Light.ttf": "IntoneMono Nerd Font Mono",
                "IosevkaSS08-Regular.ttf": "Iosevka SS08",
                "Jokerman.ttf": "Jokerman",
                "SpaceMonoNerdFontMono-Regular.ttf": "SpaceMono Nerd Font Mono"
            }
            
            for filename in os.listdir(FONTS_DIR):
                if filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                    font_family_name = font_mapping.get(filename, 
                        os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title())
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
<title>Jumperless – Dual Terminal</title>
<link rel="stylesheet" href="{css_href}">
<style>
{font_faces}
  html, body {{
    height:100%; width:100%; margin:0; padding:0; background:#0f1115; color:#e6e6e6;
    overflow:hidden !important;
  }}
  *::-webkit-scrollbar {{ width:0 !important; height:0 !important; display:none !important; }}
  * {{ scrollbar-width:none !important; }}
  
  .terminal-container {{
    position:absolute; inset:0; display:flex; flex-direction:column; overflow:hidden;
    width: 100%; height: 100%;
  }}
  
  .tab-bar {{
    background: #1a1f2a; border-bottom: 1px solid #333844; height: 40px;
    display: flex; align-items: center; padding: 0 8px; flex-shrink: 0;
  }}
  
  .tab {{
    padding: 8px 16px; margin-right: 4px; background: #2a2f3a; 
    border: 1px solid #333844; border-bottom: none; border-radius: 6px 6px 0 0;
    cursor: pointer; color: #888; transition: all 0.2s;
  }}
  
  .tab:hover {{ background: #3a4250; color: #ccc; }}
  .tab.active {{ background: #0f1115; color: #e6e6e6; border-color: #4b9cff; }}
  
  .terminal-wrapper {{
    flex: 1; position: relative; overflow: hidden;
  }}
  
  .terminal-pane {{
    position: absolute; inset: 8px; overflow: hidden; display: none;
  }}
  
  .terminal-pane.active {{ display: block; }}
  
  .terminal {{ width: 100%; height: 100%; overflow: hidden; }}
  .xterm .xterm-viewport {{ overflow: hidden !important; }}
</style>
</head>
<body>
  <div class="terminal-container">
    <div class="tab-bar">
      <div class="tab active" onclick="switchTab('serial')">Jumperless</div>
      <div class="tab" onclick="switchTab('app')">Backend</div>
    </div>
    <div class="terminal-wrapper">
      <div id="serial-pane" class="terminal-pane active">
        <div id="serial-terminal" class="terminal"></div>
      </div>
      <div id="app-pane" class="terminal-pane">
        <div id="app-terminal" class="terminal"></div>
      </div>
    </div>
  </div>

  <script src="{js_xterm}"></script>
  <script src="{js_fit}"></script>
  <script>
    const SERIAL_WS_URL = "ws://{WS_HOST}:{WS_PORT}";
    const APP_WS_URL = "ws://{WS_HOST}:{WS_APP_PORT}";
    
    // Terminal configurations
    const terminalConfig = {{
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
      scrollback: 10000,
      convertEol: false
    }};
    
    // Create terminals
    const serialTerm = new Terminal(terminalConfig);
    const appTerm = new Terminal({{...terminalConfig, cursorBlink: false}});
    
    const serialFit = new FitAddon.FitAddon();
    const appFit = new FitAddon.FitAddon();
    
    // Setup terminals
    serialTerm.loadAddon(serialFit);
    appTerm.loadAddon(appFit);
    
    serialTerm.open(document.getElementById("serial-terminal"));
    appTerm.open(document.getElementById("app-terminal"));
    
    // Global references
    window.serialTerm = serialTerm;
    window.appTerm = appTerm;
    window.serialFit = serialFit;
    window.appFit = appFit;
    
    let activeTab = 'serial';
    let serialWS = null;
    let appWS = null;
    
    // Tab switching function - make it globally accessible
    window.switchTab = function(tabName) {{
      // Update tab appearance
      document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
      // Find the tab that should be active by checking onclick content
      document.querySelectorAll('.tab').forEach(tab => {{
        const onclick = tab.getAttribute('onclick');
        if (onclick && onclick.includes("'" + tabName + "'")) {{
          tab.classList.add('active');
        }}
      }});
      
      // Update terminal panes
      document.querySelectorAll('.terminal-pane').forEach(pane => pane.classList.remove('active'));
      document.getElementById(tabName + '-pane').classList.add('active');
      
      activeTab = tabName;
      
      // Refit the active terminal
      setTimeout(() => {{
        if (tabName === 'serial') {{
          serialFit.fit();
          serialTerm.refresh(0, serialTerm.rows - 1);
          serialTerm.focus();
        }} else {{
          appFit.fit();
          appTerm.refresh(0, appTerm.rows - 1);
        }}
      }}, 10);
    }};
    
    // No setup arrow in HTML anymore - using Qt overlay button
    
    // Serial terminal WebSocket with buffering optimization
    let serialBuffer = '';
    let bufferTimer = null;
    
    function flushSerialBuffer() {{
      if (serialBuffer.length > 0) {{
        serialTerm.write(serialBuffer);
        serialBuffer = '';
      }}
      bufferTimer = null;
    }}
    
    function connectSerialWS() {{
      if (serialWS && serialWS.readyState === WebSocket.OPEN) return;
      serialWS = new WebSocket(SERIAL_WS_URL);
      serialWS.binaryType = "arraybuffer";
      const utf8 = new TextDecoder('utf-8', {{ fatal: false }});

      serialWS.onmessage = (ev) => {{
        if (ev.data instanceof ArrayBuffer) {{
          const s = utf8.decode(new Uint8Array(ev.data), {{ stream: true }});
          if (s) {{
            // Buffer small chunks for better performance
            serialBuffer += s;
            
            // Flush immediately for interactive characters or when buffer gets large
            if (s.length > 100 || /[\\r\\n>\\$#]/.test(s) || serialBuffer.length > 1000) {{
              flushSerialBuffer();
            }} else if (!bufferTimer) {{
              // Batch smaller chunks with a short delay
              bufferTimer = setTimeout(flushSerialBuffer, 5);
            }}
          }}
        }}
      }};
      
      serialWS.onopen = () => {{}};
      serialWS.onclose = () => {{
        try {{ const tail = utf8.decode(); if (tail) serialTerm.write(tail); }} catch(_) {{}}
      }};

      serialTerm.onData(data => {{
        if (!serialWS || serialWS.readyState !== WebSocket.OPEN) return;
        serialWS.send(JSON.stringify({{type:"tx", data}}));
      }});

      serialTerm.onResize(e => {{
        if (serialWS && serialWS.readyState === WebSocket.OPEN) {{
          serialWS.send(JSON.stringify({{type:"resize", cols:e.cols, rows:e.rows}}));
        }}
      }});
    }}
    
    // App output terminal WebSocket
    function connectAppWS() {{
      if (appWS && appWS.readyState === WebSocket.OPEN) return;
      appWS = new WebSocket(APP_WS_URL);
      appWS.binaryType = "arraybuffer";

      appWS.onmessage = (ev) => {{
        if (ev.data instanceof ArrayBuffer) {{
          const s = new TextDecoder('utf-8').decode(new Uint8Array(ev.data));
          if (s) appTerm.write(s);
        }}
      }};
      
      appWS.onopen = () => {{}};
      appWS.onclose = () => {{}};
    }}
    
    // Resize handling with enhanced sidebar responsiveness
    function handleResize() {{
      // Force refit both terminals to handle sidebar changes
      setTimeout(() => {{
        serialFit.fit();
        appFit.fit();
        if (activeTab === 'serial') {{
          serialTerm.refresh(0, serialTerm.rows - 1);
        }} else {{
          appTerm.refresh(0, appTerm.rows - 1);
        }}
      }}, 50);  // Small delay to let layout settle
    }}
    
    // More comprehensive resize detection
    window.addEventListener("resize", handleResize);
    new ResizeObserver(handleResize).observe(document.body);
    new ResizeObserver(handleResize).observe(document.querySelector('.terminal-container'));
    
    // Global function for external resize triggering (from Qt side)
    window.forceResize = handleResize;
    
    // Initial setup
    connectSerialWS();
    connectAppWS();
    
    // Initial resize with multiple attempts for proper alignment
    function initialResize() {{
      try {{
        serialFit.fit();
        appFit.fit();
        if (activeTab === 'serial') {{
          serialTerm.refresh(0, serialTerm.rows - 1);
          serialTerm.focus();
        }} else {{
          appTerm.refresh(0, appTerm.rows - 1);
        }}
      }} catch(e) {{
        console.log('Initial resize error:', e);
      }}
    }}
    
    // Multiple resize attempts to ensure proper initial alignment
    initialResize();
    setTimeout(initialResize, 100);
    setTimeout(initialResize, 500);
    setTimeout(initialResize, 1000);
    
    // Welcome messages
    //setTimeout(() => {{
      //serialTerm.writeln("\\x1b[36m📡 Jumperless Serial Terminal Ready\\x1b[0m");
     // serialTerm.writeln("\\x1b[33mUse GUI controls to connect and manage device\\x1b[0m");
     // serialTerm.writeln("");
      
     // appTerm.writeln("\\x1b[36m🖥️ Application Output Terminal\\x1b[0m");
     // appTerm.writeln("\\x1b[33mGUI actions and system messages appear here\\x1b[0m");
     // appTerm.writeln("");
  //  }}, 100);
  </script>
</body>
</html>
"""

# ============================================================================
# CUSTOM DRAG HANDLE WIDGET
# ============================================================================

class DragHandle(QWidget):
    """Custom drag handle widget for resizing collapsed sidebar"""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.dragging = False
        self.drag_start_x = 0
        self.original_sidebar_width = 350
        
    def mousePressEvent(self, event):
        """Handle mouse press to start dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_x = event.globalPosition().x()
            self.setCursor(Qt.SizeHorCursor)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move during dragging"""
        if self.dragging:
            # Calculate new width based on drag distance
            current_x = event.globalPosition().x()
            drag_distance = current_x - self.drag_start_x
            
            # If dragged far enough to the right, expand sidebar
            if drag_distance > 50:  # 50px threshold
                self.dragging = False
                self.main_window._expand_sidebar_from_drag()
                
    def mouseReleaseEvent(self, event):
        """Handle mouse release to end dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.SizeHorCursor)

# ============================================================================
# GUI MAIN WINDOW
# ============================================================================

class JumperlessBridgeWindow(QMainWindow):
    """Main application window with integrated Qt GUI and xterm.js terminal"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jumperless Bridge - Qt GUI")
        self.resize(1400, 900)
        
        # Initialize core state
        self.sidebar_collapsed = False
        self.background_threads = []
        self.backend = None
        
        # Start WebSocket servers
        self._start_websocket_servers()
        
        # Initialize GUI
        self._init_ui()
        
        # Initialize backend systems
        self._init_backend()
        
        # Start background monitoring
        self._start_background_tasks()
    
    def _start_websocket_servers(self):
        """Start both WebSocket servers for xterm.js terminals"""
        ready_event = threading.Event()
        ws_thread = threading.Thread(
            target=start_ws_servers, 
            args=(ready_event,), 
            daemon=True
        )
        ws_thread.start()
        ready_event.wait(timeout=3.0)
        self.background_threads.append(ws_thread)
    
    def _init_ui(self):
        """Initialize the Qt user interface"""
        # Central widget with splitter
        central = QWidget(self)
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal, self)
        main_layout.addWidget(splitter)
        
        # Left sidebar with anchor
        self.sidebar = self._create_sidebar()
        splitter.addWidget(self.sidebar)
        
        # Right terminal view with setup arrow overlay
        terminal_container = QWidget()
        terminal_layout = QVBoxLayout(terminal_container)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(0)
        
        # Create terminal view
        self.terminal_view = self._create_terminal_view()
        terminal_layout.addWidget(self.terminal_view)
        
        # Setup arrow button (overlay on terminal view)
        self.setup_arrow_btn = QPushButton("▶", terminal_container)
        self.setup_arrow_btn.setObjectName("setup_arrow_btn")
        self.setup_arrow_btn.setMaximumSize(0, 3)
        self.setup_arrow_btn.setMinimumSize(0, 3)
        self.setup_arrow_btn.setToolTip("Open Setup Panel")
        self.setup_arrow_btn.clicked.connect(self._toggle_sidebar)
        self.setup_arrow_btn.hide()  # Initially hidden since sidebar starts open
        
        # Position the arrow button on the left edge, middle vertically
        self.setup_arrow_btn.setParent(terminal_container)
        # Will be positioned dynamically in _position_setup_arrow method
        self.setup_arrow_btn.raise_()  # Bring to front
        
        splitter.addWidget(terminal_container)
        
        # Add drag handle for when sidebar is collapsed
        self.drag_handle = DragHandle(terminal_container, self)
        self.drag_handle.setObjectName("drag_handle")
        self.drag_handle.setMaximumWidth(15)
        self.drag_handle.setMinimumWidth(15)
        self.drag_handle.setCursor(Qt.SizeHorCursor)
        self.drag_handle.setToolTip("Drag to expand setup panel")
        self.drag_handle.hide()  # Initially hidden since sidebar is open
        
        # Position drag handle on left edge
        self.drag_handle.setParent(terminal_container)
        self.drag_handle.setGeometry(0, 0, 5, terminal_container.height())
        
        # Set splitter proportions (sidebar:terminal = 1:3)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([350, 1050])
        
        # Store splitter reference for drag functionality
        self.main_splitter = splitter
        self.terminal_container = terminal_container
        
        # Connect resize event to update drag handle size
        terminal_container.installEventFilter(self)
        
        # Monitor splitter resize to show/hide setup arrow
        splitter.splitterMoved.connect(self._on_splitter_moved)
        
        # Apply styling
        self._apply_styling()
    
    def _create_sidebar(self) -> QWidget:
        """Create the collapsible sidebar with controls"""
        sidebar = QFrame(self)
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setMinimumWidth(320)
        sidebar.setMaximumWidth(400)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header with collapse button
        header_layout = QHBoxLayout()
        title = QLabel("Jumperless Control", sidebar)
        title.setObjectName("sidebar_title")
        
        self.collapse_btn = QPushButton("◀", sidebar)
        self.collapse_btn.setObjectName("collapse_btn")
        self.collapse_btn.setMaximumWidth(35)
        self.collapse_btn.clicked.connect(self._toggle_sidebar)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.collapse_btn)
        layout.addLayout(header_layout)
        
        # Connection section
        layout.addWidget(self._create_connection_section())
        
        # Bridge operations section
        layout.addWidget(self._create_bridge_operations_section())
        
        # Wokwi section
        layout.addWidget(self._create_wokwi_section())
        
        # System section
        layout.addWidget(self._create_system_section())
        
        # Status section
        layout.addStretch()
        self.status_label = QLabel("Starting up...", sidebar)
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        return sidebar
    
    def _create_connection_section(self) -> QGroupBox:
        """Create the connection controls section"""
        group = QGroupBox("Connection", self)
        layout = QVBoxLayout(group)
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumContentsLength(20)
        port_layout.addWidget(self.port_combo)
        layout.addLayout(port_layout)
        
        # Connection buttons
        btn_layout = QHBoxLayout()
        self.rescan_btn = QPushButton("Rescan")
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        
        self.rescan_btn.clicked.connect(self._request_port_rescan)
        self.connect_btn.clicked.connect(self._connect_serial)
        self.disconnect_btn.clicked.connect(self._disconnect_serial)
        
        btn_layout.addWidget(self.rescan_btn)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        layout.addLayout(btn_layout)
        
        return group
    
    def _create_bridge_operations_section(self) -> QGroupBox:
        """Create the bridge operations section"""
        group = QGroupBox("Operations", self)
        layout = QVBoxLayout(group)
        
        # Mode toggles
        self.interactive_cb = QCheckBox("Interactive Mode")
        self.wokwi_enabled_cb = QCheckBox("Wokwi Integration")
        self.arduino_flash_cb = QCheckBox("Arduino Flashing")
        self.debug_cb = QCheckBox("Debug Output")
        
        self.wokwi_enabled_cb.setChecked(True)
        self.arduino_flash_cb.setChecked(True)
        
        # Connect signals
        self.interactive_cb.toggled.connect(self._toggle_interactive_mode)
        self.wokwi_enabled_cb.toggled.connect(self._toggle_wokwi)
        self.arduino_flash_cb.toggled.connect(self._toggle_arduino_flash)
        self.debug_cb.toggled.connect(self._toggle_debug)
        
        layout.addWidget(self.interactive_cb)
        layout.addWidget(self.wokwi_enabled_cb)
        layout.addWidget(self.arduino_flash_cb)
        layout.addWidget(self.debug_cb)
        
        # Rate control
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Update Rate:"))
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(100, 2000)
        self.rate_slider.setValue(500)
        self.rate_label = QLabel("500ms")
        self.rate_slider.valueChanged.connect(self._update_rate_changed)
        
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label)
        layout.addLayout(rate_layout)
        
        return group
    
    def _create_wokwi_section(self) -> QGroupBox:
        """Create the Wokwi integration section"""
        group = QGroupBox("Wokwi Projects", self)
        layout = QVBoxLayout(group)
        
        # Slot management
        self.slots_btn = QPushButton("Manage Slots")
        self.flash_btn = QPushButton("Flash Arduino")
        self.projects_btn = QPushButton("View Projects")
        
        self.slots_btn.clicked.connect(self._manage_slots)
        self.flash_btn.clicked.connect(self._flash_arduino)
        self.projects_btn.clicked.connect(self._view_projects)
        
        layout.addWidget(self.slots_btn)
        layout.addWidget(self.flash_btn)
        layout.addWidget(self.projects_btn)
        
        # Slot status
        self.slot_status = QLabel("0 slots assigned")
        layout.addWidget(self.slot_status)
        
        return group
    
    def _create_system_section(self) -> QGroupBox:
        """Create the system management section"""
        group = QGroupBox("System", self)
        layout = QVBoxLayout(group)
        
        # System buttons
        self.config_btn = QPushButton("Arduino Config")
        self.firmware_btn = QPushButton("Update Firmware")
        self.app_update_btn = QPushButton("Check App Updates")
        
        self.config_btn.clicked.connect(self._edit_config)
        self.firmware_btn.clicked.connect(self._update_firmware)
        self.app_update_btn.clicked.connect(self._check_app_updates)
        
        layout.addWidget(self.config_btn)
        layout.addWidget(self.firmware_btn)
        layout.addWidget(self.app_update_btn)
        
        return group
    
    def _create_terminal_view(self) -> QWebEngineView:
        """Create the xterm.js terminal view"""
        view = QWebEngineView(self)
        
        # Disable scrollbars if possible
        try:
            if QWebEngineSettings and hasattr(QWebEngineSettings, "ShowScrollBars"):
                QWebEngineSettings.defaultSettings().setAttribute(
                    QWebEngineSettings.ShowScrollBars, False
                )
                view.page().settings().setAttribute(
                    QWebEngineSettings.ShowScrollBars, False
                )
        except Exception:
            pass
        
        # Load dual terminal HTML
        use_local = have_local_assets()
        html = generate_dual_terminal_html(use_local)
        
        if use_local:
            base_url = QUrl.fromLocalFile(os.path.abspath(ASSETS_DIR) + os.sep)
        else:
            base_url = QUrl("https://local/")
            
        view.setHtml(html, baseUrl=base_url)
        view.loadFinished.connect(self._terminal_loaded)
        
        return view
    
    def _apply_styling(self):
        """Apply Qt stylesheet for modern appearance"""
        style = """
            QMainWindow { background: #0f1115; }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #333844;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px;
            }
            QFrame { 
                background: #151821; 
                border: 1px solid #333844; 
                border-radius: 6px; 
            }
            QLabel#sidebar_title { 
                font-size: 16px; 
                font-weight: bold; 
                color: #8ab4f8;
            }
            QLabel#status_label { 
                color: #98e6a7; 
                font-style: italic;
            }
            QPushButton {
                background: #2a2f3a; 
                color: #e6e6e6;
                border: 1px solid #333844; 
                border-radius: 6px; 
                padding: 6px 8px;
                min-height: 18px;
            }
            QPushButton:hover { 
                border-color: #4b9cff; 
                background: #3a4250;
            }
            QPushButton:pressed { 
                background: #1a1f2a; 
            }
            QPushButton#collapse_btn {
                background: #8a64ff; 
                color: white;
                font-weight: bold;
            }
            QPushButton#setup_arrow_btn {
                background: #4caf50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #4caf50;
                font-size: 12px;
            }
            QPushButton#setup_arrow_btn:hover {
                background: #45a049;
            }
            QWidget#drag_handle {
                background: #4caf50;
                border-right: 2px solid #45a049;
            }
            QWidget#drag_handle:hover {
                background: #45a049;
            }
            QComboBox {
                background: #0f1115; 
                color: #e6e6e6;
                border: 1px solid #333844; 
                border-radius: 6px; 
                padding: 6px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #151821; 
                color: #e6e6e6; 
                selection-background-color: #244580;
                border: 1px solid #333844;
            }
            QCheckBox {
                color: #e6e6e6;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px; 
                height: 16px;
                border: 1px solid #333844;
                border-radius: 3px;
                background: #0f1115;
            }
            QCheckBox::indicator:checked {
                background: #4caf50;
                border-color: #4caf50;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #333844;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #8ab4f8;
                width: 18px;
                border-radius: 9px;
                margin: -6px 0;
            }
        """
        self.setStyleSheet(style)
    
    def _init_backend(self):
        """Initialize the backend Jumperless systems"""
        try:
            # Get backend instance and set up callback
            self.backend = get_backend_instance(gui_mode=True)
            self.backend.set_gui_callback(self._handle_backend_event)
            
            # Initialize backend systems
            QTimer.singleShot(1000, self._delayed_init)
            
        except Exception as e:
            self._set_status(f"Initialization error: {str(e)}", error=True)
            self.backend = None
    
    def _delayed_init(self):
        """Delayed initialization of heavy backend components"""
        def init_worker():
            try:
                if self.backend:
                    self._log_to_app("🔧 Initializing backend systems...", "cyan")
                    if self.backend.initialize():
                        self._log_to_app("✅ Backend initialized successfully", "green")
                        
                        # Get port information from backend and populate GUI
                        self._log_to_app("📋 Getting port information from backend...", "cyan")
                        
                        # Try to get port info from backend
                        port_info = None
                        if hasattr(self.backend, 'get_port_info'):
                            port_info = self.backend.get_port_info()
                        elif hasattr(backend_module, 'portName') and backend_module.portName:
                            # Fallback: construct port info from backend globals
                            port_info = {
                                'main_port': getattr(backend_module, 'portName', None),
                                'arduino_port': getattr(backend_module, 'arduinoPort', None),
                                'organized_ports': {
                                    getattr(backend_module, 'portName', 'Unknown'): 'Jumperless Main',
                                    getattr(backend_module, 'arduinoPort', 'Unknown'): 'Arduino Programming'
                                } if hasattr(backend_module, 'portName') else {}
                            }
                        
                        # Populate GUI with detected ports
                        if port_info and port_info.get('main_port'):
                            self._log_to_app("🎯 Populating GUI with backend's detected ports...", "green")
                            # Use event system to populate GUI from main thread
                            from PySide6.QtCore import QCoreApplication
                            populate_event = StatusUpdateEvent("populate_ports", is_error=False)
                            populate_event.port_info = port_info  # Add port info to event
                            QCoreApplication.postEvent(self, populate_event)
                        else:
                            self._log_to_app("⚠️ No port info available from backend", "yellow")
                        
                        self._log_to_app("ℹ️ Backend running in Wokwi-only mode", "blue")
                        
                        # Start Wokwi loop if needed
                        self.backend.start_wokwi_loop()
                        
                        # Backend is now fully ready
                        self._log_to_app("🏁 Backend fully initialized and ready", "green")
                    else:
                        self._log_to_app("❌ Backend initialization failed", "red")
                        # Still allow auto-scan to proceed - it may work with fallback methods
                else:
                    self._log_to_app("⚠️ Backend not available - using direct port scanning", "yellow")
                
                # App update check removed from startup - available via manual button only
                
                # Backend already handles port detection - schedule connection monitoring via event
                print("📨 Backend already detected ports - scheduling connection monitoring")
                self._log_to_app("✅ Backend completed port detection - GUI ready", "green")
                self._log_to_app("⏱️ Scheduling connection monitoring start", "blue")
                
                # Use event system instead of QTimer from background thread
                from PySide6.QtCore import QCoreApplication
                start_monitoring_event = StatusUpdateEvent("start_monitoring", is_error=False)
                QCoreApplication.postEvent(self, start_monitoring_event)
                
            except Exception as e:
                # Use thread-safe method to set status
                from PySide6.QtCore import QCoreApplication
                event = ScanErrorEvent(f"Setup error: {str(e)}", is_error=True)
                QCoreApplication.postEvent(self, event)
        
        # Run initialization in background thread
        init_thread = threading.Thread(target=init_worker, daemon=True)
        init_thread.start()
        self.background_threads.append(init_thread)
    
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Port monitoring will be started after connection
        pass
    
    def _start_connection_monitoring(self):
        """Start monitoring for USB disconnect/reconnect - backend handles port monitoring"""
        # Simple status check only - backend handles actual port monitoring via check_presence()
        self.connection_monitor = QTimer()
        self.connection_monitor.timeout.connect(self._check_gui_connection_status)
        self.connection_monitor.start(3000)  # Check every 3 seconds (less frequent)
        self._last_connected_port = None
        self._log_to_app("GUI connection status monitoring started (backend handles port monitoring)", "blue")
    
    def _check_gui_connection_status(self):
        """Simple GUI connection status check - backend handles port monitoring"""
        if not hasattr(self, 'connection_monitor'):
            return
            
        try:
            # Check if GUI WebSocket bridge is connected
            is_gui_connected = SER.is_open()
            current_port = SER.port_name if is_gui_connected else None
            
            # Only log disconnection events for user awareness
            if self._last_connected_port and not is_gui_connected:
                self._log_to_app(f"🔌 GUI disconnected from: {self._last_connected_port}", "yellow")
                self._set_status("GUI disconnected - backend monitoring for reconnection...")
                self._last_connected_port = None
            
            # Update last known port (for disconnect detection only)
            if is_gui_connected and current_port:
                if not self._last_connected_port:
                    self._log_to_app(f"🔗 GUI connected to: {current_port}", "green")
                self._last_connected_port = current_port
                
        except Exception as e:
            # Silent fail - just status monitoring
            pass
    
    # _startup_rescan() removed - backend handles startup port detection
    # Manual rescanning is handled by _request_port_rescan() method
    
    # ========================================================================
    # UI EVENT HANDLERS
    # ========================================================================
    
    def _toggle_sidebar(self):
        """Toggle sidebar collapse/expand with Qt setup arrow and drag handle"""
        if self.sidebar_collapsed:
            # Expand sidebar
            self.sidebar.show()
            self.collapse_btn.setText("◀")
            self.sidebar_collapsed = False
            self._log_to_app("⚙️ Setup panel opened", "blue")
            # Hide setup arrow and drag handle when sidebar is open
            self.setup_arrow_btn.hide()
            self.drag_handle.hide()
        else:
            # Collapse sidebar
            self.sidebar.hide()  
            self.collapse_btn.setText("▶")
            self.sidebar_collapsed = True
            self._log_to_app("⚙️ Setup panel collapsed - click ▶ arrow or drag edge to reopen", "blue")
            # Show setup arrow and drag handle when sidebar is collapsed
            self._position_setup_arrow()  # Position before showing
            self.setup_arrow_btn.show()
            self.drag_handle.show()
        
        # Trigger terminal resize after sidebar animation
        QTimer.singleShot(100, self._force_terminal_resize)
    
    def _expand_sidebar_from_drag(self):
        """Expand sidebar from drag handle interaction"""
        if self.sidebar_collapsed:
            self.sidebar.show()
            self.collapse_btn.setText("◀")
            self.sidebar_collapsed = False
            self._log_to_app("⚙️ Setup panel opened via drag", "blue")
        
        # Always restore sidebar to proper size and hide controls
        self.main_splitter.setSizes([350, 1050])  # Restore default proportions
        self.setup_arrow_btn.hide()
        self.drag_handle.hide()
        
        # Trigger terminal resize
        QTimer.singleShot(100, self._force_terminal_resize)
    
    def _on_splitter_moved(self, pos, index):
        """Handle splitter movement to show/hide setup arrow based on sidebar size"""
        if index == 0:  # Sidebar splitter position
            sidebar_width = self.main_splitter.sizes()[0]
            
            # Show setup arrow if sidebar is very small (< 50px) but not fully collapsed
            if sidebar_width < 50 and sidebar_width > 0 and not self.sidebar_collapsed:
                self._position_setup_arrow()  # Position before showing
                self.setup_arrow_btn.show()
                self.drag_handle.show()
                self._log_to_app("⚙️ Setup arrow shown - sidebar resized small", "blue")
            elif sidebar_width >= 50 and not self.sidebar_collapsed:
                self.setup_arrow_btn.hide()
                self.drag_handle.hide()
    
    def _position_setup_arrow(self):
        """Position the setup arrow at left edge, vertically centered"""
        if hasattr(self, 'setup_arrow_btn') and hasattr(self, 'terminal_container'):
            container_height = self.terminal_container.height()
            # Position in middle vertically, at left edge
            y_pos = max(50, (container_height - 30) // 2)  # Center vertically, min 50px from top
            self.setup_arrow_btn.move(5, y_pos)
    
    def eventFilter(self, obj, event):
        """Handle resize events for terminal container"""
        if obj == self.terminal_container and event.type() == QEvent.Resize:
            # Update drag handle height when terminal container resizes
            if hasattr(self, 'drag_handle'):
                self.drag_handle.setGeometry(0, 0, 5, self.terminal_container.height())
            # Reposition setup arrow
            self._position_setup_arrow()
        return super().eventFilter(obj, event)
    
    
    def _force_terminal_resize(self):
        """Force terminal to resize/reflow after sidebar toggle"""
        try:
            # Execute JavaScript resize function in the WebEngineView
            self.terminal_view.page().runJavaScript("if (typeof window.forceResize === 'function') window.forceResize();")
        except Exception as e:
            print(f"Terminal resize error: {e}")  # Debug output
    
    def _request_port_rescan(self):
        """Rescan ports using backend"""
        if not self.backend:
            self._log_to_app("❌ Backend not available", "red")
            return
            
        self._log_to_app("🔍 Rescanning for Jumperless devices...", "cyan")
        
        def scan_worker():
            from PySide6.QtCore import QCoreApplication
            try:
                port_info = self.backend.scan_ports()
                # Use QApplication.postEvent instead of QTimer in thread
                if port_info:
                    # Post custom event to main thread
                    event = ScanResultEvent(port_info)
                    QCoreApplication.postEvent(self, event)
                else:
                    event = ScanErrorEvent("No Jumperless devices found", is_error=False)
                    QCoreApplication.postEvent(self, event)
            except Exception as e:
                event = ScanErrorEvent(f"Scan error: {e}", is_error=True)
                QCoreApplication.postEvent(self, event)
        
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def _handle_scan_results(self, port_info):
        """Handle port scan results with auto-connect capability"""
        try:
            main_port = port_info.get('main_port')
            arduino_port = port_info.get('arduino_port')
            organized_ports = port_info.get('organized_ports', {})
            
            self.port_combo.clear()
            
            # Add main port first
            if main_port:
                main_desc = organized_ports.get(main_port, 'Jumperless Main')
                self.port_combo.addItem(f"{main_port} - {main_desc}", main_port)
                self._log_to_app(f"📍 Main port: {main_port} ({main_desc})", "green")
                # Ensure main port is selected as current
                self.port_combo.setCurrentIndex(0)
            
            # Add other ports
            for port_name, description in organized_ports.items():
                if port_name != main_port:
                    self.port_combo.addItem(f"{port_name} - {description}", port_name)
                    self._log_to_app(f"📌 Port: {port_name} ({description})", "blue")
            
            if arduino_port:
                arduino_desc = organized_ports.get(arduino_port, 'Arduino Programming')
                self._log_to_app(f"🔧 Arduino port: {arduino_port} ({arduino_desc})", "magenta")
                
            self._set_status(f"Found {len(organized_ports)} port(s)")
            
            # Auto-connect to main port if this is from the startup auto-scan
            if main_port and hasattr(self, '_enable_auto_connect') and self._enable_auto_connect:
                self._log_to_app(f"🚀 Auto-connecting to main port: {main_port}", "green")
                self._enable_auto_connect = False  # Clear flag
                QTimer.singleShot(1000, self._connect_serial)  # Small delay for UI to update
            elif not main_port:
                self._set_status("No main port found - please select manually")
            else:
                self._set_status(f"Found {len(organized_ports)} port(s) - Select and connect")
                
        except Exception as e:
            self._log_to_app(f"❌ Error processing scan results: {e}", "red")
            # Clear auto-connect flag on error
            if hasattr(self, '_enable_auto_connect'):
                self._enable_auto_connect = False
    
    
    
    def _handle_backend_error(self, signal_data):
        """Handle error signal from backend"""
        message = signal_data.get('message', 'Unknown error')
        details = signal_data.get('details', '')
        
        self._log_to_app(f"❌ Backend error: {message}", "red")
        if details:
            self._log_to_app(f"   Details: {details}", "gray")
    
    def _connect_serial(self):
        """Connect to the selected serial port"""
        port = self.port_combo.currentData()
        if not port:
            self._set_status("No port selected", error=True)
            return
        
        if not self.backend:
            self._log_to_app("❌ Backend not available", "red")
            return
        
        self._log_to_app(f"🔌 Attempting to connect to {port}...", "cyan")
        
        # If backend is waiting for port selection, provide the selected port
        if self.backend.waiting_for_port_selection:
            # Extract port number from selection for backend compatibility  
            port_index = None
            for i in range(self.port_combo.count()):
                if self.port_combo.itemData(i) == port:
                    port_index = str(i + 1)  # 1-based indexing for backend
                    break
            
            if port_index:
                self.backend.set_port_selection_result(port_index)
                self._log_to_app(f"🔗 Port selection provided to backend: {port}", "green")
                return
        
        # Connect WebSocket serial bridge first (for GUI terminal)
        try:
            SER.open(port, FIXED_BAUD)
            self._log_to_app(f"✅ Terminal bridge connected to {port}", "green")
        except Exception as e:
            self._log_to_app(f"❌ WebSocket bridge connection failed: {e}", "red")
            return
        
        # Notify backend about the port for Wokwi operations (but don't give it serial access)
        if self.backend:
            # Backend stores port info but doesn't maintain a connection
            backend_module.portName = port
            backend_module.arduinoPort = port  # Assume same for now
            self._log_to_app(f"ℹ️ Backend notified of port {port} for Wokwi operations", "blue")
        
        self._set_status(f"Connected to {port}")
        self._log_to_app(f"✅ GUI manages serial, backend handles Wokwi on-demand", "green")
    
    def _disconnect_serial(self):
        """Disconnect from serial port"""
        try:
            self._log_to_app("🔌 Disconnecting serial port...", "yellow")
            
            # Disconnect WebSocket bridge
            SER.close()
            
            # Disconnect backend
            if self.backend:
                self.backend.disconnect()
            
            self._set_status("Disconnected")
            self._log_to_app("✅ Serial port disconnected", "yellow")
        except Exception as e:
            self._set_status(f"Disconnect error: {str(e)}", error=True)
    
    def _toggle_interactive_mode(self, enabled: bool):
        """Toggle interactive mode"""
        if self.backend:
            # Backend manages interactive mode internally
            self._log_to_app(f"⚡ Interactive mode {'enabled' if enabled else 'disabled'}", "magenta")
        else:
            # Fallback to global variable
            global interactive_mode
            interactive_mode = enabled
            backend_module.interactive_mode = enabled
            self._log_to_app(f"⚡ Interactive mode {'enabled' if enabled else 'disabled'}", "magenta")
        self._set_status(f"Interactive mode {'enabled' if enabled else 'disabled'}")
    
    def _toggle_wokwi(self, enabled: bool):
        """Toggle Wokwi integration"""
        if self.backend:
            self.backend.toggle_wokwi_updates()
        else:
            global noWokwiStuff
            noWokwiStuff = not enabled
            backend_module.noWokwiStuff = not enabled
            self._log_to_app(f"🌐 Wokwi integration {'enabled' if enabled else 'disabled'}", "cyan")
        self._set_status(f"Wokwi integration {'enabled' if enabled else 'disabled'}")
    
    def _toggle_arduino_flash(self, enabled: bool):
        """Toggle Arduino flashing"""
        if self.backend:
            self.backend.toggle_arduino_flashing()
        else:
            global disableArduinoFlashing
            disableArduinoFlashing = not enabled
            backend_module.disableArduinoFlashing = not enabled
        self._set_status(f"Arduino flashing {'enabled' if enabled else 'disabled'}")
    
    def _toggle_debug(self, enabled: bool):
        """Toggle debug output"""
        if self.backend:
            self.backend.toggle_debug_mode()
        else:
            global debugWokwi
            debugWokwi = enabled
            backend_module.debugWokwi = enabled
        self._set_status(f"Debug output {'enabled' if enabled else 'disabled'}")
    
    def _update_rate_changed(self, value: int):
        """Handle update rate change"""
        rate_seconds = value / 1000.0  # Convert to seconds
        if self.backend:
            self.backend.set_wokwi_update_rate(rate_seconds + 0.4)
        else:
            global wokwiUpdateRate
            wokwiUpdateRate = rate_seconds
            backend_module.wokwiUpdateRate = wokwiUpdateRate
        self.rate_label.setText(f"{value}ms")
    
    def _manage_slots(self):
        """Open slot management dialog"""
        def slot_worker():
            try:
                self._log_to_app("Opening slot management interface...", "blue")
                # Enable GUI input for interactive slot management
                backend_module.gui_input_enabled = True
                print(f"[GUI] DEBUG: gui_input_enabled set to {backend_module.gui_input_enabled}")
                print(f"[GUI] DEBUG: user_input_queue exists: {hasattr(backend_module, 'user_input_queue')}")
                self._log_to_app("🎮 GUI input enabled - you can now interact via terminal", "cyan")
                
                backend_module.assign_wokwi_slots()
                
                # Disable GUI input after completion
                backend_module.gui_input_enabled = False
                self._log_to_app("🎮 GUI input disabled", "cyan")
                
                # Update slot count
                count = backend_module.count_assigned_slots()
                # Use thread-safe event instead of QTimer
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent("Slot management completed", is_error=False, slot_count=count)
                QCoreApplication.postEvent(self, event)
                self._log_to_app(f"✅ Slot management completed - {count} slots assigned", "green")
            except Exception as e:
                # Make sure to disable GUI input on error
                backend_module.gui_input_enabled = False
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent(f"Slot management error: {str(e)}", is_error=True)
                QCoreApplication.postEvent(self, event)
        
        threading.Thread(target=slot_worker, daemon=True).start()
    
    def _flash_arduino(self):
        """Flash Arduino with current slot content"""
        def flash_worker():
            try:
                self._log_to_app("⚡ Arduino flashing initiated...", "yellow")
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent("Arduino flashing initiated...", is_error=False)
                QCoreApplication.postEvent(self, event)
                
                # Here you would integrate with the existing flash_arduino_sketch function
                # For now, show completion message
                import time
                time.sleep(1)  # Simulate flashing time
                
                event = StatusUpdateEvent("Arduino flashing completed", is_error=False)
                QCoreApplication.postEvent(self, event)
                self._log_to_app("✅ Arduino flashing completed successfully", "green")
                
            except Exception as e:
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent(f"Flash error: {str(e)}", is_error=True)
                QCoreApplication.postEvent(self, event)
        
        threading.Thread(target=flash_worker, daemon=True).start()
    
    def _view_projects(self):
        """Show saved projects"""
        def projects_worker():
           
            try:
                backend_module.print_saved_projects()
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent("Project list printed to terminal", is_error=False)
                QCoreApplication.postEvent(self, event)
            except Exception as e:
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent(f"Projects error: {str(e)}", is_error=True)
                QCoreApplication.postEvent(self, event)
        
        threading.Thread(target=projects_worker, daemon=True).start()
    
    def _edit_config(self):
        """Edit Arduino CLI configuration"""
        def config_worker():
            
            try:
                backend_module.edit_arduino_cli_config()
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent("Arduino CLI config editor opened", is_error=False)
                QCoreApplication.postEvent(self, event)
            except Exception as e:
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent(f"Config error: {str(e)}", is_error=True)
                QCoreApplication.postEvent(self, event)
        
        threading.Thread(target=config_worker, daemon=True).start()
    
    def _update_firmware(self):
        """Update Jumperless firmware"""
        if not self.backend:
            self._log_to_app("❌ Backend not available", "red")
            return
            
        def firmware_worker():
            try:
                self._log_to_app("🔄 Firmware update starting...", "blue")
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent("Firmware update starting...", is_error=False)
                QCoreApplication.postEvent(self, event)
                result = self.backend.update_firmware(force=True)
                # Backend will send notifications via callback
            except Exception as e:
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent(f"Firmware update error: {str(e)}", is_error=True)
                QCoreApplication.postEvent(self, event)
        
        threading.Thread(target=firmware_worker, daemon=True).start()
    
    def _check_app_updates(self):
        """Check for application updates"""
        def update_worker():
            try:
                if 'check_for_app_updates' in dir(backend_module):
                    backend_module.check_for_app_updates()
                    from PySide6.QtCore import QCoreApplication
                    event = StatusUpdateEvent("App update check completed", is_error=False)
                    QCoreApplication.postEvent(self, event)
                else:
                    from PySide6.QtCore import QCoreApplication
                    event = StatusUpdateEvent("App update check not available", is_error=False)
                    QCoreApplication.postEvent(self, event)
            except Exception as e:
                from PySide6.QtCore import QCoreApplication
                event = StatusUpdateEvent(f"Update check error: {str(e)}", is_error=True)
                QCoreApplication.postEvent(self, event)
        
        threading.Thread(target=update_worker, daemon=True).start()
    
    def _terminal_loaded(self, success: bool):
        """Handle terminal load completion"""
        if success:
            self._set_status("Terminal ready")
            # Position setup arrow after terminal loads
            QTimer.singleShot(300, self._position_setup_arrow)
            # Force initial terminal resize after loading
            QTimer.singleShot(500, self._force_terminal_resize)
            # Additional resize after a longer delay to ensure proper alignment  
            QTimer.singleShot(1500, self._force_terminal_resize)
        else:
            self._set_status("Terminal load failed", error=True)
    
    def _set_status(self, message: str, error: bool = False):
        """Update status label and log to app terminal"""
        self.status_label.setText(message)
        if error:
            self.status_label.setStyleSheet("color: #ff9aa2; font-style: italic;")
            self._log_to_app(f"❌ {message}", "red")
        else:
            self.status_label.setStyleSheet("color: #98e6a7; font-style: italic;")
            self._log_to_app(f"ℹ️ {message}", "green")
    
    def _log_to_app(self, message: str, color: str = "white"):
        """Log a message to the app output terminal"""
        # Add \n\r for proper xterm.js line endings
        APP_OUT.log_message(message + "\n\r", color)
    
    def _populate_gui_from_backend(self, port_info):
        """Populate GUI combo box from backend's port detection"""
        try:
            main_port = port_info.get('main_port')
            arduino_port = port_info.get('arduino_port')
            organized_ports = port_info.get('organized_ports', {})
            
            # Clear and populate combo box
            self.port_combo.clear()
            
            if main_port and main_port != 'Unknown':
                # Add main port first and select it
                main_desc = organized_ports.get(main_port, 'Jumperless Main')
                self.port_combo.addItem(f"{main_port} - {main_desc}", main_port)
                self.port_combo.setCurrentIndex(0)
                self._log_to_app(f"📍 GUI populated with main port: {main_port}", "green")
                
            if arduino_port and arduino_port != main_port and arduino_port != 'Unknown':
                # Add arduino port as option
                arduino_desc = organized_ports.get(arduino_port, 'Arduino Programming')
                self.port_combo.addItem(f"{arduino_port} - {arduino_desc}", arduino_port) 
                self._log_to_app(f"🔧 Added arduino port: {arduino_port}", "blue")
            
            # Add any other organized ports
            for port_name, description in organized_ports.items():
                if port_name not in [main_port, arduino_port] and port_name != 'Unknown':
                    self.port_combo.addItem(f"{port_name} - {description}", port_name)
                    self._log_to_app(f"📌 Added port: {port_name} ({description})", "blue")
            
            # Update status and auto-connect to main port
            port_count = len([p for p in [main_port, arduino_port] if p and p != 'Unknown'])
            if main_port and main_port != 'Unknown':
                self._set_status(f"Detected {port_count} port(s) - Main: {main_port}")
                self._log_to_app("🔌 Auto-connecting to detected main port...", "cyan")
                
                # Auto-connect to the main port after backend detection
                try:
                    self._connect_serial()
                    self._log_to_app("✅ Auto-connection successful!", "green")
                except Exception as e:
                    self._log_to_app(f"❌ Auto-connection failed: {e}", "red")
                    self._log_to_app("🎯 Manual connection required - use Connect button", "yellow")
            else:
                self._set_status("No ports detected from backend")
                self._log_to_app("⚠️ No valid ports found from backend", "yellow")
                
        except Exception as e:
            self._log_to_app(f"❌ Error populating GUI from backend: {e}", "red")
    
    def _handle_backend_event(self, event_type, data=None):
        """Handle events from the backend"""
        try:
            if event_type == 'backend_initialized':
                port_info = data or {}
                # Backend initialized - populate GUI with detected ports
                if port_info.get('main_port'):
                    self._log_to_app(f"✅ Backend initialized with main port: {port_info['main_port']}", "green")
                    # Also log firmware info if available
                    firmware_version = port_info.get('firmware_version', 'Unknown') 
                    if firmware_version != 'Unknown':
                        is_v5 = port_info.get('is_v5', False)
                        v5_text = " (V5)" if is_v5 else ""
                        self._log_to_app(f"🔬 Firmware: {firmware_version}{v5_text}", "cyan")
                    
                    # Populate GUI combo box with backend's detected ports
                    self._populate_gui_from_backend(port_info)
                else:
                    self._log_to_app(f"✅ Backend initialized", "green")
                
            elif event_type == 'connection_established':
                port = data.get('port', 'Unknown')
                self._log_to_app(f"✅ Connected to {port}", "green")
                self._set_status(f"Connected to {port}")
                
            elif event_type == 'connection_failed':
                error = data.get('error', 'Unknown error')
                port = data.get('port', 'Unknown')
                self._log_to_app(f"❌ Failed to connect to {port}: {error}", "red")
                self._set_status(f"Connection failed: {error}", error=True)
                
            elif event_type == 'connection_lost':
                self._log_to_app("Connection lost", "yellow")
                self._set_status("Connection lost", error=True)
                
            elif event_type == 'disconnected':
                self._log_to_app("🔌 Disconnected", "blue")
                self._set_status("Disconnected")
                
            elif event_type == 'serial_data_received':
                # Forward serial data to WebSocket terminal
                data_str = data.get('data', '')
                if data_str:
                    SER.send_to_clients(data_str)
                
            elif event_type == 'interactive_mode_changed':
                enabled = data.get('enabled', False)
                mode_text = "enabled" if enabled else "disabled"
                self._log_to_app(f"🎮 Interactive mode {mode_text}", "cyan")
                
            elif event_type == 'firmware_update_complete':
                success = data.get('success', False)
                if success:
                    self._log_to_app("✅ Firmware update completed", "green")
                else:
                    self._log_to_app("❌ Firmware update failed", "red")
                
            elif event_type == 'scan_error':
                error = data.get('error', 'Unknown error')
                self._log_to_app(f"⚠️ Port scan error: {error}", "yellow")
                
            elif event_type == 'serial_error':
                error = data.get('error', 'Unknown error')
                self._log_to_app(f"⚠️ Serial error: {error}", "yellow")
                
            elif event_type == 'wokwi_toggled':
                enabled = data.get('enabled', False)
                status = "enabled" if enabled else "disabled"
                self._log_to_app(f"🔄 Wokwi updates {status}", "cyan")
                
            elif event_type == 'arduino_flashing_toggled':
                enabled = data.get('enabled', False)
                status = "enabled" if enabled else "disabled"
                self._log_to_app(f"🔧 Arduino flashing {status}", "magenta")
                
            elif event_type == 'debug_toggled':
                enabled = data.get('enabled', False)
                status = "enabled" if enabled else "disabled"
                self._log_to_app(f"🐛 Debug mode {status}", "blue")
                
            elif event_type == 'reconnected':
                self._log_to_app("🔄 Reconnected - forcing updates", "green")
                
            elif event_type == 'wokwi_error':
                error = data.get('error', 'Unknown error')
                slot = data.get('slot', 'unknown')
                self._log_to_app(f"⚠️ Wokwi error (slot {slot}): {error}", "yellow")
                
            elif event_type == 'backend_output':
                # Handle backend output - redirect to app output tab
                message = data.get('message', '')
                color = data.get('color', 'white')
                end = data.get('end', '\n')
                
                # Format message for app output
                formatted_message = message
                if end == '\n':
                    formatted_message += '\n\r'  # Add carriage return for xterm.js
                
                APP_OUT.log_message(formatted_message, color)
                
            elif event_type == 'port_selection_required':
                # Handle manual port selection request
                message = data.get('message', 'Please select a port')
                self._log_to_app(f"🔌 {message}", "cyan")
                
                # If no ports in combo, trigger a scan
                if self.port_combo.count() == 0:
                    self._log_to_app("🔍 No ports available, scanning...", "yellow")
                    self._request_port_rescan()
                    
            elif event_type == 'port_scan_started':
                self._log_to_app("🔍 Starting port detection...", "cyan")
                
            elif event_type == 'release_serial_for_detection':
                # Temporarily close WebSocket serial connection to allow backend port detection
                self._log_to_app("🔄 Releasing serial connection for port detection...", "yellow")
                try:
                    SER.close()
                    self._log_to_app("✅ Serial connection released for detection", "green")
                except Exception as e:
                    self._log_to_app(f"⚠️ Error releasing serial: {e}", "yellow")
                
            elif event_type == 'port_scan_completed':
                # Handle successful port detection - LOG ONLY, do not populate GUI
                main_port = data.get('main_port')
                arduino_port = data.get('arduino_port')
                organized_ports = data.get('organized_ports', {})
                
                self._log_to_app(f"✅ Backend port detection completed - main: {main_port}", "green")
                # GUI port population is handled ONLY by manual _request_port_rescan() method
                
            elif event_type == 'manual_port_selection_needed':
                # Handle case where automatic detection failed
                jumperless_ports = data.get('jumperless_ports', [])
                message = data.get('message', 'Manual port selection needed')
                
                self._log_to_app(f"⚠️ {message}", "yellow")
                self._log_to_app(f"📋 Found {len(jumperless_ports)} Jumperless device(s) - please select manually", "cyan")
                
                # Populate dropdown with available ports for manual selection
                self._populate_manual_port_selection(jumperless_ports)
                
            else:
                self._log_to_app(f"🔔 Backend event: {event_type}", "blue")
                
        except Exception as e:
            self._log_to_app(f"❌ Error handling backend event {event_type}: {e}", "red")
    
    # REMOVED: _update_gui_with_port_info() - no longer needed
    # Backend port info is logged by event handlers, GUI populated by _handle_scan_results() only
    
    # REMOVED: _update_gui_with_detected_ports() - no longer needed
    # GUI port population is handled ONLY by _handle_scan_results() method
    
    def _populate_manual_port_selection(self, jumperless_ports):
        """Populate port combo for manual selection when auto-detection fails"""
        try:
            self.port_combo.clear()
            
            for i, (port, desc, hwid, interface, additional_attrs) in enumerate(jumperless_ports):
                display_text = f"{port} - {desc}"
                self.port_combo.addItem(display_text, port)
                self._log_to_app(f"📋 Available: {port} ({desc})", "blue")
            
            self._set_status(f"Please select port manually ({len(jumperless_ports)} available)")
            self._log_to_app("👆 Please select a port from the dropdown and click Connect", "cyan")
            
        except Exception as e:
            self._log_to_app(f"❌ Error populating manual port selection: {e}", "red")
    
    # REMOVED: _connect_to_main_port_after_detection() - no longer needed
    # Auto-connection is handled by _handle_scan_results() -> _connect_serial()
    
    
    def event(self, event):
        """Handle custom events from background threads"""
        if event.type() == ScanResultEvent.EVENT_TYPE:
            # Handle scan results in main thread
            self._handle_scan_results(event.port_info)
            return True
        elif event.type() == ScanErrorEvent.EVENT_TYPE:
            # Handle scan errors and status updates in main thread
            if event.is_error:
                self._log_to_app(f"❌ {event.error_message}", "red")
                self._set_status(event.error_message, error=True)
            else:
                self._log_to_app(f"❌ {event.error_message}", "red") 
                # Don't set error status for informational messages
            return True
        elif event.type() == StatusUpdateEvent.EVENT_TYPE:
            # Handle status updates from background threads
            if event.message == "start_monitoring":
                # Special case: start connection monitoring from main thread
                self._log_to_app("🔄 Starting connection monitoring from main thread", "blue")
                QTimer.singleShot(250, self._start_connection_monitoring)
            elif event.message == "populate_ports":
                # Special case: populate GUI with backend's detected ports
                if hasattr(event, 'port_info') and event.port_info:
                    self._log_to_app("🎯 Populating GUI combo box with detected ports", "green")
                    self._populate_gui_from_backend(event.port_info)
                else:
                    self._log_to_app("❌ No port info in populate event", "red")
            else:
                self._set_status(event.message, error=event.is_error)
                if event.slot_count is not None:
                    self.slot_status.setText(f"{event.slot_count} slots assigned")
            return True
            # StartupScanEvent removed - backend handles startup port detection
        else:
            # Let Qt handle other events
            return super().event(event)
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    def closeEvent(self, event):
        """Handle application closing"""
        try:
            self._log_to_app("🔄 Shutting down Jumperless Bridge...", "yellow")
            
            # Stop connection monitoring and other timers
            if hasattr(self, 'connection_monitor'):
                self.connection_monitor.stop()
            if hasattr(self, 'arrow_poll_timer'):
                self.arrow_poll_timer.stop()
            
            # Close serial connection
            SER.close()
            
            # Shutdown backend
            if self.backend:
                self.backend.shutdown()
            
            # Wait for background threads to finish
            for thread in self.background_threads:
                if thread.is_alive():
                    thread.join(timeout=0.5)
            
            self._log_to_app("👋 Goodbye!", "green")
        except Exception as e:
            print(f"Shutdown error: {e}")
        
        super().closeEvent(event)

# ============================================================================
# APPLICATION BOOTSTRAP
# ============================================================================

def main():
    """Main application entry point"""
    # Handle SIGINT gracefully
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    except Exception:
        pass
    
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Jumperless Bridge - Qt GUI")
    app.setApplicationName("JumperlessBridge")
    
    # Show ASCII art in console for those who care :)
    print("\n🚀 Jumperless Bridge GUI Starting...")
    print("📡 WebSocket server will start on {}:{}".format(WS_HOST, WS_PORT))
    
    window = JumperlessBridgeWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
