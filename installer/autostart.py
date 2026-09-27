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
        print_info("Habilitando servicios en systemd para inicio automático..." if lang == "es" else "Enabling systemd autostart...")
        cmds = [
            "systemctl daemon-reload",
            "systemctl enable labsentinel.service 2>/dev/null || true",
            "systemctl enable sentinel.service 2>/dev/null || true",
            "systemctl enable sentinel-orchestrator.service 2>/dev/null || true"
        ]
        for c in cmds:
            subprocess.run(c, shell=True, capture_output=True)
        print_success("Inicio automático configurado en systemd." if lang == "es" else "Systemd autostart enabled.")
        return True

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

            # 1. Intentar Task Scheduler (ONLOGON)
            task_cmd = f'schtasks /Create /TN "SentinelOS_Service" /TR "\"{start_bat}\"" /SC ONLOGON /F'
            res = subprocess.run(task_cmd, shell=True, capture_output=True)
            if res.returncode == 0:
                print_success("Tarea de inicio programada en Windows Task Scheduler (ONLOGON)." if lang == "es" else "Autostart scheduled in Windows Task Scheduler.")
                return True

            # 2. Fallback: Carpeta de Inicio de Windows (Startup folder de usuario sin requerir privilegios Admin)
            appdata = os.environ.get("APPDATA")
            if appdata:
                startup_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
                if os.path.exists(startup_dir):
                    startup_bat = os.path.join(startup_dir, "SentinelOS_AutoStart.cmd")
                    with open(startup_bat, "w", encoding="utf-8") as f:
                        f.write(f'call "{start_bat}"\n')
                    print_success("Servicio registrado en la Carpeta de Inicio de Windows." if lang == "es" else "Service registered in Windows Startup folder.")
                    return True

            return False
        except Exception as e:
            print_warning(f"Aviso al configurar autoinicio: {e}")
            return False

    return False
