"""
TCP relay server for Diffie-Hellman clients.

The server is intentionally only a postman:
- it accepts Alice and Bob connections,
- forwards JSON messages between them,
- does not generate keys,
- does not compute or store the shared secret.
"""

import argparse
import json
import socket
import threading
from typing import Callable, Dict, List, Tuple

from app_config import get_bind_host, get_server_port, load_config


ClientRecord = Tuple[socket.socket, Tuple[str, int], threading.Lock]


class DHRelayServer:
    def __init__(self, host: str, port: int, logger: Callable[[str], None] = print):
        self.host = host
        self.port = port
        self.logger = logger
        self.clients: Dict[str, ClientRecord] = {}
        self.pending: Dict[str, List[dict]] = {"alice": [], "bob": []}
        self.lock = threading.Lock()

    def start(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()

            self._log(f"[server] Listening on {self.host}:{self.port}")
            self._log("[server] Waiting for Alice and Bob...")

            while True:
                conn, addr = server_socket.accept()
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True,
                )
                thread.start()

    def _handle_client(self, conn: socket.socket, addr: Tuple[str, int]) -> None:
        role = None
        try:
            reader = conn.makefile("r", encoding="utf-8", newline="\n")
            hello = self._read_json(reader)
            role = str(hello.get("role", "")).lower()

            if hello.get("type") != "hello" or role not in {"alice", "bob"}:
                self._send_json(conn, {"type": "error", "message": "Expected hello from alice or bob"})
                return

            if not self._register_client(role, conn, addr):
                self._send_json(conn, {"type": "error", "message": f"Role {role} is already connected"})
                return

            self._log(f"[server] {role} connected from {addr[0]}:{addr[1]}")
            self._send_json(conn, {"type": "server_info", "message": "registered", "role": role})
            self._flush_pending(role)
            self._notify_peer_joined(role)

            for line in reader:
                if not line.strip():
                    continue
                message = json.loads(line)
                self._relay(role, message)
        except (ConnectionError, OSError, json.JSONDecodeError) as exc:
            self._log(f"[server] Connection issue with {role or addr}: {exc}")
        finally:
            if role:
                self._unregister_client(role, conn)
            try:
                conn.close()
            except OSError:
                pass

    def _register_client(self, role: str, conn: socket.socket, addr: Tuple[str, int]) -> bool:
        with self.lock:
            if role in self.clients:
                return False
            self.clients[role] = (conn, addr, threading.Lock())
            return True

    def _unregister_client(self, role: str, conn: socket.socket) -> None:
        with self.lock:
            current = self.clients.get(role)
            if current and current[0] is conn:
                del self.clients[role]
                self._log(f"[server] {role} disconnected")

    def _relay(self, sender: str, message: dict) -> None:
        target = str(message.get("to") or self._peer_for(sender)).lower()
        if target not in {"alice", "bob"}:
            self._send_to(sender, {"type": "error", "message": f"Invalid target: {target}"})
            return

        forwarded = dict(message)
        forwarded["from"] = sender
        forwarded["to"] = target

        if self._send_to(target, forwarded):
            self._log(f"[server] relayed {forwarded.get('type')} from {sender} to {target}")
            return

        with self.lock:
            self.pending[target].append(forwarded)
        self._log(f"[server] queued {forwarded.get('type')} for {target}")

    def _flush_pending(self, role: str) -> None:
        with self.lock:
            messages = self.pending[role]
            self.pending[role] = []

        for message in messages:
            self._send_to(role, message)
            self._log(f"[server] delivered queued {message.get('type')} to {role}")

    def _notify_peer_joined(self, role: str) -> None:
        peer = self._peer_for(role)
        self._send_to(peer, {"type": "peer_joined", "role": role})

    def _send_to(self, role: str, message: dict) -> bool:
        with self.lock:
            record = self.clients.get(role)

        if not record:
            return False

        conn, _, send_lock = record
        try:
            with send_lock:
                self._send_json(conn, message)
            return True
        except OSError:
            return False

    @staticmethod
    def _peer_for(role: str) -> str:
        return "bob" if role == "alice" else "alice"

    def _log(self, message: str) -> None:
        self.logger(message)

    @staticmethod
    def _send_json(conn: socket.socket, message: dict) -> None:
        payload = json.dumps(message, separators=(",", ":")) + "\n"
        conn.sendall(payload.encode("utf-8"))

    @staticmethod
    def _read_json(reader) -> dict:
        line = reader.readline()
        if not line:
            raise ConnectionError("client disconnected before hello")
        return json.loads(line)


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser(description="Diffie-Hellman relay server")
    parser.add_argument("--host", default=get_bind_host(config), help="Host/IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=get_server_port(config), help="TCP port to listen on")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    DHRelayServer(args.host, args.port).start()
