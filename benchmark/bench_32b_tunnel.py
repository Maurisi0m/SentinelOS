#!/usr/bin/env python3
"""
Benchmark 3.2B en servidor via SSH tunnel (localhost:18080 -> servidor:8080)
Una sola pregunta para medir t/s real del 3.2B con el nuevo Q4_K_M optimizado
"""
import urllib.request, json, time

TUNNEL_URL = "http://127.0.0.1:18080/v1/chat/completions"

SYSTEM = (
    "SENTINEL, mentor cognitivo STEM. Responde en espanol con rigor cientifico. "
    "Encierra conceptos clave en [[Concepto]]. Cero emojis. Solo temas STEM."
)

QUESTIONS = [
    "Explica que es un controlador PID y describe sus tres terminos P, I y D con ejemplos.",
    "Como funciona el protocolo I2C a nivel de senales electricas? Describe SCL y SDA.",
    "Que es la complejidad temporal O(n log n) y en que algoritmos aparece?",
    "Explica la diferencia entre proceso y hilo en Linux.",
    "Que es Q-Learning en Reinforcement Learning?",
]

def infer(question):
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question}
        ],
        "temperature": 0.15, "top_p": 0.85, "min_p": 0.05,
        "repeat_penalty": 1.1, "max_tokens": 250, "stream": False,
    }
    req = urllib.request.Request(
        TUNNEL_URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode())
    elapsed = time.time() - t0
    usage = data.get("usage", {})
    tok = usage.get("completion_tokens", 0)
    tps = round(tok / elapsed, 2) if elapsed > 0 else 0
    finish = data["choices"][0].get("finish_reason", "?")
    print(f"  {elapsed:.2f}s | {tok} tok | {tps} t/s | [{finish}]")
    print(f"  >> {data['choices'][0]['message']['content'][:200]}")
    return tps

tps_list = []
print("="*70)
print("BENCHMARK 3.2B (i5-4310U) via SSH tunnel 127.0.0.1:18080")
print("="*70)
for i, q in enumerate(QUESTIONS, 1):
    print(f"\n[{i}/{len(QUESTIONS)}] {q[:65]}...")
    try:
        tps_list.append(infer(q))
    except Exception as e:
        print(f"  ERROR: {e}")

if tps_list:
    print(f"\n{'='*70}")
    print(f"PROMEDIO 3.2B: {round(sum(tps_list)/len(tps_list), 2)} t/s")
    print(f"(1B en RTX 5060 promedio: 37.02 t/s)")
    ratio = round(37.02 / (sum(tps_list)/len(tps_list)), 2) if tps_list else "?"
    print(f"Factor de velocidad 1B/3.2B: {ratio}x")
    print("="*70)
