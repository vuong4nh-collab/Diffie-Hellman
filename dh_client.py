"""
Diffie-Hellman network client for the relay-server model.

Run three terminals:
  1. python relay_server.py
  2. python dh_client.py alice
  3. python dh_client.py bob

The relay server only forwards public values. Alice and Bob compute the shared
secret locally and can then exchange encrypted messages through the same relay.
"""

import argparse
import base64
import hashlib
import json
import socket
from typing import Optional

from app_config import get_server_host, get_server_port, load_config
from diffie_hellman import DH_Parameters, DiffieHellman


DEMO_PARAMETERS = DH_Parameters(
    p=(1 << 127) - 1,  # Educational demo prime. Use --generate-params for custom p,g.
    g=3,
)


def send_json(sock: socket.socket, message: dict) -> None:
    payload = json.dumps(message, separators=(",", ":")) + "\n"
    sock.sendall(payload.encode("utf-8"))


def read_json(reader) -> dict:
    line = reader.readline()
    if not line:
        raise ConnectionError("server closed the connection")
    return json.loads(line)


def create_alice_dh(generate_params: bool, bit_length: int) -> DiffieHellman:
    if generate_params:
        print(f"[alice] Generating {bit_length}-bit DH parameters...")
        return DiffieHellman(bit_length=bit_length)

    print("[alice] Using built-in demo DH parameters")
    return DiffieHellman(parameters=DEMO_PARAMETERS, verbose=False)


def create_bob_dh(params: DH_Parameters) -> DiffieHellman:
    print("[bob] Using DH parameters received from Alice")
    return DiffieHellman(parameters=params, verbose=False)


def validate_public_key(public_key: int, params: DH_Parameters) -> None:
    if not (2 <= public_key <= params.p - 2):
        raise ValueError("Invalid peer public key")


def int_to_bytes(value: int) -> bytes:
    length = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(length, "big")


def key_fingerprint(shared_secret: int) -> str:
    digest = hashlib.sha256(int_to_bytes(shared_secret)).hexdigest()
    return digest[:24]


def make_fernet(shared_secret: int):
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise RuntimeError("Install cryptography first: pip install -r requirements.txt") from exc

    digest = hashlib.sha256(int_to_bytes(shared_secret)).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_message(shared_secret: int, plaintext: str) -> str:
    return make_fernet(shared_secret).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_message(shared_secret: int, token: str) -> str:
    plaintext = make_fernet(shared_secret).decrypt(token.encode("ascii"))
    return plaintext.decode("utf-8")


def handle_server_event(message: dict) -> bool:
    message_type = message.get("type")
    if message_type == "server_info":
        print(f"[server] {message.get('message')} as {message.get('role')}")
        return True
    if message_type == "peer_joined":
        print(f"[server] peer joined: {message.get('role')}")
        return True
    if message_type == "error":
        raise RuntimeError(message.get("message", "server error"))
    return False


def run_alice(sock: socket.socket, reader, args: argparse.Namespace) -> None:
    dh = create_alice_dh(args.generate_params, args.bit_length)
    params = dh.get_parameters()
    public_key = dh.generate_public_key()

    print("[alice] Sending public DH parameters p,g to Bob through the server")
    send_json(sock, {
        "type": "dh_params",
        "to": "bob",
        "p": params.p,
        "g": params.g,
    })

    print("[alice] Sending public key A = g^a mod p")
    send_json(sock, {
        "type": "public_key",
        "to": "bob",
        "public_key": public_key,
    })

    shared_secret: Optional[int] = None
    while shared_secret is None:
        message = read_json(reader)
        if handle_server_event(message):
            continue

        if message.get("type") == "public_key" and message.get("from") == "bob":
            bob_public_key = int(message["public_key"])
            validate_public_key(bob_public_key, params)
            shared_secret = dh.compute_shared_secret(bob_public_key)
            print(f"[alice] Shared secret fingerprint: {key_fingerprint(shared_secret)}")

    if args.message:
        ciphertext = encrypt_message(shared_secret, args.message)
        print("[alice] Sending encrypted message to Bob through the server")
        send_json(sock, {
            "type": "encrypted_message",
            "to": "bob",
            "ciphertext": ciphertext,
        })

        while True:
            message = read_json(reader)
            if handle_server_event(message):
                continue
            if message.get("type") == "encrypted_reply" and message.get("from") == "bob":
                plaintext = decrypt_message(shared_secret, message["ciphertext"])
                print(f"[alice] Encrypted reply from Bob: {plaintext}")
                return


def run_bob(sock: socket.socket, reader, args: argparse.Namespace) -> None:
    params: Optional[DH_Parameters] = None
    alice_public_key: Optional[int] = None
    dh: Optional[DiffieHellman] = None
    shared_secret: Optional[int] = None

    while shared_secret is None:
        message = read_json(reader)
        if handle_server_event(message):
            continue

        if message.get("type") == "dh_params" and message.get("from") == "alice":
            params = DH_Parameters(p=int(message["p"]), g=int(message["g"]))
            print("[bob] Received public DH parameters p,g")

        elif message.get("type") == "public_key" and message.get("from") == "alice":
            alice_public_key = int(message["public_key"])
            print("[bob] Received Alice public key A")

        if params is not None and alice_public_key is not None:
            validate_public_key(alice_public_key, params)
            dh = create_bob_dh(params)
            bob_public_key = dh.generate_public_key()
            send_json(sock, {
                "type": "public_key",
                "to": "alice",
                "public_key": bob_public_key,
            })
            print("[bob] Sent public key B = g^b mod p")
            shared_secret = dh.compute_shared_secret(alice_public_key)
            print(f"[bob] Shared secret fingerprint: {key_fingerprint(shared_secret)}")

    while True:
        message = read_json(reader)
        if handle_server_event(message):
            continue

        if message.get("type") == "encrypted_message" and message.get("from") == "alice":
            plaintext = decrypt_message(shared_secret, message["ciphertext"])
            print(f"[bob] Encrypted message from Alice: {plaintext}")

            reply = f"Bob received: {plaintext}"
            ciphertext = encrypt_message(shared_secret, reply)
            send_json(sock, {
                "type": "encrypted_reply",
                "to": "alice",
                "ciphertext": ciphertext,
            })
            print("[bob] Sent encrypted reply to Alice")
            return


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser(description="Diffie-Hellman client over relay server")
    parser.add_argument("role", choices=["alice", "bob"], help="Client role")
    parser.add_argument("--host", default=get_server_host(config), help="Relay server host")
    parser.add_argument("--port", type=int, default=get_server_port(config), help="Relay server port")
    parser.add_argument("--timeout", type=float, default=config["timeout"], help="Socket timeout in seconds")
    parser.add_argument("--message", default="Hello Bob, the shared secret works.", help="Alice message")
    parser.add_argument("--generate-params", action="store_true", help="Alice generates fresh p,g")
    parser.add_argument("--bit-length", type=int, default=config["bit_length"], help="Bit length with --generate-params")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
        sock.settimeout(args.timeout)
        reader = sock.makefile("r", encoding="utf-8", newline="\n")
        send_json(sock, {"type": "hello", "role": args.role})

        if args.role == "alice":
            run_alice(sock, reader, args)
        else:
            run_bob(sock, reader, args)


if __name__ == "__main__":
    main()
