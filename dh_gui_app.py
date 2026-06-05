"""
Tkinter client for the Diffie-Hellman relay demo.

End users only need this app. The relay server runs separately on the host machine:
  python relay_server.py

Typical use:
  1. Host starts relay_server.py once on their machine.
  2. User A opens this app, chooses Alice, clicks Connect.
  3. User B opens this app, chooses Bob, clicks Connect.
  4. After both show the same fingerprint, send encrypted chat messages.
"""

import queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Optional

from app_config import get_server_host, get_server_port, load_config
from dh_client import (
    DEMO_PARAMETERS,
    decrypt_message,
    encrypt_message,
    key_fingerprint,
    read_json,
    send_json,
    validate_public_key,
)
from diffie_hellman import DH_Parameters, DiffieHellman


class DHClientSession:
    def __init__(self, ui_queue: "queue.Queue[tuple[str, str]]"):
        self.ui_queue = ui_queue
        self.role: Optional[str] = None
        self.sock: Optional[socket.socket] = None
        self.reader = None
        self.receiver_thread: Optional[threading.Thread] = None
        self.dh: Optional[DiffieHellman] = None
        self.params: Optional[DH_Parameters] = None
        self.alice_public_key: Optional[int] = None
        self.shared_secret: Optional[int] = None
        self.connected = False
        self.lock = threading.Lock()

    def connect(self, role: str, host: str, port: int, timeout: float, generate_params: bool, bit_length: int) -> None:
        if self.connected:
            self._log("Already connected")
            return

        self.role = role
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(None)
        self.reader = self.sock.makefile("r", encoding="utf-8", newline="\n")
        send_json(self.sock, {"type": "hello", "role": role})
        self.connected = True
        self._status(f"Connected as {role}")

        if role == "alice":
            self._start_as_alice(generate_params, bit_length)
        else:
            self._log("Waiting for Alice DH parameters and public key")

        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()

    def disconnect(self) -> None:
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.reader = None
        self.shared_secret = None
        self._status("Disconnected")

    def send_chat(self, text: str) -> None:
        with self.lock:
            shared_secret = self.shared_secret
            sock = self.sock

        if not sock or not shared_secret:
            raise RuntimeError("Shared secret is not ready")

        peer = "bob" if self.role == "alice" else "alice"
        ciphertext = encrypt_message(shared_secret, text)
        send_json(sock, {
            "type": "chat_message",
            "to": peer,
            "ciphertext": ciphertext,
        })
        self.ui_queue.put(("chat", f"You: {text}"))
        self._log("Sent encrypted chat message")

    def _start_as_alice(self, generate_params: bool, bit_length: int) -> None:
        if generate_params:
            self._log(f"Generating fresh {bit_length}-bit DH parameters")
            self.dh = DiffieHellman(bit_length=bit_length, verbose=False)
        else:
            self._log("Using built-in demo DH parameters")
            self.dh = DiffieHellman(parameters=DEMO_PARAMETERS, verbose=False)

        self.params = self.dh.get_parameters()
        public_key = self.dh.generate_public_key()

        send_json(self.sock, {
            "type": "dh_params",
            "to": "bob",
            "p": self.params.p,
            "g": self.params.g,
        })
        send_json(self.sock, {
            "type": "public_key",
            "to": "bob",
            "public_key": public_key,
        })
        self._log("Sent p,g and Alice public key A to Bob")

    def _receive_loop(self) -> None:
        try:
            while self.connected and self.reader:
                message = read_json(self.reader)
                self._handle_message(message)
        except Exception as exc:
            if self.connected:
                self._log(f"Connection closed: {exc}")
                self._status("Disconnected")
            self.connected = False

    def _handle_message(self, message: dict) -> None:
        message_type = message.get("type")

        if message_type == "server_info":
            self._log(f"Server registered this client as {message.get('role')}")
            return
        if message_type == "peer_joined":
            self._log(f"Peer joined: {message.get('role')}")
            return
        if message_type == "error":
            self._log(f"Server error: {message.get('message')}")
            return

        if self.role == "alice":
            self._handle_alice_message(message)
        elif self.role == "bob":
            self._handle_bob_message(message)

        if message_type == "chat_message":
            self._handle_chat_message(message)

    def _handle_alice_message(self, message: dict) -> None:
        if message.get("type") != "public_key" or message.get("from") != "bob":
            return

        if not self.dh or not self.params:
            self._log("Received Bob key before Alice DH was initialized")
            return

        bob_public_key = int(message["public_key"])
        validate_public_key(bob_public_key, self.params)
        shared_secret = self.dh.compute_shared_secret(bob_public_key)
        self._set_shared_secret(shared_secret)

    def _handle_bob_message(self, message: dict) -> None:
        if message.get("from") != "alice":
            return

        if message.get("type") == "dh_params":
            self.params = DH_Parameters(p=int(message["p"]), g=int(message["g"]))
            self._log("Received public DH parameters p,g from Alice")

        elif message.get("type") == "public_key":
            self.alice_public_key = int(message["public_key"])
            self._log("Received Alice public key A")

        if self.params and self.alice_public_key and not self.shared_secret:
            validate_public_key(self.alice_public_key, self.params)
            self.dh = DiffieHellman(parameters=self.params, verbose=False)
            bob_public_key = self.dh.generate_public_key()
            send_json(self.sock, {
                "type": "public_key",
                "to": "alice",
                "public_key": bob_public_key,
            })
            self._log("Sent Bob public key B to Alice")
            shared_secret = self.dh.compute_shared_secret(self.alice_public_key)
            self._set_shared_secret(shared_secret)

    def _handle_chat_message(self, message: dict) -> None:
        with self.lock:
            shared_secret = self.shared_secret

        if not shared_secret:
            self._log("Encrypted chat arrived before shared secret was ready")
            return

        try:
            plaintext = decrypt_message(shared_secret, message["ciphertext"])
        except Exception as exc:
            self._log(f"Failed to decrypt message: {exc}")
            return

        sender = message.get("from", "peer").title()
        self.ui_queue.put(("chat", f"{sender}: {plaintext}"))

    def _set_shared_secret(self, shared_secret: int) -> None:
        with self.lock:
            self.shared_secret = shared_secret
        fingerprint = key_fingerprint(shared_secret)
        self._log(f"Shared secret fingerprint: {fingerprint}")
        self.ui_queue.put(("fingerprint", fingerprint))
        self.ui_queue.put(("ready", "Shared secret ready"))

    def _log(self, message: str) -> None:
        self.ui_queue.put(("client", message))

    def _status(self, message: str) -> None:
        self.ui_queue.put(("status", message))


class DHGuiApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Diffie-Hellman Client")
        self.root.geometry("980x720")

        self.ui_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self.client_session = DHClientSession(self.ui_queue)
        self.config = load_config()
        self.server_host = get_server_host(self.config)
        self.server_port = get_server_port(self.config)
        self.timeout = float(self.config["timeout"])

        self.role_var = tk.StringVar(value="alice")
        self.status_var = tk.StringVar(value="Not connected")
        self.fingerprint_var = tk.StringVar(value="-")
        self.generate_params_var = tk.BooleanVar(value=False)
        self.bit_length_var = tk.StringVar(value=str(self.config["bit_length"]))
        self.message_var = tk.StringVar(value="")

        self._build_ui()
        self._poll_queue()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        top = ttk.Frame(self.root, padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Relay server:").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Label(
            top,
            text=f"{self.server_host}:{self.server_port}",
        ).grid(row=0, column=1, sticky="w")

        client_bar = ttk.LabelFrame(self.root, text="Connection", padding=12)
        client_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        client_bar.columnconfigure(9, weight=1)

        ttk.Label(client_bar, text="Role").grid(row=0, column=0, padx=(0, 6))
        ttk.Combobox(
            client_bar,
            textvariable=self.role_var,
            values=("alice", "bob"),
            width=8,
            state="readonly",
        ).grid(row=0, column=1, padx=(0, 12))

        ttk.Checkbutton(
            client_bar,
            text="Generate fresh params",
            variable=self.generate_params_var,
        ).grid(row=0, column=2, padx=(0, 8))
        ttk.Label(client_bar, text="Bits").grid(row=0, column=3, padx=(0, 6))
        ttk.Entry(client_bar, textvariable=self.bit_length_var, width=6).grid(row=0, column=4, padx=(0, 12))

        ttk.Button(client_bar, text="Connect", command=self._connect_client).grid(row=0, column=5, padx=(0, 8))
        ttk.Button(client_bar, text="Disconnect", command=self._disconnect_client).grid(row=0, column=6, padx=(0, 12))
        ttk.Label(client_bar, text="Status:").grid(row=0, column=7, padx=(0, 4))
        ttk.Label(client_bar, textvariable=self.status_var).grid(row=0, column=8, sticky="w", padx=(0, 12))
        ttk.Label(client_bar, text="Fingerprint:").grid(row=0, column=9, sticky="e", padx=(0, 4))
        ttk.Label(client_bar, textvariable=self.fingerprint_var).grid(row=0, column=10, sticky="w")

        body = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        body.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        log_frame = ttk.LabelFrame(body, text="Event Log", padding=8)
        chat_frame = ttk.LabelFrame(body, text="Encrypted Chat", padding=8)
        body.add(log_frame, weight=1)
        body.add(chat_frame, weight=1)

        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled", height=18)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        self.chat_text = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state="disabled", height=18)
        self.chat_text.grid(row=0, column=0, columnspan=2, sticky="nsew")
        ttk.Entry(chat_frame, textvariable=self.message_var).grid(row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 8))
        self.send_button = ttk.Button(chat_frame, text="Send Encrypted", command=self._send_chat, state="disabled")
        self.send_button.grid(row=1, column=1, pady=(8, 0))

    def _connect_client(self) -> None:
        try:
            role = self.role_var.get()
            bit_length = int(self.bit_length_var.get())
            generate_params = self.generate_params_var.get()
            self.client_session.connect(
                role,
                self.server_host,
                self.server_port,
                self.timeout,
                generate_params,
                bit_length,
            )
        except Exception as exc:
            messagebox.showerror(
                "Connect failed",
                f"Could not connect to {self.server_host}:{self.server_port}\n\n{exc}",
            )

    def _disconnect_client(self) -> None:
        self.client_session.disconnect()
        self.send_button.configure(state="disabled")
        self.fingerprint_var.set("-")

    def _send_chat(self) -> None:
        text = self.message_var.get().strip()
        if not text:
            return
        try:
            self.client_session.send_chat(text)
            self.message_var.set("")
        except Exception as exc:
            messagebox.showerror("Send failed", str(exc))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, message = self.ui_queue.get_nowait()
                if kind == "client":
                    self._append_log(message)
                elif kind == "status":
                    self.status_var.set(message)
                elif kind == "fingerprint":
                    self.fingerprint_var.set(message)
                elif kind == "ready":
                    self.status_var.set(message)
                    self.send_button.configure(state="normal")
                elif kind == "chat":
                    self._append_chat(message)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _append_log(self, message: str) -> None:
        self._append_text(self.log_text, message)

    def _append_chat(self, message: str) -> None:
        self._append_text(self.chat_text, message)

    @staticmethod
    def _append_text(widget: scrolledtext.ScrolledText, message: str) -> None:
        widget.configure(state="normal")
        widget.insert(tk.END, message + "\n")
        widget.see(tk.END)
        widget.configure(state="disabled")


def main() -> None:
    root = tk.Tk()
    DHGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
