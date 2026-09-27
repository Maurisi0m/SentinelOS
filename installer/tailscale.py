#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de integración Tailscale Zero-Config para SentinelOS.
Detecta instalaciones existentes, reutiliza sesiones activas, gestiona banderas de configuración
y habilita Tailscale Serve HTTPS automáticamente.
"""
import subprocess, shutil, sys, time, re, json
from .banner import Colors, print_info, print_success, print_warning, print_error, print_step

def check_tailscale_path() -> str:
    """Devuelve la ruta absoluta del binario tailscale."""
    # En Windows a veces tailscale está en Program Files pero no en PATH de la sesión actual
    p = shutil.which("tailscale")
    if p: return p
    if sys.platform == "win32":
        default_win = r"C:\Program Files\Tailscale\tailscale.exe"
        if shutil.which(default_win):
            return default_win
    return ""

def is_tailscale_logged_in(ts_bin: str) -> tuple[bool, str]:
    """Verifica si Tailscale ya tiene una sesión iniciada y extrae su dominio MagicDNS."""
    try:
        out = subprocess.check_output([ts_bin, "status", "--json"], text=True, stderr=subprocess.DEVNULL)
        data = json.loads(out)
        self_node = data.get("Self", {})
        dns_name = self_node.get("DNSName", "").rstrip('.')
        is_online = self_node.get("Online", False)
        backend_state = data.get("BackendState", "")

        if backend_state == "Running" and dns_name:
            return True, dns_name
    except Exception:
        pass
    return False, ""

def install_tailscale_system(lang="es") -> str:
    print_step("Instalando Tailscale en el sistema..." if lang == "es" else "Installing Tailscale on system...")
    if sys.platform.startswith("linux"):
        cmd = "curl -fsSL https://tailscale.com/install.sh | sh"
        subprocess.run(cmd, shell=True)
    elif sys.platform == "win32":
        subprocess.run(["winget", "install", "tailscale.tailscale", "--accept-package-agreements", "--accept-source-agreements", "-e", "--silent"])
    return check_tailscale_path()

def configure_external_firewall_access(port=8001, lang="es"):
    """Abre el puerto en el firewall del sistema para permitir conexiones externas desde otros dispositivos."""
    print_info("Configurando reglas de firewall para acceso externo e interoperabilidad..." if lang == "es" else "Configuring firewall rules for external access...")
    if sys.platform == "win32":
        try:
            cmd = f'netsh advfirewall firewall add rule name="SentinelOS_{port}" dir=in action=allow protocol=TCP localport={port}'
            subprocess.run(cmd, shell=True, capture_output=True)
            print_success(f"Regla de Windows Defender Firewall activa para puerto {port}.")
        except Exception as e:
            print_warning(f"No se pudo registrar regla en Windows Firewall: {e}")
    elif sys.platform.startswith("linux"):
        try:
            if shutil.which("ufw"):
                subprocess.run(["ufw", "allow", f"{port}/tcp"], capture_output=True)
                print_success(f"Regla de UFW activa para puerto {port}/tcp.")
            elif shutil.which("iptables"):
                subprocess.run(f"iptables -I INPUT -p tcp --dport {port} -j ACCEPT", shell=True, capture_output=True)
        except Exception:
            pass

def get_tailscale_ip(ts_bin: str) -> str:
    """Extrae la dirección IPv4 de la interfaz Tailscale."""
    try:
        out = subprocess.check_output([ts_bin, "ip", "-4"], text=True, timeout=3, stderr=subprocess.DEVNULL).strip()
        lines = out.splitlines()
        if lines and lines[0]:
            return lines[0].strip()
    except Exception:
        pass
    return ""

def setup_tailscale_interactive(lang="es") -> dict:
    """Configura Tailscale, soluciona problemas de firewall externo y devuelve la IP y el dominio."""
    ts_bin = check_tailscale_path()
    if not ts_bin:
        ts_bin = install_tailscale_system(lang)
        if not ts_bin:
            print_error("No se pudo instalar Tailscale de forma desatendida.")
            return {"url": "", "ip": "", "domain": ""}

    print_success(f"Tailscale detectado en: {Colors.CYAN}{ts_bin}{Colors.RESET}")
    configure_external_firewall_access(8001, lang)

    # Verificar si ya está conectado
    already_in, magic_domain = is_tailscale_logged_in(ts_bin)
    if already_in and magic_domain:
        ts_ip = get_tailscale_ip(ts_bin)
        print_success(f"Sesión activa detectada en Tailscale: {Colors.GREEN}https://{magic_domain}/{Colors.RESET}")
        if ts_ip:
            print_info(f"IP Tailscale activa: {Colors.CYAN}{ts_ip}{Colors.RESET}")
        print_info("Vinculando puerto 8001 a Tailscale Serve HTTPS...")
        try:
            subprocess.run([ts_bin, "serve", "--reset"], capture_output=True, timeout=5)
            subprocess.run([ts_bin, "serve", "--bg", "8001"], capture_output=True, timeout=5)
        except Exception:
            pass
        return {"url": f"https://{magic_domain}/", "ip": ts_ip, "domain": magic_domain}

    # Si no está conectado, solicitar autenticación con código QR usando --reset para evitar conflictos
    print_info("Iniciando vinculación interactiva con código QR...")
    try:
        proc = subprocess.Popen(
            [ts_bin, "up", "--qr", "--reset", "--accept-routes"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        while True:
            line = proc.stdout.readline()
            if not line:
                break
            print(line, end="")

        proc.wait()
    except Exception as e:
        print_warning(f"Aviso durante tailscale up: {e}")

    # Re-verificar tras el proceso
    time.sleep(3)
    ok, domain = is_tailscale_logged_in(ts_bin)
    if ok and domain:
        ts_ip = get_tailscale_ip(ts_bin)
        print_success(f"¡Autenticación completada con éxito! Dominio: {domain} | IP: {ts_ip}")
        try:
            subprocess.run([ts_bin, "serve", "--reset"], capture_output=True, timeout=5)
            subprocess.run([ts_bin, "serve", "--bg", "8001"], capture_output=True, timeout=5)
        except Exception:
            pass
        return {"url": f"https://{domain}/", "ip": ts_ip, "domain": domain}

    return {"url": "", "ip": "", "domain": ""}
