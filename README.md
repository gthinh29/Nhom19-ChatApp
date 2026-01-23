# 🚀 ChatApp - Ứng dụng Chat Desktop (Python/PyQt6) - Nhóm 19


    **Môn học:** Lập trình mạng (Network Programming)


    **Giảng viên hướng dẫn:** Bùi Dương Thế


## 👥 Thành viên nhóm 19


<table>
  <tr>
   <td><strong>STT</strong>
   </td>
   <td><strong>Họ và Tên</strong>
   </td>
  </tr>
  <tr>
   <td>1
   </td>
   <td><strong>Phạm Gia Thịnh</strong>
   </td>
  </tr>
  <tr>
   <td>2
   </td>
   <td><strong>Trần Trung Chiến</strong>
   </td>
  </tr>
  <tr>
   <td>3
   </td>
   <td><strong>Nguyễn Hoàng Linh Tú</strong>
   </td>
  </tr>
  <tr>
   <td>4
   </td>
   <td><strong>Trần Hoài Phong</strong>
   </td>
  </tr>
</table>



## 📖 Giới thiệu đề tài

**Xây dựng ứng dụng trò chuyện trực tuyến (Chat App) qua mạng LAN/Internet sử dụng kiến trúc Client-Server.**

Trong kỷ nguyên số, nhu cầu giao tiếp thời gian thực là cốt lõi của mọi hệ thống mạng. Chúng tôi chọn đề tài này để rèn luyện kỹ năng xử lý Đa luồng (Multi-threading), Socket Programming và Kiến trúc phân tán.


## 📁 Cấu Trúc Dự Án

Cấu trúc thư mục chi tiết của dự án:

ChatApp/ \
├── server/                          # SERVER (Backend) \
│   ├── main.py                      # Khởi động Server, cấu hình SSL \
│   ├── database.py                  # Quản lý SQLite & Bcrypt \
│   ├── router.py                    # Định tuyến lệnh (Login, Chat, File) \
│   ├── controllers/                 # Controllers xử lý logic nghiệp vụ \
│   ├── uploads/                     # Thư mục chứa file người dùng gửi \
│   ├── server.crt & server.key      # Chứng chỉ SSL \
│   ├── .env                         # Cấu hình Email (SMTP) \
│   └── pending_uploads.json         # Lưu trạng thái upload dở dang \
│ \
├── client/                          # CLIENT (Frontend) \
│   ├── main.py                      # Khởi động Client \
│   ├── network/ \
│   │   └── network_client.py        # Socket Client (SSL, Send/Receive) \
│   ├── managers/                    # Quản lý logic (Auth, Chat, File, Connection) \
│   ├── ui/ \
│   │   ├── main_window.py           # Cửa sổ chính \
│   │   ├── dialogs/                 # Các hộp thoại chức năng \
│   │   │   ├── login_dialog.py      # Đăng nhập/Đăng ký/Quên mật khẩu \
│   │   │   ├── export_dialog.py     # Xuất lịch sử chat \
│   │   │   └── settings_dialog.py   # Cài đặt cấu hình \
│   │   ├── widgets/                 # Các Widget tùy chỉnh \
│   │   │   ├── toast.py             # Thông báo nổi (Toast Notification) \
│   │   │   ├── bubbles.py           # Bong bóng chat \
│   │   │   └── custom.py            # Custom UI Components \
│   │   └── styles.py                # Discord Theme \
│ \
├── common/protocol.py               # Định nghĩa Giao thức \
├── config.ini                       # Cấu hình hệ thống \
└── README.md                        # Tài liệu dự án \



## 🛠️ Cài Đặt & Chạy


### 1. Yêu cầu hệ thống



* **Python 3.10+**
* Hệ điều hành: Windows, macOS, hoặc Linux


### 2. Cài đặt thư viện

Chạy lệnh sau để cài đặt các gói cần thiết:

pip install PyQt6 bcrypt cryptography python-dotenv \



### 3. Cấu hình (config.ini)

Đảm bảo file config.ini có nội dung sau:

[server] \
HOST = 0.0.0.0 \
PORT = 12345 \
 \
[security] \
SSL_CERT_FILE = server/server.crt \
SSL_KEY_FILE = server/server.key \
VERIFY_CERT = false \
 \
[limits] \
HEARTBEAT_INTERVAL = 10 \
HEARTBEAT_TIMEOUT = 30 \



### 4. Khởi động ứng dụng

**Bước 1: Chạy Server**

python server/main.py \


**Bước 2: Chạy Client** (Mở thêm terminal mới)

python client/main.py \



## 🔥 Tính Năng Nổi Bật & Nâng Cao

Dự án không chỉ dừng lại ở việc chat cơ bản mà còn tích hợp nhiều tính năng nâng cao (Advanced Features) để tối ưu trải nghiệm người dùng và độ tin cậy.


### 🌟 1. Hệ Thống Truyền Tải File Thông Minh (Smart File Transfer)



* **Resumable Upload (Tải nối tiếp):** Sử dụng cơ chế lưu trạng thái vào file pending_uploads.json. Nếu mạng bị ngắt giữa chừng, hệ thống sẽ tự động tiếp tục tải từ điểm bị ngắt (offset) thay vì tải lại từ đầu khi có mạng trở lại.
* **Chunked Transfer:** Chia nhỏ file thành các gói 64KB, giúp truyền ổn định các file dung lượng lớn (GB) mà không gây nghẽn luồng chat.


### 📊 2. Quản Lý & Xuất Dữ Liệu (Data Export)



* **Export Chat History:** Tính năng cho phép người dùng trích xuất toàn bộ lịch sử cuộc trò chuyện ra file (PDF/Text/HTML) để lưu trữ hoặc báo cáo.
* **Database Persistence:** Mọi tin nhắn và thông tin người dùng được lưu trữ an toàn trong SQLite, đảm bảo không mất dữ liệu khi tắt ứng dụng.


### 🎨 3. Giao Diện & Trải Nghiệm Người Dùng (UI/UX)



* **Live Avatar Updates:** (Mới) Cập nhật ảnh đại diện thời gian thực. Khi một người dùng thay đổi avatar, thay đổi sẽ được đồng bộ ngay lập tức tới sidebar và khung chat của tất cả các user khác đang online mà không cần tải lại ứng dụng.
* **Toast Notifications:** Hệ thống thông báo nổi (Toast) tự xây dựng (toast.py), hiển thị trạng thái (Thành công/Lỗi/Info) một cách tinh tế.
* **Async Image Loading:** Giải mã ảnh Base64 trên luồng riêng (Thread), giúp giao diện cuộn mượt mà 60fps ngay cả khi hiển thị nhiều ảnh chất lượng cao.
* **Discord Dark Theme:** Giao diện tối hiện đại, giảm mỏi mắt.


### 🔒 4. Bảo Mật & Xác Thực (Security & Auth)



* **Forgot Password via Email:** (Mới) Tích hợp SMTP Server. Khi người dùng quên mật khẩu, hệ thống sẽ gửi mã xác thực (OTP) về email đã đăng ký để cho phép thiết lập lại mật khẩu an toàn.
* **Mã hóa SSL/TLS:** Toàn bộ dữ liệu truyền tải được mã hóa đầu cuối.
* **Bcrypt Hashing:** Mật khẩu được băm an toàn với Salt 12 vòng.
* **Heartbeat/Ping-Pong:** Cơ chế tự động phát hiện mất kết nối.


## 📡 Giao Thức Truyền Thông (Protocol)

Hệ thống sử dụng giao thức tùy chỉnh dựa trên TCP/IP với cấu trúc gói tin:

[4-byte Length Header] + [Payload Body]

**Các lệnh chính:**


<table>
  <tr>
   <td><strong>Lệnh</strong>
   </td>
   <td><strong>Mô tả</strong>
   </td>
   <td><strong>Định dạng Payload</strong>
   </td>
  </tr>
  <tr>
   <td>LOGIN
   </td>
   <td>Đăng nhập
   </td>
   <td>`LOGIN
   </td>
  </tr>
  <tr>
   <td>REGISTER
   </td>
   <td>Đăng ký
   </td>
   <td>`REGISTER
   </td>
  </tr>
  <tr>
   <td>MSG
   </td>
   <td>Gửi tin nhắn
   </td>
   <td>`MSG
   </td>
  </tr>
  <tr>
   <td>FILE
   </td>
   <td>Gửi file
   </td>
   <td>`FILE
   </td>
  </tr>
  <tr>
   <td>AVATAR
   </td>
   <td>Cập nhật Avatar
   </td>
   <td>`AVATAR
   </td>
  </tr>
  <tr>
   <td>RESET_PW
   </td>
   <td>Quên mật khẩu
   </td>
   <td>`RESET_PW
   </td>
  </tr>
  <tr>
   <td>PING
   </td>
   <td>Kiểm tra kết nối
   </td>
   <td>PING
   </td>
  </tr>
</table>



## ❓ Troubleshooting (Sửa lỗi thường gặp)

**1. Lỗi "Connection Refused":**



* Kiểm tra Server đã chạy chưa.
* Kiểm tra IP và PORT trong config.ini có khớp không.

**2. Lỗi "SSL Certificate Verify Failed":**



* Đây là do dùng chứng chỉ tự ký (Self-signed).
* Vào client/network/network_client.py, đảm bảo context.check_hostname = False.

**3. Lỗi upload file bị gián đoạn:**



* Hệ thống sẽ tự động ghi nhận vào pending_uploads.json. Chỉ cần kết nối lại mạng, quá trình upload sẽ tự động tiếp tục.

**4. Không gửi được Email:**



* Kiểm tra file .env hoặc cấu hình SMTP trong server/config.ini đã điền đúng App Password của Gmail chưa.


## 📝 Cam kết và Đóng góp

Dự án được thực hiện bởi sự đóng góp công bằng của cả 4 thành viên Nhóm 19. Lịch sử commit code được lưu trữ đầy đủ trên Git Repository này.