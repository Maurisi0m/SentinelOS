#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de integración Tailscale Zero-Config para SentinelOS.
Detecta instalaciones existentes, muestra cuenta y red si ya está activo,
gestiona inicio de sesión interactivo con QR y enlace web automático en navegador,
y habilita Tailscale Serve HTTPS automáticamente.
"""
import subprocess
import shutil
import sys
import os
import time
import re
import json
import webbrowser
from .banner import Colors, print_info, print_success, print_warning, print_error, print_step

def check_tailscale_path() -> str:
    """Devuelve la ruta absoluta del binario tailscale."""
    p = shutil.which("tailscale")
    if p:
        return p
    if sys.platform == "win32":
        possible_paths = [
            r"C:\Program Files\Tailscale\tailscale.exe",
            r"C:\Program Files (x86)\Tailscale\tailscale.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tailscale", "tailscale.exe")
        ]
        for path in possible_paths:
            if os.path.isfile(path):
                return path
    elif sys.platform.startswith("linux"):
        for path in ["/usr/bin/tailscale", "/usr/local/bin/tailscale"]:
            if os.path.isfile(path):
                return path
    return ""

def get_tailscale_details(ts_bin: str) -> dict:
    """
    Extrae información detallada del estado de Tailscale:
    - Estado de conexión (BackendState)
    - Cuenta del usuario (Email / LoginName, DisplayName)
    - Red / Tailnet
    - Nombre del nodo (HostName)
    - Dirección IP de Tailscale (IPv4)
    - Dominio MagicDNS (FQDN)
    - URL de autenticación pendiente
    """
    info = {
        "installed": False,
        "logged_in": False,
        "backend_state": "NoState",
        "account_email": "",
        "account_name": "",
        "tailnet": "",
        "node_name": "",
        "tailscale_ip": "",
        "magic_domain": "",
        "auth_url": ""
    }
    if not ts_bin:
        return info

    info["installed"] = True
    try:
        out = subprocess.check_output([ts_bin, "status", "--json"], text=True, stderr=subprocess.DEVNULL, timeout=6)
        data = json.loads(out)
        
        backend_state = data.get("BackendState", "NoState")
        info["backend_state"] = backend_state
        info["auth_url"] = data.get("AuthURL", "")

        self_node = data.get("Self", {})
        info["node_name"] = self_node.get("HostName", "")
        raw_dns = self_node.get("DNSName", "").rstrip('.')
        info["magic_domain"] = raw_dns

        ips = self_node.get("TailscaleIPs", []) or []
        if ips:
            info["tailscale_ip"] = ips[0]
        else:
            info["tailscale_ip"] = get_tailscale_ip(ts_bin)

        # Extraer Red (Tailnet)
        tailnet_obj = data.get("CurrentTailnet")
        if tailnet_obj and isinstance(tailnet_obj, dict):
            info["tailnet"] = tailnet_obj.get("Name", "") or tailnet_obj.get("MagicDNSSuffix", "")
        if not info["tailnet"] and data.get("MagicDNSSuffix"):
            info["tailnet"] = data.get("MagicDNSSuffix")

        # Extraer Cuenta / Usuario
        user_id = str(self_node.get("UserID", ""))
        users_dict = data.get("User", {}) or {}
        if user_id and user_id in users_dict:
            u = users_dict[user_id]
            info["account_email"] = u.get("LoginName", "")
            info["account_name"] = u.get("DisplayName", "")
        elif users_dict:
            first_user = next(iter(users_dict.values()))
            info["account_email"] = first_user.get("LoginName", "")
            info["account_name"] = first_user.get("DisplayName", "")

        # Si aún no tenemos email y el estado es Running, intentar con whoami
        if backend_state == "Running" and not info["account_email"]:
            try:
                who_out = subprocess.check_output([ts_bin, "whoami"], text=True, stderr=subprocess.DEVNULL, timeout=3).strip()
                if who_out and "@" in who_out:
                    info["account_email"] = who_out
            except Exception:
                pass

        # Consideramos sesión activa si está en Running y tiene IP o dominio
        if backend_state == "Running" and (info["tailscale_ip"] or info["magic_domain"]):
            info["logged_in"] = True

    except Exception:
        pass

    return info

def is_tailscale_logged_in(ts_bin: str) -> tuple[bool, str]:
    """Compatibilidad: verifica si Tailscale tiene sesión activa y devuelve (True, dominio)."""
    d = get_tailscale_details(ts_bin)
    return d["logged_in"], d["magic_domain"]

def get_tailscale_ip(ts_bin: str) -> str:
    """Extrae la dirección IPv4 de la interfaz Tailscale."""
    if not ts_bin:
        return ""
    try:
        out = subprocess.check_output([ts_bin, "ip", "-4"], text=True, timeout=3, stderr=subprocess.DEVNULL).strip()
        lines = out.splitlines()
        if lines and lines[0]:
            return lines[0].strip()
    except Exception:
        pass
    return ""

def configure_external_firewall_access(port=8001, lang="es"):
    """Regla de firewall auxiliar para el puerto local."""
    if sys.platform == "win32":
        try:
            cmd = f'netsh advfirewall firewall add rule name="SentinelOS_{port}" dir=in action=allow protocol=TCP localport={port} profile=private'
            subprocess.run(cmd, shell=True, capture_output=True)
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        try:
            if shutil.which("ufw"):
                subprocess.run(["ufw", "allow", f"{port}/tcp"], capture_output=True)
            elif shutil.which("iptables"):
                subprocess.run(f"iptables -I INPUT -p tcp --dport {port} -j ACCEPT", shell=True, capture_output=True)
        except Exception:
            pass

def install_tailscale_system(lang="es") -> str:
    """Instala Tailscale en el sistema operativo anfitrión."""
    print_step("Instalando Tailscale en el sistema..." if lang == "es" else "Installing Tailscale on system...")
    if sys.platform.startswith("linux"):
        try:
            cmd = "curl -fsSL https://tailscale.com/install.sh | sh"
            subprocess.run(cmd, shell=True)
        except Exception as e:
            print_error(f"Error al instalar Tailscale en Linux: {e}")
    elif sys.platform == "win32":
        installed_via_winget = False
        if shutil.which("winget"):
            print_info("Ejecutando instalación desatendida mediante Windows Package Manager (winget)...")
            try:
                res = subprocess.run(
                    ["winget", "install", "tailscale.tailscale", "--accept-package-agreements", "--accept-source-agreements", "-e", "--silent"],
                    capture_output=True,
                    text=True
                )
                if res.returncode == 0:
                    installed_via_winget = True
            except Exception:
                pass
        
        if not installed_via_winget:
            print_info("Descargando instalador oficial de Tailscale para Windows...")
            try:
                import urllib.request
                import tempfile
                setup_msi = os.path.join(tempfile.gettempdir(), "tailscale-setup.exe")
                url = "https://pkgs.tailscale.com/stable/tailscale-setup-latest.exe"
                urllib.request.urlretrieve(url, setup_msi)
                print_info("Ejecutando instalador de Tailscale...")
                subprocess.run([setup_msi, "/quiet"], check=False)
            except Exception as e:
                print_warning(f"Aviso en descarga de instalador: {e}")
                print_info("Puedes descargar Tailscale manualmente en: https://tailscale.com/download")

    time.sleep(3)
    return check_tailscale_path()

def login_tailscale_with_qr_and_browser(ts_bin: str, lang="es") -> dict:
    """
    Inicia sesión en Tailscale mostrando código QR en la consola
    y abriendo simultáneamente el enlace directo de registro/login en el navegador.
    """
    print()
    print("═" * 74)
    print(f"  {Colors.BOLD}{Colors.CYAN}🌐 REGISTRO / VINCULACIÓN DE CUENTA TAILSCALE{Colors.RESET}")
    print("═" * 74)
    print("  Tailscale requiere asociar este equipo a una cuenta gratuita.")
    print("  Puedes iniciar sesión con Google, Microsoft, GitHub, Apple o Correo.")
    print("  Generando código QR y enlace web de autorización...")
    print("═" * 74 + "\n")

    auth_url_found = None
    browser_opened = False

    try:
        proc = subprocess.Popen(
            [ts_bin, "up", "--qr", "--reset", "--accept-routes"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        qr_started = False
        while True:
            line = proc.stdout.readline()
            if not line:
                break

            # Buscar la URL de autenticación
            url_match = re.search(r'(https://login\.tailscale\.com/a/[a-zA-Z0-9]+)', line)
            if url_match and not auth_url_found:
                auth_url_found = url_match.group(1)
                print(f"\n{Colors.BOLD}{Colors.YELLOW}" + "╔" + "═" * 72 + "╗")
                print(f"║  🔗 {Colors.RESET}{Colors.BOLD}ENLACE DIRECTO DE AUTENTICACIÓN / REGISTRO DE CUENTA:{Colors.YELLOW}           ║")
                print(f"║     {Colors.CYAN}{auth_url_found}{Colors.YELLOW}  ║")
                print(f"║                                                                        ║")
                print(f"║  👉 {Colors.GREEN}Abriendo enlace automáticamente en tu navegador web...{Colors.YELLOW}             ║")
                print("╚" + "═" * 72 + "╝" + f"{Colors.RESET}\n")

                if not browser_opened:
                    try:
                        webbrowser.open(auth_url_found)
                        browser_opened = True
                    except Exception:
                        pass

            # Si empieza el bloque visual del QR, notificar
            if ("██" in line or "▄" in line) and not qr_started:
                qr_started = True
                print(f"{Colors.BOLD}📱 O escanea este código QR con la cámara de tu celular:{Colors.RESET}\n")

            # Imprimir la línea en la terminal
            print(line, end="")

        proc.wait(timeout=180)

    except subprocess.TimeoutExpired:
        print_warning("Tiempo de espera agotado para la autorización interactiva.")
    except KeyboardInterrupt:
        print_warning("\nProceso de vinculación cancelado por el usuario.")
        return {"url": "", "ip": "", "domain": ""}
    except Exception as e:
        print_warning(f"Aviso durante vinculación de Tailscale: {e}")

    # Verificar si el login fue exitoso
    time.sleep(2)
    details = get_tailscale_details(ts_bin)
    if details["logged_in"]:
        ts_ip = details["tailscale_ip"]
        magic_domain = details["magic_domain"]
        account_str = details["account_email"] or details["account_name"] or "Cuenta verificada"
        tailnet_str = details["tailnet"] or "Red Tailscale"
        node_str = details["node_name"] or "Este equipo"

        print("\n" + f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74)
        print("  🎉  ¡VINCULACIÓN EXITOSA CON TAILSCALE!")
        print("═" * 74 + f"{Colors.RESET}")
        print(f"  {Colors.BOLD}👤  Cuenta vinculada:{Colors.RESET}     {Colors.CYAN}{account_str}{Colors.RESET}")
        print(f"  {Colors.BOLD}🌐  Red (Tailnet):{Colors.RESET}         {Colors.CYAN}{tailnet_str}{Colors.RESET}")
        print(f"  {Colors.BOLD}🖥️  Nombre del nodo:{Colors.RESET}       {node_str}")
        print(f"  {Colors.BOLD}🔒  IP Tailscale:{Colors.RESET}          {Colors.GREEN}{ts_ip}{Colors.RESET}")
        if magic_domain:
            print(f"  {Colors.BOLD}✨  Dominio MagicDNS:{Colors.RESET}      {Colors.GREEN}https://{magic_domain}/{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74 + f"{Colors.RESET}\n")

        # Configurar Tailscale Serve para HTTPS si está disponible
        try:
            subprocess.run([ts_bin, "serve", "--reset"], capture_output=True, timeout=5)
            subprocess.run([ts_bin, "serve", "--bg", "8001"], capture_output=True, timeout=5)
        except Exception:
            pass

        return {
            "url": f"https://{magic_domain}/" if magic_domain else "",
            "ip": ts_ip,
            "domain": magic_domain,
            "account": account_str,
            "tailnet": tailnet_str
        }

    return {"url": "", "ip": "", "domain": ""}

def setup_tailscale_interactive(lang="es") -> dict:
    """
    Configuración inteligente de Tailscale:
    1. Si ya está instalado y conectado -> Informa al usuario su cuenta, tailnet e IP y pregunta si desea usarla.
    2. Si está instalado pero sin sesión -> Explica el requisito de cuenta, pregunta y lanza QR + navegador.
    3. Si no está instalado -> Explica el servicio y cuenta, ofrece instalarlo y si acepta lanza QR + navegador.
    """
    ts_bin = check_tailscale_path()

    # =========================================================================
    # CASO 1: TAILSCALE YA ESTÁ INSTALADO EN EL SISTEMA
    # =========================================================================
    if ts_bin:
        configure_external_firewall_access(8001, lang)
        details = get_tailscale_details(ts_bin)

        # SUB-CASO 1.A: Ya tiene una sesión activa y conectada
        if details["logged_in"]:
            account_str = details["account_email"] or details["account_name"] or "Sesión activa"
            tailnet_str = details["tailnet"] or "Red Privada Tailscale"
            node_str = details["node_name"] or "Este equipo"
            ts_ip = details["tailscale_ip"]
            magic_domain = details["magic_domain"]

            print("\n" + f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74)
            print("  ✔  TAILSCALE YA ESTÁ INSTALADO Y CONECTADO EN ESTE EQUIPO")
            print("═" * 74 + f"{Colors.RESET}")
            print(f"  {Colors.BOLD}👤  Cuenta vinculada:{Colors.RESET}     {Colors.CYAN}{account_str}{Colors.RESET}")
            print(f"  {Colors.BOLD}🌐  Red (Tailnet):{Colors.RESET}         {Colors.CYAN}{tailnet_str}{Colors.RESET}")
            print(f"  {Colors.BOLD}🖥️  Nombre del nodo:{Colors.RESET}       {node_str}")
            print(f"  {Colors.BOLD}🔒  IP Tailscale:{Colors.RESET}          {Colors.GREEN}{ts_ip}{Colors.RESET}")
            if magic_domain:
                print(f"  {Colors.BOLD}✨  Dominio MagicDNS:{Colors.RESET}      {Colors.GREEN}https://{magic_domain}/{Colors.RESET}")
            print("═" * 74 + "\n")

            use_existing = input("¿Deseas mantener esta conexión y usar esta cuenta para SentinelOS? (S/n): ").strip().lower()
            if use_existing not in ['n', 'no']:
                # Configurar Serve HTTPS
                try:
                    subprocess.run([ts_bin, "serve", "--reset"], capture_output=True, timeout=5)
                    subprocess.run([ts_bin, "serve", "--bg", "8001"], capture_output=True, timeout=5)
                except Exception:
                    pass
                return {
                    "url": f"https://{magic_domain}/" if magic_domain else "",
                    "ip": ts_ip,
                    "domain": magic_domain,
                    "account": account_str,
                    "tailnet": tailnet_str
                }
            else:
                change_acc = input("¿Deseas cerrar sesión en Tailscale y cambiar de cuenta ahora? (s/N): ").strip().lower()
                if change_acc in ['s', 'si', 'y']:
                    try:
                        print_info("Cerrando sesión en Tailscale...")
                        subprocess.run([ts_bin, "logout"], capture_output=True, timeout=5)
                    except Exception:
                        pass
                    return login_tailscale_with_qr_and_browser(ts_bin, lang)
                else:
                    print_info("Omitiendo configuración de Tailscale. Operando en modo LAN local.")
                    return {"url": "", "ip": "", "domain": ""}

        # SUB-CASO 1.B: Está instalado pero NO tiene sesión activa (NoState, NeedsLogin, etc.)
        else:
            print("\n" + f"{Colors.BOLD}{Colors.YELLOW}" + "═" * 74)
            print("  ℹ️  TAILSCALE ESTÁ INSTALADO (SIN SESIÓN ACTIVA)")
            print("═" * 74 + f"{Colors.RESET}")
            print("  Se detectó Tailscale en el sistema, pero requiere iniciar sesión.")
            print("  Nota: Requiere una cuenta gratuita en tailscale.com (Google, GitHub, etc.).")
            print("  Al continuar, se mostrará un código QR y se abrirá el enlace en tu navegador.")
            print("═" * 74 + "\n")

            start_login = input("¿Deseas iniciar sesión o registrar tu cuenta de Tailscale ahora? (S/n): ").strip().lower()
            if start_login not in ['n', 'no']:
                return login_tailscale_with_qr_and_browser(ts_bin, lang)
            else:
                print_info("Omitiendo Tailscale. SentinelOS funcionará en modo Red Local (LAN).")
                return {"url": "", "ip": "", "domain": ""}

    # =========================================================================
    # CASO 2: TAILSCALE NO ESTÁ INSTALADO EN EL SISTEMA
    # =========================================================================
    print("\n" + f"{Colors.BOLD}{Colors.CYAN}" + "═" * 74)
    print("  🔒  CONEXIÓN SEGURA REMOTA (TAILSCALE ZERO-CONFIG)")
    print("═" * 74 + f"{Colors.RESET}")
    print("  Tailscale no está instalado en este equipo.")
    print("  Permite acceder a SentinelOS de forma remota y segura desde tu celular")
    print("  o laptop fuera de casa sin abrir puertos en tu módem.")
    print("  • Requiere crear una cuenta gratuita en https://tailscale.com.")
    print("  • La instalación es automática y sin costo alguno.")
    print("═" * 74 + "\n")

    want_install = input("¿Deseas instalar y configurar Tailscale automáticamente? (S/n): ").strip().lower()
    if want_install in ['n', 'no']:
        print_info("Omitiendo Tailscale. SentinelOS funcionará en modo Red Local (LAN).")
        return {"url": "", "ip": "", "domain": ""}

    ts_bin = install_tailscale_system(lang)
    if not ts_bin:
        print_warning("No se pudo detectar el ejecutable de Tailscale tras la instalación.")
        print_info("Puedes instalarlo manualmente desde: https://tailscale.com/download")
        return {"url": "", "ip": "", "domain": ""}

    configure_external_firewall_access(8001, lang)
    return login_tailscale_with_qr_and_browser(ts_bin, lang)
