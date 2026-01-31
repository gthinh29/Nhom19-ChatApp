

import base64
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QStackedWidget, 
                             QListWidget, QListWidgetItem, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage # [ADD] Cần import QImage để xử lý dữ liệu ảnh
from client.ui.styles import BG_APP, BG_INPUT, BG_SIDEBAR, TEXT_MAIN, TEXT_SUB, PRIMARY, PRIMARY_HOVER, GREEN, RED
from client.ui.widgets import AvatarWidget
from client.core.bus import SignalBus

class SettingsWindow(QDialog):
    """Dialog cài đặt hồ sơ - cho phép chỉnh sửa thông tin cá nhân"""
    
    profile_updated = pyqtSignal(str, str)  # Phát khi hồ sơ cập nhật (fullname, avatar_b64)

    def __init__(self, controller_dummy, current_fullname, current_pixmap, current_avatar_b64=None):
        super().__init__()
        self.bus = SignalBus.get()
        self.setWindowTitle("Cài đặt")
        self.setFixedSize(700, 500)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {BG_APP}; }}
            QLabel {{ color: {TEXT_MAIN}; font-size: 14px; }}
            QLineEdit {{ 
                background-color: {BG_INPUT}; 
                color: white; 
                padding: 10px; 
                border-radius: 4px; 
                border: 1px solid {BG_SIDEBAR};
                font-size: 14px;
            }}
            QLineEdit:focus {{ border: 1px solid {PRIMARY}; }}
        """)
        
        self.current_fullname = current_fullname
        self.current_pixmap = current_pixmap
        self.current_avatar_b64 = current_avatar_b64
        
        self.new_avt_bytes = None  # Chứa bytes của ảnh mới nếu user chọn
        
        self.init_ui()

    def init_ui(self):
        """Khởi tạo giao diện - Sidebar menu + Content area"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==================== SIDEBAR MENU (TRÁI) ====================
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"background-color: {BG_SIDEBAR}; border-right: 1px solid {BG_INPUT};")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10, 20, 10, 20)
        sb_layout.setSpacing(5)

        lbl_title = QLabel("CÀI ĐẶT")
        lbl_title.setStyleSheet(f"color: {TEXT_SUB}; font-weight: bold; font-size: 12px; margin-bottom: 10px;")
        sb_layout.addWidget(lbl_title)

        self.menu_list = QListWidget()
        self.menu_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.menu_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ 
                padding: 10px; 
                border-radius: 4px; 
                color: {TEXT_SUB}; 
                font-weight: 500;
            }}
            QListWidget::item:selected {{ 
                background-color: #3F4147; 
                color: {TEXT_MAIN}; 
            }}
            QListWidget::item:hover {{ 
                background-color: #35373C; 
                color: {TEXT_MAIN}; 
            }}
        """)
        
        item_profile = QListWidgetItem("Hồ sơ của tôi")
        item_security = QListWidgetItem("Bảo mật & OTP")
        
        self.menu_list.addItem(item_profile)
        self.menu_list.addItem(item_security)
        
        self.menu_list.currentRowChanged.connect(self.change_page)
        
        sb_layout.addWidget(self.menu_list)
        sb_layout.addStretch()
        
        btn_close = QPushButton("Đóng")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"color: {TEXT_SUB}; background: transparent; text-align: left; padding: 10px;")
        btn_close.clicked.connect(self.close)
        sb_layout.addWidget(btn_close)

        main_layout.addWidget(sidebar)

        # ================== 2. CONTENT AREA (PHẢI) ==================
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        self.pages = QStackedWidget()
        
        self.page_profile = self.create_profile_page()
        self.page_security = self.create_security_page()
        
        self.pages.addWidget(self.page_profile)
        self.pages.addWidget(self.page_security)
        
        content_layout.addWidget(self.pages)
        main_layout.addWidget(content_area)

        self.menu_list.setCurrentRow(0)

    def change_page(self, index):
        self.pages.setCurrentIndex(index)

    # --- TRANG 1: HỒ SƠ ---
    def create_profile_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_head = QLabel("Hồ sơ người dùng")
        lbl_head.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_head)

        # Avatar Section
        h_avt = QHBoxLayout()
        h_avt.setSpacing(20)
        
        self.preview_avt = AvatarWidget(80, self.current_fullname)
        
        # [FIX] Logic hiển thị ảnh: Ưu tiên Base64 nếu Pixmap rỗng
        is_image_set = False
        
        # 1. Thử dùng Pixmap (nếu hợp lệ)
        if self.current_pixmap and not self.current_pixmap.isNull():
            self.preview_avt.set_image(self.current_pixmap.toImage())
            is_image_set = True
            
        # 2. Nếu Pixmap lỗi, thử decode từ Base64 string
        if not is_image_set and self.current_avatar_b64:
            try:
                b64_str = self.current_avatar_b64
                # Fix padding base64 nếu cần
                padding = len(b64_str) % 4
                if padding: b64_str += '=' * (4 - padding)
                
                img_data = base64.b64decode(b64_str)
                qimg = QImage.fromData(img_data)
                
                if not qimg.isNull():
                    self.preview_avt.set_image(qimg)
            except Exception as e:
                print(f"Error decoding avatar fallback: {e}")

        btn_change_avt = QPushButton("Đổi Avatar")
        btn_change_avt.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_change_avt.setStyleSheet(f"""
            QPushButton {{ background-color: {PRIMARY}; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {PRIMARY_HOVER}; }}
        """)
        btn_change_avt.clicked.connect(self.choose_avatar)
        
        h_avt.addWidget(self.preview_avt)
        h_avt.addWidget(btn_change_avt)
        h_avt.addStretch()
        layout.addLayout(h_avt)

        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background: {BG_INPUT};")
        layout.addWidget(line)

        layout.addWidget(QLabel("Tên hiển thị"))
        self.txt_name = QLineEdit(self.current_fullname)
        layout.addWidget(self.txt_name)

        layout.addStretch()

        self.btn_save_profile = QPushButton("Lưu thay đổi")
        self.btn_save_profile.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_profile.setFixedHeight(40)
        self.btn_save_profile.setStyleSheet(f"""
            QPushButton {{ background-color: {GREEN}; color: white; border-radius: 4px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: #1F944D; }}
        """)
        self.btn_save_profile.clicked.connect(self.save_profile_action)
        layout.addWidget(self.btn_save_profile)

        return page

    # --- TRANG 2: BẢO MẬT ---
    def create_security_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_head = QLabel("Đổi mật khẩu")
        lbl_head.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_head)

        lbl_desc = QLabel("Để bảo mật, chúng tôi cần xác thực qua Email trước khi đổi mật khẩu.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"color: {TEXT_SUB}; margin-bottom: 10px;")
        layout.addWidget(lbl_desc)

        self.btn_req_otp = QPushButton("Gửi mã xác thực (OTP) đến Email")
        self.btn_req_otp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_req_otp.setFixedHeight(36)
        self.btn_req_otp.setStyleSheet(f"""
            QPushButton {{ background-color: {PRIMARY}; color: white; border-radius: 4px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {PRIMARY_HOVER}; }}
            QPushButton:disabled {{ background-color: {BG_INPUT}; color: {TEXT_SUB}; }}
        """)
        self.btn_req_otp.clicked.connect(self.req_otp_action)
        layout.addWidget(self.btn_req_otp)

        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background: {BG_INPUT}; margin: 10px 0;")
        layout.addWidget(line)

        layout.addWidget(QLabel("Mã OTP"))
        self.txt_otp = QLineEdit()
        self.txt_otp.setPlaceholderText("Nhập 6 số từ email...")
        self.txt_otp.setEnabled(False) 
        layout.addWidget(self.txt_otp)

        layout.addWidget(QLabel("Mật khẩu mới"))
        self.txt_new_pass = QLineEdit()
        self.txt_new_pass.setPlaceholderText("Tối thiểu 6 ký tự")
        self.txt_new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_new_pass.setEnabled(False)
        layout.addWidget(self.txt_new_pass)

        layout.addStretch()

        self.btn_confirm_pass = QPushButton("Xác nhận đổi mật khẩu")
        self.btn_confirm_pass.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm_pass.setFixedHeight(40)
        self.btn_confirm_pass.setEnabled(False)
        self.btn_confirm_pass.setStyleSheet(f"""
            QPushButton {{ background-color: {RED}; color: white; border-radius: 4px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: #A1282C; }}
            QPushButton:disabled {{ background-color: {BG_INPUT}; color: {TEXT_SUB}; }}
        """)
        self.btn_confirm_pass.clicked.connect(self.confirm_pass_action)
        layout.addWidget(self.btn_confirm_pass)

        return page

    # --- LOGIC HANDLERS ---

    def choose_avatar(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Chọn Avatar", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)")
        if fname:
            try:
                with open(fname, "rb") as f:
                    self.new_avt_bytes = f.read()
                
                # Preview ảnh vừa chọn
                pix = QPixmap(fname)
                if not pix.isNull():
                    self.preview_avt.set_image(pix.toImage())
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể đọc file ảnh: {str(e)}")

    def save_profile_action(self):
        new_name = self.txt_name.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Lỗi", "Tên hiển thị không được để trống")
            return
        
        # Logic: Xác định dữ liệu ảnh cần gửi
        bytes_to_send = self.new_avt_bytes
        
        # Nếu không chọn ảnh mới, dùng ảnh cũ (decode từ base64)
        if bytes_to_send is None and self.current_avatar_b64:
            try:
                b64_str = self.current_avatar_b64
                padding = len(b64_str) % 4
                if padding: b64_str += '=' * (4 - padding)
                bytes_to_send = base64.b64decode(b64_str)
            except:
                bytes_to_send = None
        
        # Gửi lệnh lên Server (QUA BUS)
        self.bus.ui_update_profile.emit(new_name, bytes_to_send)
        
        # Emit signal để ChatWindow cập nhật Sidebar ngay (Optimistic UI)
        b64_for_signal = ""
        if bytes_to_send:
            b64_for_signal = base64.b64encode(bytes_to_send).decode('utf-8')
        
        self.profile_updated.emit(new_name, b64_for_signal)
        
        self.close()

    def req_otp_action(self):
        self.bus.ui_request_otp.emit()
        self.btn_req_otp.setText("Đang gửi yêu cầu...")
        self.btn_req_otp.setEnabled(False)

    def enable_otp_inputs(self):
        """ChatWindow gọi hàm này khi nhận tín hiệu 'otp_sent'"""
        self.btn_req_otp.setText("OTP đã được gửi! Kiểm tra Email.")
        self.txt_otp.setEnabled(True)
        self.txt_new_pass.setEnabled(True)
        self.btn_confirm_pass.setEnabled(True)
        self.txt_otp.setFocus()

    def confirm_pass_action(self):
        otp = self.txt_otp.text().strip()
        new_p = self.txt_new_pass.text().strip()
        
        if len(otp) < 4 or len(new_p) < 6:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập OTP và mật khẩu mới (tối thiểu 6 ký tự).")
            return

        self.bus.ui_change_password.emit(otp, new_p)
        self.close()