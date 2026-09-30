#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Creador de Accesos Directos Nativos de Escritorio y Menú Inicio v2.0
Crea accesos directos silenciosos (sin ventana negra de terminal) en el Escritorio y Menú Inicio en Windows y Linux.
"""
import os, sys, struct, subprocess, tempfile
from .banner import Colors, print_success, print_warning, print_info

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
    content = '''import os, sys, time, subprocess, urllib.request, webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "labsentinel_backend")

def is_running():
    try:
        req = urllib.request.Request("http://127.0.0.1:8001/api/data", headers={"User-Agent": "SentinelLauncher"})
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False

def main():
    if not is_running():
        # Priorizar pythonw de .venv para evitar abrir consola negra
        if sys.platform == "win32":
            venv_pyw = os.path.join(ROOT_DIR, ".venv", "Scripts", "pythonw.exe")
            venv_py = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
            sys_pyw = sys.executable.replace("python.exe", "pythonw.exe")
            py_bin = venv_pyw if os.path.exists(venv_pyw) else (venv_py if os.path.exists(venv_py) else sys_pyw)
            
            log_file = os.path.join(ROOT_DIR, "sentinel_backend.log")
            log_out = open(log_file, "a", encoding="utf-8")
            
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
                cwd=BACKEND_DIR,
                stdout=log_out,
                stderr=log_out,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
                close_fds=True
            )
        else:
            venv_py = os.path.join(ROOT_DIR, ".venv", "bin", "python3")
            py_bin = venv_py if os.path.exists(venv_py) else sys.executable
            log_file = os.path.join(ROOT_DIR, "sentinel_backend.log")
            log_out = open(log_file, "a", encoding="utf-8")
            subprocess.Popen(
                [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
                cwd=BACKEND_DIR,
                stdout=log_out,
                stderr=log_out,
                start_new_session=True
            )

        # Esperar hasta que el servidor esté listo
        for _ in range(12):
            time.sleep(0.5)
            if is_running():
                break

    webbrowser.open("http://127.0.0.1:8001")

if __name__ == "__main__":
    main()
'''
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(content)
    return launcher_path

def get_desktop_dir() -> str:
    """Obtiene la ruta real del Escritorio considerando OneDrive y configuraciones de usuario."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            val, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            d = os.path.expandvars(val)
            if os.path.exists(d):
                return d
        except Exception:
            pass
        fallback = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        return fallback if os.path.exists(fallback) else os.path.expanduser("~/Desktop")
    else:
        return os.path.expanduser("~/Desktop")

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

    if system == "Windows":
        # Localizar el ejecutable pythonw (silencioso sin terminal)
        venv_pyw = os.path.join(root_dir, ".venv", "Scripts", "pythonw.exe")
        venv_py = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
        sys_pyw = sys.executable.replace("python.exe", "pythonw.exe")
        target_py = venv_pyw if os.path.exists(venv_pyw) else (sys_pyw if os.path.exists(sys_pyw) else sys.executable)

        desktop_dir = get_desktop_dir()
        desktop_lnk = os.path.join(desktop_dir, "SentinelOS Cockpit.lnk")
        success_desktop = create_windows_lnk(
            target_path=target_py,
            arguments=f'"{launcher_path}"',
            working_dir=root_dir,
            shortcut_path=desktop_lnk,
            icon_path=ico_path,
            description="SentinelOS Distributed Cockpit"
        )

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

        if success_desktop:
            msg = f"Acceso directo creado en el Escritorio: {desktop_lnk}" if lang == "es" else f"Desktop shortcut created: {desktop_lnk}"
            print_success(msg)
            return True
        return False

    elif system == "Linux":
        # Formato estándar FreeDesktop .desktop
        icon_path = os.path.join(root_dir, "labsentinel_backend", "dist", "favicon.svg")
        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SentinelOS Cockpit
Comment=Laboratorio STEM y Panel de Control Distribuido
Exec=python3 "{launcher_path}"
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
        except Exception:
            pass

        # Guardar en Escritorio si existe
        desktop_dir = get_desktop_dir()
        desktop_file = os.path.join(desktop_dir, "SentinelOS.desktop")
        try:
            if os.path.exists(desktop_dir):
                with open(desktop_file, "w", encoding="utf-8") as f:
                    f.write(desktop_entry)
                os.chmod(desktop_file, 0o755)
        except Exception:
            pass

        msg = "Acceso directo creado en Aplicaciones y Escritorio." if lang == "es" else "Desktop entry created in Applications and Desktop."
        print_success(msg)
        return True

    return False

def remove_desktop_shortcuts(root_dir: str, os_info: dict):
    """Remueve los accesos directos al desinstalar desde todas las rutas posibles del sistema."""
    system = os_info.get("system", "Linux")
    if system == "Windows":
        candidates = set()
        candidates.add(get_desktop_dir())
        candidates.add(get_start_menu_dir())
        
        u_prof = os.environ.get("USERPROFILE", "")
        if u_prof:
            for sub in ["Desktop", "Escritorio", r"OneDrive\Desktop", r"OneDrive\Escritorio"]:
                p = os.path.join(u_prof, sub)
                if os.path.exists(p):
                    candidates.add(p)
        pub = os.environ.get("PUBLIC", r"C:\Users\Public")
        for sub in ["Desktop", "Escritorio"]:
            p = os.path.join(pub, sub)
            if os.path.exists(p):
                candidates.add(p)

        for p in candidates:
            if p and os.path.exists(p):
                for name in ["SentinelOS Cockpit.lnk", "SentinelOS.lnk", "Sentinel.lnk"]:
                    lnk = os.path.join(p, name)
                    if os.path.exists(lnk):
                        try:
                            os.remove(lnk)
                        except Exception:
                            pass
        
        for f in ["launch_cockpit.pyw", "start_sentinel_bg.bat", "Sentinel.ico", "sentinel_backend.log"]:
            target = os.path.join(root_dir, f)
            if os.path.exists(target):
                try:
                    os.remove(target)
                except Exception:
                    pass
    elif system == "Linux":
        for p in [get_desktop_dir(), get_start_menu_dir(), os.path.expanduser("~/.local/share/applications")]:
            if p and os.path.exists(p):
                for name in ["SentinelOS.desktop", "sentinelos.desktop"]:
                    f = os.path.join(p, name)
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except Exception:
                            pass
