import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.68.68', username='mauro', password='Pollito92.')

cmd = 'export PATH="/home/mauro/.nvm/versions/node/v20.20.2/bin:$PATH" && cd /home/mauro/labsentinel-web/frontend && npm run build'
stdin, stdout, stderr = client.exec_command(f'bash -c \'{cmd}\'')

print("--- STDOUT ---")
print(stdout.read().decode())
print("--- STDERR ---")
print(stderr.read().decode())
client.close()
