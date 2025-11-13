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
import socket
import argparse

from daemon.weaprous import WeApRous

PORT = 8000  # Default port

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

@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print "[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body)

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