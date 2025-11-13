#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import logging
import socket
import argparse
import threading
import time
from typing import Dict

from daemon.weaprous import WeApRous

# config
PORT = 8000
PEER_TTL = 180
CLEANUP_INTERVAL = 30
TCP_CONNECT_TIMEOUT = 4  # seconds for outgoing P2P connect
MAX_BODY_BYTES = 128 * 1024  # 128KB

# logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

app = WeApRous()

# state
peers: Dict[str, Dict[str, Any]] = {}   # peer_id -> {"host":..., "port":..., "files": [...], "last_seen": ts}
peers_lock = threading.Lock()

channels: Dict[str, Dict[str, Any]] = {}  # optional if you implement channels
channels_lock = threading.Lock()

# -------------------------------------------------------------------
# Helper đọc dữ liệu JSON / form từ Request
# -------------------------------------------------------------------
def get_request_data(request):
    """
    Lấy dữ liệu body từ request:
    - Ưu tiên request.json_data
    - Nếu không có thì dùng request.form_data
    """
    data = getattr(request, "json_data", None)
    if not data:
        data = getattr(request, "form_data", None)
    if not isinstance(data, dict):
        data = {}
    return data


# -------------------------------------------------------------------
# Login API (JSON)
# -------------------------------------------------------------------
@app.route('/login', methods=['POST'])
def handle_api_login(request, response):
    """
    Xử lý login cho API, trả về JSON.
    Yêu cầu: {"username":"admin","password":"password"}
    """
    logging.info("Handling POST /login (JSON Response)...")

    data = get_request_data(request)
    username = data.get('username')
    password = data.get('password')

    if username == 'admin' and password == 'password':
        # 200 OK
        body = json.dumps({"ok": True, "message": "Logged in"})
        return response.build_json_response(body, status_code=200, reason="OK")
    else:
        # 401 Unauthorized
        body = json.dumps({"ok": False, "error": "Unauthorized"})
        return response.build_json_response(body, status_code=401, reason="Unauthorized")


# -------------------------------------------------------------------
# /submit-info : đăng ký peer
# -------------------------------------------------------------------
@app.route('/submit-info', methods=['POST'])
def handler_submit_info(request, response):
    """
    Register or update a peer:
    Body JSON: {"peer_id":"peer1","host":"1.2.3.4","port":10001}
    """
    data = get_request_data(request)
    peer_id = data.get("peer_id")
    host = data.get("host")
    port = data.get("port")

    if not peer_id or not host or port is None:
        body = json.dumps({"ok": False, "error": "missing fields"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    try:
        port = int(port)
        if not (1 <= port <= 65535):
            raise ValueError("port out of range")
    except Exception:
        body = json.dumps({"ok": False, "error": "invalid port"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    with peers_lock:
        peers[peer_id] = {
            "host": host,
            "port": port,
            "files": [],
            "last_seen": time.time()
        }

    logging.info("submit-info: %s -> %s:%s", peer_id, host, port)
    body = json.dumps({"ok": True, "peer": peer_id})
    return response.build_json_response(body, status_code=200, reason="OK")

# -------------------------------------------------------------------
# /add-list : cập nhật danh sách files của peer
# -------------------------------------------------------------------
@app.route('/add-list', methods=['PUT'])
def handler_add_list(request, response):
    """
    Update files list for a peer.
    Body JSON: {"peer_id":"peer1","files":[...]}
    """
    data = get_request_data(request)
    pid = data.get("peer_id")
    files = data.get("files", [])

    if not pid:
        body = json.dumps({"ok": False, "error": "missing peer_id"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    if not isinstance(files, list):
        body = json.dumps({"ok": False, "error": "files must be list"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    with peers_lock:
        if pid in peers:
            peers[pid]["files"] = files
            peers[pid]["last_seen"] = time.time()
            logging.info("add-list: updated files for %s (%d files)", pid, len(files))
            body = json.dumps({"ok": True})
            return response.build_json_response(body, status_code=200, reason="OK")
        else:
            body = json.dumps({"ok": False, "error": "unknown peer"})
            return response.build_json_response(body, status_code=404, reason="Not Found")


# -------------------------------------------------------------------
# /get-list : trả danh sách peers
# -------------------------------------------------------------------
@app.route('/get-list', methods=['GET'])
def handler_get_list(request, response):
    """
    Return list of peers with metadata.
    """
    with peers_lock:
        out = []
        for pid, info in peers.items():
            out.append({
                "peer_id": pid,
                "host": info["host"],
                "port": info["port"],
                "files": info.get("files", [])
            })

    body = json.dumps({"peers": out})
    return response.build_json_response(body, status_code=200, reason="OK")


# -------------------------------------------------------------------
# Helper TCP gửi message tới peer
# -------------------------------------------------------------------
def _tcp_send(host, port, payload_json: str):
    """
    Helper: open TCP connection to host:port, send payload_json (string),
    return (ok, detail)
    """
    try:
        with socket.create_connection((host, int(port)), timeout=TCP_CONNECT_TIMEOUT) as s:
            s.sendall((payload_json + "\n").encode('utf-8'))
        return True, None
    except Exception as e:
        return False, str(e)
@app.route('/create-channel', methods=['POST'])
def handler_create_channel(request, response):
    """
    Tạo một kênh chat mới.
    Body JSON: {"channel": "room1", "owner": "peerA"}
    """
    data = get_request_data(request)
    ch = data.get("channel")
    owner = data.get("owner")

    if not ch or not owner:
        body = json.dumps({"ok": False, "error": "missing fields"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    with channels_lock:
        if ch in channels:
            body = json.dumps({"ok": False, "error": "channel exists"})
            return response.build_json_response(body, status_code=409, reason="Conflict")

        channels[ch] = {
            "owner": owner,
            "members": set([owner]),
            "created": time.time()
        }

    body = json.dumps({"ok": True, "channel": ch})
    return response.build_json_response(body, status_code=201, reason="Created")


@app.route('/join-channel', methods=['POST'])
def handler_join_channel(request, response):
    """
    Tham gia một kênh chat.
    Body JSON: {"channel": "room1", "peer_id": "peerB"}
    """
    data = get_request_data(request)
    ch = data.get("channel")
    pid = data.get("peer_id")

    if not ch or not pid:
        body = json.dumps({"ok": False, "error": "missing fields"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    with channels_lock:
        if ch not in channels:
            body = json.dumps({"ok": False, "error": "channel not found"})
            return response.build_json_response(body, status_code=404, reason="Not Found")

        channels[ch]["members"].add(pid)
        members_list = list(channels[ch]["members"])

    body = json.dumps({
        "ok": True,
        "channel": ch,
        "members": members_list
    })
    return response.build_json_response(body, status_code=200, reason="OK")


@app.route('/list-channels', methods=['GET'])
def handler_list_channels(request, response):
    """
    Liệt kê tất cả channel hiện có cùng owner và members.
    """
    with channels_lock:
        out = [
            {
                "name": name,
                "owner": ch["owner"],
                "members": list(ch["members"])
            }
            for name, ch in channels.items()
        ]

    body = json.dumps({"channels": out})
    return response.build_json_response(body, status_code=200, reason="OK")

# -------------------------------------------------------------------
# /send-peer : gửi tới 1 peer
# -------------------------------------------------------------------
@app.route('/send-peer', methods=['POST'])
def handler_send_peer(request, response):
    """
    Relay a message to a single peer (tracker acts as short-lived relay).
    Body: {"to":"peerB","from":"peerA","message":"..."}
    """
    data = get_request_data(request)
    to = data.get("to")
    frm = data.get("from")
    message = data.get("message")

    if not to or not frm or message is None:
        body = json.dumps({"ok": False, "error": "missing fields"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    with peers_lock:
        target = peers.get(to)

    if not target:
        body = json.dumps({"ok": False, "error": "peer not found"})
        return response.build_json_response(body, status_code=404, reason="Not Found")

    payload = json.dumps({
        "type": "message",
        "from": frm,
        "to": to,
        "payload": message,
        "ts": time.time()
    })
    ok, detail = _tcp_send(target["host"], target["port"], payload)

    if ok:
        body = json.dumps({"ok": True})
        return response.build_json_response(body, status_code=200, reason="OK")
    else:
        logging.warning("send-peer: failed to %s: %s", to, detail)
        body = json.dumps({"ok": False, "error": "connect_failed", "detail": detail})
        return response.build_json_response(body, status_code=500, reason="Internal Server Error")


# -------------------------------------------------------------------
# /broadcast-peer : gửi tới tất cả peer (trừ sender)
# -------------------------------------------------------------------
@app.route('/broadcast-peer', methods=['POST'])
def handler_broadcast_peer(request, response):
    """
    Forward message to all peers in registry (fire-and-forget per peer via
    background threads), returns immediate acknowledgement.
    Body: {"from":"peerA","message":"text"}
    """
    data = get_request_data(request)
    frm = data.get("from")
    message = data.get("message")

    if not frm or message is None:
        body = json.dumps({"ok": False, "error": "missing fields"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    with peers_lock:
        target_list = [
            (pid, info["host"], info["port"])
            for pid, info in peers.items()
            if pid != frm
        ]

    results = []

    def send_worker(pid, host, port):
        payload = json.dumps({
            "type": "message",
            "from": frm,
            "to": pid,
            "payload": message,
            "ts": time.time()
        })
        ok, detail = _tcp_send(host, port, payload)
        results.append({"peer": pid, "ok": ok, "detail": detail})

    threads = []
    for pid, host, port in target_list:
        t = threading.Thread(target=send_worker,
                             args=(pid, host, port),
                             daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=2.0)

    body = json.dumps({
        "ok": True,
        "attempted": len(target_list),
        "results_sample": results[:20]
    })
    return response.build_json_response(body, status_code=200, reason="OK")


@app.route('/connect-peer', methods=['POST'])
def handler_connect_peer(request, response):
    """
    Help two peers connect:
    Body: {"from":"peerA","to":"peerB", "mode":"info"|"attempt-tracker"}
    mode="info": tracker trả về host/port của peerB để peerA tự connect.
    mode="attempt-tracker": tracker thử mở TCP tới peerB (ít dùng, có thể fail do NAT).
    """
    data = get_request_data(request)  # dùng helper giống các API khác

    frm = data.get("from")
    to = data.get("to")
    mode = data.get("mode", "info")

    if not frm or not to:
        body = json.dumps({"ok": False, "error": "missing fields"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    with peers_lock:
        target = peers.get(to)
        requester = peers.get(frm)

    if not target:
        body = json.dumps({"ok": False, "error": "target not found"})
        return response.build_json_response(body, status_code=404, reason="Not Found")

    if mode == "info":
        # Trả về địa chỉ của peer đích cho client tự tạo kết nối TCP
        body = json.dumps({
            "ok": True,
            "target": {
                "host": target["host"],
                "port": target["port"]
            }
        })
        return response.build_json_response(body, status_code=200, reason="OK")

    elif mode == "attempt-tracker":
        # Tracker thử mở TCP tới peer đích (thường chỉ dùng test, không reliable qua NAT)
        payload = json.dumps({
            "type": "connect-probe",
            "from": frm,
            "to": to,
            "ts": time.time()
        })
        ok, detail = _tcp_send(target["host"], target["port"], payload)
        if ok:
            body = json.dumps({"ok": True, "note": "tracker attempted connect"})
            return response.build_json_response(body, status_code=200, reason="OK")
        else:
            body = json.dumps({
                "ok": False,
                "error": "connect_failed",
                "detail": detail
            })
            return response.build_json_response(body, status_code=500, reason="Internal Server Error")

    else:
        body = json.dumps({"ok": False, "error": "unknown mode"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")
# cleanup thread
def cleanup_loop():
    logging.info("cleanup thread started (TTL=%s)", PEER_TTL)
    while True:
        now = time.time()
        removed = []
        with peers_lock:
            for pid, info in list(peers.items()):
                if now - info.get("last_seen", 0) > PEER_TTL:
                    removed.append(pid)
                    del peers[pid]
        if removed:
            logging.info("cleanup removed peers: %s", removed)
            # remove from channels if needed
            with channels_lock:
                for ch in channels.values():
                    ch["members"] -= set(removed)
        time.sleep(CLEANUP_INTERVAL)


# start cleanup once
threading.Thread(target=cleanup_loop, daemon=True).start()

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()