#!/bin/bash
set -e

PASS="Pollito92."

# 1. Escribir servicio
python3 - << 'PYEOF'
svc = """[Unit]
Description=SENTINEL Cognitive STEM OS - High Performance Local LLM Daemon
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=sentinel
Group=sentinel
WorkingDirectory=/opt/sentinel

Environment="OMP_PROC_BIND=CLOSE"
Environment="LD_LIBRARY_PATH=/opt/sentinel/bin"
Environment="MALLOC_ARENA_MAX=1"

Nice=-10

ExecStart=/opt/sentinel/bin/llama-server -m /opt/sentinel/models/sentinel-master.Q4_K_M.gguf --host 127.0.0.1 --port 8080 -t 4 -tb 4 -c 4096 -fa on -np 1 -n -1 --temp 0.15 --top-p 0.85 --top-k 40 --repeat-penalty 1.1 --min-p 0.05 -ctk q8_0 -ctv q8_0 --mmap --mlock --cont-batching --no-warmup

Restart=always
RestartSec=3
LimitMEMLOCK=infinity
LimitNOFILE=65535
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sentinel-os

[Install]
WantedBy=multi-user.target
"""
with open("/tmp/sentinel_q4.service", "w") as f:
    f.write(svc)
print("[1/4] Servicio escrito en /tmp/sentinel_q4.service")
PYEOF

# 2. Copiar con sudo -S (pass por stdin)
echo "$PASS" | sudo -S cp /tmp/sentinel_q4.service /etc/systemd/system/sentinel.service
echo "[2/4] Copiado a /etc/systemd/system/sentinel.service"

# 3. Reload y restart
echo "$PASS" | sudo -S systemctl daemon-reload
echo "$PASS" | sudo -S systemctl restart sentinel
echo "[3/4] Servicio reiniciado"

# 4. Verificar
sleep 5
STATUS=$(systemctl is-active sentinel 2>&1)
echo "[4/4] Estado: $STATUS"

# 5. Confirmar modelo cargado
echo "--- MODELO EN USO ---"
cat /etc/systemd/system/sentinel.service | grep ExecStart
