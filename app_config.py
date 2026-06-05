"""
Shared configuration for the Diffie-Hellman relay demo.
"""

import json
from pathlib import Path
from typing import Any, Dict


CONFIG_PATH = Path(__file__).with_name("config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "server_host": "127.0.0.1",
    "server_port": 5001,
    "bind_host": "0.0.0.0",
    "timeout": 60.0,
    "bit_length": 256,
}


def load_config() -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)

    if not CONFIG_PATH.exists():
        return config

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return config

    if isinstance(data, dict):
        config.update(data)

    return config


def get_server_host(config: Dict[str, Any] | None = None) -> str:
    """Address clients connect to (your machine IP or domain)."""
    cfg = config or load_config()
    return str(cfg.get("server_host") or cfg.get("host") or DEFAULT_CONFIG["server_host"])


def get_server_port(config: Dict[str, Any] | None = None) -> int:
    cfg = config or load_config()
    return int(cfg.get("server_port") or cfg.get("port") or DEFAULT_CONFIG["server_port"])


def get_bind_host(config: Dict[str, Any] | None = None) -> str:
    """Address the relay server listens on (use 0.0.0.0 on your machine)."""
    cfg = config or load_config()
    return str(cfg.get("bind_host") or DEFAULT_CONFIG["bind_host"])
