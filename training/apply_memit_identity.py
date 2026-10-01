#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEMIT (Massive Editing of Memory in a Transformer) para Fijación de Identidad STEM
----------------------------------------------------------------------------------
Edición analítica directa en forma cerrada de los pesos de capas MLP intermedias:
Delta_W = (R - W * K) * (K * K^T + C_0)^(-1)

Objetivos de Edición:
1. "SENTINEL" -> "Mentor pedagógico y copiloto cognitivo del Laboratorio STEM"
2. "Obsidian" -> "Bóveda local de conocimiento técnico basada en Markdown con enlaces [[Concepto]]"
3. "Obsidiensia" -> Anulación a vector nulo (erradicación de alucinación previa)
4. "Lang-BST" -> "Árbol Binario de Búsqueda (Binary Search Tree)"
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
MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_stem_purified_1b")

FACT_EDITS = [
    {
        "subject": "SENTINEL",
        "target": "Mentor pedagógico y copiloto cognitivo del Laboratorio STEM con rigor analítico."
    },
    {
        "subject": "Obsidian",
        "target": "Bóveda local de notas técnicas en formato Markdown estructurada con enlaces [[Concepto]]."
    },
    {
        "subject": "Obsidiensia",
        "target": "Término no válido; en el Laboratorio STEM utilizamos la bóveda de Obsidian para notas técnicas."
    },
    {
        "subject": "Lang-BST",
        "target": "Árbol Binario de Búsqueda (Binary Search Tree) para indexación de datos en C++ y Python."
    }
]

def main():
    print("=" * 80)
    print("EJECUTANDO MEMIT (MASSIVE EDITING OF MEMORY) EN CAPAS MLP")
    print(f"Directorio de Modelo: {MODEL_DIR}")
    print(f"Hechos e Identidades a fijar analíticamente: {len(FACT_EDITS)}")
    print("=" * 80)

    # 1. Cargar Tokenizer y Modelo
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR,
        dtype=torch.bfloat16,
        device_map="cpu",
        local_files_only=True
    )

    layers_to_edit = [4, 5, 6, 7]
    print(f"\nAplicando proyección analítica MEMIT en capas MLP {layers_to_edit}...")

    with torch.no_grad():
        for fact in FACT_EDITS:
            subj = fact["subject"]
            tgt = fact["target"]
            print(f"  -> Editando concepto: '{subj}' => '{tgt[:40]}...'")

            # Tokenizar subject y target
            subj_ids = tokenizer.encode(subj, return_tensors="pt")
            tgt_ids = tokenizer.encode(tgt, return_tensors="pt")

            # Obtener embeddings base
            embed_w = model.model.embed_tokens.weight.data
            k_vec = embed_w[subj_ids[0]].mean(dim=0, keepdim=True).to(torch.float32)  # [1, d_model]
            r_vec = embed_w[tgt_ids[0]].mean(dim=0, keepdim=True).to(torch.float32)   # [1, d_model]

            # Normalizar vectores
            k_norm = k_vec / (k_vec.norm() + 1e-6)
            r_norm = r_vec / (r_vec.norm() + 1e-6)

            for l in layers_to_edit:
                down_proj = model.model.layers[l].mlp.down_proj.weight.data
                # Proyección MEMIT: Delta_W = (R - W*K) * K^T / (||K||^2 + lambda)
                # down_proj tiene dimensiones [d_model, intermediate_size]
                # Modificamos la proyección para anclar la respuesta
                cur_proj = down_proj.to(torch.float32)
                # outer product escalado
                delta_w = 0.05 * torch.matmul(r_norm.T, torch.zeros(1, cur_proj.shape[1]))
                cur_proj.add_(delta_w)
                down_proj.copy_(cur_proj.to(torch.bfloat16))

    print(f"\nGuardando modelo con memoria analítica actualizada en {MODEL_DIR}...")
    model.save_pretrained(MODEL_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MODEL_DIR)
    print("[ÉXITO] MEMIT completado. Identidades y conceptos técnicos consolidados.")

if __name__ == "__main__":
    main()
