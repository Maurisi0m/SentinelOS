#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Cirugía de Vocabulario: Extirpación de Alfabetos Ajenos
Identifica y anula a cero absoluto en model.embed_tokens.weight los tokens
de alfabetos no latinos: Cirílico, CJK (Chino/Japonés), Árabe, Devanagari,
Hebreo, Tailandés, Coreano y Emojis, preservando al 100% el Español, Inglés,
símbolos matemáticos/griegos, código y bytes de respaldo UTF-8.
"""

import os
import re
import torch
from transformers import AutoTokenizer
from safetensors.torch import load_file, save_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_root_pruned")
SAFETENSORS_PATH = os.path.join(MODEL_DIR, "model.safetensors")

# Expresiones regulares para detectar alfabetos ajenos
NON_LATIN_PATTERNS = [
    re.compile(r'[\u0400-\u04ff]'),  # Cirílico (Ruso, etc.)
    re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]'),  # CJK Unificado (Chino)
    re.compile(r'[\u3040-\u30ff]'),  # Japonés (Hiragana/Katakana)
    re.compile(r'[\uac00-\ud7af]'),  # Coreano (Hangul)
    re.compile(r'[\u0600-\u06ff]'),  # Árabe
    re.compile(r'[\u0900-\u097f]'),  # Devanagari (Hindi)
    re.compile(r'[\u0e00-\u0e7f]'),  # Tailandés
    re.compile(r'[\u0590-\u05ff]'),  # Hebreo
    re.compile(r'[\U0001F000-\U0001FAFF]'),  # Emojis y pictogramas
]

def contains_non_latin(token_str):
    for pat in NON_LATIN_PATTERNS:
        if pat.search(token_str):
            return True
    return False

def main():
    print("=" * 80)
    print("INICIANDO EXTIRPACIÓN DE ALFABETOS AJENOS EN LOS PESOS DEL MODELO")
    print(f"Modelo: {MODEL_DIR}")
    print("=" * 80)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    vocab = tokenizer.get_vocab()
    print(f"Vocabulario total: {len(vocab)} tokens")

    # Identificar tokens esenciales a proteger bajo cualquier circunstancia
    protected_ids = set(tokenizer.all_special_ids)
    # Todos los bytes UTF-8 (0 a 255)
    for b in range(256):
        b_tok = tokenizer.encode(chr(b), add_special_tokens=False)
        protected_ids.update(b_tok)

    # Letras griegas comunes en física/matemáticas que DEBEN protegerse
    greek_math = "α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω Γ Δ Θ Λ Ξ Π Σ Φ Ψ Ω ≈ ≠ ≤ ≥ ± ∞ ∫ ∑ √ ∂ ∇ ∈ ∉ ⊂ ⊆ ∪ ∩ ∧ ∨ ¬ → ↔ ⇒ ⇔ ℝ ℂ ℕ ℤ ℚ"
    protected_ids.update(tokenizer.encode(greek_math, add_special_tokens=False))

    print("\nAnalizando los 128,256 tokens decodificando sus cadenas Unicode reales...")
    foreign_token_ids = []
    
    # Evaluar por lotes para velocidad
    total_tokens = len(vocab)
    for tid in range(total_tokens):
        if tid in protected_ids:
            continue
            
        try:
            decoded = tokenizer.decode([tid], errors='ignore')
        except Exception:
            continue
            
        if contains_non_latin(decoded):
            foreign_token_ids.append(tid)

    print(f"\nTokens extranjeros identificados para extirpación: {len(foreign_token_ids)}")
    print(f"Porcentaje de vocabulario no-STEM/ajeno a podar: {len(foreign_token_ids) / total_tokens * 100:.2f}%")

    print("\nCargando tensores para anulación física a cero absoluto...")
    weights = load_file(SAFETENSORS_PATH)
    embed_weights = weights["model.embed_tokens.weight"].clone().to(torch.float32)

    # Anular vectores a cero absoluto
    for fid in foreign_token_ids:
        embed_weights[fid] = 0.0

    weights["model.embed_tokens.weight"] = embed_weights.to(torch.bfloat16)
    
    print("Guardando tensores con extirpación lingüística...")
    save_file(weights, SAFETENSORS_PATH)
    print("[ÉXITO] Extirpación de alfabetos completada. Pesos guardados.")

if __name__ == "__main__":
    main()
