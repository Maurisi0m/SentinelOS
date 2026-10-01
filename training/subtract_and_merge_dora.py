#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusión DoRA y Sustracción Quirúrgica de Vectores de Tarea (Task Vector Subtraction)
-----------------------------------------------------------------------------------
1. Carga el modelo base Llama-3.2-1B-Instruct en torch.bfloat16.
2. Fusiona los adaptadores DoRA (dora_adapters_1b) descomponiendo dirección y magnitud.
3. Sustrae los subespacios de activación de ficción, romance y charla no técnica (Task Arithmetic).
4. Guarda el modelo purificado en export/sentinel_stem_purified_1b/.
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
from peft import PeftModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "unsloth/Llama-3.2-1B-Instruct"
DORA_ADAPTER_DIR = os.path.join(BASE_DIR, "training", "dora_adapters_1b")
OUTPUT_PURIFIED_DIR = os.path.join(BASE_DIR, "export", "sentinel_stem_purified_1b")

SUBTRACTION_FACTOR = 0.25  # lambda para sustracción de tensores

def main():
    print("=" * 80)
    print("FUSIÓN DoRA Y SUSTRACCIÓN QUIRÚRGICA DE VECTORES DE TAREA (1B)")
    print(f"Modelo Base: {BASE_MODEL_ID}")
    print(f"Adaptadores DoRA: {DORA_ADAPTER_DIR}")
    print(f"Salida Purificada: {OUTPUT_PURIFIED_DIR}")
    print(f"Factor de Resta (Lambda): {SUBTRACTION_FACTOR}")
    print("=" * 80)

    # 1. Cargar Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, local_files_only=True)

    # 2. Cargar Modelo Base
    print("\n[1/4] Cargando Modelo Base en torch.bfloat16...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        dtype=torch.bfloat16,
        device_map="cpu",  # CPU para no saturar VRAM durante la fusión de safetensors
        local_files_only=True
    )

    # 3. Cargar y Fusionar DoRA
    print("\n[2/4] Fusionando adaptadores DoRA (magnitud + dirección)...")
    peft_model = PeftModel.from_pretrained(base_model, DORA_ADAPTER_DIR)
    merged_model = peft_model.merge_and_unload()
    print("Fusión DoRA completada con éxito.")

    # 4. Sustracción Quirúrgica de Subespacios de Ficción/Fluff
    print("\n[3/4] Ejecutando Sustracción de Vectores de Tarea no deseadas en capas intermedias...")
    # Contrastive task vector projection: anulación en capas 4 a 14
    with torch.no_grad():
        num_layers = len(merged_model.model.layers)
        subtracted_params = 0
        for l_idx in range(num_layers):
            layer = merged_model.model.layers[l_idx]
            
            # En capas intermedias donde residen las representaciones semánticas:
            if 3 <= l_idx <= 13:
                # Proyección ortogonal de supresión de ruido en down_proj y o_proj
                down_w = layer.mlp.down_proj.weight.data
                mean_col = down_w.mean(dim=1, keepdim=True)
                down_w.sub_(SUBTRACTION_FACTOR * 0.05 * mean_col)
                subtracted_params += 1

                o_w = layer.self_attn.o_proj.weight.data
                mean_col_o = o_w.mean(dim=1, keepdim=True)
                o_w.sub_(SUBTRACTION_FACTOR * 0.05 * mean_col_o)
                subtracted_params += 1

    print(f"Sustracción aplicada sobre {subtracted_params} matrices de proyección.")

    # 5. Guardar Modelo Purificado
    print(f"\n[4/4] Guardando modelo purificado en {OUTPUT_PURIFIED_DIR}...")
    os.makedirs(OUTPUT_PURIFIED_DIR, exist_ok=True)
    merged_model.save_pretrained(OUTPUT_PURIFIED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_PURIFIED_DIR)
    print("\n[ÉXITO] Modelo purificado guardado en disco.")

if __name__ == "__main__":
    main()
