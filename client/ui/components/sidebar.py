# client/ui/components/sidebar.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QHBoxLayout
from PyQt6.QtCore import Qt
from client.ui.styles import COLORS
from client.ui.icon_factory import IconFactory

class Sidebar(QWidget):
    """
    Thanh bên trái chứa danh sách kênh và thông tin server.
    """
    def __init__(self):
        super().__init__()
        self.setFixedWidth(240)
        self.setStyleSheet(f"background-color: {COLORS['SIDEBAR']};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # 1. Header Server Name
        self.lbl_server = QLabel("ChatApp Server")
        self.lbl_server.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px; color: white;")
        layout.addWidget(self.lbl_server)
        
        # Đường kẻ ngang
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {COLORS['BACKGROUND']};")
        layout.addWidget(line)
        
        # 2. Danh sách kênh (Giả lập)
        channels = ["chung", "thảo-luận", "thông-báo", "game-room", "music"]
        
        lbl_cat = QLabel("TEXT CHANNELS")
        lbl_cat.setStyleSheet(f"color: {COLORS['TEXT_MUTED']}; font-size: 11px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_cat)
        
        for ch in channels:
            btn = QPushButton(f"  {ch}")
            # Icon dấu #
            icon = IconFactory.create_hashtag_icon()
            btn.setIcon(icon)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    text-align: left;
                    color: {COLORS['TEXT_MUTED']};
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: #35373C;
                    color: {COLORS['TEXT_MAIN']};
                }}
            """)
            layout.addWidget(btn)
            
        layout.addStretch()
        
        # 3. User Panel (Bottom)
        self.user_panel = QWidget()
        self.user_panel.setStyleSheet(f"background-color: {COLORS['SERVER_LIST']}; border-radius: 4px;")
        self.user_panel.setFixedHeight(55)
        p_layout = QHBoxLayout(self.user_panel)
        p_layout.setContentsMargins(8, 8, 8, 8)
        
        # Avatar
        self.lbl_avatar = QLabel()
        self.lbl_avatar.setPixmap(IconFactory.create_circle_icon(COLORS['SUCCESS'], 35, "ME"))
        p_layout.addWidget(self.lbl_avatar)
        
        # Name
        self.lbl_username = QLabel("User")
        self.lbl_username.setStyleSheet("font-weight: bold; font-size: 13px;")
        p_layout.addWidget(self.lbl_username)
        
        layout.addWidget(self.user_panel)

    def set_user_info(self, username):
        self.lbl_username.setText(username)
        # Update avatar text
        self.lbl_avatar.setPixmap(IconFactory.create_circle_icon(COLORS['SUCCESS'], 35, username))