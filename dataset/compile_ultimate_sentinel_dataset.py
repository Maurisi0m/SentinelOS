#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador del Dataset Maestro Definitivo para SENTINEL
Fusiona:
1. dataset/healing_thought_c_dataset.jsonl (Modo pensamiento dual, C memory, ESP32 pines)
2. dataset/master_agentic_dataset.jsonl (Herramientas agénticas, PackageManager, Obsidian)
3. dataset/mega_lora_dataset.jsonl (Fundamentos STEM, Robótica, Linux, Docker, Klipper)
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
OUT_PATH = os.path.join(DATASET_DIR, "ultimate_sentinel_dataset.jsonl")

INPUT_FILES = [
    os.path.join(DATASET_DIR, "healing_thought_c_dataset.jsonl"),
    os.path.join(DATASET_DIR, "master_agentic_dataset.jsonl"),
    os.path.join(DATASET_DIR, "mega_lora_dataset.jsonl")
]

def main():
    seen_queries = set()
    total = 0

    with open(OUT_PATH, "w", encoding="utf-8") as out_f:
        for in_path in INPUT_FILES:
            if not os.path.exists(in_path):
                print(f"[SKIP] No existe: {in_path}")
                continue
            with open(in_path, "r", encoding="utf-8") as in_f:
                for line in in_f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        user_msg = next((m["content"] for m in data["messages"] if m["role"] == "user"), "")
                        if user_msg and user_msg not in seen_queries:
                            seen_queries.add(user_msg)
                            out_f.write(json.dumps(data, ensure_ascii=False) + "\n")
                            total += 1
                    except Exception as e:
                        pass

    print(f"[ÉXITO] Dataset definitivo compilado con {total} ejemplos únicos en: {OUT_PATH}")

if __name__ == "__main__":
    main()
