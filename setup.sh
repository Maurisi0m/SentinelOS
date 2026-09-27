#!/usr/bin/env bash
# ==============================================================================
# SentinelOS Universal Installer Bootstrap (Linux / macOS)
# ==============================================================================
set -e

# Asegurar permisos de superusuario si es necesario
if [ "$EUID" -ne 0 ] && [ -z "$VIRTUAL_ENV" ]; then
    SUDO="sudo"
else
    SUDO=""
fi

echo "[*] Verificando dependencias base (Python 3, Git, Curl)..."

if ! command -v python3 &>/dev/null; then
    echo "[!] Python 3 no detectado. Instalando..."
    if command -v apt-get &>/dev/null; then
        $SUDO apt-get update && $SUDO apt-get install -y python3 python3-pip python3-venv curl git
    elif command -v dnf &>/dev/null; then
        $SUDO dnf install -y python3 python3-pip curl git
    elif command -v pacman &>/dev/null; then
        $SUDO pacman -Sy --noconfirm python python-pip curl git
    fi
fi

# Lanzar asistente de instalación interactivo
PYTHONPATH=. python3 -m installer
