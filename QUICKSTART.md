# 🚀 QUICK START - HƯỚNG DẪN NHANH

Chỉ 5 phút để chạy được ứng dụng Diffie-Hellman!

---

## 1️⃣ CÀI ĐẶT (2 phút)

### Bước 1: Clone/Download code

```bash
# Sao chép tất cả các file Python vào một thư mục
mkdir DH_Project
cd DH_Project
# Copy: diffie_hellman.py, advanced_examples.py, test_diffie_hellman.py
```

### Bước 2: Cài đặt dependency

```bash
pip install cryptography
```

**Xong!** ✅

---

## 2️⃣ CHẠY DEMO NGAY (1 phút)

### Demo Cơ Bản - Trao Đổi Khóa

```bash
python3 diffie_hellman.py
```

**Output:**
```
======================================================================
DIFFIE-HELLMAN KEY EXCHANGE PROTOCOL
======================================================================

[Step 0] Khởi tạo Alice và Bob
[*] Sinh số nguyên tố 512 bit...
[*] Tìm căn nguyên thủy...
[✓] DH Parameters ready

[Step 1] Alice và Bob sinh cặp khóa
[13:45:12] Alice: Generated private key (secret): a = 456789...
[13:45:12] Alice: Computed public key: A = g^a mod p = 234567...

[Step 2] Trao đổi khóa công khai
[→] Alice → Bob
    Message: {"type": "public_key", "A": 234567...}

[THÀNH CÔNG] Cả hai đã tính ra khóa bí mật chung giống nhau!
```

### Demo Nâng Cao - MITM + Encryption

```bash
python3 advanced_examples.py
```

**Output:**
```
MITM ATTACK SIMULATION
======================================================================
[!] Eve initialized as Man-in-the-Middle attacker
[!] Eve intercepted: Alice → Bob
[!] Eve computed secret with Alice
[!] Eve computed secret with Bob
[!] Eve intercepted thông điệp mã hóa
[!] Eve giải mã với khóa: K_eve_alice = ...
[!] EVE ĐÃ ĐỌC THÔNG ĐIỆP CỦA ALICE!
```

### Demo Client-Server Relay

Server chỉ chuyển tiếp public values giữa Alice và Bob, không biết shared secret.

**Trên máy host** — chạy server trước:

```bash
python relay_server.py
```

**Trên cùng máy hoặc máy khác** — chạy client:

```bash
# Terminal 2
python dh_client.py alice

# Terminal 3
python dh_client.py bob
```

Mặc định client kết nối tới `server_host` trong `config.json` (`127.0.0.1` khi test localhost).

Alice và Bob in cùng `Shared secret fingerprint`. CLI gửi một tin nhắn mã hóa và nhận một reply rồi thoát.

### Demo Giao Diện Desktop (Client)

**Bước 1:** trên máy host:

```bash
python relay_server.py
```

**Bước 2:** mở 2 cửa sổ GUI:

```bash
python dh_gui_app.py
```

1. Cửa sổ 1: chọn **alice** → **Connect**
2. Cửa sổ 2: chọn **bob** → **Connect**
3. Khi fingerprint giống nhau → **Send Encrypted** (chat hai chiều)

GUI **không** có nút start server — người dùng chỉ thao tác Connect và chat.

### Cấu hình mạng (`config.json`)

```json
{
  "server_host": "127.0.0.1",
  "server_port": 5001,
  "bind_host": "0.0.0.0",
  "timeout": 60.0,
  "bit_length": 256
}
```

| Tình huống | `server_host` |
|-----------|---------------|
| Test 1 máy | `127.0.0.1` (không cần đổi) |
| 2+ máy cùng LAN | IP máy chạy `relay_server.py` |

---

## 3️⃣ CHẠY TESTS (1 phút)

```bash
python3 test_diffie_hellman.py
```

**Output:**
```
test_alice_bob_different_keys ... ok
test_alice_generate_keys ... ok
test_bob_generate_keys ... ok
...
======================================================================
TEST SUMMARY
======================================================================
Tests run: 30
Successes: 30
Failures: 0
```

---

## 4️⃣ CODE ĐƠN GIẢN (1 phút)

### Sử dụng trực tiếp trong code của bạn:

```python
from diffie_hellman import Alice, Bob

# Tạo Alice và Bob
alice = Alice(bit_length=256)  # 256 bit để nhanh
bob = Bob(bit_length=256)

# Bước 1: Sinh khóa
A = alice.step1_generate_keys()
B = bob.step1_generate_keys()

# Bước 2: Trao đổi khóa
bob.step2_receive_alice_key(A)
alice.step2_receive_bob_key(B, bob.dh.get_parameters())

# Bước 3: Tính khóa bí mật chung
K_alice = alice.step3_compute_shared_secret()
K_bob = bob.step3_compute_shared_secret()

# Kiểm tra
print(f"Alice's K: {K_alice}")
print(f"Bob's K:   {K_bob}")
print(f"Equal? {K_alice == K_bob}")  # True ✅
```

### Sử dụng Encryption:

```python
from advanced_examples import EncryptedMessenger

# K là khóa bí mật chung từ DH
messenger = EncryptedMessenger(shared_secret=K_alice)

# Mã hóa
message = "Hello Bob!"
encrypted = messenger.encrypt(message)

# Giải mã
decrypted = messenger.decrypt(encrypted)
assert decrypted == message
```

---

## 5️⃣ TÙYCHỈNH THAM SỐ

### Thay Đổi Độ Dài Bit:

```python
# 256 bit: nhanh nhất (< 1 giây)
alice = Alice(bit_length=256)

# 512 bit: nhanh (1-2 giây)
alice = Alice(bit_length=512)

# 1024 bit: chậm (5-10 giây)
alice = Alice(bit_length=1024)

# 2048 bit: rất chậm (30-60 giây)
alice = Alice(bit_length=2048)
```

### Khuyến Nghị:

| Tình Huống | Bit Length |
|-----------|-----------|
| Demo/Test | 256-512 |
| Learning | 512-1024 |
| Production | 2048+ |

---

## 🎯 CÁC BƯỚC TIẾP THEO

### Nếu Muốn Hiểu Sâu Hơn:

1. **Đọc code**: Mở `diffie_hellman.py`, đọc comments
2. **Chạy từng bước**: Thêm breakpoints, debug
3. **Thay đổi**: Sửa code, chạy lại
4. **Thực nghiệm**: Test với bit_length khác nhau

### Nếu Muốn Mở Rộng:

1. **Thêm mã hóa**: Sử dụng `EncryptedMessenger`
2. **Thêm authentication**: Dùng Digital Signature
3. **Thêm MITM defense**: Implement Certificate
4. **Web interface**: Dùng Flask/Django

---

## ⚡ QUICK REFERENCE

### Các Lệnh Hay Dùng

```bash
# Chạy relay server (máy host)
python relay_server.py

# Chạy GUI client
python dh_gui_app.py

# Chạy client CLI
python dh_client.py alice
python dh_client.py bob

# Chạy demo cơ bản (local, không TCP)
python3 diffie_hellman.py

# Chạy demo nâng cao
python3 advanced_examples.py

# Chạy tests
python3 test_diffie_hellman.py

# Chạy test cụ thể
python3 -m unittest test_diffie_hellman.TestAliceAndBob -v

# Check code style
python3 -m py_compile diffie_hellman.py

# Performance test
python3 -c "
from diffie_hellman import Alice
import time

for bits in [256, 512, 1024]:
    start = time.time()
    alice = Alice(bits)
    elapsed = time.time() - start
    print(f'{bits}-bit: {elapsed:.2f}s')
"
```

### Các Hàm Quan Trọng

```python
# Hàm toán học
is_prime(n)           # Kiểm tra số nguyên tố
generate_prime(bits)  # Sinh số nguyên tố
find_primitive_root(p)  # Tìm căn nguyên thủy

# Lớp DH
DiffieHellman(bit_length)
dh.generate_private_key()
dh.generate_public_key()
dh.compute_shared_secret(other_public_key)

# Lớp Alice/Bob
Alice(bit_length)
alice.step1_generate_keys()
alice.step2_receive_bob_key(B, params)
alice.step3_compute_shared_secret()

# Mã hóa
EncryptedMessenger(shared_secret)
messenger.encrypt(plaintext)
messenger.decrypt(encrypted_dict)

# Tấn công
Eve(bit_length)
eve.intercept_message(sender, receiver, msg)
eve.compute_shared_secret_with_alice(A)
```

---

## 🐛 TROUBLESHOOTING

### Lỗi: `ModuleNotFoundError: No module named 'cryptography'`

```bash
# Fix:
pip install cryptography
```

### Lỗi: Chạy quá chậm

```python
# Giảm bit_length:
alice = Alice(256)  # Thay vì 2048
```

### Lỗi: `K(Alice) ≠ K(Bob)`

```python
# Kiểm tra:
# 1. Có chia sẻ cùng p, g không?
# 2. Có trao đổi khóa công khai đúng không?
# 3. Có tính khóa bí mật đúng không?
```

### Lỗi: `Connect failed` (GUI / client)

```bash
# 1. Đảm bảo server đang chạy trên máy host:
python relay_server.py

# 2. Kiểm tra server_host trong config.json
# 3. Test localhost: server_host = "127.0.0.1"
```

### Lỗi: Tests failed trên Windows (UnicodeEncodeError)

```powershell
$env:PYTHONIOENCODING="utf-8"
python test_diffie_hellman.py
```

### Lỗi: Tests failed (khác)

```bash
# Chạy chi tiết:
python3 -m unittest test_diffie_hellman -v

# Debug:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📊 PERFORMANCE

### Thời Gian Chạy Típical

```
256-bit:  < 1 giây
512-bit:  1-2 giây
1024-bit: 5-10 giây
2048-bit: 30-60 giây
```

### Memory Usage

```
< 10 MB cho tất cả các bít length
```

---

## 💡 TIPS

1. **Nhanh nhất**: `python3 diffie_hellman.py` (dùng 512 bit)
2. **Hiệu quả nhất**: Lưu params, reuse `p, g`
3. **Bảo mật nhất**: Dùng 2048+ bit
4. **Học tập tốt nhất**: Đọc code, chạy debugger

---

## 📚 NEXT STEPS

### Tiếp Theo Sau Khi Hiểu DH:

```
DH (Diffie-Hellman)
    ↓
ECDH (Elliptic Curve DH) - Nhanh hơn
    ↓
TLS/SSL - Sử dụng ECDH
    ↓
PGP/GPG - End-to-end encryption
    ↓
Zero Knowledge Proofs - Advanced
```

---

## 🎓 TÓNG TẮT 5 PHÚT

**Diffie-Hellman là:**
- Giao thức trao đổi khóa công khai
- Cho phép 2 bên tạo khóa bí mật chung
- Không mã hóa dữ liệu, chỉ trao đổi khóa
- Dùng làm cơ sở cho TLS, SSH, IPSec

**Cách hoạt động:**
1. Thỏa thuận p, g (công khai)
2. Alice chọn a (bí mật), tính A = g^a mod p
3. Bob chọn b (bí mật), tính B = g^b mod p
4. Trao đổi A ↔ B
5. Alice tính K = B^a mod p
6. Bob tính K = A^b mod p
7. K(Alice) = K(Bob) ✅

**Bảo mật:**
- ✅ Khó tính logarit rời rạc (DLP)
- ⚠️ Dễ bị MITM attack
- ✅ Cần authentication để phòng chống

**Ứng dụng:**
- TLS/SSL (HTTPS)
- SSH
- IPSec
- Signal App
- WhatsApp
- Nhiều ứng dụng khác

---

**Chúc mừng! Bây giờ bạn đã có ứng dụng DH hoạt động! 🎉**

*(Cập nhật: 2026-06-04)*
