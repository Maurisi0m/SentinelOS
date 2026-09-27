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
    
    # 1. Intentar Docker si el daemon está vivo
    docker_bin = shutil.which("docker")
    docker_running = False
    if docker_bin:
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            docker_running = (res.returncode == 0)
        except Exception:
            docker_running = False

    if docker_running:
        print_info("Iniciando microservicios de laboratorio con Docker Compose...")
        subprocess.run(["docker", "compose", "up", "-d"], cwd=root_dir)
    else:
        # Modo Nativo Autónomo
        system = os_info["system"]
        if system == "Linux" and os.path.exists("/etc/systemd/system/labsentinel.service"):
            print_info("Iniciando servicios con systemd en Linux...")
            subprocess.run(["systemctl", "restart", "labsentinel.service"])
        else:
            # En Windows o sin systemd: arrancar uvicorn en segundo plano con logging
            print_info("Iniciando backend uvicorn como proceso en segundo plano..." if lang == "es" else "Starting uvicorn backend as a background process...")
            py_bin = sys.executable

            log_out = open(log_file_path, "a", encoding="utf-8")
            if system == "Windows":
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                subprocess.Popen(
                    [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
                    cwd=backend_dir,
                    stdout=log_out,
                    stderr=log_out,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    close_fds=True
                )
            else:
                subprocess.Popen(
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
