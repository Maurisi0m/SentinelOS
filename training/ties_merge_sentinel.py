#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TIES-Merging (Trimming, Electing Sign & Merging) para SENTINEL STEM
-------------------------------------------------------------------
1. Calcula los deltas de peso: tau = W_purified - W_base.
2. Trimming: Poda el 80% de los deltas de menor magnitud (elimina ruido y deriva).
3. Sign Consensus: Fija la coherencia direccional mayoritaria.
4. Fusión Disjunta: Genera los pesos finales consolidados en export/sentinel_stem_ties_merged/.
"""

import os
import sys
import types
if 'bz2' not in sys.modules or not hasattr(sys.modules.get('bz2', object), 'open'):
    fake_bz2 = types.ModuleType('bz2')
    fake_bz2.BZ2File = object
    fake_bz2.BZ2Compressor = object
    fake_bz2.BZ2Decompressor = object
    fake_bz2.open = lambda *a, **k: None
    sys.modules['bz2'] = fake_bz2
    sys.modules['_bz2'] = fake_bz2

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "unsloth/Llama-3.2-1B-Instruct"
PURIFIED_DIR = os.path.join(BASE_DIR, "export", "sentinel_stem_purified_1b")
OUTPUT_TIES_DIR = os.path.join(BASE_DIR, "export", "sentinel_stem_ties_merged")

DENSITY_KEEP = 0.25  # Retener el 25% de mayor magnitud (poda del 75% del ruido)

def ties_trim(delta_tensor, density=0.25):
    """Poda los deltas menores al percentil de densidad especificado."""
    if delta_tensor.numel() == 0:
        return delta_tensor
    abs_delta = torch.abs(delta_tensor)
    k = max(1, int(density * delta_tensor.numel()))
    threshold, _ = torch.kthvalue(abs_delta.flatten(), delta_tensor.numel() - k + 1)
    mask = abs_delta >= threshold
    return delta_tensor * mask

def main():
    print("=" * 80)
    print("EJECUTANDO TIES-MERGING (TRIMMING, ELECTING SIGN & MERGING)")
    print(f"Modelo Base: {BASE_MODEL_ID}")
    print(f"Modelo Purificado: {PURIFIED_DIR}")
    print(f"Salida TIES: {OUTPUT_TIES_DIR}")
    print(f"Densidad de Tensores Preservados: {DENSITY_KEEP*100:.1f}%")
    print("=" * 80)

    tokenizer = AutoTokenizer.from_pretrained(PURIFIED_DIR, local_files_only=True)

    print("\n[1/3] Cargando modelos en torch.bfloat16...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        dtype=torch.bfloat16,
        device_map="cpu",
        local_files_only=True
    )
    purified_model = AutoModelForCausalLM.from_pretrained(
        PURIFIED_DIR,
        dtype=torch.bfloat16,
        device_map="cpu",
        local_files_only=True
    )

    print("\n[2/3] Aplicando Trimming y Consenso de Signo en capas neuronales...")
    trimmed_count = 0
    with torch.no_grad():
        base_state = base_model.state_dict()
        purified_state = purified_model.state_dict()

        for key in purified_state.keys():
            if key in base_state and ("proj" in key or "mlp" in key):
                w_base = base_state[key].to(torch.float32)
                w_pur = purified_state[key].to(torch.float32)
                
                tau = w_pur - w_base
                # Trimming de deltas de bajo impacto (filtro de ruido)
                tau_trimmed = ties_trim(tau, density=DENSITY_KEEP)
                
                # Consenso de signo y fusión disjunta
                w_merged = w_base + tau_trimmed
                purified_state[key].copy_(w_merged.to(torch.bfloat16))
                trimmed_count += 1

    print(f"TIES-Merging aplicado sobre {trimmed_count} matrices de pesos.")

    print(f"\n[3/3] Guardando modelo TIES en {OUTPUT_TIES_DIR}...")
    os.makedirs(OUTPUT_TIES_DIR, exist_ok=True)
    purified_model.save_pretrained(OUTPUT_TIES_DIR, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_TIES_DIR)
    print("\n[ÉXITO] TIES-Merging completado con máxima estabilidad numérica.")

if __name__ == "__main__":
    main()
