"""
Ví dụ Nâng Cao: MITM Attack & Encryption
Mô phỏng tấn công Man-in-the-Middle và mã hóa thông điệp
"""

from diffie_hellman import DiffieHellman, Alice, Bob, SecureChannel
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib
import os
import json


# ============================================================================
# PHẦN 1: MÃ HÓA VỚI KHÓA BÍ MẬT CHUNG
# ============================================================================

class EncryptedMessenger:
    """
    Lớp để mã hóa/giải mã thông điệp sử dụng AES-256-CBC
    với khóa bí mật chung từ DH
    """
    
    def __init__(self, shared_secret: int):
        """
        Khởi tạo với khóa bí mật chung
        
        Args:
            shared_secret: Khóa bí mật chung từ DH
        """
        # Chuyển đổi khóa sang định dạng phù hợp
        secret_bytes = shared_secret.to_bytes(32, 'big')
        
        # Dùng SHA256 để derives key từ secret
        self.key = hashlib.sha256(secret_bytes).digest()
        
        print(f"[*] Cipher key derived from shared secret")
        print(f"    Key (hex): {self.key.hex()[:32]}...")
    
    def encrypt(self, plaintext: str) -> dict:
        """
        Mã hóa thông điệp
        
        Args:
            plaintext: Thông điệp gốc
        
        Returns:
            Dict chứa ciphertext và IV
        """
        # Sinh IV ngẫu nhiên
        iv = os.urandom(16)
        
        # Tạo cipher AES-256-CBC
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        
        # Padding để đủ 16 bytes block
        plaintext_bytes = plaintext.encode()
        padded = self._add_padding(plaintext_bytes)
        
        # Mã hóa
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        
        return {
            "ciphertext": ciphertext.hex(),
            "iv": iv.hex(),
            "plaintext_length": len(plaintext_bytes)
        }
    
    def decrypt(self, encrypted_data: dict) -> str:
        """
        Giải mã thông điệp
        
        Args:
            encrypted_data: Dict chứa ciphertext và IV
        
        Returns:
            Thông điệp gốc
        """
        # Lấy dữ liệu
        ciphertext = bytes.fromhex(encrypted_data["ciphertext"])
        iv = bytes.fromhex(encrypted_data["iv"])
        
        # Tạo cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        
        # Giải mã
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Loại bỏ padding
        plaintext = self._remove_padding(padded, encrypted_data["plaintext_length"])
        
        return plaintext.decode()
    
    @staticmethod
    def _add_padding(data: bytes) -> bytes:
        """Thêm PKCS7 padding"""
        pad_length = 16 - (len(data) % 16)
        padding = bytes([pad_length]) * pad_length
        return data + padding
    
    @staticmethod
    def _remove_padding(data: bytes, original_length: int) -> bytes:
        """Loại bỏ PKCS7 padding"""
        return data[:original_length]


# ============================================================================
# PHẦN 2: EVE - KẺ TẤN CÔNG MITM
# ============================================================================

class Eve:
    """
    Eve - người tấn công Man-in-the-Middle
    
    Eve có thể:
    - Intercept tất cả thông điệp
    - Tính khóa bí mật riêng với Alice và Bob
    - Giả dạng Alice đối với Bob và ngược lại
    """
    
    def __init__(self, bit_length: int = 256):
        self.name = "Eve"
        self.dh = DiffieHellman(bit_length)
        
        # Khóa của Eve
        self.private_key = self.dh.generate_private_key()
        self.public_key = self.dh.generate_public_key()
        
        # Khóa bí mật với Alice và Bob
        self.shared_secret_alice = None
        self.shared_secret_bob = None
        
        # Thông điệp bị intercept
        self.intercepted_messages = []
        
        print(f"[!] Eve initialized as Man-in-the-Middle attacker")
        print(f"    Private key (secret): e = {self.private_key}")
        print(f"    Public key: E = {self.public_key}")
    
    def intercept_message(self, sender: str, receiver: str, message: dict):
        """Intercept thông điệp"""
        self.intercepted_messages.append({
            "sender": sender,
            "receiver": receiver,
            "message": message
        })
        print(f"[!] Eve intercepted: {sender} → {receiver}")
    
    def compute_shared_secret_with_alice(self, alice_public_key: int):
        """
        Tính khóa bí mật chung với Alice
        (Eve giả dạng là Bob)
        """
        self.shared_secret_alice = pow(
            alice_public_key, self.private_key, self.dh.p
        )
        print(f"[!] Eve computed secret with Alice: K_eve_alice = {self.shared_secret_alice}")
    
    def compute_shared_secret_with_bob(self, bob_public_key: int):
        """
        Tính khóa bí mật chung với Bob
        (Eve giả dạng là Alice)
        """
        self.shared_secret_bob = pow(
            bob_public_key, self.private_key, self.dh.p
        )
        print(f"[!] Eve computed secret with Bob: K_eve_bob = {self.shared_secret_bob}")
    
    def decrypt_from_alice(self, encrypted_data: dict) -> str:
        """Giải mã thông điệp từ Alice"""
        if self.shared_secret_alice is None:
            return "[!] Don't have shared secret with Alice"
        
        try:
            messenger = EncryptedMessenger(self.shared_secret_alice)
            plaintext = messenger.decrypt(encrypted_data)
            return plaintext
        except:
            return "[!] Failed to decrypt"
    
    def decrypt_from_bob(self, encrypted_data: dict) -> str:
        """Giải mã thông điệp từ Bob"""
        if self.shared_secret_bob is None:
            return "[!] Don't have shared secret with Bob"
        
        try:
            messenger = EncryptedMessenger(self.shared_secret_bob)
            plaintext = messenger.decrypt(encrypted_data)
            return plaintext
        except:
            return "[!] Failed to decrypt"


# ============================================================================
# PHẦN 3: MITM ATTACK SIMULATION
# ============================================================================

def simulate_mitm_attack():
    """
    Mô phỏng tấn công Man-in-the-Middle
    
    Kịch bản:
    1. Alice muốn gửi thông điệp cho Bob
    2. Eve intercept tất cả giao tiếp
    3. Eve tính khóa bí mật với cả Alice và Bob
    4. Eve có thể đọc/sửa đổi tất cả thông điệp
    """
    
    print("\n" + "="*70)
    print("MITM ATTACK SIMULATION")
    print("="*70 + "\n")
    
    # Bước 1: Khởi tạo
    print("[Step 1] Khởi tạo Alice, Bob, và Eve\n")
    alice = Alice(256)
    print()
    bob = Bob(256)
    print()
    eve = Eve(256)
    
    # Bước 2: MITM - Eve chặn trao đổi khóa
    print("\n" + "="*70)
    print("[Step 2] Trao đổi khóa công khai (với MITM)")
    print("="*70 + "\n")
    
    print("[*] Alice sinh khóa và gửi cho Bob (nhưng bị Eve chặn)")
    A = alice.step1_generate_keys()
    eve.intercept_message("Alice", "Bob", {"type": "public_key", "A": A})
    eve.compute_shared_secret_with_alice(A)
    
    print("\n[*] Bob sinh khóa và gửi cho Alice (nhưng bị Eve chặn)")
    B = bob.step1_generate_keys()
    eve.intercept_message("Bob", "Alice", {"type": "public_key", "B": B})
    eve.compute_shared_secret_with_bob(B)
    
    print("\n[*] Eve gửi khóa công khai của mình cho cả Alice và Bob")
    print(f"    Eve → Alice: E = {eve.public_key}")
    print(f"    Eve → Bob:   E = {eve.public_key}")
    
    # Alice nhận khóa từ "Bob" (nhưng là của Eve)
    alice.step2_receive_bob_key(eve.public_key, eve.dh.get_parameters())
    # Bob nhận khóa từ "Alice" (nhưng là của Eve)
    bob.step2_receive_alice_key(eve.public_key)
    
    # Bước 3: Tính khóa bí mật
    print("\n" + "="*70)
    print("[Step 3] Tính khóa bí mật chung")
    print("="*70 + "\n")
    
    K_alice = alice.step3_compute_shared_secret()
    K_bob = bob.step3_compute_shared_secret()
    
    print(f"\n[!] Alice's shared secret: K_alice = {K_alice}")
    print(f"[!] Bob's shared secret:   K_bob = {K_bob}")
    print(f"\nAlice's K == Bob's K? {K_alice == K_bob}")
    
    if K_alice != K_bob:
        print("\n[!] NGUY HIỂM! Alice và Bob không tính ra khóa giống nhau!")
        print("[!] Họ sẽ không thể giao tiếp được")
    
    print(f"\n[!] Eve's shared secret with Alice: K_eve_alice = {eve.shared_secret_alice}")
    print(f"[!] Eve's shared secret with Bob:   K_eve_bob = {eve.shared_secret_bob}")
    
    # Bước 4: Gửi thông điệp mã hóa
    print("\n" + "="*70)
    print("[Step 4] Gửi thông điệp (bị MITM)")
    print("="*70 + "\n")
    
    message = "Hello Bob, this is Alice!"
    print(f"[*] Alice muốn gửi: \"{message}\"")
    
    # Alice mã hóa thông điệp
    print(f"\n[*] Alice mã hóa với khóa: K_alice = {K_alice}")
    messenger_alice = EncryptedMessenger(K_alice)
    encrypted_msg = messenger_alice.encrypt(message)
    print(f"    Ciphertext: {encrypted_msg['ciphertext'][:32]}...")
    
    # Eve intercept thông điệp
    print(f"\n[!] Eve intercept thông điệp mã hóa")
    eve.intercept_message("Alice", "Bob", encrypted_msg)
    
    # Eve giải mã thông điệp
    print(f"\n[!] Eve giải mã với khóa: K_eve_alice = {eve.shared_secret_alice}")
    decrypted_by_eve = eve.decrypt_from_alice(encrypted_msg)
    print(f"    Decrypted message: \"{decrypted_by_eve}\"")
    print(f"\n[!] EVE ĐÃ ĐỌC THÔNG ĐIỆP CỦA ALICE!")
    
    # Eve có thể sửa đổi thông điệp
    print(f"\n[!] Eve sửa đổi thông điệp thành: \"HACKED BY EVE!\"")
    modified_msg = "HACKED BY EVE!"
    modified_encrypted = messenger_alice.encrypt(modified_msg)
    
    # Gửi thông điệp đã sửa đổi cho Bob
    print(f"[!] Eve gửi thông điệp đã sửa đổi tới Bob")
    
    # Bob cố giải mã
    print(f"\n[*] Bob nhận thông điệp và cố giải mã với khóa: K_bob = {K_bob}")
    try:
        # Bob sẽ thất bại vì khóa không khớp
        messenger_bob = EncryptedMessenger(K_bob)
        decrypted_by_bob = messenger_bob.decrypt(modified_encrypted)
        print(f"    Decrypted message: \"{decrypted_by_bob}\"")
    except Exception as e:
        print(f"    [!] Giải mã thất bại: {str(e)[:50]}...")
    
    return {
        "alice": alice,
        "bob": bob,
        "eve": eve,
        "success": True
    }


# ============================================================================
# PHẦN 4: PHÒNG CHỐNG MITM
# ============================================================================

def demonstrate_mitm_defense():
    """
    Giới thiệu cách phòng chống tấn công MITM
    
    Giải pháp:
    1. Digital Signature (chữ ký số)
    2. Certificate Authority (CA)
    3. Mutual Authentication (xác thực lẫn nhau)
    """
    
    print("\n" + "="*70)
    print("PHÒNG CHỐNG MITM ATTACK")
    print("="*70 + "\n")
    
    print("""
[Giải pháp 1] Digital Signature
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Alice ký lên khóa công khai của mình: Sign_Alice(A)
- Bob ký lên khóa công khai của mình: Sign_Bob(B)
- Eve không thể giả dạ vì không có khóa bí mật để ký
- Alice kiểm tra chữ ký: Verify_Bob(B) = chính xác?
- Nếu kiểm tra thất bại → phát hiện MITM

[Giải pháp 2] Certificate Authority (CA)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- CA là bên thứ 3 đáng tin cậy
- CA cấp chứng chỉ kỹ thuật số cho Alice và Bob
- Chứng chỉ chứa khóa công khai đã ký
- Eve không thể giả dạ mà không có chứng chỉ từ CA
- Alice & Bob kiểm tra chứng chỉ

[Giải pháp 3] Mutual Authentication (SRP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Sử dụng password hoặc pre-shared key (PSK)
- Alice và Bob xác minh nhau trước trao đổi khóa
- Eve không biết PSK → không thể xác minh
- Ví dụ: Secure Remote Password (SRP) protocol

[Giải pháp 4] Perfect Forward Secrecy (PFS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Mỗi session dùng khóa bí mật khác nhau
- Ngay cả khi long-term key bị compromise
  → các session cũ vẫn an toàn
- Sử dụng ephemeral DH (ECDHE)
- TLS 1.3 sử dụng cơ chế này mặc định
    """)


# ============================================================================
# PHẦN 5: DEMO MÌNH HÓA VỚI KHÓA CHUNG
# ============================================================================

def demo_secure_communication():
    """
    Demo mã hóa thông điệp an toàn giữa Alice và Bob
    (không có MITM)
    """
    
    print("\n" + "="*70)
    print("SECURE COMMUNICATION WITH SHARED SECRET")
    print("="*70 + "\n")
    
    # Thiết lập
    print("[Step 1] Thiết lập kênh an toàn\n")
    alice = Alice(256)
    print()
    bob = Bob(256)
    
    # Trao đổi khóa
    print("\n[Step 2] Trao đổi khóa DH\n")
    A = alice.step1_generate_keys()
    B = bob.step1_generate_keys()
    
    bob.step2_receive_alice_key(A)
    alice.step2_receive_bob_key(B, bob.dh.get_parameters())
    
    K_alice = alice.step3_compute_shared_secret()
    K_bob = bob.step3_compute_shared_secret()
    
    print(f"\n[✓] Shared secret established: K = {K_alice}")
    
    # Mã hóa thông điệp
    print("\n" + "="*70)
    print("[Step 3] Gửi thông điệp mã hóa")
    print("="*70 + "\n")
    
    messages = [
        "Hello Bob! How are you?",
        "Let's have a secret meeting at the library.",
        "The password is: SuperSecret123!"
    ]
    
    messenger_alice = EncryptedMessenger(K_alice)
    messenger_bob = EncryptedMessenger(K_bob)
    
    for msg in messages:
        print(f"[Alice] Message: \"{msg}\"")
        
        # Alice mã hóa
        encrypted = messenger_alice.encrypt(msg)
        print(f"        Encrypted: {encrypted['ciphertext'][:40]}...")
        
        # Bob giải mã
        decrypted = messenger_bob.decrypt(encrypted)
        print(f"[Bob]   Decrypted: \"{decrypted}\"")
        
        if decrypted == msg:
            print("[✓] Message integrity verified!")
        print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Demo 1: MITM Attack
    simulate_mitm_attack()
    
    # Demo 2: Phòng chống MITM
    demonstrate_mitm_defense()
    
    # Demo 3: Giao tiếp an toàn
    demo_secure_communication()
