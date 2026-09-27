#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusión Directa de los Adaptadores Agénticos con la Raíz Quirúrgica de SENTINEL
Carga el modelo podado (sin cirílico/chino/árabe, sin trivia, sin ficción)
y fusiona permanentemente las habilidades agénticas y pedagógicas en sus matrices.
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_root_pruned")
AGENTIC_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "agentic_adapters")

def main():
    print("=" * 80)
    print("FUSIONANDO HABILIDADES AGÉNTICAS DIRECTAMENTE EN LA RAÍZ DEL MODELO")
    print(f"Modelo Raíz Quirúrgico: {ROOT_MODEL_DIR}")
    print(f"Adaptadores Agénticos: {AGENTIC_ADAPTERS_DIR}")
    print("=" * 80)

    print("\n[1/3] Cargando modelo podado en memoria RAM (BF16)...")
    tokenizer = AutoTokenizer.from_pretrained(ROOT_MODEL_DIR)
    base_model = AutoModelForCausalLM.from_pretrained(
        ROOT_MODEL_DIR,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        low_cpu_mem_usage=True
    )

    print("[2/3] Acoplando adaptadores LoRA entrenados...")
    peft_model = PeftModel.from_pretrained(base_model, AGENTIC_ADAPTERS_DIR)

    print("Fusionando pesos neuronales de forma permanente (merge_and_unload)...")
    final_model = peft_model.merge_and_unload()

    print(f"[3/3] Guardando pesos definitivos unificados en {ROOT_MODEL_DIR}...")
    final_model.save_pretrained(ROOT_MODEL_DIR, safe_serialization=True)
    tokenizer.save_pretrained(ROOT_MODEL_DIR)

    print("\n[ÉXITO] Habilidades agénticas fusionadas de forma permanente en la raíz de SENTINEL.")

if __name__ == "__main__":
    main()
