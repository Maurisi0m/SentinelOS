#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINAL_Q4 = os.path.join(BASE_DIR, "export", "output_gguf", "sentinel-pure-stem-1b.Q4_K_M.gguf")
HP_HOST = "192.168.68.68"
HP_USER = "mauro"
HP_PASS = "Pollito92."
REMOTE_TEMP = f"/home/{HP_USER}/sentinel-pure-stem-1b.Q4_K_M.gguf"
REMOTE_TARGET = "/opt/sentinel/models/sentinel-pure-stem-1b.Q4_K_M.gguf"

def safe_upload():
    print("=" * 80)
    print("TRANSFERENCIA ROBUSTA DE MODELO GGUF A SERVIDOR HP")
    print(f"Archivo Local: {FINAL_Q4} ({os.path.getsize(FINAL_Q4)/(1024**2):.2f} MB)")
    print("=" * 80)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HP_HOST, port=22, username=HP_USER, password=HP_PASS, timeout=10)
    except Exception:
        client.connect("100.113.156.109", port=22, username=HP_USER, password=HP_PASS, timeout=10)

    # 1. Subir backend sentinel_service.py primero
    local_backend_svc = os.path.join(BASE_DIR, "labsentinel_backend", "sentinel_service.py")
    remote_backend_svc = f"/home/{HP_USER}/labsentinel-web/backend/sentinel_service.py"
    sftp = client.open_sftp()
    if os.path.exists(local_backend_svc):
        print(f"Sincronizando {local_backend_svc} -> {remote_backend_svc}...")
        sftp.put(local_backend_svc, remote_backend_svc)
        print("[OK] sentinel_service.py sincronizado.")

    # 2. Transferencia controlada para evitar WSAENOBUFS (Windows Socket Error 10055)
    total_size = os.path.getsize(FINAL_Q4)
    print(f"Subiendo binario GGUF por bloques controlados ({total_size / (1024**2):.2f} MB)...")
    t0 = time.time()
    
    with open(FINAL_Q4, "rb") as local_f:
        with sftp.open(REMOTE_TEMP, "wb") as remote_f:
            remote_f.set_pipelined(False)
            chunk_size = 512 * 1024  # 512 KB
            transferred = 0
            last_print = time.time()
            
            while True:
                chunk = local_f.read(chunk_size)
                if not chunk:
                    break
                remote_f.write(chunk)
                transferred += len(chunk)
                now = time.time()
                if now - last_print > 3.0:
                    pct = (transferred / total_size) * 100
                    speed = (transferred / (1024**2)) / max(now - t0, 0.1)
                    print(f"Progreso: {pct:.1f}% ({transferred / (1024**2):.1f}/{total_size / (1024**2):.1f} MB) a {speed:.2f} MB/s")
                    last_print = now

    sftp.close()
    elapsed = time.time() - t0
    print(f"\n[OK] Transferencia finalizada en {elapsed:.2f}s ({total_size / (1024**2) / elapsed:.2f} MB/s)")

    # 3. Mover al directorio de producción en /opt/sentinel/models, ajustar permisos y reiniciar servicios
    print("\n---> Moviendo a /opt/sentinel/models/ y reiniciando servicios...")
    cmd_deploy = (
        f"echo {HP_PASS} | sudo -S mv {REMOTE_TEMP} {REMOTE_TARGET} && "
        f"echo {HP_PASS} | sudo -S chown sentinel:sentinel {REMOTE_TARGET} && "
        f"echo {HP_PASS} | sudo -S chmod 644 {REMOTE_TARGET} && "
        f"echo {HP_PASS} | sudo -S systemctl restart sentinel.service labsentinel.service && "
        "sleep 2 && systemctl is-active sentinel.service labsentinel.service"
    )
    stdin, stdout, stderr = client.exec_command(f'bash -c "{cmd_deploy}"')
    out = stdout.read().decode('utf-8', errors='ignore')
    print("Estado de servicios:\n", out)
    client.close()
    print("\n[DESPLIEGUE FINALIZADO CON ÉXITO]")

if __name__ == "__main__":
    safe_upload()
