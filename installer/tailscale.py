import shutil
import subprocess

def check_tailscale():
    print("[*] Comprobando integración con red Zero-Trust Tailscale...")
    ts = shutil.which("tailscale")
    if ts:
        try:
            out = subprocess.check_output([ts, "status", "--json"], timeout=3, text=True)
            print("[+] Tailscale detectado y enlazado.")
        except Exception:
            print("[*] Tailscale instalado pero esperando inicio de sesión.")
    else:
        print("[*] Tailscale opcional: no detectado en el PATH.")
