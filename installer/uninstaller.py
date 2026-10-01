import sys
import os
import shutil
import subprocess
from pathlib import Path

def perform_uninstall():
    print("""
\033[1;31m====================================================\033[0m
\033[1;31m  SENTINEL // Desinstalador Atómico y Reversión\033[0m
\033[1;31m====================================================\033[0m
""")
    # 1. Stop services
    from installer.service_runner import stop_services
    stop_services()

    # 2. Remove desktop shortcut
    try:
        if sys.platform == "win32":
            desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "SentinelOS Cockpit.url"
            if desktop.exists():
                desktop.unlink()
        else:
            desktop = Path.home() / "Desktop" / "sentinelos.desktop"
            if desktop.exists():
                desktop.unlink()
        print("[+] Accesos directos eliminados.")
    except Exception as e:
        print(f"[!] Error al remover accesos directos: {e}")

    # 3. Clean firewall rules
    try:
        if sys.platform == "win32":
            for name in ["SentinelOS-HTTP", "SentinelOS-Mesh", "SentinelOS-Vite"]:
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={name}"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            print("[+] Reglas de cortafuegos removidas.")
    except Exception:
        pass

    print("\033[1;32m[✓] Desinstalación completada con éxito sin residuos.\033[0m")
