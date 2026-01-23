from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from client.ui.components.chat_area import ChatArea
from client.ui.components.input_bar import InputBar
from client.ui.styles import GLOBAL_STYLES
from client.network.network_client import network_client
from common.protocol import CMD_MSG

class MainWindow(QMainWindow):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info # {user_id, display_name}
        self.setWindowTitle(f"ChatApp - {self.user_info['display_name']}")
        self.resize(1000, 700)
        self.setStyleSheet(GLOBAL_STYLES)

        # Layout chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 1. Khu vực Chat
        self.chat_area = ChatArea()
        self.layout.addWidget(self.chat_area)

        # 2. Thanh nhập liệu
        self.input_bar = InputBar()
        self.input_bar.send_message_signal.connect(self.handle_send_message)
        self.layout.addWidget(self.input_bar)

    def handle_send_message(self, content):
        """Xử lý khi user nhấn Gửi"""
        # Hiển thị ngay lên giao diện của mình
        self.chat_area.add_message("Tôi", content, is_me=True)
        
        # Gửi qua mạng
        # Lệnh: MSG|content
        network_client.send_packet(CMD_MSG, content)

    # Lưu ý: Logic nhận tin nhắn từ người khác sẽ được thêm ở Task tiếp theo
    # khi ta hoàn thiện ChatController