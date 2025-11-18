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
import argparse
import time
from typing import Any, Dict
from daemon.tracker import Tracker
from daemon.weaprous import WeApRous
PORT = 5000

tracker = Tracker()
app = WeApRous()
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

tracker = Tracker()
app = WeApRous()

def get_request_data(request):
    data = getattr(request, "json_data", None)
    if not data:
        data = getattr(request, "form_data", None)
    if not isinstance(data, dict):
        data = {}
    return data

@app.route('/submit-info', methods=['PUT'])
def handler_submit_info(request, response):
    data = get_request_data(request)
    peer_id = data.get("peer_id")
    host    = data.get("ip")
    port    = data.get("port")
    print(f"[handler_submit_info] peer_id: {peer_id} host:{host} port:{port} ")
    if not peer_id or not host or port is None:
        body = json.dumps({"ok": False, "error": "missing fields"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    try:
        port = int(port)
        
        tracker.register(peer_id, host, port)

    except Exception as e:
        body = json.dumps({"ok": False, "error": "bad payload", "detail": str(e)})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    body = json.dumps({
        "ok": True,
        "peer": {
            "peer_id": peer_id,
            "ip": host,
            "port": port
        }
    })
 
    return response.build_json_response(body, status_code=200, reason="OK")

@app.route('/get-list', methods=['GET'])
def handler_get_list(request, response):
    peers = tracker.list_peers()
    body = json.dumps({"peers": peers})
    return response.build_json_response(body, status_code=200, reason="OK")

@app.route('/health', methods=['GET'])
def handler_health(request, response):
    """
    Return list of peers with metadata.
    """
    body = json.dumps({"status":"ok","now": time.time()})
    return response.build_json_response(body, status_code=200, reason="OK")

@app.route('/unregister', methods=['DELETE'])
def handler_unregister(request, response):
    """
    Unregister peer khỏi tracker.
    """
    data = get_request_data(request)
    peer_id = data.get("peer_id")

    # nếu thiếu peer_id -> 400
    if peer_id is None:
        body = json.dumps({"ok": False, "error": "missing fields"})
        return response.build_json_response(body, status_code=400, reason="Bad Request")

    tracker.unregister(peer_id)

    body = json.dumps({"result": "ok"})
    return response.build_json_response(body, status_code=200, reason="OK")



if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Tracker', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()