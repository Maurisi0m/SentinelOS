import os
import sys
import time
import paramiko
from scp import SCPClient

HOST = "192.168.68.68"
USER = "mauro"
PASS = "Pollito92."
LOCAL_FILE = r"C:\Users\mauro\OneDrive\Desktop\Sentinel\export\output_gguf\sentinel-pure-stem-1b.Q4_K_M.gguf"
REMOTE_DEST = "/home/mauro/sentinel-pure-stem-1b.Q4_K_M.gguf"

def progress_callback(filename, size, sent):
    pct = (sent / size) * 100 if size > 0 else 0
    mb_sent = sent / (1024 * 1024)
    mb_total = size / (1024 * 1024)
    sys.stdout.write(f"\r[SCP] {os.path.basename(filename)}: {mb_sent:.1f}/{mb_total:.1f} MB ({pct:.1f}%)")
    sys.stdout.flush()

def main():
    if not os.path.exists(LOCAL_FILE):
        print(f"Error: {LOCAL_FILE} no existe aún.")
        return

    print(f"Connecting to {USER}@{HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=22, username=USER, password=PASS, timeout=10)
    print("SSH Connected. Uploading 1B model...")

    t0 = time.time()
    with SCPClient(client.get_transport(), progress=progress_callback) as scp:
        scp.put(LOCAL_FILE, remote_path=REMOTE_DEST)

    t1 = time.time()
    print(f"\nUpload complete in {t1 - t0:.1f}s!")

    print("Moving model to /opt/sentinel/models/ and restarting sentinel.service...")
    cmd = (
        f"echo '{PASS}' | sudo -S mv /home/mauro/sentinel-pure-stem-1b.Q4_K_M.gguf /opt/sentinel/models/sentinel-pure-stem-1b.Q4_K_M.gguf && "
        f"echo '{PASS}' | sudo -S chown sentinel:sentinel /opt/sentinel/models/sentinel-pure-stem-1b.Q4_K_M.gguf && "
        f"echo '{PASS}' | sudo -S chmod 664 /opt/sentinel/models/sentinel-pure-stem-1b.Q4_K_M.gguf && "
        f"echo '{PASS}' | sudo -S systemctl restart sentinel.service && "
        "systemctl is-active sentinel.service"
    )
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("Result:\n", out)
    if err:
        print("ERR:", err)
    client.close()

if __name__ == "__main__":
    main()
