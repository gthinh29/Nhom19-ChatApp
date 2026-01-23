from common.protocol import *
import os
import base64

class ChatController:
    """
    Xử lý các lệnh liên quan đến tin nhắn và giao tiếp giữa các người dùng.
    """
    def __init__(self, db, router):
        self.db = db
        self.router = router
        # Tạo thư mục uploads nếu chưa có
        if not os.path.exists("server/uploads"):
            os.makedirs("server/uploads")

    def handle_msg(self, sender_client, payload):
        """Xử lý lệnh MSG|content"""
        sender_name = getattr(sender_client, 'username', 'Unknown')
        sender_id = getattr(sender_client, 'user_id', 0)
        
        # 1. Lưu vào Database
        try:
            self.db.execute_query(
                "INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                (sender_id, 0, payload)
            )
        except Exception as e:
            print(f"[DB ERROR] Save message failed: {e}")

        # 2. Broadcast cho tất cả clients
        broadcast_payload = f"{sender_name}{SEPARATOR}{payload}"
        
        for client in self.router.clients:
            if client.running:
                client.send(CMD_MSG, broadcast_payload)
        
        print(f"[CHAT] {sender_name}: {payload}")

    def handle_file(self, sender_client, payload):
        """
        Xử lý lệnh FILE (Task 3).
        Payload: TYPE|filename|...
        """
        try:
            parts = payload.split(SEPARATOR)
            action = parts[0] # INIT, CHUNK, END
            filename = parts[1]
            
            # Bảo mật: Lấy tên file gốc để tránh path traversal
            safe_filename = os.path.basename(filename) 
            file_path = os.path.join("server/uploads", safe_filename)

            if action == "INIT":
                # Xóa file cũ nếu trùng tên
                if os.path.exists(file_path):
                    os.remove(file_path)
                print(f"[FILE] Receiving {safe_filename}...")

            elif action == "CHUNK":
                # Format: CHUNK|filename|offset|data_b64
                data_b64 = parts[3]
                
                # Decode và ghi nối vào file (append mode)
                with open(file_path, "ab") as f:
                    f.write(base64.b64decode(data_b64))

            elif action == "END":
                print(f"[FILE] Upload complete: {safe_filename}")
                # Thông báo cho mọi người biết có file mới
                msg_content = f"Đã gửi một file: {safe_filename}"
                self.handle_msg(sender_client, msg_content)

        except Exception as e:
            print(f"[FILE ERROR] {e}")