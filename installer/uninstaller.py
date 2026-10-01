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
from .desktop_shortcut import get_all_desktop_dirs, get_start_menu_dir

def is_admin() -> bool:
    if sys.platform == "win32":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return os.geteuid() == 0


def _run_system_command(args: list[str], timeout: int = 25) -> subprocess.CompletedProcess:
    """Run a system cleanup command, requesting sudo only when the uninstaller is not root."""
    if is_admin():
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    sudo = shutil.which("sudo")
    if sudo:
        return subprocess.run([sudo, *args], capture_output=True, text=True, timeout=timeout)
    return subprocess.CompletedProcess(args, 127, "", "administrator privileges are required")

def _path_is_within(path: str, root_dir: str) -> bool:
    if not path:
        return False
    try:
        return os.path.commonpath((os.path.realpath(path), os.path.realpath(root_dir))) == os.path.realpath(root_dir)
    except (OSError, ValueError):
        return False


def _is_sentinel_backend_process(proc, root_dir: str) -> bool:
    """Match only Sentinel's own backend/launcher, never every Python process or port owner."""
    try:
        info = proc.info
        cmdline = info.get("cmdline") or []
        command = " ".join(str(part) for part in cmdline).casefold()
        name = (info.get("name") or "").casefold()
        executable = info.get("exe") or ""
        cwd = info.get("cwd") or ""
    except Exception:
        return False

    is_python = "python" in name or "python" in os.path.basename(executable).casefold()
    if not is_python:
        return False

    is_uvicorn = "uvicorn" in command and "main:app" in command
    is_launcher = any(
        marker in command
        for marker in ("launch_cockpit.pyw", "start_sentinel_bg.bat", "start_sentinel_silent.vbs")
    )
    if not (is_uvicorn or is_launcher):
        return False

    root_marker = os.path.normcase(os.path.realpath(root_dir)).casefold()
    command_has_root = root_marker in os.path.normcase(command).casefold()
    return (
        command_has_root
        or _path_is_within(cwd, root_dir)
        or _path_is_within(executable, os.path.join(root_dir, ".venv"))
    )


def kill_sentinel_processes(root_dir: str = None) -> dict:
    """Stop only backend processes belonging to this install root; leave unrelated port owners alone."""
    root_dir = os.path.realpath(root_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = {"stopped": [], "failed": []}
    try:
        import psutil
    except ImportError:
        print_warning("No se pudo inspeccionar procesos: falta psutil.")
        result["failed"].append("psutil-unavailable")
        return result

    protected = {os.getpid()}
    try:
        current = psutil.Process(os.getpid())
        protected.update(parent.pid for parent in current.parents())
    except Exception:
        pass

    candidates = []
    for proc in psutil.process_iter(attrs=["pid", "name", "exe", "cmdline", "cwd"]):
        if proc.pid in protected or not _is_sentinel_backend_process(proc, root_dir):
            continue
        candidates.append(proc)

    # Stop child helpers together with the matched backend, without broad image-name kills.
    for proc in candidates:
        try:
            children = proc.children(recursive=True)
        except Exception:
            children = []
        for child in children:
            if child.pid not in protected and child not in candidates:
                candidates.append(child)

    for proc in candidates:
        try:
            if proc.is_running():
                proc.terminate()
        except Exception:
            continue

    _, alive = psutil.wait_procs(candidates, timeout=3)
    for proc in alive:
        try:
            proc.kill()
        except Exception:
            pass

    for proc in candidates:
        try:
            proc.wait(timeout=1)
            result["stopped"].append(proc.pid)
        except psutil.NoSuchProcess:
            result["stopped"].append(proc.pid)
        except Exception:
            result["failed"].append(proc.pid)

    return result

def remove_autostart_and_services(root_dir: str, stop_services: bool = True) -> bool:
    """Elimina servicios systemd, tareas de Windows y archivos de Startup."""
    success = True
    if sys.platform == "win32":
        for task in ("SentinelOS_Service", "SentinelOS_AutoStart"):
            try:
                query = subprocess.run(["schtasks", "/Query", "/TN", task], capture_output=True, text=True, timeout=15)
                if query.returncode == 0:
                    deleted = subprocess.run(["schtasks", "/Delete", "/TN", task, "/F"], capture_output=True, timeout=15)
                    success = success and deleted.returncode == 0
            except Exception:
                success = False

        appdata = os.environ.get("APPDATA", "")
        if appdata:
            startup_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
            for fname in [
                "SentinelOS_AutoStart.cmd", "SentinelOS_AutoStart.vbs", "SentinelOS.cmd",
                "SentinelOS Cockpit.lnk", "SentinelOS.lnk",
            ]:
                target = os.path.join(startup_dir, fname)
                if os.path.exists(target):
                    try:
                        os.remove(target)
                    except Exception:
                        success = False
        return success
    else:
        units = ("labsentinel.service", "sentinel.service", "sentinel-orchestrator.service")
        changed = False
        for unit in units:
            unit_path = os.path.join("/etc/systemd/system", unit)
            try:
                active = subprocess.run(["systemctl", "is-active", unit], capture_output=True, text=True, timeout=10)
                registered = subprocess.run(["systemctl", "list-unit-files", unit, "--no-legend"], capture_output=True, text=True, timeout=10)
            except Exception:
                success = False
                continue
            if not os.path.exists(unit_path) and active.returncode != 0 and not registered.stdout.strip():
                continue
            changed = True
            if stop_services:
                stopped = _run_system_command(["systemctl", "stop", unit], timeout=30)
                success = success and stopped.returncode == 0
            disabled = _run_system_command(["systemctl", "disable", unit], timeout=30)
            success = success and disabled.returncode == 0
            removed = _run_system_command(["rm", "-f", unit_path])
            success = success and removed.returncode == 0

        for unit in units:
            dropin = os.path.join("/etc/systemd/system", unit + ".d")
            if os.path.isdir(dropin):
                changed = True
                removed = _run_system_command(["rm", "-rf", dropin])
                success = success and removed.returncode == 0
        if changed:
            try:
                refreshed = subprocess.run(["systemctl", "daemon-reload"], capture_output=True, timeout=20)
                success = success and refreshed.returncode == 0
            except Exception:
                success = False
        return success

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
    for f in [
        "launch_cockpit.pyw", "start_sentinel_bg.bat", "start_sentinel_silent.vbs",
        "Sentinel.ico", "sentinel_backend.log",
    ]:
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
    cleanup_ok = True
    print(f"\n{Colors.BOLD}{Colors.RED}╭── DESINSTALACIÓN COMPLETA DE SENTINEL OS ─────────────────────────╮{Colors.RESET}")
    
    # 1. Terminar procesos
    print_info("1/6 Deteniendo únicamente los procesos de esta instalación..." if lang == "es" else "1/6 Stopping processes owned by this installation...")
    processes = kill_sentinel_processes(root_dir)
    time.sleep(0.5)
    if processes["failed"]:
        cleanup_ok = False
        print_warning(f"No se pudieron detener estos PIDs de SentinelOS: {', '.join(map(str, processes['failed']))}")

    # 2. Deshabilitar autostart y servicios
    print_info("2/6 Eliminando servicios y tareas de autoinicio..." if lang == "es" else "2/6 Removing services and autostart tasks...")
    if not remove_autostart_and_services(root_dir):
        cleanup_ok = False
        print_warning("No se pudieron quitar todas las tareas o servicios de autoinicio.")

    # 3. Remover reglas de firewall
    print_info("3/6 Restaurando configuración de cortafuegos..." if lang == "es" else "3/6 Restoring firewall rules...")
    if not remove_firewall_rule(os_info, 8001, lang, root_dir=root_dir):
        cleanup_ok = False
        print_warning("No se pudieron verificar todas las reglas de firewall de SentinelOS.")

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

    if cleanup_ok:
        print_success("SentinelOS ha sido desinstalado del sistema limpia y completamente." if lang == "es" else "SentinelOS has been cleanly and completely uninstalled.")
    else:
        print_warning("La limpieza terminó parcialmente. Repite la desinstalación con permisos de administrador y revisa las advertencias." if lang == "es" else "Cleanup was partial. Rerun uninstall as administrator and review the warnings.")
    print(f"{Colors.BOLD}{Colors.RED}╰──────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")
    return cleanup_ok
