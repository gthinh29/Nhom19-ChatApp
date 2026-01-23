# client/ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget
from client.ui.components.chat_area import ChatArea
from client.ui.components.input_bar import InputBar
from client.ui.components.sidebar import Sidebar  # Import mới
from client.ui.styles import GLOBAL_STYLES
from client.network.network_client import network_client
from client.core.bus import bus 
from common.protocol import CMD_MSG, SEPARATOR

class MainWindow(QMainWindow):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info 
        self.my_username = user_info.get("display_name", "Me")
        
        self.setWindowTitle(f"ChatApp - {self.my_username}")
        self.resize(1200, 800) # Tăng kích thước mặc định
        self.setStyleSheet(GLOBAL_STYLES)

        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout ngang (Sidebar | Chat Area)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar (Trái)
        self.sidebar = Sidebar()
        self.sidebar.set_user_info(self.my_username)
        main_layout.addWidget(self.sidebar)

        # 2. Main Content (Phải)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Chat Area
        self.chat_area = ChatArea()
        content_layout.addWidget(self.chat_area)

        # Input Bar
        self.input_bar = InputBar()
        self.input_bar.send_message_signal.connect(self.handle_send_message)
        content_layout.addWidget(self.input_bar)
        
        main_layout.addWidget(content_widget)
        
        # --- Lắng nghe tin nhắn ---
        bus.message_received.connect(self.on_network_message)

    def handle_send_message(self, content):
        """Gửi tin đi"""
        network_client.send_packet(CMD_MSG, content)

    def on_network_message(self, data):
        """Xử lý tin nhắn nhận được"""
        cmd, content = data
        if cmd == CMD_MSG:
            if SEPARATOR in content:
                sender, msg_text = content.split(SEPARATOR, 1)
                is_me = (sender == self.my_username)
                self.chat_area.add_message(sender, msg_text, is_me=is_me)