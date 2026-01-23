import socket
import threading
import ssl
import sys
import os
import configparser

# Add parent directory to path to import common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import *
# Các module này sẽ được tạo ở Giai đoạn 2, nhưng ta cứ import sẵn
try:
    from server.router import Router
    from server.database import Database
except ImportError:
    print("Warning: Router or Database not found yet (Phase 1)")

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
        buffer = b""
        
        try:
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
                    # Router will handle logic (Phase 2)
                    if hasattr(self, 'router') and self.router:
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
        # Remove from global list (handled in Router usually)
        if hasattr(self, 'router') and self.router:
             self.router.remove_client(self)
        print(f"[DISCONNECT] {self.addr} closed.")

def start_server():
    # Database & Router Setup (Phase 2 placeholders)
    db = None 
    router = None
    # db = Database() # Uncomment in Phase 2
    # router = Router(db) # Uncomment in Phase 2

    # Socket Setup
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    
    # SSL Context (Task 4) - Sẽ cấu hình kỹ hơn khi có Cert
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    try:
        context.load_cert_chain(certfile=SSL_CERT, keyfile=SSL_KEY)
    except FileNotFoundError:
        print("[WARNING] SSL Cert not found. Running in plain TCP mode might fail if client expects SSL.")
    
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        try:
            # Wrap socket with SSL
            conn_ssl = context.wrap_socket(conn, server_side=True)
            thread = ClientHandler(conn_ssl, addr, router)
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        except Exception as e:
            print(f"[SSL HANDSHAKE ERROR] {e}")

if __name__ == "__main__":
    start_server()