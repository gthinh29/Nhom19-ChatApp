import threading
import time
from PyQt6.QtCore import QObject
from common.protocol import CMD_PING, CMD_PONG
from client.network.network_client import network_client
from client.core.bus import bus

class ConnectionManager(QObject):
    """
    Quản lý duy trì kết nối (Heartbeat).
    Gửi PING mỗi 10 giây.
    """
    def __init__(self):
        super().__init__()
        self.running = False
        self.ping_thread = None
        self.INTERVAL = 10 # Giây

        # Lắng nghe sự kiện kết nối thành công để bắt đầu PING
        bus.network_connected.connect(self.start_heartbeat)
        bus.network_disconnected.connect(self.stop_heartbeat)

    def start_heartbeat(self):
        if self.running: return
        self.running = True
        self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self.ping_thread.start()
        print("[HEARTBEAT] Started.")

    def stop_heartbeat(self, reason=""):
        self.running = False
        print("[HEARTBEAT] Stopped.")

    def _ping_loop(self):
        """Gửi PING định kỳ"""
        while self.running and network_client.client_socket:
            try:
                network_client.send_packet(CMD_PING, "")
                # Chờ 10s trước khi gửi tiếp
                time.sleep(self.INTERVAL)
            except Exception as e:
                print(f"[HEARTBEAT ERROR] {e}")
                break

# Khởi tạo singleton
connection_manager = ConnectionManager()