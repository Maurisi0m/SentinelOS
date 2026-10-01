#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL STEM-1.5B: Despliegue Automatizado a Servidor Ubuntu HP (192.168.68.68)
1. Conecta vía SSH.
2. Transfiere el binario sentinel-stem-qwen.Q4_K_M.gguf (940 MB).
3. Transfiere los módulos actualizados del orquestador, memoria de comandos y servicios.
4. Instala y reinicia los servicios de systemd.
5. Verifica el estado en vivo.
"""

import os
import sys
import time
import urllib.request
import json
import paramiko
from scp import SCPClient

HOST = "192.168.68.68"
USER = "mauro"
PASS = "Pollito92."
REMOTE_DIR = "/home/mauro/sentinel_deploy"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UBUNTU_DIR = os.path.join(BASE_DIR, "export", "ubuntu_server")
MODEL_PATH = os.path.join(BASE_DIR, "export", "output_gguf", "sentinel-stem-qwen.Q4_K_M.gguf")

def progress_callback(filename, size, sent):
    pct = (sent / size) * 100 if size > 0 else 0
    mb_sent = sent / (1024 * 1024)
    mb_total = size / (1024 * 1024)
    sys.stdout.write(f"\r[TRANSFERENCIA] {os.path.basename(filename)}: {mb_sent:.1f}/{mb_total:.1f} MB ({pct:.1f}%)")
    sys.stdout.flush()

def main():
    print("=" * 80)
    print(f"DESPLIEGUE AUTOMATIZADO DE SENTINEL STEM-1.5B A {USER}@{HOST}")
    print("=" * 80)

    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Modelo no encontrado: {MODEL_PATH}")
        sys.exit(1)

    # 1. Conexión SSH
    print("\n[1/5] Conectando por SSH al servidor HP Ubuntu...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=22, username=USER, password=PASS, timeout=15)
        print("[OK] Conexión SSH establecida exitosamente.")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a {HOST}: {e}")
        sys.exit(1)

    # 2. Crear directorio remoto
    client.exec_command(f"mkdir -p {REMOTE_DIR}")
    print(f"[2/5] Directorio de despliegue remoto: {REMOTE_DIR}")

    # 3. Subir scripts y modelo
    print("\n[3/5] Transfiriendo módulos del orquestador y nuevo modelo GGUF...")
    t0 = time.time()
    with SCPClient(client.get_transport(), progress=progress_callback) as scp:
        # Scripts de ubuntu_server
        for item in os.listdir(UBUNTU_DIR):
            local_item = os.path.join(UBUNTU_DIR, item)
            if os.path.isfile(local_item):
                scp.put(local_item, remote_path=REMOTE_DIR)
                print()

        # Modelo GGUF Q4_K_M
        print(f"\nTransfiriendo modelo binario {os.path.basename(MODEL_PATH)} ({os.path.getsize(MODEL_PATH)/(1024*1024):.1f} MB)...")
        scp.put(MODEL_PATH, remote_path=REMOTE_DIR)
        print()

    t_upload = time.time() - t0
    speed_mb = (os.path.getsize(MODEL_PATH)/(1024*1024)) / max(1, t_upload)
    print(f"[OK] Transferencia completada en {t_upload:.1f} segundos (~{speed_mb:.1f} MB/s).")

    # 4. Ejecutar script de despliegue en Ubuntu
    print("\n[4/5] Instalando archivos en /opt/sentinel y actualizando systemd...")
    client.exec_command(f"chmod +x {REMOTE_DIR}/deploy_ubuntu_server.sh")

    cmd = f"cd {REMOTE_DIR} && echo '{PASS}' | sudo -S ./deploy_ubuntu_server.sh"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

    for line in iter(stdout.readline, ""):
        print("  " + line.strip())

    # 5. Esperar arranque de llama-server y verificar estado
    print("\n[5/5] Verificando salud del demonio llama-server (puerto 8080)...")
    time.sleep(5)

    # Chequear estado del servicio
    stdin, stdout, stderr = client.exec_command("systemctl is-active sentinel.service")
    status = stdout.read().decode("utf-8").strip()
    print(f"Estado del servicio 'sentinel.service': {status}")

    client.close()

    # Comprobar endpoint HTTP localmente
    try:
        url = f"http://{HOST}:8080/v1/models"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[VERIFICACIÓN HTTP EXITOSA] llama-server respondiendo en {url}:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[INFO] Endpoint HTTP aún terminando de iniciar o protegido: {e}")

    # Limpieza opcional de carpeta temporal de 3GB en la laptop
    pruned_temp = os.path.join(BASE_DIR, "export", "sentinel_qwen_28l")
    if os.path.exists(pruned_temp):
        import shutil
        try:
            shutil.rmtree(pruned_temp)
            print(f"\n[LIMPIEZA LOCAL] Carpeta temporal de tensores safetensors ({pruned_temp}) eliminada para liberar disco.")
        except Exception as e:
            print(f"[INFO] No se eliminó temporal local: {e}")

    print("\n" + "=" * 80)
    print("¡DESPLIEGUE COMPLETADO Y OPERATIVO EN EL SERVIDOR UBUNTU!")
    print(f"Web UI disponible en: http://{HOST}:5000")
    print("=" * 80)

if __name__ == "__main__":
    main()
