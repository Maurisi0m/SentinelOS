import os
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LLAMA_COMPLETION = os.path.join(BASE_DIR, "export", "bin", "llama-completion.exe")

BASE_MODEL = os.path.join(BASE_DIR, "export", "output_gguf", "base-llama-3.2-3b.Q4_K_M.gguf")
SENTINEL_MODEL = os.path.join(BASE_DIR, "export", "output_gguf", "sentinel-stem.Q4_K_M.gguf")

SYSTEM_PROMPT = "SENTINEL, sistema operativo cognitivo del Laboratorio STEM."

TEST_QUESTIONS = [
    {
        "id": "PRUEBA 1 (PROGRAMACIÓN EN C / CONCURRENCIA DE BAJO NIVEL Y EPOLL)",
        "query": "¿Cómo implementar un servidor concurrente de alto rendimiento en C utilizando epoll en modo Edge-Triggered (EPOLLET) para sockets no bloqueantes, cómo gestionar el buffer ante el retorno EAGAIN/EWOULDBLOCK y cómo prevenir el problema de thundering herd?"
    },
    {
        "id": "PRUEBA 2 (HARDWARE IOT / FÍSICA DE SEMICONDUCTORES Y LEVEL SHIFTERS)",
        "query": "En un sistema embebido, ¿por qué no se debe conectar directamente la señal TX de un Arduino Uno (5V) al pin RX de un ESP32 (3.3V)? Explica el efecto físico en los diodos ESD internos y cómo diseñar un level shifter bidireccional con un MOSFET canal N (BSS138)."
    }
]

def run_inference(model_path, query, max_tokens=320):
    formatted_prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{SYSTEM_PROMPT}<|eot_id|>\n"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{query}<|eot_id|>\n"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    
    cmd = [
        LLAMA_COMPLETION,
        "-m", model_path,
        "-p", formatted_prompt,
        "-n", str(max_tokens),
        "-t", "4",
        "--temp", "0.2",
        "-no-cnv",
        "--simple-io"
    ]
    
    t0 = time.time()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
    dt = time.time() - t0
    
    output = proc.stdout
    if "<|start_header_id|>assistant<|end_header_id|>" in output:
        reply = output.split("<|start_header_id|>assistant<|end_header_id|>")[-1].replace("<|eot_id|>", "").strip()
    else:
        reply = output.strip()
        
    return reply, dt

def main():
    print("=" * 80, flush=True)
    print("BENCHMARK HEAD-TO-HEAD: BASE LLAMA-3.2-3B vs SENTINEL STEM", flush=True)
    print("Formato de ambos modelos: GGUF Q4_K_M (Mismo motor llama.cpp, temp=0.2, 4 hilos)", flush=True)
    print("=" * 80, flush=True)
    
    for t in TEST_QUESTIONS:
        qid = t["id"]
        qtext = t["query"]
        print(f"\n\n################################################################################", flush=True)
        print(f"{qid}", flush=True)
        print(f"PREGUNTA: {qtext}", flush=True)
        print(f"################################################################################\n", flush=True)
        
        # 1. Base Model
        print(f"--- [1/2] EJECUTANDO EN MODELO ORIGINAL (LLAMA-3.2-3B-INSTRUCT) ---", flush=True)
        base_reply, base_time = run_inference(BASE_MODEL, qtext)
        print(f"Tiempo: {base_time:.2f}s\n", flush=True)
        print("RESPUESTA MODELO BASE:\n" + base_reply, flush=True)
        print("\n" + "-" * 80 + "\n", flush=True)
        
        # 2. SENTINEL Model
        print(f"--- [2/2] EJECUTANDO EN NUESTRO MODELO (SENTINEL STEM) ---", flush=True)
        sentinel_reply, sentinel_time = run_inference(SENTINEL_MODEL, qtext)
        print(f"Tiempo: {sentinel_time:.2f}s\n", flush=True)
        print("RESPUESTA SENTINEL:\n" + sentinel_reply, flush=True)
        print("\n" + "=" * 80 + "\n", flush=True)

if __name__ == "__main__":
    main()
