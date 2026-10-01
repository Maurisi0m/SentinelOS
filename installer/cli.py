import sys
import os
import subprocess
import shutil
from pathlib import Path

def print_help():
    print("""
\033[1;36m====================================================\033[0m
\033[1;32m  SENTINEL // STEM Cognitive OS - CLI Global\033[0m
\033[1;36m====================================================\033[0m
Uso: sentinel [comando]

Comandos disponibles:
  status     Muestra el estado operativo de los servicios y puertos
  active     Inicia los servicios del laboratorio STEM en segundo plano
  logs       Visualiza el flujo de telemetría y eventos en vivo
  restart    Reinicia los servicios del nodo
  stop       Detiene los procesos de SentinelOS
  uninstall  Desinstalación completa y reversión limpia
""")

def handle_cli():
    args = sys.argv[1:]
    if not args:
        # Si se ejecuta 'sentinel' sin argumentos, abrir la consola interactiva completa
        from installer.node_token import ensure_token
        from installer.__main__ import run_interactive_cli
        token = ensure_token()
        run_interactive_cli(3000, token)
        return

    if args[0] in ("-h", "--help", "help"):
        print_help()
        return

    cmd = args[0].lower()
    if cmd == "status":
        print("\033[1;32m[+] SentinelOS STEM Lab Status:\033[0m")
        print("  • Servidor Cockpit / API: Activo")
        print("  • Bóveda Obsidian: Sincronizada")
        print("  • Red Mesh: Escuchando")
    elif cmd == "active":
        print("[*] Iniciando servicios de SentinelOS...")
        from installer.service_runner import start_services
        start_services()
    elif cmd == "stop":
        print("[*] Deteniendo servicios de SentinelOS...")
        from installer.service_runner import stop_services
        stop_services()
    elif cmd == "restart":
        print("[*] Reiniciando servicios...")
        from installer.service_runner import stop_services, start_services
        stop_services()
        start_services()
    elif cmd == "logs":
        print("[*] Conectando con flujo de telemetría...")
        import urllib.request
        try:
            with urllib.request.urlopen("http://localhost:3000/api/logs", timeout=2) as resp:
                print(resp.read().decode())
        except Exception:
            print("[!] No se pudo contactar el servidor local en puerto 3000.")
    elif cmd == "uninstall":
        from installer.uninstaller import perform_uninstall
        perform_uninstall()
    else:
        print(f"[!] Comando desconocido: {cmd}")
        print_help()

if __name__ == "__main__":
    handle_cli()
