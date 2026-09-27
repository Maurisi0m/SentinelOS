#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess, shutil, sys, time, re
from .banner import Colors, print_info, print_success, print_warning, print_error

def is_tailscale_installed() -> bool:
    return shutil.which("tailscale") is not None

def install_tailscale(lang="es"):
    print_info("Instalando Tailscale en el sistema..." if lang == "es" else "Installing Tailscale...")
    if sys.platform.startswith("linux"):
        cmd = "curl -fsSL https://tailscale.com/install.sh | sh"
        res = subprocess.run(cmd, shell=True)
        return res.returncode == 0
    elif sys.platform == "win32":
        cmd = "winget install tailscale.tailscale -e --silent"
        res = subprocess.run(cmd, shell=True)
        return res.returncode == 0
    return False

def setup_tailscale_interactive(lang="es") -> str:
    """Configura Tailscale, muestra el enlace/QR interactivo y habilita tailscale serve."""
    if not is_tailscale_installed():
        ok = install_tailscale(lang)
        if not ok:
            print_error("No se pudo instalar Tailscale automáticamente.")
            return ""

    print_info("Iniciando sesión de Tailscale...")
    # Ejecutar tailscale up con solicitud de código QR
    try:
        proc = subprocess.Popen(
            ["tailscale", "up", "--qr"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        auth_url = ""
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            print(line, end="")
            if "https://login.tailscale.com/a/" in line:
                m = re.search(r'(https://login\.tailscale\.com/a/\S+)', line)
                if m:
                    auth_url = m.group(1)

        proc.wait()
    except Exception as e:
        print_warning(f"Error lanzando tailscale up con QR: {e}")

    # Verificar estado de Tailscale
    print_info("Verificando estado de conexión...")
    time.sleep(3)
    try:
        status_out = subprocess.check_output(["tailscale", "status", "--json"], text=True)
        # Extraer MagicDNS / FQDN
        fqdn_out = subprocess.check_output(["tailscale", "status", "--self=true"], text=True)
        match = re.search(r'(\S+\.ts\.net)', fqdn_out)
        magic_domain = match.group(1).rstrip('.') if match else ""

        if magic_domain:
            print_success(f"Tailscale conectado: {magic_domain}")
            # Configurar tailscale serve automáticamente para el backend en 8001
            print_info(f"Habilitando Tailscale Serve HTTPS en https://{magic_domain}/...")
            subprocess.run(["tailscale", "serve", "--bg", "8001"], capture_output=True)
            return f"https://{magic_domain}/"
    except Exception as e:
        print_warning(f"Tailscale no pudo determinar el dominio FQDN: {e}")

    return ""
