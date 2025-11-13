# #
# # Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# # All rights reserved.
# # This file is part of the CO3093/CO3094 course.
# #
# # WeApRous release
# #
# # The authors hereby grant to Licensee personal permission to use
# # and modify the Licensed Source Code for the sole purpose of studying
# # while attending the course
# #

# """
# daemon.httpadapter
# ~~~~~~~~~~~~~~~~~

# This module provides a http adapter object to manage and persist 
# http settings (headers, bodies). The adapter supports both
# raw URL paths and RESTful route definitions, and integrates with
# Request and Response objects to handle client-server communication.
# """

# from .request import Request
# from .response import Response
# from .dictionary import CaseInsensitiveDict

# class HttpAdapter:
#     """
#     A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
#     and routing requests.

#     The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
#     dispatching them to appropriate route handlers, and constructing responses.
#     It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
#     and :class:`Response <Response>` objects for full request lifecycle management.

#     Attributes:
#         ip (str): IP address of the client.
#         port (int): Port number of the client.
#         conn (socket): Active socket connection.
#         connaddr (tuple): Address of the connected client.
#         routes (dict): Mapping of route paths to handler functions.
#         request (Request): Request object for parsing incoming data.
#         response (Response): Response object for building and sending replies.
#     """

#     __attrs__ = [
#         "ip",
#         "port",
#         "conn",
#         "connaddr",
#         "routes",
#         "request",
#         "response",
#     ]

#     def __init__(self, ip, port, conn, connaddr, routes):
#         """
#         Initialize a new HttpAdapter instance.

#         :param ip (str): IP address of the client.
#         :param port (int): Port number of the client.
#         :param conn (socket): Active socket connection.
#         :param connaddr (tuple): Address of the connected client.
#         :param routes (dict): Mapping of route paths to handler functions.
#         """

#         #: IP address.
#         self.ip = ip
#         #: Port.
#         self.port = port
#         #: Connection
#         self.conn = conn
#         #: Conndection address
#         self.connaddr = connaddr
#         #: Routes
#         self.routes = routes
#         #: Request
#         self.request = Request()
#         #: Response
#         self.response = Response()

#     def handle_client(self, conn, addr, routes):
#         """
#         Handle an incoming client connection.

#         This method reads the request from the socket, prepares the request object,
#         invokes the appropriate route handler if available, builds the response,
#         and sends it back to the client.

#         :param conn (socket): The client socket connection.
#         :param addr (tuple): The client's address.
#         :param routes (dict): The route mapping for dispatching requests.
#         """

#         # --- BẮT ĐẦU SỬA: THAY THẾ TOÀN BỘ HÀM ---
        
#         # Connection handler.
#         self.conn = conn        
#         # Connection address.
#         self.connaddr = addr
#         # Request handler
#         req = self.request
#         # Response handler
#         resp = self.response

#         # Handle the request
#         try:
#             msg = conn.recv(1024).decode()
#             if not msg:
#                 print(f"[HttpAdapter] Client {addr} ngắt kết nối.")
#                 conn.close()
#                 return
#         except Exception as e:
#             print(f"[HttpAdapter] Lỗi khi nhận dữ liệu: {e}")
#             conn.close()
#             return
            
#         # Parse request (đã sửa ở Bước 2)
#         try:
#              req.prepare(msg, routes)
#         except Exception as e:
#              print(f"[HttpAdapter] Lỗi khi parse request: {e}")
#              # Gửi lỗi 400 Bad Request
#              response_data = (
#                 "HTTP/1.1 400 Bad Request\r\n"
#                 "Content-Length: 15\r\nConnection: close\r\n\r\n"
#                 "400 Bad Request"
#              ).encode('utf-8')
#              conn.sendall(response_data)
#              conn.close()
#              return

#         # XỬ LÝ AUTHENTICATION (POST /login) 
#         if req.method == 'POST' and req.path == '/login':
            
#             # Lấy form data đã được parse
#             form = req.form_data
#             username = form.get('username')
#             password = form.get('password')

#             if username == 'admin' and password == 'password':
#                 # --- ĐĂNG NHẬP THÀNH CÔNG (ĐÃ SỬA) ---
#                 print(f"[Auth] Đăng nhập thành công, gửi 302 Redirect cho: {username} từ {addr}")
                
#                 # 1. Xây dựng response 302 Found (Redirect)
#                 # Yêu cầu trình duyệt tự chuyển đến /index.html
#                 body = "Redirecting to /index.html"
#                 response_data = (
#                     f"HTTP/1.1 302 Found\r\n"
#                     f"Location: /index.html\r\n"
#                     f"Set-Cookie: auth=true; Path=/; HttpOnly\r\n" # Gửi cookie cùng lúc
#                     f"Content-Type: text/plain\r\n"
#                     f"Content-Length: {len(body)}\r\n"
#                     f"Connection: close\r\n"
#                     f"\r\n"
#                     f"{body}"
#                 ).encode('utf-8')

#                 # 2. Gửi response và đóng kết nối
#                 conn.sendall(response_data)
#                 conn.close()
#                 return # Quan trọng: Kết thúc xử lý tại đây
                
#             else:
#                 # --- ĐĂNG NHẬP THẤT BẠI ---
#                 print(f"[Auth] Đăng nhập thất bại cho: {username} từ {addr}")
                
#                 # 1. Gửi response 401 (sử dụng hàm mới từ Bước 3.3)
#                 response_data = resp.build_unauthorized()
#                 conn.sendall(response_data)
#                 conn.close()
#                 return # Kết thúc xử lý
        
#         # XỬ LÝ ACCESS CONTROL (GET /index.html) 
        
#         # Các trang cần bảo vệ
#         protected_paths = ['/index.html'] 
        
#         if req.method == 'GET' and req.path in protected_paths:
            
#             # Lấy cookie đã được parse
#             auth_cookie = req.cookies.get('auth')
            
#             if auth_cookie == 'true':
#                 # --- ĐÃ XÁC THỰC ---
#                 print(f"[Auth] Client {addr} đã xác thực, cho phép truy cập.")
#                 # Để code chạy tiếp xuống phần build_response
#             else:
#                 # --- CHƯA XÁC THỰC ---
#                 print(f"[Auth] Client {addr} truy cập bị từ chối. Yêu cầu đăng nhập.")
                
#                 # 1. Gửi response 401
#                 response_data = resp.build_unauthorized()
#                 conn.sendall(response_data)
#                 conn.close()
#                 return # Kết thúc xử lý

#         if req.hook:
#             print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path,req.hook._route_methods))
#             req.hook(headers = "bksysnet",body = "get in touch")
#             #
#             # TODO: handle for App hook here
#             #


#         response = resp.build_response(req)

#         conn.sendall(response)
#         conn.close()


#     @property
#     def extract_cookies(self, req, resp):
#         """
#         Build cookies from the :class:`Request <Request>` headers.

#         :param req:(Request) The :class:`Request <Request>` object.
#         :param resp: (Response) The res:class:`Response <Response>` object.
#         :rtype: cookies - A dictionary of cookie key-value pairs.
#         """
        
#         return req.cookies

#     def build_response(self, req, resp):
#         """Builds a :class:`Response <Response>` object 

#         :param req: The :class:`Request <Request>` used to generate the response.
#         :param resp: The  response object.
#         :rtype: Response
#         """
#         response = Response()

#         # Set encoding.
#         # response.encoding = get_encoding_from_headers(response.headers)
#         response.encoding = 'utf-8' # Mặc định
#         response.raw = resp
        
#         # response.reason = response.raw.reason 

#         if isinstance(req.url, bytes):
#             response.url = req.url.decode("utf-8")
#         else:
#             response.url = req.url

#         # Add new cookies from the server.
#         # response.cookies = extract_cookies(req)
#         pass

#         # Give the Response some context.
#         response.request = req
#         response.connection = self

#         return response

#     # def get_connection(self, url, proxies=None):
#         # """Returns a url connection for the given URL. 

#         # :param url: The URL to connect to.
#         # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
#         # :rtype: int
#         # """

#         # proxy = select_proxy(url, proxies)

#         # if proxy:
#             # proxy = prepend_scheme_if_needed(proxy, "http")
#             # proxy_url = parse_url(proxy)
#             # if not proxy_url.host:
#                 # raise InvalidProxyURL(
#                     # "Please check proxy URL. It is malformed "
#                     # "and could be missing the host."
#                 # )
#             # proxy_manager = self.proxy_manager_for(proxy)
#             # conn = proxy_manager.connection_from_url(url)
#         # else:
#             # # Only scheme should be lower case
#             # parsed = urlparse(url)
#             # url = parsed.geturl()
#             # conn = self.poolmanager.connection_from_url(url)

#         # return conn


#     def add_headers(self, request):
#         """
#         Add headers to the request.

#         This method is intended to be overridden by subclasses to inject
#         custom headers. It does nothing by default.

        
#         :param request: :class:`Request <Request>` to add headers to.
#         """
#         pass

#     def build_proxy_headers(self, proxy):
#         """Returns a dictionary of the headers to add to any request sent
#         through a proxy. 

#         :class:`HttpAdapter <HttpAdapter>`.

#         :param proxy: The url of the proxy being used for this request.
#         :rtype: dict
#         """
#         headers = {}
#         #
#         # TODO: build your authentication here
#         #       username, password =...
#         # we provide dummy auth here
#         #
#         username, password = ("user1", "password")

#         if username:
#             headers["Proxy-Authorization"] = (username, password)

#         return headers

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
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes (dictionary từ WeApRous)
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.
        """

        
        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        # Handle the request
        try:
            # Tăng buffer size để nhận được các request lớn hơn
            msg = conn.recv(4096).decode()
            if not msg:
                print(f"[HttpAdapter] Client {addr} ngắt kết nối.")
                conn.close()
                return
        except Exception as e:
            print(f"[HttpAdapter] Lỗi khi nhận dữ liệu: {e}")
            conn.close()
            return
            
        # Parse request 
        try:
             req.prepare(msg, routes)
        except Exception as e:
             print(f"[HttpAdapter] Lỗi khi parse request: {e}")
             response_data = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Length: 15\r\nConnection: close\r\n\r\n"
                "400 Bad Request"
             ).encode('utf-8')
             conn.sendall(response_data)
             conn.close()
             return
        
        # Các trang cần bảo vệ
        protected_paths = ['/index.html'] 
        
        if req.method == 'GET' and req.path in protected_paths:
            
            # Lấy cookie đã được parse
            auth_cookie = req.cookies.get('auth')
            
            if auth_cookie == 'true':
                # --- ĐÃ XÁC THỰC ---
                print(f"[Auth] Client {addr} đã xác thực, cho phép truy cập {req.path}.")
            else:
                # --- CHƯA XÁC THỰC ---
                print(f"[Auth] Client {addr} truy cập {req.path} bị từ chối. Yêu cầu đăng nhập.")
                
                # Gán request vào response để build_unauthorized
                resp.request = req 
                
                response_data = resp.build_unauthorized()
                conn.sendall(response_data)
                conn.close()
                return # Kết thúc xử lý

        if req.hook:
            print(f"[HttpAdapter] Routing to WeApRous handler for {req.method} {req.path}")
            try:
                response_data = req.hook(request=req, response=resp)
                
                conn.sendall(response_data)
                conn.close()
                return 
                
            except Exception as e:
                print(f"[HttpAdapter] Lỗi nghiêm trọng trong WeApRous handler: {e}")
                # Gửi lỗi 500 Internal Server Error
                resp.request = req # Gán request để build lỗi
                response_data = (
                    "HTTP/1.1 500 Internal Server Error\r\n"
                    "Content-Length: 21\r\nConnection: close\r\n\r\n"
                    "500 Internal Server Error"
                ).encode('utf-8')
                conn.sendall(response_data)
                conn.close()
                return

        print(f"[HttpAdapter] Serving static file: {req.path}")
        response = resp.build_response(req)

        conn.sendall(response)
        conn.close()


    @property
    def extract_cookies(self, req, resp):
        """
        Build cookies from the :class:`Request <Request>` headers.
        """
        
        return req.cookies

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object """
        response = Response()
        response.encoding = 'utf-8' # Mặc định
        response.raw = resp
        
        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        pass

        response.request = req
        response.connection = self

        return response

    def add_headers(self, request):
        """
        Add headers to the request.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 
        """
        headers = {}
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers