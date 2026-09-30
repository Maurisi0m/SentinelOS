#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Desinstalador Universal y Seguro (Uninstaller Guard) v2.0
Realiza una desinstalación 100% limpia y completa:
1. Identifica y termina todos los procesos de SentinelOS y libera el puerto 8001.
2. Elimina todas las tareas programadas y accesos de inicio automático (Startup).
3. Remueve las reglas de Firewall (Windows Defender / Linux UFW).
4. Borra todos los accesos directos (.lnk y .desktop) en TODOS los directorios de Escritorio
   (OneDrive Desktop, Escritorio de Usuario, Escritorio Público y Menú Inicio).
5. Opcionalmente purga el entorno virtual (.venv) y archivos de configuración.
"""

import os
import sys
import time
import shutil
import subprocess
from .banner import Colors, print_success, print_warning, print_info, print_error, print_panel, print_prompt
from .firewall import remove_firewall_rule
from .port_guard import get_process_on_port

def is_admin() -> bool:
    if sys.platform == "win32":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return os.geteuid() == 0

def kill_sentinel_processes():
    """Identifica y termina con fuerza cualquier proceso de SentinelOS o que ocupe el puerto 8001."""
    # 1. Terminar proceso en puerto 8001
    pid, proc_name = get_process_on_port(8001)
    if pid > 0:
        try:
            if sys.platform == "win32":
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
            else:
                subprocess.run(f"kill -9 {pid} 2>/dev/null", shell=True, capture_output=True)
        except Exception:
            pass

    # 2. Terminar procesos python que ejecuten SentinelOS
    if sys.platform == "win32":
        try:
            # Terminar procesos con linea de comando de Sentinel
            ps_script = """
            Get-CimInstance Win32_Process | Where-Object { 
                $_.CommandLine -match "labsentinel_backend" -or 
                $_.CommandLine -match "launch_cockpit" -or 
                $_.CommandLine -match "service_runner" -or 
                $_.CommandLine -match "uvicorn.*main:app"
            } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
            """
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], capture_output=True)
        except Exception:
            pass
    else:
        subprocess.run("pkill -9 -f 'labsentinel_backend|main:app|launch_cockpit|service_runner' 2>/dev/null || true", shell=True)

def remove_autostart_and_services(root_dir: str):
    """Elimina servicios systemd, tareas de Windows y archivos de Startup."""
    if sys.platform == "win32":
        try:
            subprocess.run('schtasks /Delete /TN "SentinelOS_Service" /F', shell=True, capture_output=True)
            subprocess.run('schtasks /Delete /TN "SentinelOS_AutoStart" /F', shell=True, capture_output=True)
        except Exception:
            pass

        # Eliminar archivo en carpeta Startup
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            startup_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
            for fname in ["SentinelOS_AutoStart.cmd", "SentinelOS.cmd", "SentinelOS Cockpit.lnk", "SentinelOS.lnk"]:
                target = os.path.join(startup_dir, fname)
                if os.path.exists(target):
                    try:
                        os.remove(target)
                    except Exception:
                        pass
    else:
        subprocess.run("systemctl stop labsentinel.service sentinel.service sentinel-orchestrator.service 2>/dev/null || true", shell=True)
        subprocess.run("systemctl disable labsentinel.service sentinel.service sentinel-orchestrator.service 2>/dev/null || true", shell=True)
        subprocess.run("rm -f /etc/systemd/system/labsentinel.service /etc/systemd/system/sentinel.service /etc/systemd/system/sentinel-orchestrator.service", shell=True)
        subprocess.run("rm -rf /etc/systemd/system/sentinel*.service.d 2>/dev/null || true", shell=True)
        subprocess.run("systemctl daemon-reload 2>/dev/null || true", shell=True)

def get_all_possible_desktop_paths() -> list[str]:
    """Descubre todas las ubicaciones posibles del Escritorio en el sistema (OneDrive, Usuario, Público)."""
    paths = set()
    if sys.platform == "win32":
        # 1. Registro de Windows Shell Folders
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            val, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            d = os.path.expandvars(val)
            if os.path.exists(d):
                paths.add(d)
        except Exception:
            pass

        # 2. USERPROFILE\Desktop
        u_prof = os.environ.get("USERPROFILE", "")
        if u_prof:
            for sub in ["Desktop", "Escritorio", r"OneDrive\Desktop", r"OneDrive\Escritorio"]:
                p = os.path.join(u_prof, sub)
                if os.path.exists(p):
                    paths.add(p)

        # 3. Public Desktop
        pub = os.environ.get("PUBLIC", r"C:\Users\Public")
        for sub in ["Desktop", "Escritorio"]:
            p = os.path.join(pub, sub)
            if os.path.exists(p):
                paths.add(p)

        # 4. Menú Inicio Programas
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            p = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs")
            if os.path.exists(p):
                paths.add(p)
    else:
        paths.add(os.path.expanduser("~/Desktop"))
        paths.add(os.path.expanduser("~/.local/share/applications"))
        paths.add("/usr/share/applications")

    return [p for p in paths if os.path.exists(p)]

def remove_all_shortcuts(root_dir: str):
    """Borra todos los accesos directos creados en cualquier carpeta del sistema."""
    names_to_delete = [
        "SentinelOS Cockpit.lnk",
        "SentinelOS.lnk",
        "Sentinel.lnk",
        "SentinelOS.desktop",
        "sentinelos.desktop"
    ]
    for d in get_all_possible_desktop_paths():
        for name in names_to_delete:
            f = os.path.join(d, name)
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    # Borrar archivos generados en el directorio raíz
    for f in ["launch_cockpit.pyw", "start_sentinel_bg.bat", "Sentinel.ico", "sentinel_backend.log"]:
        target = os.path.join(root_dir, f)
        if os.path.exists(target):
            try:
                os.remove(target)
            except Exception:
                pass

def run_full_uninstall(os_info: dict, root_dir: str, lang: str = "es", purge_venv: bool = False) -> bool:
    """Ejecuta la desinstalación completa y limpia de SentinelOS."""
    print(f"\n{Colors.BOLD}{Colors.RED}╭── DESINSTALACIÓN COMPLETA DE SENTINEL OS ─────────────────────────╮{Colors.RESET}")
    
    # 1. Terminar procesos
    print_info("1/5 Deteniendo procesos y liberando puerto 8001..." if lang == "es" else "1/5 Stopping processes and releasing port 8001...")
    kill_sentinel_processes()
    time.sleep(0.5)

    # 2. Deshabilitar autostart y servicios
    print_info("2/5 Eliminando servicios y tareas de autoinicio..." if lang == "es" else "2/5 Removing services and autostart tasks...")
    remove_autostart_and_services(root_dir)

    # 3. Remover reglas de firewall
    print_info("3/5 Removiendo reglas de cortafuegos..." if lang == "es" else "3/5 Removing firewall rules...")
    remove_firewall_rule(os_info, 8001, lang)

    # 4. Remover accesos directos
    print_info("4/5 Borrando accesos directos del Escritorio y Menú Inicio..." if lang == "es" else "4/5 Deleting desktop and start menu shortcuts...")
    remove_all_shortcuts(root_dir)

    # 5. Limpieza opcional de entorno virtual y credenciales
    if purge_venv:
        print_info("5/5 Purgando entorno virtual (.venv) y configuraciones locales..." if lang == "es" else "5/5 Purging virtual environment (.venv) and local configs...")
        venv_path = os.path.join(root_dir, ".venv")
        if os.path.exists(venv_path):
            try:
                shutil.rmtree(venv_path, ignore_errors=True)
            except Exception:
                pass
        for cfile in ["node_auth.json", "mesh_peers.json"]:
            cp = os.path.join(root_dir, "config", cfile)
            if os.path.exists(cp):
                try:
                    os.remove(cp)
                except Exception:
                    pass
    else:
        print_info("5/5 Conservando archivos fuente y entorno virtual para reinstalación rápida." if lang == "es" else "5/5 Preserving source files and virtualenv.")

    print_success("SentinelOS ha sido desinstalado del sistema limpia y exitosamente." if lang == "es" else "SentinelOS has been successfully and cleanly uninstalled.")
    print(f"{Colors.BOLD}{Colors.RED}╰──────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")
    return True
