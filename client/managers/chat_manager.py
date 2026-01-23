from PyQt6.QtCore import QObject
from common.protocol import *
from client.core.bus import bus

class ChatManager(QObject):
    """
    Quản lý logic nhận tin nhắn chat từ Server và phân phối cho UI.
    """
    def __init__(self):
        super().__init__()
        # Đăng ký nhận mọi message từ Network
        bus.message_received.connect(self.process_incoming_message)

    def process_incoming_message(self, data):
        cmd, content = data
        
        if cmd == CMD_MSG:
            # Format nhận từ Server: sender_name|content
            if SEPARATOR in content:
                sender, msg_text = content.split(SEPARATOR, 1)
                
                # Bắn tín hiệu ra cho UI (MainWindow) bắt lấy
                # Gói data dạng dict cho dễ dùng
                message_data = {
                    "sender": sender,
                    "content": msg_text,
                    "is_file": False # Sẽ xử lý file sau
                }
                # Chúng ta tái sử dụng signal message_received của Bus nhưng với data đã xử lý
                # Tuy nhiên để tránh vòng lặp, tốt nhất UI nên lắng nghe Bus trực tiếp 
                # hoặc ta tạo signal riêng. Ở đây ta dùng cách Bus.msg_received(object) 
                # nhưng để đơn giản, UI sẽ tự parse hoặc ta emit một event specific.
                
                # Cách tốt nhất: Emit một signal riêng biệt cho Chat
                # Vì bus.message_received là RAW packet.
                # Ta sẽ thêm signal 'chat_message_received' vào Bus hoặc xử lý trực tiếp tại UI.
                pass 
