# Diffie-Hellman Key Exchange - Hướng Dẫn Sử Dụng

## 📋 Giới Thiệu

Dự án này là một **ứng dụng hoàn chỉnh về trao đổi khóa bảo mật Diffie-Hellman** cho môn An Ninh Mạng.

### Tính Năng Chính:
- ✅ Triển khai đầy đủ thuật toán Diffie-Hellman
- ✅ Mô phỏng giao tiếp giữa Alice và Bob (local)
- ✅ Client–server relay qua TCP socket thật
- ✅ Giao diện desktop client-only (`dh_gui_app.py`)
- ✅ Hỗ trợ trao đổi khóa đến 4096 bit
- ✅ Mã hóa thông điệp (AES-256 / Fernet)
- ✅ Mô phỏng tấn công MITM
- ✅ Unit tests toàn diện (80%+ coverage)
- ✅ Phân tích bảo mật chi tiết

---

## 📁 Cấu Trúc Tệp

```
DIffie-Hellman/
├── diffie_hellman.py            # Lõi DH + Alice/Bob + demo local
├── relay_server.py              # Relay server (chạy trên máy host)
├── dh_client.py                 # Client CLI (Alice/Bob)
├── dh_gui_app.py                # Client GUI (người dùng cuối)
├── app_config.py                # Đọc config.json
├── config.json                  # server_host, bind_host, port...
├── advanced_examples.py         # MITM + AES encryption
├── test_diffie_hellman.py       # Unit tests
├── requirements.txt             # Python dependencies
├── README.md                    # Hướng dẫn chi tiết
├── QUICKSTART.md                # Bắt đầu nhanh
├── DH_Project_Guide.md          # Hướng dẫn xây dựng dự án
├── TIMELINE_CHECKLIST.md        # Timeline 4 tuần
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

### 5. Chạy Mô Hình Client-Server Relay

Mô hình này dùng một **relay server** làm "bưu tá". Server chỉ chuyển tiếp `p`, `g`, public key và ciphertext. Server **không** tính, **không** biết, và **không** lưu shared secret.

#### Kiến trúc

```
Máy host (bạn)          Máy client (người dùng)
relay_server.py    ◄── TCP ──►  dh_gui_app.py (Alice)
                         ◄── TCP ──►  dh_gui_app.py (Bob)
```

- **Host**: chỉ chạy `relay_server.py` một lần.
- **Client**: chỉ chạy GUI hoặc `dh_client.py`, không cần start server.

#### Cấu hình `config.json`

```json
{
  "server_host": "127.0.0.1",
  "server_port": 5001,
  "bind_host": "0.0.0.0",
  "timeout": 60.0,
  "bit_length": 256
}
```

| Key | Dùng cho | Ý nghĩa |
|-----|----------|---------|
| `server_host` | Client (GUI/CLI) | Địa chỉ server để kết nối |
| `server_port` | Cả hai | Port TCP |
| `bind_host` | Server | `0.0.0.0` = lắng nghe mọi interface trên máy host |

**Test trên 1 máy:** giữ `server_host: "127.0.0.1"` — vẫn dùng TCP socket thật qua loopback.

**Test trên nhiều máy:** đặt `server_host` thành IP máy chạy server (ví dụ `192.168.1.100`) trên **mỗi máy client**.

#### Chạy bằng CLI

Mở 3 terminal trên máy host (hoặc server riêng + 2 client):

```bash
# Terminal 1: relay server (máy host)
python relay_server.py
```

```bash
# Terminal 2: Alice
python dh_client.py alice
```

```bash
# Terminal 3: Bob
python dh_client.py bob
```

Luồng hoạt động:
1. Alice gửi `p`, `g`, `A = g^a mod p` lên server.
2. Server chuyển tiếp các giá trị công khai đó cho Bob.
3. Bob gửi `B = g^b mod p` lên server.
4. Server chuyển tiếp `B` cho Alice.
5. Alice tính `K = B^a mod p`, Bob tính `K = A^b mod p`.
6. Hai bên in cùng fingerprint; server chỉ thấy public values/ciphertext.

### 6. Chạy Giao Diện Desktop (Client)

GUI là **client-only** — người dùng không start server trên app.

**Bước 1 — Máy host:** chạy server trước

```bash
python relay_server.py
```

**Bước 2 — Mỗi người dùng:** mở GUI

```bash
python dh_gui_app.py
```

Cách demo trên **1 máy** (localhost):
1. Terminal: `python relay_server.py`
2. Cửa sổ GUI 1: chọn **alice** → **Connect**
3. Cửa sổ GUI 2: chọn **bob** → **Connect**
4. Khi cả hai hiện cùng **Fingerprint**, gõ tin nhắn → **Send Encrypted**

GUI đọc `server_host` và `server_port` từ `config.json` (hiển thị read-only trên giao diện). Chat mã hóa hai chiều qua relay server.

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

### Module 3: Relay & GUI (mạng TCP)

**Chạy server (máy host):**

```bash
python relay_server.py
```

**Client GUI:**

```bash
python dh_gui_app.py
# Chọn alice/bob → Connect → chat sau khi fingerprint khớp
```

**Client CLI:**

```bash
python dh_client.py alice
python dh_client.py bob
```

Cấu hình trong `config.json` — xem mục **5. Chạy Mô Hình Client-Server Relay**.

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

## 📝 Chuẩn Bị Báo Cáo

### Cấu Trúc Báo Cáo:

1. **Giới Thiệu (2-3 trang)**
   - Lịch sử DH
   - Tầm quan trọng
   - Mục tiêu dự án

2. **Lý Thuyết (4-5 trang)**
   - Modular Arithmetic
   - Nguyên lý DH
   - Độ phức tạp

3. **Thiết Kế & Triển Khai (4-5 trang)**
   - Kiến trúc
   - Sơ đồ lớp
   - Code mẫu

4. **Kiểm Thử (2-3 trang)**
   - Test cases
   - Kết quả
   - Hiệu suất

5. **Bảo Mật (3-4 trang)**
   - Lỗ hổng
   - Phòng chống
   - Phân tích MITM

6. **Kết Luận (1-2 trang)**
   - Tóm tắt
   - Hạn chế
   - Hướng phát triển

### Hình ảnh & Biểu đồ cần có:

```
□ Sơ đồ nguyên lý DH
□ Sơ đồ kiến trúc (Alice-Bob-Eve)
□ Biểu đồ độ phức tạp thời gian
□ Bảng so sánh (bit_length vs time)
□ Sơ đồ tấn công MITM
□ Code snippet quan trọng
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
   # Flask/Django web app
   # Real-time visualization
   # Interactive demo
   ```

---

## 🐛 Gỡ Lỗi

### Lỗi Thường Gặp:

| Lỗi | Nguyên Nhân | Giải Pháp |
|-----|-----------|----------|
| `Connect failed` | Server chưa chạy hoặc sai `server_host` | Chạy `relay_server.py`; kiểm tra IP/port/firewall |
| `Timeout` | Bit length quá lớn hoặc server không phản hồi | Giảm bit_length; tăng `timeout` trong config |
| `K(Alice) ≠ K(Bob)` | Tham số p,g khác nhau | Chia sẻ cùng p,g |
| `ValueError: Invalid key` | Khóa bí mật ngoài [2,p-2] | Check generate_private_key() |
| `ImportError` | Thiếu cryptography | `pip install cryptography` |
| `UnicodeEncodeError` (Windows) | Console không in được tiếng Việt | `$env:PYTHONIOENCODING="utf-8"` trước khi chạy test |

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

---

## 📞 Hỗ Trợ & Liên Hệ

Nếu gặp vấn đề:

1. **Check lại code**: So với file mẫu
2. **Đọc error message**: Thường nó chỉ rõ vấn đề
3. **Google**: "Diffie-Hellman [lỗi]"
4. **Hỏi thầy/cô**: Cung cấp code + error trace

---

## 📄 License

Code này được cung cấp cho mục đích **giáo dục**. Tự do sử dụng, sửa đổi, nhưng không tính lợi nhuận.

---

**Cập nhật lần cuối: 2026-06-04**

Chúc bạn hoàn thành dự án thành công! 🎓🔐
