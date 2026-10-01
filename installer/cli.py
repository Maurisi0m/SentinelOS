#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - CLI Manager (Comandos de Terminal del Sistema) v2.5
Proporciona comandos de terminal intuitivos y universales disponibles en el PATH:
- sentinel active   (o sentinel start)  : Inicializa el sistema y servicio en segundo plano
- sentinel stop                         : Detiene el sistema y libera el puerto 8001
- sentinel restart                      : Reinicia el servicio
- sentinel status                       : Muestra el estado operativo, IPs y recursos
- sentinel logs                         : Visualiza los logs en tiempo real
- sentinel open                         : Abre el panel de control en el navegador
- sentinel hotspot                      : Inicia red Wi-Fi hotspot de emergencia sin router
- sentinel uninstall                    : Desinstala completamente SentinelOS
"""

import os
import sys
import time
import json
import socket
import shutil
import urllib.request
import subprocess
from .banner import Colors, print_success, print_warning, print_info, print_error
from .port_guard import get_process_on_port
from .uninstaller import kill_sentinel_processes, run_full_uninstall

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "labsentinel_backend")
LOG_FILE = os.path.join(ROOT_DIR, "sentinel_backend.log")

def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def is_backend_healthy() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:8001/api/health", headers={"User-Agent": "SentinelCLI"})
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False

def cmd_active():
    """Inicializa el sistema SentinelOS en segundo plano y verifica su funcionamiento."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}╭── INICIALIZANDO SENTINEL OS (MODO OPERATIVO) ───────────────────────╮{Colors.RESET}")
    pid, _ = get_process_on_port(8001)
    if pid > 0 and is_backend_healthy():
        print_success(f"SentinelOS ya está activo y operando en segundo plano (PID: {pid}).")
    else:
        print_info("Iniciando servicio de SentinelOS en segundo plano (Puerto 8001)...")
        if sys.platform == "win32":
            venv_pyw = os.path.join(ROOT_DIR, ".venv", "Scripts", "pythonw.exe")
            venv_py = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
            sys_pyw = sys.executable.replace("python.exe", "pythonw.exe")
            py_bin = venv_pyw if os.path.exists(venv_pyw) else (venv_py if os.path.exists(venv_py) else sys_pyw)

            log_out = open(LOG_FILE, "a", encoding="utf-8")
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
            # En Linux: si existe systemd unit activa, usarla; si no, subproceso daemon
            unit_exists = os.path.exists("/etc/systemd/system/labsentinel.service")
            if unit_exists:
                subprocess.run(["systemctl", "start", "labsentinel.service"], capture_output=True)
            else:
                venv_py = os.path.join(ROOT_DIR, ".venv", "bin", "python3")
                py_bin = venv_py if os.path.exists(venv_py) else sys.executable
                log_out = open(LOG_FILE, "a", encoding="utf-8")
                subprocess.Popen(
                    [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
                    cwd=BACKEND_DIR,
                    stdout=log_out,
                    stderr=log_out,
                    start_new_session=True
                )

        print_info("Esperando confirmación de enlace de red local...")
        ready = False
        for _ in range(15):
            time.sleep(0.4)
            if is_backend_healthy():
                ready = True
                break

        if ready:
            print_success("¡Servicio SentinelOS inicializado y saludable!")
        else:
            print_warning("El servicio se inició, pero la respuesta de salud tardó más de lo previsto.")

    lan_ip = get_lan_ip()
    print(f"\n  {Colors.BOLD}🌐 Enlace Localhost:{Colors.RESET}       {Colors.CYAN}http://127.0.0.1:8001{Colors.RESET}")
    print(f"  {Colors.BOLD}📡 Enlace Red Local (LAN):{Colors.RESET} {Colors.GREEN}http://{lan_ip}:8001{Colors.RESET} (Sin requerir Internet)")
    
    # Token
    auth_file = os.path.join(ROOT_DIR, "config", "node_auth.json")
    if os.path.exists(auth_file):
        try:
            with open(auth_file, "r") as f:
                token = json.load(f).get("token")
                if token:
                    print(f"  {Colors.BOLD}🔑 Token de Vinculación:{Colors.RESET}   {Colors.YELLOW}{token}{Colors.RESET}")
        except Exception:
            pass

    print(f"{Colors.BOLD}{Colors.CYAN}╰─────────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")

def cmd_stop():
    """Detiene los procesos SentinelOS sin terminar aplicaciones ajenas por conflicto de puerto."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}Deteniendo los procesos de SentinelOS (puertos 8001/8002)...{Colors.RESET}")
    result = kill_sentinel_processes(ROOT_DIR)
    if result["failed"]:
        print_warning(f"No se pudieron detener estos PIDs de SentinelOS: {', '.join(map(str, result['failed']))}")
    if sys.platform != "win32":
        units = ["systemctl", "stop", "labsentinel.service", "sentinel.service", "sentinel-orchestrator.service"]
        stopped = subprocess.run(units, capture_output=True)
        if stopped.returncode and shutil.which("sudo"):
            subprocess.run(["sudo", "-n", *units], capture_output=True)
    time.sleep(0.5)
    occupied = {port: get_process_on_port(port)[0] for port in (8001, 8002)}
    occupied = {port: pid for port, pid in occupied.items() if pid > 0}
    if not occupied and not result["failed"]:
        print_success("SentinelOS detenido con éxito; no quedan procesos escuchando en 8001/8002.")
    else:
        details = ", ".join(f"{port} (PID {pid})" for port, pid in occupied.items())
        if details:
            print_warning(f"Quedan procesos en estos puertos; se dejaron intactos: {details}.")

def cmd_restart():
    """Reinicia el servicio de SentinelOS."""
    cmd_stop()
    time.sleep(1)
    cmd_active()

def cmd_status():
    """Muestra el estado en tiempo real del servicio y de la red."""
    pid, name = get_process_on_port(8001)
    healthy = is_backend_healthy()
    lan_ip = get_lan_ip()

    print(f"\n{Colors.BOLD}{Colors.CYAN}╭── ESTADO DEL SISTEMA SENTINEL OS ──────────────────────────────────╮{Colors.RESET}")
    if pid > 0 and healthy:
        print(f"  Estado:        {Colors.GREEN}● OPERATIVO Y SALUDABLE{Colors.RESET}")
        print(f"  PID:           {pid} ({name})")
        print(f"  Puerto:        8001 (Abierto)")
        print(f"  IP LAN:        http://{lan_ip}:8001")
        print(f"  Modo:          100% Autónomo (Funcional con o sin Internet)")
    elif pid > 0:
        print(f"  Estado:        {Colors.YELLOW}▲ PROCESO ACTIVO PERO RESPONDIENDO LENTO{Colors.RESET}")
        print(f"  PID:           {pid}")
    else:
        print(f"  Estado:        {Colors.RED}○ DETENIDO (APAGADO){Colors.RESET}")
        print(f"  Usa:           '{Colors.CYAN}sentinel active{Colors.RESET}' para encenderlo.")
    print(f"{Colors.BOLD}{Colors.CYAN}╰────────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")

def cmd_logs():
    """Muestra los logs en tiempo real."""
    if not os.path.exists(LOG_FILE):
        print_warning("No hay registros en el archivo de log aún.")
        return
    print(f"\n{Colors.BOLD}── Mostrando últimas líneas de: {LOG_FILE} ──{Colors.RESET}\n")
    try:
        if sys.platform == "win32":
            ps_cmd = f"Get-Content '{LOG_FILE}' -Tail 35 -Wait"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd])
        else:
            subprocess.run(["tail", "-n", "35", "-f", LOG_FILE])
    except KeyboardInterrupt:
        print("\nLectura de logs finalizada.")

def cmd_open():
    """Abre el panel en el navegador predeterminado."""
    if not is_backend_healthy():
        print_info("Iniciando servicio previamente...")
        cmd_active()
    import webbrowser
    webbrowser.open("http://127.0.0.1:8001")

def cmd_hotspot():
    """Crea un punto de acceso Wi-Fi local para conectar laptops/servidores sin router ni internet."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}╭── PUNTO DE ACCESO WI-FI SENTINEL OS (MODO SIN ROUTER) ─────────────╮{Colors.RESET}")
    print("  Activando Red Hotspot Wi-Fi para comunicación directa de nodos...")
    ssid = "SentinelOS-Mesh"
    password = "sentinelmesh2026"

    if sys.platform == "win32":
        try:
            subprocess.run(f'netsh wlan set hostednetwork mode=allow ssid={ssid} key={password}', shell=True, capture_output=True)
            res = subprocess.run('netsh wlan start hostednetwork', shell=True, capture_output=True, text=True)
            if "started" in res.stdout.lower() or "iniciado" in res.stdout.lower():
                print_success(f"Red Wi-Fi creada con éxito: SSID '{ssid}' | Clave: '{password}'")
            else:
                # Intentar método Mobile Hotspot vía PowerShell
                ps = """
                $connectionProfile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
                $tetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($connectionProfile)
                $tetheringManager.StartTetheringAsync()
                """
                subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
                print_info(f"Punto de acceso configurado. Conecta tus demás nodos a la red Wi-Fi de esta laptop.")
        except Exception as e:
            print_warning(f"Aviso Hotspot: {e}")
    else:
        # Linux (NetworkManager)
        try:
            cmd = f"nmcli dev wifi hotspot ssid '{ssid}' password '{password}'"
            subprocess.run(cmd, shell=True)
            print_success(f"Hotspot Wi-Fi Linux iniciado: SSID '{ssid}' | Clave: '{password}'")
        except Exception as e:
            print_warning(f"Aviso Hotspot: {e}")

    print(f"{Colors.BOLD}{Colors.CYAN}╰────────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")

def cmd_help():
    print(f"""
{Colors.BOLD}{Colors.CYAN}SENTINEL OS - Interfaz de Comandos de Terminal (CLI){Colors.RESET}

{Colors.BOLD}Comandos disponibles:{Colors.RESET}
  {Colors.GREEN}sentinel active{Colors.RESET}    Arranca SentinelOS en segundo plano y muestra enlaces LAN
  {Colors.GREEN}sentinel stop{Colors.RESET}      Detiene todos los procesos y libera el puerto 8001
  {Colors.GREEN}sentinel restart{Colors.RESET}   Reinicia el servicio de telemetría y API
  {Colors.GREEN}sentinel status{Colors.RESET}    Muestra estado del nodo, PID, memoria e IPs de red
  {Colors.GREEN}sentinel logs{Colors.RESET}      Sigue los registros de eventos y errores en vivo
  {Colors.GREEN}sentinel open{Colors.RESET}      Abre el panel de control en tu navegador
  {Colors.GREEN}sentinel hotspot{Colors.RESET}   Crea red Wi-Fi propia para operar sin router ni internet
  {Colors.GREEN}sentinel uninstall{Colors.RESET} Desinstala completamente SentinelOS del sistema
""")

def install_cli_to_path(root_dir: str):
    """Instala el comando 'sentinel' en el PATH del sistema (Windows y Linux)."""
    if sys.platform == "win32":
        # 1. Crear sentinel.cmd en %LOCALAPPDATA%\Microsoft\WindowsApps (siempre en PATH)
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            winapps = os.path.join(local_appdata, "Microsoft", "WindowsApps")
            if os.path.exists(winapps):
                cmd_path = os.path.join(winapps, "sentinel.cmd")
                bat_path = os.path.join(winapps, "sentinel.bat")
                py_exe = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
                if not os.path.exists(py_exe):
                    py_exe = sys.executable

                content = f'@echo off\r\n"{py_exe}" -m installer.cli %*\r\n'
                try:
                    with open(cmd_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    with open(bat_path, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception:
                    pass

        # 2. También registrar la carpeta bin en el registro de Windows HKCU\Environment\Path
        bin_dir = os.path.join(root_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        bin_cmd = os.path.join(bin_dir, "sentinel.cmd")
        py_exe = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
        if not os.path.exists(py_exe):
            py_exe = sys.executable
        with open(bin_cmd, "w", encoding="utf-8") as f:
            f.write(f'@echo off\r\n"{py_exe}" -m installer.cli %*\r\n')

        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
            cur_path, _ = winreg.QueryValueEx(key, "Path")
            if bin_dir.lower() not in cur_path.lower():
                new_path = cur_path + ";" + bin_dir
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
        except Exception:
            pass

    else:
        # Linux (Ubuntu, Mint, Debian)
        script_content = f"""#!/bin/sh
VENV_PY="{root_dir}/.venv/bin/python3"
if [ -f "$VENV_PY" ]; then
    PY_BIN="$VENV_PY"
else
    PY_BIN="$(command -v python3)"
fi
exec "$PY_BIN" -m installer.cli "$@"
"""
        # Intentar /usr/local/bin (si es root) o ~/.local/bin
        installed = False
        if os.geteuid() == 0 or os.access("/usr/local/bin", os.W_OK):
            target = "/usr/local/bin/sentinel"
            try:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(script_content)
                os.chmod(target, 0o755)
                installed = True
            except Exception:
                pass

        if not installed:
            user_bin = os.path.expanduser("~/.local/bin")
            os.makedirs(user_bin, exist_ok=True)
            target = os.path.join(user_bin, "sentinel")
            try:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(script_content)
                os.chmod(target, 0o755)
            except Exception:
                pass

def main():
    if len(sys.argv) < 2:
        cmd_help()
        return

    sub = sys.argv[1].lower().strip()
    if sub in ["active", "start", "on", "up"]:
        cmd_active()
    elif sub in ["stop", "down", "off", "kill"]:
        cmd_stop()
    elif sub in ["restart", "reload"]:
        cmd_restart()
    elif sub in ["status", "ps", "info"]:
        cmd_status()
    elif sub in ["logs", "log"]:
        cmd_logs()
    elif sub in ["open", "web", "cockpit"]:
        cmd_open()
    elif sub in ["hotspot", "wifi"]:
        cmd_hotspot()
    elif sub in ["uninstall", "remove", "purge"]:
        from .system_detector import detect_operating_system
        os_info = detect_operating_system()
        run_full_uninstall(os_info, ROOT_DIR, lang="es", purge_venv=True)
    else:
        cmd_help()

if __name__ == "__main__":
    main()
