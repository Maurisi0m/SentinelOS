#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sustracción Matricial de Vector de Desaprendizaje (Negative Task Vector Subtraction) para Llama-3.2-1B
Extirpa el espacio latente NO-STEM (farándula, romance, astrología, deportes de entretenimiento,
cocina cotidiana, New Age y charla casual) directamente de los tensores de peso de las 16 capas de Llama 3.2 1B.
Fórmula: W_pruned = W_base - alpha * (LoRA_B @ LoRA_A * scaling)
"""

import os
import shutil
import torch
from safetensors.torch import load_file, save_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_DIR = r"C:\Users\mauro\.cache\huggingface\hub\models--unsloth--Llama-3.2-1B-Instruct\snapshots\5a8abab4a5d6f164389b1079fb721cfab8d7126c"
BASE_MODEL_WEIGHTS = os.path.join(BASE_MODEL_DIR, "model.safetensors")
NEGATIVE_ADAPTER_PATH = os.path.join(BASE_DIR, "training", "negative_adapters_1b", "adapter_model.safetensors")
OUTPUT_MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_1b_unlearned")
OUTPUT_MODEL_WEIGHTS = os.path.join(OUTPUT_MODEL_DIR, "model.safetensors")

SUBTRACTION_ALPHA = 0.35
LORA_SCALING = 32.0 / 16.0  # alpha / r = 2.0
NUM_LAYERS = 16

def main():
    print("=" * 80)
    print("EJECUTANDO SUSTRACCIÓN MATRICIAL DE VECTOR NO-STEM (DESAPRENDIZAJE NEURONAL)")
    print(f"Modelo Base: {BASE_MODEL_WEIGHTS}")
    print(f"Adaptador Negativo: {NEGATIVE_ADAPTER_PATH}")
    print(f"Factor de Resta (alpha): {SUBTRACTION_ALPHA}")
    print(f"Destino: {OUTPUT_MODEL_DIR}")
    print("=" * 80)

    if not os.path.exists(NEGATIVE_ADAPTER_PATH):
        raise FileNotFoundError(f"No se encontró el adaptador negativo en {NEGATIVE_ADAPTER_PATH}. Ejecute primero train_negative_adapter_1b.py")

    os.makedirs(OUTPUT_MODEL_DIR, exist_ok=True)

    print("\n[1/4] Cargando tensores de pesos del modelo base Llama-3.2-1B-Instruct...")
    base_weights = load_file(BASE_MODEL_WEIGHTS)

    print("[2/4] Cargando tensores de gradiente no deseado del adaptador...")
    negative_weights = load_file(NEGATIVE_ADAPTER_PATH)

    print(f"\n[3/4] Sustrayendo representaciones no-STEM a lo largo de las {NUM_LAYERS} capas de atención y MLP...")
    modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    subtracted_count = 0

    for l in range(NUM_LAYERS):
        for mod in modules:
            is_attn = "proj" in mod and any(x in mod for x in ["q", "k", "v", "o"])
            sub_block = "self_attn" if is_attn else "mlp"

            prefix_a = f"base_model.model.model.layers.{l}.{sub_block}.{mod}.lora_A.weight"
            prefix_b = f"base_model.model.model.layers.{l}.{sub_block}.{mod}.lora_B.weight"
            target_key = f"model.layers.{l}.{sub_block}.{mod}.weight"

            if prefix_a in negative_weights and prefix_b in negative_weights and target_key in base_weights:
                lora_a = negative_weights[prefix_a].to(torch.float32)
                lora_b = negative_weights[prefix_b].to(torch.float32)

                delta_w = torch.mm(lora_b, lora_a) * LORA_SCALING
                orig_w = base_weights[target_key].to(torch.float32)

                pruned_w = orig_w - (SUBTRACTION_ALPHA * delta_w)
                base_weights[target_key] = pruned_w.to(torch.bfloat16)
                subtracted_count += 1

    print(f"[OK] Sustracción completada en {subtracted_count} tensores matriciales.")

    print(f"\n[4/4] Guardando modelo quirúrgicamente amputado en {OUTPUT_MODEL_WEIGHTS}...")
    save_file(base_weights, OUTPUT_MODEL_WEIGHTS)

    # Copiar configuración y tokenizadores
    for fname in ["config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]:
        src = os.path.join(BASE_MODEL_DIR, fname)
        dst = os.path.join(OUTPUT_MODEL_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    print("=" * 80)
    print(f"[ÉXITO] Modelo Llama-3.2-1B-PureSTEM (Unlearned) exportado exitosamente en: {OUTPUT_MODEL_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
