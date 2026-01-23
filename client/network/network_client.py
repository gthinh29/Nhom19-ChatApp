import socket
import ssl
import threading
import struct
import time
import os
import sys

# Thêm đường dẫn để import common
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt6.QtCore import QObject
from common.protocol import *
from client.core.bus import bus

class NetworkClient(QObject):
    """
    Quản lý kết nối TCP/SSL tới Server.
    Chạy một luồng riêng (Receiver Thread) để lắng nghe dữ liệu liên tục.
    """
    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.running = False
        self.send_lock = threading.Lock() # Đảm bảo thread-safe khi gửi

    def connect_to_server(self, host, port, use_ssl=True):
        """Thiết lập kết nối socket và SSL handshake"""
        try:
            # 1. Tạo socket TCP cơ bản
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 2. Bọc SSL nếu được yêu cầu (Task 4)
            if use_ssl:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                # Tắt verify chặt chẽ vì dùng self-signed cert (môi trường dev)
                context.check_hostname = False 
                context.verify_mode = ssl.CERT_NONE 
                
                self.client_socket = context.wrap_socket(
                    self.client_socket, 
                    server_hostname=host
                )

            # 3. Kết nối
            print(f"[NETWORK] Connecting to {host}:{port}...")
            self.client_socket.connect((host, port))
            self.running = True
            
            # 4. Khởi động luồng nhận tin
            receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            receive_thread.start()
            
            bus.network_connected.emit()
            print("[NETWORK] Connected successfully.")
            return True

        except Exception as e:
            print(f"[NETWORK ERROR] Connection failed: {e}")
            bus.network_disconnected.emit(str(e))
            return False

    def send_packet(self, cmd, payload=""):
        """Đóng gói và gửi lệnh tới server"""
        if not self.client_socket:
            return

        with self.send_lock:
            try:
                packet = pack_packet(cmd, payload)
                self.client_socket.sendall(packet)
            except Exception as e:
                print(f"[SEND ERROR] {e}")
                self.disconnect()

    def disconnect(self):
        """Ngắt kết nối an toàn"""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.client_socket = None
        bus.network_disconnected.emit("Connection closed")

    def _receive_loop(self):
        """Vòng lặp lắng nghe dữ liệu từ server (Chạy trên background thread)"""
        while self.running and self.client_socket:
            try:
                # 1. Đọc Header (4 bytes độ dài)
                header_data = self._read_bytes(HEADER_SIZE)
                if not header_data:
                    break # Mất kết nối

                msg_len = struct.unpack(HEADER_FORMAT, header_data)[0]

                # 2. Đọc Payload
                payload_data = self._read_bytes(msg_len)
                if not payload_data:
                    break

                # 3. Giải mã và bắn tín hiệu
                cmd, content = unpack_packet(header_data, payload_data)
                if cmd:
                    self._dispatch_command(cmd, content)

            except Exception as e:
                print(f"[RECEIVE ERROR] {e}")
                break
        
        self.disconnect()

    def _read_bytes(self, num_bytes):
        """Hàm helper để đọc đủ số bytes yêu cầu"""
        data = b""
        while len(data) < num_bytes:
            try:
                chunk = self.client_socket.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data += chunk
            except:
                return None
        return data

    def _dispatch_command(self, cmd, content):
        """Phân loại lệnh nhận được và phát tín hiệu tương ứng"""
        # Xử lý Login/Register (sẽ được AuthManager bắt)
        if cmd == CMD_LOGIN or cmd == CMD_REGISTER:
            # Logic xử lý cụ thể sẽ nằm ở AuthManager, 
            # ở đây ta dùng bus để broadcast raw message
            # Để đơn giản hóa, ta sẽ tạo một tín hiệu chung hoặc xử lý tại chỗ
            # Trong kiến trúc này, ta sẽ bắn signal raw để Manager xử lý
            pass # Tạm thời để trống, AuthManager sẽ hook vào bus sau
            
        # Lưu ý: Trong kiến trúc clean, NetworkClient chỉ nên emit data raw
        # hoặc parse sơ bộ. Để đơn giản cho task này, ta sẽ emit trực tiếp
        # thông qua bus.message_received và để các Manager lọc.
        bus.message_received.emit((cmd, content))

# Biến toàn cục
network_client = NetworkClient()