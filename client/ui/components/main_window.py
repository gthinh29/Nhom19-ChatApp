from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from client.ui.components.chat_area import ChatArea
from client.ui.components.input_bar import InputBar
from client.ui.styles import GLOBAL_STYLES
from client.network.network_client import network_client
from client.core.bus import bus # Import Bus
from common.protocol import CMD_MSG, SEPARATOR

class MainWindow(QMainWindow):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info 
        self.my_username = user_info.get("display_name", "Me") # Giả định server trả về username
        
        self.setWindowTitle(f"ChatApp - {self.my_username}")
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
        
        # --- Lắng nghe tin nhắn từ Server ---
        bus.message_received.connect(self.on_network_message)

    def handle_send_message(self, content):
        """Gửi tin đi"""
        # Lưu ý: Khi gửi đi, ta KHÔNG add vào UI ngay lập tức.
        # Ta chờ Server broadcast lại để đảm bảo tính đồng bộ (Server là Single Source of Truth).
        # Hoặc ta add ngay (Optimistic UI) nhưng phải xử lý logic duplicate.
        # Cách đơn giản nhất: Chờ server broadcast về.
        
        network_client.send_packet(CMD_MSG, content)

    def on_network_message(self, data):
        """Xử lý tin nhắn nhận được"""
        cmd, content = data
        if cmd == CMD_MSG:
            # Format: sender_name|content
            if SEPARATOR in content:
                sender, msg_text = content.split(SEPARATOR, 1)
                
                # Kiểm tra xem có phải tin của chính mình không
                # (Server broadcast lại cho cả người gửi)
                # Lưu ý: So sánh tên hiển thị không phải cách tốt nhất (nên dùng ID),
                # nhưng với Task đơn giản này ta tạm dùng tên.
                is_me = (sender == self.my_username) or (sender == network_client.client_socket.getsockname()) # Logic tạm
                
                # Thực tế ta nên so sánh username
                # Để chính xác, ở login_success server nên trả về username chuẩn.
                # Giả sử self.my_username chính xác.
                
                self.chat_area.add_message(sender, msg_text, is_me=(sender == self.my_username))