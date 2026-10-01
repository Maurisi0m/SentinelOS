#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instala la llave pública SSH de la laptop en labsentinel para login sin contraseña.
"""

import os
import paramiko

HOST = "192.168.68.68"
USER = "mauro"
PASS = "Pollito92."

pubkey_path = os.path.expanduser("~/.ssh/id_ed25519.pub")
with open(pubkey_path, "r", encoding="utf-8") as f:
    pubkey = f.read().strip()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS)

commands = [
    "mkdir -p ~/.ssh && chmod 700 ~/.ssh",
    f"echo '{pubkey}' >> ~/.ssh/authorized_keys",
    "chmod 600 ~/.ssh/authorized_keys"
]

for cmd in commands:
    client.exec_command(cmd)

print("[OK] Llave pública instalada en ~/.ssh/authorized_keys de labsentinel.")
client.close()
