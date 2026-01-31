"""Hằng số giao thức, cấu hình mạng và định nghĩa lệnh."""

import configparser
import os


class Protocol:
    """Lớp chứa tất cả các hằng số giao thức, cấu hình mạng và định nghĩa lệnh"""
    
    # Tải cấu hình từ config.ini
    _config = configparser.ConfigParser()
    _config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
    if os.path.exists(_config_path):
        _config.read(_config_path)
    
    # ==================== CẤU HÌNH MẠNG (từ config.ini) ====================
    HOST = _config.get('server', 'HOST', fallback='0.0.0.0')
    PORT = _config.getint('server', 'PORT', fallback=12345)
    WEB_PORT = _config.getint('server', 'WEB_PORT', fallback=8080)
    BROADCAST_PORT = _config.getint('server', 'BROADCAST_PORT', fallback=50000)
    LENGTH_PREFIX_SIZE = 4              # Byte đầu tiên chứa độ dài gói tin (struct.pack('!I', length))
    
    # ==================== LỆNH XÁC THỰC ====================
    LOGIN = "LOGIN"                     # Đăng nhập với username/password
    REGISTER = "REGISTER"               # Đăng ký tài khoản mới
    FORGOT_PW = "FORGOT_PW"             # Yêu cầu khôi phục mật khẩu (OTP)
    RESET_PASSWORD = "RESET_PASSWORD"   # Yêu cầu đổi mật khẩu (user đã đăng nhập)
    CONFIRM_RESET = "CONFIRM_RESET"     # Xác nhận và đặt mật khẩu mới
    UPDATE_PROFILE = "UPDATE_PROFILE"   # Cập nhật thông tin tài khoản (tên, avatar)
    
    # ==================== LỆNH TRÒ CHUYỆN ====================
    MSG = "MSG"                         # Gửi tin nhắn văn bản
    IMAGE = "IMAGE"                     # Gửi ảnh
    
    # Lệnh File (Upload & Download đa kênh)
    FILE = "FILE"                       # Tin nhắn thông báo file
    
    # --- Upload ---
    UPLOAD_REQ = "UPLOAD_REQ"           # Yêu cầu cấp quyền upload
    UPLOAD_RESP = "UPLOAD_RESP"         # Server trả về Token upload
    FILE_STREAM = "FILE_STREAM"         # Handshake upload (Client -> Server)
    
    # --- Download ---
    DOWNLOAD_REQ = "DOWNLOAD_REQ"       # Yêu cầu tải file (Gửi qua Chat Socket)
    DOWNLOAD_RESP = "DOWNLOAD_RESP"     # Server trả về Token + Size (Gửi qua Chat Socket)
    FILE_DOWNLOAD_STREAM = "FILE_DOWNLOAD_STREAM" # Handshake download (Client -> Server Data Socket)
    
    GET_PENDING_FILES = "GET_PENDING_FILES"  # Lấy danh sách file đang upload/pending
    CANCEL_FILE = "CANCEL_FILE"         # Hủy upload file (format: CANCEL_FILE|fileid)
    EXPORT_CHAT = "EXPORT_CHAT"         # Xuất lịch sử chat ra Email
    HISTORY = "HISTORY"                 # Lấy lịch sử tin nhắn (khi đăng nhập hoặc cuộn lên)
    
    # ==================== LỆNH QUẢN LÝ TRẠNG THÁI ====================
    ONLINE_LIST = "ONLINE_LIST"         # Gửi danh sách user đang online
    USER_STATUS = "USER_STATUS"         # Thông báo user vào/rời phòng chat
    FORCE_LOGOUT = "FORCE_LOGOUT"       # Đẩy user ra ngoài (đăng nhập ở chỗ khác)
    
    # ==================== PHẢN HỒI ====================
    SUCCESS = "SUCCESS"                 # Thành công
    ERROR = "ERROR"                     # Lỗi