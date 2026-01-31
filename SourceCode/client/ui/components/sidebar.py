import base64
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QAbstractItemView, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from client.ui.styles import BG_SIDEBAR, TEXT_SUB, PRIMARY, BG_CARD, GREEN
from client.ui.widgets import AvatarWidget

class Sidebar(QFrame):
    """Sidebar chứa danh sách online và thẻ người dùng hiện tại."""
    
    settings_requested = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, username, fullname, parent=None):
        super().__init__(parent)
        self.username = username
        self.fullname = fullname
        self.setFixedWidth(280)
        self.setStyleSheet(f"background-color: {BG_SIDEBAR}; border: none;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 35)
        layout.setSpacing(10)
        
        # Logo
        lbl_logo = QLabel("  LAN CHAT")
        lbl_logo.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {PRIMARY}; margin-bottom: 20px; letter-spacing: 1px;")
        layout.addWidget(lbl_logo)
        
        # Channel Button
        layout.addWidget(QLabel("KÊNH CHAT", styleSheet=f"color:{TEXT_SUB}; font-size:12px; font-weight:bold; margin-top: 10px;"))
        btn_chan = QPushButton("#  sảnh-chính")
        btn_chan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_chan.setStyleSheet(f"""
            QPushButton {{ background-color: #3F4147; color: white; padding: 10px; border-radius: 5px; text-align: left; font-weight: bold; font-size: 15px; }}
            QPushButton:hover {{ background-color: #3F4147; }}
        """)
        layout.addWidget(btn_chan)
        layout.addSpacing(15)

        # Online List
        layout.addWidget(QLabel(f"THÀNH VIÊN ONLINE", styleSheet=f"color:{TEXT_SUB}; font-size:12px; font-weight:bold;"))
        self.list_onl = QListWidget()
        self.list_onl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_onl.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        # Add self first
        self.add_user_item(self.username, self.fullname, is_me=True)
        layout.addWidget(self.list_onl)

        layout.addStretch()
        
        # User Card (Bottom)
        self._init_user_card(layout)

    def _init_user_card(self, parent_layout):
        u_card = QFrame()
        u_card.setStyleSheet(f"background-color: {BG_CARD}; border-radius: 8px;")
        uc_lay = QHBoxLayout(u_card); uc_lay.setContentsMargins(8, 8, 8, 8)
        
        self.user_avt_widget = AvatarWidget(40, self.fullname)
        
        user_info_lay = QVBoxLayout(); user_info_lay.setSpacing(0)
        self.l_name = QLabel(self.fullname); self.l_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        l_status = QLabel("Online"); l_status.setStyleSheet(f"color: {GREEN}; font-size: 11px;")
        user_info_lay.addWidget(self.l_name); user_info_lay.addWidget(l_status)
        
        btn_set = QPushButton("")
        btn_set.setFixedSize(30, 30)
        btn_set.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_set.setToolTip("Cài đặt tài khoản")
        btn_set.setStyleSheet("background: transparent; font-size: 16px; border-radius: 4px;")
        btn_set.clicked.connect(self.settings_requested.emit)
        
        btn_out = QPushButton("")
        btn_out.setFixedSize(30, 30)
        btn_out.setToolTip("Đăng xuất")
        btn_out.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_out.setStyleSheet("background: transparent; font-size: 16px; color: #DA373C; border-radius: 4px;")
        btn_out.clicked.connect(self.logout_requested.emit)

        uc_lay.addWidget(self.user_avt_widget)
        uc_lay.addLayout(user_info_lay)
        uc_lay.addWidget(btn_set)
        uc_lay.addWidget(btn_out)
        
        parent_layout.addWidget(u_card)

    def add_user_item(self, username, fullname, is_me=False):
        display = f"  {fullname} (Bạn)" if is_me else f"  {fullname}"
        item = QListWidgetItem(display)
        item.setData(Qt.ItemDataRole.UserRole, username)
        self.list_onl.addItem(item)

    def set_online_list(self, users):
        self.list_onl.clear()
        # Add me first
        self.add_user_item(self.username, self.fullname, is_me=True)
        for u in users:
            if u.get("username") != self.username:
                self.add_user_item(u.get("username"), u.get("fullname"))

    def update_user_status(self, status, username, fullname):
        # Trả về True nếu là User mới Join (để MainWindow hiện Toast)
        if username == self.username: return False
        
        found = False
        for i in range(self.list_onl.count()):
            item = self.list_onl.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == username:
                if status == "JOIN": item.setText(f"  {fullname}") 
                elif status == "LEAVE": self.list_onl.takeItem(i)
                found = True
                break
        
        if status == "JOIN" and not found:
            self.add_user_item(username, fullname)
            return True # Joined
        
        return False

    def update_self_profile(self, name, avt_b64):
        self.fullname = name
        self.l_name.setText(name)
        
        # Decode avatar logic
        img = None
        if avt_b64:
            try:
                padding = len(avt_b64) % 4
                if padding: avt_b64 += '=' * (4 - padding)
                pix = QPixmap()
                pix.loadFromData(base64.b64decode(avt_b64))
                if not pix.isNull(): img = pix.toImage()
            except: pass
        self.user_avt_widget.set_image(img)