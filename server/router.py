

from common.protocol import Protocol
from server.controllers.auth_controller import AuthController
from server.controllers.chat_controller import ChatController

class Router:
    """Bộ định tuyến xử lý các yêu cầu từ client"""
    
    def __init__(self, server_context):
        """Khởi tạo các controller xử lý"""
        self.auth_ctrl = AuthController(server_context)
        self.chat_ctrl = ChatController(server_context)

    def dispatch(self, conn, cmd, parts, current_user):
        """
        Nhận lệnh từ client và chuyển tới controller thích hợp
        
        Tham số:
        - conn: Connection socket của client
        - cmd: Tên lệnh (từ Protocol)
        - parts: Dữ liệu kèm theo, được tách bằng delimiter
        - current_user: Username của client hiện tại
        """
        
        # ==================== NHÓM LỆNH XÁC THỰC ====================
        if cmd == Protocol.LOGIN:
            self.auth_ctrl.handle_login(conn, parts)
        
        elif cmd == Protocol.REGISTER:
            self.auth_ctrl.handle_register(conn, parts)
            
        elif cmd == Protocol.FORGOT_PW:
            self.auth_ctrl.handle_forgot_password(conn, parts)
            
        elif cmd == Protocol.RESET_PASSWORD:
            self.auth_ctrl.handle_reset_request_logged_in(conn, current_user)
            
        elif cmd == Protocol.CONFIRM_RESET:
            self.auth_ctrl.handle_confirm_reset(conn, parts)
            
        elif cmd == Protocol.UPDATE_PROFILE:
            self.auth_ctrl.handle_update_profile(conn, parts, current_user)

        # ==================== NHÓM LỆNH CHAT ====================
        elif cmd == Protocol.MSG:
            self.chat_ctrl.handle_message(conn, parts)
            
        elif cmd == Protocol.IMAGE:
            self.chat_ctrl.handle_image(conn, parts)
        
        # Xử lý yêu cầu Upload File (Gửi từ Chat Socket)
        elif cmd == Protocol.UPLOAD_REQ:
            self.chat_ctrl.handle_upload_request(conn, parts, current_user)

        # Xử lý yêu cầu Download File (Gửi từ Chat Socket)
        elif cmd == Protocol.DOWNLOAD_REQ:
            self.chat_ctrl.handle_download_request(conn, parts, current_user)

        # Lệnh FILE cũ (không dùng nữa)
        elif cmd == Protocol.FILE:
            self.chat_ctrl.handle_file(conn, parts)
            
        elif cmd == Protocol.GET_PENDING_FILES:
            self.chat_ctrl.handle_get_pending_files(conn, current_user)
            
        elif cmd == Protocol.CANCEL_FILE:
            self.chat_ctrl.handle_cancel_file(conn, parts, current_user)
            
        elif cmd == Protocol.EXPORT_CHAT:
            self.chat_ctrl.handle_export_chat(conn, parts)

        elif cmd == Protocol.HISTORY:
            self.chat_ctrl.handle_history(conn, parts)
            
        else:
            print(f"⚠️ Lệnh không xác định: {cmd}")