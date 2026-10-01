#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Evaluación y Simulación de Inferencia en Servidor Intel Core i5
Condiciones de Silicio y Entorno Simulado:
- 100% CPU (-ngl 0 / --n-gpu-layers 0): Cero offloading a GPU.
- Hilos: 4 hilos físicos (-t 4) correspondientes a la topología estándar de i5.
- Aceleración de Memoria: Flash Attention CPU (--flash-attn on) + KV Cache Cuantizado (-ctk q8_0 -ctv q8_0).
- Especulación: Decodificación especulativa con modelo borrador de 1B (-md sentinel-draft-1b.Q4_K_M.gguf).
"""

import os
import sys
import time
import json
import subprocess
import re

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLAMA_CLI = os.path.join(BASE_DIR, "export", "bin", "llama-cli.exe")
MASTER_MODEL = os.path.join(BASE_DIR, "export", "output_gguf", "sentinel-master.Q4_K_M.gguf")
DRAFT_MODEL = os.path.join(BASE_DIR, "export", "output_gguf", "sentinel-draft-1b.Q4_K_M.gguf")
OUTPUT_BENCHMARK = os.path.join(BASE_DIR, "benchmark", "intel_i5_simulation_results.json")

SYSTEM_PROMPT = (
    "SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.\n"
    "Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]]."
)

TEST_CASES = [
    {
        "id": "deep_reasoning_buck",
        "name": "Razonamiento Profundo R1: Fuente Buck 12V a 5V",
        "prompt": "[MODO_PENSAMIENTO: ACTIVO]\nDiseña una fuente reductora Buck de 12V a 5V para alimentar un ESP32 a 1A. ¿Qué inductancia necesito?",
        "expected_keywords": ["inductor", "Buck", "saturación", "duty cycle", "ESP32", "corriente", "bobina"],
        "max_tokens": 200,
    },
    {
        "id": "c_memory_safety",
        "name": "Guardarraíl DPO: Seguridad de Punteros en C",
        "prompt": "¿Cómo implementar una función en C que reasigne un búfer duplicando su tamaño si se llena?",
        "expected_keywords": ["realloc", "NULL", "temporal", "puntero", "memoria", "búfer", "fuga"],
        "max_tokens": 200,
    },
    {
        "id": "esp32_silicon_guardrail",
        "name": "Guardarraíl Silicio ESP32: Pines Prohibidos GPIO 6-11",
        "prompt": "Quiero conectar un sensor SPI en mi ESP32 usando los pines GPIO 6, 7 y 8. Escribe el código.",
        "expected_keywords": ["GPIO", "flash", "SPI", "prohibido", "boot", "reinicio", "peligro", "crash"],
        "max_tokens": 180,
    }
]

def run_i5_inference(prompt, max_tokens=180, use_speculative=True):
    formatted_prompt = (
        f"<|start_header_id|>system<|end_header_id|>\n\n"
        f"{SYSTEM_PROMPT}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{prompt}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )

    cmd = [
        LLAMA_CLI,
        "-m", MASTER_MODEL,
        "-p", formatted_prompt,
        "-n", str(max_tokens),
        "-ngl", "0",            # 0% GPU offload (Estricto CPU Intel Core i5)
        "-t", "4",              # 4 Cores CPU Intel i5
        "--flash-attn", "on",   # Flash Attention CPU (evita cache misses en L2/L3)
        "-ctk", "q8_0",         # Cache KV Cuantizado Q8
        "-ctv", "q8_0",
        "--temp", "0.2",
        "-st",
        "--no-warmup",
    ]

    if use_speculative and os.path.exists(DRAFT_MODEL):
        cmd.extend([
            "-md", DRAFT_MODEL,
            "--spec-draft-n-max", "4"
        ])

    start_time = time.perf_counter()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    elapsed = time.perf_counter() - start_time

    output = proc.stdout
    stderr = proc.stderr

    # Parsear estadísticas desde stdout [ Prompt: XX.X t/s | Generation: YY.Y t/s ]
    prompt_speed = 0.0
    gen_speed = 0.0
    m_st = re.search(r'\[\s*Prompt:\s*([\d\.]+)\s*t/s\s*\|\s*Generation:\s*([\d\.]+)\s*t/s\s*\]', output)
    if m_st:
        prompt_speed = float(m_st.group(1))
        gen_speed = float(m_st.group(2))

    # Limpiar output quitando cabeceras de llama-cli
    clean_resp = output
    if ">" in clean_resp:
        clean_resp = clean_resp.split(">", 1)[-1]
    if "[ Prompt:" in clean_resp:
        clean_resp = clean_resp.split("[ Prompt:")[0]
    clean_resp = clean_resp.strip()

    return {
        "response": clean_resp,
        "elapsed_seconds": round(elapsed, 2),
        "prompt_speed_tok_s": prompt_speed,
        "gen_speed_tok_s": gen_speed,
    }

def main():
    print("=" * 80)
    print("SIMULADOR DE ENTORNO SERVIDOR HP INTEL CORE i5 (UBUNTU SERVER)")
    print("Arquitectura: 100% CPU (-ngl 0) | 4 Cores (-t 4) | Flash Attention CPU")
    print("KV Cache: Q8_0 | Especulación: Draft 1B Q4_K_M")
    print("=" * 80)

    if not os.path.exists(MASTER_MODEL):
        print(f"[ERROR] Modelo maestro no encontrado: {MASTER_MODEL}")
        return

    results = []

    for test in TEST_CASES:
        print(f"\n================================================================================")
        print(f"EVALUANDO: {test['name']}")
        print(f"Prompt: {test['prompt']}")
        print(f"================================================================================")
        res = run_i5_inference(test["prompt"], max_tokens=test["max_tokens"], use_speculative=True)
        
        text = res["response"]
        passed_keywords = [kw for kw in test["expected_keywords"] if kw.lower() in text.lower()]
        has_thought = "<thought>" in text or "</thought>" in text
        
        print(f"Tiempo Total: {res['elapsed_seconds']}s")
        print(f"Velocidad Prompt (TTFT): {res['prompt_speed_tok_s']} tok/s")
        print(f"Velocidad Generación: {res['gen_speed_tok_s']} tok/s")
        print(f"Keywords Detectadas: {len(passed_keywords)}/{len(test['expected_keywords'])} {passed_keywords}")
        if has_thought:
            print("[COGNICIÓN] Traza de pensamiento reflexivo <thought> verificada.")

        # Snippet seguro
        lines = [l for l in text.split("\n") if l.strip()]
        snippet = "\n".join(lines[:12]) if len(lines) > 12 else text
        print(f"\n[RESPUESTA GENERADA]:\n{snippet}\n")

        results.append({
            "test_id": test["id"],
            "test_name": test["name"],
            "metrics": {
                "elapsed_seconds": res["elapsed_seconds"],
                "prompt_speed_tok_s": res["prompt_speed_tok_s"],
                "gen_speed_tok_s": res["gen_speed_tok_s"],
            },
            "has_thought": has_thought,
            "passed_keywords": passed_keywords,
            "response_full": text,
        })

    os.makedirs(os.path.dirname(OUTPUT_BENCHMARK), exist_ok=True)
    with open(OUTPUT_BENCHMARK, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print(f"Reporte de simulación i5 guardado exitosamente en: {OUTPUT_BENCHMARK}")
    print("=" * 80)

if __name__ == "__main__":
    main()
