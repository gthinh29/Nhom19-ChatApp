from common.protocol import *
from server.controllers.auth_controller import AuthController
# Import controller mới
from server.controllers.chat_controller import ChatController

class Router:
    def __init__(self, db):
        self.db = db
        self.clients = [] # Danh sách các client đang online
        
        # Khởi tạo các Controllers
        self.auth_controller = AuthController(db)
        self.chat_controller = ChatController(db, self) # Truyền self để ChatController có thể access danh sách clients

    def add_client(self, client):
        if client not in self.clients:
            self.clients.append(client)

    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)

    def route(self, client, cmd, payload):
        """Điều hướng lệnh tới Controller phù hợp"""
        # Nhóm lệnh Authentication
        if cmd == CMD_LOGIN:
            self.auth_controller.login(client, payload)
        elif cmd == CMD_REGISTER:
            self.auth_controller.register(client, payload)
            
        # Nhóm lệnh Chat
        elif cmd == CMD_MSG:
            self.chat_controller.handle_msg(client, payload)
            
        # Nhóm lệnh System (Ping/Pong) - Sẽ làm rõ ở Commit 12
        elif cmd == CMD_PING:
            client.send(CMD_PONG, "")
            # Cập nhật thời gian hoạt động cuối cùng (nếu có logic timeout)
            client.last_heartbeat = datetime.now() if hasattr(client, 'last_heartbeat') else None
            
        else:
            print(f"[ROUTER] Unknown command: {cmd}")

# Cần import datetime để dùng cho heartbeat sau này
from datetime import datetime