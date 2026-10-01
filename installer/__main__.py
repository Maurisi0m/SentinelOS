"""SentinelOS - Orquestador Principal del Instalador Multiplataforma.

Uso:
  python -m installer
"""

import sys
import os
import time
from pathlib import Path

BANNER = """\033[1;36m
  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝\033[0m
  \033[1;32m[+] SentinelOS 2.0 - Sistema Operativo Cognitivo & Laboratorio STEM\033[0m
  \033[1;30m    Iniciando despliegue automatizado para estudiantes e investigadores\033[0m
"""

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

    # 2. Token y configuración criptográfica del nodo
    from installer.node_token import ensure_token
    token = ensure_token()
    print(f"[+] Token criptográfico del nodo asegurado: {token[:12]}...")

    # 3. Verificación y resolución de puertos
    from installer.port_guard import check_and_prepare_ports
    check_and_prepare_ports((8001, 8002, 3000))

    # 4. Configuración de cortafuegos
    from installer.firewall import configure_firewall
    configure_firewall()

    # 5. Accesos directos y autoarranque
    from installer.desktop_shortcut import create_desktop_shortcut
    create_desktop_shortcut("http://localhost:3000")

    from installer.autostart import configure_autostart
    configure_autostart()

    # 6. Comprobación de Tailscale opcional
    from installer.tailscale import check_tailscale
    check_tailscale()

    # 7. Inicio de servicios del laboratorio STEM
    print("\n\033[1;32m====================================================\033[0m")
    print("\033[1;32m  ¡Instalación y configuración de SentinelOS lista! \033[0m")
    print("\033[1;32m====================================================\033[0m\n")

    from installer.service_runner import start_services
    start_services(background=True)

    print("\nPuedes acceder al panel de control en:")
    print("👉 \033[1;36mhttp://localhost:3000\033[0m\n")

if __name__ == "__main__":
    main()
