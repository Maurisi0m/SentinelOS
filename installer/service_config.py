"""Persist the HTTP port selected for the local SentinelOS backend."""

import json
import os
import tempfile

DEFAULT_HTTP_PORT = 8001
ALTERNATE_HTTP_PORT = 8002
ALLOWED_HTTP_PORTS = {DEFAULT_HTTP_PORT, ALTERNATE_HTTP_PORT}


def get_service_port(root_dir: str) -> int:
    config_path = os.path.join(root_dir, "config", "service.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            port = int(json.load(f).get("http_port", DEFAULT_HTTP_PORT))
        return port if port in ALLOWED_HTTP_PORTS else DEFAULT_HTTP_PORT
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return DEFAULT_HTTP_PORT


def set_service_port(root_dir: str, port: int) -> None:
    if port not in ALLOWED_HTTP_PORTS:
        raise ValueError(f"Unsupported SentinelOS HTTP port: {port}")

    config_dir = os.path.join(root_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "service.json")
    fd, temp_path = tempfile.mkstemp(prefix="service-", suffix=".json", dir=config_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"http_port": port}, f, indent=2)
        os.replace(temp_path, config_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
