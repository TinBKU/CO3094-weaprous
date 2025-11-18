#!/usr/bin/env python3
"""
peer_web.py - Hybrid P2P Chat + Web UI Bridge (CO3094 style)

- P2P TCP message exchange between peers
- Tracker REST integration (register / list peers)
- WebSocket bridge từ browser <-> peer
- Middleware: có thể kiểm tra session cookie qua cookie_http_server /whoami
- Đăng ký ws_port với cookie_http_server /register_peer_ws
"""

import os
import socket
import threading
import json
import time
import argparse
import requests
import asyncio
import websockets
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# -----------------------------
# Config
# -----------------------------
TRACKER_URL = "http://127.0.0.1:5000"   # tracker_server.py
COOKIE_SERVER = "http://127.0.0.1:9000" # cookie_http_server.py

STATIC_HOST = "0.0.0.0"
DEFAULT_STATIC_PORT = 8000
DEFAULT_WS_PORT = 7000


def make_msg(channel, peer_id, text):
    return {
        "type": "msg",
        "channel": channel,
        "from": peer_id,
        "text": text,
        "ts": time.time(),
    }


# -----------------------------
# WebSocket Bridge
# -----------------------------
class WebSocketBridge:
    def __init__(self, ws_port, auth_mode="soft"):
        """
        auth_mode:
          - "strict": bắt buộc gọi /whoami, lỗi là từ chối WebSocket
          - "soft": cố gắng gọi /whoami, nếu lỗi network thì vẫn cho qua,
                    nhưng nếu server trả ok=false thì từ chối
          - "off": bỏ qua hoàn toàn bước /whoami (offline/dev)
        """
        self.clients = set()
        self.lock = threading.Lock()
        self.ws_port = ws_port
        self.peer_ref = None
        self.auth_mode = auth_mode

        # tạo event loop riêng cho WebSocket server
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._start_loop, daemon=True).start()

        # chạy HTTP/websocket server
        asyncio.run_coroutine_threadsafe(self._start_server(ws_port), self.loop)

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _start_server(self, ws_port):
        self.server = await websockets.serve(self._ws_handler, "0.0.0.0", ws_port)
        print(f"[WS] WebSocket server listening ws://127.0.0.1:{ws_port}/ws")

    async def _ws_handler(self, websocket, path=None):
        """
        Handler xử lý client WebSocket kết nối vào backend peer_web.
        Có middleware kiểm tra session cookie (tùy auth_mode).
        """

        # -----------------------------------------
        # Middleware kiểm tra session cookie
        # -----------------------------------------
        if self.auth_mode == "off":
            print("[WS] auth_mode=off, accept all WebSocket connections")
        else:
            headers = {}
            if hasattr(websocket, "request") and websocket.request:
                headers = websocket.request.headers
            elif hasattr(websocket, "request_headers"):
                headers = websocket.request_headers

            cookies = headers.get("Cookie", "")
            print("[WS] incoming cookies:", cookies)

            try:
                r = requests.get(
                    f"{COOKIE_SERVER}/whoami",
                    headers={"Cookie": cookies},
                    timeout=2,
                )
                info = r.json()

                if not r.ok or not info.get("ok"):
                    print("[WS] whoami failed:", r.status_code, info)
                    if self.auth_mode == "strict":
                        # strict: backend là bắt buộc
                        await websocket.close(code=4401, reason="Unauthorized")
                        return
                    else:
                        # soft: chỉ log, vẫn cho qua
                        print("[WS] auth_mode=soft, allow despite whoami not ok")
                else:
                    print("[WS] whoami ok. user:", info.get("user"))

            except Exception as e:
                print("[WS] whoami exception:", e)
                if self.auth_mode == "strict":
                    await websocket.close(code=4401, reason="Auth error")
                    return
                else:
                    print("[WS] auth_mode=soft, ignore whoami exception")

        # -----------------------------------------
        # Kết nối hợp lệ → client vào danh sách
        # -----------------------------------------
        print("[WS] client connected")
        with self.lock:
            self.clients.add(websocket)

        # Gửi event chào
        await websocket.send(json.dumps({
            "type": "connected",
            "peer_id": self.peer_ref.peer_id
        }))

        # -----------------------------------------
        # Nhận message từ UI
        # -----------------------------------------
        try:
            async for raw in websocket:
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue

                cmd = obj.get("cmd")
                if not cmd:
                    continue

                # xử lý command
                if cmd == "broadcast":
                    if self.peer_ref:
                        self.peer_ref.broadcast(
                            obj.get("channel", "general"),
                            obj.get("text", "")
                        )
                    else:
                        print("[WS] broadcast but peer_ref is None")
                        continue

                elif cmd == "connect":
                    # dùng tracker: peer_id -> ip, port
                    pid = obj.get("peer_id")
                    ok, info = self.peer_ref.connect_to_peer(pid)
                    await websocket.send(json.dumps({
                        "type": "connect_result",
                        "ok": ok,
                        "info": info,
                    }))

                elif cmd == "connect_manual":
                    # offline/manual: ip + port
                    ip = obj.get("ip")
                    port = obj.get("port")
                    try:
                        port = int(port)
                    except Exception:
                        port = None

                    if not ip or port is None:
                        await websocket.send(json.dumps({
                            "type": "connect_result",
                            "ok": False,
                            "info": "missing ip/port"
                        }))
                    else:
                        ok, info = self.peer_ref.connect_to_addr(ip, port)
                        await websocket.send(json.dumps({
                            "type": "connect_result",
                            "ok": ok,
                            "info": info,
                        }))

                elif cmd == "create_room":
                    room = obj["channel"]
                    to_peer = obj.get("to_peer")

                    self.peer_ref.join_channel(room)
                    self.push_event({"type": "joined_channel", "channel": room})

                    if to_peer:
                        print(f"[WS] create_room -> to_peer={to_peer}")
                        ok, info = self.peer_ref.send_direct(to_peer, "__meta__", f"join:{room}")
                        print(f"[WS] send_direct meta join:{room} to {to_peer} -> ok={ok}, info={info}")

                        # fallback: nếu gửi direct fail thì broadcast cho tất cả
                        if not ok:
                            print("[WS] send_direct failed, fallback to broadcast __meta__")
                            self.peer_ref.broadcast("__meta__", f"join:{room}")
                    else:
                        self.peer_ref.broadcast("__meta__", f"join:{room}")


                elif cmd == "join":
                    room = obj["channel"]
                    if room == "__meta__":  # tránh lỗi
                        continue

                    self.peer_ref.join_channel(room)
                    self.push_event({"type": "joined_channel", "channel": room})

                elif cmd == "list_peers":
                    self.peer_ref.fetch_peers()
                    await websocket.send(json.dumps({
                        "type": "peers",
                        "peers": self.peer_ref.known_peers
                    }))

                elif cmd == "direct_msg":
                    to_peer = obj["to_peer"]
                    text = obj["text"]
                    ch = obj.get("channel")
                    ok, info = self.peer_ref.send_direct(to_peer, ch, text)
                    await websocket.send(json.dumps({
                        "type": "direct_result",
                        "ok": ok,
                        "info": info,
                    }))

        except websockets.exceptions.ConnectionClosed:
            pass

        finally:
            print("[WS] client disconnected")
            with self.lock:
                self.clients.discard(websocket)

    # ==========================================================
    # _broadcast(): gửi đến tất cả client WebSocket
    # ==========================================================
    async def _broadcast(self, data: str):
        """
        Gửi 1 JSON string đến tất cả client WebSocket đã kết nối.
        """
        with self.lock:
            clients = list(self.clients)

        for ws in clients:
            try:
                await ws.send(data)
            except:
                # nếu gửi lỗi → remove client
                with self.lock:
                    if ws in self.clients:
                        self.clients.remove(ws)

    # ==========================================================
    # push_event → schedule _broadcast()
    # ==========================================================
    def push_event(self, event_obj):
        """
        Đẩy event từ backend peer → UI React qua WebSocket.
        """
        data = json.dumps(event_obj)
        asyncio.run_coroutine_threadsafe(
            self._broadcast(data),
            self.loop
        )


# -----------------------------
# Peer (P2P TCP)
# -----------------------------
class Peer:
    def __init__(self, peer_id, listen_ip, listen_port, ws_bridge):
        self.peer_id = peer_id
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.ws_bridge = ws_bridge

        self.running = True
        self.connections = {}  # peer_id (hoặc ip:port) -> socket
        self.conn_lock = threading.Lock()

        self.channels = {"general"}
        self.current_channel = "general"

        self.known_peers = {}

    # --- Tracker interaction ---
    def register_with_tracker(self):
        try:
            requests.put(
                TRACKER_URL + "/submit-info",
                json={
                    "peer_id": self.peer_id,
                    "ip": self.listen_ip,
                    "port": self.listen_port,
                },
                timeout=2,
            )
            print(f"[Tracker] registered {self.peer_id}")
        except Exception as e:
            print("[Tracker] register failed:", e)

    def unregister_with_tracker(self):
        try:
            requests.delete(
                TRACKER_URL + "/unregister",
                json={"peer_id": self.peer_id},
                timeout=2,
            )
        except Exception as e:
            print("[Tracker] unregister failed:", e)

    def fetch_peers(self):
        try:
            res = requests.get(TRACKER_URL + "/get-list", timeout=2).json()
            peers = res.get("peers", [])
            self.known_peers = {
                p["peer_id"]: {"ip": p["ip"], "port": p["port"]}
                for p in peers
                if p["peer_id"] != self.peer_id
            }
            print("[Peer] known_peers:", self.known_peers)
        except Exception as e:
            print("[Tracker] fetch_peers failed:", e)

    # --- TCP server ---
    def start_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((self.listen_ip, self.listen_port))
            s.listen(50)
            self.server_sock = s
            print(f"[Peer] listening TCP {self.listen_ip}:{self.listen_port}")
        except Exception as e:
            print(f"[Peer] failed to bind {self.listen_ip}:{self.listen_port} -> {e}")
            raise
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self.running:
            try:
                conn, _ = self.server_sock.accept()
                threading.Thread(target=self._peer_handler, args=(conn,), daemon=True).start()
            except Exception:
                break

    # --- outbound connect (dùng tracker) ---
    def connect_to_peer(self, peer_id):
        info = self.known_peers.get(peer_id)
        if not info:
            return False, "Peer not found in tracker"

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((info["ip"], info["port"]))
            s.sendall(json.dumps({"type": "intro", "peer_id": self.peer_id}).encode() + b"\n")
            with self.conn_lock:
                self.connections[peer_id] = s
            threading.Thread(target=self._peer_reader, args=(peer_id, s), daemon=True).start()
            self.ws_bridge.push_event({"type": "peer_connected", "peer_id": peer_id})
            return True, "connected"
        except Exception as e:
            return False, str(e)

    # --- outbound connect (manual, không tracker) ---
    def connect_to_addr(self, ip, port):
        """
        Kết nối thẳng tới 1 peer bằng ip/port, không cần tracker.
        Peer key tạm là "ip:port".
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            # gửi intro với peer_id của mình
            s.sendall(json.dumps({"type": "intro", "peer_id": self.peer_id}).encode() + b"\n")

            peer_key = f"{ip}:{port}"
            with self.conn_lock:
                self.connections[peer_key] = s

            threading.Thread(target=self._peer_reader, args=(peer_key, s), daemon=True).start()
            self.ws_bridge.push_event({"type": "peer_connected", "peer_id": peer_key})
            return True, f"connected to {ip}:{port}"
        except Exception as e:
            return False, str(e)

    def _peer_handler(self, conn):
        """
        Xử lý kết nối inbound (mình là server, peer kia connect vào).
        Logic xử lý message sau khi đã intro giống với _peer_reader:
        - xử lý __meta__ (join room) trước
        - sau đó mới xử lý msg thường
        """
        remote_id = None
        try:
            f = conn.makefile("rb")
            while True:
                line = f.readline()
                if not line:
                    break

                try:
                    obj = json.loads(line.decode().strip())
                except Exception:
                    continue

                # Bước 1: xử lý intro để biết remote_id
                if obj.get("type") == "intro":
                    remote_id = obj["peer_id"]
                    with self.conn_lock:
                        self.connections[remote_id] = conn
                    self.ws_bridge.push_event({
                        "type": "peer_connected",
                        "peer_id": remote_id
                    })
                    continue  # đọc message tiếp theo

                # Bước 2: xử lý meta channel giống _peer_reader
                ch = obj.get("channel")
                if ch == "__meta__":
                    text = obj.get("text", "")
                    if isinstance(text, str) and text.startswith("join:"):
                        room = text.split(":", 1)[1]
                        self.join_channel(room)
                        self.ws_bridge.push_event({
                            "type": "joined_channel",
                            "channel": room,
                        })
                    # không đưa __meta__ xuống _handle_incoming_msg
                    continue

                # Bước 3: message thường
                if obj.get("type") == "msg":
                    self._handle_incoming_msg(obj)

        except Exception as e:
            print("[Peer] _peer_handler error:", e)
        finally:
            # nếu biết remote_id thì cleanup connections + báo UI
            if remote_id is not None:
                with self.conn_lock:
                    self.connections.pop(remote_id, None)
                self.ws_bridge.push_event({
                    "type": "peer_disconnected",
                    "peer_id": remote_id
                })
            else:
                try:
                    conn.close()
                except Exception:
                    pass


    def _peer_reader(self, peer_id, sock):
        try:
            f = sock.makefile("rb")
            while True:
                line = f.readline()
                if not line:
                    break
                try:
                    obj = json.loads(line.decode().strip())
                except Exception:
                    continue

                # meta channel
                ch = obj.get("channel")
                if ch == "__meta__":
                    text = obj.get("text", "")
                    if isinstance(text, str) and text.startswith("join:"):
                        room = text.split(":", 1)[1]
                        self.join_channel(room)
                        self.ws_bridge.push_event({
                            "type": "joined_channel",
                            "channel": room,
                        })
                    continue

                if obj.get("type") == "msg":
                    self._handle_incoming_msg(obj)
        except Exception as e:
            print("[Peer] _peer_reader error:", e)
        finally:
            with self.conn_lock:
                self.connections.pop(peer_id, None)
            self.ws_bridge.push_event({"type": "peer_disconnected", "peer_id": peer_id})

    def _handle_incoming_msg(self, obj):
        ch = obj.get("channel", "general")

        # --- Bảo vệ DM: nếu là dm:a:b mà mình không phải a/b => bỏ qua ---
        if ch.startswith("dm:"):
            parts = ch.split(":")
            # format dm:peerA:peerB
            if len(parts) == 3:
                allowed = {parts[1], parts[2]}
                if self.peer_id not in allowed:
                    print(f"[Peer] ignore DM for others: ch={ch}, me={self.peer_id}")
                    return

        # auto join nếu chưa có (chỉ cho kênh hợp lệ)
        if ch not in self.channels:
            self.join_channel(ch)
            self.ws_bridge.push_event({"type": "joined_channel", "channel": ch})

        # push ra UI
        self.ws_bridge.push_event({"type": "msg", "payload": obj})

    # --- broadcast ---
    def broadcast(self, channel, text):
        """
        Gửi message tới các peer đã connect.
        - "__meta__": luôn gửi cho tất cả (control).
        - "dm:a:b": chỉ gửi cho đúng 2 peer a, b.
        - kênh thường: gửi cho tất cả connections.
        """
        msg = make_msg(channel, self.peer_id, text)
        print("[DEBUG] broadcasting:", msg)
        data = (json.dumps(msg) + "\n").encode()

        with self.conn_lock:
            peers_snapshot = list(self.connections.items())

        # --- Meta channel: gửi cho tất cả ---
        if channel == "__meta__":
            for pid, sock in peers_snapshot:
                try:
                    sock.sendall(data)
                except Exception as e:
                    print(f"[Peer] meta send to {pid} failed:", e)
                    with self.conn_lock:
                        self.connections.pop(pid, None)
            return

        # --- DM channel: dm:userA:userB -> chỉ gửi cho 2 người đó ---
        dm_targets = None
        if channel.startswith("dm:"):
            parts = channel.split(":")
            if len(parts) == 3:
                dm_targets = {parts[1], parts[2]}

        for pid, sock in peers_snapshot:
            # nếu là DM mà pid không thuộc 2 người, bỏ qua
            if dm_targets is not None and pid not in dm_targets:
                continue

            try:
                sock.sendall(data)
            except Exception as e:
                print(f"[Peer] send to {pid} failed:", e)
                with self.conn_lock:
                    self.connections.pop(pid, None)

        # echo local cho UI peer gửi
        self.ws_bridge.push_event({"type": "msg", "payload": msg})

    # --- Gửi meta/message trực tiếp tới 1 peer ---
    def send_direct(self, peer_id, channel, text):
        """
        Gửi 1 message tới đúng peer_id (dùng cho DM/meta như join:room).
        Trả về (ok, info).
        """
        msg = make_msg(channel, self.peer_id, text)
        data = (json.dumps(msg) + "\n").encode()

        with self.conn_lock:
            sock = self.connections.get(peer_id)

        if not sock:
            print(f"[Peer] send_direct: no connection to {peer_id}")
            return False, "no connection"

        try:
            sock.sendall(data)
            return True, "sent"
        except Exception as e:
            print(f"[Peer] send_direct to {peer_id} failed: {e}")
            with self.conn_lock:
                self.connections.pop(peer_id, None)
            return False, str(e)

    def join_channel(self, channel):
        self.channels.add(channel)

    def shutdown(self):
        self.running = False
        self.unregister_with_tracker()
        with self.conn_lock:
            for sock in self.connections.values():
                try:
                    sock.close()
                except Exception:
                    pass
            self.connections.clear()


# -----------------------------
# Static file server (optional)
# -----------------------------
def start_static_server(static_port):
    static_folder = os.path.join(os.getcwd(), "static")
    os.makedirs(static_folder, exist_ok=True)
    os.chdir(static_folder)
    server = ThreadingHTTPServer((STATIC_HOST, static_port), SimpleHTTPRequestHandler)
    print(f"[HTTP] Static files at http://127.0.0.1:{static_port}/")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def register_ws_port_with_cookie_server(peer_id, ws_port):
    try:
        requests.post(
            f"{COOKIE_SERVER}/register_peer_ws",
            json={"peer_id": peer_id, "ws_port": ws_port},
            timeout=2,
        )
        print(f"[CookieServer] registered ws_port={ws_port} for peer_id={peer_id}")
    except Exception as e:
        print("[CookieServer] register_ws_port failed:", e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default="admin")  # nên trùng username để login mapping đơn giản
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--static-port", type=int, default=DEFAULT_STATIC_PORT)
    parser.add_argument("--ws-port", type=int, default=DEFAULT_WS_PORT)

    # mode cho tracker & cookie & auth
    parser.add_argument("--no-tracker", action="store_true", help="Disable tracker register/fetch")
    parser.add_argument("--no-cookie", action="store_true", help="Disable register_ws_port to cookie server")
    parser.add_argument(
        "--auth-mode",
        choices=["strict", "soft", "off"],
        default="soft",
        help="WebSocket auth mode with cookie server (/whoami)"
    )

    args = parser.parse_args()

    # optional static server (có thể không dùng nếu chạy Vite dev)
    start_static_server(args.static_port)

    ws = WebSocketBridge(ws_port=args.ws_port, auth_mode=args.auth_mode)
    peer = Peer(args.id, args.host, args.port, ws)
    ws.peer_ref = peer

    peer.start_server()

    # dùng tracker khi không tắt
    if not args.no_tracker:
        peer.register_with_tracker()
        peer.fetch_peers()

    # đăng ký ws_port với cookie server để /login trả về
    if not args.no_cookie:
        register_ws_port_with_cookie_server(peer.peer_id, args.ws_port)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        peer.shutdown()


if __name__ == "__main__":
    main()
