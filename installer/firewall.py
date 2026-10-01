import sys
import subprocess
import shutil

def configure_firewall():
    print("[*] Configurando reglas de cortafuegos para telemetría y malla SentinelOS...")
    try:
        if sys.platform == "win32":
            # Windows Defender Firewall
            rules = [
                ("SentinelOS-HTTP", "8001", "TCP"),
                ("SentinelOS-Mesh", "8002", "UDP"),
                ("SentinelOS-Vite", "3000", "TCP")
            ]
            for name, port, proto in rules:
                subprocess.run([
                    "netsh", "advfirewall", "firewall", "add", "rule",
                    f"name={name}", "dir=in", "action=allow",
                    f"protocol={proto}", f"localport={port}"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            print("[+] Reglas de Windows Defender Firewall registradas.")
        elif sys.platform.startswith("linux"):
            if shutil.which("ufw"):
                for port, proto in [("8001", "tcp"), ("8002", "udp"), ("3000", "tcp")]:
                    subprocess.run(["sudo", "ufw", "allow", f"{port}/{proto}"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                print("[+] Reglas UFW registradas.")
    except Exception as e:
        print(f"[!] Advertencia al configurar cortafuegos: {e}")
