#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Gestor de Reglas de Cortafuegos (Firewall Guard) v2.0
Configura reglas de entrada para permitir conectividad LAN y Wi-Fi en Windows Defender Firewall y Linux UFW / Firewalld.
"""
import os, sys, shutil, subprocess
from .banner import Colors, print_success, print_warning, print_info, print_panel

RULE_NAME = "SentinelOS Core"

def is_admin() -> bool:
    """Verifica si el proceso actual tiene permisos elevados de administrador/root."""
    if sys.platform == "win32":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0

def check_firewall_rule(os_info: dict, port: int = 8001) -> bool:
    """Verifica si la regla de firewall ya está activa en el sistema."""
    system = os_info.get("system", "Linux")
    if system == "Windows":
        try:
            res = subprocess.run(
                f'netsh advfirewall firewall show rule name="{RULE_NAME}"',
                shell=True,
                capture_output=True,
                text=True
            )
            return res.returncode == 0 and RULE_NAME in res.stdout
        except Exception:
            return False
    elif system == "Linux":
        if shutil.which("ufw"):
            try:
                res = subprocess.run(["ufw", "status"], capture_output=True, text=True)
                return str(port) in res.stdout and ("ALLOW" in res.stdout or "Permitir" in res.stdout)
            except Exception:
                pass
        return False
    return False

def configure_firewall_rule(os_info: dict, port: int = 8001, lang: str = "es") -> tuple[bool, str]:
    """
    Configura y abre la regla de entrada en el firewall para el puerto de telemetría y Cockpit.
    En Windows utiliza netsh con elevación segura UAC si es necesario.
    En Linux utiliza ufw o firewall-cmd con sudo.
    """
    system = os_info.get("system", "Linux")
    
    # Comprobar si ya existe
    if check_firewall_rule(os_info, port):
        msg = f"La regla de firewall '{RULE_NAME}' para el puerto {port} ya está activa." if lang == "es" else f"Firewall rule '{RULE_NAME}' for port {port} is already active."
        print_success(msg)
        return True, msg

    print_info(f"Configurando regla de firewall para el puerto {port} (Red LAN/Wi-Fi)..." if lang == "es" else f"Configuring firewall rule for port {port} (LAN/Wi-Fi)...")

    if system == "Windows":
        rule_cmd = f'advfirewall firewall add rule name="{RULE_NAME}" dir=in action=allow protocol=TCP localport={port} profile=private,domain description="SentinelOS Telemetry and Cockpit Port"'
        if is_admin():
            try:
                res = subprocess.run(f"netsh {rule_cmd}", shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    msg = f"Regla de Windows Defender Firewall habilitada con éxito para el puerto {port}." if lang == "es" else f"Windows Defender Firewall rule successfully added for port {port}."
                    print_success(msg)
                    return True, msg
                else:
                    return False, res.stderr or res.stdout
            except Exception as e:
                return False, str(e)
        else:
            # Invocar elevación UAC limpia mediante PowerShell
            try:
                ps_cmd = f'Start-Process netsh -ArgumentList \'{rule_cmd}\' -Verb RunAs -Wait -WindowStyle Hidden'
                res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=30)
                if check_firewall_rule(os_info, port):
                    msg = f"Regla de Windows Defender Firewall habilitada con éxito para el puerto {port}." if lang == "es" else f"Windows Defender Firewall rule successfully added for port {port}."
                    print_success(msg)
                    return True, msg
                else:
                    msg = "No se concedió elevación de administrador para abrir el firewall. Otros equipos en LAN podrían no conectarse." if lang == "es" else "Admin elevation was not granted. LAN devices might not be able to connect."
                    print_warning(msg)
                    return False, msg
            except Exception as e:
                print_warning(f"Aviso al configurar firewall: {e}")
                return False, str(e)

    elif system == "Linux":
        if shutil.which("ufw"):
            try:
                cmd = f"sudo ufw allow {port}/tcp comment '{RULE_NAME}'"
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    msg = f"Regla UFW añadida para el puerto {port}/tcp." if lang == "es" else f"UFW rule added for port {port}/tcp."
                    print_success(msg)
                    return True, msg
            except Exception as e:
                pass
        elif shutil.which("firewall-cmd"):
            try:
                cmd = f"sudo firewall-cmd --add-port={port}/tcp --permanent && sudo firewall-cmd --reload"
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    msg = f"Regla firewalld añadida para el puerto {port}/tcp." if lang == "es" else f"Firewalld rule added for port {port}/tcp."
                    print_success(msg)
                    return True, msg
            except Exception as e:
                pass

        print_info(f"Firewall no restrictivo detectado o configurado manualmente para el puerto {port}.")
        return True, "Firewall configured"

    return False, "Unsupported OS"

def remove_firewall_rule(os_info: dict, port: int = 8001, lang: str = "es") -> bool:
    """Remueve las reglas creadas de firewall al desinstalar."""
    system = os_info.get("system", "Linux")
    if system == "Windows":
        try:
            cmd = f'netsh advfirewall firewall delete rule name="{RULE_NAME}"'
            if is_admin():
                subprocess.run(cmd, shell=True, capture_output=True)
            else:
                ps_cmd = f'Start-Process netsh -ArgumentList \'advfirewall firewall delete rule name="{RULE_NAME}"\' -Verb RunAs -Wait -WindowStyle Hidden'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
            return True
        except Exception:
            return False
    elif system == "Linux":
        if shutil.which("ufw"):
            subprocess.run(f"sudo ufw delete allow {port}/tcp 2>/dev/null || true", shell=True, capture_output=True)
        return True
    return False
