import socket
import threading
import ssl
import sys
import os
import configparser

# Add parent directory to path to import common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import *
# Import chính thức (đã bỏ try-except của giai đoạn 1)
from server.router import Router
from server.database import Database

# Load Config
config = configparser.ConfigParser()
config.read('config.ini')

HOST = config['server']['HOST']
PORT = int(config['server']['PORT'])
SSL_CERT = config['security']['SSL_CERT_FILE']
SSL_KEY = config['security']['SSL_KEY_FILE']

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr, router):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.router = router
        self.username = None
        self.running = True

    def run(self):
        print(f"[NEW CONNECTION] {self.addr} connected.")
        
        try:
            # Thêm client vào danh sách quản lý của Router ngay khi kết nối
            if self.router:
                self.router.add_client(self)

            while self.running:
                # 1. Read Header (4 bytes)
                header_data = self.read_bytes(HEADER_SIZE)
                if not header_data:
                    break
                
                msg_len = struct.unpack(HEADER_FORMAT, header_data)[0]
                
                # 2. Read Payload
                payload_data = self.read_bytes(msg_len)
                if not payload_data:
                    break
                
                # 3. Process
                cmd, content = unpack_packet(header_data, payload_data)
                if cmd:
                    # Router xử lý logic chính
                    if self.router:
                        self.router.route(self, cmd, content)
                    else:
                        print(f"[RAW RECV] {cmd}: {content[:50]}...")

        except Exception as e:
            print(f"[ERROR] {self.addr}: {e}")
        finally:
            self.close()

    def read_bytes(self, num_bytes):
        data = b""
        while len(data) < num_bytes:
            try:
                chunk = self.conn.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data += chunk
            except:
                return None
        return data

    def send(self, cmd, payload=""):
        try:
            packet = pack_packet(cmd, payload)
            self.conn.sendall(packet)
        except Exception as e:
            print(f"[SEND ERROR] {e}")

    def close(self):
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        # Xóa client khỏi danh sách quản lý
        if self.router:
             self.router.remove_client(self)
        print(f"[DISCONNECT] {self.addr} closed.")

def start_server():
    # Khởi tạo Database và Router (Đã kích hoạt)
    print("[INIT] Connecting to Database...")
    db = Database() 
    
    print("[INIT] Starting Router...")
    router = Router(db) 

    # Socket Setup
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Cho phép tái sử dụng địa chỉ port ngay khi tắt server (tránh lỗi Address already in use)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    
    # SSL Context Setup
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    try:
        context.load_cert_chain(certfile=SSL_CERT, keyfile=SSL_KEY)
        print("[SECURE] SSL Context loaded successfully.")
    except FileNotFoundError:
        print("[WARNING] SSL Cert not found. Running in plain TCP mode (Development only).")
    
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    while True:
        try:
            conn, addr = server.accept()
            # Wrap socket với SSL
            try:
                conn_ssl = context.wrap_socket(conn, server_side=True)
                thread = ClientHandler(conn_ssl, addr, router)
                thread.start()
                print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            except ssl.SSLError as e:
                print(f"[SSL HANDSHAKE FAILED] {addr}: {e}")
                conn.close()
        except Exception as e:
            print(f"[SERVER ERROR] {e}")

if __name__ == "__main__":
    start_server()