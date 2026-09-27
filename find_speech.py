import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("100.113.156.109", username="mauro", password="Pollito92.")

remote_py = """
with open('/home/mauro/labsentinel-web/frontend/dist/assets/index-DuObCxWb.js', 'r', encoding='utf-8') as f:
    s = f.read()

idx = s.find('speechSynthesis.speak')
print(s[idx-900:idx-500])
"""

sftp = client.open_sftp()
with sftp.file('/tmp/find_speech.py', 'w') as f:
    f.write(remote_py)
sftp.close()

stdin, stdout, stderr = client.exec_command("python3 /tmp/find_speech.py")
print(stdout.read().decode())
client.close()
