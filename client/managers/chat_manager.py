"""Mô-đun client\managers\chat_manager.py - mô tả ngắn bằng tiếng Việt."""

from common.protocol import Protocol
from client.core.bus import SignalBus

class ChatManager:
    def __init__(self, network_client):
        self.net = network_client
        self.bus = SignalBus.get()
        
        # Kết nối Signal
        self.bus.ui_send_text.connect(self.send_text)
        self.bus.ui_request_history.connect(self.request_history)

    def send_text(self, text):
        if not self.net.is_connected: return False
        if text.strip():
            try:
                self.net.send_packet(f"{Protocol.MSG}|{text}")
                return True
            except:
                return False
        return False

    def request_history(self, last_id):
        if self.net.is_connected:
            self.net.send_history(last_id)