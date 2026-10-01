#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sustracción Matricial de delta_W_trivia:
Extirpa el espacio latente de humanidades, debates políticos, mitología,
farándula e intrigas monárquicas de las capas intermedias de SENTINEL.
"""

import os
import torch
from safetensors.torch import load_file, save_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "export", "sentinel_root_pruned", "model.safetensors")
TRIVIA_ADAPTER_PATH = os.path.join(BASE_DIR, "training", "trivia_adapters", "adapter_model.safetensors")

SUBTRACTION_ALPHA = 0.35
LORA_SCALING = 32.0 / 16.0  # 2.0

def main():
    print("=" * 80)
    print("EJECUTANDO SUSTRACCIÓN MATRICIAL DE HUMANIDADES Y TRIVIA (delta_W_trivia)")
    print(f"Modelo: {MODEL_PATH}")
    print(f"Adaptador: {TRIVIA_ADAPTER_PATH}")
    print(f"Factor de Resta (alpha): {SUBTRACTION_ALPHA}")
    print("=" * 80)

    print("\n[1/3] Cargando tensores del modelo actual...")
    model_weights = load_file(MODEL_PATH)

    print("[2/3] Cargando tensores de delta_W_trivia...")
    trivia_weights = load_file(TRIVIA_ADAPTER_PATH)

    print("\n[3/3] Sustrayendo representaciones de humanidades en las 28 capas...")
    modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    subtracted_count = 0

    for l in range(28):
        for mod in modules:
            prefix_a = f"base_model.model.model.layers.{l}.self_attn.{mod}.lora_A.weight" if "proj" in mod and ("q" in mod or "k" in mod or "v" in mod or "o" in mod) else f"base_model.model.model.layers.{l}.mlp.{mod}.lora_A.weight"
            prefix_b = f"base_model.model.model.layers.{l}.self_attn.{mod}.lora_B.weight" if "proj" in mod and ("q" in mod or "k" in mod or "v" in mod or "o" in mod) else f"base_model.model.model.layers.{l}.mlp.{mod}.lora_B.weight"
            
            target_key = f"model.layers.{l}.self_attn.{mod}.weight" if "proj" in mod and ("q" in mod or "k" in mod or "v" in mod or "o" in mod) else f"model.layers.{l}.mlp.{mod}.weight"

            if prefix_a in trivia_weights and prefix_b in trivia_weights and target_key in model_weights:
                lora_a = trivia_weights[prefix_a].to(torch.float32)
                lora_b = trivia_weights[prefix_b].to(torch.float32)

                delta_w = torch.mm(lora_b, lora_a) * LORA_SCALING
                orig_w = model_weights[target_key].to(torch.float32)

                pruned_w = orig_w - (SUBTRACTION_ALPHA * delta_w)
                model_weights[target_key] = pruned_w.to(torch.bfloat16)
                subtracted_count += 1

    print(f"[OK] delta_W_trivia sustraído exitosamente en {subtracted_count} tensores.")
    print("Guardando tensores quirúrgicamente amputados...")
    save_file(model_weights, MODEL_PATH)
    print("\n[ÉXITO] Sustracción completada. Pesos actualizados en disco.")

if __name__ == "__main__":
    main()
