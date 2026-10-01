#!/usr/bin/env bash
# SentinelOS - Desinstalador Oficial para Linux
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${RED}==============================================================================${NC}"
echo -e "${RED}             SENTINEL OS - DESINSTALADOR OFICIAL PARA LINUX v2.0              ${NC}"
echo -e "${RED}==============================================================================${NC}"
echo ""

read -p "¿Deseas proceder con la desinstalación completa de SentinelOS? (S/n): " CONFIRM
if [[ "$CONFIRM" =~ ^[nN]$ ]]; then
    echo "Operación cancelada."
    exit 0
fi

echo -e "${CYAN}[1/4] Deteniendo y deshabilitando servicios systemd...${NC}"
sudo systemctl stop labsentinel.service sentinel.service sentinel-orchestrator.service 2>/dev/null || true
sudo systemctl disable labsentinel.service sentinel.service sentinel-orchestrator.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/labsentinel.service /etc/systemd/system/sentinel.service /etc/systemd/system/sentinel-orchestrator.service 2>/dev/null || true
sudo rm -rf /etc/systemd/system/sentinel*.service.d 2>/dev/null || true
sudo systemctl daemon-reload 2>/dev/null || true

# Terminar procesos restantes en el puerto 8001
fuser -k 8001/tcp 2>/dev/null || true
pkill -9 -f "labsentinel_backend|main:app" 2>/dev/null || true

echo -e "${CYAN}[2/4] Removiendo regla de cortafuegos (UFW / Firewalld)...${NC}"
if command -v ufw >/dev/null 2>&1; then
    sudo ufw delete allow 8001/tcp 2>/dev/null || true
elif command -v firewall-cmd >/dev/null 2>&1; then
    sudo firewall-cmd --remove-port=8001/tcp --permanent 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
fi

echo -e "${CYAN}[3/4] Eliminando accesos directos (.desktop)...${NC}"
rm -f "$HOME/Desktop/SentinelOS.desktop" "$HOME/Desktop/sentinelos.desktop" 2>/dev/null || true
rm -f "$HOME/.local/share/applications/SentinelOS.desktop" 2>/dev/null || true
sudo rm -f "/usr/share/applications/SentinelOS.desktop" 2>/dev/null || true

read -p "¿Deseas eliminar también el entorno virtual (.venv)? (s/N): " PURGE
if [[ "$PURGE" =~ ^[sS]$ ]]; then
    echo -e "${CYAN}[4/4] Eliminando entorno virtual .venv...${NC}"
    rm -rf "$(dirname "$0")/.venv" "$(dirname "$0")/config/node_auth.json" "$(dirname "$0")/config/mesh_peers.json" 2>/dev/null || true
else
    echo -e "${CYAN}[4/4] Archivos de código y .venv preservados.${NC}"
fi

echo ""
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}        DESINSTALACIÓN COMPLETADA EXITOSAMENTE EN LINUX                       ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo "SentinelOS ha sido removido del sistema y el puerto 8001 está liberado."
