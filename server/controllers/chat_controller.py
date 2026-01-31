

from common.protocol import Protocol
import time
import os
import base64
import uuid

class ChatController:
    """Controller quản lý các yêu cầu liên quan đến việc gửi/nhận tin nhắn"""
    
    def __init__(self, server_context):
        """Khởi tạo với context server và database"""
        self.server = server_context
        self.db = server_context.db

    def _get_sender_info(self, conn):
        """Lấy thông tin người gửi: Username|Fullname|AvatarBase64"""
        if conn in self.server.online_map:
            u_name, f_name = self.server.online_map[conn]
            
            # Lấy thông tin mới nhất từ DB
            u_info = self.db.get_user_info(u_name)
            
            # Xử lý kết quả trả về từ DB (Dictionary)
            avt_file = ""
            real_name = f_name
            
            if u_info:
                avt_file = u_info.get('avatar', "")
                real_name = u_info.get('fullname', f_name)
            
            # Lấy Base64 avatar an toàn
            try:
                avt_b64 = self.server.get_avatar_base64(avt_file)
            except:
                avt_b64 = ""
            
            return f"{u_name}|{real_name}|{avt_b64}"
        return None

    def handle_message(self, conn, parts):
        """Xử lý tin nhắn văn bản"""
        sender_info = self._get_sender_info(conn)
        if sender_info and len(parts) >= 2:
            content = "|".join(parts[1:])
            username = sender_info.split("|")[0]
            
            mid = self.db.save_message(username, content, msg_type="text")
            print(f"[MSG] Saved text from {username} (ID: {mid})")

            self.server.broadcast(f"{sender_info}:{content}", sender_conn=conn)

    def handle_image(self, conn, parts):
        """Xử lý gửi ảnh (Vẫn giữ logic cũ cho ảnh nhỏ/chụp nhanh)"""
        sender_info = self._get_sender_info(conn)
        if sender_info and len(parts) >= 3:
            fn, b64 = parts[1], parts[2]
            c_str = f"[IMAGE]:{fn}|{b64}"
            username = sender_info.split("|")[0]
            
            mid = self.db.save_message(username, c_str, msg_type="image")
            print(f"[IMG] Saved image from {username} (ID: {mid})")
            
            self.server.broadcast(f"{sender_info}:{c_str}", sender_conn=conn)

    def handle_upload_request(self, conn, parts, current_user):
        """
        Xử lý yêu cầu gửi file lớn với hỗ trợ tiếp tục
        Giao thức: UPLOAD_REQ|filename|filesize
        """
        if len(parts) < 3: return
        
        # Sau thẩu file name để an toàn
        raw_filename = parts[1]
        filename = raw_filename.replace("|", "_")
        
        try: total_size = int(parts[2])
        except: return
        
        # Kiểm tra giới hạn file
        max_size = getattr(self.server, 'MAX_FILE_SIZE', 4 * 1024 * 1024 * 1024)
        if total_size > max_size:
            self.server.send_packet(conn, f"{Protocol.ERROR}|File too large (>4GB)")
            return

        # Tạo Token và ID
        token = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        
        safe_filename = os.path.basename(filename)
        
        # Tạo tên file Unique (Final Name) để lưu trữ và trả về cho Client
        # Ví dụ: 172839_tailieu.pdf
        final_filename = f"{int(time.time())}_{safe_filename}"
        
        # Xác định file tạm để tính Offset
        temp_filename = f"temp_{current_user}_{safe_filename}.part"
        temp_path = os.path.join(self.server.FILE_DIR, temp_filename)
        
        offset = 0
        if os.path.exists(temp_path):
            current_size = os.path.getsize(temp_path)
            if current_size < total_size:
                offset = current_size
                print(f"🔄 [RESUME] Found partial file. Resuming from {offset} bytes.")
            else:
                # File cũ bị lỗi hoặc đã xong nhưng chưa dọn, xóa làm lại
                try: os.remove(temp_path)
                except: pass
        
        # 1. Lưu vào DB (Dùng tên final_filename)
        self.db.create_or_update_file_transfer(
            current_user, file_id, final_filename, total_size, offset, 'pending', ""
        )
        
        # 2. Lưu vào Memory
        self.server.pending_uploads[token] = {
            'username': current_user,
            'filename': final_filename, # Server sẽ lưu file cuối cùng với tên này
            'total_size': total_size,
            'file_id': file_id,
            'created_at': time.time(),
            'temp_path': temp_path,     # Ghi vào file tạm này
            'offset': offset            # Vị trí ghi tiếp
        }
        
        # 3. Trả về Token, Offset VÀ FINAL FILENAME cho Client
        # Client cần final_filename để khi upload xong, nó tạo bong bóng chat với tên đúng trên server
        print(f"🎫 [UPLOAD] Token: {token} | Offset: {offset}/{total_size}")
        self.server.send_packet(conn, f"{Protocol.UPLOAD_RESP}|{token}|{offset}|{final_filename}")

    def handle_download_request(self, conn, parts, current_user):
        """
        Xử lý yêu cầu tải file từ Server với hỗ trợ tiếp tục
        Giao thức: DOWNLOAD_REQ|filename|offset(optional)
        """
        if len(parts) < 2: return
        
        # Sau thẩu file name
        filename = parts[1].replace("|", "_")
        
        # Lấy offset từ Client (nếu có)
        offset = 0
        if len(parts) >= 3:
            try: offset = int(parts[2])
            except: offset = 0
        
        if ".." in filename or "/" in filename or "\\" in filename:
             self.server.send_packet(conn, f"{Protocol.ERROR}|Tên file không hợp lệ")
             return

        file_path = os.path.join(self.server.FILE_DIR, filename)
        if not os.path.exists(file_path):
             print(f"⚠️ [DOWNLOAD] File not found: {filename}")
             self.server.send_packet(conn, f"{Protocol.ERROR}|File không tồn tại trên Server")
             return

        file_size = os.path.getsize(file_path)
        if offset >= file_size: offset = 0 
        
        token = str(uuid.uuid4())
        
        if not hasattr(self.server, 'pending_downloads'):
            self.server.pending_downloads = {}

        self.server.pending_downloads[token] = {
            'file_path': file_path,
            'user': current_user,
            'created_at': time.time(),
            'offset': offset 
        }
        
        self.server.send_packet(conn, f"{Protocol.DOWNLOAD_RESP}|{token}|{file_size}")

    def handle_file(self, conn, parts):
        pass

    def handle_history(self, conn, parts):
        last_id = None
        if len(parts) >= 2:
            try: last_id = int(parts[1])
            except: pass
        
        limit = getattr(self.server, "HISTORY_LIMIT", 20)
        
        try:
            rows = self.db.get_recent_messages(limit, before_id=last_id)
            rows = list(rows)[::-1]
        except Exception as e:
            print(f"[HISTORY ERROR] DB Call failed: {e}")
            self.server.send_packet(conn, f"{Protocol.HISTORY}|END")
            return

        if not rows:
            self.server.send_packet(conn, f"{Protocol.HISTORY}|END")
            return

        for row in rows:
            try:
                msg_id = row[0]
                sender_username = row[1]
                content = row[2]
                
                if len(content) > 50000 and "|" in content:
                    if content.startswith("[FILE]:") or content.startswith("[IMAGE]:"):
                        try:
                            header_part = content.split('|', 1)[0]
                            content = header_part + "|"
                        except: pass
                
                u_info = self.db.get_user_info(sender_username)
                display_name = sender_username
                avatar_b64 = ""
                
                if u_info:
                    display_name = u_info.get('fullname') or sender_username
                    avt_file = u_info.get('avatar') or ""
                    try:
                        avatar_b64 = self.server.get_avatar_base64(avt_file)
                    except: pass

                header = f"{sender_username}|{display_name}|{avatar_b64}"
                self.server.send_packet(conn, f"{Protocol.HISTORY}|{msg_id}|{header}:{content}")
            
            except Exception as e:
                print(f"[HISTORY SKIP] Error row {row[0]}: {e}")
                continue

        self.server.send_packet(conn, f"{Protocol.HISTORY}|BATCH_END")

    def handle_get_pending_files(self, conn, username):
        if not username:
            self.server.send_packet(conn, "PENDING_FILES|")
            return
        files = self.db.get_pending_file_transfers(username)
        if not files:
            self.server.send_packet(conn, "PENDING_FILES|")
            return
        parts = ["PENDING_FILES"]
        for f in files:
            parts.extend([
                str(f['fileid']), f['filename'], str(f['total_size']), 
                str(f['uploaded_bytes']), f['status'], f['file_path'] or ''
            ])
        self.server.send_packet(conn, "|".join(parts))

    # [NEW] XỬ LÝ LỆNH CANCEL TỪ CLIENT
    def handle_cancel_file(self, conn, parts, username):
        """
        Xóa file tạm trên server khi client bấm Hủy Upload
        Giao thức: CANCEL_FILE|filename
        """
        if len(parts) < 2: return
        
        # [SECURITY] Sanitize tên file
        filename = parts[1].replace("|", "_")
        
        print(f"🗑️ [CANCEL] User {username} requested cancel for {filename}")
        
        # 1. Tìm và xóa file tạm: temp_{username}_{filename}.part
        safe_filename = os.path.basename(filename)
        temp_filename = f"temp_{username}_{safe_filename}.part"
        temp_path = os.path.join(self.server.FILE_DIR, temp_filename)
        
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"✅ [CANCEL] Deleted temp file: {temp_filename}")
                self.server.send_packet(conn, f"System:Đã xóa file tạm {filename} trên server.")
            except Exception as e:
                print(f"⚠️ [CANCEL] Could not delete file: {e}")
        else:
            print(f"ℹ️ [CANCEL] Temp file not found: {temp_filename}")

    def handle_export_chat(self, conn, parts):
        if len(parts) < 2: return
        email_to = parts[1]
        if not self.server.is_valid_email(email_to):
            self.server.send_packet(conn, "System:Email không hợp lệ!")
            return
        
        try:
            history = self.db.get_recent_messages(100)
            log = "\n".join([f"[{r[3]}] {r[1]}: {r[2]}" for r in history])
            if self.server.send_email(email_to, "LanChat - Lịch sử Chat", log):
                self.server.send_packet(conn, "System:Đã gửi lịch sử chat!")
            else:
                self.server.send_packet(conn, "System:Không thể gửi email.")
        except:
            self.server.send_packet(conn, "System:Lỗi xuất file.")