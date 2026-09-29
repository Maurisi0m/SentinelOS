#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Configurador de Autoinicio al Encender el Servidor / Equipo (v2.0)
Soporta Systemd en Linux y Task Scheduler + Shell Startup en Windows para inicio desatendido.
"""
import os, sys, subprocess, shutil
from .banner import print_success, print_warning, print_info

def configure_autostart(os_info: dict, root_dir: str, lang="es") -> bool:
    system = os_info["system"]
    
    if system == "Linux":
        print_info("Configurando servicios en systemd para inicio automático..." if lang == "es" else "Configuring systemd service for autostart...")
        import getpass
        current_user = getpass.getuser()
        backend_dir = os.path.abspath(os.path.join(root_dir, "labsentinel_backend"))
        venv_py = os.path.abspath(os.path.join(root_dir, ".venv", "bin", "python3"))
        if not os.path.exists(venv_py):
            venv_py = os.path.abspath(os.path.join(root_dir, ".venv", "bin", "python"))
        py_bin = venv_py if os.path.exists(venv_py) else sys.executable
        
        service_content = f"""[Unit]
Description=Lab Sentinel OS Backend
After=network.target

[Service]
User={current_user}
WorkingDirectory={backend_dir}
ExecStart={py_bin} -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=labsentinel

[Install]
WantedBy=multi-user.target
"""
        service_target = "/etc/systemd/system/labsentinel.service"
        temp_service = "/tmp/labsentinel.service"
        try:
            with open(temp_service, "w", encoding="utf-8") as f:
                f.write(service_content)
        except Exception:
            pass

        installed = False
        try:
            with open(service_target, "w", encoding="utf-8") as f:
                f.write(service_content)
            installed = True
        except PermissionError:
            res = subprocess.run(["sudo", "-n", "cp", temp_service, service_target], capture_output=True)
            if res.returncode == 0:
                subprocess.run(["sudo", "-n", "chmod", "644", service_target], capture_output=True)
                installed = True
            else:
                res2 = subprocess.run(f"sudo cp {temp_service} {service_target} && sudo chmod 644 {service_target}", shell=True)
                installed = (res2.returncode == 0)

        cmds = [
            "systemctl daemon-reload 2>/dev/null || sudo systemctl daemon-reload 2>/dev/null || true",
            "systemctl enable labsentinel.service 2>/dev/null || sudo systemctl enable labsentinel.service 2>/dev/null || true"
        ]
        for c in cmds:
            subprocess.run(c, shell=True, capture_output=True)

        if installed or os.path.exists(service_target):
            print_success("Inicio automático configurado en systemd (labsentinel.service)." if lang == "es" else "Systemd autostart enabled (labsentinel.service).")
            return True
        else:
            print_warning("Aviso: No se pudo registrar en /etc/systemd/system/. El sistema iniciará en modo daemon." if lang == "es" else "Notice: Could not register in /etc/systemd/system/. System will run in daemon mode.")
            return False

    elif system == "Windows":
        print_info("Registrando servicio de inicio automático en Windows..." if lang == "es" else "Configuring Windows Startup...")
        try:
            start_bat = os.path.join(root_dir, "start_sentinel_bg.bat")
            py_exe = sys.executable
            backend_dir = os.path.join(root_dir, "labsentinel_backend")
            with open(start_bat, "w", encoding="utf-8") as f:
                f.write('@echo off\n')
                f.write(f'cd /d "{backend_dir}"\n')
                f.write(f'start "" /b "{py_exe}" -m uvicorn main:app --host 0.0.0.0 --port 8001\n')
                f.write('timeout /t 3 /nobreak >nul\n')
                f.write('start "" http://localhost:8001\n')

            # 1. Intentar Task Scheduler (ONLOGON)
            task_cmd = f'schtasks /Create /TN "SentinelOS_Service" /TR "\"{start_bat}\"" /SC ONLOGON /F'
            res = subprocess.run(task_cmd, shell=True, capture_output=True)
            if res.returncode == 0:
                print_success("Tarea de inicio programada en Windows Task Scheduler (ONLOGON con apertura de navegador)." if lang == "es" else "Autostart scheduled in Windows Task Scheduler with browser launch.")
                return True

            # 2. Fallback: Carpeta de Inicio de Windows (Startup folder de usuario sin requerir privilegios Admin)
            appdata = os.environ.get("APPDATA")
            if appdata:
                startup_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
                if os.path.exists(startup_dir):
                    startup_bat = os.path.join(startup_dir, "SentinelOS_AutoStart.cmd")
                    with open(startup_bat, "w", encoding="utf-8") as f:
                        f.write(f'call "{start_bat}"\n')
                    print_success("Servicio y navegador registrados en la Carpeta de Inicio de Windows." if lang == "es" else "Service and browser registered in Windows Startup folder.")
                    return True

            return False
        except Exception as e:
            print_warning(f"Aviso al configurar autoinicio: {e}")
            return False

    return False

def disable_autostart(os_info: dict, root_dir: str):
    """Limpia tareas programadas si el usuario decidió no habilitar el autoinicio."""
    system = os_info["system"]
    if system == "Windows":
        try:
            subprocess.run('schtasks /Delete /TN "SentinelOS_Service" /F', shell=True, capture_output=True)
            appdata = os.environ.get("APPDATA")
            if appdata:
                startup_bat = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup\SentinelOS_AutoStart.cmd")
                if os.path.exists(startup_bat):
                    os.remove(startup_bat)
            start_bat = os.path.join(root_dir, "start_sentinel_bg.bat")
            if os.path.exists(start_bat):
                os.remove(start_bat)
        except Exception:
            pass
    elif system == "Linux":
        try:
            subprocess.run("systemctl disable labsentinel.service 2>/dev/null || true", shell=True, capture_output=True)
        except Exception:
            pass
