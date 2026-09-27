#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, time, subprocess, socket
from .banner import ASCII_BANNER, Colors, print_header, print_success, print_warning, print_error, print_info
from .i18n import I18n
from .skills import AVAILABLE_SKILLS
from .tailscale import setup_tailscale_interactive

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(ASCII_BANNER)

    # -------------------------------------------------------------
    # PASO 1: SELECCIÓN DE IDIOMA
    # -------------------------------------------------------------
    print_header("Selección de Idioma / Language Selection", "1/5")
    print(f"  {Colors.BOLD}[1]{Colors.RESET} Español (Latinoamérica / España)")
    print(f"  {Colors.BOLD}[2]{Colors.RESET} English (US / Global)\n")
    lang_choice = input("Selecciona una opción / Select an option [1]: ").strip()
    lang = "en" if lang_choice == "2" else "es"
    i18n = I18n(lang)

    print_success(f"Idioma establecido: {'Español' if lang == 'es' else 'English'}\n")
    time.sleep(1)

    # -------------------------------------------------------------
    # PASO 2: CATÁLOGO DE SKILLS & MÓDULOS
    # -------------------------------------------------------------
    print_header(i18n.t("step2"), "2/5")
    print(i18n.t("step2_desc") + "\n")

    selected_skills = []
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

    # Ejecutar submenús interactivos para cada skill seleccionada
    configured_skills = []
    for idx in chosen_indices:
        if 1 <= idx <= len(AVAILABLE_SKILLS):
            skill_instance = AVAILABLE_SKILLS[idx - 1]()
            skill_instance.configure_interactive(lang)
            configured_skills.append(skill_instance)

    # -------------------------------------------------------------
    # PASO 3: TÉRMINOS Y RESPONSABILIDAD ÉTICA
    # -------------------------------------------------------------
    print_header(i18n.t("step3"), "3/5")
    print(f"{Colors.YELLOW}{i18n.t('terms_text')}{Colors.RESET}\n")
    agree = input(i18n.t("accept_terms")).strip().lower()
    if agree not in ['s', 'si', 'y', 'yes', '']:
        print_error(i18n.t("terms_rejected"))
        sys.exit(1)

    print_success("Términos aceptados.\n")
    time.sleep(1)

    # -------------------------------------------------------------
    # PASO 4: TAILSCALE ZERO-CONFIG + QR
    # -------------------------------------------------------------
    print_header(i18n.t("step4"), "4/5")
    ts_ask = input(i18n.t("tailscale_prompt")).strip().lower()
    remote_url = ""
    if ts_ask != 'n':
        remote_url = setup_tailscale_interactive(lang)

    # -------------------------------------------------------------
    # PASO 5: DESPLIEGUE DOCKER Y SERVICIOS
    # -------------------------------------------------------------
    print_header(i18n.t("step5"), "5/5")
    print_info(i18n.t("deploying"))

    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:8001"

    # Verificar si docker-compose está disponible
    has_docker = subprocess.run("docker compose version", shell=True, capture_output=True).returncode == 0
    if has_docker:
        print_info("Levantando contenedores optimizados con Docker Compose...")
        subprocess.run("docker compose up -d", shell=True)
        print_success("Contenedores desplegados correctamente.")
    else:
        print_warning("Docker no detectado. Utilizando servicios nativos de sistema.")

    # -------------------------------------------------------------
    # TARJETA FINAL DE RESUMEN
    # -------------------------------------------------------------
    print("\n" + "=" * 74)
    print(f"{Colors.BOLD}{Colors.GREEN}  {i18n.t('success_title')}{Colors.RESET}")
    print("=" * 74)
    print(f"  {Colors.BOLD}🌐 {i18n.t('access_local')}{Colors.RESET}   {Colors.CYAN}{local_url}{Colors.RESET}")
    if remote_url:
        print(f"  {Colors.BOLD}🔒 {i18n.t('access_remote')}{Colors.RESET}  {Colors.GREEN}{remote_url}{Colors.RESET}")
    print(f"  {Colors.BOLD}📊 Módulos Activos:{Colors.RESET}      Core STEM, Cockpit Web, " + ", ".join(s.id for s in configured_skills))
    print(f"  {Colors.BOLD}💻 Comando para unir otros servidores (Nodos Satélite):{Colors.RESET}")
    print(f"     curl -fsSL {local_url}/api/mesh/join.sh | bash")
    print("=" * 74 + "\n")

if __name__ == "__main__":
    main()
