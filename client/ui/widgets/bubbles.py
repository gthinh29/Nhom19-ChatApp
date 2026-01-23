from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import base64
from client.ui.styles import COLORS

class ImageDecoderThread(QThread):
    """
    Task 7: Worker Thread giải mã ảnh Base64 -> QPixmap
    Giúp UI không bị đơ khi load ảnh lớn.
    """
    result_ready = pyqtSignal(QPixmap)

    def __init__(self, base64_data):
        super().__init__()
        self.base64_data = base64_data

    def run(self):
        try:
            image_data = base64.b64decode(self.base64_data)
            image = QImage.fromData(image_data)
            if not image.isNull():
                # Scale ảnh thumbnail tối đa 300px
                pixmap = QPixmap.fromImage(image).scaled(
                    300, 300, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.result_ready.emit(pixmap)
        except Exception as e:
            print(f"Decode error: {e}")

class MessageBubble(QWidget):
    """
    Widget hiển thị 1 tin nhắn (Text hoặc Image).
    """
    def __init__(self, sender, content, is_me=False, is_image=False):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        
        # Bong bóng nội dung
        self.bubble = QLabel()
        self.bubble.setWordWrap(True)
        self.bubble.setMaximumWidth(400) # Giới hạn chiều rộng
        
        # Màu sắc dựa trên người gửi
        bg_color = COLORS['PRIMARY'] if is_me else '#404249'
        self.bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
            }}
        """)

        if is_image:
            self.bubble.setText("📷 Đang tải ảnh...")
            # Bắt đầu giải mã Async
            self.decoder = ImageDecoderThread(content)
            self.decoder.result_ready.connect(self.display_image)
            self.decoder.start()
        else:
            # Text thường (Hỗ trợ HTML cơ bản)
            self.bubble.setText(f"<b>{sender}</b>:<br>{content}")

        # Căn chỉnh trái/phải
        if is_me:
            self.layout.addStretch()
            self.layout.addWidget(self.bubble)
        else:
            self.layout.addWidget(self.bubble)
            self.layout.addStretch()

    def display_image(self, pixmap):
        """Callback khi ảnh giải mã xong"""
        self.bubble.setPixmap(pixmap)
        self.bubble.setText("") # Xóa text loading