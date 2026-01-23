from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt
from client.ui.styles import COLORS
from client.ui.widgets.bubbles import MessageBubble

class ChatArea(QScrollArea):
    """
    Khu vực cuộn chứa các bong bóng chat.
    """
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet(f"background-color: {COLORS['CHAT_BG']}; border: none;")
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self.setWidget(self.container)

    def add_message(self, sender, content, is_me=False):
        """
        Thêm tin nhắn mới vào giao diện.
        Tự động nhận diện nếu content là ảnh (theo quy ước tạm thời).
        """
        is_image = False
        display_content = content
        
        # Quy ước: Nếu tin nhắn bắt đầu bằng [IMAGE] thì phần sau là Base64
        if content.startswith("[IMAGE]"):
            is_image = True
            display_content = content.replace("[IMAGE]", "") 

        bubble = MessageBubble(sender, display_content, is_me, is_image)
        self.layout.addWidget(bubble)
        
        # Tự động cuộn xuống dưới cùng
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())