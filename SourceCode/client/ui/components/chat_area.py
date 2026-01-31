"""
Chat Area - Khu vực hiển thị tin nhắn
[FINAL COMPLETE]
1. Fix lỗi hiển thị 2 bong bóng (Duplicate Check bằng Clean Filename).
2. Tự động cập nhật ID Server (Timestamp) cho bong bóng Local của người gửi.
3. Hỗ trợ Resume/Cancel cho cả Upload và Download.
4. [FIXED] Smart Swap: Xóa bong bóng ảo chính xác dù Server trả về tên có Timestamp.
"""
import re 
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QWidget, QPushButton
from PyQt6.QtCore import Qt, QTimer
from client.ui.styles import BG_APP, BG_SIDEBAR, TEXT_SUB
from client.ui.widgets import MessageBubble
from client.core.bus import SignalBus

class ChatArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG_APP};")
        
        self.avatar_cache = {} 
        self.active_upload_bubbles = {}   
        self.active_download_bubbles = {} 
        self.processed_local_files = set()
        self.resume_widgets = {} 
        
        # Map để tìm lại bong bóng Local của mình: 'clean_name.pdf' -> MessageBubble Object
        self.pending_file_bubbles = {} 
        
        self.request_history_callback = None
        self.init_ui()
        self.setup_signals()
        
        # Yêu cầu danh sách file treo khi khởi tạo
        QTimer.singleShot(500, lambda: SignalBus.get().ui_request_pending_files.emit())

    def setup_signals(self):
        bus = SignalBus.get()
        # Upload Signals
        bus.file_upload_start.connect(self.add_upload_bubble)
        bus.file_upload_progress.connect(self.update_upload_progress)
        bus.file_upload_completed_msg.connect(self.on_upload_complete_local) 
        
        # Download Signals
        bus.file_download_start.connect(self.add_download_bubble)
        bus.file_download_progress.connect(self.update_download_progress)
        bus.file_download_complete.connect(self.on_download_complete)
        
        # Resume/Cancel Signals
        bus.file_pending_restore.connect(self.add_resume_bubble)
        bus.ui_cancel_upload.connect(self.on_gui_cancel_upload)
        bus.ui_cancel_download.connect(self.on_gui_cancel_download)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        
        head = QFrame()
        head.setFixedHeight(50)
        head.setStyleSheet(f"background-color: {BG_APP}; border-bottom: 2px solid {BG_SIDEBAR};")
        hl = QHBoxLayout(head); hl.setContentsMargins(20,0,20,0); hl.setSpacing(10)
        hl.addWidget(QLabel("#", styleSheet=f"font-size: 24px; color: {TEXT_SUB}; font-weight: 300;"))
        hl.addWidget(QLabel("sảnh-chính", styleSheet="font-size: 18px; font-weight: bold;"))
        hl.addStretch()
        search = QLineEdit(); search.setPlaceholderText("Tìm kiếm...")
        search.setFixedSize(200, 30)
        search.setStyleSheet(f"background-color: {BG_SIDEBAR}; border-radius: 4px; padding-left: 10px; font-size: 12px;")
        hl.addWidget(search)
        layout.addWidget(head)

        self.lbl_status_bar = QLabel("⚠️ Mất kết nối đến Server! Đang thử kết nối lại...")
        self.lbl_status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status_bar.setStyleSheet(f"background-color: #DA373C; color: white; font-weight: bold; padding: 5px;")
        self.lbl_status_bar.hide()
        layout.addWidget(self.lbl_status_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }") 
        self.msg_con = QWidget()
        self.mlay = QVBoxLayout(self.msg_con)
        self.mlay.setSpacing(20); self.mlay.setContentsMargins(30, 20, 30, 20)
        self.mlay.addStretch() 
        self.lbl_loading = QLabel("⟳ Đang tải tin nhắn...")
        self.lbl_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading.setStyleSheet(f"color: {TEXT_SUB}; font-style: italic; font-size: 12px; margin: 10px;")
        self.lbl_loading.hide() 
        self.mlay.addWidget(self.lbl_loading, alignment=Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.msg_con)
        self.scroll.verticalScrollBar().valueChanged.connect(self._check_scroll)
        layout.addWidget(self.scroll)

    def get_clean_filename(self, raw_name):
        """Lọc tên file: 12345_abc.txt -> abc.txt"""
        if not raw_name: return ""
        match = re.match(r"^\d+_(.+)$", raw_name)
        if match: return match.group(1)
        return raw_name

    def set_connection_lost(self, lost):
        if lost: self.lbl_status_bar.show()
        else: self.lbl_status_bar.hide()

    def show_loading(self, show, text="⟳ Đang tải tin nhắn..."):
        self.lbl_loading.setText(text)
        if show: self.lbl_loading.show()
        else: self.lbl_loading.hide()

    def update_avatar_cache(self, username, b64):
        self.avatar_cache[username] = b64

    # ================== GUI CANCEL HANDLERS ==================
    def on_gui_cancel_upload(self, filename):
        self.remove_upload_bubble(filename)
        if filename in self.resume_widgets: self._on_click_cancel_resume(filename, self.resume_widgets[filename], True)

    def on_gui_cancel_download(self, filename):
        self.remove_download_bubble(filename)
        if filename in self.resume_widgets: self._on_click_cancel_resume(filename, self.resume_widgets[filename], False)

    # ================== MAIN ADD BUBBLE ==================
    def add_bubble(self, data):
        """Thêm tin nhắn từ Server - Cập nhật bong bóng Local nếu trùng"""
        try:
            msg_type = data.get('type')
            is_me = data.get('is_me')
            server_fname = data.get('filename')
            
            # Extract filename nếu thiếu
            if not server_fname and msg_type == "file":
                c = str(data.get('content'))
                if c.startswith("[FILE]:"):
                    try: server_fname = c[7:].split('|')[0]
                    except: pass

            if is_me and msg_type in ("file", "image") and server_fname:
                clean_name = self.get_clean_filename(server_fname)

                # 0. Nếu đã xử lý trước đó, bỏ qua
                if clean_name in self.processed_local_files:
                    return

                # 1. Nếu bong bóng Local đang chờ xác nhận
                if clean_name in self.pending_file_bubbles:
                    print(f"[UI] Matching Server response for: {server_fname}")
                    bubble_widget = self.pending_file_bubbles.pop(clean_name)
                    bubble_widget.data['filename'] = server_fname
                    if hasattr(bubble_widget, 'refresh_ui'):
                        bubble_widget.refresh_ui()
                    self.processed_local_files.add(clean_name)
                    return

                # 2. Nếu đang có bong bóng upload progress, chuyển nó thành bong bóng file hoàn chỉnh
                if clean_name in self.active_upload_bubbles:
                    print(f"[UI] Converting upload-progress bubble to final for: {server_fname}")
                    old = self.active_upload_bubbles.pop(clean_name)
                    try:
                        old.hide(); self.mlay.removeWidget(old); old.deleteLater()
                    except: pass

                    # Tạo bong bóng file thực tế (hiển thị tên sạch cho sender, lưu filename server)
                    data['is_me'] = True
                    data['filename'] = server_fname
                    self._enrich_user_data(data)
                    b = MessageBubble(data, self)
                    # Đánh dấu đã xử lý để tránh bong bóng kép khi local on_upload_complete được gọi sau
                    self.processed_local_files.add(clean_name)
                    self.mlay.addWidget(b)
                    QTimer.singleShot(100, self._safe_scroll_to_bottom)
                    return

                # 3. Smart Swap: Xóa bong bóng loading cũ (nếu tồn tại tên raw)
                self.remove_upload_bubble(server_fname)
                    
        except Exception as e: print(f"[UI ERROR] add_bubble: {e}")
        
        self._enrich_user_data(data)
        b = MessageBubble(data, self)
        self.mlay.addWidget(b)
        QTimer.singleShot(100, self._safe_scroll_to_bottom)

    # ================== UPLOAD COMPLETE (LOCAL) ==================
    def on_upload_complete_local(self, msg_data):
        """Khi upload xong: Vẽ bong bóng file Local (chứa tên gốc)"""
        fname = msg_data.get('filename') # Đây là Server Filename (có timestamp)
        # Nếu đã được server xử lý và chuyển bubble trước đó, bỏ qua
        clean_name = self.get_clean_filename(fname)
        if clean_name in self.processed_local_files:
            # Dọn các state tạm nếu cần
            try:
                self.remove_upload_bubble(fname)
            except: pass
            if fname in self.resume_widgets:
                try: w = self.resume_widgets.pop(fname); w.deleteLater()
                except: pass
            return

        # [SMART REMOVE] Xóa bong bóng loading (đang dùng key Clean Name)
        self.remove_upload_bubble(fname)

        if fname in self.resume_widgets:
            w = self.resume_widgets.pop(fname); w.deleteLater()

        self._enrich_user_data(msg_data)
        b = MessageBubble(msg_data, self)

        # Lưu vào map chờ Server xác nhận tên thật
        if clean_name:
            self.pending_file_bubbles[clean_name] = b
            self.processed_local_files.add(clean_name)
            if len(self.processed_local_files) > 50: self.processed_local_files.pop()

        self.mlay.addWidget(b)
        QTimer.singleShot(100, self._safe_scroll_to_bottom)

    # ================== RESUME BUBBLE ==================
    def add_resume_bubble(self, filename, path, percent, is_upload):
        if filename in self.resume_widgets: return 
        if is_upload and filename in self.active_upload_bubbles: return 
        if not is_upload and filename in self.active_download_bubbles: return

        clean_name = self.get_clean_filename(filename)
        container = QFrame()
        container.setStyleSheet(f"background-color: {BG_SIDEBAR}; border-radius: 8px; border: 1px solid #FFD700;")
        container.setFixedHeight(60)
        cl = QHBoxLayout(container)
        cl.setContentsMargins(10, 5, 10, 5)
        
        type_str = "Upload" if is_upload else "Download"
        icon_str = "📤" if is_upload else "📥"
        info = QLabel(f"{icon_str} <b>{clean_name}</b><br><i style='color:#AAA'>{type_str} tạm dừng</i>")
        info.setStyleSheet("color: white; font-size: 12px;")
        
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setFixedSize(60, 30)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("QPushButton { background-color: #DA373C; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #A0282C; }")
        btn_cancel.clicked.connect(lambda: self._on_click_cancel_resume(filename, container, is_upload))

        btn_resume = QPushButton("Tiếp tục")
        btn_resume.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_resume.setFixedSize(80, 30)
        btn_resume.setStyleSheet("QPushButton { background-color: #5865F2; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #4752C4; }")
        btn_resume.clicked.connect(lambda: self._on_click_resume(filename, path, container, is_upload))
        
        cl.addWidget(info); cl.addStretch(); cl.addWidget(btn_cancel); cl.addWidget(btn_resume)
        self.mlay.addWidget(container)
        self.resume_widgets[filename] = container
        QTimer.singleShot(100, self._safe_scroll_to_bottom)

    def _on_click_resume(self, filename, path, widget, is_upload):
        widget.hide() 
        if is_upload: SignalBus.get().ui_send_file.emit(path)
        else: SignalBus.get().ui_resume_download.emit(filename, path)

    def _on_click_cancel_resume(self, filename, widget, is_upload):
        widget.hide(); self.mlay.removeWidget(widget); widget.deleteLater()
        if filename in self.resume_widgets: del self.resume_widgets[filename]
        if is_upload: SignalBus.get().ui_cancel_upload.emit(filename)
        else: SignalBus.get().ui_cancel_download.emit(filename)

    # ================== UPLOAD BUBBLES ==================
    def add_upload_bubble(self, filename, total_bytes, sender_name, is_me):
        # [SMART] Đảm bảo không trùng bong bóng resume
        if filename in self.resume_widgets:
            try: w = self.resume_widgets.pop(filename); w.deleteLater()
            except: pass
        
        # [SMART] Xóa bong bóng cũ nếu có (dùng clean name check)
        self.remove_upload_bubble(filename)
        
        data = {"sender": sender_name, "is_me": is_me, "type": "upload_progress", "filename": filename, "percent": 0, "total_bytes": total_bytes}
        self._enrich_user_data(data)
        b = MessageBubble(data, self)
        self.active_upload_bubbles[filename] = b
        self.mlay.addWidget(b)
        QTimer.singleShot(100, self._safe_scroll_to_bottom)

    def update_upload_progress(self, filename, percent):
        if filename in self.active_upload_bubbles:
            bubble = self.active_upload_bubbles[filename]
            if hasattr(bubble, 'update_progress'): bubble.update_progress(percent, 0, 0)

    def remove_upload_bubble(self, filename):
        """[SMART REMOVE] Xóa bong bóng theo tên chính xác HOẶC tên clean"""
        try:
            # Case 1: Tên chính xác
            if filename in self.active_upload_bubbles:
                old = self.active_upload_bubbles.pop(filename)
                old.hide(); self.mlay.removeWidget(old); old.deleteLater()
                return

            # Case 2: Tìm theo Clean Name (nếu Server gửi tên có timestamp nhưng UI đang lưu tên clean)
            clean = self.get_clean_filename(filename)
            if clean in self.active_upload_bubbles:
                old = self.active_upload_bubbles.pop(clean)
                old.hide(); self.mlay.removeWidget(old); old.deleteLater()
        except: pass

    # ================== DOWNLOAD BUBBLES ==================
    def add_download_bubble(self, filename, total_bytes):
        if filename in self.active_download_bubbles: self.remove_download_bubble(filename)
        data = {"sender": "System", "is_me": True, "type": "download_progress", "filename": filename, "percent": 0, "total_bytes": total_bytes}
        b = MessageBubble(data, self)
        self.active_download_bubbles[filename] = b
        self.mlay.addWidget(b)
        QTimer.singleShot(100, self._safe_scroll_to_bottom)

    def update_download_progress(self, filename, percent):
        if filename in self.active_download_bubbles:
            bubble = self.active_download_bubbles[filename]
            if hasattr(bubble, 'update_progress'): bubble.update_progress(percent, 0, 0)

    def on_download_complete(self, filename, save_path):
        self.remove_download_bubble(filename)

    def remove_download_bubble(self, filename):
        try:
            if filename in self.active_download_bubbles:
                old = self.active_download_bubbles.pop(filename)
                old.hide(); self.mlay.removeWidget(old); old.deleteLater()
        except: pass

    # ================== HELPERS ==================
    def add_history_bubble(self, data):
        self._enrich_user_data(data)
        b = MessageBubble(data, self)
        self.mlay.insertWidget(2, b)
        self._maintain_scroll_pos()

    def _enrich_user_data(self, data): pass
    def _check_scroll(self, value):
        if value <= 5 and self.request_history_callback: self.request_history_callback()
    def _maintain_scroll_pos(self):
        try:
            bar = self.scroll.verticalScrollBar()
            prev_max = bar.maximum()
            def restore():
                try:
                    if self.scroll:
                        curr = self.scroll.verticalScrollBar()
                        curr.setValue(curr.value() + (curr.maximum() - prev_max))
                except: pass
            QTimer.singleShot(0, restore)
        except: pass
    def _safe_scroll_to_bottom(self):
        try:
            if self.scroll:
                self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        except: pass