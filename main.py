import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
import platform
import ctypes
import subprocess
from flask_socketio import SocketIO, emit
import importlib
import psutil
from werkzeug.serving import run_simple
import gevent
from gevent.server import StreamServer
import ssl
import sys
import io
import socket
from eventlet.green import socket as green_socket
from gevent import monkey
from gevent.pool import Pool
import subprocess

# Monkey patch để gevent có thể làm việc với các thư viện socket, SSL, ...
monkey.patch_all()
# Biến toàn cục
app_process = None  # Biến lưu trữ tiến trình Flask

# Đường dẫn đến thư mục chứa main.py
directory_path = None

import ssl
import io
import os
import subprocess
import psutil
from gevent import socket, pool as gevent_pool
from gevent.pywsgi import WSGIServer
from tkinter import messagebox
from subprocess import Popen, PIPE
import sys

# Biến global để lưu trữ tiến trình
app_process = None

def start_flask_server():
    global app_process

    main_py_path = os.path.join(directory_path, "main.py")
    if not os.path.exists(main_py_path):
        messagebox.showerror("Lỗi", f"Không tìm thấy main.py trong thư mục {directory_path}")
        return

    try:
        # Đọc nội dung của main.py
        with open(main_py_path, 'r', encoding='utf-8') as f:
            main_py_content = f.read()

        # Nội dung của class SimpleWSGIServer
        server_class_content = r"""
import ssl
import io
from gevent import socket, pool as gevent_pool, monkey
from gevent.pywsgi import WSGIServer
class SimpleWSGIServer:
    def __init__(self, app, host='0.0.0.0', port=5000, use_ssl=False, certfile='localhost.crt', keyfile='localhost.key'):
        self.app = app
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.certfile = certfile
        self.keyfile = keyfile
        self.pool = gevent_pool.Pool(10)

        if self.use_ssl:
            if not self.certfile or not self.keyfile:
                raise ValueError("Cần cung cấp 'certfile' và 'keyfile' khi bật SSL.")
        
        print(f"Khởi tạo server với SSL={self.use_ssl} trên {self.host}:{self.port}")

    def handle_request(self, client_socket):
        try:
            request_data = client_socket.recv(1024)
            if not request_data:
                print("Nhận yêu cầu trống từ client. Bỏ qua.")
                return

            try:
                decoded_request = request_data.decode('utf-8', errors='ignore')
                print(f"Yêu cầu nhận được (đã giải mã): {decoded_request}")
            except Exception as e:
                print(f"Lỗi giải mã dữ liệu: {e}")
                decoded_request = "<Không thể giải mã dữ liệu>"

            request_lines = decoded_request.splitlines()
            if len(request_lines) == 0 or " " not in request_lines[0]:
                print("Yêu cầu không hợp lệ: Thiếu dòng đầu tiên hoặc không đúng định dạng.")
                response = self.create_error_response(400, "Bad Request")
                client_socket.sendall(response)
                return

            try:
                request_line = request_lines[0]
                method, path, _ = request_line.split(maxsplit=2)
            except ValueError:
                print("Yêu cầu không hợp lệ: Không thể phân tích dòng đầu tiên.")
                response = self.create_error_response(400, "Bad Request")
                client_socket.sendall(response)
                return

            environ = {
                'REQUEST_METHOD': method,
                'PATH_INFO': path,
                'SERVER_NAME': self.host,
                'SERVER_PORT': str(self.port),
                'wsgi.input': io.BytesIO(request_data),
                'wsgi.errors': io.StringIO(),
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'https' if self.use_ssl else 'http',
            }

            response_headers = []
            def start_response(status, headers):
                nonlocal response_headers
                response_headers = headers
                return lambda data: None

            response_body = self.app(environ, start_response)
            response_status = "200 OK" if response_headers else "500 Internal Server Error"
            response_headers = "\r\n".join(f"{k}: {v}" for k, v in response_headers)
            response_data = f"HTTP/1.1 {response_status}\r\n{response_headers}\r\n\r\n".encode()

            for part in response_body:
                response_data += part

            client_socket.sendall(response_data)
            print(f"Đã gửi phản hồi: {response_status}")
        except Exception as e:
            print(f"Lỗi khi xử lý yêu cầu: {e}")
            error_response = self.create_error_response(500, "Internal Server Error")
            client_socket.sendall(error_response)
        finally:
            client_socket.close()
            print("Đóng kết nối với client")

    def create_error_response(self, status_code, message):
        status_messages = {
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        }
        status_text = status_messages.get(status_code, "Unknown Error")
        response_body = f"<html><body><h1>{status_code} {status_text}</h1><p>{message}</p></body></html>"
        return f"HTTP/1.1 {status_code} {status_text}\r\nContent-Type: text/html\r\nContent-Length: {len(response_body)}\r\n\r\n{response_body}".encode()

    def serve_forever(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Server đang chạy trên {'https' if self.use_ssl else 'http'}://{self.host}:{self.port}")

        if self.use_ssl:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
                server_socket = context.wrap_socket(server_socket, server_side=True)
                print("SSL đã được áp dụng thành công.")
            except Exception as e:
                print(f"Lỗi khi áp dụng SSL: {e}")
                raise

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"Nhận kết nối từ {client_address}")
                self.pool.spawn(self.handle_request, client_socket)  
            except Exception as e:
                print(f"Lỗi khi chấp nhận kết nối: {e}")
"""

        new_main_py_content = f"""
{main_py_content}
{server_class_content}
if __name__ == "__main__":
    # Khởi tạo server riêng của bạn
    wsgi_server = SimpleWSGIServer(app)
    
    # Sử dụng gevent để chạy cả hai server đồng thời
    gevent.spawn(wsgi_server.serve_forever)  # Chạy server WSGI của bạn trong gevent greenlet
    
    # Chạy Flask-SocketIO trên port 5001 (hoặc port khác nếu cần)
    socketio.run(app, host='0.0.0.0', port=5001, ssl_context=('localhost.crt', 'localhost.key'))
"""

        new_main_py_path = os.path.join(directory_path, "new_main.py")

        with open(new_main_py_path, 'w', encoding='utf-8') as f:
            f.write(new_main_py_content)

        # Chạy server trong một tiến trình mới
        app_process = Popen([sys.executable, new_main_py_path])

        messagebox.showinfo("Thông báo", f"Máy chủ Flask đã khởi động với {new_main_py_path}")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể khởi động Flask server: {str(e)}")
def stop_flask_server():
    global app_process

    try:
        if app_process is not None:
            app_process.terminate()  # Dừng tiến trình server
            app_process.wait(timeout=5)  # Đợi tiến trình dừng
            app_process = None  # Reset app_process
            messagebox.showinfo("Thông báo", "Máy chủ Flask đã dừng.")
        else:
            messagebox.showinfo("Thông báo", "Không có máy chủ nào đang chạy.")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể dừng máy chủ Flask: {str(e)}")
def choose_directory():
    global directory_path
    directory_path = filedialog.askdirectory()
    if directory_path:
        folder_label.config(text=f"Đã chọn thư mục: {directory_path}")

def open_instructions1():
    fixed_path = os.path.abspath('flaskconfig.html')
    if os.path.exists(fixed_path):
        webbrowser.open(f'file://{fixed_path}')
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy file flaskconfig.html tại đường dẫn cố định.")
def open_instructions():
    fixed_path = os.path.abspath('index.html')
    if os.path.exists(fixed_path):
        webbrowser.open(f'file://{fixed_path}')
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy file index.html tại đường dẫn cố định.")
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def is_root():
    return os.geteuid() == 0

def run_as_admin():
    system = platform.system()
    if system == "Windows":
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
            sys.exit()
    elif system in ["Linux", "Darwin"]:
        if not is_root():
            print("Chạy lại ứng dụng với quyền root.")
            os.system(f'sudo {sys.executable} "{__file__}"')
            sys.exit()

run_as_admin()
def open_instructions2():
    fixed_path = os.path.abspath('virtualhost.html')
    if os.path.exists(fixed_path):
        webbrowser.open(f'file://{fixed_path}')
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy file index.html tại đường dẫn cố định.")
# Giao diện Tkinter
root = tk.Tk()
root.title("Bobby webserver for flask")

# Nhãn hiển thị thư mục chứa main.py
folder_label = tk.Label(root, text="Chưa chọn thư mục chứa main.py", width=50)
folder_label.pack(pady=10)

# Nút chọn thư mục chứa main.py
choose_button = tk.Button(root, text="Chọn thư mục chứa main.py", command=choose_directory)
choose_button.pack(pady=5)

# Nút khởi động máy chủ Flask
start_button = tk.Button(root, text="Bật máy chủ", command=start_flask_server)
start_button.pack(pady=5)

# Nút tắt máy chủ Flask
stop_button = tk.Button(root, text="Tắt máy chủ", command=stop_flask_server)
stop_button.pack(pady=5)

# Nút mở trang HTML hướng dẫn đưa web lên mạng
instructions_button = tk.Button(root, text="Hướng dẫn đưa web lên mạng", command=open_instructions)
instructions_button.pack(pady=5)

instructions_button1 = tk.Button(root, text="Cách cấu hình môi trường cho flask server", command=open_instructions1)
instructions_button1.pack(pady=5)
instructions_button2 = tk.Button(root, text="Cách cấu hình virtualhost cho flask server", command=open_instructions2)
instructions_button2.pack(pady=5)
# Chạy giao diện Tkinter
root.mainloop()
print("Cảm ơn đã dùng dịch vụ webserverbobby")