from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PyQt6.QtCore import Qt
from client.ui.styles import COLORS

class ChatArea(QScrollArea):
    """
    Khu vực cuộn chứa các bong bóng chat (Message Bubbles).
    """
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet(f"background-color: {COLORS['CHAT_BG']}; border: none;")
        
        # Container chứa tin nhắn
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self.setWidget(self.container)

    def add_message(self, sender, content, is_me=False):
        """Thêm một tin nhắn vào giao diện (Dạng text đơn giản cho Phase 3)"""
        # Trong Phase 4 sẽ thay bằng Bubble Widget phức tạp hơn
        lbl = QLabel(f"{sender}: {content}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"""
            background-color: {'#5865F2' if is_me else '#404249'};
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 14px;
        """)
        
        # Căn lề trái/phải
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0,0,0,0)
        wrapper_layout.addWidget(lbl)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignRight if is_me else Qt.AlignmentFlag.AlignLeft)
        
        self.layout.addWidget(wrapper)
        
        # Tự động cuộn xuống dưới
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())