

import os
import re 
import base64
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, 
                             QPushButton, QGraphicsDropShadowEffect, QDialog, 
                             QScrollArea, QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon, QColor, QImage
from client.ui.styles import ME_BUBBLE, THEM_BUBBLE, TEXT_SUB, BG_INPUT, PRIMARY, BG_APP
from client.ui.widgets.custom import AvatarWidget
from client.core.bus import SignalBus 

class ImageViewer(QDialog):
    """Cửa sổ xem ảnh Fullscreen"""
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Xem Ảnh")
        self.resize(1000, 800)
        self.setWindowFlags(Qt.WindowType.Window) 
        self.setStyleSheet(f"background-color: {BG_APP};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.lbl_img = QLabel()
        self.lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img.setPixmap(pixmap) 
        
        self.scroll.setWidget(self.lbl_img)
        layout.addWidget(self.scroll)
        
        self.btn_close = QPushButton("✕", self)
        self.btn_close.setFixedSize(40, 40)
        self.btn_close.move(940, 20)
        self.btn_close.setStyleSheet("background: rgba(0,0,0,0.5); color: white; border-radius: 20px; font-size: 18px;")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)

class MessageBubble(QWidget):
    def __init__(self, data, parent_win=None):
        super().__init__()
        self.data = data # Dữ liệu này sẽ được ChatArea cập nhật
        self.parent_win = parent_win 
        self.is_me = data.get('is_me', False)
        self.sender_name = data.get('sender', 'Unknown')
        self.bus = SignalBus.get()
        self.init_ui()

    def get_clean_filename(self, raw_name):
        """Làm sạch tên file hiển thị"""
        if not raw_name: return "File"
        # Regex: 12345_tenfile.ext -> tenfile.ext
        match = re.match(r"^\d+_(.+)$", raw_name)
        if match: return match.group(1)
        return raw_name

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(10)

        # 1. Avatar
        self.avt = None
        if not self.is_me:
            self.avt = AvatarWidget(38, self.sender_name)
            layout.addWidget(self.avt, alignment=Qt.AlignmentFlag.AlignTop)
            if self.data.get('avatar_data'):
                self.update_avatar_display(self.data.get('avatar_data'))
        else:
            layout.addStretch()

        # 2. Content
        content_container = QWidget()
        cc_layout = QVBoxLayout(content_container)
        cc_layout.setContentsMargins(0, 0, 0, 0)
        cc_layout.setSpacing(4)

        if not self.is_me:
            self.lbl_name = QLabel(self.sender_name)
            self.lbl_name.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11px; font-weight: bold; margin-left: 2px;")
            cc_layout.addWidget(self.lbl_name)

        # 3. Bubble Frame
        bubble = QFrame()
        bg_color = ME_BUBBLE if self.is_me else THEM_BUBBLE
        msg_type = self.data.get('type')
        if msg_type in ["upload_progress", "download_progress"]:
            bg_color = "#202225"
            
        radius = "18px 18px 2px 18px" if self.is_me else "2px 18px 18px 18px"
        bubble.setStyleSheet(f"background-color: {bg_color}; border-radius: {radius};")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10); shadow.setColor(QColor(0,0,0,40)); shadow.setOffset(0, 2)
        bubble.setGraphicsEffect(shadow)

        b_lay = QVBoxLayout(bubble)
        b_lay.setContentsMargins(14, 10, 14, 10)

        # 4. Render
        if msg_type == 'history': msg_type = self.data.get('content_type', 'text')
        
        if msg_type == "text": self._render_text(b_lay)
        elif msg_type == "image": self._render_image(b_lay)
        elif msg_type == "file": self._render_file_download(b_lay)
        elif msg_type == "upload_progress": self._render_upload_progress(b_lay)
        elif msg_type == "download_progress": self._render_download_progress(b_lay)

        cc_layout.addWidget(bubble)
        layout.addWidget(content_container)
        
        if not self.is_me: layout.addStretch()

    def _render_text(self, layout):
        lbl = QLabel(self.data.get('content'))
        lbl.setWordWrap(True); lbl.setMaximumWidth(550)
        lbl.setStyleSheet("background: transparent; font-size: 15px; color: white; border: none;")
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(lbl)

    def _render_image(self, layout):
        pixmap = None
        qimg = self.data.get("qimage")
        if qimg and isinstance(qimg, QImage) and not qimg.isNull():
            pixmap = QPixmap.fromImage(qimg)
        elif self.data.get('content') and not str(self.data.get('content')).startswith("[IMAGE]:"):
             pixmap = QPixmap(self.data.get('content'))

        if pixmap and not pixmap.isNull():
            thumb = pixmap.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            btn_img = QPushButton()
            btn_img.setIcon(QIcon(thumb)); btn_img.setIconSize(thumb.size())
            btn_img.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_img.setStyleSheet("border: none; background: transparent; border-radius: 8px;")
            btn_img.clicked.connect(lambda: ImageViewer(pixmap, self.window()).show())
            layout.addWidget(btn_img)
        else:
            lbl = QLabel("🖼️ [Ảnh]"); layout.addWidget(lbl)

    def _render_upload_progress(self, layout):
        raw_name = self.data.get("filename", "File")
        clean_name = self.get_clean_filename(raw_name)
        
        h_layout = QHBoxLayout()
        lbl = QLabel(f"📤 Đang gửi: {clean_name}")
        lbl.setStyleSheet("color: #eeeeee; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        h_layout.addWidget(lbl); h_layout.addStretch()
        
        btn_cancel = QPushButton("✖")
        btn_cancel.setFixedSize(20, 20); btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("QPushButton { background: transparent; color: #FF5555; font-weight: bold; border: none; } QPushButton:hover { background: rgba(255, 85, 85, 0.2); border-radius: 10px; }")
        btn_cancel.clicked.connect(lambda: self.bus.ui_cancel_upload.emit(raw_name))
        h_layout.addWidget(btn_cancel)
        layout.addLayout(h_layout)
        
        self.pbar = QProgressBar(); self.pbar.setRange(0, 100); self.pbar.setValue(0); self.pbar.setFixedHeight(6); self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet(f"QProgressBar {{ border: none; background-color: rgba(0, 0, 0, 0.3); border-radius: 3px; }} QProgressBar::chunk {{ background-color: {PRIMARY}; border-radius: 3px; }}")
        layout.addWidget(self.pbar)
        
        self.lbl_percent = QLabel("0%"); self.lbl_percent.setStyleSheet("color: #aaaaaa; font-size: 10px; background: transparent; margin-top: 2px; border: none;")
        self.lbl_percent.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.lbl_percent)

    def _render_download_progress(self, layout):
        raw_name = self.data.get("filename", "File")
        clean_name = self.get_clean_filename(raw_name)
        
        h_layout = QHBoxLayout()
        lbl = QLabel(f"📥 Đang tải: {clean_name}")
        lbl.setStyleSheet("color: #eeeeee; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        h_layout.addWidget(lbl); h_layout.addStretch()
        
        btn_cancel = QPushButton("✖")
        btn_cancel.setFixedSize(20, 20); btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("QPushButton { background: transparent; color: #FF5555; font-weight: bold; border: none; } QPushButton:hover { background: rgba(255, 85, 85, 0.2); border-radius: 10px; }")
        btn_cancel.clicked.connect(lambda: self.bus.ui_cancel_download.emit(raw_name))
        h_layout.addWidget(btn_cancel)
        layout.addLayout(h_layout)
        
        self.pbar = QProgressBar(); self.pbar.setRange(0, 100); self.pbar.setValue(0); self.pbar.setFixedHeight(6); self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet(f"QProgressBar {{ border: none; background-color: rgba(0, 0, 0, 0.3); border-radius: 3px; }} QProgressBar::chunk {{ background-color: #2ecc71; border-radius: 3px; }}")
        layout.addWidget(self.pbar)
        
        self.lbl_percent = QLabel("0%"); self.lbl_percent.setStyleSheet("color: #aaaaaa; font-size: 10px; background: transparent; margin-top: 2px; border: none;")
        self.lbl_percent.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.lbl_percent)

    def _render_file_download(self, layout):
        # Lấy tên file ban đầu (có thể là tên local hoặc tên server)
        # Quan trọng: UI chỉ hiển thị clean_name
        current_fname = self.data.get("filename", "File")
        
        # Parse tên file từ content nếu cần
        if current_fname == "File" and self.data.get('content'):
            c = str(self.data.get('content'))
            if c.startswith("[FILE]:"):
                try: current_fname = c[7:].split('|')[0]
                except: pass
            else:
                current_fname = os.path.basename(c)

        clean_name = self.get_clean_filename(current_fname)

        file_frame = QFrame()
        file_frame.setStyleSheet(f"background: rgba(0,0,0,0.15); border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);")
        ff_lay = QHBoxLayout(file_frame)
        
        icon_file = QLabel("📄")
        icon_file.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        
        # Hiển thị tên sạch (không đuôi số)
        name_file = QLabel(clean_name)
        name_file.setStyleSheet("font-weight: 600; color: white; background: transparent; border: none;")
        
        ff_lay.addWidget(icon_file)
        ff_lay.addWidget(name_file)
        ff_lay.addStretch()
        
        btn_dl = QPushButton("⬇")
        btn_dl.setFixedSize(32, 32)
        btn_dl.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dl.setStyleSheet(f"""
            QPushButton {{ background: {BG_INPUT}; color: white; border-radius: 16px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1); }}
            QPushButton:hover {{ background: {PRIMARY}; }}
        """)
        
        # [QUAN TRỌNG] Không truyền tham số vào save_file
        # Để hàm tự đọc self.data['filename'] mới nhất (do ChatArea cập nhật)
        btn_dl.clicked.connect(self.save_file)
        
        ff_lay.addWidget(btn_dl)
        layout.addWidget(file_frame)

    def update_userdata(self, username, avatar_b64):
        if self.sender_name == username and self.avt:
            self.update_avatar_display(avatar_b64)

    def update_avatar_display(self, avatar_b64):
        if avatar_b64 and self.avt:
            self.avt.set_image_from_b64_async(avatar_b64)

    def update_progress(self, percent, bytes_sent, total_bytes):
        if hasattr(self, 'pbar'): 
            self.pbar.setValue(percent)
            if hasattr(self, 'lbl_percent'): self.lbl_percent.setText(f"{percent}%")

    def save_file(self):
        """Hàm xử lý khi bấm tải xuống"""
        # [DYNAMIC READ] Luôn đọc tên file mới nhất từ self.data
        # Khi ChatArea nhận tin từ Server, nó sẽ update self.data['filename'] thành tên có số
        server_filename = self.data.get("filename", "downloaded_file")
        
        # Nếu chưa có filename chuẩn, thử parse
        if server_filename == "downloaded_file" and self.data.get('content'):
             c = str(self.data.get('content'))
             if c.startswith("[FILE]:"):
                 try: server_filename = c[7:].split('|')[0]
                 except: pass

        # Gợi ý tên đẹp (bỏ số)
        suggested_name = self.get_clean_filename(server_filename)

        file_data_b64 = self.data.get("data")
        
        if file_data_b64:
            save_path, _ = QFileDialog.getSaveFileName(self, "Lưu file", suggested_name)
            if save_path:
                try:
                    with open(save_path, "wb") as f: f.write(base64.b64decode(file_data_b64))
                    QMessageBox.information(self, "Thành công", f"Đã lưu file: {os.path.basename(save_path)}")
                except Exception as e:
                    QMessageBox.warning(self, "Lỗi", "Không thể lưu file!")
        else:
            # Gửi tên file server (có số) để tải
            print(f"[BUBBLE] Requesting download for: {server_filename}")
            SignalBus.get().ui_download_file.emit(server_filename)