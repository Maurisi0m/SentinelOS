import sys
import paramiko

def run_cmd(cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect("192.168.68.68", port=22, username="mauro", password="Pollito92.", timeout=3)
    except Exception:
        client.connect("100.113.156.109", port=22, username="mauro", password="Pollito92.", timeout=5)
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    client.close()
    if out:
        sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    if err:
        sys.stderr.buffer.write(err.encode("utf-8", errors="replace"))
        sys.stderr.buffer.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-c":
            cmd = sys.argv[2]
        elif sys.argv[1] == "-f":
            with open(sys.argv[2], "r", encoding="utf-8") as f:
                cmd = f.read()
        else:
            cmd = " ".join(sys.argv[1:])
    else:
        cmd = sys.stdin.read()
    run_cmd(cmd)
