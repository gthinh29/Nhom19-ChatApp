"""Quản lý xác thực người dùng."""

import base64
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from common.protocol import Protocol
from client.core.bus import SignalBus

class AuthTask(QThread):
    """Luồng xử lý nhiệm vụ xác thực mà không chặn UI"""
    
    result_signal = pyqtSignal(bool, str, str)  # (ok, msg, data)
    
    def __init__(self, client, task, *args):
        super().__init__()
        self.c = client       # NetworkClient instance
        self.t = task         # Loại nhiệm vụ (l=login, r=register, etc)
        self.a = args         # Tham số của nhiệm vụ

    def run(self):
        """Thực thi nhiệm vụ trong luồng riêng"""
        ok, msg, d = False, "Lỗi kết nối", ""
        try:
            # Gọi các hàm đồng bộ (blocking) của NetworkClient
            if self.t == "l":       # Login
                ok, msg, d = self.c.send_login(*self.a)
            elif self.t == "r":     # Register
                ok, msg = self.c.send_register(*self.a)
            elif self.t == "f":     # Forgot Password (OTP Request)
                ok, msg = self.c.send_forgot_request(*self.a)
            elif self.t == "rs":    # Reset Password (Confirm)
                ok, msg = self.c.send_confirm_reset(*self.a)
        except Exception as e: 
            msg = str(e)
        self.result_signal.emit(ok, msg, d)


class AuthManager(QObject):
    """Manager quản lý logic xác thực, thay thế AuthController"""

    def __init__(self, network_client):
        super().__init__()
        self.net = network_client
        self.bus = SignalBus.get()
        # Lưu username từ network client nếu có (thường là rỗng lúc đầu)
        self.username = network_client.username if hasattr(network_client, 'username') else None
        self.worker = None

        # ==================== INPUT SIGNALS (Lắng nghe từ UI) ====================
        
        # 1. Nhóm Pre-Login (Từ LoginDialog)
        if hasattr(self.bus, 'ui_request_login'):
            self.bus.ui_request_login.connect(self.login)
        if hasattr(self.bus, 'ui_request_register'):
            self.bus.ui_request_register.connect(self.register)
        if hasattr(self.bus, 'ui_forgot_request_otp'):
            self.bus.ui_forgot_request_otp.connect(self.request_forgot_otp)
        if hasattr(self.bus, 'ui_forgot_reset_pass'):
            self.bus.ui_forgot_reset_pass.connect(self.request_reset_pass)

        # 2. Nhóm Post-Login (Từ MainWindow/Sidebar)
        self.bus.ui_request_logout.connect(self.logout)
        self.bus.ui_update_profile.connect(self.send_update_profile)
        
        # [QUAN TRỌNG] Kết nối sự kiện Settings
        self.bus.ui_request_otp.connect(self.request_otp_change_pass) 
        self.bus.ui_change_password.connect(self.change_password_internal)
        self.bus.ui_export_chat.connect(self.request_export_chat)

        # 3. Lắng nghe gói tin thụ động từ Server
        self.bus.network_packet_received.connect(self.on_packet_received)

    # ==================== PUBLIC ACTIONS (Logic xử lý) ====================

    def _run_task(self, task_type, *args):
        """Helper chạy AuthTask"""
        self.worker = AuthTask(self.net, task_type, *args)
        self.worker.result_signal.connect(self._on_task_finished)
        self.worker.start()

    def login(self, username, password):
        self._run_task("l", username, password)
    
    def register(self, username, password, fullname, email):
        self._run_task("r", username, password, fullname, email)
    
    def request_forgot_otp(self, username, email):
        self._run_task("f", username, email)
    
    def request_reset_pass(self, username, otp, new_pass):
        self._run_task("rs", username, otp, new_pass)

    def logout(self):
        """Xử lý đăng xuất: Gửi lời chào tạm biệt trước khi ngắt"""
        # 1. Gửi gói tin LOGOUT
        if self.net.is_connected and self.username:
            try:
                self.net.send_packet(f"{Protocol.LOGOUT}|{self.username}")
            except: pass

        # 2. Ngắt kết nối socket an toàn
        try:
            self.net.disconnect() 
        except: pass

    # ==================== POST-LOGIN ACTIONS ====================

    def send_update_profile(self, name, avt_bytes):
        if not self.net.is_connected: return
        b64 = ""
        if avt_bytes:
            b64 = base64.b64encode(avt_bytes).decode('utf-8')
        # Gửi lệnh: UPDATE_PROFILE|Fullname|Base64Avatar
        self.net.send_packet(f"{Protocol.UPDATE_PROFILE}|{name}|{b64}")

    def request_otp_change_pass(self):
        """Yêu cầu OTP để đổi mật khẩu (khi đã đăng nhập)"""
        # Gửi lệnh lấy OTP (Dùng chung lệnh RESET_PASSWORD hoặc lệnh riêng tùy Server)
        # Giả sử Server hiểu lệnh RESET_PASSWORD là gửi OTP về email
        self.net.send_packet(Protocol.RESET_PASSWORD)

    def change_password_internal(self, otp, new_pass):
        """Đổi mật khẩu (khi đã đăng nhập)"""
        if hasattr(self.net, 'username'):
            self.net.send_packet(f"{Protocol.CONFIRM_RESET}|{self.net.username}|{otp}|{new_pass}")

    def request_export_chat(self, email):
        self.net.send_packet(f"{Protocol.EXPORT_CHAT}|{email}")

    # ==================== CALLBACKS & SIGNAL EMISSION ====================

    def _on_task_finished(self, ok, msg, data):
        """Nhận kết quả từ Thread và bắn Signal vào Bus"""
        task_type = self.worker.t
        
        if task_type == "l": # Login
            if ok:
                fullname = msg
                avatar = data
                
                # Cập nhật username vào manager
                if hasattr(self.net, 'username'):
                    self.username = self.net.username
                
                if hasattr(self.bus, 'core_auth_success'):
                    self.bus.core_auth_success.emit(fullname, avatar)
            else:
                if hasattr(self.bus, 'core_auth_failed'):
                    self.bus.core_auth_failed.emit(msg)

        elif task_type == "r": # Register
            if hasattr(self.bus, 'core_register_result'):
                self.bus.core_register_result.emit(ok, msg)

        elif task_type == "f": # Forgot OTP
            if hasattr(self.bus, 'core_forgot_result'):
                self.bus.core_forgot_result.emit(ok, msg, "otp_sent")

        elif task_type == "rs": # Reset Confirm
            if hasattr(self.bus, 'core_forgot_result'):
                self.bus.core_forgot_result.emit(ok, msg, "reset_done")

    def on_packet_received(self, d):
        """Xử lý các gói tin Auth thụ động từ Server"""
        t = d.get("type")
        content = d.get("content", "")
        
        # 1. Xử lý Force Logout (Bị đá)
        if t == "force_logout":
            reason = content if content else "Phiên đăng nhập hết hạn"
            try:
                self.net.disconnect()
            except: pass
            
            if hasattr(self.bus, 'auth_force_logout'):
                self.bus.auth_force_logout.emit(reason)

        # 2. [FIX] Xử lý thông báo OTP (cho trường hợp đổi pass bên trong)
        # Server gửi dạng: System: Mã OTP đã được gửi...
        elif t == "system":
            # Kiểm tra từ khóa: "OTP" và ("gửi" hoặc "sent")
            if "OTP" in content and ("gửi" in content or "sent" in content):
                if hasattr(self.bus, 'auth_otp_sent'):
                    self.bus.auth_otp_sent.emit()