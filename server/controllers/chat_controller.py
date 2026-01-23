from common.protocol import *
import json
from datetime import datetime

class ChatController:
    """
    Xử lý các lệnh liên quan đến tin nhắn và giao tiếp giữa các người dùng.
    """
    def __init__(self, db, router):
        self.db = db
        self.router = router

    def handle_msg(self, sender_client, payload):
        """
        Xử lý lệnh MSG|content
        Mặc định mô hình này là Global Chat (Chat nhóm chung).
        """
        message_content = payload
        sender_id = getattr(sender_client, 'user_id', None)
        sender_name = getattr(sender_client, 'username', 'Unknown')

        if not sender_id:
            return # Chưa đăng nhập thì không được chat

        # 1. Lưu vào Database (Global chat: receiver_id = 0 hoặc NULL)
        try:
            self.db.execute_query(
                "INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                (sender_id, 0, message_content)
            )
        except Exception as e:
            print(f"[DB ERROR] Save message failed: {e}")

        # 2. Broadcast cho tất cả clients đang kết nối
        # Format gửi xuống client: MSG|sender_name|content
        broadcast_payload = f"{sender_name}{SEPARATOR}{message_content}"
        
        # Danh sách client từ Router
        for client in self.router.clients:
            # Gửi cho tất cả (bao gồm cả người gửi để xác nhận, hoặc lọc ra tùy logic UI)
            # Ở đây ta gửi hết, UI sẽ tự lọc nếu cần.
            if client.running:
                client.send(CMD_MSG, broadcast_payload)
        
        print(f"[CHAT] {sender_name}: {message_content}")