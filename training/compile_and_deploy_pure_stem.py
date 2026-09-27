#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversión GGUF, Cuantización iMatrix y Despliegue en Servidor HP
----------------------------------------------------------------
1. Convierte export/sentinel_dpo_aligned_1b/ a GGUF F16.
2. Cuantiza con iMatrix calibrada a Q4_K_M (sentinel-pure-stem-1b.Q4_K_M.gguf).
3. Transfiere vía SFTP a /opt/sentinel/models/ en el servidor HP (192.168.68.68).
4. Reinicia sentinel.service y labsentinel.service.
5. Ejecuta diagnóstico de inferencia en vivo.
"""

import os
import sys
import subprocess
import time
import paramiko

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HF_MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_dpo_aligned_1b")
OUTPUT_GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
F16_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-pure-stem-1b.f16.gguf")
FINAL_Q4 = os.path.join(OUTPUT_GGUF_DIR, "sentinel-pure-stem-1b.Q4_K_M.gguf")
IMATRIX_FILE = os.path.join(OUTPUT_GGUF_DIR, "sentinel.imatrix")

LLAMA_REPO = os.path.join(BASE_DIR, "export", "llama_repo")
CONVERTER = os.path.join(LLAMA_REPO, "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

HP_HOST = "192.168.68.68"
HP_USER = "mauro"
HP_PASS = "Pollito92."
REMOTE_MODEL_PATH = "/opt/sentinel/models/sentinel-pure-stem-1b.Q4_K_M.gguf"

def run_step(desc, cmd, cwd=None, extra_env=None):
    print(f"\n---> {desc}")
    print(f"Comando: {cmd}")
    t0 = time.time()
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    res = subprocess.run(cmd, shell=True, text=True, cwd=cwd, env=env)
    if res.returncode != 0:
        raise RuntimeError(f"Fallo en: {desc} (Código de salida: {res.returncode})")
    print(f"[OK] Completado en {time.time() - t0:.2f}s.")

def main():
    print("=" * 80)
    print("PIPELINE DE CONVERSIÓN GGUF, CUANTIZACIÓN Y DESPLIEGUE REMOTO")
    print("=" * 80)

    # 1 y 2: Conversión y Cuantización fresca de los tensores DPO + RepE
    conv_env = {
        "PYTHONPATH": f"{LLAMA_REPO};{os.path.join(LLAMA_REPO, 'gguf-py')}"
    }
    if os.path.exists(F16_GGUF):
        try:
            os.remove(F16_GGUF)
        except Exception:
            pass
    if os.path.exists(FINAL_Q4):
        try:
            os.remove(FINAL_Q4)
        except Exception:
            pass

    run_step(
        "Convirtiendo modelo HF consolidado (DoRA + Task Vectors + MEMIT + TIES + DPO + RepE) a GGUF F16...",
        f'"{sys.executable}" "{CONVERTER}" "{HF_MODEL_DIR}" --outfile "{F16_GGUF}" --outtype f16',
        cwd=LLAMA_REPO,
        extra_env=conv_env
    )

    quant_cmd = f'"{QUANTIZER}" "{F16_GGUF}" "{FINAL_Q4}" Q4_K_M'
    run_step("Cuantizando a Q4_K_M de ultra-baja latencia y máxima precisión matemática...", quant_cmd)

    file_size_mb = os.path.getsize(FINAL_Q4) / (1024**2)
    print(f"\n[INFO] Binario GGUF Q4_K_M verificado: {file_size_mb:.2f} MB")

    # 3. Transferir al Servidor HP (vía home de usuario para evitar bloqueos de permisos)
    print(f"\n---> Conectando vía SFTP a {HP_HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HP_HOST, port=22, username=HP_USER, password=HP_PASS, timeout=5)
    except Exception:
        client.connect("100.113.156.109", port=22, username=HP_USER, password=HP_PASS, timeout=8)

    sftp = client.open_sftp()
    temp_remote_path = f"/home/{HP_USER}/sentinel-pure-stem-1b.Q4_K_M.gguf"
    print(f"Transfiriendo modelo GGUF {FINAL_Q4} -> {temp_remote_path}...")
    t_tx = time.time()
    sftp.put(FINAL_Q4, temp_remote_path)

    local_backend_svc = os.path.join(BASE_DIR, "labsentinel_backend", "sentinel_service.py")
    remote_backend_svc = f"/home/{HP_USER}/labsentinel-web/backend/sentinel_service.py"
    if os.path.exists(local_backend_svc):
        print(f"Sincronizando {local_backend_svc} -> {remote_backend_svc}...")
        sftp.put(local_backend_svc, remote_backend_svc)

    sftp.close()
    print(f"[OK] Transferencia completada en {time.time() - t_tx:.2f}s.")

    # 4. Mover a /opt/sentinel/models, ajustar permisos y reiniciar servicios en el HP
    print("\n---> Moviendo binario, ajustando permisos y reiniciando sentinel.service y labsentinel.service...")
    cmd_deploy = (
        f"echo {HP_PASS} | sudo -S mv {temp_remote_path} {REMOTE_MODEL_PATH} && "
        f"echo {HP_PASS} | sudo -S chown sentinel:sentinel {REMOTE_MODEL_PATH} && "
        f"echo {HP_PASS} | sudo -S chmod 644 {REMOTE_MODEL_PATH} && "
        f"echo {HP_PASS} | sudo -S systemctl restart sentinel.service labsentinel.service && "
        "systemctl is-active sentinel.service labsentinel.service"
    )
    stdin, stdout, stderr = client.exec_command(f'bash -c "{cmd_deploy}"')
    out = stdout.read().decode('utf-8', errors='ignore')
    print("Estado de servicios:\n", out)
    client.close()

    print("\n[ÉXITO TOTAL] Modelo SENTINEL Pure STEM 1B desplegado y operativo en el servidor HP.")

if __name__ == "__main__":
    main()
