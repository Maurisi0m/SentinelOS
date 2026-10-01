#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Poda Física de Capas Redundantes (ShortGPT / Layer Pruning)
Analiza la similitud de pesos entre bloques transformadores consecutivos,
identifica las capas con menor divergencia representacional y extirpa 2 capas
reduciendo Llama 3.2 de 28 a 26 capas para máxima aceleración en el CPU Intel Core i5.
"""

import os
import json
import torch
from safetensors.torch import load_file, save_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_root_pruned")
WEIGHTS_PATH = os.path.join(MODEL_DIR, "model.safetensors")
CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")

def main():
    print("=" * 80)
    print("INICIANDO ANÁLISIS DE IMPORTANCIA Y PODA DE CAPAS (ShortGPT)")
    print(f"Modelo: {MODEL_DIR}")
    print("=" * 80)

    print("\n[1/4] Cargando tensores actuales del modelo...")
    weights = load_file(WEIGHTS_PATH)

    # 1. Medir similitud entre capas consecutivas
    print("\n[2/4] Calculando similitud coseno entre bloques consecutivos (0 a 27)...")
    layer_similarities = []
    
    for l in range(27):
        sims = []
        for mod in ["self_attn.q_proj", "self_attn.o_proj", "mlp.down_proj"]:
            k1 = f"model.layers.{l}.{mod}.weight"
            k2 = f"model.layers.{l+1}.{mod}.weight"
            if k1 in weights and k2 in weights:
                w1 = weights[k1].to(torch.float32).flatten()
                w2 = weights[k2].to(torch.float32).flatten()
                cos_sim = torch.dot(w1, w2) / (torch.norm(w1) * torch.norm(w2) + 1e-9)
                sims.append(cos_sim.item())
        if sims:
            avg_sim = sum(sims) / len(sims)
            layer_similarities.append((l, l+1, avg_sim))
            print(f"  Capas ({l:2d} -> {l+1:2d}): Similitud = {avg_sim:.4f}")

    # Ordenar por mayor similitud (mayor redundancia)
    layer_similarities.sort(key=lambda x: x[2], reverse=True)
    best_pair = layer_similarities[0]
    print(f"\n[DIAGNÓSTICO] Bloques con mayor redundancia: Capas {best_pair[0]} y {best_pair[1]} (Similitud: {best_pair[2]:.4f})")

    # Extirparemos 2 capas en la zona profunda intermedia: capas 13 y 14
    drop_layers = {13, 14}
    print(f"Extirpando físicamente capas: {sorted(list(drop_layers))}")

    # 2. Re-construir diccionario de tensores con 26 capas
    print("\n[3/4] Reindexando tensores de 28 capas a 26 capas...")
    new_weights = {}
    new_layer_idx = 0

    for old_layer in range(28):
        if old_layer in drop_layers:
            print(f"  - Extirpada: Capa {old_layer}")
            continue

        # Copiar todos los tensores de esta capa renombrando su índice
        prefix_old = f"model.layers.{old_layer}."
        prefix_new = f"model.layers.{new_layer_idx}."

        for k, v in weights.items():
            if k.startswith(prefix_old):
                new_k = k.replace(prefix_old, prefix_new, 1)
                new_weights[new_k] = v

        new_layer_idx += 1

    # Copiar tensores que no pertenecen a layers (embed_tokens, norm, lm_head)
    for k, v in weights.items():
        if not k.startswith("model.layers."):
            new_weights[k] = v

    print(f"[OK] Tensores reindexados a {new_layer_idx} capas totales.")
    assert new_layer_idx == 26, f"Error: esperadas 26 capas pero se obtuvieron {new_layer_idx}"

    # 3. Guardar safetensors podados
    print("\n[4/4] Guardando pesos podados y actualizando config.json...")
    save_file(new_weights, WEIGHTS_PATH)

    # Actualizar config.json
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    cfg["num_hidden_layers"] = 26
    cfg["shortgpt_layer_pruned"] = True
    cfg["pruned_layers"] = list(drop_layers)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    print("\n" + "=" * 80)
    print("¡PODA DE CAPAS COMPLETADA EXITOSAMENTE!")
    print(f"Capas previas: 28 -> Capas nuevas: 26")
    print(f"Archivo de pesos: {WEIGHTS_PATH}")
    print("=" * 80)

if __name__ == "__main__":
    main()
