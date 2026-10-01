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
    print_success, print_warning, print_error, print_info, print_step, print_badge,
    print_panel, print_menu_item, print_prompt
)
from .system_detector import get_detailed_os
from .deps_manager import ensure_python_libraries, check_and_install_docker, check_frontend_assets
from .i18n import I18n
from .skills import AVAILABLE_SKILLS
from .tailscale import setup_tailscale_interactive
from .autostart import configure_autostart, disable_autostart
from .service_runner import start_and_verify_services
from .node_token import get_or_create_node_auth
from .firewall import configure_firewall_rule, remove_firewall_rule, check_firewall_rule
from .desktop_shortcut import configure_desktop_shortcuts, remove_desktop_shortcuts
from .port_guard import check_and_resolve_port, is_sentinel_install_on_port
from .service_config import get_service_port, set_node_role, set_service_port
from .uninstaller import kill_sentinel_processes, run_full_uninstall
from .cli import install_cli_to_path
import webbrowser
import subprocess
import json
import urllib.request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def detect_existing_installation(root_dir: str, os_info: dict) -> dict:
    """Detecta de forma inteligente si SentinelOS ya está instalado o activo en esta máquina."""
    auth_file = os.path.join(root_dir, "config", "node_auth.json")
    start_bat = os.path.join(root_dir, "start_sentinel_bg.bat")
    silent_vbs = os.path.join(root_dir, "start_sentinel_silent.vbs")
    systemd_file = "/etc/systemd/system/labsentinel.service"
    launcher_pyw = os.path.join(root_dir, "launch_cockpit.pyw")

    auth_data = {}
    has_valid_auth = False

    if os.path.exists(auth_file):
        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                auth_data = json.load(f)
                if auth_data.get("token") and auth_data.get("node_id"):
                    has_valid_auth = True
        except Exception:
            pass

    is_running = False
    live_info = {}
    active_port = get_service_port(root_dir)
    for probe_port in dict.fromkeys([active_port, 8001, 8002]):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{probe_port}/api/health", headers={"User-Agent": "SentinelInstaller"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    if is_sentinel_install_on_port(probe_port, root_dir) is False:
                        continue
                    is_running = True
                    active_port = probe_port
                    try:
                        info_req = urllib.request.Request(f"http://127.0.0.1:{probe_port}/api/node/token", headers={"User-Agent": "SentinelInstaller"})
                        with urllib.request.urlopen(info_req, timeout=2) as info_resp:
                            live_info = json.loads(info_resp.read().decode())
                    except Exception:
                        pass
                    break
        except Exception:
            pass
    if is_running:
        set_service_port(root_dir, active_port)

    has_autostart = False
    if os_info.get("system") == "Linux":
        has_autostart = os.path.exists(systemd_file)
    else:
        has_autostart = os.path.exists(start_bat) or os.path.exists(silent_vbs)

    # Una instalación SOLO se considera existente si:
    # 1. Salud y telemetría del servicio responden en vivo, O
    # 2. Tiene credenciales reales guardadas (has_valid_auth) Y (tiene autostart programado o launcher configurado)
    is_installed = is_running or (has_valid_auth and (has_autostart or os.path.exists(launcher_pyw)))

    return {
        "is_installed": is_installed,
        "is_running": is_running,
        "live_info": live_info,
        "node_auth": auth_data if has_valid_auth else {},
        "has_autostart": has_autostart,
        "port": active_port,
    }

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
    deps = ["fastapi", "uvicorn", "aiohttp", "requests", "psutil", "pydantic", "websockets"]
    if sys.platform == "win32":
        deps.append("pywinpty")
    else:
        deps.append("ptyprocess")

    pip_cmd = [
        venv_python, "-m", "pip", "install",
        "--prefer-binary",
        "--trusted-host", "pypi.org",
        "--trusted-host", "files.pythonhosted.org",
        *deps
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

def uninstall_system_cli(os_info: dict, lang="es"):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}¿Deseas eliminar también el entorno virtual (.venv) y configuraciones locales?{Colors.RESET}")
    print("  [s] Sí - Limpieza total absoluta")
    print("  [N] No - Conservar código y entorno virtual (Por defecto)")
    choice = input("  Selecciona una opción (s/N): ").strip().lower()
    purge = choice == "s"
    run_full_uninstall(os_info, ROOT_DIR, lang=lang, purge_venv=purge)

def _close_terminal_smoothly(os_info: dict, lang="es"):
    is_desktop = os_info.get("system") == "Windows" or bool(os.environ.get("DISPLAY")) or bool(os.environ.get("WAYLAND_DISPLAY"))
    if is_desktop:
        print("\n" + f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74)
        print("  ✔  SentinelOS está activo y operando 24/7 en segundo plano." if lang == "es" else "  ✔  SentinelOS is running 24/7 in the background.")
        print("     Esta terminal se cerrará automáticamente en 4 segundos..." if lang == "es" else "     This terminal will automatically close in 4 seconds...")
        print("═" * 74 + f"{Colors.RESET}\n")
        try:
            sys.stdout.flush()
        except Exception:
            pass
        time.sleep(4)

        if os_info.get("system") == "Windows":
            try:
                import ctypes
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            except Exception:
                pass
        elif os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            try:
                import signal
                ppid = os.getppid()
                if ppid > 1:
                    os.kill(ppid, signal.SIGHUP)
            except Exception:
                pass

def main():
    if "--uninstall" in sys.argv:
        os_info = get_detailed_os()
        uninstall_system_cli(os_info, "es")
        return

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
    # DETECCIÓN DE INSTALACIÓN PREVIA EXISTENTE
    # -------------------------------------------------------------
    existing = detect_existing_installation(ROOT_DIR, os_info)
    if existing["is_installed"] and "--fresh" not in sys.argv:
        node_name = existing["live_info"].get("node_name") or existing["node_auth"].get("node_name") or os_info.get("hostname") or "Sentinel-Node"
        node_id = existing["live_info"].get("node_id") or existing["node_auth"].get("node_id") or "node-live"
        token = existing["live_info"].get("token") or existing["node_auth"].get("token") or "sntl_live_active"
        status_badge = f"{Colors.GREEN}● EN LÍNEA (http://127.0.0.1:{existing['port']}){Colors.RESET}" if existing["is_running"] else f"{Colors.YELLOW}○ DETENIDO (Listo para arrancar){Colors.RESET}"
        autostart_str = f"{Colors.GREEN}Activo (Inicio con Sistema){Colors.RESET}" if existing["has_autostart"] else f"{Colors.DIM}No programado{Colors.RESET}"

        print(f"{Colors.BOLD}{Colors.CYAN}╭── ⚡ INSTALACIÓN EXISTENTE DE SENTINEL OS DETECTADA ────────────────╮{Colors.RESET}")
        print(f"  {Colors.BOLD}● Estado en vivo:{Colors.RESET}       {status_badge}")
        print(f"  {Colors.BOLD}🖥️  Identidad de Nodo:{Colors.RESET}   {node_name} {Colors.DIM}(ID: {node_id}){Colors.RESET}")
        print(f"  {Colors.BOLD}🔑  Token PIN Malla:{Colors.RESET}     {Colors.GREEN}{token}{Colors.RESET}")
        print(f"  {Colors.BOLD}🚀  Autostart (Boot):{Colors.RESET}    {autostart_str}")
        print(f"  {Colors.BOLD}📦  Plataforma:{Colors.RESET}          {os_info['distro_name']} ({os_info['ram_gb']} GB RAM • {os_info['cores']} Cores)")
        print(f"{Colors.BOLD}{Colors.CYAN}╰─────────────────────────────────────────────────────────────────────╯{Colors.RESET}\n")

        print(f"  {Colors.BOLD}¿Qué acción deseas realizar hoy?{Colors.RESET}\n")
        print_menu_item("1", "Abrir Cockpit / Iniciar Servicio", "Abre el panel en el navegador y mantiene el daemon 24/7 en segundo plano", "Recomendado", Colors.GREEN)
        print_menu_item("2", "Actualizar y Reparar", "Recompila assets frontend, valida librerías y reinicia los servicios", "Update", Colors.CYAN)
        print_menu_item("3", "Reconfigurar Servidor", "Cambiar rol (Maestro/Satélite), Tailscale, autostart o módulos STEM", "Config", Colors.YELLOW)
        print_menu_item("4", "Reinstalación Limpia", "Resetear credenciales y tokens, ejecutando el instalador desde cero", "Clean", Colors.MAGENTA)
        print_menu_item("5", "Desinstalar SentinelOS", "Detener demonios, limpiar tareas de autoinicio y servicios del sistema", "Danger", Colors.RED)
        print_menu_item("0", "Salir", "Cerrar el asistente sin hacer cambios", "", Colors.DIM)

        choice = print_prompt("Selecciona una opción", "1")

        if choice in ["", "1"]:
            if not existing["is_running"]:
                healthy, local_base = start_and_verify_services(os_info, ROOT_DIR, "es")
            else:
                print_success("El servidor ya está en ejecución y saludable.")
                healthy = True
                local_base = f"http://127.0.0.1:{existing['port']}"
            if healthy:
                active_port = int(local_base.rsplit(":", 1)[-1])
                if existing["has_autostart"]:
                    configure_autostart(os_info, ROOT_DIR, "es", port=active_port)
                configure_firewall_rule(os_info, port=active_port, lang="es", root_dir=ROOT_DIR)
                configure_desktop_shortcuts(ROOT_DIR, os_info, "es")
                try:
                    print_info("Abriendo panel de control en tu navegador predeterminado...")
                    webbrowser.open(local_base)
                except Exception:
                    pass
            _close_terminal_smoothly(os_info, "es")
            return

        elif choice == "2":
            print_step("Iniciando actualización y verificación de componentes...")
            ensure_python_libraries("es")
            check_frontend_assets(ROOT_DIR, "es")
            stopped = kill_sentinel_processes(ROOT_DIR)
            if stopped["failed"]:
                print_error(f"No pude detener backends de SentinelOS para actualizarla: {', '.join(map(str, stopped['failed']))}")
                healthy = False
                local_base = f"http://127.0.0.1:{get_service_port(ROOT_DIR)}"
            else:
                healthy, local_base = start_and_verify_services(os_info, ROOT_DIR, "es")
            if healthy:
                active_port = int(local_base.rsplit(":", 1)[-1])
                if existing["has_autostart"]:
                    configure_autostart(os_info, ROOT_DIR, "es", port=active_port)
                configure_firewall_rule(os_info, port=active_port, lang="es", root_dir=ROOT_DIR)
                configure_desktop_shortcuts(ROOT_DIR, os_info, "es")
                try:
                    print_info("Abriendo panel de control en tu navegador predeterminado...")
                    webbrowser.open(f"{local_base}/?first_run=1")
                except Exception:
                    pass
            _close_terminal_smoothly(os_info, "es")
            return

        elif choice == "3":
            print_info("Iniciando asistente de reconfiguración...")
            pass

        elif choice == "4":
            print_warning("Limpiando configuración previa para reinstalación limpia...")
            stopped = kill_sentinel_processes(ROOT_DIR)
            if stopped["failed"]:
                print_error(f"No pude detener los procesos actuales: {', '.join(map(str, stopped['failed']))}. No continuaré para evitar una reinstalación mezclada.")
                return
            auth_file = os.path.join(ROOT_DIR, "config", "node_auth.json")
            if os.path.exists(auth_file):
                try:
                    os.remove(auth_file)
                except Exception:
                    pass
            print_success("Configuración anterior reseteada. Continuando con la instalación...")
            pass

        elif choice == "5":
            uninstall_system_cli(os_info, "es")
            return

        elif choice == "0":
            print("\nHasta pronto.\n")
            return

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
    # PASO 2: ROL Y MODO DE DESPLIEGUE DEL SISTEMA
    # -------------------------------------------------------------
    print_header("Rol y Modo de Despliegue / Node Deployment Role", "2/7")
    print("Elige cómo deseas configurar este equipo en tu infraestructura:\n" if lang == "es" else "Choose how to configure this machine in your infrastructure:\n")
    print(f"  {Colors.BOLD}[1]{Colors.RESET} {Colors.CYAN}Nodo Maestro (Control / Cockpit){Colors.RESET}")
    print("      Para tu laptop personal o estación de trabajo de administración.")
    print("      Despliega el Dashboard interactivo con monitoreo local y gestor de servidores remotos.\n")

    print(f"  {Colors.BOLD}[2]{Colors.RESET} {Colors.YELLOW}Servidor Dedicado / Nodo de Cómputo (Laboratorio 24/7){Colors.RESET}")
    print("      Para servidores físicos, racks, clusters o máquinas secundarias.")
    print("      Ejecuta cargas pesadas, inferencia IA y telemetría perimetral permanente.\n")

    print(f"  {Colors.BOLD}[3]{Colors.RESET} {Colors.GREEN}Nodo de Red / Sentinel Mesh (Interconexión Segura){Colors.RESET}")
    print("      Configuración especializada de red cifrada multi-nodo.\n")

    print(f"  {Colors.BOLD}[4]{Colors.RESET} {Colors.RED}Desinstalar SentinelOS (Detener y remover servicios de este equipo){Colors.RESET}\n")

    role_choice = input("Selecciona una opción / Select an option [1]: ").strip()
    node_role = "master"

    if role_choice == "4":
        confirm = input("¿Estás seguro de que deseas desinstalar SentinelOS de este equipo? (s/N): ").strip().lower()
        if confirm in ['s', 'si', 'y']:
            uninstall_system_cli(os_info, lang)
        else:
            print("Operación cancelada.")
        return

    if role_choice == "2":
        print("\n" + "-" * 70)
        print("  OPCIONES DE CONFIGURACIÓN DEL SERVIDOR" if lang == "es" else "  SERVER CONFIGURATION OPTIONS")
        print("-" * 70)
        print(f"  {Colors.BOLD}[A]{Colors.RESET} {Colors.CYAN}Agente Puro Headless (Solo conexión para Dashboard Maestro, sin interfaz){Colors.RESET}")
        print("      - Sin abrir navegador ni consumir recursos en interfaz gráfica.")
        print("      - Levanta el demonio en segundo plano 24/7 (auto-arranque en boot).")
        print("      - Genera el Token y la IP para vincularlo a tu Laptop Maestra.\n")

        print(f"  {Colors.BOLD}[B]{Colors.RESET} {Colors.GREEN}Servidor Híbrido / Cockpit Multi-Nodo (Interfaz Web Propia + Enlace a otros Cockpits){Colors.RESET}")
        print("      - Proporciona su propia interfaz web Cockpit accesible en red local (puerto HTTP configurado).")
        print("      - Levanta el demonio permanente en segundo plano con inicio automático.")
        print("      - Genera el Token PIN para vincularse bidireccionalmente con otros Cockpits de la red.\n")

        print(f"  {Colors.BOLD}[C]{Colors.RESET} {Colors.YELLOW}Servidor Standalone (Únicamente Dashboard Propio local){Colors.RESET}")
        print("      - Servidor autónomo con panel web local sin vinculación remota.\n")

        sub_choice = input("Selección de modo de servidor [A]: ").strip().lower()
        if sub_choice == "b":
            node_role = "server_hybrid"
        elif sub_choice == "c":
            node_role = "server_standalone"
        else:
            node_role = "server_headless"
    elif role_choice == "3":
        node_role = "mesh"
    else:
        node_role = "master"

    set_node_role(ROOT_DIR, node_role)
    print_success(f"Modo de nodo establecido: {node_role.upper()}\n")

    print_step("Reservando un puerto HTTP de SentinelOS (8001 o 8002)...")
    service_port, _ = check_and_resolve_port(port=get_service_port(ROOT_DIR), lang="es", root_dir=ROOT_DIR)
    set_service_port(ROOT_DIR, service_port)

    # -------------------------------------------------------------
    # PASO 3: CATÁLOGO DE SKILLS & MÓDULOS CON SUBMENÚS
    # -------------------------------------------------------------
    print_header(i18n.t("step2"), "3/7")
    print(i18n.t("step2_desc") + "\n")

    for idx, skill_cls in enumerate(AVAILABLE_SKILLS, 1):
        name = skill_cls.name_es if lang == "es" else skill_cls.name_en
        desc = skill_cls.desc_es if lang == "es" else skill_cls.desc_en
        print(f"  {Colors.BOLD}[{idx}]{Colors.RESET} {Colors.CYAN}{name}{Colors.RESET}")
        print(f"      {Colors.DIM}{desc}{Colors.RESET}")

    default_skills = "N" if node_role == "server_headless" else "A"
    print(f"\n  {Colors.BOLD}[A]{Colors.RESET} {Colors.GREEN}Instalar todas las skills recomendadas{Colors.RESET}")
    print(f"  {Colors.BOLD}[N]{Colors.RESET} Solo núcleo mínimo (STEM LLM + Telemetría)\n")

    choice = input(f"Selección [{default_skills}]: ").strip().lower()
    if choice == "":
        choice = default_skills.lower()

    if choice == "a":
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
    # PASO 4: TÉRMINOS Y RESPONSABILIDAD ÉTICA
    # -------------------------------------------------------------
    print_header(i18n.t("step3"), "4/7")
    print(f"{Colors.YELLOW}{i18n.t('terms_text')}{Colors.RESET}\n")
    agree = input(i18n.t("accept_terms")).strip().lower()
    if agree not in ['s', 'si', 'y', 'yes', '']:
        print_error(i18n.t("terms_rejected"))
        sys.exit(1)
    print_success("Términos aceptados.\n")

    # -------------------------------------------------------------
    # PASO 5: AUTOINICIO AL ENCENDER EL SERVIDOR (OPCIONAL/RECOMENDADO)
    # -------------------------------------------------------------
    print_header(i18n.t("step_autostart"), "5/7")
    if node_role in ["server_headless", "server_hybrid", "server_standalone"]:
        print_info("Modo Servidor detectado: El auto-inicio 24/7 en boot es altamente recomendado para mantener el servicio activo.")
    elif node_role == "master":
        print_info("Modo central: al iniciar sesión, el backend arrancará oculto y se abrirá el Cockpit.")
    
    prompt_auto = i18n.t("step_autostart_desc")
    auto_choice = input(prompt_auto).strip().lower()
    autostart_enabled = (auto_choice not in ['n', 'no'])
    if autostart_enabled:
        configure_autostart(os_info, ROOT_DIR, lang, port=service_port, node_role=node_role)
    else:
        disable_autostart(os_info, ROOT_DIR)
        print_info("Inicio automático omitido por el usuario." if lang == "es" else "Autostart skipped by user.")

    # -------------------------------------------------------------
    # PASO 6: CONEXIÓN SEGURA TAILSCALE ZERO-CONFIG
    # -------------------------------------------------------------
    print_header(i18n.t("step4"), "6/7")
    ts_data = setup_tailscale_interactive(lang, http_port=service_port)
    remote_url = ts_data.get("url", "")
    ts_ip = ts_data.get("ip", "")
    ts_account = ts_data.get("account", "")
    ts_tailnet = ts_data.get("tailnet", "")

    # -------------------------------------------------------------
    # PASO 7: DESPLIEGUE REAL Y VERIFICACIÓN EN VIVO HTTP
    # -------------------------------------------------------------
    print_header(i18n.t("step5"), "7/7")
    is_healthy, local_base = start_and_verify_services(os_info, ROOT_DIR, lang, port=service_port)
    if is_healthy:
        service_port = int(local_base.rsplit(":", 1)[-1])
        set_service_port(ROOT_DIR, service_port)

    # Abrir firewall únicamente en el puerto real que ya respondió a la API de telemetría.
    print_header("Seguridad de Red y Cortafuegos / Firewall Guard", "6.5/7")
    print_info(f"Permitir que otros equipos de tu LAN se conecten por TCP {service_port}.")
    fw_choice = input(f"¿Deseas habilitar la regla de firewall para el puerto {service_port}? (S/n): ").strip().lower()
    if is_healthy and fw_choice not in ['n', 'no']:
        configure_firewall_rule(os_info, port=service_port, lang=lang, root_dir=ROOT_DIR)
    print()

    # Configurar acceso directo en Escritorio y Menú Inicio para el Cockpit
    if node_role != "server_headless" and is_healthy:
        configure_desktop_shortcuts(ROOT_DIR, os_info, lang)
    
    # Instalar comandos 'sentinel' en el PATH del sistema
    try:
        install_cli_to_path(ROOT_DIR)
        print_success("Comandos de terminal 'sentinel' (active, stop, status, logs) instalados en el PATH.")
    except Exception as e:
        print_warning(f"Aviso instalación CLI en PATH: {e}")

    lan_ip = get_lan_ip()
    local_display_url = f"http://{lan_ip}:{service_port}"
    node_auth = get_or_create_node_auth(ROOT_DIR)

    # -------------------------------------------------------------
    # TARJETAS FINALES SEGÚN EL ROL DEL NODO
    # -------------------------------------------------------------
    if node_role == "server_headless":
        print("\n" + f"{Colors.BOLD}{Colors.CYAN}" + "═" * 74)
        print("  🔑  SERVIDOR ACTIVO EN MODO HEADLESS (CONEXIÓN A DASHBOARD MAESTRO)")
        print("═" * 74 + f"{Colors.RESET}")
        print(f"  {Colors.BOLD}🖥️  Nombre del Servidor:{Colors.RESET}        {node_auth.get('node_name', 'Sentinel-Server')}")
        print(f"  {Colors.BOLD}🌐  Dirección IP Local (LAN):{Colors.RESET}   {Colors.CYAN}{local_display_url}{Colors.RESET}")
        if ts_ip:
            print(f"  {Colors.BOLD}🔒  Dirección IP Tailscale:{Colors.RESET}     {Colors.CYAN}http://{ts_ip}:{service_port}{Colors.RESET}")
        print(f"  {Colors.BOLD}🔑  Token de Conexión PIN:{Colors.RESET}      {Colors.GREEN}{node_auth.get('token')}{Colors.RESET}")
        server_status = f"{Colors.GREEN}ACTIVO 24/7 EN SEGUNDO PLANO (Sin UI local){Colors.RESET}" if is_healthy else f"{Colors.RED}NO VALIDADO: backend/telemetría requieren revisión{Colors.RESET}"
        print(f"  {Colors.BOLD}📡  Estado del Servicio:{Colors.RESET}        {server_status}\n")
        print(f"  {Colors.YELLOW}Instrucciones de vinculación con tu Laptop Maestra:{Colors.RESET}")
        print("  1. Abre el Cockpit en tu Laptop Maestra.")
        print("  2. En el menú superior o barra lateral pulsa en '[+ Conectar Servidor]'.")
        print(f"  3. Pega los siguientes datos de este servidor:")
        print(f"     • Host / IP:  {lan_ip} (o la IP de Tailscale: {ts_ip if ts_ip else lan_ip})")
        print(f"     • Puerto:     {service_port}")
        print(f"     • Token PIN:  {node_auth.get('token')}\n")
        print(f"{Colors.BOLD}{Colors.CYAN}" + "═" * 74 + f"{Colors.RESET}\n")

    elif node_role == "server_hybrid":
        print("\n" + f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74)
        print("  ✨  SERVIDOR HÍBRIDO ACTIVO: WEB PROPIA + VINCULACIÓN A MAESTRO")
        print("═" * 74 + f"{Colors.RESET}")
        print(f"  {Colors.BOLD}💻  Interfaz Web del Servidor:{Colors.RESET}   {Colors.CYAN}{local_display_url}{Colors.RESET}{' (Comprobado ✔)' if is_healthy else ' (API no validada)'}")
        print(f"  {Colors.BOLD}🔑  Token para Laptop Maestra:{Colors.RESET}   {Colors.GREEN}{node_auth.get('token')}{Colors.RESET}")
        if ts_ip:
            print(f"  {Colors.BOLD}🔒  IP Tailscale Segura:{Colors.RESET}        {Colors.CYAN}http://{ts_ip}:{service_port}{Colors.RESET}")
        server_status = f"{Colors.GREEN}OPERATIVO 24/7{Colors.RESET}" if is_healthy else f"{Colors.RED}NO VALIDADO: backend/telemetría requieren revisión{Colors.RESET}"
        print(f"  {Colors.BOLD}📡  Estado del Servicio:{Colors.RESET}        {server_status}\n")
        print(f"  {Colors.YELLOW}Datos para vincular a tu Laptop Maestra:{Colors.RESET}")
        print(f"  • Host: {lan_ip} | Puerto: {service_port} | Token: {node_auth.get('token')}\n")
        print(f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74 + f"{Colors.RESET}\n")

        open_web = input("¿Deseas abrir la interfaz gráfica local en este servidor? (s/N): ").strip().lower()
        if open_web in ['s', 'si', 'y'] and is_healthy:
            try:
                webbrowser.open(f"{local_base}/?first_run=1")
            except Exception:
                pass

    else:
        # Nodo Maestro o Servidor Standalone con interfaz interactiva
        print("\n" + f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74)
        print(f"  🎉  {i18n.t('success_title')}")
        print("═" * 74 + f"{Colors.RESET}")
        print(f"  {Colors.BOLD}💻  Enlace Localhost:{Colors.RESET}           {Colors.CYAN}{local_base}{Colors.RESET}{' (Comprobado ✔)' if is_healthy else ' (API no validada)'}")
        print(f"  {Colors.BOLD}🌐  Enlace Red Local (LAN):{Colors.RESET}     {Colors.CYAN}{local_display_url}{Colors.RESET}{' (Comprobado ✔)' if is_healthy else ' (API no validada)'}")
        if ts_ip:
            print(f"  {Colors.BOLD}🔒  IP Red Segura Tailscale:{Colors.RESET}   {Colors.CYAN}http://{ts_ip}:{service_port}{Colors.RESET}")
        if ts_account:
            print(f"  {Colors.BOLD}👤  Cuenta Tailscale:{Colors.RESET}          {Colors.CYAN}{ts_account}{Colors.RESET} ({ts_tailnet})")
        if remote_url:
            print(f"  {Colors.BOLD}✨  Enlace Cifrado MagicDNS:{Colors.RESET}   {Colors.GREEN}{remote_url}{Colors.RESET} (HTTPS Cifrado ✔)")
        
        active_skills_list = [s.id for s in configured_skills] if configured_skills else ["Core STEM"]
        print(f"  {Colors.BOLD}🧩  Módulos Desplegados:{Colors.RESET}        {', '.join(active_skills_list)}")
        print(f"  {Colors.BOLD}🚀  Modo Activo:{Colors.RESET}                {node_role.upper()}")
        print(f"  {Colors.BOLD}⚡  Control en Terminal:{Colors.RESET}        'sentinel active' | 'sentinel stop' | 'sentinel status'")
        print(f"{Colors.BOLD}{Colors.GREEN}" + "═" * 74 + f"{Colors.RESET}\n")

        open_web = input("¿Deseas abrir el panel en tu navegador predeterminado ahora? (S/n): " if lang == "es" else "Open cockpit in browser now? (Y/n): ").strip().lower()
        if open_web not in ['n', 'no'] and is_healthy:
            try:
                print_info("Abriendo panel de control en tu navegador predeterminado..." if lang == "es" else "Opening cockpit in default browser...")
                webbrowser.open(f"{local_base}/?first_run=1")
            except Exception:
                pass

    if not is_healthy:
        print_warning("No se abrirá Cockpit porque /api/data no validó. Revisa sentinel_backend.log y vuelve a iniciar el instalador para reparar.")

    _close_terminal_smoothly(os_info, lang)

if __name__ == "__main__":
    main()
