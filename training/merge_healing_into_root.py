#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusión de Adaptadores de Curación en el Modelo de 26 Capas
Integra los pesos de curación de forma permanente en export/sentinel_root_pruned.
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_26L_DIR = os.path.join(BASE_DIR, "export", "sentinel_root_pruned")
HEALING_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "healing_adapters")

def main():
    print("=" * 80)
    print("FUSIONANDO PESOS DE CURACIÓN EN EL MODELO PODADO DE 26 CAPAS")
    print(f"Modelo: {ROOT_26L_DIR}")
    print(f"Adaptadores: {HEALING_ADAPTERS_DIR}")
    print("=" * 80)

    print("\n[1/3] Cargando modelo de 26 capas en memoria RAM (BF16)...")
    tokenizer = AutoTokenizer.from_pretrained(ROOT_26L_DIR)
    base_model = AutoModelForCausalLM.from_pretrained(
        ROOT_26L_DIR,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        low_cpu_mem_usage=True
    )

    print("[2/3] Acoplando adaptadores LoRA de curación...")
    peft_model = PeftModel.from_pretrained(base_model, HEALING_ADAPTERS_DIR)

    print("Fusionando pesos neuronales de forma permanente (merge_and_unload)...")
    final_model = peft_model.merge_and_unload()

    print(f"[3/3] Guardando modelo curado definitivo en {ROOT_26L_DIR}...")
    final_model.save_pretrained(ROOT_26L_DIR, safe_serialization=True)
    tokenizer.save_pretrained(ROOT_26L_DIR)

    print("\n[ÉXITO] Modelo de 26 capas curado y fusionado de forma permanente.")

if __name__ == "__main__":
    main()
