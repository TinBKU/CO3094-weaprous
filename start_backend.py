# #
# # Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# # All rights reserved.
# # This file is part of the CO3093/CO3094 course,
# # and is released under the "MIT License Agreement". Please see the LICENSE
# # file that should have been included as part of this package.
# #
# # WeApRous release
# #
# # The authors hereby grant to Licensee personal permission to use
# # and modify the Licensed Source Code for the sole purpose of studying
# # while attending the course
# #


# """
# start_backend
# ~~~~~~~~~~~~~~~~~

# This module provides a simple entry point for deploying backend server process
# using the socket framework. It parses command-line arguments to configure the
# server's IP address and port, and then launches the backend server.
# """

# import socket
# import argparse

# from daemon import create_backend

# # Default port number used if none is specified via command-line arguments.
# PORT = 9000 

# if __name__ == "__main__":
#     """
#     Entry point for launching the backend server.

#     This block parses command-line arguments to determine the server's IP address
#     and port. It then calls `create_backend(ip, port)` to start the RESTful
#     application server.

#     :arg --server-ip (str): IP address to bind the server (default: 127.0.0.1).
#     :arg --server-port (int): Port number to bind the server (default: 9000).
#     """

#     parser = argparse.ArgumentParser(
#         prog='Backend',
#         description='Start the backend process',
#         epilog='Backend daemon for http_deamon application'
#     )
#     parser.add_argument('--server-ip',
#         type=str,
#         default='0.0.0.0',
#         help='IP address to bind the server. Default is 0.0.0.0'
#     )
#     parser.add_argument(
#         '--server-port',
#         type=int,
#         default=PORT,
#         help='Port number to bind the server. Default is {}.'.format(PORT)
#     )
 
#     args = parser.parse_args()
#     ip = args.server_ip
#     port = args.server_port

#     create_backend(ip, port)


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
start_backend
~~~~~~~~~~~~~~~~~

This module provides a simple entry point for deploying backend server process
using the socket framework. It parses command-line arguments to configure the
server's IP address and port, and then launches the backend server.

*** ĐÂY LÀ NƠI CHỨA LOGIC CỦA ỨNG DỤNG (Application Logic) ***
"""

import socket
import argparse
import json

# --- THÊM MỚI: Import WeApRous và các thành phần ---
from daemon.weaprous import WeApRous
# -----------------------------------------------

from daemon import create_backend

# Default port number used if none is specified via command-line arguments.
PORT = 9000 

app = WeApRous()

@app.route('/login', methods=['POST'])
def handle_login(request, response):
    """
    Xử lý POST /login.
    Hàm này được gọi từ httpadapter.py (thay vì code hardcode).
    Nó nhận vào 2 đối tượng: request và response.
    """
    print(f"[WeApRous] Handling POST /login...")
    
    # 1. Lấy dữ liệu (hỗ trợ cả JSON (raw) và Form)
    data = request.json_data  # Thử parse JSON (raw) trước
    if not data:
        data = request.form_data # Nếu không có JSON, thử parse form-urlencoded
        
    username = data.get('username')
    password = data.get('password')
    
    print(f"[WeApRous] Login attempt: user={username}")

    # 2. Kiểm tra logic
    if username == 'admin' and password == 'password':
        print(f"[WeApRous] Login Succeeded. Setting cookie and redirecting.")
        #Đăng nhập thành công: Set Cookie và Redirect
        
        # Gán request vào response để hàm build_redirect có thể đọc
        response.request = request 
        
        # Set cookie vào response
        response.set_header('Set-Cookie', 'auth=true; Path=/; HttpOnly')
        
        # Trả về response 302
        return response.build_redirect('/index.html')
    else:
        print(f"[WeApRous] Login Failed. Returning 401.")
        # Đăng nhập thất bại: Trả về 401
        
        # Gán request vào response
        response.request = request 
        
        return response.build_unauthorized()


@app.route('/api/login', methods=['POST'])
def handle_api_login(request, response):
    """
    Xử lý login cho API (Task 2), trả về JSON.
    """
    print(f"[WeApRous] Handling POST /api/login (JSON Response)...")
    
    # Lấy data (ưu tiên JSON, sau đó là Form)
    data = request.json_data
    if not data:
        data = request.form_data
        
    username = data.get('username')
    password = data.get('password')

    # Gán request vào response để hàm build_json_response có thể dùng
    response.request = request 

    if username == 'admin' and password == 'password':
        # Đăng nhập thành công: Trả về JSON, 200 OK
        response_body = json.dumps({"ok": True, "message": "Logged in"})
        return response.build_json_response(response_body, status_code=200)
    else:
        # Đăng nhập thất bại: Trả về JSON, 401 Unauthorized
        response_body = json.dumps({"ok": False, "error": "Unauthorized"})
        return response.build_json_response(response_body, status_code=401, reason="Unauthorized")



if __name__ == "__main__":
    """
    Entry point for launching the backend server.
    """

    parser = argparse.ArgumentParser(
        prog='Backend',
        description='Start the backend process',
        epilog='Backend daemon for http_deamon application'
    )
    parser.add_argument('--server-ip',
        type=str,
        default='0.0.0.0',
        help='IP address to bind the server. Default is 0.0.0.0'
    )
    parser.add_argument(
        '--server-port',
        type=int,
        default=PORT,
        help='Port number to bind the server. Default is {}.'.format(PORT)
    )
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    create_backend(ip, port, routes=app.routes)