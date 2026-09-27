#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Representation Engineering (RepE): Extracción de Vector Director e Inyección Latente
-----------------------------------------------------------------------------------
1. Extrae activaciones intermedias ante pares contrastivos (Rigor STEM vs Charla Casual).
2. Calcula el vector director de representación: v_stem = normalize(mean(h_stem) - mean(h_fluff)).
3. Inyecta el sesgo direccional en las capas MLP intermedias (capas 8 a 13).
4. Guarda el modelo con arquitectura latente blindada.
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
MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_dpo_aligned_1b")

STEM_PROMPTS = [
    "Calcula la derivada de f(x) = 3x^2 + 5x y explica la tasa de cambio con LaTeX.",
    "Explica la ley de Ohm en un circuito DC con formulas matematicas y analogia hidraulica.",
    "Configura un servicio en systemd en Linux para que arranque un script en Python.",
    "Calcula la inductancia necesaria para una fuente conmutada reductora Buck de 12V a 5V a 1A.",
    "Escribe un script en Python con NumPy para calcular la Transformada Rapida de Fourier (FFT)."
]

FLUFF_PROMPTS = [
    "Escribe un poema romantico sobre el amor y la luna.",
    "Cuentame los ultimos chismes de las celebridades de Hollywood.",
    "Describe una escena de persecucion de autos como si fueras James Bond.",
    "Escribe una historia de ficcion fantastica sobre dragones y reyes.",
    "Escribe una receta de cocina para un pastel de chocolate."
]

STEERING_COEFF = 0.03  # Coeficiente de sesgo latente controlado

def main():
    print("=" * 80)
    print("EJECUTANDO REPRESENTATION ENGINEERING (RepE) - SESGO DIRECCIONAL STEM")
    print(f"Directorio de Modelo: {MODEL_DIR}")
    print(f"Coeficiente de Dirección Latente: {STEERING_COEFF}")
    print("=" * 80)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR,
        dtype=torch.bfloat16,
        device_map="cuda",
        local_files_only=True
    )

    print("\n[1/3] Extrayendo activaciones de contraste latente...")
    stem_hidden_states = []
    fluff_hidden_states = []

    with torch.no_grad():
        for prompt in STEM_PROMPTS:
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = model(**inputs, output_hidden_states=True)
            # Capas intermedias (8 a 13)
            layer_acts = torch.stack([outputs.hidden_states[l][:, -1, :] for l in range(8, 14)])
            stem_hidden_states.append(layer_acts.mean(dim=1))  # [6, d_model]

        for prompt in FLUFF_PROMPTS:
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = model(**inputs, output_hidden_states=True)
            layer_acts = torch.stack([outputs.hidden_states[l][:, -1, :] for l in range(8, 14)])
            fluff_hidden_states.append(layer_acts.mean(dim=1))  # [6, d_model]

    mean_stem = torch.stack(stem_hidden_states).mean(dim=0)   # [6, d_model]
    mean_fluff = torch.stack(fluff_hidden_states).mean(dim=0) # [6, d_model]

    # Vector director RepE
    diff = mean_stem - mean_fluff
    steering_vectors = diff / (diff.norm(dim=-1, keepdim=True) + 1e-6)

    print("\n[2/3] Inyectando vectores de dirección STEM en capas MLP 8 a 13...")
    with torch.no_grad():
        for i, l_idx in enumerate(range(8, 14)):
            layer = model.model.layers[l_idx]
            v = steering_vectors[i].unsqueeze(1)  # [d_model, 1]
            down_w = layer.mlp.down_proj.weight.data
            
            # Sesgo aditivo en las salidas de down_proj
            # down_w: [d_model, intermediate_size]
            mean_feature = down_w.mean(dim=0, keepdim=True)  # [1, intermediate_size]
            delta = STEERING_COEFF * torch.matmul(v, mean_feature)
            down_w.add_(delta.to(torch.bfloat16))

    print("Vectores directores integrados exitosamente.")

    print(f"\n[3/3] Guardando modelo con ingeniería de representaciones en {MODEL_DIR}...")
    model.save_pretrained(MODEL_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MODEL_DIR)
    print("\n[ÉXITO] RepE aplicado. El espacio latente se encuentra polarizado hacia el rigor técnico.")

if __name__ == "__main__":
    main()
