import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.68.68', username='mauro', password='Pollito92.')

sftp = client.open_sftp()
with sftp.open("/tmp/debug_test.py", "w") as f:
    f.write('''import sys
sys.path.append("/home/mauro/labsentinel-web/backend")
import sentinel_service
from self_learning_engine import CommandMemoryManager

msg = "Hola!"
print("is_greeting:", sentinel_service.is_greeting(msg))
print("vault_ctx:", repr(sentinel_service.get_vault_context(msg)))

cmd_mem = CommandMemoryManager("/home/mauro/labsentinel-web/backend")
print("cmd_mem_ctx:", repr(cmd_mem.get_mastery_context_prompt(msg)))
''')
sftp.close()

stdin, stdout, stderr = client.exec_command('/home/mauro/labsentinel-web/backend/venv/bin/python3 /tmp/debug_test.py')
print("--- STDOUT ---")
print(stdout.read().decode())
print("--- STDERR ---")
print(stderr.read().decode())
client.close()
