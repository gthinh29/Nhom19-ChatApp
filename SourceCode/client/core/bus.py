"""SignalBus: hệ thống signal toàn cục."""

from PyQt6.QtCore import QObject, pyqtSignal

class SignalBus(QObject):
    # UI -> Logic
    ui_send_text = pyqtSignal(str)              
    ui_request_history = pyqtSignal(int)        
    ui_send_file = pyqtSignal(str)              
    ui_send_image = pyqtSignal(str)             
    
    ui_download_file = pyqtSignal(str)          # Tải mới (Hiện dialog chọn nơi lưu)
    ui_resume_download = pyqtSignal(str, str)   # Tải tiếp (filename, old_path)
    
    ui_cancel_upload = pyqtSignal(str)          
    ui_cancel_download = pyqtSignal(str)        
    ui_request_pending_files = pyqtSignal()     
    
    # Auth
    ui_request_login = pyqtSignal(str, str)              
    ui_request_register = pyqtSignal(str, str, str, str) 
    ui_forgot_request_otp = pyqtSignal(str, str)         
    ui_forgot_reset_pass = pyqtSignal(str, str, str)     
    ui_request_logout = pyqtSignal()
    ui_update_profile = pyqtSignal(str, bytes)  
    ui_request_otp = pyqtSignal()               
    ui_change_password = pyqtSignal(str, str)   
    ui_export_chat = pyqtSignal(str)            

    # Logic -> UI
    network_connected = pyqtSignal()            
    network_disconnected = pyqtSignal()         
    network_packet_received = pyqtSignal(dict)  

    core_auth_success = pyqtSignal(str, str)        
    core_auth_failed = pyqtSignal(str)              
    core_register_result = pyqtSignal(bool, str)    
    core_forgot_result = pyqtSignal(bool, str, str) 
    auth_otp_sent = pyqtSignal()                
    auth_force_logout = pyqtSignal(str)         

    # File Upload
    file_upload_start = pyqtSignal(str, int, str, bool) 
    file_upload_progress = pyqtSignal(str, int)    
    file_upload_done = pyqtSignal(str)                  
    file_upload_completed_msg = pyqtSignal(dict)        
    
    # [UPDATED] (filename, path, percent, is_upload)
    file_pending_restore = pyqtSignal(str, str, int, bool)

    # File Download
    file_download_start = pyqtSignal(str, int)          
    file_download_progress = pyqtSignal(str, int)  
    file_download_complete = pyqtSignal(str, str)       

    core_history_loaded = pyqtSignal()

    _instance = None
    @staticmethod
    def get():
        if SignalBus._instance is None: SignalBus._instance = SignalBus()
        return SignalBus._instance