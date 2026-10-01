#!/usr/bin/env python3
"""Benchmark de velocidad del modelo Q4_K_M en produccion"""
import paramiko, json, time

HOST = "100.113.156.109"
USER = "mauro"
PASS = "Pollito92."

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS)

cmd = r"""python3 -c "
import urllib.request, json, time

payload = {
    'messages': [{'role': 'user', 'content': 'Define brevemente que es un controlador PID en control automatico. Describe sus tres terminos.'}],
    'temperature': 0.15,
    'top_p': 0.85,
    'min_p': 0.05,
    'repeat_penalty': 1.1,
    'max_tokens': 150,
    'stream': False
}

req = urllib.request.Request(
    'http://127.0.0.1:8080/v1/chat/completions',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

t0 = time.time()
with urllib.request.urlopen(req, timeout=120) as r:
    data = json.loads(r.read().decode('utf-8'))
elapsed = time.time() - t0

c = data['choices'][0]
usage = data.get('usage', {})
comp_tokens = usage.get('completion_tokens', '?')
tps = round(int(comp_tokens) / elapsed, 2) if isinstance(comp_tokens, int) else '?'

print(f'TIEMPO: {elapsed:.2f}s')
print(f'TOKENS GENERADOS: {comp_tokens}')
print(f'VELOCIDAD: {tps} t/s')
print(f'FINISH: {c[\"finish_reason\"]}')
print('---')
print(c['message']['content'][:500])
"
"""

_, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
client.close()

print(out)
if err:
    print("[STDERR]", err[:300])
