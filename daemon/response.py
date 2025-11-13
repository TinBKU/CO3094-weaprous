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
# daemon.response
# ~~~~~~~~~~~~~~~~~

# This module provides a :class: `Response <Response>` object to manage and persist 
# response settings (cookies, auth, proxies), and to construct HTTP responses
# based on incoming requests. 

# The current version supports MIME type detection, content loading and header formatting
# """
# import datetime
# import os
# import mimetypes
# from .dictionary import CaseInsensitiveDict

# BASE_DIR = ""

# class Response():   
#     """The :class:`Response <Response>` object, which contains a
#     server's response to an HTTP request.

#     Instances are generated from a :class:`Request <Request>` object, and
#     should not be instantiated manually; doing so may produce undesirable
#     effects.

#     :class:`Response <Response>` object encapsulates headers, content, 
#     status code, cookies, and metadata related to the request-response cycle.
#     It is used to construct and serve HTTP responses in a custom web server.

#     :attrs status_code (int): HTTP status code (e.g., 200, 404).
#     :attrs headers (dict): dictionary of response headers.
#     :attrs url (str): url of the response.
#     :attrsencoding (str): encoding used for decoding response content.
#     :attrs history (list): list of previous Response objects (for redirects).
#     :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
#     :attrs cookies (CaseInsensitiveDict): response cookies.
#     :attrs elapsed (datetime.timedelta): time taken to complete the request.
#     :attrs request (PreparedRequest): the original request object.

#     Usage::

#       >>> import Response
#       >>> resp = Response()
#       >>> resp.build_response(req)
#       >>> resp
#       <Response>
#     """

#     __attrs__ = [
#         "_content",
#         "_header",
#         "status_code",
#         "method",
#         "headers",
#         "url",
#         "history",
#         "encoding",
#         "reason",
#         "cookies",
#         "elapsed",
#         "request",
#         "body",
#         "reason",
#     ]


#     def __init__(self, request=None):
#         """
#         Initializes a new :class:`Response <Response>` object.

#         : params request : The originating request object.
#         """

#         self._content = False
#         self._content_consumed = False
#         self._next = None

#         #: Integer Code of responded HTTP Status, e.g. 404 or 200.
#         self.status_code = None

#         #: Case-insensitive Dictionary of Response Headers.
#         #: For example, ``headers['content-type']`` will return the
#         #: value of a ``'Content-Type'`` response header.
#         self.headers = {}

#         #: URL location of Response.
#         self.url = None

#         #: Encoding to decode with when accessing response text.
#         self.encoding = None

#         #: A list of :class:`Response <Response>` objects from
#         #: the history of the Request.
#         self.history = []

#         #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
#         self.reason = None

#         #: A of Cookies the response headers.
#         self.cookies = CaseInsensitiveDict()

#         #: The amount of time elapsed between sending the request
#         self.elapsed = datetime.timedelta(0)

#         #: The :class:`PreparedRequest <PreparedRequest>` object to which this
#         #: is a response.
#         self.request = None


#     def get_mime_type(self, path):
#         """
#         Determines the MIME type of a file based on its path.

#         "params path (str): Path to the file.

#         :rtype str: MIME type string (e.g., 'text/html', 'image/png').
#         """

#         try:
#             mime_type, _ = mimetypes.guess_type(path)
#         except Exception:
#             return 'application/octet-stream'
#         return mime_type or 'application/octet-stream'


#     def prepare_content_type(self, mime_type='text/html'):
#         """
#         Prepares the Content-Type header and determines the base directory
#         for serving the file based on its MIME type.

#         :params mime_type (str): MIME type of the requested resource.

#         :rtype str: Base directory path for locating the resource.

#         :raises ValueError: If the MIME type is unsupported.
#         """
        
#         base_dir = ""

#         # Processing mime_type based on main_type and sub_type
#         main_type, sub_type = mime_type.split('/', 1)
#         print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
#         if main_type == 'text':
#             self.headers['Content-Type']='text/{}'.format(sub_type)
#             if sub_type == 'plain' or sub_type == 'css':
#                 base_dir = BASE_DIR+"static/"
#             elif sub_type == 'html':
#                 base_dir = BASE_DIR+"www/"
#             else:
#                 # handle_text_other(sub_type)
#                 base_dir = BASE_DIR+"static/" # Mặc định cho text khác
#         elif main_type == 'image':
#             base_dir = BASE_DIR+"static/"
#             self.headers['Content-Type']='image/{}'.format(sub_type)
#         elif main_type == 'application':
#             # Sửa: Mặc định cho JS
#             if sub_type == 'javascript' or sub_type == 'x-javascript':
#                 base_dir = BASE_DIR+"static/"
#                 self.headers['Content-Type'] = 'application/javascript'
#             else:
#                 base_dir = BASE_DIR+"apps/"
#                 self.headers['Content-Type']='application/{}'.format(sub_type)
#         #
#         #  TODO: process other mime_type
#         #        application/xml       
#         #        application/zip
#         #        ...
#         #        text/csv
#         #        text/xml
#         #        ...
#         #        video/mp4 
#         #        video/mpeg
#         #        ...
#         #
#         else:
#             # raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))
#             print("[Response] MIME type không xác định: {}. Mặc định là 'static/'".format(mime_type))
#             base_dir = BASE_DIR+"static/"
#             self.headers['Content-Type'] = mime_type


#         return base_dir


#     def build_content(self, path, base_dir):
#         """
#         Loads the objects file from storage space.

#         :params path (str): relative path to the file.
#         :params base_dir (str): base directory where the file is located.

#         :rtype tuple: (int, bytes) representing content length and content data.
#         """

#         filepath = os.path.join(base_dir, path.lstrip('/'))

#         print("[Response] serving the object at location {}".format(filepath))
#             #
#             #  TODO: implement the step of fetch the object file
#             #        store in the return value of content
#             #
        
#     # -------------------------------------------------------------------------- #
#         try:
#             # 'rb' = read binary (quan trọng cho ảnh, file, v.v.)
#             with open(filepath, 'rb') as f:
#                 content = f.read()
#             return len(content), content
#         except FileNotFoundError:
#             print(f"[Response] Lỗi: Không tìm thấy file {filepath}")
#             # Trả về 0 và content rỗng, logic ở httpadapter sẽ xử lý 404
#             return 0, b"" 
#         except Exception as e:
#             print(f"[Response] Lỗi khi đọc file: {e}")
#             return 0, b""
#     # -------------------------------------------------------------------------- #


#     def build_response_header(self, request):
#         """
#         Constructs the HTTP response headers based on the class:`Request <Request>
#         and internal attributes.

#         :params request (class:`Request <Request>`): incoming request object.

#         :rtypes bytes: encoded HTTP response header.
#         """
        
#     # -------------------------------------------------------------------------- #
#         # Gán giá trị mặc định nếu chưa có
#         if not self.status_code:
#             self.status_code = 200
#             self.reason = "OK"
#     # -------------------------------------------------------------------------- #
        
#         reqhdr = request.headers
#         rsphdr = self.headers

#         #Build dynamic headers
#         headers = {
#                 "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
#                 "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
#                 "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
#                 "Cache-Control": "no-cache",
#                 "Content-Type": "{}".format(self.headers['Content-Type']),
#                 "Content-Length": "{}".format(len(self._content)),
#                 # "Cookie": "{}".format(reqhdr.get("Cookie", "sessionid=xyz789")), #dummy cooki
#         #
#         # TODO prepare the request authentication
#         #
# 	# self.auth = ...
#                 "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
#                 "Max-Forward": "10",
#                 "Pragma": "no-cache",
#                 "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
#                 "Warning": "199 Miscellaneous warning",
#                 "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
#                 "Connection": "close", # Thêm: Đóng kết nối sau mỗi response
#             }

#         # Header text alignment
#             #
#             #  TODO: implement the header building to create formated
#             #        header from the provied headers
#             #
        
#     # -------------------------------------------------------------------------- #
#         # Bắt đầu với dòng status
#         fmt_header = f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
        
#         # Thêm tất cả header động
#         for key, value in headers.items():
#             fmt_header += f"{key}: {value}\r\n"
            
#         # Thêm các header đã được set thủ công (ví dụ: Set-Cookie)
#         # Ghi đè các header động nếu trùng key
#         for key, value in self.headers.items():
#             if key not in headers: 
#                 fmt_header += f"{key}: {value}\r\n"

#         # Dòng trống cuối cùng để ngăn cách header và body
#         fmt_header += "\r\n"
        
#         return str(fmt_header).encode('utf-8')
#     # -------------------------------------------------------------------------- #


#     def build_notfound(self):
#         """
#         Constructs a standard 404 Not Found HTTP response.

#         :rtype bytes: Encoded 404 response.
#         """
        
#         # Thêm status_code và reason
#         self.status_code = 404
#         self.reason = "Not Found"
        
#         body = "404 Not Found"
#         return (
#             f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
#             f"Content-Type: text/html\r\n"
#             f"Content-Length: {len(body)}\r\n"
#             f"Connection: close\r\n"
#             f"\r\n"
#             f"{body}"
#         ).encode('utf-8')


#     # THÊM HÀM set_header và build_unauthorized 
#     def set_header(self, key, value):
#         """
#         Thêm hoặc cập nhật một header cho response.
#         Chúng ta sẽ dùng cái này cho 'Set-Cookie'.
#         """
#         self.headers[key] = value

#     def build_unauthorized(self):
#         """
#         Constructs a standard 401 Unauthorized HTTP response.
#         """
#         # Thêm status_code và reason
#         self.status_code = 401
#         self.reason = "Unauthorized"
        
#         body = "401 Unauthorized"
#         return (
#             f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
#             f"Content-Type: text/html\r\n"
#             f"Content-Length: {len(body)}\r\n"
#             f"Connection: close\r\n"
#             f"\r\n"
#             f"{body}"
#         ).encode('utf-8')


#     def build_response(self, request):
#         """
#         Builds a full HTTP response including headers and content based on the request.

#         :params request (class:`Request <Request>`): incoming request object.

#         :rtype bytes: complete HTTP response using prepared headers and content.
#         """
#     # -------------------------------------------------------------------------- #
#         # Xử lý request rỗng ---
#         if not request.method or not request.path:
#              print("[Response] Request không hợp lệ.")
#              return self.build_notfound() # Hoặc một lỗi 400 Bad Request
#     # -------------------------------------------------------------------------- #

#         path = request.path

#         mime_type = self.get_mime_type(path)
#         print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

#         base_dir = ""

#         #If HTML, parse and serve embedded objects
#         if path.endswith('.html') or mime_type == 'text/html':
#             base_dir = self.prepare_content_type(mime_type = 'text/html')
#         elif mime_type == 'text/css':
#             base_dir = self.prepare_content_type(mime_type = 'text/css')
        
#         # TODO: add support objects
        
#     # -------------------------------------------------------------------------- #
#         # Thêm các object khác ---
#         elif mime_type.startswith('image/'):
#             base_dir = self.prepare_content_type(mime_type = mime_type)
#         elif mime_type == 'application/javascript' or mime_type == 'application/x-javascript':
#              base_dir = self.prepare_content_type(mime_type = 'application/javascript')
#     # -------------------------------------------------------------------------- #
    
#         else:
#         # -------------------------------------------------------------------------- #
#             # return self.build_notfound() 
#             # Thử tìm file trong static
#             print(f"[Response] Thử tìm {path} trong 'static/'")
#             base_dir = self.prepare_content_type(mime_type = mime_type)

#         c_len, self._content = self.build_content(path, base_dir)
        
#         # Trả về 404 nếu không tìm thấy file ---
#         if c_len == 0 and not self._content:
#             return self.build_notfound()
#         # -------------------------------------------------------------------------- #

#         self._header = self.build_response_header(request)

#         return self._header + self._content


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
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
from .dictionary import CaseInsensitiveDict

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        self.status_code = None
        
        self.headers = {} 

        self.url = None
        self.encoding = None
        self.history = []
        self.reason = None
        self.cookies = CaseInsensitiveDict()
        self.elapsed = datetime.timedelta(0)
        
        self.request = request


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.
        """
        
        base_dir = ""

        # Processing mime_type based on main_type and sub_type
        try:
            main_type, sub_type = mime_type.split('/', 1)
        except ValueError:
            # Xử lý trường hợp mime_type không hợp lệ
            main_type = 'application'
            sub_type = 'octet-stream'

        print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        if main_type == 'text':
            self.headers['Content-Type']='text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR+"static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR+"www/"
            else:
                base_dir = BASE_DIR+"static/" 
        elif main_type == 'image':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='image/{}'.format(sub_type)
        elif main_type == 'application':
            if sub_type == 'javascript' or sub_type == 'x-javascript':
                base_dir = BASE_DIR+"static/"
                self.headers['Content-Type'] = 'application/javascript'
            else:
                base_dir = BASE_DIR+"apps/"
                self.headers['Content-Type']='application/{}'.format(sub_type)
        else:
            print("[Response] MIME type không xác định: {}. Mặc định là 'static/'".format(mime_type))
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type'] = mime_type

        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.
        """

        # Chặn truy cập file bên ngoài (Directory Traversal)
        if '..' in path:
            print(f"[Response] Lỗi: Phát hiện cố gắng truy cập trái phép {path}")
            return 0, b""

        filepath = os.path.join(base_dir, path.lstrip('/'))

        print("[Response] serving the object at location {}".format(filepath))
            
        try:
            # 'rb' = read binary
            with open(filepath, 'rb') as f:
                content = f.read()
            return len(content), content
        except FileNotFoundError:
            print(f"[Response] Lỗi: Không tìm thấy file {filepath}")
            return 0, b"" 
        except IsADirectoryError:
            print(f"[Response] Lỗi: {filepath} là một thư mục, không phải file.")
            return 0, b""
        except Exception as e:
            print(f"[Response] Lỗi khi đọc file: {e}")
            return 0, b""


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the request.
        """
        
        # Gán giá trị mặc định nếu chưa có
        if not self.status_code:
            self.status_code = 200
            self.reason = "OK"
        
        # Đảm bảo request là một đối tượng hợp lệ
        if not request or not request.headers:
            reqhdr = {}
        else:
            reqhdr = request.headers
            
        rsphdr = self.headers

        #Build dynamic headers
        headers = {
                # "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                # "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                # "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
                "Cache-Control": "no-cache",
                # "Content-Type": "{}".format(self.headers['Content-Type']), # Sẽ được thêm bên dưới
                "Content-Length": "{}".format(len(self._content)),
                "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
                # "Max-Forward": "10",
                "Pragma": "no-cache",
                # "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
                # "Warning": "199 Miscellaneous warning",
                # "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
                "Connection": "close",
            }

        fmt_header = f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
        
        # Thêm tất cả header động
        for key, value in headers.items():
            fmt_header += f"{key}: {value}\r\n"
            
        # Thêm các header đã được set thủ công (ví dụ: Set-Cookie, Content-Type, Location)
        # Ghi đè các header động nếu trùng key
        for key, value in self.headers.items():
            fmt_header += f"{key}: {value}\r\n"

        fmt_header += "\r\n"
        
        return str(fmt_header).encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.
        """
        
        self.status_code = 404
        self.reason = "Not Found"
        self.headers['Content-Type'] = 'text/html'
        
        body = "404 Not Found"
        self._content = body.encode('utf-8')
        
        fmt_header = self.build_response_header(self.request) 

        return fmt_header + self._content


    def set_header(self, key, value):
        """
        Thêm hoặc cập nhật một header cho response.
        """
        self.headers[key] = value

    def build_unauthorized(self):
        """
        Constructs a standard 401 Unauthorized HTTP response.
        """
        self.status_code = 401
        self.reason = "Unauthorized"
        self.headers['Content-Type'] = 'text/html'

        body = "401 Unauthorized"
        self._content = body.encode('utf-8')
        
        fmt_header = self.build_response_header(self.request) 

        return fmt_header + self._content

    def build_redirect(self, location='/index.html'):
        """
        Constructs a standard 302 Found (Redirect) HTTP response.
        """
        self.status_code = 302
        self.reason = "Found"
        self.headers['Content-Type'] = 'text/plain'
        
        body = f"Redirecting to {location}"
        self._content = body.encode('utf-8')
        
        self.set_header('Location', location)
        
        fmt_header = self.build_response_header(self.request) 
        
        return fmt_header + self._content


    def build_response(self, request):
        """
        Builds a full HTTP response (cho file tĩnh)
        """
        self.request = request 
        
        if not request.method or not request.path:
             print("[Response] Request không hợp lệ.")
             return self.build_notfound()

        path = request.path
        mime_type = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        base_dir = ""

        #If HTML, parse and serve embedded objects
        if path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type = 'text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type = 'text/css')
        elif mime_type.startswith('image/'):
            base_dir = self.prepare_content_type(mime_type = mime_type)
        elif mime_type == 'application/javascript' or mime_type == 'application/x-javascript':
             base_dir = self.prepare_content_type(mime_type = 'application/javascript')
        else:
            print(f"[Response] Thử tìm {path} trong 'static/'")
            base_dir = self.prepare_content_type(mime_type = mime_type)

        c_len, self._content = self.build_content(path, base_dir)
        
        # Trả về 404 nếu không tìm thấy file
        if c_len == 0 and not self._content:
            return self.build_notfound()

        # self._header được tạo bởi build_response_header
        self._header = self.build_response_header(request)

        return self._header + self._content
    
    def build_json_response(self, body_str, status_code=200, reason="OK"):
        self.status_code = status_code
        self.reason = reason
        self.headers['Content-Type'] = 'application/json'

        # body_str là một chuỗi JSON đã được .dumps()
        self._content = body_str.encode('utf-8')
        
        # Gán request (nếu có) để build_response_header
        # Đảm bảo self.request đã được gán trước khi gọi hàm này
        
        # Gọi hàm build_response_header để tạo header chuẩn
        fmt_header = self.build_response_header(self.request) 

        return fmt_header + self._content