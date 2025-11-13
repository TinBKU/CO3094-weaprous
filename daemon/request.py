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
# daemon.request
# ~~~~~~~~~~~~~~~~~

# This module provides a Request object to manage and persist 
# request settings (cookies, auth, proxies).
# """
# from .dictionary import CaseInsensitiveDict

# class Request():
#     """The fully mutable "class" `Request <Request>` object,
#     containing the exact bytes that will be sent to the server.

#     Instances are generated from a "class" `Request <Request>` object, and
#     should not be instantiated manually; doing so may produce undesirable
#     effects.

#     Usage::

#       >>> import deamon.request
#       >>> req = request.Request()
#       ## Incoming message obtain aka. incoming_msg
#       >>> r = req.prepare(incoming_msg)
#       >>> r
#       <Request>
#     """
#     __attrs__ = [
#         "method",
#         "url",
#         "headers",
#         "body",
#         "reason",
#         "cookies",
#         "body",
#         "routes",
#         "hook",
#     ]

#     def __init__(self):
#         #: HTTP verb to send to the server.
#         self.method = None
#         #: HTTP URL to send the request to.
#         self.url = None
#         #: dictionary of HTTP headers.
#         self.headers = None
#         #: HTTP path
#         self.path = None        
#         # The cookies set used to create Cookie header
#         self.cookies = None
#         #: request body to send to the server.
#         self.body = None
#         #: Routes
#         self.routes = {}
#         #: Hook point for routed mapped-path
#         self.hook = None

#     def extract_request_line(self, request):
#         try:
#             lines = request.splitlines()
#             first_line = lines[0]
#             method, path, version = first_line.split()

#             if path == '/':
#                 path = '/index.html'
#         except Exception:
#             return None, None, None # Sửa: Luôn trả về 3 giá trị để tránh lỗi unpacking

#         return method, path, version
             
#     def prepare_headers(self, request):
#         """Prepares the given HTTP headers."""
#         lines = request.split('\r\n')
#         headers = {}
#         for line in lines[1:]:
#             if ': ' in line:
#                 key, val = line.split(': ', 1)
#                 headers[key.lower()] = val
#         return headers

#     def prepare(self, request, routes=None):
#         """Prepares the entire request with the given parameters."""

#     # -------------------------------------------------------------------------- #
#         # Tách Header và Body 
#         try:
#             header_part, self.body = request.split('\r\n\r\n', 1)
#         except ValueError:
#             # Nếu không có body (ví dụ: request GET), request chỉ là header
#             header_part = request
#             self.body = ""
#     # -------------------------------------------------------------------------- #

#         # Prepare the request line (chỉ parse từ header_part)
#         self.method, self.path, self.version = self.extract_request_line(header_part)
#         print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

#         #
#         # @bksysnet Preapring the webapp hook with WeApRous instance
#         # ...
#         #
        
#         if routes is not None and routes != {}:
#             self.routes = routes
#             self.hook = routes.get((self.method, self.path))
#             #
#             # self.hook manipulation goes here
#             # ...
#             #

#         # Parse headers (chỉ parse từ header_part)
#         self.headers = self.prepare_headers(header_part)
#         cookies = self.headers.get('cookie', '')
        
#     # -------------------------------------------------------------------------- #      
#         # logic parse cookies from header
#         self.cookies = CaseInsensitiveDict()
#         if cookies:
#             try:
#                 # Phân tích chuỗi cookie (ví dụ: "auth=true; session=abc")
#                 pairs = [p.strip() for p in cookies.split(';')]
#                 for pair in pairs:
#                     if '=' in pair:
#                         key, value = pair.split('=', 1)
#                         # Lưu cookie vào self.cookies
#                         self.cookies[key.strip()] = value.strip()
#             except Exception as e:
#                 print(f"[Request] Error parsing cookie string: {e}")
#     # -------------------------------------------------------------------------- #
    
#         return

#     def prepare_body(self, data, files, json=None):
#         self.prepare_content_length(self.body)
#         self.body = body
#         #
#         # TODO prepare the request authentication
#         #
#     # self.auth = ...
#         return


#     def prepare_content_length(self, body):
#         # self.headers["Content-Length"] = "0"
        
#     # -------------------------------------------------------------------------- #
#         if body is not None:
#             self.headers["Content-Length"] = str(len(body))
#         else:
#              self.headers["Content-Length"] = "0"
#         return
#     # -------------------------------------------------------------------------- #

#     def prepare_auth(self, auth, url=""):
#         #
#         # TODO prepare the request authentication
#         #
#     # self.auth = ...
#         return

#     def prepare_cookies(self, cookies):
#             self.headers["Cookie"] = cookies

#     # -------------------------------------------------------------------------- #
#     # Thêm property để parse Form Data
#     @property
#     def form_data(self):
#         """
#         Parses 'application/x-www-form-urlencoded' body.
#         Trả về một dictionary.
#         """
#         # Chỉ parse nếu body tồn tại và Content-Type là 'application/x-www-form-urlencoded'
#         if not self.body or self.headers.get('content-type') != 'application/x-www-form-urlencoded':
#             return {}
        
#         data = {}
#         try:
#             # Dùng thư viện chuẩn của Python để parse
#             from urllib.parse import unquote
            
#             pairs = self.body.split('&')
#             for pair in pairs:
#                 if '=' in pair:
#                     key, val = pair.split('=', 1)
#                     # unquote() để xử lý các ký tự đặc biệt như 'admin%40test.com'
#                     data[unquote(key)] = unquote(val)
#         except Exception as e:
#             print(f"[Request] Lỗi khi parse form data: {e}")
            
#         return data
#     # -------------------------------------------------------------------------- #



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
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict
from urllib.parse import unquote

class Request():
    """The fully mutable "class" `Request <Request>` object.
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            if not lines:
                return None, None, None
                
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None, None # Sửa: Luôn trả về 3 giá trị để tránh lỗi unpacking

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]: # Bắt đầu từ dòng thứ 2
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val # Lưu key dạng lowercase
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

    # -------------------------------------------------------------------------- #
        # Tách Header và Body 
        try:
            header_part, self.body = request.split('\r\n\r\n', 1)
        except ValueError:
            # Nếu không có body (ví dụ: request GET), request chỉ là header
            header_part = request
            self.body = ""
    # -------------------------------------------------------------------------- #

        # Prepare the request line (chỉ parse từ header_part)
        self.method, self.path, self.version = self.extract_request_line(header_part)
        if not self.method:
             raise ValueError("Invalid HTTP request line")
             
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        #
        
        if routes is not None and routes != {}:
            self.routes = routes
            # Tìm hook (hàm handler) dựa trên (METHOD, PATH)
            self.hook = routes.get((self.method, self.path))
            
            if self.hook:
                print(f"[Request] Found WeApRous hook for {self.method} {self.path}")
            
        # Parse headers (chỉ parse từ header_part)
        self.headers = self.prepare_headers(header_part)
        cookies_str = self.headers.get('cookie', '')
        
    # -------------------------------------------------------------------------- #      
        # logic parse cookies from header
        self.cookies = CaseInsensitiveDict()
        if cookies_str:
            try:
                # Phân tích chuỗi cookie (ví dụ: "auth=true; session=abc")
                pairs = [p.strip() for p in cookies_str.split(';')]
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        # Lưu cookie vào self.cookies
                        self.cookies[key.strip()] = value.strip()
            except Exception as e:
                print(f"[Request] Error parsing cookie string: {e}")
    # -------------------------------------------------------------------------- #
    
        return

    def prepare_body(self, data, files, json=None):
        self.prepare_content_length(self.body)
        self.body = body
        return


    def prepare_content_length(self, body):
        if body is not None:
             if isinstance(body, str):
                 self.headers["Content-Length"] = str(len(body.encode('utf-8')))
             else:
                 self.headers["Content-Length"] = str(len(body))
        else:
             self.headers["Content-Length"] = "0"
        return

    def prepare_auth(self, auth, url=""):
        return

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies

    # -------------------------------------------------------------------------- #
    # property để parse Form Data
    @property
    def form_data(self):
        """
        Parses 'application/x-www-form-urlencoded' body.
        Trả về một dictionary.
        """
        content_type = self.headers.get('content-type', '')
        # Chỉ parse nếu body tồn tại và Content-Type là 'application/x-www-form-urlencoded'
        if not self.body or 'application/x-www-form-urlencoded' not in content_type:
            return {}
        
        data = {}
        try:
            pairs = self.body.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, val = pair.split('=', 1)
                    # unquote() để xử lý các ký tự đặc biệt
                    data[unquote(key)] = unquote(val)
        except Exception as e:
            print(f"[Request] Lỗi khi parse form data (x-www-form-urlencoded): {e}")
            
        return data
        
    # Property để parse JSON Data (raw)
    @property
    def json_data(self):
        """
        Parses 'application/json' body (từ Postman Raw).
        Trả về một dictionary.
        """
        content_type = self.headers.get('content-type', '')
        if not self.body or 'application/json' not in content_type:
            return {}
            
        try:
            import json
            return json.loads(self.body)
        except Exception as e:
            print(f"[Request] Lỗi khi parse JSON body: {e}")
            return {}
    # -------------------------------------------------------------------------- #