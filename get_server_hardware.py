import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.68.68', username='mauro', password='Pollito92.')

cmds = [
    ("MODEL", "cat /sys/devices/virtual/dmi/id/product_name || true"),
    ("CPU", "lscpu"),
    ("RAM", "free -m"),
    ("DISK", "df -h /"),
    ("OS", "cat /etc/os-release"),
    ("UPTIME", "uptime -p")
]

for name, cmd in cmds:
    stdin, stdout, stderr = client.exec_command(f"echo Pollito92. | sudo -S {cmd}")
    print(f"=== {name} ===")
    print(stdout.read().decode()[:400])

client.close()
