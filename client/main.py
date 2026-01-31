import sys
import os
import threading
import gc

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer

from client.network.network_client import NetworkClient
from client.core.bus import SignalBus

from client.managers.auth_manager import AuthManager
from client.managers.chat_manager import ChatManager
from client.managers.file_manager import FileManager
from client.managers.connection_manager import ConnectionManager

from client.ui.dialogs.login_dialog import LoginWindow
from client.ui.main_window import MainWindow

class ChatApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.aboutToQuit.connect(self._cleanup)
        default_font = QFont("Segoe UI", 10)
        self.app.setFont(default_font)
        self.bus = SignalBus.get()
        self.net_client = None
        self.auth_mgr = None
        self.chat_mgr = None
        self.file_mgr = None
        self.conn_mgr = None
        self.login_win = None
        self.main_win = None
        self.bus.core_auth_success.connect(self.on_login_success)
        self.bus.ui_request_logout.connect(self.on_logout)
        self.bus.network_connected.connect(self.on_network_connected)
        self.bus.network_disconnected.connect(self.on_network_disconnected)
        self.start_application()

    def start_application(self):
        self.net_client = NetworkClient()
        self.auth_mgr = AuthManager(self.net_client)
        self.chat_mgr = ChatManager(self.net_client)
        self.file_mgr = FileManager(self.net_client)
        self.conn_mgr = ConnectionManager(self.net_client)
        threading.Thread(target=self._initial_connect, daemon=True).start()
        if not self.login_win:
            self.login_win = LoginWindow()
        self.login_win.set_network_status(False)
        self.login_win.show()

    def _initial_connect(self):
        ok, msg = self.net_client.connect_server()
        if not ok:
            print(f"[Main] Initial Connect Failed: {msg}")

    def on_network_connected(self):
        if self.login_win:
            QTimer.singleShot(0, lambda: self.login_win.set_network_status(True))

    def on_network_disconnected(self):
        if self.login_win and self.login_win.isVisible():
            QTimer.singleShot(0, lambda: self.login_win.set_network_status(False))

    def on_login_success(self, fullname, avatar_b64):
        print(f"🚀 Login Success: {fullname}")
        if self.login_win:
            password = self.login_win.txt_pass.text().strip()
            self.conn_mgr.password = password
            self.login_win.hide()
        self.main_win = MainWindow(self.net_client.username, fullname, avatar_b64)
        self.main_win.show()
        self.net_client.start_receiver()
        try:
            self.bus.ui_request_history.emit(0)
            self.bus.ui_request_pending_files.emit()
        except Exception:
            pass

    def on_logout(self):
        print("🚪 Logout requested...")
        if self.login_win:
            self.login_win.reset_state()
            self.login_win.show()
        if self.main_win:
            self.main_win.close()
            self.main_win.deleteLater()
            self.main_win = None
        self._cleanup()
        self.start_application()

    def _cleanup(self):
        print("🧹 Cleaning up application...")
        try:
            if self.file_mgr:
                self.file_mgr.shutdown()
        except: pass
        if self.net_client:
            try:
                self.net_client.disconnect()
            except: pass
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