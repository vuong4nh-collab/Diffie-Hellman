# HƯỚNG DẪN XÂY DỰNG DỰ ÁN
# Ứng Dụng Trao Đổi Khóa Bảo Mật Giữa Hai Người Dùng Dựa Trên Diffie-Hellman

---

## 1. GIỚI THIỆU VỀ DIFFIE-HELLMAN (DH)

### 1.1 Khái Niệm
- **Diffie-Hellman** là thuật toán trao đổi khóa công khai (key exchange protocol)
- Cho phép hai bên trao đổi thông qua kênh không bảo mật và tạo ra **khóa bí mật chung**
- Được phát minh năm 1976 bởi Whitfield Diffie và Martin Hellman
- **Không** mã hóa dữ liệu, chỉ trao đổi khóa

### 1.2 Ưu Điểm
- ✅ An toàn: khó tính toán logarit rời rạc (Discrete Logarithm Problem)
- ✅ Không cần chia sẻ khóa bí mật trước
- ✅ Hoạt động trên kênh công khai
- ✅ Cơ sở cho nhiều giao thức hiện đại (TLS, SSH, IPSec)

### 1.3 Nhược Điểm
- ❌ Dễ bị tấn công Man-in-the-Middle (MITM)
- ❌ Chậm hơn các phương pháp khác
- ❌ Cần số nguyên tố lớn (2048-4096 bit)

---

## 2. NGUYÊN LÝ HOẠT ĐỘNG

### 2.1 Các Bước Thực Hiện

```
BƯỚC 1: Thỏa Thuận Tham Số Công Khai
┌─────────────────────────────────┐
│ Alice và Bob chọn:              │
│ - p: số nguyên tố lớn (công khai) │
│ - g: căn nguyên thủy mod p (công khai) │
└─────────────────────────────────┘

BƯỚC 2: Tính Giá Trị Công Khai
Alice:                          Bob:
- Chọn: a (bí mật)             - Chọn: b (bí mật)
- Tính: A = g^a mod p          - Tính: B = g^b mod p
- Gửi: A (công khai)           - Gửi: B (công khai)

BƯỚC 3: Trao Đổi Qua Kênh Công Khai
Alice ────────────── A ────────────→ Bob
       ←────────────── B ──────────── 

BƯỚC 4: Tính Khóa Bí Mật Chung
Alice:                          Bob:
K = B^a mod p                   K = A^b mod p
```

### 2.2 Chứng Minh Toán Học
```
K (Alice) = B^a mod p = (g^b mod p)^a mod p = g^(ab) mod p
K (Bob)   = A^b mod p = (g^a mod p)^b mod p = g^(ab) mod p

→ K (Alice) = K (Bob) ✓
```

---

## 3. KIẾN TRÚC DỰ ÁN

### 3.1 Cấu Trúc Thư Mục
```
DIffie-Hellman/
├── diffie_hellman.py            # Lõi DH, Alice/Bob, SecureChannel, demo local
├── relay_server.py              # Relay TCP — chạy trên máy host
├── dh_client.py                 # Client CLI (Alice/Bob qua socket)
├── dh_gui_app.py                # Client GUI — người dùng không start server
├── app_config.py                # load_config(), get_server_host(), get_bind_host()
├── config.json                  # server_host, server_port, bind_host, timeout
├── advanced_examples.py         # MITM + EncryptedMessenger (AES)
├── test_diffie_hellman.py       # Unit tests
├── requirements.txt
├── README.md
├── QUICKSTART.md
├── DH_Project_Guide.md
├── TIMELINE_CHECKLIST.md
└── 00_SUMMARY.md
```

### 3.2 Kiến Trúc Client–Server Relay

```
┌─────────────┐     TCP JSON      ┌──────────────────┐     TCP JSON      ┌─────────────┐
│ Alice       │ ────────────────► │ relay_server.py  │ ◄──────────────── │ Bob         │
│ dh_gui_app  │                   │ (máy host)       │                   │ dh_gui_app  │
│ hoặc        │ ◄──────────────── │ Chỉ forward msg  │ ────────────────► │ hoặc        │
│ dh_client   │                   │ Không biết K     │                   │ dh_client   │
└─────────────┘                   └──────────────────┘                   └─────────────┘
      │                                    │                                    │
      └────────────── tính shared secret K cục bộ (DiffieHellman) ──────────────┘
```

- **Host**: `python relay_server.py` — bind `bind_host` (mặc định `0.0.0.0`).
- **Client**: `python dh_gui_app.py` — kết nối tới `server_host:server_port`.
- **Test 1 máy**: `server_host = 127.0.0.1` — TCP loopback, không cần đổi config.
- **Test nhiều máy**: mỗi client trỏ `server_host` về IP máy host.

### 3.3 Công Nghệ Sử Dụng
- **Ngôn ngữ**: Python 3.8+
- **Thư viện**: `cryptography`, `socket`, `json`
- **Giao diện** (tùy chọn): `tkinter` hoặc `PyQt5`
- **Kiểm thử**: `pytest`

---

## 4. THIẾT KẾ CHI TIẾT

### 4.1 Module: diffie_hellman.py

**Chức năng chính:**
- Kiểm tra số nguyên tố
- Tìm căn nguyên thủy
- Tính toán khóa công khai/bí mật

**Pseudocode:**
```
class DiffieHellman:
    __init__(bit_length=2048):
        p = generate_large_prime(bit_length)
        g = find_primitive_root(p)
    
    generate_private_key():
        return random(2, p-1)
    
    generate_public_key(private_key):
        return pow(g, private_key, p)
    
    compute_shared_secret(their_public, my_private):
        return pow(their_public, my_private, p)
```

### 4.2 Module: relay_server.py + dh_client.py

**Relay server** — chuyển tiếp JSON giữa Alice và Bob:
- Đăng ký role `alice` / `bob` qua message `hello`
- Queue message nếu peer chưa kết nối
- Không gọi `DiffieHellman`, không lưu shared secret

**Client CLI/GUI** — dùng chung logic socket:
- Alice gửi `dh_params` + `public_key`
- Bob gửi `public_key`
- Mã hóa chat bằng Fernet (SHA-256 từ shared secret)

**Cấu trúc message (relay):**
```json
{
  "type": "public_key",
  "from": "alice",
  "to": "bob",
  "public_key": 123456789
}
```

### 4.3 Module: diffie_hellman.py (local)

**SecureChannel** — mô phỏng kênh trong bộ nhớ (demo local, không TCP):
- Dùng trong `run_diffie_hellman_protocol()` khi chạy `python diffie_hellman.py`
- Alice/Bob trao đổi khóa qua dict + print, không cần `relay_server.py`

**Flow local:**
```
1. Alice & Bob sinh khóa trong cùng process
2. SecureChannel chuyển public_key + params
3. Cả hai tính K — kiểm tra K(Alice) == K(Bob)
```

## 5. TÍNH NĂNG CHÍNH CỦA DÙNG

### Tính Năng Cơ Bản
- ✅ Trao đổi khóa Diffie-Hellman đầy đủ
- ✅ Hỗ trợ 1024, 2048, 4096 bit key
- ✅ Mô phỏng communication Alice-Bob
- ✅ Xác minh khóa giống nhau

### Tính Năng Nâng Cao
- ✅ Mã hóa dữ liệu với khóa chung (AES-256 / Fernet)
- ✅ Tấn công MITM mô phỏng + phòng chống
- ✅ Phân tích hiệu suất (thời gian tính toán)
- ✅ Giao diện client GUI (`dh_gui_app.py`)
- ✅ Relay TCP tách server/client
- ✅ Lưu trữ lịch sử giao tiếp (log + chat)

---

## 6. HƯỚNG DẪN TRIỂN KHAI

### 6.1 Giai Đoạn 1: Lõi Thuật Toán (Tuần 1-2)
```python
# Kiểm tra số nguyên tố (Miller-Rabin)
def is_prime(n, k=40):
    """Kiểm tra số nguyên tố dùng Miller-Rabin"""
    pass

# Tìm căn nguyên thủy
def find_primitive_root(p):
    """Tìm g sao cho g là căn nguyên thủy mod p"""
    pass

# Tính khóa chung
def dh_key_exchange():
    """Mô phỏng trao đổi khóa hoàn chỉnh"""
    pass
```

### 6.2 Giai Đoạn 2: Relay TCP (Tuần 3)

**relay_server.py** — server trung gian trên máy host:

```python
# Chạy một lần trên máy host
python relay_server.py
# Mặc định bind 0.0.0.0:5001 (config bind_host)
```

**dh_client.py / dh_gui_app.py** — client kết nối tới server:

```python
# Client đọc server_host từ config.json
from app_config import get_server_host, get_server_port

host = get_server_host()   # 127.0.0.1 (localhost) hoặc IP máy host
port = get_server_port()   # 5001

# GUI: người dùng chọn alice/bob → Connect
# Không start server trong GUI
```

**Luồng demo GUI:**
1. Host: `python relay_server.py`
2. User A: `python dh_gui_app.py` → Alice → Connect
3. User B: `python dh_gui_app.py` → Bob → Connect
4. So fingerprint → Send Encrypted

### 6.3 Giai Đoạn 3: Mã Hóa & An Toàn (Tuần 4)
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

# Tạo cipher từ khóa chung
def create_cipher(shared_secret):
    """Chuyển khóa DH thành khóa AES"""
    key = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'dh_salt',
        iterations=100000
    ).derive(str(shared_secret).encode())
    
    cipher = Fernet(urlsafe_b64encode(key))
    return cipher

# Mã hóa thông điệp
def encrypt_message(message, shared_secret):
    cipher = create_cipher(shared_secret)
    encrypted = cipher.encrypt(message.encode())
    return encrypted

# Giải mã thông điệp
def decrypt_message(encrypted, shared_secret):
    cipher = create_cipher(shared_secret)
    decrypted = cipher.decrypt(encrypted).decode()
    return decrypted
```

---

## 7. KIỂM THỬ VÀ ĐÁNH GIÁ

### 7.1 Test Cases

| Test | Mục Đích | Kết Quả Mong Muốn |
|------|----------|------------------|
| `test_prime_generation` | Kiểm tra sinh số nguyên tố | Trả về số nguyên tố hợp lệ |
| `test_primitive_root` | Kiểm tra căn nguyên thủy | g là căn nguyên thủy mod p |
| `test_shared_secret_equal` | Khóa chung bằng nhau | K(Alice) = K(Bob) |
| `test_different_private_keys` | Khóa bí mật khác nhau | a ≠ b |
| `test_encryption_decryption` | Mã hóa/giải mã | Thông điệp ban đầu = thông điệp giải mã |
| `test_mitm_attack` | Phát hiện MITM | Khóa không trùng khớp |

### 7.2 Metrics Hiệu Suất

```
┌─────────────┬──────────┬──────────┬──────────┐
│ Bit Length  │ Time (s) │ Key Size │ Security │
├─────────────┼──────────┼──────────┼──────────┤
│ 1024 bit    │ 0.2      │ 128 byte │ ⚠️ Yếu   │
│ 2048 bit    │ 2.5      │ 256 byte │ ✅ Tốt  │
│ 4096 bit    │ 15.0     │ 512 byte │ ✅ Tuyệt │
└─────────────┴──────────┴──────────┴──────────┘
```

---

## 8. PHÂN TÍCH AN TOÀN

### 8.1 Tấn Công Có Thể Xảy Ra

**1. Man-in-the-Middle (MITM)**
```
Attacker Eve can:
- Intercept A from Alice
- Intercept B from Bob
- Impersonate Alice to Bob (send A' = g^e mod p)
- Impersonate Bob to Alice (send B' = g^e mod p)
- Compute K1 = B^e mod p, K2 = A^e mod p

Phòng chống:
→ Sử dụng Digital Signature (RSA/ECDSA)
→ Certificate Authority (CA)
→ Mutual Authentication
```

**2. Brute Force Attack**
```
Attacker tries all possible values of a
Cost: O(√p) with Pollard's rho algorithm

Phòng chống:
→ Sử dụng số nguyên tố p rất lớn (2048+ bit)
→ Chọn safe prime: p = 2q + 1 (q cũng nguyên tố)
```

**3. Side-Channel Attack**
```
Phòng chống:
→ Dùng constant-time multiplication
→ Timing-safe comparison
```

### 8.2 Khuyến Nghị An Toàn

| Yêu Cầu | Khuyến Nghị |
|---------|------------|
| Prime Size | Tối thiểu 2048 bit |
| Generator | g = 2 (cân bằng performance/security) |
| Authentication | Dùng HMAC hoặc chữ ký số |
| Transport | TLS/SSL mã hóa |

---

## 9. CẤU TRÚC BÁO CÁO

### 9.1 Nội Dung Báo Cáo (15-20 trang)

**1. Giới Thiệu** (2-3 trang)
- Lịch sử DH
- Tầm quan trọng
- Mục tiêu dự án

**2. Cơ Sở Lý Thuyết** (3-4 trang)
- Kiến thức Toán học (Modular Arithmetic, Primitive Root)
- Nguyên lý DH chi tiết
- Độ phức tạp thuật toán

**3. Thiết Kế Hệ Thống** (3-4 trang)
- Kiến trúc ứng dụng
- Flow diagram
- Class diagram
- Database schema (nếu có)

**4. Triển Khai** (3-4 trang)
- Code chính
- Hướng dẫn cài đặt
- Giao diện người dùng

**5. Kiểm Thử & Đánh Giá** (2-3 trang)
- Test cases
- Kết quả test
- Phân tích hiệu suất

**6. An Ninh & Tấn Công** (2-3 trang)
- Phân tích lỗ hổng
- MITM attack simulation
- Cách phòng chống

**7. Kết Luận** (1-2 trang)
- Tóm tắt
- Hạn chế
- Hướng phát triển tương lai

---

## 10. LƯU Ý QUAN TRỌNG

### 10.1 Không Nên Làm

❌ Không sử dụng số nguyên tố nhỏ (< 1024 bit)
❌ Không mã hóa bằng DH trực tiếp (DH chỉ trao đổi khóa)
❌ Không bỏ qua authentication
❌ Không dùng fixed/weak generator

### 10.2 Best Practices

✅ Luôn kiểm tra a, b ∈ [2, p-2]
✅ Sử dụng secure random number generator
✅ Implement authentication layer
✅ Ghi log tất cả hoạt động
✅ Test coverage ≥ 80%

---

## 11. THAM KHẢO THÊM

### Tài Liệu
- NIST SP 800-56A: Recommendation for Pair-Wise Key Establishment Schemes
- RFC 2631: Diffie-Hellman Key Agreement Method
- RFC 3526: More Modular Exponential (MODP) Diffie-Hellman groups

### Thư Viện
- `cryptography`: https://cryptography.io/
- `pycryptodome`: https://pycryptodome.readthedocs.io/

### Công Cụ
- Wireshark: Phân tích gói tin
- IDA Pro: Reverse engineering
- OpenSSL: Tính toán DH

---

**Tài Liệu này được cập nhật lần cuối: 2024-01-15**
