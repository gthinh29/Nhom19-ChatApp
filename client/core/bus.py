from PyQt6.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    """
    EventBus hoạt động như một trung tâm liên lạc (Singleton).
    Giúp các thành phần UI và Network giao tiếp mà không cần tham chiếu trực tiếp.
    """
    _instance = None

    # --- Định nghĩa các Tín hiệu (Signals) ---
    # Tín hiệu mạng
    network_connected = pyqtSignal()
    network_disconnected = pyqtSignal(str) # str: Lý do
    
    # Tín hiệu xác thực
    login_success = pyqtSignal(dict) # dict: {user_id, username, display_name}
    login_failed = pyqtSignal(str)   # str: Lỗi
    register_success = pyqtSignal(str)
    register_failed = pyqtSignal(str)

    # Tín hiệu chat
    message_received = pyqtSignal(object) # Message object hoặc dict

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            # Gọi init của QObject đúng cách cho singleton
            super(EventBus, cls._instance).__init__()
        return cls._instance

# Biến toàn cục để import dễ dàng
bus = EventBus()