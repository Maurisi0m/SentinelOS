#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Creador de Accesos Directos Nativos de Escritorio y Menú Inicio v2.5
Crea accesos directos nativos y silenciosos en el Escritorio y Menú Inicio en Windows, Ubuntu, Mint y Debian.
Garantiza que el acceso directo sea visible y ejecutable en cualquier PC o laptop.
"""
import os, sys, struct, subprocess, tempfile, shutil
from .banner import Colors, print_success, print_warning, print_info
from .service_config import get_service_port

def generate_sentinel_ico(ico_path: str):
    """Genera un archivo de icono .ico nativo de 32x32 RGBA sin requerir Pillow."""
    width = 32
    height = 32
    bpp = 32

    # Cabecera ICO (tipo 1 = icon, 1 imagen)
    header = struct.pack('<HHH', 0, 1, 1)

    # Cabecera DIB BMP (altura duplicada para color + máscara)
    bih = struct.pack('<IIIHHIIIIII', 40, width, height * 2, 1, bpp, 0, width * height * 4, 0, 0, 0, 0)

    # Generación de píxeles: Gradiente circular ciberespacial (púrpura a cian)
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            dx = x - 15.5
            dy = y - 15.5
            dist = (dx*dx + dy*dy) ** 0.5
            if dist <= 14.0:
                b = int(255 * (x / 31.0))
                g = int(180 * (y / 31.0))
                r = int(140 + 80 * (1 - x / 31.0))
                a = 255
                if 11.5 <= dist <= 13.5:
                    r, g, b = 56, 189, 248  # Anillo cian neón
            else:
                r, g, b, a = 0, 0, 0, 0
            pixels.extend([b, g, r, a])

    mask_row_bytes = ((width + 31) // 32) * 4
    mask = bytearray(mask_row_bytes * height)

    img_data = bih + pixels + mask
    img_size = len(img_data)
    offset = 6 + 16

    entry = struct.pack('<BBBBHHII', width, height, 0, 0, 1, bpp, img_size, offset)

    with open(ico_path, 'wb') as f:
        f.write(header + entry + img_data)

def create_silent_launcher(root_dir: str) -> str:
    """Crea el script launch_cockpit.pyw que arranca el daemon silenciosamente si está apagado y abre el navegador."""
    launcher_path = os.path.join(root_dir, "launch_cockpit.pyw")
    content = '''import os, sys, webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from installer.background_service import launch_service_manager, wait_for_health
from installer.service_config import get_service_port

def main():
    port = get_service_port(ROOT_DIR)
    launch_service_manager(ROOT_DIR, suppress_ui=True)
    if wait_for_health(port, timeout=90):
        webbrowser.open(f"http://127.0.0.1:{port}")

if __name__ == "__main__":
    main()
'''
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(content)
    return launcher_path

def get_all_desktop_dirs() -> list[str]:
    """Obtiene todas las posibles rutas de Escritorio en el sistema (OneDrive, Usuario, Público, Linux)."""
    dirs = set()
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            val, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            d = os.path.expandvars(val)
            if os.path.exists(d):
                dirs.add(d)
        except Exception:
            pass

        u_prof = os.environ.get("USERPROFILE", "")
        if u_prof:
            for sub in ["Desktop", "Escritorio", r"OneDrive\Desktop", r"OneDrive\Escritorio"]:
                p = os.path.join(u_prof, sub)
                if os.path.exists(p):
                    dirs.add(p)

        pub = os.environ.get("PUBLIC", r"C:\Users\Public")
        for sub in ["Desktop", "Escritorio"]:
            p = os.path.join(pub, sub)
            if os.path.exists(p):
                dirs.add(p)
    else:
        # Linux (Ubuntu, Mint, Debian, etc.)
        home = os.path.expanduser("~")
        for sub in ["Desktop", "Escritorio"]:
            p = os.path.join(home, sub)
            if os.path.exists(p):
                dirs.add(p)
        try:
            res = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                xdg_d = res.stdout.strip()
                if os.path.exists(xdg_d):
                    dirs.add(xdg_d)
        except Exception:
            pass

    return [d for d in dirs if os.path.exists(d)]

def get_start_menu_dir() -> str:
    """Obtiene el directorio de Programas del Menú Inicio en Windows o Linux."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            programs = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs")
            if os.path.exists(programs):
                return programs
        return ""
    else:
        apps = os.path.expanduser("~/.local/share/applications")
        os.makedirs(apps, exist_ok=True)
        return apps

def create_windows_lnk(target_path: str, arguments: str, working_dir: str, shortcut_path: str, icon_path: str = None, description: str = "") -> bool:
    """Crea un acceso directo .lnk en Windows utilizando WScript.Shell de forma nativa."""
    vbs_lines = [
        'Set ws = CreateObject("WScript.Shell")',
        f'Set s = ws.CreateShortcut("{shortcut_path}")',
        f's.TargetPath = "{target_path}"',
        f's.Arguments = "{arguments}"',
        f's.WorkingDirectory = "{working_dir}"',
    ]
    if icon_path and os.path.exists(icon_path):
        vbs_lines.append(f's.IconLocation = "{icon_path}"')
    if description:
        vbs_lines.append(f's.Description = "{description}"')
    vbs_lines.append('s.Save')

    vbs_content = "\r\n".join(vbs_lines)
    vbs_file = os.path.join(tempfile.gettempdir(), 'create_sntl_lnk.vbs')
    try:
        with open(vbs_file, 'w', encoding='utf-8') as f:
            f.write(vbs_content)
        subprocess.run(['cscript', '//nologo', vbs_file], capture_output=True)
        if os.path.exists(vbs_file):
            os.remove(vbs_file)
        return os.path.exists(shortcut_path)
    except Exception:
        return False

def configure_desktop_shortcuts(root_dir: str, os_info: dict, lang: str = "es") -> bool:
    """Configura los accesos directos de escritorio y menú inicio según el sistema operativo."""
    system = os_info.get("system", "Linux")
    launcher_path = create_silent_launcher(root_dir)
    ico_path = os.path.join(root_dir, "Sentinel.ico")
    if not os.path.exists(ico_path):
        try:
            generate_sentinel_ico(ico_path)
        except Exception:
            pass

    created_any = False

    if system == "Windows":
        venv_pyw = os.path.join(root_dir, ".venv", "Scripts", "pythonw.exe")
        venv_py = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
        sys_pyw = sys.executable.replace("python.exe", "pythonw.exe")
        target_py = venv_pyw if os.path.exists(venv_pyw) else (sys_pyw if os.path.exists(sys_pyw) else sys.executable)

        desktop_dirs = get_all_desktop_dirs()
        for d in desktop_dirs:
            desktop_lnk = os.path.join(d, "SentinelOS Cockpit.lnk")
            ok = create_windows_lnk(
                target_path=target_py,
                arguments=f'"{launcher_path}"',
                working_dir=root_dir,
                shortcut_path=desktop_lnk,
                icon_path=ico_path,
                description="SentinelOS Distributed Cockpit"
            )
            if ok:
                created_any = True

        start_menu_dir = get_start_menu_dir()
        if start_menu_dir:
            start_lnk = os.path.join(start_menu_dir, "SentinelOS Cockpit.lnk")
            create_windows_lnk(
                target_path=target_py,
                arguments=f'"{launcher_path}"',
                working_dir=root_dir,
                shortcut_path=start_lnk,
                icon_path=ico_path,
                description="SentinelOS Distributed Cockpit"
            )

        if created_any:
            msg = f"Acceso directo creado en el Escritorio ({len(desktop_dirs)} ubicaciones detectadas)." if lang == "es" else "Desktop shortcut created in all detected desktop directories."
            print_success(msg)
            return True
        return False

    elif system == "Linux":
        # Formato estándar FreeDesktop .desktop para Ubuntu, Mint, Debian, Arch
        venv_py = os.path.join(root_dir, ".venv", "bin", "python3")
        py_bin = venv_py if os.path.exists(venv_py) else "python3"
        icon_path = os.path.join(root_dir, "labsentinel_backend", "dist", "favicon.svg")
        if not os.path.exists(icon_path):
            icon_path = ico_path

        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SentinelOS Cockpit
Comment=Laboratorio STEM y Panel de Control Distribuido
Exec={py_bin} "{launcher_path}"
Path={root_dir}
Icon={icon_path}
Terminal=false
Categories=System;Development;Science;
StartupNotify=true
"""
        # Guardar en aplicaciones del sistema
        apps_dir = get_start_menu_dir()
        app_file = os.path.join(apps_dir, "sentinelos.desktop")
        try:
            with open(app_file, "w", encoding="utf-8") as f:
                f.write(desktop_entry)
            os.chmod(app_file, 0o755)
            created_any = True
        except Exception:
            pass

        # Guardar en todos los Escritorios detectados (Desktop, Escritorio, xdg)
        desktop_dirs = get_all_desktop_dirs()
        for d in desktop_dirs:
            desktop_file = os.path.join(d, "SentinelOS.desktop")
            try:
                with open(desktop_file, "w", encoding="utf-8") as f:
                    f.write(desktop_entry)
                os.chmod(desktop_file, 0o755)
                # Marcar como confiable en GNOME/Cinnamon (Ubuntu/Mint)
                try:
                    subprocess.run(["gio", "set", desktop_file, "metadata::trusted", "true"], capture_output=True)
                except Exception:
                    pass
                created_any = True
            except Exception:
                pass

        if created_any:
            msg = "Acceso directo creado en Aplicaciones y Escritorio (Ubuntu / Mint)." if lang == "es" else "Desktop entry created in Applications and Desktop."
            print_success(msg)
            return True

    return False

def remove_desktop_shortcuts(root_dir: str, os_info: dict):
    """Remueve los accesos directos al desinstalar desde todas las rutas posibles del sistema."""
    names_to_delete = [
        "SentinelOS Cockpit.lnk",
        "SentinelOS.lnk",
        "Sentinel.lnk",
        "SentinelOS.desktop",
        "sentinelos.desktop"
    ]
    for d in get_all_desktop_dirs():
        for name in names_to_delete:
            f = os.path.join(d, name)
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    s_dir = get_start_menu_dir()
    if s_dir and os.path.exists(s_dir):
        for name in names_to_delete:
            f = os.path.join(s_dir, name)
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    for f in ["launch_cockpit.pyw", "start_sentinel_bg.bat", "Sentinel.ico", "sentinel_backend.log"]:
        target = os.path.join(root_dir, f)
        if os.path.exists(target):
            try:
                os.remove(target)
            except Exception:
                pass
