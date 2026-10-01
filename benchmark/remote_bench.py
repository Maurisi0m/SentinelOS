import urllib.request, json, time

SYSTEM = "SENTINEL, mentor STEM. Responde en espanol con rigor cientifico. Encierra conceptos clave en [[Concepto]]. Cero emojis."

questions = [
    "Explica que es un controlador PID y describe sus tres terminos P, I y D.",
    "Como funciona el protocolo I2C a nivel de senales electricas? Describe SCL y SDA.",
    "Que es la complejidad temporal O(n log n) y en que algoritmos aparece?",
    "Explica la diferencia entre proceso y hilo en Linux.",
    "Que es Q-Learning en Reinforcement Learning?",
]

results = []
for i, q in enumerate(questions, 1):
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
        ans = data["choices"][0]["message"]["content"][:120]
        print(f"RESULT|{i}|{elapsed:.2f}|{tok}|{tps}|{finish}|{ans}")
        results.append(tps)
    except Exception as e:
        print(f"ERR|{i}|{e}")

if results:
    avg = round(sum(results)/len(results), 2)
    print(f"AVG|{avg}|{len(results)}")
