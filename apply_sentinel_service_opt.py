import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("192.168.68.68", port=22, username="mauro", password="Pollito92.")

unit_content = """[Unit]
Description=SENTINEL Cognitive STEM OS - High Performance Local LLM Daemon
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=sentinel
Group=sentinel
WorkingDirectory=/opt/sentinel

Environment="OMP_PROC_BIND=CLOSE"
Environment="LD_LIBRARY_PATH=/opt/sentinel/bin:${LD_LIBRARY_PATH}"

ExecStart=/opt/sentinel/bin/llama-server \\
    -m /opt/sentinel/models/sentinel-pure-stem-1b.Q4_K_M.gguf \\
    --host 127.0.0.1 \\
    --port 8080 \\
    -t 4 \\
    -tb 4 \\
    -c 4096 \\
    -np 1 \\
    -n -1 \\
    -fa on \\
    -b 512 \\
    -ub 512 \\
    --cache-reuse 64 \\
    --cache-prompt \\
    -ctk f16 \\
    -ctv f16 \\
    --load-mode mmap+mlock \\
    --cont-batching

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

stdin, stdout, stderr = client.exec_command("cat > /tmp/sentinel.service.new")
stdin.write(unit_content)
stdin.close()
stdout.read()

cmd = (
    "echo 'Pollito92.' | sudo -S cp /tmp/sentinel.service.new /etc/systemd/system/sentinel.service && "
    "echo 'Pollito92.' | sudo -S systemctl daemon-reload && "
    "echo 'Pollito92.' | sudo -S systemctl restart sentinel.service && "
    "systemctl is-active sentinel.service"
)
stdin, stdout, stderr = client.exec_command(cmd)
print("Service Status:", stdout.read().decode('utf-8'))
client.close()
