

import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QProgressBar, QDialog
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QPalette
from client.ui.styles import BG_APP, BG_INPUT, BG_SIDEBAR, TEXT_MAIN, TEXT_SUB, PRIMARY
from client.ui.icon_factory import IconFactory
from client.ui.dialogs.export_dialog import ExportEmailDialog
from client.core.bus import SignalBus

class InputBar(QFrame):
    """Thanh nhập liệu và công cụ phía dưới"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bus = SignalBus.get()
        self.setStyleSheet(f"background-color: {BG_APP}; padding: 15px;")
        self.init_ui()

    def init_ui(self):
        icl = QHBoxLayout(self)
        icl.setContentsMargins(20, 0, 20, 20)
        icl.setSpacing(15)
        icl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Buttons (Exposed for MainWindow)
        # [FIX] Đổi tên biến để MainWindow có thể truy cập (image_btn, file_btn)
        self.image_btn = self._create_icon_btn("camera")
        self.file_btn = self._create_icon_btn("clip")
        
        # Nút Export Email (Giữ logic xử lý tại chỗ vì nó không cần Optimistic UI)
        self.btn_export = self._create_icon_btn("email")
        self.btn_export.clicked.connect(self.request_export)

        icl.addWidget(self.image_btn)
        icl.addWidget(self.file_btn)
        icl.addWidget(self.btn_export)

        # Input Capsule
        capsule = QFrame()
        capsule.setFixedHeight(55)
        capsule.setStyleSheet(f"background-color: {BG_INPUT}; border-radius: 25px;")
        cap_lay = QHBoxLayout(capsule); cap_lay.setContentsMargins(20, 0, 10, 0); cap_lay.setSpacing(5)
        
        self.txt = QLineEdit()
        self.txt.setPlaceholderText("Nhập tin nhắn...") 
        self.txt.setFixedHeight(25) 
        self._setup_input_style()
        self.txt.returnPressed.connect(self.send_message)
        
        self.btn_send_msg = QPushButton()
        self.btn_send_msg.setFixedSize(25, 25)
        self.btn_send_msg.setIcon(IconFactory.create_icon("send", PRIMARY, 20))
        self.btn_send_msg.setIconSize(QSize(20, 20))
        self.btn_send_msg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_msg.setStyleSheet(f"QPushButton {{ background-color: transparent; border-radius: 18px; }} QPushButton:hover {{ background-color: {BG_SIDEBAR}; }}")
        self.btn_send_msg.clicked.connect(self.send_message)

        cap_lay.addWidget(self.txt)
        cap_lay.addWidget(self.btn_send_msg)
        icl.addWidget(capsule, 1)

        # Progress Bar
        self.upload_progress_bar = QProgressBar()
        self.upload_progress_bar.setFixedHeight(16)
        self.upload_progress_bar.setRange(0, 100)
        self.upload_progress_bar.setValue(0)
        self.upload_progress_bar.hide()
        icl.addWidget(self.upload_progress_bar)

    def _create_icon_btn(self, icon_name):
        """Helper tạo nút icon"""
        btn = QPushButton()
        btn.setFixedSize(40, 40)
        btn.setIcon(IconFactory.create_icon(icon_name, "#B5BAC1", 24))
        btn.setIconSize(QSize(24, 24))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("QPushButton { background-color: transparent; border-radius: 20px; } QPushButton:hover { background-color: #404249; }")
        return btn

    def _setup_input_style(self):
        p_text_color = QColor(TEXT_SUB); p_text_color.setAlpha(180) 
        pal = self.txt.palette()
        pal.setColor(QPalette.ColorRole.PlaceholderText, p_text_color)
        pal.setColor(QPalette.ColorRole.Text, QColor(TEXT_MAIN))
        self.txt.setPalette(pal)
        self.txt.setStyleSheet(f"QLineEdit {{ border: none; background: transparent; font-size: 15px; color: {TEXT_MAIN}; selection-background-color: {PRIMARY}; padding: 0px; }}")

    def set_enabled_input(self, enabled):
        self.txt.setPlaceholderText("Nhập tin nhắn..." if enabled else "Đang mất kết nối...")
        self.btn_send_msg.setEnabled(enabled)
        self.image_btn.setEnabled(enabled)
        self.file_btn.setEnabled(enabled)
        self.btn_export.setEnabled(enabled)

    def send_message(self):
        t = self.txt.text().strip()
        if t:
            self.bus.ui_send_text.emit(t)
            self.txt.clear()

    # [REMOVED] pick_img & pick_file đã được chuyển sang MainWindow
    
    def request_export(self):
        dlg = ExportEmailDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            email = dlg.get_email()
            if email: self.bus.ui_export_chat.emit(email)

    def update_progress(self, percent):
        self.upload_progress_bar.setValue(percent)
        if not self.upload_progress_bar.isVisible(): self.upload_progress_bar.show()
        if percent >= 100: QTimer.singleShot(800, self.upload_progress_bar.hide)