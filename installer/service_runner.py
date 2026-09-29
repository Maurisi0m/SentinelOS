#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Lanzador y Verificador de Salud de Servicios en Vivo (v2.0)
Inicia los servicios en Docker o como daemon nativo ultra-rápido, captura logs para auto-diagnóstico
y no concluye hasta validar con peticiones HTTP reales que el servidor responde con HTTP 200.
"""
import os, sys, time, subprocess, shutil, urllib.request
from .banner import Colors, print_info, print_success, print_warning, print_error, print_step

def start_and_verify_services(os_info: dict, root_dir: str, lang="es") -> tuple[bool, str]:
    print_step("Desplegando y verificando servicios de SentinelOS..." if lang == "es" else "Deploying and verifying SentinelOS services...")
    
    log_file_path = os.path.join(root_dir, "sentinel_backend.log")
    backend_dir = os.path.join(root_dir, "labsentinel_backend")
    proc = None
    system = os_info.get("system", "Linux")
    
    # 1. Determinar modo de ejecución: Docker solo si se especificó explícitamente --docker
    use_docker = "--docker" in sys.argv
    if use_docker:
        docker_bin = shutil.which("docker")
        if docker_bin:
            print_info("Iniciando microservicios de laboratorio con Docker Compose...")
            subprocess.run(["docker", "compose", "up", "-d"], cwd=root_dir)
        else:
            print_warning("Docker no encontrado. Conmutando a modo nativo autónomo...")
            use_docker = False

    if not use_docker:
        # Modo Nativo Autónomo
        started_via_systemd = False
        
        # En Linux, verificar e iniciar servicio systemd si está disponible
        if system == "Linux" and (os.path.exists("/etc/systemd/system/labsentinel.service") or os.path.exists("/lib/systemd/system/labsentinel.service")):
            print_info("Iniciando servicios con systemd en Linux...")
            # Intentar reload y restart
            subprocess.run(["systemctl", "daemon-reload"], capture_output=True)
            res = subprocess.run(["systemctl", "restart", "labsentinel.service"], capture_output=True)
            if res.returncode != 0:
                subprocess.run(["sudo", "-n", "systemctl", "restart", "labsentinel.service"], capture_output=True)

            time.sleep(1)
            chk = subprocess.run(["systemctl", "is-active", "labsentinel.service"], capture_output=True, text=True)
            if "active" in chk.stdout:
                started_via_systemd = True
                print_success("Servicio systemd labsentinel.service activo.")

        if not started_via_systemd:
            # En Windows o sin systemd activo: arrancar uvicorn como daemon en segundo plano
            print_info("Iniciando backend uvicorn como proceso en segundo plano..." if lang == "es" else "Starting uvicorn backend as a background process...")
            
            # Priorizar siempre el intérprete del entorno virtual aislado si existe
            if sys.platform == "win32":
                venv_py = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
            else:
                venv_py = os.path.join(root_dir, ".venv", "bin", "python3")
                if not os.path.exists(venv_py):
                    venv_py = os.path.join(root_dir, ".venv", "bin", "python")
            py_bin = venv_py if os.path.exists(venv_py) else sys.executable

            log_out = open(log_file_path, "a", encoding="utf-8")
            if system == "Windows":
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                proc = subprocess.Popen(
                    [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
                    cwd=backend_dir,
                    stdout=log_out,
                    stderr=log_out,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    close_fds=True
                )
            else:
                proc = subprocess.Popen(
                    [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
                    cwd=backend_dir,
                    stdout=log_out,
                    stderr=log_out,
                    start_new_session=True
                )

    # 2. Batería de verificación HTTP en vivo (Polling con timeout de 20 segundos)
    print_info("Esperando respuesta del servidor en http://127.0.0.1:8001..." if lang == "es" else "Waiting for server response on http://127.0.0.1:8001...")
    
    server_healthy = False
    start_time = time.time()
    
    for attempt in range(1, 25):
        time.sleep(1)
        if proc is not None and proc.poll() is not None:
            print_error(f"El backend uvicorn terminó prematuramente con código {proc.poll()}.")
            break
        try:
            req = urllib.request.Request("http://127.0.0.1:8001/api/data", headers={"User-Agent": "SentinelInstaller"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    latency = round((time.time() - start_time) * 1000)
                    server_healthy = True
                    print_success(f"Servidor y API de telemetría activos (HTTP 200) en http://127.0.0.1:8001 (Latencia: {latency} ms)")
                    break
        except Exception:
            # Reintentar probando la ruta raíz
            try:
                req_root = urllib.request.Request("http://127.0.0.1:8001/", headers={"User-Agent": "SentinelInstaller"})
                with urllib.request.urlopen(req_root, timeout=2) as resp_root:
                    if resp_root.status == 200:
                        latency = round((time.time() - start_time) * 1000)
                        server_healthy = True
                        print_success(f"Servidor web activo en http://127.0.0.1:8001 (Latencia: {latency} ms)")
                        break
            except Exception:
                pass
            print(f" {Colors.DIM}.{Colors.RESET}", end="", flush=True)

    print()
    if not server_healthy:
        print_error("El servidor tardó más de lo esperado en responder." if lang == "es" else "Server took longer than expected to respond.")
        if os.path.exists(log_file_path):
            print_warning("Últimas líneas del registro del servidor (sentinel_backend.log):")
            try:
                with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()[-12:]
                    for l in lines:
                        print(f"  {Colors.DIM}{l.rstrip()}{Colors.RESET}")
            except Exception:
                pass
        return False, "http://127.0.0.1:8001"

    return True, "http://127.0.0.1:8001"
