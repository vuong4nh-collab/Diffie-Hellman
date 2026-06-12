import os
import json
import logging
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from diffie_hellman import DiffieHellman, DH_Parameters
from advanced_examples import EncryptedMessenger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DH_Web_App")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = "dh_secret_key_123!"
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory session state
session_state = {
    "alice_connected": False,
    "bob_connected": False,
    "alice_sid": None,
    "bob_sid": None,
    "p": None,
    "g": None,
    "A": None,  # Alice's Public Key
    "B": None,  # Bob's Public Key
    "K": None,  # Shared secret (for display/intercept demo purposes only)
    "audit_log": [],
    "packets": [],
    "packet_counter": 400
}

def add_audit_log(event_type, message):
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "type": event_type,
        "message": message
    }
    session_state["audit_log"].append(log_entry)
    # Broadcast log entry to all clients
    socketio.emit("audit_log_entry", log_entry)
    logger.info(f"[{timestamp}] {event_type}: {message}")

def add_intercepted_packet(sender, receiver, data_type, payload, status):
    session_state["packet_counter"] += 1
    packet = {
        "id": session_state["packet_counter"],
        "sender": sender.upper(),
        "receiver": receiver.upper(),
        "type": data_type,
        "payload": payload,
        "status": status
    }
    session_state["packets"].append(packet)
    socketio.emit("packet_intercepted", packet)

def reset_session_state():
    session_state["p"] = None
    session_state["g"] = None
    session_state["A"] = None
    session_state["B"] = None
    session_state["K"] = None
    session_state["audit_log"] = []
    session_state["packets"] = []
    session_state["packet_counter"] = 400
    add_audit_log("SYSTEM", "Session reset by user.")
    socketio.emit("session_reset_triggered")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state")
def get_state():
    return jsonify({
        "alice_connected": session_state["alice_connected"],
        "bob_connected": session_state["bob_connected"],
        "p": session_state["p"],
        "g": session_state["g"],
        "A": session_state["A"],
        "B": session_state["B"],
        "audit_log": session_state["audit_log"],
        "packets": session_state["packets"]
    })

# WebSocket Event Handlers
@socketio.on("connect")
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on("join")
def handle_join(data):
    role = data.get("role", "observer")
    sid = request.sid

    if role == "alice":
        if session_state["alice_connected"] and session_state["alice_sid"] != sid:
            emit("error_msg", {"message": "Alice is already connected."})
            return
        session_state["alice_connected"] = True
        session_state["alice_sid"] = sid
        join_room("alice_room")
        add_audit_log("CONNECTION", "Alice connected to the secure channel.")
        socketio.emit("peer_status", {"role": "alice", "connected": True})
        
    elif role == "bob":
        if session_state["bob_connected"] and session_state["bob_sid"] != sid:
            emit("error_msg", {"message": "Bob is already connected."})
            return
        session_state["bob_connected"] = True
        session_state["bob_sid"] = sid
        join_room("bob_room")
        add_audit_log("CONNECTION", "Bob connected to the secure channel.")
        socketio.emit("peer_status", {"role": "bob", "connected": True})
        
    else:
        join_room("observers")
        logger.info(f"Observer joined: {sid}")

    # Send current state back to the newly joined client
    emit("init_state", {
        "role": role,
        "alice_connected": session_state["alice_connected"],
        "bob_connected": session_state["bob_connected"],
        "p": session_state["p"],
        "g": session_state["g"],
        "A": session_state["A"],
        "B": session_state["B"],
        "audit_log": session_state["audit_log"],
        "packets": session_state["packets"]
    })

@socketio.on("dh_params")
def handle_dh_params(data):
    p = data.get("p")
    g = data.get("g")
    session_state["p"] = p
    session_state["g"] = g
    
    add_audit_log("DH_PARAMS", f"Alice sent DH Parameters (p: {p[:16]}..., g: {g})")
    
    # Intercept packet for Eve
    payload_str = f"p = {p[:16]}... g = {g}"
    add_intercepted_packet("Alice", "Bob", "DH_PARAMS", payload_str, "Insecure Phase")
    
    # Relay parameters to Bob
    socketio.emit("dh_params_relay", {"p": p, "g": g}, room="bob_room")

@socketio.on("public_key")
def handle_public_key(data):
    role = data.get("role")
    pub_key = data.get("public_key")
    
    if role == "alice":
        session_state["A"] = pub_key
        add_audit_log("PUB_KEY", f"Alice sent Public Key A ({pub_key[:16]}...)")
        # Intercept packet for Eve
        add_intercepted_packet("Alice", "Bob", "PUB_KEY_A", f"A = {pub_key[:24]}...", "Insecure Phase")
        # Relay to Bob
        socketio.emit("public_key_relay", {"from": "alice", "public_key": pub_key}, room="bob_room")
    elif role == "bob":
        session_state["B"] = pub_key
        add_audit_log("PUB_KEY", f"Bob sent Public Key B ({pub_key[:16]}...)")
        # Intercept packet for Eve
        add_intercepted_packet("Bob", "Alice", "PUB_KEY_B", f"B = {pub_key[:24]}...", "Insecure Phase")
        # Relay to Alice
        socketio.emit("public_key_relay", {"from": "bob", "public_key": pub_key}, room="alice_room")

@socketio.on("chat_message")
def handle_chat_message(data):
    sender = data.get("sender")
    ciphertext = data.get("ciphertext")
    iv = data.get("iv")
    
    receiver = "bob" if sender == "alice" else "alice"
    recipient_room = "bob_room" if sender == "alice" else "alice_room"
    
    # Relay message
    socketio.emit("chat_message_relay", {
        "sender": sender,
        "ciphertext": ciphertext,
        "iv": iv
    }, room=recipient_room)
    
    add_audit_log("MESSAGE", f"Relayed encrypted message from {sender.title()} to {receiver.title()}")
    
    # Intercept packet for Eve
    payload_str = f"PAYLOAD: {ciphertext[:20]}... (IV: {iv[:8]}...)"
    add_intercepted_packet(sender, receiver, "CIPHERTEXT", payload_str, "Encrypted - Key Unknown")

@socketio.on("reset")
def handle_reset():
    reset_session_state()

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    if session_state["alice_sid"] == sid:
        session_state["alice_connected"] = False
        session_state["alice_sid"] = None
        add_audit_log("CONNECTION", "Alice disconnected.")
        socketio.emit("peer_status", {"role": "alice", "connected": False})
    elif session_state["bob_sid"] == sid:
        session_state["bob_connected"] = False
        session_state["bob_sid"] = None
        add_audit_log("CONNECTION", "Bob disconnected.")
        socketio.emit("peer_status", {"role": "bob", "connected": False})

if __name__ == "__main__":
    # Ensure templates and static folders exist
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    
    port = 5000
    logger.info(f"Starting Diffie-Hellman web app on http://localhost:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
