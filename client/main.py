import sys
import os
import configparser

# Setup đường dẫn import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from client.network.network_client import network_client
from client.ui.dialogs.login_dialog import LoginDialog
from client.ui.main_window import MainWindow

def main():
    # 1. Load Config
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.ini')
    config.read(config_path)
    
    SERVER_IP = config['server']['HOST']
    SERVER_PORT = int(config['server']['PORT'])
    
    # 2. Setup App
    app = QApplication(sys.argv)
    
    # 3. Kết nối Server
    if not network_client.connect_to_server(SERVER_IP, SERVER_PORT):
        print("Không thể kết nối tới server.")
        return # Thoát nếu không có server

    # 4. Hiện Dialog Đăng nhập
    login_dialog = LoginDialog()
    if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
        # Nếu đăng nhập thành công -> Mở Main Window
        # Lấy thông tin user (tạm thời lấy từ title hoặc bus, ở đây giả lập)
        # Trong thực tế AuthManager sẽ lưu user info
        user_info = {"user_id": 1, "display_name": "User"} # Placeholder
        
        window = MainWindow(user_info)
        window.show()
        sys.exit(app.exec())
    else:
        # Người dùng tắt dialog hoặc hủy
        network_client.disconnect()
        sys.exit(0)

if __name__ == "__main__":
    main()