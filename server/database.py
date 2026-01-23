import sqlite3
import threading

class Database:
    def __init__(self, db_name="chatapp.db"):
        self.db_name = db_name
        self.lock = threading.Lock() # Đảm bảo an toàn khi đa luồng truy cập DB
        self.create_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        # Bật chế độ WAL (Write-Ahead Logging) để tăng tốc độ và tránh lỗi locked
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def create_tables(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Bảng Users
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                display_name TEXT,
                avatar BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Bảng Messages
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                receiver_id INTEGER,
                content TEXT,
                is_file BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sender_id) REFERENCES users(user_id),
                FOREIGN KEY(receiver_id) REFERENCES users(user_id)
            )
            """)
            
            conn.commit()
            conn.close()

    def execute_query(self, query, params=()):
        """Thực thi lệnh INSERT, UPDATE, DELETE"""
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
            except Exception as e:
                print(f"[DB ERROR] {e}")
                return None
            finally:
                conn.close()
                
    def fetch_one(self, query, params=()):
        """Lấy 1 dòng dữ liệu (SELECT)"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.close()
            return result