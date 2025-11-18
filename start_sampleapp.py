#!/usr/bin/env python3
import argparse
import threading
import time
import secrets
import json

# ===== IMPORT CHUẨN: CHỈ WEAPROUS =====
from daemon.weaprous import WeApRous

# response được import tự động qua callback
from daemon.response import Response
from daemon.request import Request

# ==========================================
# SESSION STORE (session_id -> user)
# ==========================================

SESSIONS = {}
SESS_LOCK = threading.Lock()

def create_session(username: str) -> str:
    sid = secrets.token_hex(16)
    with SESS_LOCK:
        SESSIONS[sid] = {
            "username": username,
            "created_at": time.time()
        }
    return sid

def get_session_user(session_id: str):
    if not session_id:
        return None
    with SESS_LOCK:
        sess = SESSIONS.get(session_id)
        return sess["username"] if sess else None

def delete_session(session_id: str):
    with SESS_LOCK:
        if session_id in SESSIONS:
            del SESSIONS[session_id]


# ==========================================
# PEER WS PORT REGISTRY (peer_id -> port)
# ==========================================

PEER_WS_PORTS = {}
PEER_LOCK = threading.Lock()

def register_peer_ws(peer_id: str, ws_port: int):
    with PEER_LOCK:
        PEER_WS_PORTS[peer_id] = ws_port

def get_ws_port(peer_id: str, default_port=7000):
    with PEER_LOCK:
        return PEER_WS_PORTS.get(peer_id, default_port)


# ==========================================
# Helper: lấy body theo chuẩn (JSON > FORM)
# ==========================================

def get_request_data(request):
    data = request.json_data
    if not isinstance(data, dict) or not data:
        data = request.form_data
    if not isinstance(data, dict):
        data = {}
    return data


# ==========================================
# TẠO APP WeApRous
# ==========================================

app = WeApRous()


# ==========================================
# ROUTE /login
# ==========================================
@app.route("/login", methods=["POST"])
def handler_login(request: Request, response: Response):
    response.request = request
    data = get_request_data(request)

    username = data.get("username", "").strip()

    if not username:
        return response.build_json_response(
            json.dumps({"ok": False, "error": "unauthorized"}),
            status_code=401,
            reason="Unauthorized"
        )

    sid = create_session(username)
    peer_id = username
    ws_port = get_ws_port(peer_id)

    response.set_header("Set-Cookie", f"session={sid}; Path=/; HttpOnly")

    return response.build_json_response(
        json.dumps({
            "ok": True,
            "msg": "login success",
            "user": username,
            "peer_id": peer_id,
            "ws_port": ws_port
        }),
        200,
        "OK"
    )


# ==========================================
# ROUTE /logout
# ==========================================
@app.route("/logout", methods=["POST"])
def handler_logout(request: Request, response: Response):
    response.request = request

    sid = request.cookies.get("session")
    if sid:
        delete_session(sid)

    response.set_header(
        "Set-Cookie",
        "session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/"
    )

    return response.build_json_response(
        json.dumps({"ok": True, "msg": "logged out"}), 200, "OK"
    )


# ==========================================
# ROUTE /whoami
# ==========================================
@app.route("/whoami", methods=["GET"])
def handler_whoami(request: Request, response: Response):
    response.request = request

    sid = request.cookies.get("session")
    username = get_session_user(sid)

    if not username:
        return response.build_json_response(
            json.dumps({"ok": False, "error": "no session"}),
            401, "Unauthorized"
        )

    ws_port = get_ws_port(username)

    return response.build_json_response(
        json.dumps({
            "ok": True,
            "user": username,
            "ws_port": ws_port
        }),
        200, "OK"
    )


# ==========================================
# ROUTE /register_peer_ws
# ==========================================
@app.route("/register_peer_ws", methods=["POST"])
def handler_register_peer_ws(request: Request, response: Response):
    response.request = request
    data = request.json_data or {}

    peer_id = data.get("peer_id")
    ws_port = data.get("ws_port")

    try:
        ws_port = int(ws_port)
    except:
        ws_port = None

    if not peer_id or ws_port is None:
        return response.build_json_response(
            json.dumps({"ok": False, "error": "bad payload"}),
            400, "Bad Request"
        )

    register_peer_ws(peer_id, ws_port)
    print(f"[REGISTER] peer={peer_id} ws_port={ws_port}")

    return response.build_json_response(
        json.dumps({"ok": True, "msg": "registered"}), 200, "OK"
    )


# ==========================================
# MAIN — CHẠY CHUẨN CO3093/CO3094
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='CookieServer',
        epilog='Backend daemon'
    )
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=9000)

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    print(f"[+] Cookie/session backend running on http://{ip}:{port}")

    app.prepare_address(ip, port)
    app.run()
