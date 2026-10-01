#!/usr/bin/env bash
# ==============================================================================
# Sentinel Mesh Node Join Script
# Ejecuta este script en cualquier servidor o máquina satélite de tu laboratorio
# para conectarlo en vivo con tu Sentinel Core.
# ==============================================================================
set -e

CORE_URL="${CORE_URL:-http://127.0.0.1:8001}"
TOKEN=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --token) TOKEN="$2"; shift ;;
        --core) CORE_URL="$2"; shift ;;
        *) echo "Parámetro desconocido: $1"; exit 1 ;;
    esac
    shift
done

echo "[*] Uniendo este servidor al Sentinel Mesh..."
echo "[*] Core: $CORE_URL"

mkdir -p /opt/sentinel-mesh
curl -fsSL "$CORE_URL/mesh/sentinel_agent.py" -o /opt/sentinel-mesh/sentinel_agent.py || cp sentinel_agent.py /opt/sentinel-mesh/ 2>/dev/null

cat << EOF > /etc/systemd/system/sentinel-agent.service
[Unit]
Description=Sentinel Mesh Satellite Telemetry Agent
After=network.target

[Service]
Type=simple
User=root
Environment="SENTINEL_CORE_URL=$CORE_URL"
Environment="SENTINEL_MESH_TOKEN=$TOKEN"
ExecStart=/usr/bin/python3 /opt/sentinel-mesh/sentinel_agent.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now sentinel-agent.service

echo "✔ ¡Servidor satélite vinculado y transmitiendo métricas a Sentinel Core!"
