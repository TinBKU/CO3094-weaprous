
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

        # 1) Nếu chưa set status_code, mặc định 200 OK
        if not self.status_code:
            self.status_code = 200
            self.reason = "OK"

        # 2) CORS: lấy Origin từ request (headers trong Request đều là lowercase)
        if request and getattr(request, "headers", None):
            reqhdr = request.headers
            origin = reqhdr.get("origin")   # header key đã được .lower()
        else:
            reqhdr = {}
            origin = None

        # Nếu có Origin thì trả lại đúng Origin, không dùng '*'
        cors_origin = origin if origin else "*"

        self.headers.setdefault("Access-Control-Allow-Origin", cors_origin)
        self.headers.setdefault("Access-Control-Allow-Credentials", "true")
        self.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization")

        # 4) Dynamic headers cơ bản
        headers = {
            "Accept": "{}".format(reqhdr.get("accept", "application/json")),
            "Cache-Control": "no-cache",
            "Content-Length": "{}".format(
                len(self._content) if getattr(self, "_content", None) else 0
            ),
            "Date": "{}".format(
                datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            ),
            "Pragma": "no-cache",
            "Connection": "close",
        }

        fmt_header = f"HTTP/1.1 {self.status_code} {self.reason}\r\n"

        for key, value in headers.items():
            fmt_header += f"{key}: {value}\r\n"

        for key, value in self.headers.items():
            fmt_header += f"{key}: {value}\r\n"

        fmt_header += "\r\n"
        return fmt_header.encode("utf-8")



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
        body = b"401 Unauthorized"
        response = (
            "HTTP/1.1 401 Unauthorized\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n"
            "Access-Control-Allow-Headers: Content-Type, Authorization\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("utf-8") + body
        return response



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