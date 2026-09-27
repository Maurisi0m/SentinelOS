import paramiko
import os
import sys

# DNS permanente de Tailscale - funciona en cualquier red
HOST = "labsentinel.tailc83bd7.ts.net"
USER = "mauro"
PASS = "Pollito92."

print("Conectando SSH a HP...", flush=True)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

print("[1/3] Subiendo SentinelCockpit.jsx...", flush=True)
sftp.put("SentinelCockpit.jsx", "/home/mauro/labsentinel-web/frontend/src/components/SentinelCockpit.jsx")

print("[2/3] Subiendo index.css...", flush=True)
sftp.put("index.css", "/home/mauro/labsentinel-web/frontend/src/index.css")

sftp.close()

print("[3/3] Compilando frontend (Vite build)...", flush=True)
cmd = "export PATH=/home/mauro/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin:/usr/local/bin:$PATH && cd /home/mauro/labsentinel-web/frontend && npm run build"
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode()
err = stderr.read().decode()

print("Build Output:\n", out, flush=True)
if err and "error" in err.lower():
    print("Build Errors:\n", err, flush=True)

client.close()
print("[EXITO] Frontend desplegado y compilado!", flush=True)
