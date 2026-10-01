import os
import sys
from pathlib import Path

def create_desktop_shortcut(url="http://localhost:3000"):
    print("[*] Creando acceso directo al Cockpit de SentinelOS...")
    try:
        if sys.platform == "win32":
            desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
            if desktop.exists():
                url_file = desktop / "SentinelOS Cockpit.url"
                content = f"[InternetShortcut]\nURL={url}\nIconIndex=0\nIconFile={sys.executable}\n"
                url_file.write_text(content, encoding="utf-8")
                print(f"[+] Acceso directo creado en: {url_file}")
        elif sys.platform.startswith("linux"):
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                desktop = Path.home() / "Escritorio"
            if desktop.exists():
                desktop_entry = desktop / "sentinelos.desktop"
                content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SentinelOS Cockpit
Comment=Laboratorio STEM y Cockpit MLOps
Exec=xdg-open {url}
Icon=utilities-terminal
Terminal=false
Categories=Education;Development;
"""
                desktop_entry.write_text(content, encoding="utf-8")
                desktop_entry.chmod(0o755)
                print(f"[+] Acceso directo creado en: {desktop_entry}")
    except Exception as e:
        print(f"[!] Nota sobre acceso directo: {e}")
