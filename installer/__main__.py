#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Asistente de Instalación Universal Autónomo (v2.0)
Detecta el sistema operativo, auto-repara dependencias, configura skills con submenús,
gestiona Tailscale sin conflictos, habilita inicio automático y verifica en vivo el servidor.
"""
import os, sys, time, socket

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from .banner import (
    ASCII_BANNER, Colors, play_intro_animation, print_header,
    print_success, print_warning, print_error, print_info, print_step, print_badge
)
from .system_detector import get_detailed_os
from .deps_manager import ensure_python_libraries, check_and_install_docker, check_frontend_assets
from .i18n import I18n
from .skills import AVAILABLE_SKILLS
from .tailscale import setup_tailscale_interactive
from .autostart import configure_autostart, disable_autostart
from .service_runner import start_and_verify_services
import webbrowser
import subprocess

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def auto_bootstrap_venv():
    """Garantiza que SentinelOS se ejecute siempre dentro de su entorno virtual aislado (.venv)."""
    if "--no-venv-bootstrap" in sys.argv or os.environ.get("SENTINEL_NO_VENV") == "1":
        return

    venv_dir = os.path.abspath(os.path.join(ROOT_DIR, ".venv"))
    if sys.platform == "win32":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python3")

    # Comprobar si ya estamos ejecutándonos exactamente dentro del .venv del proyecto
    current_prefix = os.path.abspath(sys.prefix).lower()
    current_exe = os.path.abspath(sys.executable).lower()
    target_venv_lower = venv_dir.lower()

    if current_prefix == target_venv_lower or current_exe.startswith(target_venv_lower):
        # Ya estamos dentro del entorno virtual del proyecto
        return

    print(f"\n{Colors.CYAN}[*] Detectado entorno del sistema: {sys.executable}{Colors.RESET}")
    print(f"{Colors.YELLOW}[*] Auto-reparación: Inicializando entorno virtual aislado (.venv) para garantizar permisos y librerías...{Colors.RESET}")

    # 1. Asegurar que .venv exista con su ejecutable funcional
    needs_create = True
    if os.path.exists(venv_python):
        try:
            chk = subprocess.run([venv_python, "-c", "import sys; print(1)"], capture_output=True, text=True, timeout=5)
            if chk.returncode == 0 and "1" in chk.stdout:
                needs_create = False
        except Exception:
            needs_create = True

    if needs_create:
        # Usar --without-pip que nunca falla (evita errores de ensurepip en Windows 11 Store y Linux minimal)
        print(f"{Colors.CYAN}[*] Creando estructura del entorno virtual seguro...{Colors.RESET}")
        res = subprocess.run([sys.executable, "-m", "venv", "--without-pip", venv_dir], capture_output=True, text=True, timeout=45)
        if not os.path.exists(venv_python) and sys.platform == "win32":
            subprocess.run(["py", "-3", "-m", "venv", "--without-pip", venv_dir], capture_output=True, timeout=45)

    if not os.path.exists(venv_python):
        print(f"{Colors.RED}[!] Aviso: No se pudo crear {venv_python}. Continuando con el intérprete actual...{Colors.RESET}")
        return

    # 2. Asegurar que pip esté presente y operativo dentro de .venv
    chk_pip = subprocess.run([venv_python, "-m", "pip", "--version"], capture_output=True, text=True)
    if chk_pip.returncode != 0:
        print(f"{Colors.YELLOW}[*] Auto-reparación: Desplegando gestor pip autónomo dentro del entorno virtual...{Colors.RESET}")
        local_get_pip = os.path.join(ROOT_DIR, "installer", "get-pip.py")
        if os.path.exists(local_get_pip):
            subprocess.run([venv_python, local_get_pip, "--no-setuptools", "--no-wheel"], capture_output=True, text=True, timeout=120)
        else:
            subprocess.run([venv_python, "-m", "ensurepip", "--upgrade"], capture_output=True, timeout=60)

    # 3. Pre-instalar dependencias fundamentales directamente dentro de .venv
    print(f"{Colors.CYAN}[*] Auto-reparación: Pre-instalando librerías esenciales (fastapi, uvicorn, psutil, pydantic) en el entorno aislado...{Colors.RESET}")
    pip_cmd = [
        venv_python, "-m", "pip", "install",
        "--prefer-binary",
        "--trusted-host", "pypi.org",
        "--trusted-host", "files.pythonhosted.org",
        "fastapi", "uvicorn", "aiohttp", "requests", "psutil", "pydantic"
    ]
    if sys.platform == "win32":
        pip_cmd.insert(4, "--only-binary=:all:")
    
    subprocess.run(pip_cmd, capture_output=True, text=True, timeout=180)

    print(f"{Colors.GREEN}[OK] Entorno virtual aislado configurado exitosamente.{Colors.RESET}")
    print(f"{Colors.GREEN}[OK] Conmutando ejecución a: {venv_python}{Colors.RESET}\n")

    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT_DIR
    env["VIRTUAL_ENV"] = venv_dir
    args = [a for a in sys.argv[1:] if a != "--no-venv-bootstrap"]
    cmd = [venv_python, "-m", "installer", "--no-venv-bootstrap", *args]
    res = subprocess.run(cmd, env=env)
    sys.exit(res.returncode)

def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    auto_bootstrap_venv()

    # -------------------------------------------------------------
    # INTRODUCCIÓN ANIMADA
    # -------------------------------------------------------------
    play_intro_animation()

    # -------------------------------------------------------------
    # DETECCIÓN DE SISTEMA Y HARDWARE
    # -------------------------------------------------------------
    os_info = get_detailed_os()
    print(f"\n{Colors.BOLD}{Colors.CYAN}╭── INFORMACIÓN DEL SISTEMA DETECTADO ─────────────────────────────────╮{Colors.RESET}")
    print(f"  {Colors.BOLD}🖥️  Plataforma:{Colors.RESET}         {os_info['distro_name']} ({os_info['arch']})")
    print(f"  {Colors.BOLD}📦  Gestor de Paquetes:{Colors.RESET} {os_info['pkg_manager']}")
    print(f"  {Colors.BOLD}⚡  Memoria RAM Total:{Colors.RESET}  {os_info['ram_gb']} GB")
    gpu_badge = f"{Colors.GREEN}NVIDIA GPU Detectada (Aceleración Habilitada){Colors.RESET}" if os_info['has_nvidia'] else f"{Colors.YELLOW}CPU Nativa (Optimizada AVX2){Colors.RESET}"
    print(f"  {Colors.BOLD}🎮  Acelerador:{Colors.RESET}         {gpu_badge}")
    print(f"{Colors.BOLD}{Colors.CYAN}╰──────────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")

    # -------------------------------------------------------------
    # PASO 1: SELECCIÓN DE IDIOMA
    # -------------------------------------------------------------
    print_header("Selección de Idioma / Language Selection", "1/6")
    print(f"  {Colors.BOLD}[1]{Colors.RESET} Español (Latinoamérica / España)")
    print(f"  {Colors.BOLD}[2]{Colors.RESET} English (US / Global)\n")
    lang_choice = input("Selecciona una opción / Select an option [1]: ").strip()
    lang = "en" if lang_choice == "2" else "es"
    i18n = I18n(lang)

    print_success(f"Idioma establecido: {'Español' if lang == 'es' else 'English'}\n")
    time.sleep(0.5)

    # -------------------------------------------------------------
    # AUTO-VERIFICACIÓN DE DEPENDENCIAS
    # -------------------------------------------------------------
    print_step("Comprobando entorno base y librerías..." if lang == "es" else "Checking base environment and packages...")
    ensure_python_libraries(lang)
    check_frontend_assets(ROOT_DIR, lang)
    check_and_install_docker(os_info, lang)
    print()

    # -------------------------------------------------------------
    # PASO 2: CATÁLOGO DE SKILLS & MÓDULOS CON SUBMENÚS
    # -------------------------------------------------------------
    print_header(i18n.t("step2"), "2/6")
    print(i18n.t("step2_desc") + "\n")

    for idx, skill_cls in enumerate(AVAILABLE_SKILLS, 1):
        name = skill_cls.name_es if lang == "es" else skill_cls.name_en
        desc = skill_cls.desc_es if lang == "es" else skill_cls.desc_en
        print(f"  {Colors.BOLD}[{idx}]{Colors.RESET} {Colors.CYAN}{name}{Colors.RESET}")
        print(f"      {Colors.DIM}{desc}{Colors.RESET}")

    print(f"\n  {Colors.BOLD}[A]{Colors.RESET} {Colors.GREEN}Instalar todas las skills recomendadas{Colors.RESET}")
    print(f"  {Colors.BOLD}[N]{Colors.RESET} Solo núcleo mínimo (STEM LLM + Cockpit)\n")

    choice = input("Selección [A]: ").strip().lower()
    if choice == "" or choice == "a":
        chosen_indices = list(range(1, len(AVAILABLE_SKILLS) + 1))
    elif choice == "n":
        chosen_indices = []
    else:
        try:
            chosen_indices = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
        except Exception:
            chosen_indices = list(range(1, len(AVAILABLE_SKILLS) + 1))

    configured_skills = []
    for idx in chosen_indices:
        if 1 <= idx <= len(AVAILABLE_SKILLS):
            skill_instance = AVAILABLE_SKILLS[idx - 1]()
            skill_instance.configure_interactive(lang)
            configured_skills.append(skill_instance)

    # -------------------------------------------------------------
    # PASO 3: TÉRMINOS Y RESPONSABILIDAD ÉTICA
    # -------------------------------------------------------------
    print_header(i18n.t("step3"), "3/6")
    print(f"{Colors.YELLOW}{i18n.t('terms_text')}{Colors.RESET}\n")
    agree = input(i18n.t("accept_terms")).strip().lower()
    if agree not in ['s', 'si', 'y', 'yes', '']:
        print_error(i18n.t("terms_rejected"))
        sys.exit(1)
    print_success("Términos aceptados.\n")

    # -------------------------------------------------------------
    # PASO 4: AUTOINICIO AL ENCENDER EL SERVIDOR (OPCIONAL/RECOMENDADO)
    # -------------------------------------------------------------
    print_header(i18n.t("step_autostart"), "4/6")
    prompt_auto = i18n.t("step_autostart_desc")
    auto_choice = input(prompt_auto).strip().lower()
    autostart_enabled = (auto_choice not in ['n', 'no'])
    if autostart_enabled:
        configure_autostart(os_info, ROOT_DIR, lang)
    else:
        disable_autostart(os_info, ROOT_DIR)
        print_info("Inicio automático omitido por el usuario." if lang == "es" else "Autostart skipped by user.")

    # -------------------------------------------------------------
    # PASO 5: CONEXIÓN SEGURA TAILSCALE ZERO-CONFIG
    # -------------------------------------------------------------
    print_header(i18n.t("step4"), "5/6")
    ts_ask = input(i18n.t("tailscale_prompt")).strip().lower()
    ts_data = {"url": "", "ip": "", "domain": ""}
    if ts_ask not in ['n', 'no']:
        ts_data = setup_tailscale_interactive(lang)

    remote_url = ts_data.get("url", "")
    ts_ip = ts_data.get("ip", "")

    # -------------------------------------------------------------
    # PASO 6: DESPLIEGUE REAL Y VERIFICACIÓN EN VIVO HTTP
    # -------------------------------------------------------------
    print_header(i18n.t("step5"), "6/6")
    is_healthy, local_base = start_and_verify_services(os_info, ROOT_DIR, lang)

    lan_ip = get_lan_ip()
    local_display_url = f"http://{lan_ip}:8001"

    # -------------------------------------------------------------
    # TARJETA FINAL DE ÉXITO Y CONECTIVIDAD COMPROBADA
    # -------------------------------------------------------------
    print("\n" + f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74)
    print(f"  🎉  {i18n.t('success_title')}")
    print("═" * 74 + f"{Colors.RESET}")
    print(f"  {Colors.BOLD}💻  Enlace Localhost:{Colors.RESET}           {Colors.CYAN}http://127.0.0.1:8001{Colors.RESET} (Comprobado ✔)")
    print(f"  {Colors.BOLD}🌐  Enlace Red Local (LAN):{Colors.RESET}     {Colors.CYAN}{local_display_url}{Colors.RESET} (Comprobado ✔)")
    if ts_ip:
        print(f"  {Colors.BOLD}🔒  IP Red Segura Tailscale:{Colors.RESET}   {Colors.CYAN}http://{ts_ip}:8001{Colors.RESET} (Comprobado ✔)")
    if remote_url:
        print(f"  {Colors.BOLD}✨  Enlace Cifrado MagicDNS:{Colors.RESET}   {Colors.GREEN}{remote_url}{Colors.RESET} (HTTPS Cifrado ✔)")
    
    active_skills_list = [s.id for s in configured_skills] if configured_skills else ["Core STEM"]
    print(f"  {Colors.BOLD}🧩  Módulos Desplegados:{Colors.RESET}        {', '.join(active_skills_list)}")
    print(f"  {Colors.BOLD}🚀  Unir Servidores Satélite (Mesh Fleet):{Colors.RESET}")
    print(f"      curl -fsSL {local_display_url}/api/mesh/join.sh | bash\n")
    print(f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74 + f"{Colors.RESET}\n")

    # Si es sistema de escritorio (Windows o con interfaz grafica), abrir navegador por defecto
    if os_info.get("system") == "Windows" or os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        try:
            print_info("Abriendo panel de control en tu navegador predeterminado..." if lang == "es" else "Opening cockpit in default browser...")
            webbrowser.open("http://127.0.0.1:8001")
        except Exception:
            pass

if __name__ == "__main__":
    main()
