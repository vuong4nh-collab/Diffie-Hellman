# Diffie-Hellman Key Exchange - Hướng Dẫn Sử Dụng

## 📋 Giới Thiệu

Dự án này là một **ứng dụng hoàn chỉnh về trao đổi khóa bảo mật Diffie-Hellman** cho môn An Ninh Mạng.

### Tính Năng Chính:
- ✅ Triển khai đầy đủ thuật toán Diffie-Hellman
- ✅ Mô phỏng giao tiếp giữa Alice và Bob (local)
- ✅ Giao diện Web mô phỏng trực quan & chat real-time (`web_app.py`)
- ✅ Hỗ trợ trao đổi khóa đến 4096 bit
- ✅ Mã hóa thông điệp (AES-256 / Fernet)
- ✅ Mô phỏng tấn công MITM (Eavesdropping & Decryption)
- ✅ Unit tests toàn diện (80%+ coverage)
- ✅ Phân tích bảo mật chi tiết

---

## 📁 Cấu Trúc Tệp

```
DIffie-Hellman/
├── diffie_hellman.py            # Lõi DH + Alice/Bob + demo local
├── web_app.py                   # Web App Flask + SocketIO (Demo trực quan)
├── app_config.py                # Đọc config.json
├── config.json                  # server_host, bind_host, port...
├── advanced_examples.py         # MITM + AES encryption
├── test_diffie_hellman.py       # Unit tests
├── requirements.txt             # Python dependencies
├── README.md                    # Hướng dẫn chi tiết
├── QUICKSTART.md                # Bắt đầu nhanh
├── DEMO_GUIDE.md                # Kịch bản demo báo cáo
├── DH_Project_Guide.md          # Hướng dẫn xây dựng dự án
├── TIMELINE_CHECKLIST.md        # Timeline 4 tuần
├── templates/
│   └── index.html               # Giao diện HTML của Web App
├── static/
│   ├── css/
│   │   └── style.css            # Stylesheet cho Web App
│   └── js/
│       └── app.js               # Logic SocketIO & UI cho Web App
└── 00_SUMMARY.md                # Tóm tắt package
```

---

## 🚀 Cài Đặt & Chạy

### 1. Cài Đặt Dependencies

```bash
# Tạo virtual environment (tùy chọn)
python3 -m venv venv
source venv/bin/activate

# Cài đặt thư viện
pip install cryptography
```

### 2. Chạy Demo Cơ Bản

```bash
# Chạy toàn bộ quá trình DH (512 bit - nhanh)
python3 diffie_hellman.py
```

**Output mong muốn:**
```
======================================================================
DIFFIE-HELLMAN KEY EXCHANGE PROTOCOL
======================================================================

[Step 0] Khởi tạo Alice và Bob
[*] Sinh số nguyên tố 512 bit...
[*] Tìm căn nguyên thủy...
[✓] DH Parameters ready
    p (prime): 8123456...
    g (generator): 2
...
[THÀNH CÔNG] Cả hai đã tính ra khóa bí mật chung giống nhau!
```

### 3. Chạy Unit Tests

```bash
python3 test_diffie_hellman.py
```

**Output mong muốn:**
```
test_alice_bob_different_keys (test_diffie_hellman.TestAliceAndBob) ... ok
test_alice_generate_keys (test_diffie_hellman.TestAliceAndBob) ... ok
test_bob_generate_keys (test_diffie_hellman.TestAliceAndBob) ... ok
...

======================================================================
TEST SUMMARY
======================================================================
Tests run: 30
Successes: 30
Failures: 0
Errors: 0
```

### 4. Chạy Ví Dụ Nâng Cao

```bash
python3 advanced_examples.py
```

**Bao gồm:**
- ⚠️ Mô phỏng tấn công MITM
- 🔐 Mã hóa thông điệp với khóa chung
- 🛡️ Cách phòng chống MITM

### 5. Chạy Giao Diện Web (Flask & Socket.IO)

Ứng dụng web cung cấp một giao diện mô phỏng trực quan, sinh động luồng trao đổi khóa và cho phép chat mã hóa hai chiều với các biểu đồ về Entropy dữ liệu, danh sách gói tin bị Eve chặn đứng (intercepted packets) và nhật ký chi tiết.

#### Cách Chạy:

1. **Khởi động server Web Flask:**
   ```bash
   python web_app.py
   ```
   Server sẽ đọc cấu hình từ `config.json` và khởi chạy (mặc định tại `http://localhost:5001`).

2. **Truy cập giao diện Web:**
   Mở trình duyệt và truy cập: `http://localhost:5001` (hoặc IP máy chủ tương ứng).

#### Hai Chế Độ Hoạt Động Trên Web:

*   **Mô phỏng Tại chỗ (Simulation Mode - Khuyên dùng):**
    *   Thao tác toàn bộ quá trình trao đổi khóa ngay trên **1 màn hình duy nhất**.
    *   Nhấp chọn lần lượt các nút:
        1. **Bước 1: Tạo Params (p, g) và Khóa A** (Alice sinh khóa và gửi tham số).
        2. **Bước 2: Phản hồi Khóa B** (Bob nhận tham số, sinh khóa B và gửi lại).
        3. **Bước 3: Thiết lập Khóa Chung** (Cả hai cùng tính toán ra khóa bí mật $K$).
    *   Sau khi khóa chung được thiết lập thành công, giao diện chat bảo mật sẽ xuất hiện. Bạn có thể gửi tin nhắn qua lại để xem quá trình mã hóa AES-256-CBC diễn ra trực quan.
*   **Kết nối Mạng (Relay Mode):**
    *   Mở hai tab trình duyệt khác nhau (hoặc hai thiết bị khác nhau trong cùng mạng LAN).
    *   Chọn **Chế độ: Kết nối Mạng** và chọn **Vai trò** (một bên chọn **Alice**, bên kia chọn **Bob**).
    *   Nhấp **Kết nối** trên cả hai giao diện.
    *   Thực hiện trao đổi khóa và nhắn tin real-time thông qua máy chủ relay Socket.IO.

#### Eve's View (Hacker Terminal):
*   Tại cột bên phải, tab **Eve's View** mô phỏng một hacker (Eve) đang bắt gói tin trên mạng (`eth0`).
*   Khi Alice và Bob trao đổi các tham số công khai (`p`, `g`, public keys `A` và `B`), Eve sẽ **chặn và đọc được** toàn bộ thông tin này dưới dạng bản rõ (Insecure Phase).
*   Tuy nhiên, khi Alice và Bob chuyển sang nhắn tin mã hóa, Eve chỉ thu thập được các gói tin có nhãn `CIPHERTEXT` với payload đã được mã hóa AES.
*   Biểu đồ Entropy dữ liệu sẽ trực quan hóa độ hỗn loạn của dữ liệu (Entropy tăng cao gần bằng 1 khi truyền ciphertext, thể hiện tính bảo mật cao).

---

## 📖 Cách Sử Dụng Từng Module

### Module 1: diffie_hellman.py

**Sử dụng cơ bản:**

```python
from diffie_hellman import Alice, Bob

# Tạo Alice và Bob
alice = Alice(bit_length=256)
bob = Bob(bit_length=256)

# Bước 1: Sinh khóa
A = alice.step1_generate_keys()
B = bob.step1_generate_keys()

# Bước 2: Trao đổi khóa công khai
bob.step2_receive_alice_key(A)
alice.step2_receive_bob_key(B, bob.dh.get_parameters())

# Bước 3: Tính khóa bí mật chung
K_alice = alice.step3_compute_shared_secret()
K_bob = bob.step3_compute_shared_secret()

# Kiểm tra
assert K_alice == K_bob, "Keys should be equal!"
print(f"Shared secret: {K_alice}")
```

**Sử dụng DH trực tiếp:**

```python
from diffie_hellman import DiffieHellman

# Tạo DH instance
dh1 = DiffieHellman(bit_length=2048)
dh2 = DiffieHellman(bit_length=2048)  # Chia sẻ p, g

# Sinh khóa bí mật
a = dh1.generate_private_key()
b = dh2.generate_private_key()

# Tính khóa công khai
A = dh1.generate_public_key()
B = dh2.generate_public_key()

# Tính khóa bí mật chung
K1 = dh1.compute_shared_secret(B)
K2 = dh2.compute_shared_secret(A)

assert K1 == K2
```

### Module 2: advanced_examples.py

**Mã hóa thông điệp:**

```python
from advanced_examples import EncryptedMessenger

# K là khóa bí mật chung từ DH
messenger = EncryptedMessenger(shared_secret=K)

# Mã hóa
encrypted = messenger.encrypt("Hello Bob!")
print(encrypted)
# {'ciphertext': '...', 'iv': '...', 'plaintext_length': 11}

# Giải mã
decrypted = messenger.decrypt(encrypted)
assert decrypted == "Hello Bob!"
```

**Mô phỏng MITM:**

```python
from advanced_examples import simulate_mitm_attack

result = simulate_mitm_attack()
# In ra chi tiết tấn công MITM của Eve
```

Cấu hình trong `config.json` — xem mục **5. Chạy Giao Diện Web**.

### Module 3: web_app.py (Web App Flask + SocketIO)

Khởi chạy ứng dụng web phục vụ việc mô phỏng trực quan và thực hành:
```bash
python web_app.py
```
*   `reset_session_state()`: Reset toàn bộ thông tin khóa học và nhật ký.
*   `add_intercepted_packet()`: Gửi gói tin thu thập được lên giao diện của Eve.
*   `handle_chat_message()`: Trung chuyển các thông điệp đã mã hóa cùng vector khởi tạo (IV).

### Module 4: test_diffie_hellman.py

**Chạy test cụ thể:**

```python
import unittest
from test_diffie_hellman import TestAliceAndBob

# Chạy một test cụ thể
suite = unittest.TestLoader().loadTestsFromTestCase(TestAliceAndBob)
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
```

---

## 🔧 Thay Đổi Độ Dài Bit

Độ dài bit ảnh hưởng đến:
- **An toàn**: Lớn hơn → An toàn hơn
- **Tốc độ**: Lớn hơn → Chậm hơn

### Khuyến Nghị:

| Bit Length | Thời Gian | An Ninh | Dùng Cho |
|-----------|----------|--------|---------|
| 256 bit   | <1 giây   | ⚠️ Yếu | Demo/Test |
| 512 bit   | ~1 giây   | ⚠️ Yếu | Learning |
| 1024 bit  | ~5 giây   | ⚠️ Yếu | Education |
| 2048 bit  | ~30 giây  | ✅ Tốt | Production |
| 4096 bit  | ~3 phút   | ✅ Tuyệt | High Security |

### Ví dụ:

```python
# Dùng 1024 bit cho testing
alice = Alice(bit_length=1024)
bob = Bob(bit_length=1024)

# Dùng 2048 bit cho demo thực tế
alice = Alice(bit_length=2048)
bob = Bob(bit_length=2048)
```

---

## 📊 Output và Kết Quả

### Output Chuẩn (không lỗi):

```
[✓] DH Parameters ready
    p (prime): 123456789...
    g (generator): 2

[→] Alice → Bob
    Message: {"type": "public_key", "A": 987654...}

[✓] [THÀNH CÔNG] Cả hai đã tính ra khóa bí mật chung giống nhau!
```

### Output Lỗi (cần sửa):

```
# Lỗi 1: Khóa không giống nhau
Alice's K == Bob's K? False
✗ [THẤT BẠI] Khóa bí mật không giống nhau!

# Lỗi 2: Timeout (bit_length quá lớn)
TimeoutError: Computation took too long
→ Giảm bit_length hoặc tăng timeout
```

---

## 🧪 Unit Testing

### Chạy tất cả tests:

```bash
python3 test_diffie_hellman.py -v
```

### Chạy test cụ thể:

```bash
python3 -m unittest test_diffie_hellman.TestAliceAndBob.test_full_key_exchange -v
```

### Test Coverage:

```bash
pip install coverage
coverage run -m pytest test_diffie_hellman.py
coverage report
coverage html
```

---

## 🔐 Bảo Mật & Cảnh Báo

### ⚠️ KHÔNG NÊN LÀM:

```python
# ❌ Sai: Dùng số bit quá nhỏ
alice = Alice(bit_length=64)  # KHÔNG AN TOÀN!

# ❌ Sai: Không kiểm tra khóa
if a < 2 or a > p - 2:  # Bỏ qua kiểm tra
    pass

# ❌ Sai: Dùng weak generator
g = 1  # Không hợp lệ!

# ❌ Sai: Reuse khóa bí mật
shared_secret = K
shared_secret = K  # Session mới nên dùng khóa khác
```

### ✅ NÊN LÀM:

```python
# ✅ Đúng: Dùng bit_length phù hợp
alice = Alice(bit_length=2048)

# ✅ Đúng: Kiểm tra khóa bí mật
if not (2 <= private_key <= p - 2):
    raise ValueError("Invalid private key")

# ✅ Đúng: Dùng generator hợp lệ
g = find_primitive_root(p)

# ✅ Đúng: Mỗi session mới dùng khóa mới
for session in sessions:
    K_new = compute_shared_secret(...)
    # Không reuse K_new
```

---


## 🎯 Ý Tưởng Mở Rộng

### Tính Năng Nâng Cao:

1. **Elliptic Curve DH (ECDH)**
   ```python
   from cryptography.hazmat.primitives.asymmetric import ec
   # Nhanh hơn DH truyền thống
   ```

2. **Forward Secrecy**
   ```python
   # Mỗi session dùng khóa khác
   # Ngay cả khóa lâu dài bị compromise cũng không ảnh hưởng
   ```

3. **Zero-Knowledge Proof**
   ```python
   # Alice chứng minh biết a mà không tiết lộ a
   ```

4. **Multiparty Key Exchange**
   ```python
   # Hơn 2 người trao đổi khóa
   # Ví dụ: Alice, Bob, Carol, Dave
   ```

5. **Web Interface**
   ```python
   # Flask/SocketIO Web App đã tích hợp sẵn (web_app.py)
   # Real-time visualization & chat
   ```

---

## 🐛 Gỡ Lỗi

### Lỗi Thường Gặp:

| Lỗi | Nguyên Nhân | Giải Pháp |
|-----|-----------|----------|
| `Timeout` | Bit length quá lớn | Giảm bit_length trong config |
| `K(Alice) ≠ K(Bob)` | Tham số p,g khác nhau | Chia sẻ cùng p,g |
| `ValueError: Invalid key` | Khóa bí mật ngoài [2,p-2] | Check generate_private_key() |
| `ImportError` | Thiếu cryptography / flask / flask-socketio | `pip install -r requirements.txt` |
| `UnicodeEncodeError` (Windows) | Console không in được tiếng Việt | `$env:PYTHONIOENCODING="utf-8"` trước khi chạy test |
| `WebSocket connection failed` (Web App) | Flask-SocketIO không tương thích hoặc chưa cài `simple-websocket` | `pip install simple-websocket` và khởi chạy lại `web_app.py` |
| `Address already in use` | Cổng 5001 đang được ứng dụng khác sử dụng | Thay đổi `server_port` trong `config.json` hoặc tắt tiến trình đang chiếm cổng |

### Debug Mode:

```python
# Thêm logging chi tiết
import logging
logging.basicConfig(level=logging.DEBUG)

# In intermediate values
print(f"[DEBUG] p = {dh.p}")
print(f"[DEBUG] g = {dh.g}")
print(f"[DEBUG] a = {alice.dh.private_key}")
print(f"[DEBUG] A = {alice.dh.public_key}")
```

---

## 📚 Tài Liệu Tham Khảo

### Chuẩn & RFC:
- **NIST SP 800-56A**: Pair-Wise Key Establishment
- **RFC 2631**: Diffie-Hellman Key Agreement
- **RFC 3526**: More MODP DH groups

### Thư Viện:
- [cryptography.io](https://cryptography.io/)
- [PyCryptodome](https://pycryptodome.readthedocs.io/)

### Bài Viết:
- [Illustrated Diffie-Hellman](https://medium.com/)
- [Discrete Log Problem](https://en.wikipedia.org/)

---

## 💡 Mẹo & Thủ Thuật

### 1. Tăng Tốc Độ Test:

```python
# Dùng 256-bit thay vì 2048-bit
alice = Alice(256)  # ~1 giây thay vì ~30 giây
```

### 2. Tái Sử Dụng Tham Số:

```python
# Chia sẻ p, g giữa các session
params = alice.dh.get_parameters()
bob.dh.p = params.p
bob.dh.g = params.g
```

### 3. Parallel Key Generation:

```python
from multiprocessing import Pool

def gen_prime(bit):
    return generate_prime(bit)

with Pool(4) as p:
    primes = p.map(gen_prime, [256, 256, 256, 256])
```

### 4. Validate Input:

```python
def validate_dh_params(p, g):
    assert is_prime(p), "p must be prime"
    assert 2 <= g < p, "g must be in [2, p-1]"
    # Có thể check thêm: g là primitive root
```


