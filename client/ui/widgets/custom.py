

import base64
from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath
from client.ui.styles import BG_CARD, TEXT_SUB, BG_INPUT, PRIMARY, PRIMARY_HOVER

class ImageDecoderWorker(QThread):
    """Worker thread giải mã Base64 sang QImage"""
    image_ready = pyqtSignal(QImage)
    
    def __init__(self, b64_data):
        super().__init__()
        self.b64_data = b64_data
    
    def run(self):
        try:
            if not self.b64_data: return
            padding = len(self.b64_data) % 4
            if padding: self.b64_data += '=' * (4 - padding)
            
            qimg = QImage.fromData(base64.b64decode(self.b64_data))
            if not qimg.isNull():
                self.image_ready.emit(qimg)
        except Exception as e:
            print(f"[ImageDecoder] Error: {e}")

class AvatarWidget(QLabel):
    """Avatar tròn với chữ cái mặc định"""
    def __init__(self, size=40, text="?", color=BG_CARD):
        super().__init__()
        self.setFixedSize(size, size)
        self.default_text = text
        self.default_color = color
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.decoder_thread = None
        self.render_initials()

    def render_initials(self):
        self.setPixmap(QPixmap())
        char = self.default_text[0].upper() if self.default_text else "?"
        self.setText(char)
        self.setStyleSheet(f"""
            background-color: {self.default_color}; 
            color: {TEXT_SUB}; 
            border-radius: {self.width()//2}px; 
            font-weight: bold; 
            font-size: {self.width()//3}px;
            border: 1px solid {BG_INPUT};
        """)

    def set_image(self, qimage):
        if qimage and not qimage.isNull():
            self.setText("")
            pix = QPixmap.fromImage(qimage)
            size = self.size()
            rounded = QPixmap(size)
            rounded.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size.width(), size.height())
            painter.setClipPath(path)
            
            painter.drawPixmap(0, 0, size.width(), size.height(), 
                              pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                         Qt.TransformationMode.SmoothTransformation))
            painter.end()
            self.setPixmap(rounded)
            self.setStyleSheet(f"border-radius: {size.width()//2}px;")
        else:
            self.render_initials()

    def set_image_from_b64_async(self, b64_data):
        if self.decoder_thread and self.decoder_thread.isRunning():
            self.decoder_thread.wait()
        
        self.decoder_thread = ImageDecoderWorker(b64_data)
        self.decoder_thread.image_ready.connect(self.set_image)
        self.decoder_thread.start()

class PendingFileItem(QFrame):
    """Item hiển thị file đang chờ/upload (Dùng trong danh sách file pending nếu có)"""
    resume_clicked = pyqtSignal(str, str)
    cancel_clicked = pyqtSignal(str)
    
    def __init__(self, fileid, filename, total_size, uploaded_bytes, status, file_path=None):
        super().__init__()
        self.fileid = fileid
        self.file_path = file_path
        
        self.setStyleSheet(f"background-color: {BG_CARD}; border-radius: 8px;")
        self.setMinimumHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # Filename
        h_lay = QHBoxLayout()
        lbl_name = QLabel(filename)
        lbl_name.setStyleSheet("font-weight: bold; color: white;")
        h_lay.addWidget(lbl_name)
        h_lay.addStretch()
        layout.addLayout(h_lay)
        
        # Size Info
        size_mb = total_size / (1024 * 1024) if total_size else 0
        layout.addWidget(QLabel(f"{size_mb:.1f} MB", styleSheet=f"color: {TEXT_SUB}; font-size: 12px;"))
        
        # Progress
        percent = int((uploaded_bytes / total_size) * 100) if total_size > 0 else 0
        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(percent)
        pbar.setFixedHeight(6)
        pbar.setStyleSheet(f"""
            QProgressBar {{ background-color: {BG_INPUT}; border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background-color: {PRIMARY}; border-radius: 3px; }}
        """)
        layout.addWidget(pbar)
        
        # Actions
        a_lay = QHBoxLayout()
        a_lay.setSpacing(8)
        
        if status in ['pending', 'uploading'] and percent < 100:
            btn_resume = QPushButton("▶️ Tiếp tục")
            btn_resume.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_resume.setFixedHeight(28)
            btn_resume.setStyleSheet(f"background-color: {PRIMARY}; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px;")
            btn_resume.clicked.connect(lambda: self.resume_clicked.emit(fileid, self.file_path or ''))
            a_lay.addWidget(btn_resume)
        
        btn_cancel = QPushButton("✕ Hủy")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setFixedHeight(28)
        btn_cancel.setStyleSheet(f"background-color: transparent; color: {TEXT_SUB}; border: 1px solid {BG_INPUT}; border-radius: 4px; font-weight: bold; font-size: 12px;")
        btn_cancel.clicked.connect(lambda: self.cancel_clicked.emit(fileid))
        
        a_lay.addWidget(btn_cancel)
        a_lay.addStretch()
        layout.addLayout(a_lay)