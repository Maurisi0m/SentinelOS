#!/usr/bin/env python3
"""Upload remote_bench.py via SFTP then execute it on server"""
import paramiko, sys

HOST = "100.113.156.109"
USER = "mauro"
PASS = "Pollito92."

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS)

# Upload
sftp = client.open_sftp()
sftp.put("benchmark/remote_bench.py", "/tmp/remote_bench.py")
sftp.close()
print("[SFTP] Subido /tmp/remote_bench.py")

# Execute - with a long timeout since 3.2B is slow
print("[RUN] Ejecutando benchmark 3.2B... (puede tardar ~3-5 min)")
_, stdout, stderr = client.exec_command("python3 /tmp/remote_bench.py", timeout=600)

tps_list = []
print("="*68)
print("BENCHMARK 3.2B Q4_K_M (i5-4310U) - Acceso local 127.0.0.1:8080")
print("="*68)

QUESTIONS = [
    "Explica que es un controlador PID...",
    "Como funciona el protocolo I2C...",
    "Que es O(n log n)...",
    "Proceso vs Hilo en Linux...",
    "Q-Learning en RL...",
]

idx = 0
for line in stdout:
    line = line.strip()
    if line.startswith("RESULT|"):
        parts = line.split("|", 6)
        i_q, elapsed, tok, tps, finish = parts[1], parts[2], parts[3], parts[4], parts[5]
        preview = parts[6] if len(parts) > 6 else ""
        q_label = QUESTIONS[int(i_q)-1] if int(i_q) <= len(QUESTIONS) else f"Q{i_q}"
        print(f"\n[{i_q}/5] {q_label}")
        print(f"  {elapsed}s | {tok} tok | {tps} t/s | [{finish}]")
        print(f"  >> {preview[:120]}")
        tps_list.append(float(tps))
    elif line.startswith("AVG|"):
        parts = line.split("|")
        avg32 = float(parts[1])
        factor = round(37.02 / avg32, 2) if avg32 > 0 else "?"
        print(f"\n{'='*68}")
        print(f"RESUMEN FINAL")
        print(f"  3.2B Q4_K_M (i5-4310U CPU) : {avg32} t/s promedio")
        print(f"  1B  Q4_K_M  (RTX 5060 GPU) : 37.02 t/s promedio")
        print(f"  Factor 1B/3.2B             : {factor}x mas rapido en GPU")
        print(f"{'='*68}")
    elif line.startswith("ERR|"):
        print(f"  ERROR: {line}")

err_out = stderr.read().decode("utf-8", errors="replace")
if err_out.strip():
    print(f"\n[STDERR]: {err_out[:300]}")

client.close()
