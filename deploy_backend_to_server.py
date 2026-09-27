import paramiko
import os
import sys

HOST = "192.168.68.68"
USER = "mauro"
PASS = "Pollito92."

print("Conectando SSH a HP...", flush=True)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

print("[1/3] Subiendo sentinel_service.py...", flush=True)
sftp.put("labsentinel_backend/sentinel_service.py", "/home/mauro/labsentinel-web/backend/sentinel_service.py")

print("[2/3] Subiendo main.py...", flush=True)
sftp.put("labsentinel_backend/main.py", "/home/mauro/labsentinel-web/backend/main.py")

sftp.close()

print("[3/3] Reiniciando labsentinel.service...", flush=True)
stdin, stdout, stderr = client.exec_command("sudo -S systemctl restart labsentinel.service")
stdin.write(PASS + "\n")
stdin.flush()
err = stderr.read().decode()
out = stdout.read().decode()

stdin, stdout, stderr = client.exec_command("systemctl is-active labsentinel.service")
status = stdout.read().decode().strip()
print(f"Estado del servicio: {status}", flush=True)

client.close()
print("[EXITO] Backend actualizado y verificado!", flush=True)
