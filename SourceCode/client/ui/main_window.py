"""
Main Window - Khung sườn lắp ráp các thành phần giao diện
[FINAL FIX] 
- Xóa dòng gây lỗi AttributeError (set_current_user_id).
- Tính toán 'is_me' thủ công tại đây để ChatArea hiển thị đúng bên phải.
"""
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox, QFileDialog, QApplication
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QTimer
import os

from client.core.bus import SignalBus
from client.ui.styles import GLOBAL_STYLE
from client.ui.components.sidebar import Sidebar
from client.ui.components.chat_area import ChatArea
from client.ui.components.input_bar import InputBar
from client.ui.dialogs.settings_dialog import SettingsWindow
from client.ui.widgets import ToastNotification

class MainWindow(QMainWindow):
    def __init__(self, username, fullname, avatar_b64):
        super().__init__()
        self.username = username
        self.fullname = fullname if fullname else username
        
        self.avatar_b64 = avatar_b64 
        self.bus = SignalBus.get()
        
        self.settings_dlg = None
        self.history_done = False
        self.loading_history = False
        self.oldest_msg_id = None
        self.history_buffer = []

        self.setWindowTitle(f"LAN Chat - {self.fullname}")
        self.resize(1200, 800)
        self.setStyleSheet(GLOBAL_STYLE)
        
        self.init_ui()
        self.connect_signals()
        
        if self.avatar_b64:
            self.sidebar.update_self_profile(self.fullname, self.avatar_b64)
            self.chat_area.update_avatar_cache(self.fullname, self.avatar_b64)
            self.chat_area.my_avatar_b64 = self.avatar_b64
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # 1. Sidebar
        self.sidebar = Sidebar(self.username, self.fullname)
        main_layout.addWidget(self.sidebar)

        # 2. Right Area
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(0)
        
        self.chat_area = ChatArea()
        
        # [REMOVED] Đã xóa dòng set_current_user_id gây lỗi
        # self.chat_area.set_current_user_id(self.username)
        
        self.chat_area.my_avatar_b64 = self.avatar_b64
        
        self.input_bar = InputBar()
        
        right_layout.addWidget(self.chat_area)
        right_layout.addWidget(self.input_bar)
        main_layout.addWidget(right_container)

    def connect_signals(self):
        # UI -> Logic
        self.sidebar.logout_requested.connect(lambda: self.bus.ui_request_logout.emit())
        self.sidebar.settings_requested.connect(self.open_settings)
        
        self.bus.ui_send_text.connect(self.on_me_sent_text)
        
        self.input_bar.image_btn.clicked.connect(self.on_btn_image_click)
        self.input_bar.file_btn.clicked.connect(self.on_btn_file_click)
        
        # Logic -> UI
        self.bus.network_disconnected.connect(self.on_network_lost)
        self.bus.network_connected.connect(self.on_network_restored)
        self.bus.auth_force_logout.connect(self.on_force_logout)
        
        # Data Flow
        self.bus.network_packet_received.connect(self.dispatch_packet)
        self.bus.file_upload_done.connect(self.on_file_upload_done)
        self.bus.auth_otp_sent.connect(self.on_otp_sent)

        self.chat_area.request_history_callback = self.request_more_history

    # ==================== HANDLERS ====================
    
    def on_file_upload_done(self, msg):
        try:
            if self.isVisible():
                self.show_toast(msg)
        except RuntimeError:
            pass

    def closeEvent(self, event):
        try:
            try: self.bus.network_packet_received.disconnect(self.dispatch_packet)
            except: pass
        except Exception:
            pass
        try:
            super().closeEvent(event)
        except KeyboardInterrupt:
            pass

        try:
            any_visible = any(w.isVisible() for w in QApplication.topLevelWidgets())
            if not any_visible:
                QApplication.quit()
        except Exception:
            pass

    def on_me_sent_text(self, text):
        msg_data = {
            "is_me": True,
            "sender": self.fullname,
            "sender_id": self.username,
            "type": "text",
            "content": text,
            "avatar_data": self.avatar_b64
        }
        self.chat_area.add_bubble(msg_data)

    def on_btn_image_click(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn Ảnh", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            qimg = QImage(file_path)
            if not qimg.isNull():
                msg_data = {
                    "is_me": True,
                    "sender": self.fullname,
                    "type": "image",
                    "qimage": qimg,
                    "avatar_data": self.avatar_b64
                }
                self.chat_area.add_bubble(msg_data)
            self.bus.ui_send_image.emit(file_path)

    def on_btn_file_click(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn File", "", "All Files (*.*)")
        if file_path:
            filename = os.path.basename(file_path)
            lower = filename.lower()
            
            if lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                qimg = QImage(file_path)
                if not qimg.isNull():
                    msg_data = {
                        "is_me": True, 
                        "sender": self.fullname, 
                        "type": "image", 
                        "qimage": qimg, 
                        "avatar_data": self.avatar_b64
                    }
                    self.chat_area.add_bubble(msg_data)
                    self.bus.ui_send_image.emit(file_path) 
                    return

            self.bus.ui_send_file.emit(file_path)

    def dispatch_packet(self, d):
        t = d.get("type")
        
        if t == "system":
            content = d.get("content", "")
            if "OTP" in content and ("gửi" in content or "sent" in content):
                return 
            self.show_toast(content)
        
        elif t == "online_list":
            self.sidebar.set_online_list(d.get("users", []))
            
        elif t == "user_status":
            joined = self.sidebar.update_user_status(d.get("status"), d.get("username"), d.get("fullname"))
            if joined: self.show_toast(f"{d.get('fullname')} đã tham gia!")
            elif d.get("status") == "LEAVE": self.show_toast(f"{d.get('fullname')} đã thoát.", True)

        elif t == "history":
            msg_id = d.get("msg_id")
            if msg_id is not None:
                self.oldest_msg_id = msg_id if self.oldest_msg_id is None else min(self.oldest_msg_id, msg_id)
            
            # [FIX] Logic nhận diện 'is_me' cho lịch sử
            sender_id = d.get('sender_id')
            if sender_id: 
                d['is_me'] = (str(sender_id) == str(self.username))
            else:
                # Fallback nếu server cũ không gửi sender_id
                d['is_me'] = (d.get('sender') == self.username) or (d.get('sender') == self.fullname)

            self.history_buffer.append(d)

        elif t == "history_end":
            self.loading_history = False
            self.history_done = True
            self.chat_area.show_loading(True, "--- Hết tin nhắn ---")

        elif t == "history_batch_end":
            self.loading_history = False
            for msg in reversed(self.history_buffer):
                self._enrich_and_add(msg, is_history=True)
            self.history_buffer.clear()
            self.chat_area.show_loading(False)
            try:
                self.bus.core_history_loaded.emit()
            except: pass

        elif t == "profile_update":
            name = d.get('fullname')
            avt = d.get('avatar')
            self.chat_area.update_avatar_cache(name, avt)
            if name == self.fullname: 
                self.on_profile_updated_local(name, avt)
            else:
                self.show_toast(f"Hồ sơ của {name} đã cập nhật!")

        # [FIX] Xử lý tin nhắn realtime (Text/File/Image)
        if d.get('is_message_packet') or t in ["text", "image", "file"]:
             sender_id = d.get('sender_id')
             
             # Kiểm tra kỹ ID người gửi
             if str(sender_id) == str(self.username):
                 d['is_me'] = True  # ÉP BUỘC là tôi
             else:
                 d['is_me'] = False
             
             self._enrich_and_add(d, is_history=False)

    def _enrich_and_add(self, data, is_history):
        sender = data.get('sender')
        avt_data = data.get('avatar_data')
        if sender and avt_data:
            self.chat_area.update_avatar_cache(sender, avt_data)
        
        if is_history:
            self.chat_area.add_history_bubble(data)
        else:
            self.chat_area.add_bubble(data)

    def request_more_history(self):
        if not self.history_done and not self.loading_history and self.oldest_msg_id is not None:
            self.loading_history = True
            self.chat_area.show_loading(True)
            self.bus.ui_request_history.emit(self.oldest_msg_id)

    def open_settings(self):
        if self.settings_dlg is None:
            self.settings_dlg = SettingsWindow(None, self.fullname, None, self.avatar_b64)
            self.settings_dlg.profile_updated.connect(self.on_profile_updated_local)
            self.settings_dlg.finished.connect(lambda: setattr(self, 'settings_dlg', None))
            self.settings_dlg.show()
        else: self.settings_dlg.raise_()

    def on_profile_updated_local(self, name, avt):
        self.fullname = name
        if avt: self.avatar_b64 = avt
        self.sidebar.update_self_profile(name, self.avatar_b64)
        self.chat_area.my_avatar_b64 = self.avatar_b64
        self.chat_area.update_avatar_cache(name, self.avatar_b64)
        self.show_toast("Cập nhật hồ sơ thành công!")

    def on_otp_sent(self):
        self.show_toast("✅ Mã OTP đã được gửi đến Email của bạn!")
        if self.settings_dlg and self.settings_dlg.isVisible():
            self.settings_dlg.enable_otp_inputs()

    def on_network_lost(self):
        self.chat_area.set_connection_lost(True)
        self.input_bar.set_enabled_input(False)
        self.show_toast("Mất kết nối server!", True)

    def on_network_restored(self):
        self.chat_area.set_connection_lost(False)
        self.input_bar.set_enabled_input(True)
        self.show_toast("Đã kết nối lại!")

    def on_force_logout(self, reason):
        QMessageBox.critical(self, "Đăng xuất", reason)
        if self.settings_dlg: self.settings_dlg.close()
        self.close()
        self.bus.ui_request_logout.emit() 

    def show_toast(self, msg, err=False):
        try:
            ToastNotification(self, msg, err)
        except RuntimeError:
            pass