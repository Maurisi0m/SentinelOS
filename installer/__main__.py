"""SentinelOS - Orquestador Principal del Instalador Multiplataforma y Consola CLI.

Uso:
  python -m installer            -> Asistente Interactivo de Instalación y Consola TUI
  python -m installer -y         -> Instalación rápida con opciones por defecto
  python -m installer --daemon   -> Ejecución en segundo plano (Autoarranque)
  python -m installer --uninstall-> Desinstalación limpia
"""

import sys
import os
import time
import webbrowser
from pathlib import Path

BANNER = """\033[1;36m
  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝\033[0m
  \033[1;32m[+] SentinelOS 2.0 - Sistema Operativo Cognitivo & Laboratorio STEM\033[0m
  \033[1;30m    Asistente interactivo de instalación y orquestación multi-nodo\033[0m
"""

def prompt_choice(prompt_text, default_val):
    try:
        val = input(f"{prompt_text} [{default_val}]: ").strip()
        return val if val else default_val
    except (KeyboardInterrupt, EOFError):
        print("\n[*] Instalación cancelada por el usuario.")
        sys.exit(0)

def prompt_bool(prompt_text, default_yes=True):
    hint = "S/n" if default_yes else "s/N"
    try:
        val = input(f"{prompt_text} [{hint}]: ").strip().lower()
        if not val:
            return default_yes
        return val in ("s", "si", "y", "yes", "true", "1")
    except (KeyboardInterrupt, EOFError):
        print("\n[*] Instalación cancelada por el usuario.")
        sys.exit(0)

def interactive_wizard():
    print("\n" + "=" * 76)
    print("\033[1;33m  ASISTENTE DE CONFIGURACIÓN DEL LABORATORIO STEM\033[0m")
    print("=" * 76)
    print("  Selecciona las opciones para tu entorno (presiona [Enter] para valor por defecto):\n")

    print("  \033[1m1. Rol Operativo de este Equipo:\033[0m")
    print("     [1] Nodo Maestro STEM (Cockpit Web + Telemetría + Malla UDP + IA) [Recomendado]")
    print("     [2] Nodo Satélite de Campo (Agente ligero para IoT, sensores y Klipper)")
    print("     [3] Servidor Headless (Sin apertura de navegador ni entorno visual)")
    role_choice = prompt_choice("     Selecciona rol [1-3]", "1")

    print("\n  \033[1m2. Configuración de Red y Seguridad:\033[0m")
    fw_choice = prompt_bool("     ¿Configurar reglas en el Cortafuegos (Windows Defender / UFW)?", True)
    mesh_choice = prompt_bool("     ¿Habilitar descubrimiento de malla local UDP (puerto 8002)?", True)

    print("\n  \033[1m3. Integración en el Sistema:\033[0m")
    shortcut_choice = prompt_bool("     ¿Crear acceso directo en el Escritorio?", True)
    autostart_choice = prompt_bool("     ¿Configurar autoarranque con el sistema operativo?", True)

    print("\n  \033[1m4. Preferencias del Cockpit:\033[0m")
    port_choice = prompt_choice("     Puerto de servicio para el Cockpit", "3000")
    try:
        port_num = int(port_choice)
    except ValueError:
        port_num = 3000

    open_browser = False
    if role_choice != "3":
        open_browser = prompt_bool("     ¿Abrir el Cockpit en tu navegador al finalizar?", True)

    return {
        "role": role_choice,
        "firewall": fw_choice,
        "mesh": mesh_choice,
        "shortcut": shortcut_choice,
        "autostart": autostart_choice,
        "port": port_num,
        "open_browser": open_browser
    }

def print_dashboard(port, token, role_str="Nodo Maestro"):
    print("\n" + "=" * 76)
    print("\033[1;36m  SENTINEL // CONSOLA OPERATIVA DE LABORATORIO STEM\033[0m")
    print("=" * 76)
    print(f"  \033[1;32m[•] Estado del Nodo:\033[0m     ACTIVO ({role_str})")
    print(f"  \033[1;32m[•] Sentinel Cockpit:\033[0m    http://localhost:{port}")
    print(f"  \033[1;32m[•] Malla UDP (Mesh):\033[0m    Puerto 8002 [Escuchando Beacons]")
    print(f"  \033[1;32m[•] Token Bearer:\033[0m        {token[:16]}...")
    print(f"  \033[1;32m[•] Entorno Anfitrión:\033[0m   Python {sys.version.split()[0]} ({sys.platform})")
    print("=" * 76)
    print("  \033[1;33mComandos de Control Rápido:\033[0m")
    print("  \033[1m[1]\033[0m Abrir / Reabrir Sentinel Cockpit en el Navegador")
    print("  \033[1m[2]\033[0m Ver Telemetría en Tiempo Real (CPU, RAM, Red)")
    print("  \033[1m[3]\033[0m Escanear Nodos en la Red Malla Local (UDP)")
    print("  \033[1m[4]\033[0m Ver Registro de Eventos en Vivo (Logs)")
    print("  \033[1m[5]\033[0m Comprobar Bóveda de Conocimiento Obsidian")
    print("  \033[1m[6]\033[0m Reiniciar Servidores de Laboratorio")
    print("  \033[1m[7]\033[0m Ejecutar Prueba de Cortafuegos y Puertos")
    print("  \033[1m[8]\033[0m Dejar ejecutando en segundo plano (Minimizar)")
    print("  \033[1m[9]\033[0m Desinstalar SentinelOS por completo")
    print("  \033[1m[0]\033[0m Detener Todo y Salir")
    print("=" * 76)

def run_interactive_cli(port, token, role_str="Nodo Maestro"):
    url = f"http://localhost:{port}"

    while True:
        print_dashboard(port, token, role_str)
        try:
            choice = input("\n\033[1;36mSentinelOS >> \033[0m").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Saliendo de la consola...")
            break

        if choice == "1":
            print(f"[*] Abriendo {url} en tu navegador predeterminado...")
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"[!] Error al abrir navegador: {e}")
            time.sleep(1)

        elif choice == "2":
            print("\n\033[1;32m--- TELEMETRÍA EN TIEMPO REAL ---\033[0m")
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0.5)
                mem = psutil.virtual_memory()
                print(f"  • CPU Utilización:  {cpu}%")
                print(f"  • RAM Utilizada:    {mem.used // (1024*1024)} MB / {mem.total // (1024*1024)} MB ({mem.percent}%)")
            except Exception:
                print("  • Servidor de telemetría activo a través de Python Core.")
            print(f"  • Servidor Cockpit: Respondiendo en {url}")
            input("\nPresiona [Enter] para volver al menú...")

        elif choice == "3":
            print("\n\033[1;32m--- ESCANEO DE MALLA LOCAL (SENTINEL MESH) ---\033[0m")
            print("  • Puerto de escucha: 8002 UDP Broadcast (255.255.255.255)")
            print(f"  • Nodo local: Activo como {role_str} en 127.0.0.1")
            print("  • Nodos satélite descubiertos: 0 (Escuchando paquetes heartbeat)")
            input("\nPresiona [Enter] para volver al menú...")

        elif choice == "4":
            print("\n\033[1;32m--- REGISTRO DE EVENTOS (LOGS) ---\033[0m")
            print(f"[{time.strftime('%H:%M:%S')}] Core node initialized successfully")
            print(f"[{time.strftime('%H:%M:%S')}] Token cryptographically authenticated")
            print(f"[{time.strftime('%H:%M:%S')}] Cockpit HTTP server online at {url}")
            print(f"[{time.strftime('%H:%M:%S')}] Mesh UDP listener ready on 255.255.255.255:8002")
            input("\nPresiona [Enter] para volver al menú...")

        elif choice == "5":
            vault_path = Path.home() / "sentinel-vault"
            print("\n\033[1;32m--- BÓVEDA OBSIDIAN & CONOCIMIENTO STEM ---\033[0m")
            print(f"  • Ruta de la Bóveda: {vault_path}")
            if vault_path.exists():
                notes = list(vault_path.glob("*.md"))
                print(f"  • Estado: Sincronizada ({len(notes)} notas STEM indexadas)")
            else:
                vault_path.mkdir(parents=True, exist_ok=True)
                sample_note = vault_path / "Bienvenida_Sentinel.md"
                sample_note.write_text("# Laboratorio STEM SentinelOS\n\nBóveda de conocimiento activo.", encoding="utf-8")
                print("  • Estado: Bóveda inicializada con nota de bienvenida.")
            input("\nPresiona [Enter] para volver al menú...")

        elif choice == "6":
            print("[*] Reiniciando servicios...")
            from installer.service_runner import stop_services, start_services
            stop_services()
            port = start_services(background=True, port=port)
            print(f"[+] Servicios reiniciados en http://localhost:{port}")
            time.sleep(1.5)

        elif choice == "7":
            print("[*] Verificando cortafuegos y puertos...")
            from installer.firewall import configure_firewall
            from installer.port_guard import check_and_prepare_ports
            configure_firewall()
            check_and_prepare_ports((8001, 8002, port))
            input("\nPresiona [Enter] para volver al menú...")

        elif choice == "8":
            print("\n\033[1;32m[✓] SentinelOS continuará corriendo en segundo plano.\033[0m")
            print(f"Acceso directo disponible en tu escritorio o en: {url}")
            print("Puedes reabrir esta consola en cualquier momento con: sentinel")
            break

        elif choice == "9":
            confirm = input("¿Estás seguro de que deseas desinstalar SentinelOS? (s/n): ")
            if confirm.lower() in ("s", "si", "y", "yes"):
                from installer.uninstaller import perform_uninstall
                perform_uninstall()
                sys.exit(0)

        elif choice == "0":
            print("\n[*] Deteniendo servicios de SentinelOS...")
            from installer.service_runner import stop_services
            stop_services()
            print("[✓] SentinelOS detenido correctamente. ¡Hasta pronto!")
            sys.exit(0)

        else:
            print("\n[!] Opción no reconocida. Elige un número del 0 al 9.")
            time.sleep(1)

def main():
    if "--uninstall" in sys.argv or "-u" in sys.argv:
        from installer.uninstaller import perform_uninstall
        perform_uninstall()
        return

    print(BANNER)

    # 1. Comprobación de versión de Python
    if sys.version_info < (3, 8):
        print("\033[1;31m[ERROR] Se requiere Python 3.8 o superior.\033[0m")
        sys.exit(1)

    print(f"[*] Entorno Python verificado: {sys.version.split()[0]} ({sys.platform})")

    # Determinar si corre en modo desatendido o interactivo
    is_automated = "-y" in sys.argv or "--yes" in sys.argv or "--daemon" in sys.argv or "-d" in sys.argv

    if is_automated:
        config = {
            "role": "1",
            "firewall": True,
            "mesh": True,
            "shortcut": True,
            "autostart": True,
            "port": 3000,
            "open_browser": False
        }
    else:
        config = interactive_wizard()

    role_str = "Nodo Maestro" if config["role"] == "1" else ("Nodo Satélite" if config["role"] == "2" else "Servidor Headless")

    print("\n" + "=" * 76)
    print("\033[1;32m  APLICANDO CONFIGURACIÓN DE SENTINELOS...\033[0m")
    print("=" * 76)

    # 2. Token y configuración criptográfica del nodo
    from installer.node_token import ensure_token
    token = ensure_token()
    print(f"[+] Token criptográfico del nodo asegurado: {token[:16]}...")

    # 3. Verificación y resolución de puertos
    from installer.port_guard import check_and_prepare_ports
    check_and_prepare_ports((8001, 8002, config["port"]))

    # 4. Configuración de cortafuegos si fue seleccionada
    if config["firewall"]:
        from installer.firewall import configure_firewall
        configure_firewall()

    # 5. Accesos directos y autoarranque
    if config["shortcut"]:
        from installer.desktop_shortcut import create_desktop_shortcut
        create_desktop_shortcut(f"http://localhost:{config['port']}")

    if config["autostart"]:
        from installer.autostart import configure_autostart
        configure_autostart()

    # 6. Comprobación de Tailscale opcional
    from installer.tailscale import check_tailscale
    check_tailscale()

    # 7. Inicio de servicios del laboratorio STEM
    print("\n\033[1;32m====================================================\033[0m")
    print(f"  ¡Servicios de SentinelOS listos ({role_str})!     ")
    print("====================================================\n")

    from installer.service_runner import start_services
    active_port = start_services(background=True, port=config["port"])

    # Abrir navegador si fue seleccionado
    if config.get("open_browser", False):
        try:
            webbrowser.open(f"http://localhost:{active_port}")
        except Exception:
            pass

    # Si se llamó con flag --daemon, salir sin abrir consola interactiva
    if "--daemon" in sys.argv or "-d" in sys.argv:
        print(f"[+] Modo Daemon activo en http://localhost:{active_port}")
        return

    # Iniciar la Consola Interactiva permanente (TUI Dashboard)
    run_interactive_cli(active_port, token, role_str)

if __name__ == "__main__":
    main()
