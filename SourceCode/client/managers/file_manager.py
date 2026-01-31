"""Quản lý upload/download, resume và lưu trạng thái file tạm thời."""

import os
import time
import json
import base64
import threading
import socket
import ssl
import struct
import re
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QFileDialog, QApplication
from common.protocol import Protocol
from client.core.bus import SignalBus

class UploadThread(QThread):
    finished_signal = pyqtSignal()
    def __init__(self, func, *args):
        super().__init__()
        self.func = func; self.args = args
    def run(self):
        try: self.func(*self.args)
        except Exception as e: print(f"[Thread Error] {e}")
        self.finished_signal.emit()

class FileManager(QObject):
    def __init__(self, network_client):
        super().__init__()
        self.net = network_client
        self.bus = SignalBus.get()
        self.file_upload_lock = threading.Lock() 
        self._temp_workers = []
        self._shutdown = False
        
        self._token_waiters = {}
        self._download_waiters = {} 
        self.abort_set = set()
        self.pending_store_file = "pending_uploads.json"

        self.bus.ui_send_file.connect(self.send_file)
        self.bus.ui_send_image.connect(self.send_image)
        
        self.bus.ui_download_file.connect(self.download_file) 
        self.bus.ui_resume_download.connect(self.resume_download)
        
        self.bus.ui_cancel_upload.connect(self.cancel_file_upload)
        self.bus.ui_cancel_download.connect(self.cancel_file_download)
        
        self.bus.network_packet_received.connect(self.on_packet_received)
        self.bus.ui_request_pending_files.connect(self.load_pending_uploads)

    # Hàm lọc bỏ số timestamp (12345_file.pdf -> file.pdf)
    def get_clean_filename(self, raw_name):
        if not raw_name: return "downloaded_file"
        match = re.match(r"^\d+_(.+)$", raw_name)
        if match:
            return match.group(1)
        return raw_name

    # ================== CANCEL LOGIC ==================
    def cancel_file_upload(self, filename):
        print(f"[MANAGER] Canceling upload: {filename}")
        self.abort_set.add(filename)
        self.remove_pending_record(filename)
        # Gửi lệnh hủy (Server sẽ tìm file temp tương ứng)
        self.net.send_packet(f"CANCEL_FILE|{filename}")
        self.bus.file_upload_done.emit(f"Đã hủy gửi: {filename}")

    def cancel_file_download(self, filename):
        print(f"[MANAGER] Canceling download: {filename}")
        self.abort_set.add(filename)
        self.remove_pending_record(filename) 
        self.bus.file_download_complete.emit(filename, "")
        self.bus.file_upload_done.emit(f"Đã hủy tải: {filename}")

    # ================== PERSISTENCE ==================
    def load_pending_uploads(self):
        if not os.path.exists(self.pending_store_file): return
        try:
            with open(self.pending_store_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for fname, info in data.items():
                if isinstance(info, dict):
                    path = info.get('path')
                    ftype = info.get('type', 'upload')
                    # Với download, file có thể chưa tồn tại hoặc tồn tại 1 phần, vẫn hiện resume
                    if (path and os.path.exists(path)) or ftype == 'download':
                        is_upload = (ftype == 'upload')
                        self.bus.file_pending_restore.emit(fname, path, 0, is_upload)
                    else:
                        self.remove_pending_record(fname)
        except: pass

    def save_pending_record(self, filename, path, is_upload=True):
        try:
            data = {}
            if os.path.exists(self.pending_store_file):
                with open(self.pending_store_file, 'r', encoding='utf-8') as f:
                    try: data = json.load(f)
                    except: pass
            data[filename] = {'path': path, 'time': time.time(), 'type': 'upload' if is_upload else 'download'}
            with open(self.pending_store_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except: pass

    def remove_pending_record(self, filename):
        if not os.path.exists(self.pending_store_file): return
        try:
            with open(self.pending_store_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if filename in data:
                del data[filename]
                with open(self.pending_store_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
        except: pass

    # ================== START ACTIONS ==================
    def send_image(self, path):
        if not self.net.is_connected: return
        w = UploadThread(self._do_send_image, path)
        w.finished_signal.connect(lambda: self.bus.file_upload_done.emit("Ảnh đã gửi"))
        w.start(); self._temp_workers.append(w)

    def send_file(self, path):
        if not self.net.is_connected: 
            self.bus.file_upload_done.emit("Lỗi: Chưa kết nối")
            return
            
        # [FIX 1] Sanitize: Thay thế ký tự '|' bằng '_' để tránh hỏng giao thức
        # Đây cũng chính là ui_key để định danh bong bóng chat
        fname = os.path.basename(path).replace("|", "_")
        
        if fname in self.abort_set: self.abort_set.remove(fname)
        
        self.save_pending_record(fname, path, is_upload=True)
        self.bus.file_upload_start.emit(fname, os.path.getsize(path), getattr(self.net, 'username', ''), True)
        
        # Truyền fname (ui_key) vào worker
        w = UploadThread(self._do_send_file_raw, path, fname)
        w.start(); self._temp_workers.append(w)

    def download_file(self, filename):
        """
        filename: Tên file trên server (có số, ví dụ: 12345_baocao.pdf)
        """
        if not self.net.is_connected: return
        
        # [UI FIX] Gợi ý tên đẹp cho người dùng (bỏ số)
        clean_name = self.get_clean_filename(filename)
        
        save_path, _ = QFileDialog.getSaveFileName(QApplication.activeWindow(), "Lưu file", clean_name)
        if not save_path: return

        if filename in self.abort_set: self.abort_set.remove(filename)
        
        # Lưu key là filename gốc (có số) để khớp với logic server
        self.save_pending_record(filename, save_path, is_upload=False)
        
        self.bus.file_download_start.emit(filename, 0)
        
        w = UploadThread(self._do_download_file_raw, filename, save_path)
        w.start(); self._temp_workers.append(w)

    def resume_download(self, filename, save_path):
        """[NEW] Tải tiếp (Không mở hộp thoại)"""
        if not self.net.is_connected: return
        if filename in self.abort_set: self.abort_set.remove(filename)
        
        self.save_pending_record(filename, save_path, is_upload=False)
        self.bus.file_download_start.emit(filename, 0)
        
        w = UploadThread(self._do_download_file_raw, filename, save_path)
        w.start(); self._temp_workers.append(w)

    def shutdown(self, wait_ms=2000):
        self._shutdown = True
        for w in list(self._temp_workers):
            try:
                if w.isRunning(): w.wait(wait_ms)
            except: pass
        self._temp_workers.clear()

    # ================== WORKERS ==================
    def _do_send_image(self, path):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            self.net.send_packet(f"{Protocol.IMAGE}|{os.path.basename(path)}|{b64}")
        except: pass

    def _do_send_file_raw(self, path, ui_key=None):
        # ui_key: Tên file sạch dùng để update UI (khớp với send_file)
        # fname: Tên dùng để request upload (có thể giống ui_key)
        fname = ui_key if ui_key else os.path.basename(path).replace("|", "_")
        total = os.path.getsize(path)
        
        # Thêm field 'server_name' để hứng tên file thật từ Server
        waiter = {'event': threading.Event(), 'token': None, 'error': None, 'offset': 0, 'server_name': None}
        
        with self.file_upload_lock: self._token_waiters[fname] = waiter
        self.net.send_packet(f"{Protocol.UPLOAD_REQ}|{fname}|{total}")
        
        if not waiter['event'].wait(15.0):
            self.bus.file_upload_done.emit("Lỗi: Server Timeout.")
            self.bus.file_pending_restore.emit(fname, path, 0, True)
            return
            
        token = waiter['token']
        if not token: 
            error_msg = waiter.get('error', 'Lỗi không xác định')
            self.bus.file_upload_done.emit(f"Lỗi: {error_msg}")
            self.bus.file_pending_restore.emit(fname, path, 0, True)
            return

        if fname in self.abort_set: 
            self.net.send_packet(f"CANCEL_FILE|{fname}")
            return

        # [FIX 2] Lấy tên file thật từ Server (nếu có), nếu không thì dùng tên cũ
        server_filename = waiter.get('server_name') or fname

        # Truyền server_filename vào stream data để upload
        # TRUYỀN ui_key vào để update progress bar đúng bong bóng
        self._stream_data(token, path, total, server_filename, is_upload=True, offset=waiter.get('offset', 0), ui_key=fname)

    def _do_download_file_raw(self, filename, save_path):
        local_offset = os.path.getsize(save_path) if os.path.exists(save_path) else 0
        waiter = {'event': threading.Event(), 'token': None, 'size': 0, 'error': None}
        
        with self.file_upload_lock: self._download_waiters[filename] = waiter
        self.net.send_packet(f"{Protocol.DOWNLOAD_REQ}|{filename}|{local_offset}")
        
        if not waiter['event'].wait(15.0):
            self.bus.file_upload_done.emit(f"Lỗi tải: Server Timeout.")
            self.bus.file_pending_restore.emit(filename, save_path, 0, False)
            return
            
        token = waiter['token']
        
        # [FIX 3] Hiển thị lỗi cụ thể từ Server
        if not token:
            error_msg = waiter.get('error', 'Token không hợp lệ hoặc File bị xóa')
            print(f"[DOWNLOAD ERROR] {error_msg}") 
            self.bus.file_upload_done.emit(f"Lỗi tải: {error_msg}")
            self.bus.file_pending_restore.emit(filename, save_path, 0, False)
            return

        if filename in self.abort_set: return

        self._stream_data(token, save_path, waiter['size'], filename, is_upload=False, offset=local_offset)

    def _stream_data(self, token, path, total_size, filename, is_upload=True, offset=0, ui_key=None):
        """
        filename: 
         - Nếu là Upload: Đây là server_filename (có timestamp)
         - Nếu là Download: Đây là tên file cần tải
        ui_key: (Chỉ dùng cho Upload) Tên file sạch dùng để emit signal update UI
        """
        mode_str = "UPLOAD" if is_upload else "DOWNLOAD"
        sock = None
        # Xác định tên dùng để bắn signal progress
        # Nếu là upload và có ui_key thì dùng ui_key (để khớp bong bóng)
        # Nếu không thì dùng filename (trường hợp download)
        progress_key = ui_key if (is_upload and ui_key) else filename

        try:
            try: server_ip, _ = self.net.client_socket.getpeername()
            except: server_ip = Protocol.HOST
            if server_ip == '0.0.0.0': server_ip = '127.0.0.1'

            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(15.0) 
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(raw_sock, server_hostname=server_ip)
            sock.connect((server_ip, Protocol.PORT))
            
            prefix = Protocol.FILE_STREAM if is_upload else Protocol.FILE_DOWNLOAD_STREAM
            handshake_msg = f"{prefix}|{token}".encode('utf-8')
            sock.sendall(struct.pack('!I', len(handshake_msg)) + handshake_msg)
            
            def read_resp():
                len_b = b""; 
                while len(len_b) < 4:
                    c = sock.recv(4-len(len_b)); 
                    if not c: return None
                    len_b += c
                l = struct.unpack('!I', len_b)[0]
                d = b""; 
                while len(d) < l:
                    c = sock.recv(min(4096, l-len(d)))
                    if not c: return None
                    d += c
                return d.decode('utf-8')

            last_emit_time = 0
            emit_interval = 0.1 

            if is_upload:
                if read_resp() != "READY": 
                    self.bus.file_upload_done.emit(f"Lỗi: Server từ chối.")
                    self.bus.file_pending_restore.emit(progress_key, path, 0, True)
                    return
                sent = offset
                with open(path, 'rb') as f:
                    if offset > 0: f.seek(offset)
                    while sent < total_size:
                        if self._shutdown or progress_key in self.abort_set:
                            print(f"[UPLOAD] Aborted: {progress_key}")
                            return 
                        chunk = f.read(65536)
                        if not chunk: break
                        sock.sendall(chunk)
                        sent += len(chunk)
                        now = time.time()
                        if now - last_emit_time > emit_interval or sent == total_size:
                            percent = int((sent / total_size) * 100) if total_size > 0 else 0
                            self.bus.file_upload_progress.emit(progress_key, percent)
                            last_emit_time = now
                
                if read_resp() == "SUCCESS":
                    self.bus.file_upload_done.emit(f"Đã gửi file {filename}")
                    # Xóa record pending (dùng tên gốc progress_key để xóa đúng record đã save)
                    self.remove_pending_record(progress_key) 
                    
                    # [FIX 2 - QUAN TRỌNG] Gửi message hoàn tất chứa tên file THẬT (có số)
                    # ChatArea sẽ nhận message này, so sánh clean_name và update link download chuẩn
                    msg = {"is_me": True, "sender": getattr(self.net, 'username', 'Me'),
                           "type": "file", "filename": filename, "content": f"[FILE]:{filename}|", "data": ""}
                    self.bus.file_upload_completed_msg.emit(msg)
                else: 
                    self.bus.file_upload_done.emit("Lỗi Upload")
                    self.bus.file_pending_restore.emit(progress_key, path, 0, True)

            else: # DOWNLOAD
                self.bus.file_download_start.emit(filename, total_size)
                received = offset
                mode = 'ab' if offset > 0 else 'wb'
                with open(path, mode) as f:
                    while received < total_size:
                        if self._shutdown or filename in self.abort_set:
                            print(f"[DOWNLOAD] Aborted: {filename}")
                            f.close(); 
                            try: os.remove(path)
                            except: pass
                            return
                        chunk = sock.recv(min(65536, total_size - received))
                        if not chunk: break
                        f.write(chunk)
                        received += len(chunk)
                        now = time.time()
                        if now - last_emit_time > emit_interval or received == total_size:
                            percent = int((received / total_size) * 100) if total_size > 0 else 0
                            self.bus.file_download_progress.emit(filename, percent)
                            last_emit_time = now
                
                self.bus.file_upload_done.emit(f"Đã tải xong: {filename}")
                self.remove_pending_record(filename)
                self.bus.file_download_complete.emit(filename, path)

        except Exception as e:
            print(f"[{mode_str} STREAM ERROR] {e}")
            self.bus.file_upload_done.emit(f"Lỗi Data: {e}")
            if is_upload: 
                if progress_key not in self.abort_set: self.bus.file_pending_restore.emit(progress_key, path, 0, True)
            else: 
                if filename not in self.abort_set: self.bus.file_download_complete.emit(filename, "")
        finally:
            if sock: sock.close()

    def on_packet_received(self, data):
        cmd = data.get("command")
        if cmd == Protocol.UPLOAD_RESP:
            with self.file_upload_lock:
                for k, w in self._token_waiters.items():
                    if not w['event'].is_set():
                        w['token'] = data.get("token")
                        w['offset'] = data.get('offset', 0)
                        # [FIX 2] Nhận tên file thật từ Server (nếu NetworkClient đã parse)
                        w['server_name'] = data.get("final_name")
                        w['event'].set(); break
        elif cmd == Protocol.DOWNLOAD_RESP:
            with self.file_upload_lock:
                for k, w in self._download_waiters.items():
                    if not w['event'].is_set():
                        w['token'] = data.get("token")
                        w['size'] = int(data.get("size", 0))
                        w['event'].set(); break
        elif cmd == Protocol.ERROR:
            msg = data.get("message", "")
            with self.file_upload_lock:
                for w in self._token_waiters.values(): w['error'] = msg; w['event'].set()
                for w in self._download_waiters.values(): w['error'] = msg; w['event'].set()