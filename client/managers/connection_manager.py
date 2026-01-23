"""Quản lý kết nối và tự động kết nối lại (ConnectionManager)."""

import time
import struct
from PyQt6.QtCore import QThread, pyqtSignal
from common.protocol import Protocol
from client.core.bus import SignalBus

class ReconnectThread(QThread):
    """Luồng tự động thử kết nối lại và phát tín hiệu khi thành công."""
    reconnected = pyqtSignal()
    
    def __init__(self, network_client, username, password):
        super().__init__()
        self.net = network_client
        self.username = username
        self.password = password
        self.running = True

    def run(self):
        while self.running:
            is_ok, _ = self.net.connect_server()
            if is_ok:
                if self.password:
                    msg = f"{Protocol.LOGIN}|{self.username}|{self.password}"
                    try:
                        msg_bytes = msg.encode('utf-8')
                        length_prefix = struct.pack('!I', len(msg_bytes))
                        self.net.client_socket.sendall(length_prefix + msg_bytes)
                        self.reconnected.emit()
                        return
                    except:
                        pass
                else:
                    self.reconnected.emit()
                    return
            time.sleep(3)

class ConnectionManager:
    """Quản lý trạng thái kết nối; khởi chạy luồng reconnect khi cần."""

    def __init__(self, network_client, password=None):
        self.net = network_client
        self.password = password
        self.bus = SignalBus.get()
        self.reconnect_thread = None

        # Kết nối tới các signal hệ thống để xử lý mất/khôi phục kết nối
        self.bus.network_disconnected.connect(self.handle_connection_lost)
        self.bus.network_connected.connect(self.handle_reconnected)
        self.bus.ui_request_logout.connect(self.stop)

    def handle_connection_lost(self):
        if not self.reconnect_thread or not self.reconnect_thread.isRunning():
            self.reconnect_thread = ReconnectThread(self.net, self.net.username, self.password)
            self.reconnect_thread.reconnected.connect(lambda: self.bus.network_connected.emit())
            self.reconnect_thread.start()

    def handle_reconnected(self):
        pass

    def stop(self):
        if self.reconnect_thread:
            self.reconnect_thread.running = False
            self.reconnect_thread.wait()
        
        # Shutdown socket
        try:
            import socket
            self.net.client_socket.shutdown(socket.SHUT_RDWR)
            self.net.client_socket.close()
        except: pass