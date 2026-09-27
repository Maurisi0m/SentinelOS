#!/usr/bin/env python3
"""
SENTINEL Benchmark Comparativo v2
- Levanta llama-server.exe local con el 1B en RTX 5060 (puerto 8081)
- Consulta el 3.2B en el servidor remoto (puerto 8080 via SSH tunnel o Tailscale)
- Compara t/s, latencia y calidad en 10 preguntas STEM
"""
import subprocess, json, time, os, sys, urllib.request, urllib.error, signal

BASE      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Sentinel root
SRV_EXE   = os.path.join(BASE, "export", "bin", "llama-server.exe")
MODEL_1B  = os.path.join(BASE, "models", "llama-3.2-1b", "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
REPORT    = os.path.join(BASE, "benchmark", "comparison_1b_vs_32b.json")
LOCAL_URL = "http://127.0.0.1:8081/v1/chat/completions"
REMOTE_URL = "http://127.0.0.1:8080/v1/chat/completions"  # Via SSH tunnel

SYSTEM = (
    "SENTINEL, mentor cognitivo STEM. Responde en espanol con rigor cientifico. "
    "Encierra conceptos clave en [[Concepto]]. Cero emojis. Solo temas STEM."
)

QUESTIONS = [
    "Explica que es un controlador PID y describe sus tres terminos P, I y D con ejemplos.",
    "Como funciona el protocolo I2C a nivel de senales electricas? Describe SCL y SDA.",
    "Que es la complejidad temporal O(n log n) y en que algoritmos aparece? Da un ejemplo.",
    "Explica la diferencia entre un proceso y un hilo en sistemas operativos Linux.",
    "Que es el aprendizaje por refuerzo (Reinforcement Learning) y como funciona Q-Learning?",
    "Como se configura una direccion IP estatica en Ubuntu Server via netplan?",
    "Explica el protocolo MQTT y por que es eficiente para dispositivos IoT.",
    "Que es un puntero en C y cual es la diferencia entre malloc y calloc?",
    "Describe el funcionamiento de una red neuronal convolucional (CNN) paso a paso.",
    "Que es el protocolo TCP y como garantiza la entrega ordenada de paquetes?",
]

os.makedirs(os.path.dirname(REPORT), exist_ok=True)

def wait_server(url, timeout=30):
    """Espera hasta que llama-server responda en /health"""
    health = url.replace("/v1/chat/completions", "/health")
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(health, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False

def infer(url: str, question: str, max_tokens: int = 250) -> dict:
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": question}
        ],
        "temperature": 0.15,
        "top_p": 0.85,
        "min_p": 0.05,
        "repeat_penalty": 1.1,
        "max_tokens": max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode("utf-8"))
        elapsed = time.time() - t0
        usage   = data.get("usage", {})
        comp_tokens = usage.get("completion_tokens", 0)
        tps = round(comp_tokens / elapsed, 2) if elapsed > 0 and comp_tokens > 0 else 0
        answer = data["choices"][0]["message"]["content"]
        finish = data["choices"][0].get("finish_reason", "?")
        return {
            "elapsed_s": round(elapsed, 2),
            "tokens": comp_tokens,
            "tps": tps,
            "finish": finish,
            "response": answer[:500],
        }
    except Exception as e:
        return {"elapsed_s": 0, "tokens": 0, "tps": 0, "finish": "error", "response": str(e)[:200]}

def main():
    print("=" * 80)
    print("BENCHMARK: Llama-3.2-1B Q4_K_M (RTX 5060)  vs  sentinel-3.2B Q4_K_M (i5)")
    print("=" * 80)

    # ── Levantar servidor local 1B ────────────────────────────────────────────
    print(f"\n[SETUP] Iniciando llama-server.exe con 1B en GPU...")
    srv_cmd = [
        SRV_EXE,
        "-m", MODEL_1B,
        "--host", "127.0.0.1",
        "--port", "8081",
        "-ngl", "99",          # Todas las capas en RTX 5060
        "-t", "4",
        "-c", "4096",
        "-n", "-1",
        "--temp", "0.15",
        "--top-p", "0.85",
        "--top-k", "40",
        "--repeat-penalty", "1.1",
        "-fa", "on",
        "--log-disable",
        "--no-warmup",
    ]
    srv_proc = subprocess.Popen(srv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  PID {srv_proc.pid} — esperando que el servidor 1B arranque...")

    if not wait_server(LOCAL_URL, timeout=45):
        print("[ERROR] El servidor 1B no respondio en 45s. Abortando.")
        srv_proc.kill()
        sys.exit(1)
    print("  [OK] llama-server 1B listo en :8081")

    # ── Verificar servidor remoto 3.2B ────────────────────────────────────────
    print("\n[SETUP] Verificando servidor 3.2B remoto en :8080...")
    # El 3.2B corre en el servidor Linux, accesible via Tailscale
    REMOTE_URL_ACTUAL = "http://100.113.156.109:8080/v1/chat/completions"
    try:
        health = REMOTE_URL_ACTUAL.replace("/v1/chat/completions", "/health")
        urllib.request.urlopen(health, timeout=5)
        print("  [OK] Servidor 3.2B accesible en 100.113.156.109:8080")
        remote_url = REMOTE_URL_ACTUAL
    except Exception as e:
        print(f"  [WARN] Servidor 3.2B no accesible: {e}")
        print("  Benchmark 3.2B se omitira.")
        remote_url = None

    # ── Benchmark ─────────────────────────────────────────────────────────────
    results = []
    tps_1b_total, tps_32_total, n_32 = 0, 0, 0

    for i, q in enumerate(QUESTIONS, 1):
        print(f"\n[{i:02d}/{len(QUESTIONS)}] {q[:75]}...")
        entry = {"pregunta": q}

        # 1B local
        print("       1B (RTX 5060) -> ", end="", flush=True)
        r1 = infer(LOCAL_URL, q)
        entry["modelo_1B"] = r1
        tps_1b_total += r1["tps"]
        print(f"{r1['elapsed_s']}s | {r1['tokens']} tok | {r1['tps']} t/s | [{r1['finish']}]")

        # 3.2B remoto
        if remote_url:
            print("       3.2B (i5-4310U) -> ", end="", flush=True)
            r3 = infer(remote_url, q)
            entry["modelo_32B"] = r3
            tps_32_total += r3["tps"]
            n_32 += 1
            print(f"{r3['elapsed_s']}s | {r3['tokens']} tok | {r3['tps']} t/s | [{r3['finish']}]")

        results.append(entry)

        # Guardar progreso
        with open(REPORT, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    # ── Resumen ───────────────────────────────────────────────────────────────
    n = len(QUESTIONS)
    avg_1b  = round(tps_1b_total / n, 2)
    avg_32  = round(tps_32_total / n_32, 2) if n_32 > 0 else "N/A"
    factor  = round(avg_1b / avg_32, 2) if isinstance(avg_32, float) and avg_32 > 0 else "N/A"

    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print(f"  1B Q4_K_M  (RTX 5060 GPU) : {avg_1b} t/s promedio")
    print(f"  3.2B Q4_K_M (i5-4310U CPU): {avg_32} t/s promedio")
    print(f"  Velocidad relativa 1B/3.2B : {factor}x")
    print(f"\n  Reporte JSON: {REPORT}")
    print("=" * 80)

    srv_proc.terminate()
    print("[OK] Servidor 1B terminado.")

if __name__ == "__main__":
    main()
