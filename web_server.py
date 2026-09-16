import os
import json
import time
import asyncio
import http.server
import socketserver
import threading
import webbrowser
from utils import read_config, write_config

# SIGNATURE: DEPLOYED_BY_RAYZIEN_SECURE_HASH_8F3B92

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "pages", "index.html")

WS_CLIENTS = set()
LOGS = []
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            entries = []
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                if content.startswith("["):
                    return json.loads(content)
                for line in content.splitlines():
                    line_str = line.strip()
                    if line_str:
                        try:
                            entries.append(json.loads(line_str))
                        except Exception: pass
            return entries
        except Exception as e:
            print(f"[HISTORY] Error loading history: {e}")
    return []

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            for entry in STRUCTURED_LOGS:
                f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[HISTORY] Error saving history: {e}")

STRUCTURED_LOGS = load_history()

_loop = None

def get_sf_time_str():
    from datetime import datetime, timezone, timedelta
    now_utc = datetime.now(timezone.utc)
    sf_time = now_utc - timedelta(hours=8)
    return sf_time.strftime("%H:%M:%S")

def add_log(msg):
    global _loop
    t_str = get_sf_time_str()
    log_entry = {"time": t_str, "msg": msg}
    LOGS.append(log_entry)
    if len(LOGS) > 500:
        LOGS.pop(0)
    
    _broadcast(json.dumps({"type": "log", "data": log_entry}))

def add_log_structured(name, rarity, image_url="", details="", bot_source="STORMGOD", status="success"):
    t_str = get_sf_time_str()
    log_entry = {
        "time": t_str,
        "name": name,
        "rarity": rarity,
        "image_url": image_url,
        "details": details,
        "bot_source": bot_source,
        "status": status
    }
    STRUCTURED_LOGS.insert(0, log_entry)
    if len(STRUCTURED_LOGS) > 1000:
        STRUCTURED_LOGS.pop()
        
    save_history()
    _broadcast(json.dumps({"type": "structured_log", "data": log_entry}))

def clear_history():
    global STRUCTURED_LOGS
    STRUCTURED_LOGS = []
    save_history()
    _broadcast(json.dumps({"type": "history_cleared"}))

def broadcast_engine_state(state, image_url=""):
    _broadcast(json.dumps({"type": "engine_state", "data": state, "image_url": image_url}))

def broadcast_balance(coins):
    try:
        config = read_config()
        config["credits_balance"] = str(coins)
        write_config(config)
    except: pass
    _broadcast(json.dumps({"type": "balance_update", "data": str(coins)}))

def _broadcast(message):
    global _loop
    if _loop and WS_CLIENTS:
        try:
            asyncio.run_coroutine_threadsafe(_async_broadcast(message), _loop)
        except Exception:
            pass

async def _async_broadcast(message):
    global WS_CLIENTS
    disconnected = set()
    for ws in WS_CLIENTS.copy():
        try:
            await ws.send(message)
        except Exception:
            disconnected.add(ws)
    if disconnected:
        WS_CLIENTS -= disconnected

async def _ws_handler(websocket):
    global WS_CLIENTS
    WS_CLIENTS.add(websocket)
    add_log("Dashboard client connected. STORM GOD (v5.0.0)")
    add_log("⭐ Support STORMGOD development! Check Premium (/pages/premium.html)")
    try:
        config = read_config()
        await websocket.send(json.dumps({"type": "config", "data": config}))
        await websocket.send(json.dumps({"type": "logs", "data": LOGS[-50:]}))
        await websocket.send(json.dumps({"type": "structured_logs", "data": STRUCTURED_LOGS}))
        await websocket.send(json.dumps({"type": "balance_update", "data": config.get("credits_balance", "0")}))

        async for message in websocket:
            try:
                msg = json.loads(message)
                msg_type = msg.get("type")

                if msg_type == "update_config":
                    config = read_config()
                    config.update(msg.get("data", {}))
                    write_config(config)
                    add_log(f"Config updated: {list(msg.get('data', {}).keys())}")
                    await _async_broadcast(json.dumps({"type": "config", "data": config}))

                elif msg_type == "trigger_spammer":
                    val = msg.get("enabled", False)
                    config = read_config()
                    config["spam_enabled"] = "true" if val else "false"
                    write_config(config)
                    add_log(f"Spammer toggled: {val}")
                    await _async_broadcast(json.dumps({"type": "config", "data": config}))

                elif msg_type == "clear_history":
                    clear_history()

            except Exception as e:
                print(f"[WS] Message parse error: {e}")
    except Exception as e:
        print(f"[WS] Client error: {e}")
    finally:
        WS_CLIENTS.discard(websocket)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            if os.path.exists(INDEX_FILE):
                with open(INDEX_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"<h1>STORMGOD Dashboard Index Not Found</h1>")
            return

        if self.path.startswith("/api/config"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            cfg = read_config()
            self.wfile.write(json.dumps(cfg).encode("utf-8"))
            return

        if self.path.startswith("/api/discord/me"):
            from urllib.parse import parse_qs, urlparse
            query_components = parse_qs(urlparse(self.path).query)
            token = query_components.get("token", [""])[0]
            if not token:
                cfg = read_config()
                token = cfg.get("token", "")

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            if not token or token == "YOUR_TOKEN_HERE":
                self.wfile.write(json.dumps({"error": "No token provided"}).encode("utf-8"))
                return

            try:
                import requests
                headers = {"Authorization": token, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=6)
                if r.status_code == 200:
                    self.wfile.write(r.text.encode("utf-8"))
                else:
                    self.wfile.write(json.dumps({"error": f"Discord API error {r.status_code}"}).encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/config"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                data = json.loads(body)
                config = read_config()
                config.update(data)
                write_config(config)
                add_log(f"Config updated via HTTP: {list(data.keys())}")
                _broadcast(json.dumps({"type": "config", "data": config}))
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "config": config}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def start_server(http_port=8085, ws_port=8086, open_browser=True):
    def run_http():
        try:
            handler = CustomHTTPRequestHandler
            socketserver.TCPServer.allow_reuse_address = True
            with socketserver.TCPServer(("", http_port), handler) as httpd:
                print(f"\033[92m[STORMGOD] HTTP Web Dashboard listening on port {http_port}\033[0m")
                httpd.serve_forever()
        except Exception as e:
            print(f"[STORMGOD] HTTP Server failed: {e}")

    def run_ws():
        nonlocal ws_port
        try:
            import websockets
            global _loop
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
            
            start_server_fut = websockets.serve(_ws_handler, "0.0.0.0", ws_port)
            _loop.run_until_complete(start_server_fut)
            print(f"\033[92m[STORMGOD] WebSocket Server listening on port {ws_port}\033[0m")
            _loop.run_forever()
        except Exception as e:
            print(f"[STORMGOD] WS Server failed on port {ws_port}: {e}")

    threading.Thread(target=run_http, daemon=True).start()
    threading.Thread(target=run_ws, daemon=True).start()

    if open_browser:
        def open_b():
            time.sleep(1.5)
            try:
                webbrowser.open(f"http://localhost:{http_port}")
            except Exception: pass
        threading.Thread(target=open_b, daemon=True).start()
