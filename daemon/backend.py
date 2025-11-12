#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.backend
~~~~~~~~~~~~~~~~~

Mô-đun này cung cấp một đối tượng backend để quản lý và duy trì daemon backend.
Nó triển khai một máy chủ backend cơ bản bằng cách sử dụng các thư viện socket và threading của Python.
Nó hỗ trợ xử lý nhiều kết nối máy khách đồng thời và định tuyến các yêu cầu bằng bộ điều hợp HTTP tùy chỉnh.

Yêu cầu:
--------------
- socket: cung cấp giao diện mạng socket.
- threading: Cho phép xử lý máy khách đồng thời thông qua các luồng.
- response: các tiện ích phản hồi.
- httpadapter: lớp để xử lý các yêu cầu HTTP.
- CaseInsensitiveDict: cung cấp từ điển để quản lý tiêu đề hoặc tuyến đường.


Notes:
------
- Máy chủ tạo các luồng daemon để xử lý máy khách.
- Việc xử lý lỗi triển khai hiện tại là tối thiểu, các lỗi socket được in ra bảng điều khiển.
- Việc xử lý yêu cầu thực tế được ủy quyền cho Lớp HttpAdapter.

Usage Example:
--------------
>>> create_backend("127.0.0.1", 9000, routes={})

"""

import socket
import threading
import argparse

from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

def handle_client(ip, port, conn, addr, routes):
    """
    Initializes an HttpAdapter instance and delegates the client handling logic to it.

    :param ip (str): IP address of the server.
    :param port (int): Port number the server is listening on.
    :param conn (socket.socket): Client connection socket.
    :param addr (tuple): client address (IP, port).
    :param routes (dict): Dictionary of route handlers.
    """
    daemon = HttpAdapter(ip, port, conn, addr, routes)

    # Handle client
    daemon.handle_client(conn, addr, routes)

def run_backend(ip, port, routes):
    """
    Starts the backend server, binds to the specified IP and port, and listens for incoming
    connections. Each connection is handled in a separate thread. The backend accepts incoming
    connections and spawns a thread for each client.


    :param ip (str): IP address to bind the server.
    :param port (int): Port number to listen on.
    :param routes (dict): Dictionary of route handlers.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((ip, port))
        server.listen(50)
        print("[Backend] Listening on port {}".format(port))
        if routes != {}:
            print("[Backend] route settings {}".format(routes))

        while True:
            conn, addr = server.accept()
            
            #  TODO: triển khai bước kết nối đến máy khách 
            #  sử dụng lập trình đa luồng (multi-thread programming) với trình xử lý handle_client được cung cấp
            
        # -------------------------------------------------------------------------- #
            # Tạo một luồng mới để xử lý client này
            # target=handle_client chỉ định hàm sẽ chạy trong luồng mới
            # args=(...) là các tham số truyền cho hàm handle_client
            # .daemon = True cho phép chương trình chính thoát 
            # ngay cả khi luồng này vẫn đang chạy
            client_thread = threading.Thread(target=handle_client, args=(ip, port, conn, addr, routes))
            client_thread.daemon = True 
            client_thread.start() # Bắt đầu luồng
        # -------------------------------------------------------------------------- #
            
    except socket.error as e:
      print("Socket error: {}".format(e))

def create_backend(ip, port, routes={}):
    """
    Entry point for creating and running the backend server.

    :param ip (str): IP address to bind the server.
    :param port (int): Port number to listen on.
    :param routes (dict, optional): Dictionary of route handlers. Defaults to empty dict.
    """

    run_backend(ip, port, routes)