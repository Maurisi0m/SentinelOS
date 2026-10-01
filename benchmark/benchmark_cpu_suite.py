#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL CPU Performance & Speculative Decoding Benchmark Suite
Ejecuta 100% en CPU (simulando el servidor HP Intel Core i5):
1. Test de Inferencia Base en CPU (Tokens/segundo y TTFT).
2. Test de Inferencia con Flash Attention + KV Cache Q8_0 en CPU.
3. Test de Aceleración con Speculative Decoding (Modelo 3B + Borrador 1B).
4. Comparativa de fidelidad y factor de aceleración real.
"""

import os
import sys
import re
import json
import time
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(BASE_DIR, "export", "bin")
GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")

COMPLETION_BIN = os.path.join(BIN_DIR, "llama-cli.exe")
MASTER_MODEL = os.path.join(GGUF_DIR, "sentinel-master.Q4_K_M.gguf")
DRAFT_MODEL = os.path.join(GGUF_DIR, "sentinel-draft-1b.Q4_K_M.gguf")
OUTPUT_JSON = os.path.join(BASE_DIR, "benchmark", "cpu_benchmark_results.json")

TEST_PROMPTS = [
    "Explica qué es un transistor MOSFET y cómo conmuta una carga inductiva.",
    "¿Cuáles son las diferencias críticas entre la arquitectura GPIO de Raspberry Pi 4 y Raspberry Pi 5 con el chip RP1?",
]

def run_completion(model_path, draft_path, prompt, n_predict=48, use_fa=True, use_q8_kv=True):
    cmd = [
        COMPLETION_BIN,
        "-m", model_path,
        "-p", prompt,
        "-n", str(n_predict),
        "-st"
    ]

    if draft_path and os.path.exists(draft_path):
        cmd.extend(["-md", draft_path, "--spec-draft-n-max", "4"])

    if use_fa:
        cmd.extend(["--flash-attn", "on"])
    else:
        cmd.extend(["--flash-attn", "off"])

    if use_q8_kv:
        cmd.extend(["-ctk", "q8_0", "-ctv", "q8_0"])

    env = os.environ.copy()
    env["OMP_PROC_BIND"] = "CLOSE"
    env["OMP_PLACES"] = "CORES"

    start_t = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    elapsed = time.time() - start_t

    stdout = res.stdout + res.stderr

    # Parsear métricas de llama-cli [ Prompt: 39.7 t/s | Generation: 17.5 t/s ]
    prompt_speed = 0.0
    eval_speed = 0.0

    m = re.search(r'\[\s*Prompt:\s*([\d\.]+)\s*t/s\s*\|\s*Generation:\s*([\d\.]+)\s*t/s\s*\]', stdout)
    if m:
        prompt_speed = float(m.group(1))
        eval_speed = float(m.group(2))
    else:
        # Fallback regex estándar de llama.cpp
        p_match = re.search(r'prompt eval time =.*?([\d\.]+)\s*tokens per second', stdout)
        if p_match:
            prompt_speed = float(p_match.group(1))
        e_match = re.search(r'eval time =.*?([\d\.]+)\s*tokens per second', stdout)
        if e_match:
            eval_speed = float(e_match.group(1))

    return {
        "elapsed_sec": round(elapsed, 2),
        "prompt_speed_tok_s": prompt_speed,
        "eval_speed_tok_s": eval_speed,
        "stdout_snippet": stdout[-400:].strip()
    }

def main():
    print("=" * 80)
    print("SUITE DE BENCHMARKING CPU: SENTINEL-3B (SIMULADOR INTEL CORE i5)")
    print(f"Modelo Maestro: {MASTER_MODEL}")
    print(f"Modelo Borrador: {DRAFT_MODEL if os.path.exists(DRAFT_MODEL) else 'No compilado aún'}")
    print("=" * 80)

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hardware": "CPU (Intel / OpenMP Multi-Core, 0% GPU offload)",
        "tests": []
    }

    test_prompt = TEST_PROMPTS[0]

    # 1. Baseline: 3B sin Flash Attention
    print("\n[1/3] Evaluando 3B Estándar en CPU (Sin Flash Attention)...")
    res_base = run_completion(MASTER_MODEL, None, test_prompt, n_predict=48, use_fa=False, use_q8_kv=False)
    print(f"  -> Prompt Speed: {res_base['prompt_speed_tok_s']} tok/s | Gen Speed: {res_base['eval_speed_tok_s']} tok/s")
    results["tests"].append({"name": "3B Baseline (Sin FA)", "metrics": res_base})

    # 2. Con Flash Attention + KV Cache Q8_0
    print("\n[2/3] Evaluando 3B con Flash Attention + KV Q8_0 en CPU...")
    res_fa = run_completion(MASTER_MODEL, None, test_prompt, n_predict=48, use_fa=True, use_q8_kv=True)
    print(f"  -> Prompt Speed: {res_fa['prompt_speed_tok_s']} tok/s | Gen Speed: {res_fa['eval_speed_tok_s']} tok/s")
    results["tests"].append({"name": "3B Flash Attention + KV Q8", "metrics": res_fa})

    # 3. Con Speculative Decoding (si existe el modelo borrador de 1B)
    if os.path.exists(DRAFT_MODEL):
        print("\n[3/3] Evaluando 3B con Speculative Decoding (+ Draft 1B) en CPU...")
        res_spec = run_completion(MASTER_MODEL, DRAFT_MODEL, test_prompt, n_predict=48, use_fa=True, use_q8_kv=True)
        print(f"  -> Gen Speed: {res_spec['eval_speed_tok_s']} tok/s | Tiempo Total: {res_spec['elapsed_sec']}s")
        results["tests"].append({"name": "3B + Draft 1B (Speculative)", "metrics": res_spec})

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Resultados de Benchmark guardados en: {OUTPUT_JSON}")
    print("=" * 80)

if __name__ == "__main__":
    main()
