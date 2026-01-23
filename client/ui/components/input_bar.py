from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal
from client.ui.styles import COLORS

class InputBar(QWidget):
    """
    Thanh nhập tin nhắn ở dưới cùng.
    """
    send_message_signal = pyqtSignal(str) # Phát tín hiệu khi user nhấn gửi

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLORS['INPUT_BG']};")
        self.setFixedHeight(80)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Ô nhập liệu
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Nhập tin nhắn... (Nhấn Enter để gửi)")
        self.txt_input.setStyleSheet(f"background-color: {COLORS['SIDEBAR']}; color: white; border-radius: 15px; padding: 10px;")
        self.txt_input.returnPressed.connect(self.send_message)
        layout.addWidget(self.txt_input)

        # Nút gửi (Dùng text cho đơn giản, Phase sau thêm Icon)
        self.btn_send = QPushButton("Gửi")
        self.btn_send.setFixedSize(60, 40)
        self.btn_send.clicked.connect(self.send_message)
        layout.addWidget(self.btn_send)

    def send_message(self):
        text = self.txt_input.text().strip()
        if text:
            self.send_message_signal.emit(text)
            self.txt_input.clear()