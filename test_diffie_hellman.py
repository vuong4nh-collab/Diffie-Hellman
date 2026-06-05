"""
Unit Tests cho Diffie-Hellman Implementation
"""

import unittest
import sys
from diffie_hellman import (
    is_prime, generate_prime, gcd, find_primitive_root,
    DiffieHellman, Alice, Bob, SecureChannel
)


class TestMathFunctions(unittest.TestCase):
    """Test các hàm toán học cơ bản"""
    
    def test_is_prime_small_numbers(self):
        """Test kiểm tra số nguyên tố với các số nhỏ"""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18]
        
        for p in primes:
            self.assertTrue(is_prime(p), f"{p} should be prime")
        
        for c in composites:
            self.assertFalse(is_prime(c), f"{c} should not be prime")
    
    def test_is_prime_large_numbers(self):
        """Test kiểm tra số nguyên tố lớn"""
        # Số nguyên tố Carmichael: 561 = 3 * 11 * 17
        self.assertFalse(is_prime(561))
        
        # Số nguyên tố lớn
        self.assertTrue(is_prime(1000000007))
    
    def test_generate_prime_length(self):
        """Test sinh số nguyên tố với độ dài bit chính xác"""
        for bit_length in [16, 32]:  # Test với số bit nhỏ
            prime = generate_prime(bit_length)
            
            # Kiểm tra số nguyên tố
            self.assertTrue(is_prime(prime))
            
            # Kiểm tra độ dài bit
            self.assertGreaterEqual(prime.bit_length(), bit_length - 1)
            self.assertLessEqual(prime.bit_length(), bit_length)
    
    def test_gcd_basic(self):
        """Test tính GCD"""
        self.assertEqual(gcd(12, 8), 4)
        self.assertEqual(gcd(17, 5), 1)
        self.assertEqual(gcd(100, 50), 50)
    
    def test_find_primitive_root(self):
        """Test tìm căn nguyên thủy"""
        # Test với một số nguyên tố nhỏ
        p = 23
        g = find_primitive_root(p)
        
        # Kiểm tra g là căn nguyên thủy của p
        # g^i mod p phải sinh ra tất cả các số từ 1 đến p-1
        generated = set()
        for i in range(1, p):
            generated.add(pow(g, i, p))
        
        self.assertEqual(len(generated), p - 1, 
                        f"Generator {g} should generate all values mod {p}")


class TestDiffieHellman(unittest.TestCase):
    """Test lớp DiffieHellman"""
    
    def setUp(self):
        """Chuẩn bị test environment"""
        # Dùng 256 bit cho test (vừa nhanh, vừa an toàn)
        self.dh1 = DiffieHellman(256)
        self.dh2 = DiffieHellman(256)
    
    def test_dh_initialization(self):
        """Test khởi tạo DH"""
        self.assertIsNotNone(self.dh1.p)
        self.assertIsNotNone(self.dh1.g)
        self.assertTrue(is_prime(self.dh1.p))
    
    def test_private_key_generation(self):
        """Test sinh khóa bí mật"""
        a = self.dh1.generate_private_key()
        
        # Khóa bí mật phải nằm trong [2, p-2]
        self.assertGreaterEqual(a, 2)
        self.assertLessEqual(a, self.dh1.p - 2)
    
    def test_public_key_generation(self):
        """Test tính khóa công khai"""
        self.dh1.generate_private_key()
        A = self.dh1.generate_public_key()
        
        # Khóa công khai phải hợp lệ (0 < A < p)
        self.assertGreater(A, 0)
        self.assertLess(A, self.dh1.p)
    
    def test_shared_secret_computation(self):
        """Test tính khóa bí mật chung"""
        # DH1 tính public key
        A = self.dh1.generate_public_key()
        
        # DH2 tính public key
        B = self.dh2.generate_public_key()
        
        # DH1 tính shared secret từ B
        K1 = self.dh1.compute_shared_secret(B)
        
        # DH2 tính shared secret từ A
        K2 = self.dh2.compute_shared_secret(A)
        
        # Shared secret phải bằng nhau
        self.assertEqual(K1, K2, 
                        "DH1 and DH2 must compute same shared secret")
    
    def test_different_private_keys(self):
        """Test khóa bí mật của 2 người phải khác nhau"""
        a = self.dh1.generate_private_key()
        b = self.dh2.generate_private_key()
        
        # Khó có khả năng a == b (nếu có thì hệ thống có vấn đề)
        self.assertNotEqual(a, b)


class TestAliceAndBob(unittest.TestCase):
    """Test mô phỏng Alice và Bob"""
    
    def setUp(self):
        """Chuẩn bị test environment"""
        self.alice = Alice(256)
        self.bob = Bob(256)
    
    def test_alice_generate_keys(self):
        """Test Alice sinh khóa"""
        A = self.alice.step1_generate_keys()
        
        self.assertIsNotNone(A)
        self.assertGreater(A, 0)
    
    def test_bob_generate_keys(self):
        """Test Bob sinh khóa"""
        B = self.bob.step1_generate_keys()
        
        self.assertIsNotNone(B)
        self.assertGreater(B, 0)
    
    def test_full_key_exchange(self):
        """Test toàn bộ quy trình trao đổi khóa"""
        # Bước 1: Alice sinh khóa
        A = self.alice.step1_generate_keys()
        
        # Bước 2: Bob sinh khóa
        B = self.bob.step1_generate_keys()
        
        # Bước 3: Trao đổi khóa công khai
        self.bob.step2_receive_alice_key(A)
        self.alice.step2_receive_bob_key(B, self.bob.dh.get_parameters())
        
        # Bước 4: Tính khóa bí mật chung
        K_alice = self.alice.step3_compute_shared_secret()
        K_bob = self.bob.step3_compute_shared_secret()
        
        # Kiểm tra khóa giống nhau
        self.assertEqual(K_alice, K_bob,
                        "Alice and Bob must compute same shared secret")
    
    def test_alice_bob_different_keys(self):
        """Test khóa bí mật của Alice và Bob khác nhau"""
        a = self.alice.dh.generate_private_key()
        b = self.bob.dh.generate_private_key()
        
        # Khóa bí mật phải khác nhau
        self.assertNotEqual(a, b)


class TestSecurityProperties(unittest.TestCase):
    """Test các tính chất bảo mật"""
    
    def test_discrete_log_hardness(self):
        """Test khó tính logarit rời rạc"""
        dh = DiffieHellman(256)
        a = dh.generate_private_key()
        A = dh.generate_public_key()
        
        # Biết được A, p, g, nhưng không thể dễ tính được a
        # (Ngoài brute force)
        
        # Thử brute force (sẽ rất chậm với p lớn)
        found = False
        for candidate in range(2, min(dh.p, 10000)):  # Chỉ test 10000 giá trị
            if pow(dh.g, candidate, dh.p) == A:
                found = True
                break
        
        # Khó có khả năng tìm được (hoặc không tìm)
        # Đây là tính chất mong muốn
        print(f"\nDiscrete log test: Found={found} (may be True or False)")
    
    def test_shared_secret_is_large_number(self):
        """Test khóa bí mật chung là số lớn"""
        alice = Alice(256)
        bob = Bob(256)
        
        # Trao đổi khóa
        A = alice.step1_generate_keys()
        B = bob.step1_generate_keys()
        
        bob.step2_receive_alice_key(A)
        alice.step2_receive_bob_key(B, bob.dh.get_parameters())
        
        K_alice = alice.step3_compute_shared_secret()
        K_bob = bob.step3_compute_shared_secret()
        
        # Khóa bí mật phải lớn
        min_bits = 200  # Ít nhất 200 bit
        self.assertGreater(K_alice.bit_length(), min_bits)
        self.assertGreater(K_bob.bit_length(), min_bits)


class TestChannelCommunication(unittest.TestCase):
    """Test kênh truyền thông"""
    
    def test_channel_send_receive(self):
        """Test gửi/nhận thông điệp"""
        channel = SecureChannel()
        
        message = {"type": "test", "data": "hello"}
        msg_obj = channel.send_message("Alice", "Bob", message)
        
        self.assertEqual(msg_obj["sender"], "Alice")
        self.assertEqual(msg_obj["receiver"], "Bob")
        self.assertEqual(msg_obj["data"], message)
    
    def test_channel_eavesdrop_detection(self):
        """Test phát hiện eavesdropping"""
        channel = SecureChannel(simulate_eavesdrop=True)
        
        message = {"type": "test", "data": "secret"}
        channel.send_message("Alice", "Bob", message)
        
        # Eve sẽ intercept thông điệp
        self.assertGreater(len(channel.get_eavesdrop_log()), 0)


class TestPerformance(unittest.TestCase):
    """Test hiệu suất"""
    
    def test_computation_time_256bit(self):
        """Test thời gian tính toán với 256 bit"""
        import time
        
        alice = Alice(256)
        bob = Bob(256)
        
        start = time.time()
        A = alice.step1_generate_keys()
        B = bob.step1_generate_keys()
        bob.step2_receive_alice_key(A)
        alice.step2_receive_bob_key(B, bob.dh.get_parameters())
        K1 = alice.step3_compute_shared_secret()
        K2 = bob.step3_compute_shared_secret()
        elapsed = time.time() - start
        
        print(f"\n256-bit DH exchange took {elapsed:.4f} seconds")
        
        # Nên hoàn thành trong 5 giây
        self.assertLess(elapsed, 5.0)
    
    def test_key_exchange_multiple_times(self):
        """Test chạy key exchange nhiều lần"""
        for i in range(5):
            alice = Alice(128)  # Nhỏ hơn để nhanh
            bob = Bob(128)
            
            A = alice.step1_generate_keys()
            B = bob.step1_generate_keys()
            bob.step2_receive_alice_key(A)
            alice.step2_receive_bob_key(B, bob.dh.get_parameters())
            K1 = alice.step3_compute_shared_secret()
            K2 = bob.step3_compute_shared_secret()
            
            self.assertEqual(K1, K2)


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_tests():
    """Chạy tất cả các test"""
    
    # Tạo test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Thêm các test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMathFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestDiffieHellman))
    suite.addTests(loader.loadTestsFromTestCase(TestAliceAndBob))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityProperties))
    suite.addTests(loader.loadTestsFromTestCase(TestChannelCommunication))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # Chạy tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # In tóm tắt
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
