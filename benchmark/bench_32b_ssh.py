#!/usr/bin/env python3
"""Corre el benchmark del 3.2B directamente en el servidor via SSH"""
import paramiko, json, time

HOST = "100.113.156.109"
USER = "mauro"
PASS = "Pollito92."

QUESTIONS = [
    "Explica que es un controlador PID y describe sus tres terminos P, I y D.",
    "Como funciona el protocolo I2C a nivel de senales electricas? Describe SCL y SDA.",
    "Que es la complejidad temporal O(n log n) y en que algoritmos aparece?",
    "Explica la diferencia entre proceso y hilo en Linux.",
    "Que es Q-Learning en Reinforcement Learning?",
]

SCRIPT = r"""
import urllib.request, json, time

SYSTEM = "SENTINEL, mentor STEM. Responde en espanol con rigor cientifico. Encierra conceptos clave en [[Concepto]]. Cero emojis."

questions = """ + json.dumps(QUESTIONS) + r"""

results = []
for q in questions:
    payload = {
        "messages": [{"role":"system","content":SYSTEM},{"role":"user","content":q}],
        "temperature": 0.15, "top_p": 0.85, "min_p": 0.05,
        "repeat_penalty": 1.1, "max_tokens": 250, "stream": False
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type":"application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            data = json.loads(r.read().decode())
        elapsed = time.time() - t0
        tok = data.get("usage",{}).get("completion_tokens",0)
        tps = round(tok/elapsed, 2) if elapsed>0 else 0
        finish = data["choices"][0].get("finish_reason","?")
        ans = data["choices"][0]["message"]["content"][:200]
        print(f"OK|{elapsed:.2f}|{tok}|{tps}|{finish}|{ans[:80]}")
        results.append(tps)
    except Exception as e:
        print(f"ERR|{e}")

if results:
    avg = round(sum(results)/len(results), 2)
    print(f"AVG_TPS|{avg}")
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS)

print("="*70)
print("BENCHMARK 3.2B Q4_K_M (i5-4310U) - Ejecutado directamente en servidor")
print("="*70)

cmd = f"python3 -c {repr(SCRIPT)}"
_, stdout, stderr = client.exec_command(cmd, timeout=600)

tps_list = []
for i, line in enumerate(stdout, 1):
    line = line.strip()
    if line.startswith("OK|"):
        parts = line.split("|")
        elapsed, tok, tps, finish = parts[1], parts[2], parts[3], parts[4]
        preview = parts[5] if len(parts) > 5 else ""
        q_preview = QUESTIONS[i-1][:55] if i <= len(QUESTIONS) else "?"
        print(f"\n[{i}/{len(QUESTIONS)}] {q_preview}...")
        print(f"  {elapsed}s | {tok} tok | {tps} t/s | [{finish}]")
        print(f"  >> {preview}")
        tps_list.append(float(tps))
    elif line.startswith("AVG_TPS|"):
        avg_32b = float(line.split("|")[1])
        print(f"\n{'='*70}")
        print(f"RESUMEN COMPARATIVO FINAL")
        print(f"  3.2B Q4_K_M (i5-4310U CPU) : {avg_32b} t/s promedio")
        print(f"  1B  Q4_K_M (RTX 5060  GPU) : 37.02 t/s promedio")
        factor = round(37.02 / avg_32b, 2) if avg_32b > 0 else "?"
        print(f"  Factor de velocidad 1B/3.2B: {factor}x mas rapido")
        print(f"{'='*70}")
    elif line.startswith("ERR|"):
        print(f"  ERROR: {line}")

client.close()
