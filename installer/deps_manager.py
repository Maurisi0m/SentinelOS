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

def check_frontend_assets(root_dir: str, lang="es") -> bool:
    """Verifica si los recursos estáticos del frontend ya están pre-compilados en dist/.
    Informa al usuario si es necesario o no contar con Node.js / npm / Vite."""
    dist_dir = os.path.join(root_dir, "labsentinel_backend", "dist")
    index_html = os.path.join(dist_dir, "index.html")

    if os.path.exists(index_html):
        msg_ok = "Interfaz web (Cockpit) pre-compilada detectada en labsentinel_backend/dist/." if lang == "es" else "Pre-compiled web interface (Cockpit) detected in labsentinel_backend/dist/."
        print_success(msg_ok)
        msg_info = "No se requiere Node.js, npm ni Vite. El servidor web entrega la interfaz directamente en el puerto 8001." if lang == "es" else "Node.js, npm, and Vite are NOT required. The backend serves pre-compiled assets directly on port 8001."
        print_info(msg_info)
        return True

    msg_warn = "No se encontro la carpeta dist/ pre-compilada en labsentinel_backend/." if lang == "es" else "Pre-compiled dist/ directory not found in labsentinel_backend/."
    print_warning(msg_warn)

    # Intentar compilar si npm está disponible
    npm_bin = shutil.which("npm")
    frontend_dir = os.path.join(root_dir, "frontend")
    if npm_bin and os.path.exists(frontend_dir):
        print_step("Auto-reparación: Compilando interfaz gráfica con npm y Vite..." if lang == "es" else "Self-healing: Building frontend interface with npm and Vite...")
        try:
            res = subprocess.run([npm_bin, "run", "build"], cwd=frontend_dir, capture_output=True, text=True, timeout=120)
            built_dist = os.path.join(frontend_dir, "dist")
            if os.path.exists(os.path.join(built_dist, "index.html")):
                os.makedirs(dist_dir, exist_ok=True)
                shutil.copytree(built_dist, dist_dir, dirs_exist_ok=True)
                print_success("Frontend compilado y vinculado exitosamente a labsentinel_backend/dist/." if lang == "es" else "Frontend successfully compiled and linked to labsentinel_backend/dist/.")
                return True
        except Exception as e:
            print_warning(f"Aviso en compilación de frontend: {e}")

    print_info("La interfaz gráfica puede ejecutarse con los archivos estáticos empaquetados en el repositorio." if lang == "es" else "The UI can run with static assets packaged in the repository.")
    return False

def ensure_python_libraries(lang="es") -> bool:
    """Verifica e instala dependencias de Python con auto-reparación multi-fase y soporte multiplataforma."""
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

    msg_install = f"Librerías faltantes detectadas: {', '.join(missing)}. Iniciando auto-reparación..." if lang == "es" else f"Missing packages detected: {', '.join(missing)}. Initiating self-healing..."
    print_step(msg_install)

    # 0. Asegurar que pip esté presente y funcional en el entorno
    try:
        pip_check = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
        if pip_check.returncode != 0:
            print_warning("Auto-reparación: Módulo pip no detectado en el entorno. Inicializando con ensurepip..." if lang == "es" else "Self-healing: pip module not detected. Bootstrapping with ensurepip...")
            subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], capture_output=True)
    except Exception:
        pass

    is_venv = (sys.prefix != getattr(sys, "base_prefix", sys.prefix))
    extra_flags = []
    # Solo agregar --break-system-packages si es Linux, fuera de venv y PEP 668 está activo
    if not is_venv and sys.platform != "win32":
        try:
            test_pip = subprocess.run([sys.executable, "-m", "pip", "install", "--help"], capture_output=True, text=True)
            if "--break-system-packages" in test_pip.stdout:
                extra_flags.append("--break-system-packages")
        except Exception:
            pass

    # Intento 1: Ruedas binarias pre-compiladas directas (--prefer-binary)
    cmd1 = [sys.executable, "-m", "pip", "install", "--prefer-binary", *extra_flags, *missing]
    try:
        res1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=90)
        if res1.returncode == 0:
            try:
                import site, importlib
                site.main()
                importlib.invalidate_caches()
            except Exception:
                pass
            print_success("Librerías instaladas exitosamente con ruedas binarias pre-compiladas." if lang == "es" else "Libraries installed successfully with pre-compiled wheels.")
            return True
    except Exception:
        pass

    # Intento 2: Red protegida / Fallback con hosts de confianza por si hay proxies o inspección SSL
    print_warning("Auto-reparación: Reintentando instalación con hosts de confianza y timeout ampliado..." if lang == "es" else "Self-healing: Retrying with trusted hosts and extended timeout...")
    cmd2 = [
        sys.executable, "-m", "pip", "install",
        "--prefer-binary",
        "--trusted-host", "pypi.org",
        "--trusted-host", "files.pythonhosted.org",
        "--trusted-host", "pypi.python.org",
        "--timeout", "90",
        *extra_flags,
        *missing
    ]
    try:
        res2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
        if res2.returncode == 0:
            try:
                import site, importlib
                site.main()
                importlib.invalidate_caches()
            except Exception:
                pass
            print_success("Librerías instaladas y verificadas." if lang == "es" else "Libraries installed and verified.")
            return True
    except Exception:
        pass

    # Intento 3: Instalación granular paquete por paquete
    print_warning("Auto-reparación: Intentando instalación granular individual por paquete..." if lang == "es" else "Self-healing: Attempting individual package-by-package installation...")
    for pkg in missing:
        try:
            pkg_cmd = [sys.executable, "-m", "pip", "install", "--prefer-binary", *extra_flags, pkg]
            if pkg == "psutil" and sys.platform == "win32":
                pkg_cmd = [sys.executable, "-m", "pip", "install", "--only-binary=:all:", pkg]
            subprocess.run(pkg_cmd, capture_output=True, text=True, timeout=45)
        except Exception:
            pass

    # Intento 4: Si se ejecuta fuera de venv y hubo error de permisos, intentar --user
    if not is_venv:
        try:
            print_warning("Auto-reparación: Instalando en el espacio de usuario local (--user)..." if lang == "es" else "Self-healing: Installing into user space (--user)...")
            cmd_user = [sys.executable, "-m", "pip", "install", "--user", "--prefer-binary", *missing]
            subprocess.run(cmd_user, capture_output=True, text=True, timeout=90)
        except Exception:
            pass

    # Refrescar rutas de importación de Python
    try:
        import site, importlib
        site.main()
        importlib.invalidate_caches()
    except Exception:
        pass

    # Verificación final individual de importación
    still_missing = []
    for pkg in missing:
        try:
            __import__(pkg)
        except ImportError:
            still_missing.append(pkg)

    if not still_missing:
        print_success("Todas las librerías se cargaron y verificaron correctamente." if lang == "es" else "All packages loaded and verified successfully.")
        return True
    else:
        err_msg = f"No se pudieron cargar automáticamente: {', '.join(still_missing)}" if lang == "es" else f"Could not auto-load: {', '.join(still_missing)}"
        print_error(err_msg)
        print_info(f"Sugerencia de auto-reparación manual: Ejecuta '{sys.executable} -m pip install {' '.join(still_missing)}'")
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
