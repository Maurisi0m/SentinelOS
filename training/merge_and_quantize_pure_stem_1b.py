#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Fusión, Cirugía Lingüística y Cuantización para SENTINEL PURE STEM (1B)
-----------------------------------------------------------------------------------
1. Carga el modelo base Llama 3.2 1B en float16.
2. Fusiona los adaptadores LoRA de alta densidad (pure_stem_adapters_1b).
3. Cirugía Lingüística Física: Extirpación de embeddings no-STEM preservando caracteres matemáticos y griegos.
4. Conversión a GGUF F16.
5. Cuantización calibrada con iMatrix hacia Q4_K_M (sentinel-pure-stem-1b.Q4_K_M.gguf).
"""

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

import os
import shutil
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from safetensors.torch import load_file, save_file
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "unsloth/Llama-3.2-1B-Instruct"
ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "pure_stem_adapters_1b")
MERGED_DIR = os.path.join(BASE_DIR, "export", "sentinel_pure_stem_1b_merged")
OUTPUT_GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
IMATRIX_FILE = os.path.join(OUTPUT_GGUF_DIR, "sentinel.imatrix")
LLAMA_REPO = os.path.join(BASE_DIR, "export", "llama_repo")
CONVERTER = os.path.join(LLAMA_REPO, "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

F16_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-pure-stem-1b.f16.gguf")
FINAL_Q4 = os.path.join(OUTPUT_GGUF_DIR, "sentinel-pure-stem-1b.Q4_K_M.gguf")

NON_LATIN_PATTERNS = [
    re.compile(r'[\u0400-\u04ff]'),  # Cirílico
    re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]'),  # CJK
    re.compile(r'[\u3040-\u30ff]'),  # Japonés
    re.compile(r'[\uac00-\ud7af]'),  # Coreano
    re.compile(r'[\u0600-\u06ff]'),  # Árabe
    re.compile(r'[\u0900-\u097f]'),  # Devanagari
    re.compile(r'[\u0e00-\u0e7f]'),  # Tailandés
    re.compile(r'[\u0590-\u05ff]'),  # Hebreo
    re.compile(r'[\U0001F000-\U0001FAFF]'),  # Emojis
]

def contains_non_latin(token_str):
    for pat in NON_LATIN_PATTERNS:
        if pat.search(token_str):
            return True
    return False

def prune_model_embeddings(model_dir):
    print("\n[Cirugía Lingüística] Extirpando tokens ajenos no-STEM de los embeddings...")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    vocab = tokenizer.get_vocab()
    protected_ids = set(tokenizer.all_special_ids)
    for b in range(256):
        protected_ids.update(tokenizer.encode(chr(b), add_special_tokens=False))
    greek_math = "α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω Γ Δ Θ Λ Ξ Π Σ Φ Ψ Ω ≈ ≠ ≤ ≥ ± ∞ ∫ ∑ √ ∂ ∇ ∈ ∉ ⊂ ⊆ ∪ ∩ ∧ ∨ ¬ → ↔ ⇒ ⇔ ℝ ℂ ℕ ℤ ℚ"
    protected_ids.update(tokenizer.encode(greek_math, add_special_tokens=False))

    foreign_token_ids = []
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

    print(f"Tokens no-STEM identificados: {len(foreign_token_ids)} ({len(foreign_token_ids)/total_tokens*100:.2f}%)")
    
    safetensors_files = [f for f in os.listdir(model_dir) if f.endswith(".safetensors")]
    for st_file in safetensors_files:
        st_path = os.path.join(model_dir, st_file)
        weights = load_file(st_path)
        if "model.embed_tokens.weight" in weights:
            print(f"Aplicando anulación de embeddings en {st_file}...")
            embed = weights["model.embed_tokens.weight"].clone().to(torch.float32)
            for fid in foreign_token_ids:
                embed[fid] = 0.0
            weights["model.embed_tokens.weight"] = embed.to(torch.bfloat16)
            save_file(weights, st_path)
            print("Embeddings podados guardados exitosamente.")
            break

def main():
    print("=" * 80)
    print("PIPELINE DE FUSIÓN Y COMPILACIÓN GGUF: SENTINEL PURE STEM (1B)")
    print("=" * 80)
    os.makedirs(MERGED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_GGUF_DIR, exist_ok=True)

    if not os.path.exists(ADAPTERS_DIR):
        print(f"[ERROR]: Adaptadores no encontrados en {ADAPTERS_DIR}.")
        return

    # 1. Cargar modelo base 1B
    print("\n[1/5] Cargando modelo base 1B en memoria...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, local_files_only=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        low_cpu_mem_usage=True,
        local_files_only=True
    )

    # 2. Fusión de Pure STEM 1B Adapters
    print(f"\n[2/5] Fusionando adaptadores Pure STEM 1B desde {ADAPTERS_DIR}...")
    model_peft = PeftModel.from_pretrained(base_model, ADAPTERS_DIR)
    fused_model = model_peft.merge_and_unload()
    del model_peft

    print(f"Guardando modelo fusionado en {MERGED_DIR}...")
    fused_model.save_pretrained(MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_DIR)
    del fused_model
    del base_model
    import gc
    gc.collect()

    # 3. Cirugía Lingüística
    prune_model_embeddings(MERGED_DIR)

    # 4. Convertir a GGUF F16
    print("\n[4/5] Convirtiendo a GGUF F16...")
    cmd_convert = [
        sys.executable, CONVERTER,
        MERGED_DIR,
        "--outfile", F16_GGUF,
        "--outtype", "f16"
    ]
    res_conv = subprocess.run(cmd_convert, cwd=LLAMA_REPO)
    if res_conv.returncode != 0:
        print("[ERROR] Falló la conversión a GGUF F16.")
        return

    # 5. Cuantización con iMatrix
    print(f"\n[5/5] Cuantizando a {FINAL_Q4}...")
    cmd_quant = [
        QUANTIZER,
        "--imatrix", IMATRIX_FILE,
        F16_GGUF,
        FINAL_Q4,
        "Q4_K_M"
    ]
    res_quant = subprocess.run(cmd_quant)
    if res_quant.returncode != 0:
        print("[ERROR] Falló la cuantización Q4_K_M.")
        return

    if os.path.exists(F16_GGUF):
        os.remove(F16_GGUF)

    size_mb = os.path.getsize(FINAL_Q4) / (1024 * 1024)
    print("\n" + "=" * 80)
    print(f"¡ÉXITO TOTAL! SENTINEL PURE STEM 1B COMPILADO: {FINAL_Q4} ({size_mb:.2f} MB)")
    print("=" * 80)

if __name__ == "__main__":
    main()
