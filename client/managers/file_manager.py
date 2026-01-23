import os
import base64
import threading
from collections import OrderedDict
from PyQt6.QtCore import QObject
from common.protocol import *
from client.network.network_client import network_client

# --- Class LRUCache (Task 8) ---
class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return None
        # Di chuyển item vừa truy cập xuống cuối (Recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        # Nếu vượt quá dung lượng, xóa phần tử đầu tiên (Least used)
        if len(self.cache) > self.capacity:
            removed = self.cache.popitem(last=False)
            print(f"[CACHE] Evicted: {removed[0]}")

# --- Class FileManager (Task 3 + 8) ---
class FileManager(QObject):
    CHUNK_SIZE = 64 * 1024  # 64KB per chunk

    def __init__(self):
        super().__init__()
        # Khởi tạo Cache max 50 items
        self.avatar_cache = LRUCache(50)

    def get_avatar(self, user_id):
        """Lấy avatar từ cache"""
        cached_avatar = self.avatar_cache.get(user_id)
        if cached_avatar:
            return cached_avatar
        return None

    def save_avatar_to_cache(self, user_id, avatar_data):
        """Lưu avatar vào cache"""
        self.avatar_cache.put(user_id, avatar_data)

    def upload_file(self, file_path):
        """
        Gửi file theo cơ chế Chunked Upload (Task 3).
        Chạy trong thread riêng để không chặn UI.
        """
        if not os.path.exists(file_path):
            return

        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)
        
        worker = threading.Thread(target=self._upload_worker, args=(file_path, filename, filesize))
        worker.start()

    def _upload_worker(self, file_path, filename, filesize):
        try:
            # 1. Gửi lệnh INIT
            print(f"[UPLOAD] Starting {filename} ({filesize} bytes)...")
            network_client.send_packet(CMD_FILE, f"INIT|{filename}|{filesize}")
            
            # 2. Gửi từng CHUNK
            with open(file_path, 'rb') as f:
                offset = 0
                while True:
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    # Encode Base64 để gửi qua socket text
                    chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                    
                    # Packet: CHUNK|filename|offset|data
                    payload = f"CHUNK|{filename}|{offset}|{chunk_b64}"
                    network_client.send_packet(CMD_FILE, payload)
                    
                    offset += len(chunk)
            
            # 3. Gửi lệnh END
            network_client.send_packet(CMD_FILE, f"END|{filename}")
            print(f"[UPLOAD] Finished {filename}")
            
        except Exception as e:
            print(f"[UPLOAD ERROR] {e}")

# Singleton Instance
file_manager = FileManager()