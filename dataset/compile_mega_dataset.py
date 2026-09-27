#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador del Mega Dataset Unificado para SENTINEL
Fusiona el dataset maestro existente (40 casos: Klipper, ESP32, Docker, CSV analytics, guardrails)
con los 7 nuevos datasets especializados (Programación React/Python, Shells/WSL, Web sin Wikipedia,
Stack HuggingFace 2026, Matemática Discreta, Álgebra/Despejes y Arquitectura GPU/CUDA).
"""

import os
import json
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_DATASET = os.path.join(BASE_DIR, "dataset", "lora_dataset.jsonl")
SPECIALIZED_DIR = os.path.join(BASE_DIR, "dataset", "specialized_datasets")
MEGA_DATASET = os.path.join(BASE_DIR, "dataset", "mega_lora_dataset.jsonl")

STANDARD_SYSTEM_PROMPT = "SENTINEL, sistema operativo cognitivo del Laboratorio STEM."

def compile_mega_dataset():
    total_records = 0
    seen_instructions = set()

    with open(MEGA_DATASET, "w", encoding="utf-8") as f_out:
        # 1. Cargar dataset base actual
        if os.path.exists(MASTER_DATASET):
            with open(MASTER_DATASET, "r", encoding="utf-8") as f_base:
                for line in f_base:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    user_msg = next((m["content"] for m in obj["messages"] if m["role"] == "user"), "")
                    assistant_msg = next((m["content"] for m in obj["messages"] if m["role"] == "assistant"), "")
                    if user_msg and user_msg not in seen_instructions:
                        seen_instructions.add(user_msg)
                        clean_entry = {
                            "messages": [
                                {"role": "system", "content": STANDARD_SYSTEM_PROMPT},
                                {"role": "user", "content": user_msg},
                                {"role": "assistant", "content": assistant_msg}
                            ]
                        }
                        f_out.write(json.dumps(clean_entry, ensure_ascii=False) + "\n")
                        total_records += 1

        # 2. Cargar todos los datasets especializados
        specialized_files = sorted(glob.glob(os.path.join(SPECIALIZED_DIR, "*.jsonl")))
        for s_file in specialized_files:
            with open(s_file, "r", encoding="utf-8") as f_spec:
                for line in f_spec:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    user_msg = next((m["content"] for m in obj["messages"] if m["role"] == "user"), "")
                    assistant_msg = next((m["content"] for m in obj["messages"] if m["role"] == "assistant"), "")
                    if user_msg and user_msg not in seen_instructions:
                        seen_instructions.add(user_msg)
                        clean_entry = {
                            "messages": [
                                {"role": "system", "content": STANDARD_SYSTEM_PROMPT},
                                {"role": "user", "content": user_msg},
                                {"role": "assistant", "content": assistant_msg}
                            ]
                        }
                        f_out.write(json.dumps(clean_entry, ensure_ascii=False) + "\n")
                        total_records += 1

    print(f"=== COMPILACIÓN FINALIZADA ===")
    print(f"Archivo unificado generado: {MEGA_DATASET}")
    print(f"Total de pares de entrenamiento únicos: {total_records}")
    print(f"System Prompt intrínseco estandarizado: '{STANDARD_SYSTEM_PROMPT}'")

if __name__ == "__main__":
    compile_mega_dataset()
