#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Gestor Autónomo de Dependencias y Auto-Reparación (v2.0)
Detecta herramientas instaladas (reportando ruta absoluta), auto-corrige fallos de librerías
e instala dependencias fundamentales (Docker, Tailscale, paquetes Python).
"""
import os, sys, shutil, subprocess, time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from .banner import Colors, print_info, print_success, print_warning, print_error, print_step

def check_command(cmd: str) -> str:
    """Retorna la ruta absoluta del binario si está instalado, o cadena vacía si no."""
    p = shutil.which(cmd)
    if p:
        return os.path.abspath(p)
    
    # Comprobar rutas habituales en Windows si no está en PATH
    if sys.platform == "win32":
        win_candidates = {
            "docker": [
                r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
                r"C:\Program Files\Docker\Docker\DockerCli.exe"
            ],
            "tailscale": [
                r"C:\Program Files\Tailscale\tailscale.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Tailscale\tailscale.exe")
            ],
            "winget": [
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe")
            ]
        }
        for cand in win_candidates.get(cmd, []):
            if os.path.isfile(cand):
                return cand
    return ""

def ensure_python_libraries(lang="es") -> bool:
    """Verifica e instala dependencias de Python con auto-reparación y soporte PEP 668."""
    required = ["fastapi", "uvicorn", "aiohttp", "requests", "psutil", "pydantic"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        msg = f"Entorno Python verificado ({len(required)}/{len(required)} librerías activas)." if lang == "es" else f"Python environment verified ({len(required)}/{len(required)} packages active)."
        print_success(msg)
        return True

    msg_install = f"Librerías faltantes detectadas: {', '.join(missing)}. Instalando con auto-reparación..." if lang == "es" else f"Missing packages detected: {', '.join(missing)}. Installing with self-healing..."
    print_step(msg_install)

    # Intento 1: pip install con --break-system-packages (indispensable en uv y Debian 12 / Ubuntu 24.04)
    cmd1 = [sys.executable, "-m", "pip", "install", "--break-system-packages", *missing]
    try:
        res = subprocess.run(cmd1, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            print_success("Librerías instaladas exitosamente." if lang == "es" else "Libraries installed successfully.")
            return True
    except Exception:
        pass

    # Intento 2: Fallback con --prefer-binary
    print_warning("Auto-reparación: Reintentando instalación con modo binario..." if lang == "es" else "Self-healing: Retrying with binary wheels...")
    cmd2 = [sys.executable, "-m", "pip", "install", "--prefer-binary", "--break-system-packages", *missing]
    try:
        res = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            print_success("Librerías instaladas y verificadas." if lang == "es" else "Libraries installed and verified.")
            return True
    except Exception:
        pass

    # Verificación final individual
    still_missing = []
    for pkg in missing:
        try:
            __import__(pkg)
        except ImportError:
            still_missing.append(pkg)

    if not still_missing:
        print_success("Todas las librerías se cargaron correctamente." if lang == "es" else "All packages loaded successfully.")
        return True
    else:
        err_msg = f"No se pudieron cargar automáticamente: {', '.join(still_missing)}" if lang == "es" else f"Could not auto-load: {', '.join(still_missing)}"
        print_error(err_msg)
        return False

def check_and_install_docker(os_info: dict, lang="es") -> tuple[bool, str]:
    """Detecta Docker e indica su ruta absoluta; si falta, ofrece instalarlo según el SO."""
    docker_path = check_command("docker")
    if docker_path:
        print_success(f"Docker ya está instalado en: {Colors.CYAN}{docker_path}{Colors.RESET}")
        return True, docker_path

    print_info("Docker no detectado." if lang == "es" else "Docker not found.")
    system = os_info["system"]
    distro_id = os_info["distro_id"]

    if system == "Windows":
        winget_bin = check_command("winget")
        if winget_bin:
            prompt_q = "¿Deseas que SentinelOS instale Docker Desktop automáticamente vía Winget? (Requiere ~600MB) [s/N]: " if lang == "es" else "Install Docker Desktop automatically via Winget? (~600MB) [y/N]: "
            ans = input(prompt_q).strip().lower()
            if ans in ['s', 'si', 'y', 'yes']:
                print_info("Descargando e instalando Docker Desktop vía Winget...")
                try:
                    subprocess.run([winget_bin, "install", "Docker.DockerDesktop", "--accept-package-agreements", "--accept-source-agreements", "-e", "--silent"], timeout=300)
                    new_path = check_command("docker")
                    if new_path:
                        print_success(f"Docker Desktop instalado en: {Colors.CYAN}{new_path}{Colors.RESET}")
                        return True, new_path
                except Exception:
                    pass
        print_info("Continuando con servicios nativos de sistema de alto rendimiento (modo nativo)." if lang == "es" else "Proceeding with high-performance native system services.")
        return False, ""

    elif system == "Linux":
        prompt_q = "¿Deseas instalar Docker automáticamente en este servidor Linux? (Recomendado) [S/n]: " if lang == "es" else "Install Docker automatically on this Linux server? (Recommended) [Y/n]: "
        ans = input(prompt_q).strip().lower()
        if ans not in ['n', 'no']:
            print_step("Instalando Docker Engine en el servidor Linux...")
            if "ubuntu" in distro_id or "debian" in distro_id or "kali" in distro_id:
                cmd = "curl -fsSL https://get.docker.com | sh && systemctl enable --now docker"
            elif "arch" in distro_id or "manjaro" in distro_id:
                cmd = "pacman -Sy --noconfirm docker docker-compose && systemctl enable --now docker"
            elif "fedora" in distro_id or "rhel" in distro_id:
                cmd = "dnf install -y docker docker-compose && systemctl enable --now docker"
            else:
                cmd = "curl -fsSL https://get.docker.com | sh"

            try:
                subprocess.run(cmd, shell=True, timeout=180)
            except Exception:
                pass
            new_path = check_command("docker")
            if new_path:
                print_success(f"Docker instalado y habilitado en: {Colors.CYAN}{new_path}{Colors.RESET}")
                return True, new_path
        else:
            print_info("Instalación de Docker omitida. Usando servicios nativos." if lang == "es" else "Docker skipped. Using native services.")

    return False, ""

def check_and_install_tailscale(os_info: dict, lang="es") -> tuple[bool, str]:
    """Detecta Tailscale e indica su ruta absoluta; si falta, lo instala automáticamente."""
    ts_path = check_command("tailscale")
    if ts_path:
        print_success(f"Tailscale ya está instalado en: {Colors.CYAN}{ts_path}{Colors.RESET}")
        return True, ts_path

    print_info("Tailscale no detectado. Iniciando instalación autónoma..." if lang == "es" else "Tailscale not found. Initiating automated installation...")
    system = os_info["system"]

    if system == "Windows":
        winget_bin = check_command("winget")
        if winget_bin:
            try:
                subprocess.run([winget_bin, "install", "tailscale.tailscale", "--accept-package-agreements", "--accept-source-agreements", "-e", "--silent"], timeout=180)
            except Exception:
                pass
    elif system == "Linux":
        try:
            subprocess.run("curl -fsSL https://tailscale.com/install.sh | sh", shell=True, timeout=180)
        except Exception:
            pass

    new_ts_path = check_command("tailscale")
    if new_ts_path:
        print_success(f"Tailscale instalado exitosamente en: {Colors.CYAN}{new_ts_path}{Colors.RESET}")
        return True, new_ts_path
    
    print_warning("No se pudo instalar Tailscale de forma desatendida. Se continuará con acceso por red local." if lang == "es" else "Could not auto-install Tailscale. Continuing with LAN access.")
    return False, ""
