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
        msg_info = "No se requiere Node.js, npm ni Vite. El servidor web entrega la interfaz directamente en el puerto HTTP configurado." if lang == "es" else "Node.js, npm, and Vite are NOT required. The backend serves pre-compiled assets directly on the configured HTTP port."
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

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def bootstrap_pip(target_python: str = None, lang="es") -> bool:
    """Auto-reparación y bootstrap autónomo de pip si está ausente en el entorno Python."""
    if not target_python:
        target_python = sys.executable

    # Verificar si pip ya está funcional
    try:
        chk = subprocess.run([target_python, "-m", "pip", "--version"], capture_output=True, text=True, timeout=10)
        if chk.returncode == 0:
            return True
    except Exception:
        pass

    msg_start = "Auto-reparación: Módulo pip no detectado en el entorno. Iniciando instalación y recuperación autónoma de pip..." if lang == "es" else "Self-healing: pip module not detected. Initiating autonomous pip recovery..."
    print_warning(msg_start)

    local_get_pip = os.path.join(ROOT_DIR, "installer", "get-pip.py")

    # Método 1: Local get-pip.py (el más confiable y rápido, empaquetado en el repositorio)
    if os.path.exists(local_get_pip):
        print_step("Auto-reparación: Desplegando gestor pip desde bootstrap local empaquetado..." if lang == "es" else "Self-healing: Deploying pip from local bundled bootstrap...")
        try:
            res = subprocess.run([target_python, local_get_pip, "--no-setuptools", "--no-wheel"], capture_output=True, text=True, timeout=120)
            chk = subprocess.run([target_python, "-m", "pip", "--version"], capture_output=True, text=True, timeout=10)
            if chk.returncode == 0:
                print_success("Auto-reparación: Pip instalado y verificado exitosamente." if lang == "es" else "Self-healing: Pip installed and verified successfully.")
                return True
        except Exception as e:
            print_warning(f"Aviso en bootstrap local de pip: {e}")

    # Método 2: ensurepip de la biblioteca estándar
    try:
        print_step("Auto-reparación: Intentando inicialización mediante ensurepip..." if lang == "es" else "Self-healing: Attempting ensurepip initialization...")
        subprocess.run([target_python, "-m", "ensurepip", "--upgrade", "--default-pip"], capture_output=True, text=True, timeout=60)
        chk = subprocess.run([target_python, "-m", "pip", "--version"], capture_output=True, text=True, timeout=10)
        if chk.returncode == 0:
            print_success("Auto-reparación: Pip inicializado mediante ensurepip." if lang == "es" else "Self-healing: Pip initialized via ensurepip.")
            return True
    except Exception:
        pass

    # Método 3: Descarga dinámica de get-pip.py vía urllib o curl
    import tempfile
    temp_pip = os.path.join(tempfile.gettempdir(), "sentinel_get_pip.py")
    urls = [
        "https://bootstrap.pypa.io/get-pip.py",
        "https://raw.githubusercontent.com/pypa/get-pip/main/public/get-pip.py"
    ]
    downloaded = False
    for url in urls:
        try:
            print_step(f"Auto-reparación: Descargando get-pip.py desde {url}..." if lang == "es" else f"Self-healing: Downloading get-pip.py from {url}...")
            import urllib.request, ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={"User-Agent": "SentinelOS-Installer"})
            with urllib.request.urlopen(req, context=ctx, timeout=25) as resp, open(temp_pip, "wb") as f_out:
                f_out.write(resp.read())
            if os.path.exists(temp_pip) and os.path.getsize(temp_pip) > 10000:
                downloaded = True
                break
        except Exception:
            try:
                curl_bin = shutil.which("curl") or (r"C:\Windows\System32\curl.exe" if sys.platform == "win32" else None)
                if curl_bin and os.path.exists(curl_bin):
                    subprocess.run([curl_bin, "-sSL", url, "-o", temp_pip], capture_output=True, timeout=35)
                    if os.path.exists(temp_pip) and os.path.getsize(temp_pip) > 10000:
                        downloaded = True
                        break
            except Exception:
                pass

    if downloaded:
        try:
            subprocess.run([target_python, temp_pip, "--no-setuptools", "--no-wheel"], capture_output=True, text=True, timeout=120)
            chk = subprocess.run([target_python, "-m", "pip", "--version"], capture_output=True, text=True, timeout=10)
            if chk.returncode == 0:
                print_success("Auto-reparación: Pip instalado y verificado exitosamente." if lang == "es" else "Self-healing: Pip installed and verified successfully.")
                return True
        except Exception:
            pass

    # Método 4: Fallback modo usuario (--user) en Windows si hay restricciones de permisos globales
    if sys.platform == "win32" and os.path.exists(local_get_pip):
        try:
            print_step("Auto-reparación: Intentando despliegue de pip en espacio de usuario (--user)..." if lang == "es" else "Self-healing: Attempting pip deployment in user space (--user)...")
            subprocess.run([target_python, local_get_pip, "--user", "--no-setuptools", "--no-wheel"], capture_output=True, timeout=120)
            chk = subprocess.run([target_python, "-m", "pip", "--version"], capture_output=True, text=True, timeout=10)
            if chk.returncode == 0:
                print_success("Auto-reparación: Pip instalado en espacio de usuario." if lang == "es" else "Self-healing: Pip installed in user space.")
                return True
        except Exception:
            pass

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

    msg_install = f"Librerías faltantes detectadas: {', '.join(missing)}. Iniciando auto-reparación total..." if lang == "es" else f"Missing packages detected: {', '.join(missing)}. Initiating full self-healing..."
    print_step(msg_install)

    # 0. Asegurar que pip esté presente y 100% funcional en el entorno
    pip_ok = bootstrap_pip(sys.executable, lang)
    if not pip_ok:
        print_warning("Auto-reparación: No se pudo verificar pip directamente. Reintentando con configuración de entorno..." if lang == "es" else "Self-healing: Pip not verified directly. Retrying with environment config...")

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
    # En Windows, forzar --only-binary=:all: para evitar compilador C++ de Visual Studio
    cmd1 = [sys.executable, "-m", "pip", "install", "--prefer-binary", *extra_flags, *missing]
    if sys.platform == "win32":
        cmd1.insert(4, "--only-binary=:all:")
    try:
        res1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=120)
        if res1.returncode == 0:
            import site, importlib
            site.main()
            user_site = getattr(site, "getusersitepackages", lambda: None)()
            if user_site and user_site not in sys.path:
                sys.path.insert(0, user_site)
            importlib.invalidate_caches()
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
        "--timeout", "120",
        *extra_flags,
        *missing
    ]
    try:
        res2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=150)
        if res2.returncode == 0:
            import site, importlib
            site.main()
            user_site = getattr(site, "getusersitepackages", lambda: None)()
            if user_site and user_site not in sys.path:
                sys.path.insert(0, user_site)
            importlib.invalidate_caches()
            print_success("Librerías instaladas y verificadas." if lang == "es" else "Libraries installed and verified.")
            return True
    except Exception:
        pass

    # Intento 3: Instalación granular paquete por paquete
    print_warning("Auto-reparación: Intentando instalación granular individual por paquete..." if lang == "es" else "Self-healing: Attempting individual package-by-package installation...")
    for pkg in missing:
        try:
            pkg_cmd = [sys.executable, "-m", "pip", "install", "--prefer-binary", *extra_flags, pkg]
            if sys.platform == "win32":
                pkg_cmd = [sys.executable, "-m", "pip", "install", "--prefer-binary", "--only-binary=:all:", pkg]
            subprocess.run(pkg_cmd, capture_output=True, text=True, timeout=60)
        except Exception:
            pass

    # Intento 4: Si se ejecuta fuera de venv y hubo error de permisos, intentar --user
    if not is_venv:
        try:
            print_warning("Auto-reparación: Instalando en el espacio de usuario local (--user)..." if lang == "es" else "Self-healing: Installing into user space (--user)...")
            cmd_user = [sys.executable, "-m", "pip", "install", "--user", "--prefer-binary", *missing]
            subprocess.run(cmd_user, capture_output=True, text=True, timeout=120)
        except Exception:
            pass

    # Refrescar rutas de importación de Python
    try:
        import site, importlib
        site.main()
        user_site = getattr(site, "getusersitepackages", lambda: None)()
        if user_site and user_site not in sys.path:
            sys.path.insert(0, user_site)
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

    # Intento 5: Auto-recuperación agresiva final si todavía falta algún paquete
    if still_missing:
        print_step("Auto-reparación final: Descargando e instalando ruedas sin caché..." if lang == "es" else "Final self-healing: Downloading and installing wheels without cache...")
        for pkg in still_missing:
            try:
                rec_cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--force-reinstall", "--prefer-binary", pkg]
                subprocess.run(rec_cmd, capture_output=True, text=True, timeout=60)
            except Exception:
                pass
        
        # Volver a verificar
        still_missing = [p for p in still_missing if not _can_import(p)]

    if not still_missing:
        print_success("Auto-reparación completada: Todas las librerías se cargaron y verificaron correctamente." if lang == "es" else "Self-healing completed: All packages loaded and verified successfully.")
        return True
    else:
        err_msg = f"Auto-reparación parcial: Se intentó la instalación pero las siguientes librerías no pudieron inicializarse: {', '.join(still_missing)}" if lang == "es" else f"Partial self-healing: The following packages could not be initialized: {', '.join(still_missing)}"
        print_error(err_msg)
        return False

def _can_import(pkg: str) -> bool:
    try:
        __import__(pkg)
        return True
    except ImportError:
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
