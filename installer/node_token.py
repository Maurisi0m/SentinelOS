#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Gestor de Identidad y Tokens de Vinculación de Nodo
Genera y custodia las credenciales de enlace seguro entre Servidores y el Dashboard Maestro.
"""

import os
import json
import secrets
import socket
import platform
from datetime import datetime

def get_machine_name() -> str:
    try:
        return platform.node() or socket.gethostname() or "Sentinel-Node"
    except Exception:
        return "Sentinel-Node"

def get_or_create_node_auth(root_dir: str) -> dict:
    """Obtiene o genera de forma persistente el Token de autenticación del nodo."""
    cfg_dir = os.path.join(root_dir, "config")
    os.makedirs(cfg_dir, exist_ok=True)
    auth_file = os.path.join(cfg_dir, "node_auth.json")

    if os.path.exists(auth_file):
        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("token") and data.get("node_id"):
                    return data
        except Exception:
            pass

    # Generar nueva identidad de nodo y token seguro
    node_id = f"node-{secrets.token_hex(4)}"
    token = f"sntl_live_{secrets.token_hex(8)}"
    auth_data = {
        "node_id": node_id,
        "node_name": get_machine_name(),
        "token": token,
        "created_at": datetime.now().isoformat(),
        "port": 8001
    }

    try:
        with open(auth_file, "w", encoding="utf-8") as f:
            json.dump(auth_data, f, indent=2)
    except Exception as e:
        print(f"[!] Aviso al guardar node_auth.json: {e}")

    return auth_data
