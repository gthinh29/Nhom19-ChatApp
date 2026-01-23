🚀 ChatApp - Ứng dụng Chat Desktop (Python/PyQt6)

Ứng dụng nhắn tin mạng LAN/Internet hiện đại, bảo mật với giao diện Dark Mode lấy cảm hứng từ Discord.


Môn học: Lập trình mạng (Network Programming)
Giảng viên hướng dẫn: Bùi Dương Thế

1. Tên đề tài

🚀 ChatApp - Ứng dụng Chat Desktop (Python/PyQt6)

Ứng dụng nhắn tin mạng LAN/Internet hiện đại, bảo mật với giao diện Dark Mode lấy cảm hứng từ Discord.

2. Lý do chọn đề tài
Trong kỷ nguyên số, nhu cầu giao tiếp thời gian thực (Real-time communication) là cốt lõi của mọi hệ thống mạng. Chúng tôi chọn đề tài này vì:

Tính nền tảng: Ứng dụng Chat là bài toán kinh điển giúp hiểu sâu sắc nhất về mô hình TCP/IP, cách thức hoạt động của Socket và luồng dữ liệu.
Thách thức kỹ thuật: Đề tài yêu cầu xử lý đồng thời (Concurrency) để nhiều người dùng có thể giao tiếp cùng lúc, giúp nhóm rèn luyện kỹ năng xử lý Đa luồng (Multi-threading).
Tính thực tiễn: Có khả năng mở rộng để ứng dụng trong các hệ thống mạng nội bộ d

📁 Cấu Trúc Dự Án

ChatApp/
├── server/                          # SERVER (Backend)
│   ├── main.py                      # Khởi động Server, cấu hình SSL
│   ├── database.py                  # Quản lý SQLite & Bcrypt
│   ├── router.py                    # Định tuyến lệnh (Login, Chat, File)
│   ├── controllers/
│   │   ├── auth_controller.py       # Xử lý Đăng nhập/Đăng ký
│   │   └── chat_controller.py       # Xử lý Tin nhắn & File Upload
│   ├── uploads/                     # Thư mục chứa file người dùng gửi
│   ├── server.crt                   # Chứng chỉ SSL (Public Key)
│   └── server.key                   # Khóa riêng SSL (Private Key)
│
├── client/                          # CLIENT (Frontend)
│   ├── main.py                      # Khởi động Client
│   ├── network/
│   │   └── network_client.py        # Socket Client (SSL, Send/Receive)
│   ├── core/
│   │   └── bus.py                   # Event Bus (Tín hiệu liên lạc)
│   ├── managers/
│   │   ├── auth_manager.py          # Logic xác thực
│   │   ├── chat_manager.py          # Logic xử lý tin nhắn đến
│   │   ├── connection_manager.py    # Heartbeat (Ping/Pong)
│   │   └── file_manager.py          # Upload File & LRU Cache
│   ├── ui/
│   │   ├── main_window.py           # Cửa sổ chính
│   │   ├── styles.py                # Bảng màu & CSS (Discord Theme)
│   │   ├── icon_factory.py          # Vẽ Icon bằng code (Không cần ảnh ngoài)
│   │   ├── dialogs/                 # Các hộp thoại (Login)
│   │   ├── components/              # Các phần giao diện (Sidebar, ChatArea)
│   │   └── widgets/                 # Widget nhỏ (MessageBubble)
│
├── common/
│   └── protocol.py                  # Định nghĩa Giao thức (Packet Framing)
│
├── config.ini                       # Cấu hình IP, Port, SSL
└── README.md                        # Tài liệu dự án


🛠️ Cài Đặt & Chạy

1. Yêu cầu hệ thống

Python 3.10+

Hệ điều hành: Windows, macOS, hoặc Linux

2. Cài đặt thư viện

Chạy lệnh sau để cài đặt các gói cần thiết:

pip install PyQt6 bcrypt cryptography


3. Cấu hình (config.ini)

Đảm bảo file config.ini có nội dung sau:

[server]
HOST = 0.0.0.0
PORT = 12345

[security]
SSL_CERT_FILE = server/server.crt
SSL_KEY_FILE = server/server.key
VERIFY_CERT = false  ; Đặt false nếu dùng Self-Signed Cert

[limits]
HEARTBEAT_INTERVAL = 10
HEARTBEAT_TIMEOUT = 30


4. Khởi động ứng dụng

Bước 1: Chạy Server

python server/main.py


Bước 2: Chạy Client (Mở thêm terminal mới)

python client/main.py


🔥 Tính Năng Nổi Bật

🔒 1. Bảo Mật & An Toàn

Mã hóa SSL/TLS: Toàn bộ dữ liệu truyền tải được mã hóa, chống nghe lén (Man-in-the-Middle).

Bcrypt Hashing: Mật khẩu người dùng được băm (hash) với Salt 12 vòng, bảo vệ an toàn ngay cả khi lộ Database.

Heartbeat/Ping-Pong: Tự động phát hiện và ngắt kết nối các máy trạm bị treo hoặc mất mạng đột ngột sau 30 giây.

⚡ 2. Hiệu Năng Cao

Chunked File Upload: Hỗ trợ gửi file dung lượng lớn bằng cách chia nhỏ thành các gói 64KB, không làm nghẽn mạng.

Async Image Loading: Giải mã ảnh Base64 trên luồng riêng (Thread), giúp giao diện cuộn mượt mà không bị giật/đơ.

LRU Cache: Bộ nhớ đệm thông minh cho Avatar, tự động xóa các ảnh ít dùng nhất khi bộ nhớ đầy.

🎨 3. Giao Diện Người Dùng (UI/UX)

Discord Dark Theme: Giao diện tối hiện đại, dễ nhìn, giảm mỏi mắt.

Message Bubbles: Bong bóng tin nhắn thông minh, hỗ trợ hiển thị ảnh và văn bản.

Sidebar Navigation: Thanh điều hướng bên trái quản lý kênh chat và thông tin người dùng.

📡 Giao Thức Truyền Thông (Protocol)

Hệ thống sử dụng giao thức tùy chỉnh dựa trên TCP/IP với cấu trúc gói tin:
[4-byte Length Header] + [Payload Body]

Các lệnh chính:
| Lệnh | Mô tả | Định dạng Payload |
| :--- | :--- | :--- |
| LOGIN | Đăng nhập | LOGIN|username|password |
| REGISTER | Đăng ký | REGISTER|username|password |
| MSG | Gửi tin nhắn | MSG|content |
| FILE | Gửi file | FILE|INIT/CHUNK/END|... |
| PING | Kiểm tra kết nối | PING |

💾 Cơ Sở Dữ Liệu (SQLite)

Database chatapp.db tự động được tạo với 2 bảng chính:

Bảng users:

user_id: ID duy nhất

username: Tên đăng nhập

password: Mật khẩu đã mã hóa Bcrypt

display_name: Tên hiển thị

Bảng messages:

msg_id: ID tin nhắn

sender_id: ID người gửi

content: Nội dung tin nhắn

created_at: Thời gian gửi

❓ Troubleshooting (Sửa lỗi thường gặp)

1. Lỗi "Connection Refused":

Kiểm tra Server đã chạy chưa.

Kiểm tra IP và PORT trong config.ini có khớp không.

2. Lỗi "SSL Certificate Verify Failed":

Đây là do dùng chứng chỉ tự ký (Self-signed).

Vào client/network/network_client.py, đảm bảo context.check_hostname = False.

3. Lỗi "ImportError: No module named..."

Đảm bảo bạn đang chạy lệnh từ thư mục gốc ChatApp/ (ví dụ: python client/main.py), KHÔNG chạy từ bên trong thư mục con.