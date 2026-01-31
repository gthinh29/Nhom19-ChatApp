"""
Client Network Management - Quản lý kết nối mạng từ phía Client
Xử lý SSL/TLS, tìm kiếm Server tự động, gửi/nhận gói tin
[FINAL FIX] 
1. Parse Offset và Final Name từ UPLOAD_RESP để hỗ trợ Resume Upload và cập nhật tên file thật.
2. Parse DOWNLOAD_RESP chuẩn xác.
3. Thêm Debug Log chi tiết.
"""

import socket
import ssl
import os
import sys
import threading
import struct
import time
from PyQt6.QtCore import QThread, pyqtSignal

# Import Protocol
try:
    from common.protocol import Protocol
except ImportError:
    # Fallback import path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    client_dir = os.path.dirname(os.path.dirname(current_dir)) 
    root_dir = os.path.dirname(client_dir)
    sys.path.append(root_dir)
    from common.protocol import Protocol

from client.core.bus import SignalBus

class ReceiverThread(QThread):
    """Luồng nhận tin nhắn liên tục từ Server"""
    
    def __init__(self, client_socket):
        super().__init__()
        self.sock = client_socket
        self.running = True
        self.buffer = b""
        self.bus = SignalBus.get()

    def run(self):
        """Vòng lặp chính nhận dữ liệu"""
        while self.running:
            try:
                # 1. Đọc dữ liệu thô từ Socket
                data = self.sock.recv(1024 * 64)
                
                # 2. Kiểm tra kết nối đóng
                if not data: 
                    break
                
                # 3. Kiểm tra cờ chạy
                if not self.running: 
                    break

                self.buffer += data
                
                # 4. Xử lý Stream (Cắt gói tin theo Length-Prefix)
                while len(self.buffer) >= Protocol.LENGTH_PREFIX_SIZE:
                    message_length = struct.unpack('!I', self.buffer[:Protocol.LENGTH_PREFIX_SIZE])[0]
                    total_needed = Protocol.LENGTH_PREFIX_SIZE + message_length
                    
                    if len(self.buffer) < total_needed: 
                        break # Chờ thêm dữ liệu
                    
                    pkt_bytes = self.buffer[Protocol.LENGTH_PREFIX_SIZE:total_needed]
                    self.buffer = self.buffer[total_needed:]
                    
                    # Parse gói tin và bắn Signal
                    self._process_packet(pkt_bytes)
            
            except OSError:
                break
            except Exception as e:
                print(f"Receiver Error: {e}")
                break
        
        # 5. Logic bắn Signal ngắt kết nối
        if self.running:
            self.bus.network_disconnected.emit()

    def _process_packet(self, pkt_bytes):
        try:
            raw_msg = pkt_bytes.decode('utf-8')
            if raw_msg == "PONG": return

            # [DEBUG] Soi gói tin Token Resume
            if "UPLOAD_RESP" in raw_msg or "DOWNLOAD_RESP" in raw_msg:
                print(f"📥 [NET] Received: {raw_msg}")

            parsed_data = self._parse_raw_message(raw_msg)
            if parsed_data:
                self.bus.network_packet_received.emit(parsed_data)
        except: pass

    def _parse_raw_message(self, raw_msg):
        """Chuyển đổi chuỗi raw (Protocol) thành Dict dễ dùng"""
        
        # 1. Force Logout
        if raw_msg.startswith(f"{Protocol.FORCE_LOGOUT}|"):
            return {"type": "force_logout", "content": raw_msg.split("|")[1]}

        # 2. File Offset (Resume)
        if raw_msg.startswith(f"{Protocol.FILE}|OFFSET|"):
            parts = raw_msg.split("|")
            if len(parts) >= 4:
                return {"type": "file_offset", "fileid": parts[2], "offset": int(parts[3])}
            else:
                return {"type": "file_offset", "fileid": None, "offset": int(parts[2])} 

        # 3. Pending Files List
        if raw_msg.startswith("PENDING_FILES|"):
            parts = raw_msg.split("|")
            files = []
            for i in range(1, len(parts), 6):
                if i + 5 < len(parts):
                    try:
                        files.append({
                            'fileid': parts[i],
                            'filename': parts[i+1],
                            'total_size': int(parts[i+2]),
                            'uploaded_bytes': int(parts[i+3]),
                            'status': parts[i+4],
                            'file_path': parts[i+5] or None
                        })
                    except: pass
            return {"type": "pending_files", "files": files}

        # 4. Online List
        if raw_msg.startswith(f"{Protocol.ONLINE_LIST}|"):
            parts = raw_msg.split("|")[1:]
            users = []
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    users.append({"username": parts[i], "fullname": parts[i+1]})
            return {"type": "online_list", "users": users}

        # 5. User Status
        if raw_msg.startswith(f"{Protocol.USER_STATUS}|"):
            parts = raw_msg.split("|")
            return {
                "type": "user_status",
                "status": parts[1],
                "username": parts[2],
                "fullname": parts[3] if len(parts) > 3 else parts[2]
            }

        # 6. History
        if raw_msg.startswith(f"{Protocol.HISTORY}|"):
            parts = raw_msg.split("|", 2)
            if parts[1] == "END": return {"type": "history_end"}
            if parts[1] == "BATCH_END": return {"type": "history_batch_end"}
            
            try:
                msg_id = int(parts[1])
                payload = parts[2]
                
                if ":" in payload:
                    header, content = payload.split(":", 1)
                else:
                    header, content = payload, ""
                
                sender_id, sender_display, sender_avatar = header, header, ""
                if "|" in header:
                    h_parts = header.split("|")
                    if len(h_parts) >= 1: sender_id = h_parts[0]
                    if len(h_parts) >= 2: sender_display = h_parts[1]
                    if len(h_parts) >= 3: sender_avatar = h_parts[2]

                msg_data = {
                    "type": "history", 
                    "msg_id": msg_id, 
                    "sender": sender_display, 
                    "sender_id": sender_id, 
                    "avatar_data": sender_avatar,
                    "content": content
                }
                self._detect_content_type(msg_data, content)
                msg_data["content_type"] = msg_data.get("type")
                msg_data["type"] = "history"
                return msg_data
            except: return None

        # 7. UPLOAD & DOWNLOAD RESPONSE [RESUME SUPPORT]
        
        # 7a. UPLOAD RESPONSE: UPLOAD_RESP|token|offset|final_filename
        if raw_msg.startswith(f"{Protocol.UPLOAD_RESP}|"):
            parts = raw_msg.split("|")
            token = parts[1] if len(parts) > 1 else ""
            offset = int(parts[2]) if len(parts) > 2 else 0
            # [FIX] Lấy tên file thật (final_name) từ tham số thứ 4
            final_name = parts[3] if len(parts) > 3 else None
            
            return {
                "type": "upload_resp", 
                "command": Protocol.UPLOAD_RESP,
                "token": token,
                "offset": offset,
                "final_name": final_name # FileManager sẽ dùng cái này
            }

        # 7b. DOWNLOAD RESPONSE: DOWNLOAD_RESP|token|size
        if raw_msg.startswith(f"{Protocol.DOWNLOAD_RESP}|"):
            parts = raw_msg.split("|")
            token = parts[1] if len(parts) > 1 else ""
            try: size = int(parts[2])
            except: size = 0
            return {
                "type": "download_resp",
                "command": Protocol.DOWNLOAD_RESP,
                "token": token,
                "size": size
            }

        # 8. System / OTP / Update Profile
        if "Mã OTP" in raw_msg and "được gửi" in raw_msg:
            return {"type": "system", "content": raw_msg}
        
        if raw_msg.startswith("System:") or raw_msg.startswith("SUCCESS|") or raw_msg.startswith("ERROR|"):
            content = raw_msg.split("|", 1)[1] if "|" in raw_msg else raw_msg
            return {
                "type": "system", 
                "command": Protocol.ERROR if raw_msg.startswith("ERROR|") else "system",
                "message": content, 
                "content": content
            }

        if raw_msg.startswith("UPDATE_OK|"):
            p = raw_msg.split("|")
            return {"type": "profile_update", "fullname": p[1], "avatar": p[2] if len(p)>2 else ""}

        # 9. Normal Message
        if ":" in raw_msg:
            header, content = raw_msg.split(":", 1)
            sender_id, sender_display, sender_avatar = header, header, ""
            
            if "|" in header:
                parts = header.split("|")
                if len(parts) >= 1: sender_id = parts[0]
                if len(parts) >= 2: sender_display = parts[1]
                if len(parts) >= 3: sender_avatar = parts[2]
            
            msg_data = {
                "is_message_packet": True, 
                "sender": sender_display,
                "sender_id": sender_id, 
                "avatar_data": sender_avatar,
                "content": content
            }
            self._detect_content_type(msg_data, content)
            return msg_data

        return None

    def _detect_content_type(self, data_dict, content):
        if not content:
            data_dict["type"] = "text"
            return

        if content.startswith("[IMAGE]:"):
            try:
                real_content = content[8:]
                if "|" in real_content:
                    info, b64 = real_content.split("|", 1)
                else:
                    info, b64 = "unknown.png", ""
                
                data_dict["type"] = "image"
                
                from PyQt6.QtGui import QImage
                import base64
                try:
                    img_data = base64.b64decode(b64)
                    qimg = QImage.fromData(img_data)
                    data_dict["qimage"] = qimg if not qimg.isNull() else None
                except:
                    data_dict["qimage"] = None
            except: 
                data_dict["content"] = "Ảnh lỗi"
            
        elif content.startswith("[FILE]:"):
            try:
                real_content = content[7:]
                parts = real_content.split("|")
                data_dict["type"] = "file"
                data_dict["filename"] = parts[0]
                data_dict["data"] = parts[1] if len(parts) > 1 else ""
            except: pass
        else:
            data_dict["type"] = "text"


class NetworkClient:
    """Lớp quản lý kết nối mạng"""
    
    def __init__(self):
        self.context = ssl.create_default_context()
        
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cert_path = os.path.join(base_path, 'server', 'server.crt')
        
        if os.path.exists(cert_path):
            self.context.load_verify_locations(cert_path)
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_REQUIRED
        else:
            print(f"⚠️ Certificate not found at {cert_path}")
        
        self.client_socket = None
        self.is_connected = False
        self.username = ""
        self.send_lock = threading.Lock()
        
        self.receiver_thread = None
        self.bus = SignalBus.get()

        self.keep_heartbeat = True
        self.heartbeat_thread = None

    def find_server(self):
        print("📡 Đang quét tìm Server...")
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp.bind(('', Protocol.BROADCAST_PORT))
            udp.settimeout(2.0)
            while True:
                data, addr = udp.recvfrom(1024)
                msg = data.decode('utf-8')
                if msg.startswith("CHAT_SERVER|"):
                    _, port_str = msg.split("|")
                    udp.close()
                    return addr[0], int(port_str)
        except: pass
        udp.close()
        return None, None

    def connect_server(self, ip=None, port=None):
        if self.client_socket:
            try: self.client_socket.close()
            except: pass
            self.client_socket = None

        if ip is None:
            found_ip, found_port = self.find_server()
            if found_ip: ip, port = found_ip, found_port
            else: 
                ip, port = 'localhost', 12345 

        print(f"⏳ Đang kết nối tới {ip}:{port}...")
        try:
            raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw.settimeout(10.0)
            raw.connect((ip, port))
            self.client_socket = self.context.wrap_socket(raw, server_hostname=ip)
            self.client_socket.settimeout(None)
            
            self.is_connected = True
            
            self.bus.network_connected.emit()
            
            return True, f"Kết nối thành công {ip}:{port}"
        except Exception as e:
            self.is_connected = False
            return False, str(e)

    def start_receiver(self):
        self.keep_heartbeat = True
        if self.heartbeat_thread is None or not self.heartbeat_thread.is_alive():
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_sender, daemon=True)
            self.heartbeat_thread.start()

        if self.receiver_thread and self.receiver_thread.isRunning(): return
        self.receiver_thread = ReceiverThread(self.client_socket)
        self.receiver_thread.start()

    def disconnect(self):
        print("[Network] Disconnecting...")
        self.is_connected = False
        self.keep_heartbeat = False
        if self.receiver_thread:
            self.receiver_thread.running = False 

        with self.send_lock:
            if self.client_socket:
                try: self.client_socket.shutdown(socket.SHUT_RDWR)
                except: pass
                try: self.client_socket.close()
                except: pass
                self.client_socket = None

        if self.receiver_thread:
            if self.receiver_thread.isRunning():
                self.receiver_thread.wait() 
            self.receiver_thread = None

        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread = None
            
        print("[Network] Disconnected clean.")

    def _heartbeat_sender(self):
        while self.keep_heartbeat and self.is_connected:
            try:
                time.sleep(10)
                if self.is_connected: self.send_packet("PING")
            except: pass

    def send_packet(self, data_str):
        if not self.is_connected: return False
        with self.send_lock:
            sock = self.client_socket
            if not sock: return False
            try:
                data_bytes = data_str.encode('utf-8')
                length_prefix = struct.pack('!I', len(data_bytes))
                sock.sendall(length_prefix + data_bytes)
                return True
            except Exception as e:
                print(f"Send Error: {e}")
                try:
                    self.is_connected = False
                    self.bus.network_disconnected.emit()
                except: pass
                return False

    def receive_response(self, timeout=10.0):
        if not self.is_connected: return f"{Protocol.ERROR}|Mất kết nối"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.client_socket.settimeout(timeout)
                received_data = b""
                while len(received_data) < Protocol.LENGTH_PREFIX_SIZE:
                    chunk = self.client_socket.recv(Protocol.LENGTH_PREFIX_SIZE - len(received_data))
                    if not chunk: break
                    received_data += chunk
                
                if len(received_data) < Protocol.LENGTH_PREFIX_SIZE: return f"{Protocol.ERROR}|Lỗi Protocol"
                
                msg_len = struct.unpack('!I', received_data)[0]
                msg_data = b""
                while len(msg_data) < msg_len:
                    chunk = self.client_socket.recv(msg_len - len(msg_data))
                    if not chunk: break
                    msg_data += chunk
                
                decoded_msg = msg_data.decode('utf-8', errors='ignore')
                if decoded_msg == "PONG": continue
                    
                self.client_socket.settimeout(None)
                return decoded_msg
            except Exception as e:
                return f"{Protocol.ERROR}|Lỗi nhận: {e}"
            finally:
                try: self.client_socket.settimeout(None)
                except: pass
        
        return f"{Protocol.ERROR}|Timeout"
    
    def send_history(self, last_id):
        lid = int(last_id) if last_id is not None else 0
        self.send_packet(f"{Protocol.HISTORY}|{lid}")

    def send_login(self, u, p):
        if not self.is_connected: return False, "Chưa kết nối Server", ""
        if self.send_packet(f"{Protocol.LOGIN}|{u}|{p}"):
            resp = self.receive_response()
            parts = resp.split("|")
            if parts[0] == Protocol.SUCCESS:
                # Lưu username vào client để các luồng UI có thể so sánh và bỏ qua
                try:
                    self.username = u
                except: pass
                return True, parts[1] if len(parts) > 1 else u, parts[2] if len(parts) > 2 else ""
            else:
                return False, parts[1] if len(parts) > 1 else "Sai thông tin", ""
        return False, "Lỗi gửi gói tin", ""

    def send_register(self, u, p, n, e):
        if not self.is_connected: return False, "Chưa kết nối Server"
        if self.send_packet(f"{Protocol.REGISTER}|{u}|{p}|{n}|{e}"):
            resp = self.receive_response()
            parts = resp.split("|")
            if parts[0] == Protocol.SUCCESS:
                return True, parts[1] if len(parts) > 1 else "Đăng ký thành công"
            else:
                return False, parts[1] if len(parts) > 1 else "Lỗi đăng ký"
        return False, "Lỗi gửi gói tin"

    def send_forgot_request(self, u, e):
        if not self.is_connected: return False, "Chưa kết nối Server"
        self.send_packet(f"{Protocol.FORGOT_PW}|{u}|{e}")
        resp = self.receive_response()
        parts = resp.split("|")
        return (parts[0] == Protocol.SUCCESS), (parts[1] if len(parts) > 1 else "Lỗi")

    def send_confirm_reset(self, u, otp, new_pass):
        if not self.is_connected: return False, "Chưa kết nối Server"
        self.send_packet(f"{Protocol.CONFIRM_RESET}|{u}|{otp}|{new_pass}")
        resp = self.receive_response()
        parts = resp.split("|")
        return (parts[0] == Protocol.SUCCESS), (parts[1] if len(parts) > 1 else "Lỗi")