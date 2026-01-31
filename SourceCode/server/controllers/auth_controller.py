"""Controller quản lý xác thực và cập nhật profile người dùng."""

import time
import os
import base64
import random
import string
import threading
import io
from PIL import Image
from common.protocol import Protocol

class AuthController:
    """Controller quản lý các yêu cầu liên quan đến xác thực người dùng"""
    
    def __init__(self, server_context):
        """Khởi tạo với context server và database"""
        self.server = server_context
        self.db = server_context.db

    def _send_email_async(self, to_email, subject, body):
        """Gửi email không đồng bộ (trong luồng riêng) để không chặn server"""
        def task():
            self.server.send_email(to_email, subject, body)
        threading.Thread(target=task, daemon=True).start()

    def handle_login(self, conn, parts):
        """Xử lý đăng nhập và đẩy session cũ"""
        if len(parts) < 3: return
        u, p = parts[1], parts[2]
        
        user_data = self.db.login_user(u, p)
        if user_data:
            # Đẩy session cũ ra (nếu có)
            try:
                existing = self.server.user_sessions.get(u, set())
                old_conns = [c for c in existing if c is not conn]
            except Exception:
                old_conns = [c for c, username in self.server.clients.items() if username == u and c is not conn]
            
            for old_conn in old_conns:
                try:
                    self.server.send_packet(old_conn, f"{Protocol.FORCE_LOGOUT}|Tài khoản đăng nhập từ nơi khác.")
                    time.sleep(0.1)
                    self.server.disconnect_client(old_conn)
                except: pass

            current_user = u
            db_fullname = user_data[1]
            current_fullname = db_fullname if (db_fullname and len(db_fullname) < 50) else u
            
            self.server.clients[conn] = u
            self.server.online_map[conn] = (u, current_fullname)
            
            try:
                if u not in self.server.user_sessions: self.server.user_sessions[u] = set()
                self.server.user_sessions[u].add(conn)
            except: pass
            
            # Lấy avatar
            avatar_file = user_data[3]
            avt_b64 = self.server.get_avatar_base64(avatar_file)
            
            # Gửi phản hồi thành công
            self.server.send_packet(conn, f"{Protocol.SUCCESS}|{current_fullname}|{avt_b64}")
            
            # Gửi danh sách online
            online_users_flat = []
            try:
                for uname in list(self.server.user_sessions.keys()):
                    display = uname
                    for c, (onl_u, onl_f) in self.server.online_map.items():
                        if onl_u == uname: display = onl_f; break
                    online_users_flat.extend([uname, display])
            except: pass
            
            self.server.send_packet(conn, f"{Protocol.ONLINE_LIST}|" + "|".join(online_users_flat))
            
            # Thông báo user mới tham gia
            self.server.broadcast(f"{Protocol.USER_STATUS}|JOIN|{current_user}|{current_fullname}", sender_conn=conn)

            time.sleep(0.5)
            self.server.send_packet(conn, f"System:Chào mừng {current_fullname}!")
            
            # Gửi lịch sử chat
            self._send_chat_history(conn)
        else:
            self.server.send_packet(conn, f"{Protocol.ERROR}|Sai thông tin đăng nhập")

    def _send_chat_history(self, conn):
        limit = getattr(self.server, "HISTORY_LIMIT", 100)
        history = self.db.get_recent_messages(limit=limit)
        
        if not history:
            self.server.send_packet(conn, f"{Protocol.HISTORY}|END")
            return

        history_list = list(history)[::-1]
        for msg_id, sender, content, timestamp, msg_type in history_list:
            username = None
            display_name = sender
            avatar_b64 = ""

            if "|" in sender:
                username, display_name = sender.split("|", 1)

            if username:
                u_info = self.db.get_user_info(username)
                if u_info:
                    display_name = u_info['fullname'] if u_info['fullname'] else display_name
                    avatar_b64 = self.server.get_avatar_base64(u_info['avatar'])

            header = f"{username}|{display_name}|{avatar_b64}" if username else f"{display_name}|{display_name}|{avatar_b64}"
            self.server.send_packet(conn, f"{Protocol.HISTORY}|{msg_id}|{header}:{content}")

        self.server.send_packet(conn, f"{Protocol.HISTORY}|BATCH_END")

    def handle_register(self, conn, parts):
        if len(parts) < 5: return
        u, p, n, e = parts[1], parts[2], parts[3], parts[4]
        
        if not self.server.is_valid_email(e):
            self.server.send_packet(conn, f"{Protocol.ERROR}|Email không hợp lệ!")
        elif self.db.register_user(u, p, n, e):
            self.server.send_packet(conn, f"{Protocol.SUCCESS}|Tạo tài khoản thành công")
        else:
            self.server.send_packet(conn, f"{Protocol.ERROR}|Tên đăng nhập đã tồn tại")

    def handle_forgot_password(self, conn, parts):
        if len(parts) < 3: return
        u, e = parts[1], parts[2]
        if self.db.check_user_email(u, e):
            otp = ''.join(random.choices(string.digits, k=6))
            self.server.otps[u] = otp
            self._send_email_async(e, "LanChat - Khôi phục mật khẩu", f"Mã OTP của bạn: {otp}")
            self.server.send_packet(conn, f"{Protocol.SUCCESS}|Mã OTP đang được gửi...")
        else:
            self.server.send_packet(conn, f"{Protocol.ERROR}|Username và Email không khớp")

    def handle_reset_request_logged_in(self, conn, current_user):
        if not current_user: return
        info = self.db.get_user_info(current_user)
        if info and info['email']:
            otp = ''.join(random.choices(string.digits, k=6))
            self.server.otps[current_user] = otp
            self._send_email_async(info['email'], "LanChat - Xác nhận đổi mật khẩu", f"Mã xác nhận: {otp}")
            self.server.send_packet(conn, f"{Protocol.SUCCESS}|Mã OTP đang được gửi...")
        else:
            self.server.send_packet(conn, f"{Protocol.ERROR}|Tài khoản chưa có Email")

    def handle_confirm_reset(self, conn, parts):
        if len(parts) < 4: return
        u, code, new_pw = parts[1], parts[2], parts[3]
        if u in self.server.otps and self.server.otps[u] == code:
            self.db.update_password(u, new_pw)
            del self.server.otps[u]
            self.server.send_packet(conn, f"{Protocol.SUCCESS}|Đổi mật khẩu thành công!")
        else:
            self.server.send_packet(conn, f"{Protocol.ERROR}|Mã xác nhận không chính xác")

    def handle_update_profile(self, conn, parts, current_user):
        """Xử lý cập nhật profile: Lưu ảnh vào thư mục avatars và xóa ảnh cũ"""
        if not current_user or len(parts) < 2: return
        
        new_fullname = parts[1].replace("|", "")[:50]
        avt_data = parts[2] if len(parts) > 2 else ""
        
        avt_filename = None
        final_avt_b64 = ""

        # Xử lý ảnh avatar nếu có gửi lên
        if avt_data:
            # 1. TÌM VÀ XÓA AVATAR CŨ (Dọn dẹp rác)
            old_info = self.db.get_user_info(current_user)
            if old_info and old_info.get('avatar'):
                old_file = old_info.get('avatar')
                # Đường dẫn thư mục avatars
                avatars_dir = os.path.join(self.server.UPLOAD_DIR, "avatars")
                old_path = os.path.join(avatars_dir, old_file)
                
                # Kiểm tra và xóa
                if os.path.exists(old_path) and os.path.isfile(old_path):
                    try:
                        os.remove(old_path)
                        print(f" [PROFILE] Đã xóa avatar cũ: {old_file}")
                    except Exception as e:
                        print(f" [PROFILE] Lỗi xóa avatar cũ: {e}")

            # 2. LƯU AVATAR MỚI
            try:
                raw_img_data = base64.b64decode(avt_data)
                image_stream = io.BytesIO(raw_img_data)
                img = Image.open(image_stream)
                img = img.convert("RGBA")
                
                # Mã hóa ảnh sang Base64 để gửi về client hiển thị ngay
                buffer_mem = io.BytesIO()
                img.save(buffer_mem, format="PNG", optimize=True)
                final_avt_b64 = base64.b64encode(buffer_mem.getvalue()).decode('utf-8')

                # Tạo tên file mới
                safe_u = "".join(c for c in current_user if c.isalnum())
                avt_filename = f"{safe_u}_{int(time.time())}.png"
                
                # Lưu vào thư mục avatars
                avatars_dir = os.path.join(self.server.UPLOAD_DIR, "avatars")
                if not os.path.exists(avatars_dir):
                    os.makedirs(avatars_dir)
                
                save_path = os.path.join(avatars_dir, avt_filename)
                img.save(save_path, format="PNG", optimize=True)
                
            except Exception as e: 
                print(f" Lỗi upload/xử lý ảnh: {e}")
                self.server.send_packet(conn, f"{Protocol.ERROR}|File ảnh không hợp lệ hoặc bị lỗi.")
                return

        # Cập nhật thông tin vào database
        if self.db.update_user_info(current_user, new_fullname, avt_filename):
            self.server.online_map[conn] = (current_user, new_fullname)
            
            # Nếu chỉ đổi tên, lấy lại avatar cũ để gửi kèm
            if not final_avt_b64:
                u_info = self.db.get_user_info(current_user)
                final_avt_b64 = self.server.get_avatar_base64(u_info['avatar'] if u_info else "")

            # Gửi xác nhận cho chính người đổi
            self.server.send_packet(conn, f"UPDATE_OK|{new_fullname}|{final_avt_b64}")
            
            # Broadcast cập nhật profile cho tất cả user: profile_update|username|fullname|avatar_b64
            self.server.broadcast(f"profile_update|{current_user}|{new_fullname}|{final_avt_b64}")
        else:
            self.server.send_packet(conn, f"{Protocol.ERROR}|Lỗi cập nhật CSDL")