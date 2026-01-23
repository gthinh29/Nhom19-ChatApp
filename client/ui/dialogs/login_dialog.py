"""Mô-đun client\ui\dialogs\login_dialog.py - mô tả ngắn bằng tiếng Việt."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QTabWidget, QMessageBox, QFrame, QGraphicsDropShadowEffect, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor
from client.ui.styles import GLOBAL_STYLE, BG_SIDEBAR, BG_INPUT, TEXT_MAIN, TEXT_SUB, PRIMARY, GREEN, BTN_PRIMARY, BTN_GREEN
from client.core.bus import SignalBus

# ==================== WIDGET QUÊN MẬT KHẨU ====================
class ForgotPasswordWidget(QWidget):
    """Widget xử lý khôi phục mật khẩu - yêu cầu OTP qua Email"""
    
    def __init__(self, parent, go_back_callback):
        super().__init__(parent)
        self.go_back = go_back_callback
        self.bus = SignalBus.get()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(15)

        # Header
        lbl_h = QLabel("KHÔI PHỤC TÀI KHOẢN")
        lbl_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_h.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {TEXT_MAIN}; margin-top:10px; border:none;")
        layout.addWidget(lbl_h)

        # ==================== STACKED WIDGET: STEP 1 vs STEP 2 ====================
        self.stack = QStackedWidget()
        
        # --- PAGE 1: YÊU CẦU OTP ---
        p1 = QWidget()
        l1 = QVBoxLayout(p1)
        l1.setContentsMargins(0,0,0,0)
        l1.setSpacing(12)
        
        self.txt_u = QLineEdit()
        self.txt_u.setPlaceholderText("Tên đăng nhập")
        self.txt_u.setStyleSheet(self.input_style())
        
        self.txt_e = QLineEdit()
        self.txt_e.setPlaceholderText("Email đăng ký")
        self.txt_e.setStyleSheet(self.input_style())
        
        self.btn_send = QPushButton("GỬI MÃ OTP")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setStyleSheet(BTN_PRIMARY)
        self.btn_send.setFixedHeight(40)
        self.btn_send.clicked.connect(self.on_click_send)
        
        l1.addWidget(self.txt_u)
        l1.addWidget(self.txt_e)
        l1.addWidget(self.btn_send)
        l1.addStretch()
        
        # --- PAGE 2: ĐỔI MẬT KHẨU VỚI OTP ---
        p2 = QWidget()
        l2 = QVBoxLayout(p2)
        l2.setContentsMargins(0,0,0,0)
        l2.setSpacing(12)
        
        lbl_msg = QLabel("✅ Đã gửi mã OTP về Email!")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg.setStyleSheet(f"color:{GREEN}; font-weight:bold; border:none;")
        
        self.txt_otp = QLineEdit(); self.txt_otp.setPlaceholderText("Nhập mã OTP (6 số)")
        self.txt_otp.setStyleSheet(self.input_style())
        
        self.txt_new = QLineEdit(); self.txt_new.setPlaceholderText("Mật khẩu mới")
        self.txt_new.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_new.setStyleSheet(self.input_style())
        
        self.btn_rst = QPushButton("XÁC NHẬN ĐỔI")
        self.btn_rst.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rst.setStyleSheet(BTN_GREEN)
        self.btn_rst.setFixedHeight(40)
        self.btn_rst.clicked.connect(self.on_click_reset)
        
        l2.addWidget(lbl_msg); l2.addWidget(self.txt_otp); l2.addWidget(self.txt_new); l2.addWidget(self.btn_rst); l2.addStretch()

        self.stack.addWidget(p1); self.stack.addWidget(p2)
        layout.addWidget(self.stack)

        # Footer Button
        btn_back = QPushButton("← Quay lại Đăng nhập")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(f"color: {TEXT_SUB}; background: transparent; font-weight: bold; border: none;")
        btn_back.clicked.connect(self.go_back_handler)
        layout.addWidget(btn_back)

    def input_style(self):
        return f"QLineEdit {{ background-color: {BG_INPUT}; border: 1px solid transparent; border-radius: 4px; padding: 10px; color: white; }} QLineEdit:focus {{ border: 1px solid {PRIMARY}; }}"

    def on_click_send(self):
        u, e = self.txt_u.text().strip(), self.txt_e.text().strip()
        if u and e:
            self.btn_send.setText("⏳ Đang gửi..."); self.btn_send.setEnabled(False)
            self.bus.ui_forgot_request_otp.emit(u, e)
        else: QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đủ thông tin!")

    def on_click_reset(self):
        c, p = self.txt_otp.text().strip(), self.txt_new.text().strip()
        if c and p:
            self.bus.ui_forgot_reset_pass.emit(self.txt_u.text().strip(), c, p)
        else: QMessageBox.warning(self, "Lỗi", "Vui lòng nhập OTP và Mật khẩu mới!")

    def go_back_handler(self):
        self.stack.setCurrentIndex(0)
        self.btn_send.setText("GỬI MÃ OTP"); self.btn_send.setEnabled(True)
        self.txt_u.clear(); self.txt_e.clear(); self.txt_otp.clear(); self.txt_new.clear()
        self.go_back()

# --- LOGIN WINDOW CHÍNH ---
class LoginWindow(QWidget):
    
    def __init__(self): 
        super().__init__()
        self.bus = SignalBus.get()
        self.setWindowTitle("LAN Chat")
        self.resize(1000, 700)
        self.setStyleSheet(GLOBAL_STYLE)
        
        main_layout = QVBoxLayout(self); main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card Container
        card = QFrame()
        card.setFixedSize(420, 580)
        card.setStyleSheet(f"background-color: {BG_SIDEBAR}; border-radius: 12px;")
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(40); shadow.setColor(QColor(0,0,0,120)); shadow.setOffset(0,10); card.setGraphicsEffect(shadow)

        c_lay = QVBoxLayout(card); c_lay.setContentsMargins(40, 40, 40, 40); c_lay.setSpacing(10)

        # Header chung
        self.head_w = QWidget(); hl = QVBoxLayout(self.head_w); hl.setContentsMargins(0,0,0,0)
        lbl_i = QLabel("💬"); lbl_i.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl_i.setStyleSheet("font-size: 40px; margin-bottom:10px; border:none;")
        lbl_t = QLabel("Chào mừng trở lại!"); lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl_t.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {TEXT_MAIN}; border:none;")
        lbl_s = QLabel("Kết nối với bạn bè ngay lập tức."); lbl_s.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl_s.setStyleSheet(f"font-size: 13px; color: {TEXT_SUB}; margin-bottom: 20px; border:none;")
        hl.addWidget(lbl_i); hl.addWidget(lbl_t); hl.addWidget(lbl_s)
        c_lay.addWidget(self.head_w)

        # Main Stack
        self.main_stack = QStackedWidget()
        
        # --- VIEW 1: AUTH ---
        self.view_auth = QWidget(); vl = QVBoxLayout(self.view_auth); vl.setContentsMargins(0,0,0,0)
        
        self.tabs = QTabWidget()
        self.tabs.tabBar().setExpanding(True); self.tabs.tabBar().setDocumentMode(True)
        self.tabs.setStyleSheet(f"QTabWidget::pane {{ border: none; }} QTabBar::tab {{ background: transparent; color: {TEXT_SUB}; font-weight: bold; height: 40px; border-bottom: 2px solid {BG_INPUT}; margin: 0; }} QTabBar::tab:selected {{ color: {TEXT_MAIN}; border-bottom: 2px solid {PRIMARY}; }}")

        # Tab Login
        w_log = QWidget(); l1 = QVBoxLayout(w_log); l1.setContentsMargins(0,20,0,0); l1.setSpacing(15)
        
        self.txt_user = QLineEdit(); self.txt_user.setPlaceholderText("Tên đăng nhập"); self.txt_user.setStyleSheet(self.input_style())
        
        self.txt_pass = QLineEdit(); self.txt_pass.setPlaceholderText("Mật khẩu"); self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setStyleSheet(self.input_style())
        self.txt_pass.returnPressed.connect(self.do_login)
        
        btn_f = QPushButton("Quên mật khẩu?"); btn_f.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_f.setStyleSheet(f"color: {PRIMARY}; background: transparent; border: none; text-align: right; font-weight: bold;")
        btn_f.clicked.connect(self.to_forgot)
        
        self.btn_login = QPushButton("ĐĂNG NHẬP"); self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setStyleSheet(BTN_PRIMARY); self.btn_login.setFixedHeight(42); self.btn_login.clicked.connect(self.do_login)
        
        l1.addWidget(self.txt_user); l1.addWidget(self.txt_pass); l1.addWidget(btn_f); l1.addSpacing(5); l1.addWidget(self.btn_login); l1.addStretch()

        # Tab Register
        w_reg = QWidget(); l2 = QVBoxLayout(w_reg); l2.setContentsMargins(0,20,0,0); l2.setSpacing(12)
        self.ru = QLineEdit(); self.ru.setPlaceholderText("Tên đăng nhập")
        self.rn = QLineEdit(); self.rn.setPlaceholderText("Nickname")
        self.re = QLineEdit(); self.re.setPlaceholderText("Email")
        self.rp = QLineEdit(); self.rp.setPlaceholderText("Mật khẩu"); self.rp.setEchoMode(QLineEdit.EchoMode.Password)
        for i in [self.ru, self.rn, self.re, self.rp]: i.setStyleSheet(self.input_style()); i.setFixedHeight(40)
        
        self.btn_register = QPushButton("ĐĂNG KÝ"); self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.setStyleSheet(BTN_GREEN); self.btn_register.setFixedHeight(42); self.btn_register.clicked.connect(self.do_reg)
        
        l2.addWidget(self.ru); l2.addWidget(self.rn); l2.addWidget(self.re); l2.addWidget(self.rp); l2.addSpacing(10); l2.addWidget(self.btn_register); l2.addStretch()

        self.tabs.addTab(w_log, "Đăng Nhập"); self.tabs.addTab(w_reg, "Đăng Ký")
        vl.addWidget(self.tabs)

        # --- VIEW 2: FORGOT ---
        self.view_forgot = ForgotPasswordWidget(self.main_stack, self.to_auth)

        self.main_stack.addWidget(self.view_auth)
        self.main_stack.addWidget(self.view_forgot)
        
        c_lay.addWidget(self.main_stack)
        main_layout.addWidget(card)
        
        # Kết nối lắng nghe phản hồi từ Logic (AuthManager)
        self.bus.core_auth_failed.connect(self.show_error)
        self.bus.core_register_result.connect(self.on_reg_result)
        self.bus.core_forgot_result.connect(self.on_forgot_result)

        # [NEW] Mặc định ban đầu disable cho đến khi MainApp báo connected
        self.set_network_status(False)

    def input_style(self):
        return f"QLineEdit {{ background-color: {BG_INPUT}; border: 1px solid transparent; border-radius: 4px; padding: 10px; color: white; }} QLineEdit:focus {{ border: 1px solid {PRIMARY}; }}"

    def to_forgot(self): self.head_w.hide(); self.main_stack.setCurrentIndex(1)
    def to_auth(self): self.head_w.show(); self.main_stack.setCurrentIndex(0)

    # ==================== LOGIC MỚI: TRẠNG THÁI MẠNG ====================
    def set_network_status(self, is_connected):
        """Enable/Disable nút dựa trên kết nối mạng"""
        if is_connected:
            self.btn_login.setEnabled(True)
            self.btn_login.setText("ĐĂNG NHẬP")
            self.btn_login.setStyleSheet(BTN_PRIMARY)
            
            self.btn_register.setEnabled(True)
            self.btn_register.setText("ĐĂNG KÝ")
            self.btn_register.setStyleSheet(BTN_GREEN)
        else:
            disabled_style = f"background-color: {TEXT_SUB}; color: white; border: none; border-radius: 4px; padding: 10px; font-weight: bold;"
            
            self.btn_login.setEnabled(False)
            self.btn_login.setText("⏳ ĐANG KẾT NỐI...")
            self.btn_login.setStyleSheet(disabled_style)
            
            self.btn_register.setEnabled(False)
            self.btn_register.setText("⏳ ĐANG KẾT NỐI...")
            self.btn_register.setStyleSheet(disabled_style)

    def reset_state(self):
        """Khôi phục trạng thái ban đầu (dùng khi Logout)"""
        self.txt_pass.clear()
        self.tabs.setCurrentIndex(0)
        self.to_auth()
        # Đặt lại trạng thái chờ mạng (MainApp sẽ bật lại khi connect xong)
        self.set_network_status(False)

    def do_login(self): 
        # Disable button để ngăn multiple clicks
        self.btn_login.setEnabled(False)
        self.btn_login.setText("⏳ Đang đăng nhập...")
        self.bus.ui_request_login.emit(self.txt_user.text().strip(), self.txt_pass.text().strip())
        
    def do_reg(self): 
        self.btn_register.setEnabled(False)
        self.btn_register.setText("⏳ Đang tạo tài khoản...")
        self.bus.ui_request_register.emit(self.ru.text().strip(), self.rp.text().strip(), self.rn.text().strip(), self.re.text().strip())

    # --- CALLBACKS (Xử lý phản hồi từ Logic) ---
    
    def on_reg_result(self, ok, msg):
        # Khi có kết quả (dù lỗi hay không) nghĩa là mạng OK, enable lại nút
        self.set_network_status(True)
        if ok: self.show_success(msg)
        else: self.show_error(msg)

    def on_forgot_result(self, ok, msg, type_res):
        if type_res == "otp_sent":
            self.view_forgot.btn_send.setEnabled(True); self.view_forgot.btn_send.setText("GỬI MÃ OTP")
            if ok: self.view_forgot.stack.setCurrentIndex(1)
            else: QMessageBox.warning(self, "Lỗi", msg)
        elif type_res == "reset_done":
            if ok:
                QMessageBox.information(self, "Thành công", "Đổi mật khẩu thành công! Hãy đăng nhập lại.")
                self.to_auth()
                self.view_forgot.go_back_handler()
            else: QMessageBox.warning(self, "Lỗi", msg)

    def show_error(self, m):
        # Nếu server báo lỗi (sai pass), nghĩa là mạng vẫn thông -> Mở nút lại
        self.set_network_status(True)
        QMessageBox.warning(self, "Lỗi", m)
        
    def show_success(self, m):
        self.set_network_status(True)
        QMessageBox.information(self, "OK", m)
        self.tabs.setCurrentIndex(0)