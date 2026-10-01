#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL Master Ultimate: Fusión Multitarea + Poda Lingüística + Cuantización Calibrada con iMatrix
1. Fusiona adaptadores DPO (Guardarraíles C/ESP32) y adaptadores R1 (Razonamiento CoT reflexivo).
2. Extirpa alfabetos ajenos no-STEM anulando a cero los embeddings correspondientes.
3. Convierte el modelo unificado a GGUF F16.
4. Cuantiza a Q4_K_M utilizando la matriz de importancia calculada en el corpus STEM (sentinel.imatrix).
"""

import os
import sys
import shutil
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from safetensors.torch import load_file, save_file
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
DPO_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "dpo_adapters_3b")
R1_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "r1_reasoning_adapters_3b")
MERGED_DIR = os.path.join(BASE_DIR, "export", "sentinel_master_ultimate")
OUTPUT_GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
IMATRIX_FILE = os.path.join(OUTPUT_GGUF_DIR, "sentinel.imatrix")
LLAMA_REPO = os.path.join(BASE_DIR, "export", "llama_repo")
CONVERTER = os.path.join(LLAMA_REPO, "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

F16_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-master-ultimate.f16.gguf")
FINAL_Q4 = os.path.join(OUTPUT_GGUF_DIR, "sentinel-master.Q4_K_M.gguf")

NON_LATIN_PATTERNS = [
    re.compile(r'[\u0400-\u04ff]'),  # Cirílico
    re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]'),  # CJK Unificado
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
    
    # Manejar shards si existen, o model.safetensors directo
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
    print("PIPELINE DE FUSIÓN ULTIMATE Y CUANTIZACIÓN IMATRIX DE SENTINEL-3B")
    print("=" * 80)
    os.makedirs(MERGED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_GGUF_DIR, exist_ok=True)

    # 1. Cargar modelo base
    print("\n[1/6] Cargando modelo base Llama-3.2-3B en memoria...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        low_cpu_mem_usage=True,
    )

    # 2. Fusión DPO (Seguridad de memoria C y ESP32)
    print("\n[2/6] Fusionando adaptadores LoRA DPO (Guardarraíles de C y ESP32)...")
    model_dpo = PeftModel.from_pretrained(base_model, DPO_ADAPTERS_DIR)
    fused_model = model_dpo.merge_and_unload()
    del model_dpo

    # 3. Fusión R1 (Razonamiento reflexivo y duda metódica)
    if os.path.exists(R1_ADAPTERS_DIR):
        print("\n[3/6] Fusionando adaptadores LoRA R1 (Razonamiento profundo reflexivo)...")
        model_r1 = PeftModel.from_pretrained(fused_model, R1_ADAPTERS_DIR)
        fused_model = model_r1.merge_and_unload()
        del model_r1
    else:
        print("\n[3/6] Advertencia: No se encontraron adaptadores R1, continuando con DPO.")

    print(f"\n[4/6] Guardando modelo unificado en {MERGED_DIR}...")
    fused_model.save_pretrained(MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_DIR)
    del fused_model
    del base_model
    import gc
    gc.collect()

    # Cirugía de vocabulario
    prune_model_embeddings(MERGED_DIR)

    # 5. Convertir a GGUF F16
    print("\n[5/6] Convirtiendo modelo a GGUF F16...")
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

    # 6. Cuantización con iMatrix (STEM Calibrated)
    print(f"\n[6/6] Cuantizando a Q4_K_M con calibración de sensibilidad iMatrix ({IMATRIX_FILE})...")
    if os.path.exists(IMATRIX_FILE):
        cmd_quant = [
            QUANTIZER,
            "--imatrix", IMATRIX_FILE,
            F16_GGUF,
            FINAL_Q4,
            "Q4_K_M"
        ]
    else:
        print("[AVISO] iMatrix no encontrada, cuantizando estándar Q4_K_M...")
        cmd_quant = [QUANTIZER, F16_GGUF, FINAL_Q4, "Q4_K_M"]

    res_quant = subprocess.run(cmd_quant)
    if res_quant.returncode != 0:
        print("[ERROR] Falló la cuantización Q4_K_M.")
        return

    if os.path.exists(F16_GGUF):
        os.remove(F16_GGUF)

    size_mb = os.path.getsize(FINAL_Q4) / (1024 * 1024)
    print("\n" + "=" * 80)
    print(f"¡ÉXITO TOTAL! SENTINEL-MASTER Q4_K_M CALIBRADO CON IMATRIX: {FINAL_Q4}")
    print(f"Tamaño final en disco: {size_mb:.2f} MB")
    print("=" * 80)

if __name__ == "__main__":
    main()
