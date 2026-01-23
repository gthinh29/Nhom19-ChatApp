import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from client.ui.styles import BG_APP, BG_SIDEBAR, BG_INPUT, TEXT_MAIN, TEXT_SUB, PRIMARY, PRIMARY_HOVER

class ExportEmailDialog(QDialog):
    """Dialog xuất lịch sử chat"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Xuất lịch sử chat")
        self.setFixedSize(400, 220)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {BG_APP}; border: 1px solid {BG_SIDEBAR}; }}
            QLabel {{ color: {TEXT_MAIN}; font-size: 14px; }}
            QLineEdit {{ 
                background-color: {BG_INPUT}; 
                color: white; 
                padding: 10px; 
                border-radius: 5px; 
                border: 1px solid {BG_SIDEBAR};
            }}
            QLineEdit:focus {{ border: 1px solid {PRIMARY}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        lbl_title = QLabel("Nhập địa chỉ Email nhận file:")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 15px;")
        layout.addWidget(lbl_title)
        
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("example@gmail.com")
        self.txt_email.setClearButtonEnabled(True)
        layout.addWidget(self.txt_email)
        
        layout.addStretch()
        
        h_btn = QHBoxLayout()
        
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {TEXT_SUB}; border: none; font-weight: bold; }}
            QPushButton:hover {{ color: {TEXT_MAIN}; }}
        """)
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_send = QPushButton("GỬI NGAY")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setFixedHeight(36)
        self.btn_send.setStyleSheet(f"""
            QPushButton {{ background-color: {PRIMARY}; color: white; border-radius: 4px; font-weight: bold; padding: 0 15px; }}
            QPushButton:hover {{ background-color: {PRIMARY_HOVER}; }}
        """)
        self.btn_send.clicked.connect(self.accept)
        
        h_btn.addStretch()
        h_btn.addWidget(btn_cancel)
        h_btn.addWidget(self.btn_send)
        
        layout.addLayout(h_btn)

    def get_email(self):
        """Lấy địa chỉ email đã nhập"""
        return self.txt_email.text().strip()