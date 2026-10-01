import sys
import os
from pathlib import Path

def configure_autostart():
    print("[*] Configurando autoarranque de SentinelOS...")
    try:
        if sys.platform == "win32":
            startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            if startup.exists():
                bat = startup / "sentinel_autostart.bat"
                bat.write_text(f'@echo off\ncd /d "{Path(__file__).parent.parent}"\npython -m installer --daemon\n', encoding="utf-8")
                print(f"[+] Entrada de inicio registrada en: {bat}")
        elif sys.platform.startswith("linux"):
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            desktop = autostart_dir / "sentinelos.desktop"
            desktop.write_text(f"""[Desktop Entry]
Type=Application
Exec=python3 {Path(__file__).parent.parent / "installer" / "__main__.py"} --daemon
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=SentinelOS Autostart
""", encoding="utf-8")
            print(f"[+] Autoarranque configurado en: {desktop}")
    except Exception as e:
        print(f"[!] Nota sobre autoarranque: {e}")
