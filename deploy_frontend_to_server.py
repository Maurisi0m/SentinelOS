import paramiko
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = "labsentinel.tailc83bd7.ts.net"
USER = "mauro"
PASS = "Pollito92."

print("Conectando SSH a HP...", flush=True)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS, timeout=15)
sftp = client.open_sftp()

print("[1/3] Subiendo archivos del frontend...", flush=True)
print("  - Subiendo App.jsx...", flush=True)
sftp.put("App.jsx", "/home/mauro/labsentinel-web/frontend/src/App.jsx")

print("  - Subiendo NetworkTopologyView.jsx...", flush=True)
sftp.put("NetworkTopologyView.jsx", "/home/mauro/labsentinel-web/frontend/src/components/NetworkTopologyView.jsx")

print("  - Subiendo index.css...", flush=True)
sftp.put("index.css", "/home/mauro/labsentinel-web/frontend/src/index.css")

print("[2/3] Compilando frontend (Vite build)...", flush=True)
cmd = "export PATH=/home/mauro/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin:/usr/local/bin:$PATH && cd /home/mauro/labsentinel-web/frontend && npm run build"
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode()
err = stderr.read().decode()

print("Build Output:\n", out, flush=True)
if err and "error" in err.lower():
    print("Build Errors:\n", err, flush=True)
    sys.exit(1)

print("[3/3] Descargando artefactos compilados (dist) a local labsentinel_backend/dist...", flush=True)
local_dist = os.path.join(os.path.dirname(__file__), "labsentinel_backend", "dist")
os.makedirs(local_dist, exist_ok=True)
remote_dist = "/home/mauro/labsentinel-web/frontend/dist"

def download_dir(remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    for item in sftp.listdir_attr(remote_dir):
        rpath = f"{remote_dir}/{item.filename}"
        lpath = os.path.join(local_dir, item.filename)
        import stat
        if stat.S_ISDIR(item.st_mode):
            download_dir(rpath, lpath)
        else:
            sftp.get(rpath, lpath)

download_dir(remote_dist, local_dist)
print(f"Dist descargado exitosamente a: {local_dist}", flush=True)

sftp.close()
client.close()
print("[EXITO] Frontend desplegado, compilado y sincronizado localmente!", flush=True)
