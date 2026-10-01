import os
import sys
import time
import paramiko
from scp import SCPClient

HOST = "100.113.156.109"
USER = "mauro"
PASS = "Pollito92."
LOCAL_FILE = r"C:\Users\mauro\OneDrive\Desktop\Sentinel\export\output_gguf\sentinel-master.Q3_K_M.gguf"
REMOTE_DEST = "/home/mauro/sentinel-master.Q3_K_M.gguf"

def progress_callback(filename, size, sent):
    pct = (sent / size) * 100 if size > 0 else 0
    mb_sent = sent / (1024 * 1024)
    mb_total = size / (1024 * 1024)
    sys.stdout.write(f"\r[SCP] {os.path.basename(filename)}: {mb_sent:.1f}/{mb_total:.1f} MB ({pct:.1f}%)")
    sys.stdout.flush()

def main():
    print(f"Connecting to {USER}@{HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=22, username=USER, password=PASS)
    print("SSH Connected. Uploading Q3_K_M model...")

    t0 = time.time()
    with SCPClient(client.get_transport(), progress=progress_callback) as scp:
        scp.put(LOCAL_FILE, remote_path=REMOTE_DEST)

    t1 = time.time()
    print(f"\nUpload complete in {t1 - t0:.1f}s ({(os.path.getsize(LOCAL_FILE)/(1024*1024))/(max(1, t1 - t0)):.2f} MB/s)!")

    print("Moving model to /opt/sentinel/models/ and setting permissions...")
    cmd = (
        f"echo '{PASS}' | sudo -S mv /home/mauro/sentinel-master.Q3_K_M.gguf /opt/sentinel/models/sentinel-master.Q3_K_M.gguf && "
        f"echo '{PASS}' | sudo -S chown sentinel:sentinel /opt/sentinel/models/sentinel-master.Q3_K_M.gguf && "
        f"echo '{PASS}' | sudo -S chmod 664 /opt/sentinel/models/sentinel-master.Q3_K_M.gguf && "
        "ls -lh /opt/sentinel/models/"
    )
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print(out)
    if err:
        print("ERR:", err)
    client.close()

if __name__ == "__main__":
    main()
