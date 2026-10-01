#!/usr/bin/env python3
import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "100.113.156.109"
USER = "mauro"
PASS = "Pollito92."

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS)

def run(cmd):
    _, out, err = client.exec_command(f'echo "{PASS}" | sudo -S bash -c "{cmd}"')
    o = out.read().decode('utf-8', errors='replace').strip()
    e = err.read().decode('utf-8', errors='replace').strip()
    return o, e

sftp = client.open_sftp()
with sftp.file("/tmp/Modelfile.master", "w") as f:
    f.write("FROM /opt/sentinel/models/sentinel-master.Q4_K_M.gguf\n")
sftp.close()

print("[1] Creando modelo sentinel-master:titan...")
o, e = run("/bin/ollama create sentinel-master:titan -f /tmp/Modelfile.master")
print(o)
if e:
    print("ERR:", e)

print("\n[2] Modelos en Ollama:")
o, _ = run("/bin/ollama list")
print(o)


client.close()
