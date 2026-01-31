import configparser
import os


class Protocol:
    _config = configparser.ConfigParser()
    _config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
    if os.path.exists(_config_path):
        _config.read(_config_path)
    
    HOST = _config.get('server', 'HOST', fallback='0.0.0.0')
    PORT = _config.getint('server', 'PORT', fallback=12345)
    WEB_PORT = _config.getint('server', 'WEB_PORT', fallback=8080)
    BROADCAST_PORT = _config.getint('server', 'BROADCAST_PORT', fallback=50000)
    LENGTH_PREFIX_SIZE = 4
    
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"
    FORGOT_PW = "FORGOT_PW"
    RESET_PASSWORD = "RESET_PASSWORD"
    CONFIRM_RESET = "CONFIRM_RESET"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    
    MSG = "MSG"
    IMAGE = "IMAGE"
    
    FILE = "FILE"
    
    UPLOAD_REQ = "UPLOAD_REQ"
    UPLOAD_RESP = "UPLOAD_RESP"
    FILE_STREAM = "FILE_STREAM"
    
    DOWNLOAD_REQ = "DOWNLOAD_REQ"
    DOWNLOAD_RESP = "DOWNLOAD_RESP"
    FILE_DOWNLOAD_STREAM = "FILE_DOWNLOAD_STREAM"
    
    GET_PENDING_FILES = "GET_PENDING_FILES"
    CANCEL_FILE = "CANCEL_FILE"
    EXPORT_CHAT = "EXPORT_CHAT"
    HISTORY = "HISTORY"
    
    ONLINE_LIST = "ONLINE_LIST"
    USER_STATUS = "USER_STATUS"
    FORCE_LOGOUT = "FORCE_LOGOUT"
    
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
