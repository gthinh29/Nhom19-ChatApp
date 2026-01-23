# Script tạo Self-Signed Certificate cho môi trường Development
# Yêu cầu: pip install cryptography
# Nếu không muốn cài thêm lib, bạn có thể dùng lệnh openssl thủ công:
# openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime
import os

def generate_self_signed_cert():
    # 1. Tạo Private Key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 2. Tạo thông tin chủ thể (Subject)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"VN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"HoChiMinh"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"District 1"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"ChatApp Org"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    # 3. Tạo Certificate
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        subject
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Hết hạn sau 1 năm
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())

    # 4. Lưu ra file
    with open("server.key", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
        
    with open("server.crt", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("✅ Đã tạo server.crt và server.key thành công!")

if __name__ == "__main__":
    try:
        generate_self_signed_cert()
    except ImportError:
        print("❌ Lỗi: Chưa cài thư viện cryptography.")
        print("👉 Hãy chạy: pip install cryptography")