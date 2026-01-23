"""Mô-đun server\generate_cert.py - mô tả ngắn bằng tiếng Việt."""

import subprocess
import os

# Cố gắng dùng thư viện cryptography nếu có
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import datetime
    
    # Tạo khóa riêng tư
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Xây dựng chứng chỉ
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"192.168.100.101"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"192.168.100.101"),
            x509.DNSName(u"localhost"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    # Ghi chứng chỉ
    cert_path = os.path.join(os.path.dirname(__file__), 'server.crt')
    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Ghi khóa
    key_path = os.path.join(os.path.dirname(__file__), 'server.key')
    with open(key_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print(f"✅ Generated SSL certificate:")
    print(f"   server.crt: {cert_path}")
    print(f"   server.key: {key_path}")
    print(f"   CN: 192.168.100.101")
    
except ImportError:
    print("❌ cryptography library not found")
