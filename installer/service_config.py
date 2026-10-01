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


def _read_service_config(root_dir: str) -> dict:
    config_path = os.path.join(root_dir, "config", "service.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config if isinstance(config, dict) else {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}


def _write_service_config(root_dir: str, config: dict) -> None:
    config_dir = os.path.join(root_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "service.json")
    fd, temp_path = tempfile.mkstemp(prefix="service-", suffix=".json", dir=config_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        os.replace(temp_path, config_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def get_node_role(root_dir: str) -> str:
    role = str(_read_service_config(root_dir).get("node_role", "server_headless"))
    allowed = {"master", "mesh", "server_headless", "server_hybrid", "server_standalone"}
    return role if role in allowed else "server_headless"


def set_node_role(root_dir: str, role: str) -> None:
    allowed = {"master", "mesh", "server_headless", "server_hybrid", "server_standalone"}
    if role not in allowed:
        raise ValueError(f"Unsupported SentinelOS node role: {role}")
    config = _read_service_config(root_dir)
    config["node_role"] = role
    _write_service_config(root_dir, config)


def set_service_port(root_dir: str, port: int) -> None:
    if port not in ALLOWED_HTTP_PORTS:
        raise ValueError(f"Unsupported SentinelOS HTTP port: {port}")

    config = _read_service_config(root_dir)
    config["http_port"] = port
    _write_service_config(root_dir, config)
