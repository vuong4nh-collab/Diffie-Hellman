"""
Diffie-Hellman Key Exchange Implementation
Trao đổi khóa bảo mật giữa hai người dùng
"""

import random
import secrets
import math
import json
import time
from typing import Tuple, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# PHẦN 1: CÁC HÀM TOÁN HỌC CƠ BẢN
# ============================================================================

def is_prime(n: int, k: int = 40) -> bool:
    """
    Kiểm tra số nguyên tố dùng thuật toán Miller-Rabin
    
    Args:
        n: Số cần kiểm tra
        k: Số lần lặp (độ chính xác)
    
    Returns:
        True nếu n là số nguyên tố, False nếu n là hợp số
    """
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    # Viết n-1 = 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    
    # Kiểm tra với k lần lặp
    for _ in range(k):
        a = 2 + secrets.randbelow(n - 3)
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
        
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    
    return True


def generate_prime(bit_length: int) -> int:
    """
    Sinh số nguyên tố ngẫu nhiên với độ dài bit cho sẵn
    
    Args:
        bit_length: Độ dài bit (ví dụ: 1024, 2048)
    
    Returns:
        Số nguyên tố được sinh
    """
    while True:
        num = secrets.randbits(bit_length)
        num |= (1 << (bit_length - 1)) | 1  # Đảm bảo bit đầu và cuối = 1
        
        if is_prime(num):
            return num


def gcd(a: int, b: int) -> int:
    """Tính ước chung lớn nhất"""
    while b:
        a, b = b, a % b
    return a


def find_primitive_root(p: int) -> int:
    """
    Tìm căn nguyên thủy (primitive root) mod p
    
    Căn nguyên thủy g là số thỏa: g^i mod p ≠ 1 với mọi i < p-1
    
    Args:
        p: Số nguyên tố
    
    Returns:
        Căn nguyên thủy mod p
    """
    # Tìm các ước nguyên tố của p-1
    phi = p - 1  # Euler's totient function cho số nguyên tố
    
    # Lấy các ước nguyên tố nhỏ
    prime_factors = []
    temp = phi
    
    for i in range(2, int(math.sqrt(phi)) + 1):
        if temp % i == 0:
            prime_factors.append(i)
            while temp % i == 0:
                temp //= i
    
    if temp > 1:
        prime_factors.append(temp)
    
    # Tìm primitive root
    for g in range(2, p):
        is_primitive = True
        for factor in prime_factors:
            if pow(g, phi // factor, p) == 1:
                is_primitive = False
                break
        
        if is_primitive:
            return g
    
    return 2  # Fallback


# ============================================================================
# PHẦN 2: LỚP DIFFIE-HELLMAN CHÍNH
# ============================================================================

@dataclass
class DH_Parameters:
    """Các tham số công khai của Diffie-Hellman"""
    p: int  # Số nguyên tố lớn
    g: int  # Căn nguyên thủy mod p


class DiffieHellman:
    """
    Triển khai đầy đủ thuật toán Diffie-Hellman Key Exchange
    """
    
    def __init__(
        self,
        bit_length: int = 2048,
        parameters: Optional[DH_Parameters] = None,
        verbose: bool = True
    ):
        """
        Khởi tạo tham số DH
        
        Args:
            bit_length: Độ dài bit của số nguyên tố (1024, 2048, 4096)
            parameters: Tham số p, g có sẵn nếu nhận từ bên còn lại
            verbose: In thông tin khởi tạo hay không
        """
        self.bit_length = bit_length

        if parameters is not None:
            self.p = parameters.p
            self.g = parameters.g
            self.bit_length = self.p.bit_length()
        else:
            if verbose:
                print(f"[*] Sinh số nguyên tố {bit_length} bit...")
            self.p = generate_prime(bit_length)

            if verbose:
                print(f"[*] Tìm căn nguyên thủy...")
            self.g = find_primitive_root(self.p)
        
        # Khóa bí mật
        self.private_key = None
        # Khóa công khai
        self.public_key = None
        # Khóa bí mật chung
        self.shared_secret = None
        
        if verbose:
            print(f"[✓] DH Parameters ready")
            print(f"    p (prime): {self.p}")
            print(f"    g (generator): {self.g}")
    
    def generate_private_key(self) -> int:
        """
        Sinh khóa bí mật ngẫu nhiên
        
        Khóa bí mật a phải nằm trong khoảng [2, p-2]
        """
        self.private_key = 2 + secrets.randbelow(self.p - 3)
        return self.private_key
    
    def generate_public_key(self) -> int:
        """
        Tính khóa công khai từ khóa bí mật
        
        Public Key A = g^a mod p
        """
        if self.private_key is None:
            self.generate_private_key()
        
        self.public_key = pow(self.g, self.private_key, self.p)
        return self.public_key
    
    def compute_shared_secret(self, other_public_key: int) -> int:
        """
        Tính khóa bí mật chung từ khóa công khai của bên kia
        
        Shared Secret K = B^a mod p
        
        Args:
            other_public_key: Khóa công khai của bên kia
        
        Returns:
            Khóa bí mật chung
        """
        if self.private_key is None:
            raise ValueError("Private key not generated!")
        
        self.shared_secret = pow(other_public_key, self.private_key, self.p)
        return self.shared_secret
    
    def get_parameters(self) -> DH_Parameters:
        """Trả về tham số công khai"""
        return DH_Parameters(p=self.p, g=self.g)
    
    def export_state(self) -> Dict:
        """Xuất trạng thái cho debugging"""
        return {
            "bit_length": self.bit_length,
            "p": self.p,
            "g": self.g,
            "private_key": self.private_key,
            "public_key": self.public_key,
            "shared_secret": self.shared_secret
        }


# ============================================================================
# PHẦN 3: MÔ PHỎNG HAI NGƯỜI DÙNG (ALICE & BOB)
# ============================================================================

class Alice:
    """Alice - người dùng 1"""
    
    def __init__(self, bit_length: int = 2048):
        self.name = "Alice"
        self.dh = DiffieHellman(bit_length)
        self.received_params = None
        self.received_public_key = None
        self.log = []
    
    def step1_generate_keys(self):
        """Bước 1: Alice sinh cặp khóa của mình"""
        self.dh.generate_private_key()
        public_key = self.dh.generate_public_key()
        
        self._log(f"Generated private key (secret): a = {self.dh.private_key}")
        self._log(f"Computed public key: A = g^a mod p = {public_key}")
        
        return public_key
    
    def step2_receive_bob_key(self, bob_public_key: int, params: DH_Parameters):
        """Bước 2: Alice nhận khóa công khai từ Bob"""
        self.received_public_key = bob_public_key
        self.received_params = params
        
        self._log(f"Received Bob's public key: B = {bob_public_key}")
        self._log(f"Received DH parameters: p = {params.p}, g = {params.g}")
    
    def step3_compute_shared_secret(self) -> int:
        """Bước 3: Alice tính khóa bí mật chung"""
        if self.received_public_key is None:
            raise ValueError("Haven't received Bob's public key!")
        
        # Sử dụng DH của Alice nhưng thay đổi p, g nếu nhận được từ Bob
        alice_dh = DiffieHellman.__new__(DiffieHellman)
        alice_dh.p = self.received_params.p
        alice_dh.g = self.received_params.g
        alice_dh.private_key = self.dh.private_key
        alice_dh.public_key = self.dh.public_key
        
        shared_secret = alice_dh.compute_shared_secret(self.received_public_key)
        self.dh.shared_secret = shared_secret
        
        self._log(f"Computed shared secret: K = B^a mod p = {shared_secret}")
        
        return shared_secret
    
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {self.name}: {message}"
        self.log.append(log_entry)
        print(log_entry)
    
    def print_log(self):
        print("\n" + "="*70)
        print(f"LOG {self.name}:")
        print("="*70)
        for entry in self.log:
            print(entry)


class Bob:
    """Bob - người dùng 2"""
    
    def __init__(self, bit_length: int = 2048):
        self.name = "Bob"
        self.dh = DiffieHellman(bit_length)
        self.received_public_key = None
        self.log = []
    
    def step1_generate_keys(self):
        """Bước 1: Bob sinh cặp khóa của mình"""
        self.dh.generate_private_key()
        public_key = self.dh.generate_public_key()
        
        self._log(f"Generated private key (secret): b = {self.dh.private_key}")
        self._log(f"Computed public key: B = g^b mod p = {public_key}")
        
        return public_key
    
    def step2_receive_alice_key(self, alice_public_key: int):
        """Bước 2: Bob nhận khóa công khai từ Alice"""
        self.received_public_key = alice_public_key
        
        self._log(f"Received Alice's public key: A = {alice_public_key}")
    
    def step3_compute_shared_secret(self) -> int:
        """Bước 3: Bob tính khóa bí mật chung"""
        if self.received_public_key is None:
            raise ValueError("Haven't received Alice's public key!")
        
        shared_secret = self.dh.compute_shared_secret(self.received_public_key)
        
        self._log(f"Computed shared secret: K = A^b mod p = {shared_secret}")
        
        return shared_secret
    
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {self.name}: {message}"
        self.log.append(log_entry)
        print(log_entry)
    
    def print_log(self):
        print("\n" + "="*70)
        print(f"LOG {self.name}:")
        print("="*70)
        for entry in self.log:
            print(entry)


# ============================================================================
# PHẦN 4: MÔ PHỎNG KÊNH TRUYỀN THÔNG
# ============================================================================

class SecureChannel:
    """Mô phỏng kênh truyền thông an toàn"""
    
    def __init__(self, simulate_eavesdrop: bool = False):
        self.messages = []
        self.simulate_eavesdrop = simulate_eavesdrop
        self.eavesdropper_log = []
    
    def send_message(self, sender: str, receiver: str, message: Dict) -> Dict:
        """
        Gửi thông điệp từ sender đến receiver
        
        Args:
            sender: Tên người gửi
            receiver: Tên người nhận
            message: Nội dung thông điệp (dict)
        """
        timestamp = datetime.now().isoformat()
        msg_obj = {
            "timestamp": timestamp,
            "sender": sender,
            "receiver": receiver,
            "data": message
        }
        
        self.messages.append(msg_obj)
        
        print(f"\n[→] {sender} → {receiver}")
        print(f"    Message: {json.dumps(message, indent=2)}")
        
        # Mô phỏng eavesdrop
        if self.simulate_eavesdrop:
            self.eavesdropper_log.append(msg_obj)
            print(f"    [!] Eve (eavesdropper) intercepted this message!")
        
        return msg_obj
    
    def get_messages(self):
        return self.messages
    
    def get_eavesdrop_log(self):
        return self.eavesdropper_log


# ============================================================================
# PHẦN 5: CHẠY TOÀN BỘ GIAO THỨC
# ============================================================================

def run_diffie_hellman_protocol(bit_length: int = 512, verbose: bool = True):
    """
    Chạy toàn bộ giao thức Diffie-Hellman
    
    Args:
        bit_length: Độ dài bit của số nguyên tố
        verbose: In chi tiết hay không
    """
    
    print("\n" + "="*70)
    print("DIFFIE-HELLMAN KEY EXCHANGE PROTOCOL")
    print("="*70 + "\n")
    
    # Tạo Alice và Bob
    print("[Step 0] Khởi tạo Alice và Bob\n")
    alice = Alice(bit_length)
    print("\n")
    bob = Bob(bit_length)
    
    channel = SecureChannel(simulate_eavesdrop=False)
    
    # Bước 1: Alice và Bob sinh cặp khóa
    print("\n" + "="*70)
    print("BƯỚC 1: Alice và Bob sinh cặp khóa")
    print("="*70)
    
    alice_public = alice.step1_generate_keys()
    print()
    bob_public = bob.step1_generate_keys()
    
    # Bước 2: Trao đổi khóa công khai qua kênh công khai
    print("\n" + "="*70)
    print("BƯỚC 2: Trao đổi khóa công khai")
    print("="*70)
    
    # Alice gửi khóa công khai cho Bob
    channel.send_message(
        "Alice", "Bob",
        {
            "type": "public_key",
            "A": alice_public,
            "params": {"p": alice.dh.p, "g": alice.dh.g}
        }
    )
    bob.step2_receive_alice_key(alice_public)
    
    # Bob gửi khóa công khai cho Alice
    channel.send_message(
        "Bob", "Alice",
        {
            "type": "public_key",
            "B": bob_public
        }
    )
    alice.step2_receive_bob_key(bob_public, bob.dh.get_parameters())
    
    # Bước 3: Tính khóa bí mật chung
    print("\n" + "="*70)
    print("BƯỚC 3: Tính khóa bí mật chung")
    print("="*70 + "\n")
    
    alice_secret = alice.step3_compute_shared_secret()
    print()
    bob_secret = bob.step3_compute_shared_secret()
    
    # Bước 4: Xác minh khóa bí mật giống nhau
    print("\n" + "="*70)
    print("BƯỚC 4: KIỂM TRA KẾT QUẢ")
    print("="*70)
    
    print(f"\nAlice's shared secret: K = {alice_secret}")
    print(f"Bob's shared secret:   K = {bob_secret}")
    print(f"\nAlice's K == Bob's K? {alice_secret == bob_secret}")
    
    if alice_secret == bob_secret:
        print("✓ [THÀNH CÔNG] Cả hai đã tính ra khóa bí mật chung giống nhau!")
    else:
        print("✗ [THẤT BẠI] Khóa bí mật không giống nhau!")
    
    # In log
    alice.print_log()
    bob.print_log()
    
    # Thống kê
    print("\n" + "="*70)
    print("THỐNG KÊ")
    print("="*70)
    print(f"Số bit của p: {bit_length}")
    print(f"Số bit của K: {alice_secret.bit_length()}")
    print(f"Số lần gửi thông điệp: {len(channel.get_messages())}")
    
    return {
        "alice": alice,
        "bob": bob,
        "channel": channel,
        "shared_secret": alice_secret
    }


# ============================================================================
# PHẦN 6: MAIN
# ============================================================================

if __name__ == "__main__":
    # Chạy với 512 bit cho demo (nhanh hơn)
    # Trong thực tế nên dùng 2048 hoặc 4096 bit
    result = run_diffie_hellman_protocol(bit_length=512)
    
    print("\n" + "="*70)
    print("Shared Secret (dùng để mã hóa tiếp):")
    print("="*70)
    print(result['shared_secret'])
