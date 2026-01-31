

import sqlite3
import hashlib
import os
import bcrypt
import time
import threading

class Database:
    """Lớp xử lý tất cả các tương tác với database SQLite"""
    
    def __init__(self, db_name="chatapp.db"):
        # Đặt database ở thư mục gốc dự án
        current_file_path = os.path.abspath(__file__)
        server_dir = os.path.dirname(current_file_path)
        project_root = os.path.dirname(server_dir)
        
        self.db_path = os.path.join(project_root, db_name)
        
        print(f"[DB] Database path: {self.db_path}") 
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        
        self.cursor = self.conn.cursor()
        # Khóa bảo vệ truy cập cursor qua nhiều thread
        self.lock = threading.RLock()
        self.create_tables()

    def create_tables(self):
        """Tạo các bảng và thực hiện migration nếu cần thiết"""
        
        # 1. Bảng Users
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                fullname TEXT,
                email TEXT,
                avatar TEXT
            )
        """)
        self._migrate_add_column("users", "avatar", "TEXT")

        # 2. Bảng Messages
        # [FIX] Thêm msg_type để phân biệt loại tin nhắn (text/image/file)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_name TEXT,
                content TEXT,
                msg_type TEXT DEFAULT 'text',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._migrate_add_column("messages", "msg_type", "TEXT DEFAULT 'text'")

        # 3. Bảng File Transfers
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                fileid TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT,
                total_size INTEGER NOT NULL,
                uploaded_bytes INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, fileid)
            )
        """)
        self.conn.commit()
        self._migrate_add_column("file_transfers", "file_path", "TEXT")

    def _migrate_add_column(self, table, column, col_type):
        try:
            with self.lock:
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in self.cursor.fetchall()]
                if column not in columns:
                    print(f"[DB] Adding column '{column}' to '{table}'...")
                    self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                    self.conn.commit()
        except Exception as e:
            print(f"[DB] Migration Error ({table}): {e}")

    # ==================== QUẢN LÝ USER ====================

    def register_user(self, username, password, fullname, email):
        try:
            with self.lock:
                print(f"[DB] Creating user: {username}...")
                hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode('utf-8')
                self.cursor.execute("INSERT INTO users (username, password, fullname, email, avatar) VALUES (?, ?, ?, ?, ?)", 
                                    (username, hashed_pw, fullname, email, ""))
                self.conn.commit()
                print(f"[DB] User {username} created!")
                return True
        except sqlite3.IntegrityError:
            print(f"[DB] User {username} exists.")
            return False
        except Exception as e:
            print(f"[DB] Register Error: {e}")
            return False

    def login_user(self, username, password):
        """Xác thực user và trả về thông tin (id, fullname, email, avatar, password_hash) nếu hợp lệ"""
        try:
            with self.lock:
                self.cursor.execute("SELECT id, fullname, email, avatar, password FROM users WHERE username = ?", (username,))
                row = self.cursor.fetchone()

            if not row:
                return None

            stored_hash = row[4]
            try:
                if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    return row
            except Exception:
                # Nếu bcrypt thất bại, coi như xác thực không thành công
                return None

            return None
        except Exception as e:
            print(f"[DB] Login Error: {e}")
            return None

    def update_avatar(self, username, fullname, avatar):
        try:
            with self.lock:
                if avatar:
                    self.cursor.execute("UPDATE users SET fullname = ?, avatar = ? WHERE username = ?", (fullname, avatar, username))
                else:
                    self.cursor.execute("UPDATE users SET fullname = ? WHERE username = ?", (fullname, username))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"[DB] Update Avatar Error: {e}")
            return False

    def get_user_info(self, username):
        try:
            with self.lock:
                self.cursor.execute("SELECT id, username, fullname, email, avatar FROM users WHERE username = ?", (username,))
                row = self.cursor.fetchone()
            if not row:
                return None
            return {
                'id': row[0], 'username': row[1], 'fullname': row[2], 'email': row[3], 'avatar': row[4]
            }
        except Exception as e:
            print(f"[DB] get_user_info Error: {e}")
            return None

    def update_user_info(self, username, fullname, avatar_filename=None):
        try:
            with self.lock:
                if avatar_filename:
                    self.cursor.execute("UPDATE users SET fullname = ?, avatar = ? WHERE username = ?", (fullname, avatar_filename, username))
                else:
                    self.cursor.execute("UPDATE users SET fullname = ? WHERE username = ?", (fullname, username))
                self.conn.commit()
            return True
        except Exception as e:
            print(f"[DB] update_user_info Error: {e}")
            return False

    def check_user_email(self, username, email):
        with self.lock:
            self.cursor.execute("SELECT id FROM users WHERE username = ? AND email = ?", (username, email))
            return self.cursor.fetchone()

    def update_password(self, username, new_password):
        hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=12)).decode('utf-8')
        with self.lock:
            self.cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))
            self.conn.commit()

    # ==================== QUẢN LÝ MESSAGES (Fixed) ====================

    def save_message(self, sender, content, msg_type="text"):
        """Lưu tin nhắn và TRẢ VỀ ID"""
        try:
            with self.lock:
                self.cursor.execute(
                    "INSERT INTO messages (sender_name, content, msg_type) VALUES (?, ?, ?)", 
                    (sender, content, msg_type)
                )
                self.conn.commit()
                return self.cursor.lastrowid # Trả về ID
        except Exception as e:
            print(f"[DB] Save Message Error: {e}")
            return None

    def get_recent_messages(self, limit=50, before_id=None):
        """
        Lấy tin nhắn lịch sử (Hỗ trợ phân trang)
        Thay thế cho get_recent_messages_with_id và get_messages_before
        Trả về: list of tuples (id, sender_name, content, timestamp, msg_type)
        """
        try:
            query = "SELECT id, sender_name, content, timestamp, msg_type FROM messages"
            params = []

            # Bỏ qua filter nếu before_id không hợp lệ (None hoặc <= 0)
            if before_id is not None and int(before_id) > 0:
                query += " WHERE id < ?"
                params.append(before_id)

            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            with self.lock:
                self.cursor.execute(query, tuple(params))
                rows = self.cursor.fetchall()
            return rows
        except Exception as e:
            print(f"[DB] Get History Error: {e}")
            return []

    # ==================== QUẢN LÝ FILE TRANSFERS (RESUME) ====================
    
    def create_or_update_file_transfer(self, username, fileid, filename, total_size, uploaded_bytes=0, status='pending', file_path=None):
        try:
            with self.lock:
                self.cursor.execute("""
                    INSERT INTO file_transfers (username, fileid, filename, file_path, total_size, uploaded_bytes, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(username, fileid) DO UPDATE SET
                        uploaded_bytes = ?,
                        status = ?,
                        file_path = COALESCE(?, file_path),
                        updated_at = CURRENT_TIMESTAMP
                """, (username, fileid, filename, file_path, total_size, uploaded_bytes, status, 
                      uploaded_bytes, status, file_path))
                self.conn.commit()
            return True
        except Exception as e:
            print(f"[DB] File Transfer Error: {e}")
            return False

    def get_pending_file_transfers(self, username):
        try:
            with self.lock:
                self.cursor.execute("""
                    SELECT fileid, filename, total_size, uploaded_bytes, status, file_path
                    FROM file_transfers
                    WHERE username = ? AND status IN ('pending', 'uploading')
                    ORDER BY updated_at DESC
                """, (username,))
                rows = self.cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'fileid': row[0], 'filename': row[1], 'total_size': row[2],
                    'uploaded_bytes': row[3], 'status': row[4], 'file_path': row[5]
                })
            return result
        except Exception as e:
            return []

    def update_file_transfer_progress(self, username, fileid, uploaded_bytes):
        try:
            with self.lock:
                self.cursor.execute("""
                    UPDATE file_transfers
                    SET uploaded_bytes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE username = ? AND fileid = ?
                """, (uploaded_bytes, username, fileid))
                self.conn.commit()
            return True
        except: return False

    def complete_file_transfer(self, username, fileid):
        try:
            with self.lock:
                self.cursor.execute("""
                    UPDATE file_transfers
                    SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                    WHERE username = ? AND fileid = ?
                """, (username, fileid))
                self.conn.commit()
            return True
        except: return False

    def delete_file_transfer(self, username, fileid):
        try:
            # Đánh dấu hủy thay vì xóa để giữ lịch sử
            with self.lock:
                self.cursor.execute("""
                    UPDATE file_transfers
                    SET status = 'canceled', updated_at = CURRENT_TIMESTAMP
                    WHERE username = ? AND fileid = ?
                """, (username, fileid))
                self.conn.commit()
            return True
        except Exception as e:
            print(f"[DB] delete_file_transfer error: {e}")
            return False

    def close(self):
        self.conn.close()