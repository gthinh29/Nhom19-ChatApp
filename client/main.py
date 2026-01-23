import sys
import os
import configparser

# Setup đường dẫn import để có thể import các module từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Connection Manager để kích hoạt tính năng Heartbeat (tự động chạy khi import)
from client.managers.connection_manager import connection_manager

from PyQt6.QtWidgets import QApplication
from client.network.network_client import network_client
from client.ui.dialogs.login_dialog import LoginDialog
from client.ui.main_window import MainWindow

def main():
    # 1. Load Config
    config = configparser.ConfigParser()
    # Tìm file config.ini ở thư mục gốc (ChatApp3/)
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.ini')
    config.read(config_path)
    
    # Đọc thông tin Server từ config
    SERVER_IP = config['server']['HOST']
    SERVER_PORT = int(config['server']['PORT'])
    
    # 2. Setup App
    app = QApplication(sys.argv)
    
    # 3. Kết nối Server
    # Cố gắng kết nối trước khi hiện UI, nếu thất bại thì dừng chương trình
    if not network_client.connect_to_server(SERVER_IP, SERVER_PORT):
        print("Không thể kết nối tới server.")
        return # Thoát nếu không có server

    # 4. Hiện Dialog Đăng nhập
    login_dialog = LoginDialog()
    if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
        # Nếu đăng nhập thành công -> Mở Main Window
        
        # Lấy thông tin user (trong thực tế AuthManager sẽ lưu thông tin này)
        # Tạm thời dùng dữ liệu giả lập cho Task này
        user_info = {"user_id": 1, "display_name": "User"} # Placeholder
        
        window = MainWindow(user_info)
        window.show()
        sys.exit(app.exec())
    else:
        # Người dùng tắt dialog hoặc hủy đăng nhập
        network_client.disconnect()
        sys.exit(0)

if __name__ == "__main__":
    main()