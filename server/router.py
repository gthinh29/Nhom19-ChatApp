from common.protocol import *
from server.controllers.auth_controller import AuthController

class Router:
    def __init__(self, db):
        self.db = db
        self.auth_controller = AuthController(db)
        self.clients = [] # Danh sách các client đang kết nối

    def add_client(self, client):
        self.clients.append(client)

    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)

    def route(self, client, cmd, payload):
        """Điều hướng lệnh dựa trên cmd"""
        if cmd == CMD_LOGIN:
            self.auth_controller.login(client, payload)
        elif cmd == CMD_REGISTER:
            self.auth_controller.register(client, payload)
        # Các lệnh MSG, FILE sẽ thêm ở Giai đoạn 4
        else:
            print(f"[ROUTER] Lệnh chưa xử lý: {cmd}")