"""Khởi tạo ứng dụng chat và khởi chạy UI chính."""

import sys
import os
import threading
import gc

# Thiết lập đường dẫn import
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer

# Import các thành phần kiến trúc mới
from client.network.network_client import NetworkClient
from client.core.bus import SignalBus

# Managers (Logic)
from client.managers.auth_manager import AuthManager
from client.managers.chat_manager import ChatManager
from client.managers.file_manager import FileManager
from client.managers.connection_manager import ConnectionManager

# UI
from client.ui.dialogs.login_dialog import LoginWindow
from client.ui.main_window import MainWindow

class ChatApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # Use default QApplication behavior for quitting when last window closes
        
        # Đăng ký sự kiện dọn dẹp khi App chuẩn bị thoát (Bấm X)
        self.app.aboutToQuit.connect(self._cleanup)

        # Thiết lập font mặc định
        default_font = QFont("Segoe UI", 10)
        self.app.setFont(default_font)
        
        self.bus = SignalBus.get()
        
        # Biến lưu trữ trạng thái
        self.net_client = None
        self.auth_mgr = None
        self.chat_mgr = None
        self.file_mgr = None
        self.conn_mgr = None
        
        self.login_win = None
        self.main_win = None
        
        # Kết nối các Signal Flow chính
        self.bus.core_auth_success.connect(self.on_login_success)
        self.bus.ui_request_logout.connect(self.on_logout)
        
        # [NEW] Lắng nghe trạng thái mạng để Update nút Login
        self.bus.network_connected.connect(self.on_network_connected)
        self.bus.network_disconnected.connect(self.on_network_disconnected)
        
        # Bắt đầu
        self.start_application()

    def start_application(self):
        """Khởi tạo toàn bộ hệ thống"""
        # 1. Init Network Layer
        self.net_client = NetworkClient()
        
        # 2. Init Logic Layer (Managers)
        self.auth_mgr = AuthManager(self.net_client)
        self.chat_mgr = ChatManager(self.net_client)
        self.file_mgr = FileManager(self.net_client)
        self.conn_mgr = ConnectionManager(self.net_client)
        
        # 3. Kết nối Socket (Chạy ngầm)
        threading.Thread(target=self._initial_connect, daemon=True).start()
        
        # 4. Hiển thị màn hình Login
        if not self.login_win:
            self.login_win = LoginWindow()
        
        # [NEW] Mặc định disable nút khi mới mở (chờ kết nối)
        self.login_win.set_network_status(False)
        self.login_win.show()

    def _initial_connect(self):
        """Thử kết nối server lần đầu"""
        ok, msg = self.net_client.connect_server()
        if not ok:
            print(f"[Main] Initial Connect Failed: {msg}")

    # ==================== HANDLERS SỰ KIỆN MẠNG ====================
    def on_network_connected(self):
        """Khi kết nối thành công -> Mở khóa nút Login"""
        if self.login_win:
            # Dùng QTimer để đảm bảo chạy trên luồng UI chính
            QTimer.singleShot(0, lambda: self.login_win.set_network_status(True))

    def on_network_disconnected(self):
        """Khi mất kết nối -> Khóa nút Login"""
        if self.login_win and self.login_win.isVisible():
            QTimer.singleShot(0, lambda: self.login_win.set_network_status(False))

    # ==================== HANDLERS LOGIC ====================
    def on_login_success(self, fullname, avatar_b64):
        """Chuyển từ Login sang Main Window"""
        print(f" Login Success: {fullname}")
        
        # Ẩn Login thay vì Close
        if self.login_win:
            # Lưu password để reconnect nếu cần
            password = self.login_win.txt_pass.text().strip()
            self.conn_mgr.password = password
            self.login_win.hide() 
        
        # Khởi tạo Main Window
        self.main_win = MainWindow(self.net_client.username, fullname, avatar_b64)
        self.main_win.show()
        
        # Kích hoạt luồng nhận tin nhắn
        self.net_client.start_receiver()
        # Yêu cầu tải lịch sử sau khi receiver đã sẵn sàng (tránh race với server gửi lịch sử ngay khi login)
        try:
            # Emitting 0 will request the latest messages (server treats 0 as no filter)
            self.bus.ui_request_history.emit(0)
            # Yêu cầu server trả về danh sách file đang resume (nếu có)
            self.bus.ui_request_pending_files.emit()
        except Exception:
            pass

    def on_logout(self):
        """Xử lý đăng xuất"""
        print(" Logout requested...")
        
        # 1. Hiện lại Login ngay lập tức
        if self.login_win:
            self.login_win.reset_state()
            self.login_win.show()
            
        # 2. Đóng Main Window ngay lập tức
        if self.main_win:
            self.main_win.close()
            self.main_win.deleteLater()
            self.main_win = None
        
        # 3. Cleanup và Restart ngay
        # (Server sẽ tự đá phiên cũ nếu user đăng nhập lại ngay, không cần delay ở client)
        self._cleanup()
        self.start_application()

    def _cleanup(self):
        """Dọn dẹp tài nguyên"""
        print(" Cleaning up application...")
        # Shutdown managers gracefully
        try:
            if self.file_mgr:
                self.file_mgr.shutdown()
        except: pass

        if self.net_client:
            # [QUAN TRỌNG] Ngắt kết nối để phá vỡ vòng lặp recv()
            try:
                self.net_client.disconnect()
            except: pass
        
        # Xóa references
        self.auth_mgr = None
        self.chat_mgr = None
        self.file_mgr = None
        self.conn_mgr = None
        self.net_client = None
        
        gc.collect()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    try:
        client_app = ChatApp()
        client_app.run()
    except KeyboardInterrupt:
        sys.exit(0)