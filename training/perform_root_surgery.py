#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL Root Model Surgery:
1. Task Vector Subtraction: Resta matricial del vector de tarea negativo en MLP y atención.
2. Embedding & Vocabulary Nullification: Anulación física de proyecciones para tokens no-STEM.
3. Exportación a safetensors en export/sentinel_root_pruned/
"""

import os
import torch
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
from safetensors.torch import load_file, save_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGED_DIR = os.path.join(BASE_DIR, "export", "merged_model")
NEGATIVE_ADAPTER_PATH = os.path.join(BASE_DIR, "training", "negative_adapters", "adapter_model.safetensors")
OUTPUT_PRUNED_DIR = os.path.join(BASE_DIR, "export", "sentinel_root_pruned")
UNWANTED_CORPUS_PATH = os.path.join(BASE_DIR, "dataset", "unwanted_domain_corpus.jsonl")

# Parámetro de sustracción de tarea (Task Arithmetic scaling)
SUBTRACTION_ALPHA = 0.40
LORA_ALPHA = 32.0
LORA_RANK = 16.0
LORA_SCALING = LORA_ALPHA / LORA_RANK  # 2.0

def main():
    print("=" * 80)
    print("INICIANDO CIRUGÍA PROFUNDA DE TENSORES EN LA RAÍZ DE SENTINEL")
    print(f"Modelo Fuente: {MERGED_DIR}")
    print(f"Vector Negativo: {NEGATIVE_ADAPTER_PATH}")
    print(f"Factor de Resta (alpha): {SUBTRACTION_ALPHA}")
    print("=" * 80)

    os.makedirs(OUTPUT_PRUNED_DIR, exist_ok=True)

    # 1. Cargar tensores del modelo unificado actual
    print("\n[1/4] Cargando tensores de modelo unificado (Safetensors)...")
    merged_weights = load_file(os.path.join(MERGED_DIR, "model.safetensors"))
    
    # 2. Cargar tensores del adaptador negativo
    print("[2/4] Cargando tensores de vector de tarea negativo...")
    neg_weights = load_file(NEGATIVE_ADAPTER_PATH)

    # 3. Resta matricial tensor a tensor en MLP y Atención
    print("\n[3/4] Ejecutando sustracción matricial de espacio latente en 28 capas...")
    modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    num_layers = 28
    subtracted_count = 0

    for l in range(num_layers):
        for mod in modules:
            # Prefijos en el adaptador vs modelo base
            prefix_a = f"base_model.model.model.layers.{l}.self_attn.{mod}.lora_A.weight" if "proj" in mod and ("q" in mod or "k" in mod or "v" in mod or "o" in mod) else f"base_model.model.model.layers.{l}.mlp.{mod}.lora_A.weight"
            prefix_b = f"base_model.model.model.layers.{l}.self_attn.{mod}.lora_B.weight" if "proj" in mod and ("q" in mod or "k" in mod or "v" in mod or "o" in mod) else f"base_model.model.model.layers.{l}.mlp.{mod}.lora_B.weight"
            
            target_key = f"model.layers.{l}.self_attn.{mod}.weight" if "proj" in mod and ("q" in mod or "k" in mod or "v" in mod or "o" in mod) else f"model.layers.{l}.mlp.{mod}.weight"

            if prefix_a in neg_weights and prefix_b in neg_weights and target_key in merged_weights:
                lora_a = neg_weights[prefix_a].to(torch.float32)
                lora_b = neg_weights[prefix_b].to(torch.float32)
                
                # delta_W = (B @ A) * scaling
                delta_w = torch.mm(lora_b, lora_a) * LORA_SCALING
                
                orig_w = merged_weights[target_key].to(torch.float32)
                
                # W_pruned = W_orig - alpha * delta_W
                pruned_w = orig_w - (SUBTRACTION_ALPHA * delta_w)
                
                # Guardar en precisión nativa bfloat16
                merged_weights[target_key] = pruned_w.to(torch.bfloat16)
                subtracted_count += 1

    print(f"[OK] Se completó la sustracción matricial en {subtracted_count} tensores de proyección.")

    # 4. Cirugía de Embeddings: Anulación física de tokens no deseados
    print("\n[4/4] Ejecutando cirugía y anulación física de embeddings no deseados...")
    tokenizer = AutoTokenizer.from_pretrained(MERGED_DIR)
    
    # Extraer tokens del corpus no deseado
    unwanted_tokens = set()
    with open(UNWANTED_CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            for m in data["messages"]:
                tokens = tokenizer.encode(m["content"], add_special_tokens=False)
                unwanted_tokens.update(tokens)
    
    # Proteger tokens esenciales: código, sintaxis, caracteres ASCII y tokens especiales
    protected_tokens = set(tokenizer.all_special_ids)
    for c in range(256): # Bytes UTF-8 y caracteres ASCII
        byte_token = tokenizer.encode(chr(c), add_special_tokens=False)
        protected_tokens.update(byte_token)
    
    # Tokens técnicos comunes a proteger
    sample_code = "int main() { printf(); } def class return import async await while for if else uint8_t void struct"
    protected_tokens.update(tokenizer.encode(sample_code, add_special_tokens=False))

    ablated_tokens = unwanted_tokens - protected_tokens
    print(f"Total de tokens identificados para ablación de pesos: {len(ablated_tokens)}")

    embed_tensor = merged_weights["model.embed_tokens.weight"].clone().to(torch.float32)
    # Anular vectores a cero absoluto
    for tid in ablated_tokens:
        embed_tensor[tid] = 0.0

    merged_weights["model.embed_tokens.weight"] = embed_tensor.to(torch.bfloat16)
    print(f"[OK] Vectores de embedding anulados a cero absoluto para {len(ablated_tokens)} tokens.")

    # 5. Guardar modelo quirúrgicamente modificado
    print(f"\nGuardando modelo podado de raíz en: {OUTPUT_PRUNED_DIR}...")
    save_file(merged_weights, os.path.join(OUTPUT_PRUNED_DIR, "model.safetensors"))

    # Copiar configs y tokenizer
    tokenizer.save_pretrained(OUTPUT_PRUNED_DIR)
    with open(os.path.join(MERGED_DIR, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["sentinel_root_pruned"] = True
    cfg["subtraction_alpha"] = SUBTRACTION_ALPHA
    with open(os.path.join(OUTPUT_PRUNED_DIR, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    with open(os.path.join(MERGED_DIR, "generation_config.json"), "r", encoding="utf-8") as f:
        gen_cfg = json.load(f)
    with open(os.path.join(OUTPUT_PRUNED_DIR, "generation_config.json"), "w", encoding="utf-8") as f:
        json.dump(gen_cfg, f, indent=2)

    print("\n" + "=" * 80)
    print("[ÉXITO TOTAL] CIRUGÍA DE RAÍZ COMPLETADA.")
    print(f"Modelo resultante listo en: {OUTPUT_PRUNED_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
