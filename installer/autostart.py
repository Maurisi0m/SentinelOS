#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Configurador de Autoinicio al Encender el Servidor / Equipo (v2.0)
Soporta Systemd en Linux y Task Scheduler + Shell Startup en Windows para inicio desatendido.
"""
import os, sys, subprocess, shutil
from .banner import print_success, print_warning, print_info
from .service_config import get_node_role, get_service_port, set_node_role


def configure_autostart(os_info: dict, root_dir: str, lang="es", port: int | None = None, node_role: str | None = None) -> bool:
    system = os_info["system"]
    port = port or get_service_port(root_dir)
    
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
ExecStart={py_bin} -m uvicorn main:app --host 0.0.0.0 --port {port}
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
            silent_vbs = os.path.join(root_dir, "start_sentinel_silent.vbs")
            cockpit_vbs = os.path.join(root_dir, "start_sentinel_cockpit.vbs")
            if node_role:
                set_node_role(root_dir, node_role)
            role = node_role or get_node_role(root_dir)
            venv_pyw = os.path.join(root_dir, ".venv", "Scripts", "pythonw.exe")
            venv_py = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
            sys_pyw = sys.executable.replace("python.exe", "pythonw.exe")
            chosen_py = next((p for p in (venv_pyw, sys_pyw) if os.path.isfile(p)), venv_py if os.path.isfile(venv_py) else sys.executable)
            with open(silent_vbs, "w", encoding="utf-8") as f:
                f.write('Set WshShell = CreateObject("WScript.Shell")\n')
                f.write(f'WshShell.CurrentDirectory = "{root_dir}"\n')
                f.write(f'WshShell.Run """{chosen_py}"" -m installer.background_service --no-open-ui", 0, False\n')

            task_action = f'wscript.exe "{silent_vbs}"'
            # Prefer boot-time service startup so headless and hybrid nodes stay online without a desktop session.
            res = subprocess.run(
                ["schtasks.exe", "/Create", "/TN", "SentinelOS_Service", "/TR", task_action, "/SC", "ONSTART", "/RU", "SYSTEM", "/RL", "HIGHEST", "/F"],
                capture_output=True,
                text=True,
                timeout=20,
            )
            boot_registered = res.returncode == 0
            # Keep a user-session fallback in case SYSTEM cannot access this install directory.
            logon_result = subprocess.run(
                ["schtasks.exe", "/Create", "/TN", "SentinelOS_Service_Logon", "/TR", task_action, "/SC", "ONLOGON", "/F"],
                capture_output=True,
                text=True,
                timeout=20,
            )
            logon_registered = logon_result.returncode == 0
            service_registered = boot_registered or logon_registered
            service_trigger = "al arrancar Windows" if boot_registered else "al iniciar sesión"
            registration_errors = []
            if not boot_registered and res.stderr.strip():
                registration_errors.append(res.stderr.strip())
            if not logon_registered and logon_result.stderr.strip():
                registration_errors.append(logon_result.stderr.strip())

            appdata = os.environ.get("APPDATA")
            startup_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup") if appdata else ""
            task_service_registered = service_registered
            cockpit_registered = role != "master"
            cockpit_task_registered = role != "master"
            if role == "master":
                with open(cockpit_vbs, "w", encoding="utf-8") as f:
                    f.write('Set WshShell = CreateObject("WScript.Shell")\n')
                    f.write(f'WshShell.CurrentDirectory = "{root_dir}"\n')
                    f.write(f'WshShell.Run """{chosen_py}"" -m installer.open_cockpit", 0, False\n')

                cockpit_action = f'wscript.exe "{cockpit_vbs}"'
                cockpit_result = subprocess.run(
                    ["schtasks.exe", "/Create", "/TN", "SentinelOS_Cockpit", "/TR", cockpit_action, "/SC", "ONLOGON", "/F"],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                cockpit_registered = cockpit_result.returncode == 0
                cockpit_task_registered = cockpit_registered
                if not cockpit_registered and cockpit_result.stderr.strip():
                    registration_errors.append(cockpit_result.stderr.strip())

            if startup_dir and (not service_registered or not cockpit_registered):
                os.makedirs(startup_dir, exist_ok=True)
                if not task_service_registered:
                    startup_vbs = os.path.join(startup_dir, "SentinelOS_AutoStart.vbs")
                    with open(startup_vbs, "w", encoding="utf-8") as f:
                        f.write('Set WshShell = CreateObject("WScript.Shell")\n')
                        f.write(f'WshShell.CurrentDirectory = "{root_dir}"\n')
                        f.write(f'WshShell.Run """{chosen_py}"" -m installer.background_service --no-open-ui", 0, False\n')
                if role == "master" and not cockpit_registered:
                    cockpit_startup = os.path.join(startup_dir, "SentinelOS_Cockpit.vbs")
                    with open(cockpit_startup, "w", encoding="utf-8") as f:
                        f.write('Set WshShell = CreateObject("WScript.Shell")\n')
                        f.write(f'WshShell.CurrentDirectory = "{root_dir}"\n')
                        f.write(f'WshShell.Run """{chosen_py}"" -m installer.open_cockpit", 0, False\n')
                    cockpit_registered = bool(startup_dir)
                service_registered = service_registered or (bool(startup_dir) and not task_service_registered)

            if startup_dir:
                stale_names = []
                if task_service_registered:
                    stale_names.extend(("SentinelOS_AutoStart.vbs", "SentinelOS_AutoStart.cmd"))
                if cockpit_task_registered:
                    stale_names.append("SentinelOS_Cockpit.vbs")
                for stale_name in stale_names:
                    stale_path = os.path.join(startup_dir, stale_name)
                    if os.path.exists(stale_path):
                        os.remove(stale_path)

            if service_registered and cockpit_registered:
                if role == "master":
                    print_success(f"El backend se iniciará oculto {service_trigger} (con respaldo al iniciar sesión); el Cockpit se abrirá solo en modo central.")
                else:
                    print_success(f"El backend se iniciará oculto {service_trigger}; este rol no abrirá navegador.")
                return True

            details = " ".join(registration_errors) or "Task Scheduler rechazó la tarea."
            print_warning(f"No se pudo registrar completamente el inicio automático: {details}")
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
            subprocess.run('schtasks /Delete /TN "SentinelOS_Service_Logon" /F', shell=True, capture_output=True)
            subprocess.run('schtasks /Delete /TN "SentinelOS_Cockpit" /F', shell=True, capture_output=True)
            appdata = os.environ.get("APPDATA")
            if appdata:
                startup_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
                for startup_file in ("SentinelOS_AutoStart.vbs", "SentinelOS_Cockpit.vbs", "SentinelOS_AutoStart.cmd"):
                    startup_path = os.path.join(startup_dir, startup_file)
                    if os.path.exists(startup_path):
                        os.remove(startup_path)
            start_bat = os.path.join(root_dir, "start_sentinel_bg.bat")
            if os.path.exists(start_bat):
                os.remove(start_bat)
            silent_vbs = os.path.join(root_dir, "start_sentinel_silent.vbs")
            if os.path.exists(silent_vbs):
                os.remove(silent_vbs)
            cockpit_vbs = os.path.join(root_dir, "start_sentinel_cockpit.vbs")
            if os.path.exists(cockpit_vbs):
                os.remove(cockpit_vbs)
        except Exception:
            pass
    elif system == "Linux":
        try:
            subprocess.run("systemctl disable labsentinel.service 2>/dev/null || true", shell=True, capture_output=True)
        except Exception:
            pass
