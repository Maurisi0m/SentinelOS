#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Guardián Preventivo de Conflictos de Puerto (Port Conflict Guard) v2.0
Detecta antes del arranque si el puerto (por defecto 8001) está ocupado, identifica el proceso en conflicto
y ofrece terminarlo automáticamente o conmutar al siguiente puerto libre.
"""
import os, sys, time, socket, subprocess, urllib.request, json
from .banner import Colors, print_success, print_warning, print_info, print_error, print_panel, print_menu_item, print_prompt
from .service_config import DEFAULT_HTTP_PORT, ALTERNATE_HTTP_PORT


def alternate_service_port(port: int) -> int | None:
    if port == DEFAULT_HTTP_PORT:
        return ALTERNATE_HTTP_PORT
    if port == ALTERNATE_HTTP_PORT:
        return DEFAULT_HTTP_PORT
    return None

def is_port_in_use(port: int) -> bool:
    """Verifica si un puerto TCP está ocupado intentando enlazar un socket temporal."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", port))
        s.close()
        return False
    except OSError:
        return True


def sentinel_install_roots_on_port(port: int) -> set[str]:
    """Return install roots for Sentinel uvicorn processes listening on a port."""
    roots = set()
    loopback_roots = set()
    try:
        import psutil
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.status in (psutil.CONN_LISTEN, "LISTEN") and conn.pid:
                try:
                    proc = psutil.Process(conn.pid)
                    command_line = " ".join(proc.cmdline()).lower()
                    if "uvicorn" not in command_line or "main:app" not in command_line:
                        continue
                    cwd = proc.cwd()
                    if os.path.basename(cwd).lower() == "labsentinel_backend":
                        root = os.path.normcase(os.path.realpath(os.path.dirname(cwd)))
                        roots.add(root)
                        if conn.laddr.ip == "127.0.0.1":
                            loopback_roots.add(root)
                except (psutil.Error, OSError):
                    continue
    except Exception:
        pass
    return loopback_roots or roots


def is_sentinel_install_on_port(port: int, root_dir: str) -> bool | None:
    roots = sentinel_install_roots_on_port(port)
    if not roots:
        return None
    target_root = os.path.normcase(os.path.realpath(root_dir))
    return target_root in roots

def is_sentinel_on_port(port: int, root_dir: str = None) -> tuple[bool, dict]:
    """Comprueba si el servicio que responde en el puerto ya es una instancia activa de SentinelOS."""
    try:
        url = f"http://127.0.0.1:{port}/api/node/token"
        req = urllib.request.Request(url, headers={"User-Agent": "SentinelPortGuard"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ok" and "token" in data:
                    if root_dir:
                        auth_path = os.path.join(root_dir, "config", "node_auth.json")
                        try:
                            with open(auth_path, "r", encoding="utf-8") as auth_file:
                                local_token = json.load(auth_file).get("token")
                            if local_token and data.get("token") != local_token:
                                return False, {"foreign_sentinel_root": True}
                        except (OSError, ValueError, TypeError):
                            pass
                        belongs_to_install = is_sentinel_install_on_port(port, root_dir)
                        if belongs_to_install is False:
                            return False, {"foreign_sentinel_root": True}
                    return True, data
    except Exception:
        pass
    return False, {}

def get_process_on_port(port: int) -> tuple[int, str]:
    """Identifica el PID y el nombre del ejecutable que tiene ocupado el puerto."""
    # 1. Intentar mediante psutil si está disponible
    try:
        import psutil
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status in (psutil.CONN_LISTEN, 'LISTEN'):
                pid = conn.pid
                if pid:
                    p = psutil.Process(pid)
                    return pid, p.name()
    except Exception:
        pass

    # 2. Fallback nativo en Windows mediante netstat y tasklist
    if sys.platform == "win32":
        try:
            res = subprocess.run(f"netstat -ano | findstr :{port}", shell=True, capture_output=True, text=True)
            for line in res.stdout.strip().splitlines():
                if "LISTENING" in line:
                    parts = line.strip().split()
                    pid = int(parts[-1])
                    # Obtener nombre del proceso
                    t_res = subprocess.run(f'tasklist /FI "PID eq {pid}" /FO CSV /NH', shell=True, capture_output=True, text=True)
                    proc_name = "proceso"
                    if t_res.stdout:
                        fields = t_res.stdout.strip().replace('"', '').split(',')
                        if fields:
                            proc_name = fields[0]
                    return pid, proc_name
        except Exception:
            pass

    # 3. Fallback nativo en Linux mediante lsof o ss
    elif sys.platform.startswith("linux"):
        try:
            res = subprocess.run(f"lsof -i :{port} -t", shell=True, capture_output=True, text=True)
            if res.stdout.strip():
                pid = int(res.stdout.strip().split()[0])
                p_res = subprocess.run(f"ps -p {pid} -o comm=", shell=True, capture_output=True, text=True)
                return pid, p_res.stdout.strip() or "proceso"
        except Exception:
            pass

    return 0, "proceso desconocido"

def kill_process_by_pid(pid: int) -> bool:
    """Termina de forma forzada un proceso que ocupa el puerto."""
    if pid <= 0:
        return False
    try:
        import psutil
        p = psutil.Process(pid)
        p.kill()
        p.wait(timeout=3)
        return True
    except Exception:
        pass

    if sys.platform == "win32":
        res = subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
        return res.returncode == 0
    else:
        res = subprocess.run(f"kill -9 {pid} 2>/dev/null", shell=True, capture_output=True)
        return res.returncode == 0

def check_and_resolve_port(port: int = 8001, lang: str = "es", auto_resolve: bool = False, root_dir: str = None) -> tuple[int, bool]:
    """
    Evalúa el estado del puerto antes de iniciar.
    Si está libre: retorna (port, True).
    Si ya es SentinelOS activo: retorna (port, True) informando que ya corre.
    Si está ocupado por otro proceso: pregunta al usuario para liberarlo o usar el otro puerto SentinelOS.
    """
    if not is_port_in_use(port):
        return port, True

    # Comprobar si ya es SentinelOS respondiendo
    is_sentinel, s_data = is_sentinel_on_port(port, root_dir=root_dir)
    if is_sentinel:
        node_name = s_data.get("node_name", "Local")
        msg = f"SentinelOS ya está activo en http://127.0.0.1:{port} (Nodo: {node_name})." if lang == "es" else f"SentinelOS is already running on http://127.0.0.1:{port} (Node: {node_name})."
        print_info(msg)
        return port, True

    # Conflicto con otro proceso
    pid, proc_name = get_process_on_port(port)
    alt_port = alternate_service_port(port)
    if s_data.get("foreign_sentinel_root") and alt_port is not None and not is_port_in_use(alt_port):
        print_warning(f"El puerto {port} pertenece a otra copia de SentinelOS. Se usará el puerto {alt_port} para esta instalación.")
        return alt_port, True
    if alt_port is not None and is_port_in_use(alt_port):
        alt_sentinel, _ = is_sentinel_on_port(alt_port, root_dir=root_dir)
        if alt_sentinel:
            return alt_port, True
        alt_port = None

    print(f"\n{Colors.BOLD}{Colors.YELLOW}╭── ⚠️  CONFLICTO PREVENTIVO DE PUERTO DETECTADO ─────────────────────╮{Colors.RESET}")
    print(f"  {Colors.BOLD}● Puerto:{Colors.RESET}             {port} (TCP)")
    print(f"  {Colors.BOLD}⚠️  Ocupado por:{Colors.RESET}       {proc_name} {Colors.DIM}(PID: {pid}){Colors.RESET}")
    print(f"  {Colors.BOLD}ℹ️  Diagnóstico:{Colors.RESET}        El puerto requerido para el Cockpit está bloqueado.")
    print(f"{Colors.BOLD}{Colors.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")

    if auto_resolve:
        print_info(f"Auto-resolución activada: Liberando puerto {port} terminando PID {pid}...")
        if kill_process_by_pid(pid):
            time.sleep(1)
            if not is_port_in_use(port):
                print_success(f"Puerto {port} liberado exitosamente.")
                return port, True
        if alt_port is not None and not is_port_in_use(alt_port):
            return alt_port, True
        print_error("No hay un puerto SentinelOS alternativo disponible.")
        sys.exit(1)

    print(f"  {Colors.BOLD}¿Cómo deseas resolver este conflicto?{Colors.RESET}\n")
    print_menu_item("1", f"Liberar puerto {port} automáticamente", f"Termina el proceso {proc_name} (PID: {pid}) para despejar el puerto", "Recomendado", Colors.GREEN)
    if alt_port is not None:
        print_menu_item("2", f"Conmutar a puerto alternativo ({alt_port})", f"Ejecutar SentinelOS en http://127.0.0.1:{alt_port} sin afectar el otro programa", "Alternativo", Colors.CYAN)
    print_menu_item("0", "Cancelar", "Detener el instalador para revisar manualmente", "", Colors.DIM)

    choice = print_prompt("Selecciona una opción", "1")

    if choice in ("", "1"):
        print_info(f"Liberando puerto {port} terminando PID {pid}...")
        if kill_process_by_pid(pid):
            time.sleep(1.5)
            if not is_port_in_use(port):
                print_success(f"Puerto {port} liberado exitosamente.")
                return port, True
            else:
                if alt_port is not None and not is_port_in_use(alt_port):
                    print_warning(f"El puerto {port} sigue ocupado. Conmutando a {alt_port}...")
                    return alt_port, True
                print_error("No hay un puerto SentinelOS alternativo disponible.")
                sys.exit(1)
        else:
            if alt_port is not None and not is_port_in_use(alt_port):
                print_warning(f"No se pudo terminar el PID {pid}. Conmutando a {alt_port}...")
                return alt_port, True
            print_error("No hay un puerto SentinelOS alternativo disponible.")
            sys.exit(1)

    elif choice == "2":
        if alt_port is None or is_port_in_use(alt_port):
            print_error(f"El puerto alternativo {alt_port} no está disponible.")
            sys.exit(1)
        print_success(f"Puerto establecido a: {alt_port}")
        return alt_port, True

    else:
        print("\nInstalación cancelada por conflicto de puerto.\n")
        sys.exit(0)
