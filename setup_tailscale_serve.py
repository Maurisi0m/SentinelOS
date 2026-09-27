#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configura Tailscale Serve en labsentinel para tener una URL unica y permanente:

  https://labsentinel.tailc83bd7.ts.net/

Sin IP, sin puerto, HTTPS automatico, acceso solo via Tailscale (gratis).
Ejecutar: uv run python setup_tailscale_serve.py
"""

import paramiko
import sys
import time
import io

# Forzar UTF-8 en la salida de la consola Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Conexión ────────────────────────────────────────────────────────────────
HOST = "labsentinel.tailc83bd7.ts.net"   # Dominio permanente MagicDNS
USER = "mauro"
PASS = "Pollito92."
FRONTEND_PORT = 8001

FINAL_URL = f"https://labsentinel.tailc83bd7.ts.net/"
# ────────────────────────────────────────────────────────────────────────────


def ssh_run(client, cmd, desc="", sudo=False):
    """Ejecuta un comando SSH y devuelve stdout."""
    if desc:
        print(f"\n  ▶ {desc}")
    full_cmd = cmd if not sudo else f"echo '{PASS}' | sudo -S {cmd}"
    stdin, stdout, stderr = client.exec_command(full_cmd, timeout=30)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        for line in out.splitlines():
            print(f"    {line}")
    if err and "[sudo]" not in err and "password" not in err.lower():
        for line in err.splitlines():
            print(f"    [stderr] {line}")
    return out, err


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          SENTINEL — Configuración de Dominio Único              ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print(f"║  URL objetivo: https://labsentinel.tailc83bd7.ts.net/           ║")
    print("║  Protocolo   : HTTPS automático (Tailscale Serve)               ║")
    print("║  Acceso      : Solo clientes con Tailscale conectado (privado)   ║")
    print("║  Costo       : $0 — 100% gratis                                 ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    # ── 1. Conectar SSH ─────────────────────────────────────────────────────
    print("[1/6] Conectando SSH al servidor...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=22, username=USER, password=PASS, timeout=15)
        print("      ✅ SSH conectado")
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False

    # ── 2. Verificar Tailscale instalado ────────────────────────────────────
    print("\n[2/6] Verificando Tailscale en el servidor...")
    out, _ = ssh_run(client, "tailscale version", "tailscale version")
    if not out:
        print("      ❌ Tailscale no está instalado. Instalando...")
        ssh_run(client,
            "curl -fsSL https://tailscale.com/install.sh | sh",
            "Instalando Tailscale", sudo=False)
    else:
        print(f"      ✅ Tailscale {out.splitlines()[0]} disponible")

    # ── 3. Estado actual de tailscale serve ─────────────────────────────────
    print("\n[3/6] Verificando estado actual de Tailscale Serve...")
    out, _ = ssh_run(client,
        "echo '" + PASS + "' | sudo -S tailscale serve status 2>&1",
        "Estado actual")
    if "not running" in out.lower() or "no serve config" in out.lower() or not out:
        print("      ℹ️  Serve no configurado aún — lo activamos ahora")
    else:
        print("      ℹ️  Serve ya tiene configuración previa")

    # ── 4. Activar Tailscale Serve ──────────────────────────────────────────
    print(f"\n[4/6] Activando Tailscale Serve en puerto {FRONTEND_PORT}...")
    # Reset primero para evitar conflictos
    ssh_run(client,
        f"echo '{PASS}' | sudo -S tailscale serve reset 2>&1",
        "Limpiando configuración previa")
    time.sleep(1)

    # Configurar serve: localhost:8001 → HTTPS port 443
    out, err = ssh_run(client,
        f"echo '{PASS}' | sudo -S tailscale serve --bg {FRONTEND_PORT} 2>&1",
        f"Mapeando localhost:{FRONTEND_PORT} → HTTPS 443")

    time.sleep(2)

    # ── 5. Verificar configuración final ────────────────────────────────────
    print("\n[5/6] Verificando configuración final...")
    out, _ = ssh_run(client,
        f"echo '{PASS}' | sudo -S tailscale serve status 2>&1",
        "Estado de Tailscale Serve")

    # ── 6. Verificar que el backend local responde ──────────────────────────
    print("\n[6/6] Verificando que el frontend responde en localhost...")
    out, _ = ssh_run(client,
        f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{FRONTEND_PORT}/",
        f"curl http://localhost:{FRONTEND_PORT}/")
    if out.strip() == "200":
        print("      ✅ Frontend responde HTTP 200")
    else:
        print(f"      ⚠️  Código HTTP: {out or 'sin respuesta'}")
        print(f"         Asegúrate de que el servicio backend está activo:")
        print(f"         sudo systemctl status labsentinel.service")

    client.close()

    # ── Resultado final ─────────────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                    ✅ CONFIGURACIÓN COMPLETA                    ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║                                                                  ║")
    print("║  🌐 Tu dominio único permanente:                                 ║")
    print("║                                                                  ║")
    print("║     https://labsentinel.tailc83bd7.ts.net/                      ║")
    print("║                                                                  ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║  • Sin IP · Sin puerto · HTTPS automático                        ║")
    print("║  • Requiere Tailscale activo en el dispositivo cliente           ║")
    print("║  • Funciona en cualquier red (WiFi, 4G, hotspot, etc.)           ║")
    print("║  • Gratis para siempre en el plan personal de Tailscale          ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
