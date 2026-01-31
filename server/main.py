import socket
import threading
import ssl
import os
import sys
import time
import smtplib
import struct
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from common.protocol import Protocol
from server.database import Database
from server.router import Router

class ChatServer:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv(os.path.join(current_dir, '.env'))
        
        self.SMTP_EMAIL = os.getenv("EMAIL_USER")
        self.SMTP_PASSWORD = os.getenv("EMAIL_PASS")
        self.HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "10"))
        
        self.UPLOAD_DIR = os.path.join(current_dir, "uploads")
        self.AVATAR_DIR = os.path.join(self.UPLOAD_DIR, "avatars")
        self.FILE_DIR = os.path.join(self.UPLOAD_DIR, "files")
        
        os.makedirs(self.AVATAR_DIR, exist_ok=True)
        os.makedirs(self.FILE_DIR, exist_ok=True)

        self.MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        try:
            self.context.load_cert_chain(
                certfile=os.path.join(current_dir, 'server.crt'), 
                keyfile=os.path.join(current_dir, 'server.key')
            )
        except Exception as e:
            print(f"[CRITICAL] SSL Config Error: {e}")
            sys.exit(1)
        self.raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.raw_socket.bind((Protocol.HOST, Protocol.PORT))
        except Exception as e:
            print(f"[CRITICAL] Bind Error on port {Protocol.PORT}: {e}")
            sys.exit(1)
        self.raw_socket.listen(10)
        
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.db = Database()
        self.router = Router(self)
        self.clients = {}
        self.online_map = {}
        self.user_sessions = {}
        self.otps = {}
        self.avatar_cache = {}
        self.avatar_cache_order = []
        self.last_ping = {}
        
        self.pending_uploads = {} 
        self.pending_downloads = {}
        
        self.running = True
        self.HEARTBEAT_TIMEOUT = 30
        self.AVATAR_CACHE_MAX = 50
        
        print(f"[SERVER] Running securely at {Protocol.HOST}:{Protocol.PORT}")

    def send_packet(self, conn, message):
        try:
            message_bytes = message.encode('utf-8')
            length_prefix = struct.pack('!I', len(message_bytes))
            conn.sendall(length_prefix + message_bytes)
        except: pass

    def broadcast(self, message, sender_conn=None):
        active_conns = list(self.clients.keys())
        for conn in active_conns:
            if conn != sender_conn:
                try: self.send_packet(conn, message)
                except: pass

    def is_valid_email(self, email):
        import re
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

    def send_email(self, to_email, subject, body):
        if not self.SMTP_EMAIL or not self.SMTP_PASSWORD:
            print("⚠️ SMTP credentials missing")
            return False
        try:
            msg = MIMEMultipart()
            msg['From'] = self.SMTP_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.SMTP_EMAIL, self.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
            return False
            
    def get_avatar_base64(self, filename):
        if not filename: return ""
        path = os.path.join(self.AVATAR_DIR, filename)
        if os.path.exists(path):
            try:
                mtime = os.path.getmtime(path)
                cached = self.avatar_cache.get(filename)
                if cached and cached[0] == mtime: return cached[1]

                with open(path, "rb") as f: file_data = f.read()
                
                if not (file_data.startswith(b'\x89PNG\r\n\x1a\n') or file_data.startswith(b'\xff\xd8\xff')): pass 

                b64 = base64.b64encode(file_data).decode('utf-8')
                
                if len(self.avatar_cache) >= self.AVATAR_CACHE_MAX:
                    if self.avatar_cache_order:
                        oldest = self.avatar_cache_order.pop(0)
                        self.avatar_cache.pop(oldest, None)
                
                self.avatar_cache[filename] = (mtime, b64)
                if filename in self.avatar_cache_order: self.avatar_cache_order.remove(filename)
                self.avatar_cache_order.append(filename)
                return b64
            except: pass
        return ""

    def _read_exact(self, conn, size):
        buf = b""
        while len(buf) < size:
            try:
                chunk = conn.recv(size - len(buf))
                if not chunk: return None
                buf += chunk
            except: return None
        return buf

    def handle_connection_entry(self, conn, addr):
        print(f"➕ [CONN] {addr} connected.")
        try:
            length_prefix = self._read_exact(conn, 4)
            if not length_prefix: conn.close(); return

            msg_len = struct.unpack('!I', length_prefix)[0]
            if msg_len > 1024: conn.close(); return

            handshake_data = self._read_exact(conn, msg_len)
            if not handshake_data: conn.close(); return
            
            try: handshake_str = handshake_data.decode('utf-8')
            except: conn.close(); return

            if handshake_str.startswith(f"{Protocol.FILE_STREAM}|"):
                parts = handshake_str.split("|")
                if len(parts) >= 2: self.handle_data_stream(conn, addr, parts[1])
                else: conn.close()
                    
            elif handshake_str.startswith(f"{Protocol.FILE_DOWNLOAD_STREAM}|"):
                parts = handshake_str.split("|")
                if len(parts) >= 2: self.handle_download_stream(conn, addr, parts[1])
                else: conn.close()
                    
            else: self.handle_chat_loop(conn, addr, initial_msg=handshake_str)

        except Exception as e:
            print(f"[CONN ERROR] {addr}: {e}")
            conn.close()

    def handle_data_stream(self, conn, addr, token):
        print(f"🚀 [UPLOAD] Starting upload stream for token: {token}")
        
        upload_info = self.pending_uploads.get(token)
        if not upload_info:
            self.send_packet(conn, "ERROR|Invalid Token")
            conn.close(); return

        username = upload_info['username']
        filename = upload_info['filename']
        total_size = upload_info['total_size']
        file_id = upload_info['file_id']
        temp_path = upload_info.get('temp_path')
        offset = upload_info.get('offset', 0)
        if not temp_path:
            safe_filename = os.path.basename(filename)
            temp_path = os.path.join(self.FILE_DIR, f"temp_{username}_{safe_filename}.part")

        received_bytes = offset
        
        try:
            self.send_packet(conn, "READY")
            print(f"📥 [UPLOAD] Receiving {filename} from byte {offset}...")
            mode = 'ab' if offset > 0 else 'wb'
            
            with open(temp_path, mode) as f:
                while received_bytes < total_size:
                    chunk_size = min(65536, total_size - received_bytes)
                    chunk = conn.recv(chunk_size)
                    if not chunk: raise ConnectionError("Connection lost")
                    f.write(chunk)
                    received_bytes += len(chunk)
            
            print(f"✅ [UPLOAD] Transfer complete: {filename}")
            # filename đã có timestamp từ chat_controller, không cần thêm nữa
            final_filename = filename
            final_path = os.path.join(self.FILE_DIR, final_filename)
            
            if os.path.exists(final_path): os.remove(final_path)
            os.rename(temp_path, final_path)
            
            self.db.complete_file_transfer(username, file_id)
            msg_content = f"[FILE]:{final_filename}|" 
            self.db.save_message(username, msg_content, msg_type="file")
            
            if token in self.pending_uploads: del self.pending_uploads[token]

            self.send_packet(conn, "SUCCESS")
            
            u_info = self.db.get_user_info(username)
            d_name = u_info.get('fullname', username) if u_info else username
            avt = u_info.get('avatar', "")
            sender_info = f"{username}|{d_name}|{self.get_avatar_base64(avt)}"
            self.broadcast(f"{sender_info}:{msg_content}")

        except Exception as e:
            print(f"❌ [UPLOAD ERROR] {e}")
        finally:
            conn.close()

    def handle_download_stream(self, conn, addr, token):
        print(f"🚀 [DOWNLOAD] Starting download stream for token: {token}")
        
        download_info = self.pending_downloads.get(token)
        if not download_info:
            conn.close(); return
            
        file_path = download_info['file_path']
        offset = download_info.get('offset', 0)
        
        if not os.path.exists(file_path):
            conn.close(); return
            
        try:
            file_size = os.path.getsize(file_path)
            sent_bytes = offset
            chunk_size = 65536
            print(f"📤 [DOWNLOAD] Continuing download {os.path.basename(file_path)} from {offset}/{file_size}...")
            with open(file_path, "rb") as f:
                if offset > 0:
                    f.seek(offset)
                
                while sent_bytes < file_size:
                    chunk = f.read(chunk_size)
                    if not chunk: break
                    conn.sendall(chunk)
                    sent_bytes += len(chunk)
            
            print(f"✅ [DOWNLOAD] Finished sending to {addr}")
            
            if token in self.pending_downloads:
                del self.pending_downloads[token]

        except Exception as e:
            print(f"❌ [DOWNLOAD ERROR] {e}")
        finally:
            conn.close()

    def handle_chat_loop(self, conn, addr, initial_msg=None):
        buffer = b""
        if initial_msg:
            try:
                parts = initial_msg.split("|")
                cmd = parts[0]
                current_user = self.clients.get(conn)
                self.router.dispatch(conn, cmd, parts, current_user)
            except Exception as e: print(f"[INIT MSG ERROR] {e}")

        try:
            while self.running:
                try:
                    chunk = conn.recv(4096)
                    if not chunk: break
                    buffer += chunk
                except: break
                
                while len(buffer) >= Protocol.LENGTH_PREFIX_SIZE:
                    length_prefix = buffer[:Protocol.LENGTH_PREFIX_SIZE]
                    message_length = struct.unpack('!I', length_prefix)[0]
                    
                    if len(buffer) < Protocol.LENGTH_PREFIX_SIZE + message_length: break
                    
                    packet_data = buffer[Protocol.LENGTH_PREFIX_SIZE:Protocol.LENGTH_PREFIX_SIZE + message_length]
                    buffer = buffer[Protocol.LENGTH_PREFIX_SIZE + message_length:]
                    
                    try:
                        raw_msg = packet_data.decode('utf-8')
                        if not raw_msg: continue
                        parts = raw_msg.split("|")
                        cmd = parts[0]
                        
                        if cmd == "PING":
                            self.last_ping[conn] = time.time()
                            self.send_packet(conn, "PONG")
                            continue
                        
                        current_user = self.clients.get(conn)
                        try: self.router.dispatch(conn, cmd, parts, current_user)
                        except: pass
                        
                    except: pass
        except: pass
        finally:
            self.disconnect_client(conn)

    def monitor_heartbeats(self):
        while self.running:
            try:
                now = time.time()
                dead_conns = []
                for conn, last_ts in list(self.last_ping.items()):
                    if now - last_ts > self.HEARTBEAT_TIMEOUT: dead_conns.append(conn)
                for conn in dead_conns: self.disconnect_client(conn)
                time.sleep(5) 
            except: pass

    def disconnect_client(self, conn):
        username = None
        if conn in self.online_map:
            username, _ = self.online_map[conn]
            del self.online_map[conn]
        if conn in self.clients: del self.clients[conn]
        if conn in self.last_ping: del self.last_ping[conn]
            
        if username:
            try:
                sessions = self.user_sessions.get(username)
                if sessions and conn in sessions:
                    sessions.remove(conn)
                    if not sessions:
                        del self.user_sessions[username]
                        self.broadcast(f"{Protocol.USER_STATUS}|LEAVE|{username}")
                else: self.broadcast(f"{Protocol.USER_STATUS}|LEAVE|{username}")
            except: pass
        try: conn.close()
        except: pass

    def broadcast_presence(self):
        msg = f"CHAT_SERVER|{Protocol.PORT}".encode('utf-8')
        while self.running:
            try:
                self.udp_socket.sendto(msg, ('<broadcast>', Protocol.BROADCAST_PORT))
                time.sleep(2)
            except: pass

    def accept_loop(self):
        while self.running:
            try:
                client, addr = self.raw_socket.accept()
                ssl_conn = self.context.wrap_socket(client, server_side=True)
                threading.Thread(target=self.handle_connection_entry, args=(ssl_conn, addr), daemon=True).start()
            except: break

    def start(self):
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.monitor_heartbeats, daemon=True).start()
        
        accept_thread = threading.Thread(target=self.accept_loop, daemon=True)
        accept_thread.start()
        
        print("✅ Server is READY.")
        print(f"ℹ️  Max File Size: {self.MAX_FILE_SIZE / (1024*1024*1024):.2f} GB")
        
        try:
            while self.running: time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Server shutting down...")
            self.running = False
            try: self.raw_socket.close()
            except: pass
            sys.exit(0)

if __name__ == "__main__":
    ChatServer().start()