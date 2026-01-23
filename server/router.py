from common.protocol import *
from server.controllers.auth_controller import AuthController
from server.controllers.chat_controller import ChatController
from datetime import datetime

class Router:
    def __init__(self, db):
        self.db = db
        self.clients = [] # Danh sách các client đang online
        
        # Khởi tạo các Controllers
        self.auth_controller = AuthController(db)
        self.chat_controller = ChatController(db, self)

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
        
        # Nhóm lệnh File (MỚI)
        elif cmd == CMD_FILE:
            self.chat_controller.handle_file(client, payload)
            
        # Nhóm lệnh System
        elif cmd == CMD_PING:
            client.send(CMD_PONG, "")
            if hasattr(client, 'last_heartbeat'):
                client.last_heartbeat = datetime.now()
            
        else:
            print(f"[ROUTER] Unknown command: {cmd}")