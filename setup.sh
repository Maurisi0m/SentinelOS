#!/usr/bin/env bash
# ==============================================================================
# SentinelOS Universal Installer Bootstrap (Linux / macOS v2.5)
# Auto-Detección, Auto-Reparación de Entornos Virtuales y Despliegue Autónomo
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$EUID" -ne 0 ] && [ -z "$VIRTUAL_ENV" ]; then
    SUDO="sudo"
else
    SUDO=""
fi

echo -e "\n\033[1;36m====================================================================\033[0m"
echo -e "\033[1;36m       SENTINEL OS - ASISTENTE DE INSTALACIÓN UNIVERSAL\033[0m"
echo -e "\033[0;36m  Auto-Detección de Sistema, Entornos Aislados y Auto-Reparación\033[0m"
echo -e "\033[1;36m====================================================================\033[0m\n"

# 1. Verificar presencia de Python 3
if ! command -v python3 &>/dev/null; then
    echo "[!] Python 3 no detectado. Auto-reparación: Instalando paquetes base..."
    if command -v apt-get &>/dev/null; then
        $SUDO apt-get update && $SUDO apt-get install -y python3 python3-pip python3-venv curl git
    elif command -v dnf &>/dev/null; then
        $SUDO dnf install -y python3 python3-pip curl git
    elif command -v pacman &>/dev/null; then
        $SUDO pacman -Sy --noconfirm python python-pip curl git
    elif command -v zypper &>/dev/null; then
        $SUDO zypper install -y python3 python3-pip curl git
    elif command -v apk &>/dev/null; then
        $SUDO apk add python3 py3-pip python3-dev git curl
    elif command -v brew &>/dev/null; then
        brew install python git curl
    fi
fi

# 2. Asegurar que python3-venv esté presente en Debian / Ubuntu / Kali
if command -v apt-get &>/dev/null; then
    if ! dpkg -s python3-venv &>/dev/null; then
        echo "[*] Auto-reparación: Instalando paquete python3-venv del sistema para evitar bloqueos PEP 668..."
        $SUDO apt-get update -qq && $SUDO apt-get install -y -qq python3-venv python3-pip || true
    fi
fi

# 3. Auto-Reparación de Entorno Virtual Aislado (.venv)
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python3"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[*] Auto-reparación: Creando entorno virtual aislado (.venv)..."
    echo "    (Garantiza instalación limpia de dependencias sin conflictos de sistema)"
    python3 -m venv "$VENV_DIR" || {
        echo "[!] Falló python3 -m venv nativo. Intentando auto-reparar con módulo virtualenv..."
        python3 -m pip install --user virtualenv 2>/dev/null || true
        python3 -m virtualenv "$VENV_DIR" || true
    }
fi

# 4. Asegurar pip funcional dentro del venv
if [ -f "$VENV_PYTHON" ]; then
    echo -e "\033[1;32m[OK] Entorno virtual activo: $VENV_DIR\033[0m"
    if ! "$VENV_PYTHON" -m pip --version &>/dev/null; then
        echo "[*] Auto-reparación: Inicializando gestor pip interno con ensurepip..."
        "$VENV_PYTHON" -m ensurepip --upgrade &>/dev/null || true
    fi

    # Actualizar herramientas de empaquetado
    echo "[*] Verificando herramientas de construcción (pip, wheel, setuptools)..."
    "$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel -q --prefer-binary || true

    # 5. Ejecutar instalador de SentinelOS dentro del entorno virtual seguro
    PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -m installer
else
    echo "[!] Aviso: No se pudo crear el entorno virtual aislado. Continuando con Python del sistema..."
    PYTHONPATH="$SCRIPT_DIR" python3 -m installer
fi
