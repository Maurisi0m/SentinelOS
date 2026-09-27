#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Despliegue Automatizado desde la Laptop hacia labsentinel (192.168.68.68)
1. Crea el directorio remoto ~/sentinel_deploy/
2. Sube todos los scripts del orquestador y la interfaz web.
3. Sube el modelo maestro Titan calibrado con iMatrix (sentinel-master.Q4_K_M.gguf).
4. Ejecuta el script de compilación y arranque de servicios systemd en el servidor.
"""

import os
import sys
import time
import paramiko
from scp import SCPClient

HOST = "192.168.68.68"
USER = "mauro"
PASS = "Pollito92."
REMOTE_DIR = "/home/mauro/sentinel_deploy"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UBUNTU_DIR = os.path.join(BASE_DIR, "export", "ubuntu_server")
MODEL_PATH = os.path.join(BASE_DIR, "export", "output_gguf", "sentinel-master.Q4_K_M.gguf")

def progress_callback(filename, size, sent):
    pct = (sent / size) * 100 if size > 0 else 0
    mb_sent = sent / (1024 * 1024)
    mb_total = size / (1024 * 1024)
    sys.stdout.write(f"\r[TRANSFERENCIA] {os.path.basename(filename)}: {mb_sent:.1f}/{mb_total:.1f} MB ({pct:.1f}%)")
    sys.stdout.flush()

def main():
    print("=" * 80)
    print(f"INICIANDO DESPLIEGUE AUTOMATIZADO HACIA {USER}@{HOST}")
    print("=" * 80)

    # 1. Conexión SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=22, username=USER, password=PASS)
    print("[1/4] Conexión SSH establecida.")

    # 2. Crear directorio remoto
    client.exec_command(f"mkdir -p {REMOTE_DIR}")
    print(f"[2/4] Directorio remoto listo: {REMOTE_DIR}")

    # 3. Subir scripts de orquestador y web
    print("\n[3/4] Transfiriendo módulos del orquestador y servidor web...")
    with SCPClient(client.get_transport(), progress=progress_callback) as scp:
        # Subir todos los archivos de ubuntu_server
        for item in os.listdir(UBUNTU_DIR):
            local_item = os.path.join(UBUNTU_DIR, item)
            if os.path.isfile(local_item):
                scp.put(local_item, remote_path=REMOTE_DIR)
                print()

        # Subir el modelo binario GGUF Titan
        print(f"\nTransfiriendo modelo maestro Titan calibrado con iMatrix ({os.path.basename(MODEL_PATH)})...")
        scp.put(MODEL_PATH, remote_path=REMOTE_DIR)
        print()

    print("\n[4/4] Ejecutando script de compilación y despliegue en Ubuntu Server...")
    # Asegurar permisos de ejecución
    client.exec_command(f"chmod +x {REMOTE_DIR}/deploy_ubuntu_server.sh")

    # Ejecutar con sudo
    cmd = f"cd {REMOTE_DIR} && echo '{PASS}' | sudo -S ./deploy_ubuntu_server.sh"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

    # Stream logs en tiempo real
    for line in iter(stdout.readline, ""):
        print(line, end="")

    client.close()
    print("\n" + "=" * 80)
    print("¡DESPLIEGUE EN EL SERVIDOR FINALIZADO EXITOSAMENTE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
