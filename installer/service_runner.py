#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Lanzador y Verificador de Salud de Servicios en Vivo (v2.0)
Inicia los servicios en Docker o como daemon nativo ultra-rápido, captura logs para auto-diagnóstico
y no concluye hasta validar con peticiones HTTP reales que el servidor responde con HTTP 200.
"""
import os, sys, time, json, subprocess, shutil, urllib.request
from .banner import Colors, print_info, print_success, print_warning, print_error, print_step
from .port_guard import check_and_resolve_port
from .service_config import get_service_port, set_service_port

def start_and_verify_services(os_info: dict, root_dir: str, lang="es", port: int | None = None) -> tuple[bool, str]:
    print_step("Desplegando y verificando servicios de SentinelOS..." if lang == "es" else "Deploying and verifying SentinelOS services...")
    
    # 0. Verificación preventiva de puertos (Port Conflict Guard)
    port = port or get_service_port(root_dir)
    target_port, _ = check_and_resolve_port(port=port, lang=lang, root_dir=root_dir)
    set_service_port(root_dir, target_port)

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
            unit_path = "/etc/systemd/system/labsentinel.service" if os.path.exists("/etc/systemd/system/labsentinel.service") else "/lib/systemd/system/labsentinel.service"
            try:
                with open(unit_path, "r", encoding="utf-8") as unit_file:
                    unit_matches_port = f"--port {target_port}" in unit_file.read()
            except OSError:
                unit_matches_port = False

            if unit_matches_port:
                print_info("Iniciando servicios con systemd en Linux...")
                subprocess.run(["systemctl", "daemon-reload"], capture_output=True)
                res = subprocess.run(["systemctl", "restart", "labsentinel.service"], capture_output=True)
                if res.returncode != 0:
                    subprocess.run(["sudo", "-n", "systemctl", "restart", "labsentinel.service"], capture_output=True)

                time.sleep(1)
                chk = subprocess.run(["systemctl", "is-active", "labsentinel.service"], capture_output=True, text=True)
                if "active" in chk.stdout:
                    started_via_systemd = True
                    print_success("Servicio systemd labsentinel.service activo.")
            else:
                print_warning("El servicio systemd tiene otro puerto configurado; se iniciará SentinelOS con el puerto seleccionado.")

        if not started_via_systemd:
            # En Windows o sin systemd activo: arrancar uvicorn como daemon en segundo plano
            print_info(f"Iniciando backend uvicorn en puerto {target_port} en segundo plano..." if lang == "es" else f"Starting uvicorn backend on port {target_port} in background...")
            
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
                    [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(target_port)],
                    cwd=backend_dir,
                    stdout=log_out,
                    stderr=log_out,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                )
            else:
                proc = subprocess.Popen(
                    [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(target_port)],
                    cwd=backend_dir,
                    stdout=log_out,
                    stderr=log_out,
                    start_new_session=True
                )

    # 2. Verificar el backend y la API de telemetría por separado.
    print_info(f"Esperando respuesta del servidor en http://127.0.0.1:{target_port}..." if lang == "es" else f"Waiting for server response on http://127.0.0.1:{target_port}...")
    
    server_healthy = False
    start_time = time.time()
    last_error = "La API no respondió con datos de telemetría."
    telemetry_attempts = 0
    
    for attempt in range(1, 31):
        if proc is not None and proc.poll() is not None:
            print_error(f"El backend uvicorn terminó prematuramente con código {proc.poll()}.")
            break
        try:
            health_req = urllib.request.Request(f"http://127.0.0.1:{target_port}/api/health", headers={"User-Agent": "SentinelInstaller"})
            with urllib.request.urlopen(health_req, timeout=2) as health_resp:
                if health_resp.status != 200:
                    raise RuntimeError(f"/api/health respondió HTTP {health_resp.status}")
        except Exception as exc:
            last_error = f"Backend sin respuesta saludable: {exc}"
            print(f" {Colors.DIM}.{Colors.RESET}", end="", flush=True)
            time.sleep(1)
            continue

        telemetry_attempts += 1
        try:
            data_req = urllib.request.Request(f"http://127.0.0.1:{target_port}/api/data", headers={"User-Agent": "SentinelInstaller"})
            with urllib.request.urlopen(data_req, timeout=30) as data_resp:
                if data_resp.status != 200:
                    raise RuntimeError(f"/api/data respondió HTTP {data_resp.status}")
                payload = json.loads(data_resp.read().decode("utf-8"))
                if not isinstance(payload, dict) or not isinstance(payload.get("system"), dict):
                    raise RuntimeError("/api/data respondió, pero el JSON de telemetría no tiene el formato esperado")
                latency = round((time.time() - start_time) * 1000)
                server_healthy = True
                print_success(f"Backend y telemetría activos (HTTP 200) en http://127.0.0.1:{target_port} (Latencia: {latency} ms)")
                break
        except Exception as exc:
            last_error = f"El backend respondió a /api/health, pero /api/data falló: {exc}"
            if telemetry_attempts >= 3:
                break
            print(f" {Colors.DIM}.{Colors.RESET}", end="", flush=True)
            time.sleep(2)

    print()
    if not server_healthy:
        print_error(f"No se pudo validar la API de telemetría: {last_error}" if lang == "es" else f"Telemetry API validation failed: {last_error}")
        if os.path.exists(log_file_path):
            print_warning("Últimas líneas del registro del servidor (sentinel_backend.log):")
            try:
                with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()[-12:]
                    for l in lines:
                        print(f"  {Colors.DIM}{l.rstrip()}{Colors.RESET}")
            except Exception:
                pass
        return False, f"http://127.0.0.1:{target_port}"

    return True, f"http://127.0.0.1:{target_port}"
