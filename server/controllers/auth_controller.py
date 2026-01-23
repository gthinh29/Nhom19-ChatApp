import bcrypt
from common.protocol import *

class AuthController:
    def __init__(self, db):
        self.db = db

    def login(self, client, payload):
        """Xử lý lệnh LOGIN|username|password"""
        try:
            if SEPARATOR not in payload:
                client.send(CMD_LOGIN, "ERROR|Sai định dạng")
                return

            username, password = payload.split(SEPARATOR, 1)
            
            # Tìm user trong DB
            user = self.db.fetch_one("SELECT user_id, password, display_name FROM users WHERE username = ?", (username,))
            
            if user:
                user_id, hashed_pw, display_name = user
                # Task 5: Kiểm tra mật khẩu bằng bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
                    client.username = username
                    client.user_id = user_id
                    client.send(CMD_LOGIN, f"OK|{user_id}|{display_name}")
                    print(f"[AUTH] User {username} logged in.")
                    return
            
            client.send(CMD_LOGIN, "ERROR|Sai tài khoản hoặc mật khẩu")
            
        except Exception as e:
            print(f"[LOGIN ERROR] {e}")
            client.send(CMD_LOGIN, "ERROR|Lỗi server")

    def register(self, client, payload):
        """Xử lý lệnh REGISTER|username|password"""
        try:
            if SEPARATOR not in payload:
                client.send(CMD_REGISTER, "ERROR|Sai định dạng")
                return

            username, password = payload.split(SEPARATOR, 1)
            
            # Task 5: Mã hóa mật khẩu trước khi lưu
            salt = bcrypt.gensalt(rounds=12)
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            try:
                self.db.execute_query("INSERT INTO users (username, password, display_name) VALUES (?, ?, ?)", 
                                      (username, hashed_pw, username))
                client.send(CMD_REGISTER, "OK|Đăng ký thành công")
                print(f"[AUTH] New user registered: {username}")
            except Exception:
                client.send(CMD_REGISTER, "ERROR|Tên đăng nhập đã tồn tại")
                
        except Exception as e:
            print(f"[REGISTER ERROR] {e}")
            client.send(CMD_REGISTER, "ERROR|Lỗi server")