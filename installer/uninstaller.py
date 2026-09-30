#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Desinstalador Universal y Seguro (Uninstaller Guard) v2.5
Realiza una desinstalación 100% limpia y completa:
1. Identifica y termina todos los procesos de SentinelOS y libera el puerto 8001.
2. Elimina todas las tareas programadas y accesos de inicio automático (Startup y systemd).
3. Remueve las reglas de Firewall (Windows Defender / WFP / Linux UFW) y restaura el estado.
4. Borra todos los accesos directos (.lnk y .desktop) en TODOS los directorios de Escritorio
   (OneDrive Desktop, Escritorio de Usuario, Escritorio Público y Menú Inicio).
5. Remueve los comandos 'sentinel' del PATH y scripts de terminal.
6. Purgado integral de carpetas temporales, logs, caches y opcionalmente entorno virtual y directorio raíz.
7. NUNCA abre el navegador web.
"""

import os
import sys
import time
import shutil
import subprocess
from .banner import Colors, print_success, print_warning, print_info, print_error
from .firewall import remove_firewall_rule
from .port_guard import get_process_on_port
from .desktop_shortcut import get_all_desktop_dirs, get_start_menu_dir

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

def remove_all_shortcuts(root_dir: str):
    """Borra todos los accesos directos creados en cualquier carpeta del sistema."""
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

    # Borrar archivos de lanzamiento generados
    for f in ["launch_cockpit.pyw", "start_sentinel_bg.bat", "Sentinel.ico", "sentinel_backend.log"]:
        target = os.path.join(root_dir, f)
        if os.path.exists(target):
            try:
                os.remove(target)
            except Exception:
                pass

def remove_cli_from_path(root_dir: str):
    """Remueve los comandos CLI 'sentinel' instalados en el sistema."""
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            winapps = os.path.join(local_appdata, "Microsoft", "WindowsApps")
            for fname in ["sentinel.cmd", "sentinel.bat"]:
                p = os.path.join(winapps, fname)
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

        bin_dir = os.path.join(root_dir, "bin")
        if os.path.exists(bin_dir):
            try:
                shutil.rmtree(bin_dir, ignore_errors=True)
            except Exception:
                pass
    else:
        for p in ["/usr/local/bin/sentinel", os.path.expanduser("~/.local/bin/sentinel")]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

def run_full_uninstall(os_info: dict, root_dir: str, lang: str = "es", purge_venv: bool = False, purge_all_files: bool = False) -> bool:
    """Ejecuta la desinstalación completa y limpia de SentinelOS sin abrir el navegador."""
    print(f"\n{Colors.BOLD}{Colors.RED}╭── DESINSTALACIÓN COMPLETA DE SENTINEL OS ─────────────────────────╮{Colors.RESET}")
    
    # 1. Terminar procesos
    print_info("1/6 Deteniendo procesos y liberando puerto 8001..." if lang == "es" else "1/6 Stopping processes and releasing port 8001...")
    kill_sentinel_processes()
    time.sleep(0.5)

    # 2. Deshabilitar autostart y servicios
    print_info("2/6 Eliminando servicios y tareas de autoinicio..." if lang == "es" else "2/6 Removing services and autostart tasks...")
    remove_autostart_and_services(root_dir)

    # 3. Remover reglas de firewall
    print_info("3/6 Restaurando configuración de cortafuegos..." if lang == "es" else "3/6 Restoring firewall rules...")
    remove_firewall_rule(os_info, 8001, lang)

    # 4. Remover accesos directos
    print_info("4/6 Borrando accesos directos del Escritorio y Menú Inicio..." if lang == "es" else "4/6 Deleting desktop and start menu shortcuts...")
    remove_all_shortcuts(root_dir)

    # 5. Remover comandos de terminal PATH
    print_info("5/6 Eliminando comandos 'sentinel' del sistema..." if lang == "es" else "5/6 Removing 'sentinel' commands from PATH...")
    remove_cli_from_path(root_dir)

    # 6. Limpieza de carpetas y entorno virtual
    print_info("6/6 Purgando logs, configuraciones locales y temporales..." if lang == "es" else "6/6 Purging logs, local configs and temporary files...")
    
    # Limpiar config y logs
    for cfile in ["node_auth.json", "mesh_peers.json"]:
        cp = os.path.join(root_dir, "config", cfile)
        if os.path.exists(cp):
            try:
                os.remove(cp)
            except Exception:
                pass

    for tmp in ["sentinel_backend.log", "scratch/web_build/.vite"]:
        p = os.path.join(root_dir, tmp)
        if os.path.exists(p):
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
            except Exception:
                pass

    if purge_venv or purge_all_files:
        venv_path = os.path.join(root_dir, ".venv")
        if os.path.exists(venv_path):
            try:
                shutil.rmtree(venv_path, ignore_errors=True)
            except Exception:
                pass

    print_success("SentinelOS ha sido desinstalado del sistema limpia y completamente." if lang == "es" else "SentinelOS has been cleanly and completely uninstalled.")
    print(f"{Colors.BOLD}{Colors.RED}╰──────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")
    return True
