#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusión del Modelo Maestro SENTINEL (28 Capas) y Poda de Vocabulario No-STEM
1. Fusiona los adaptadores de training/master_adapters_28l en unsloth/Llama-3.2-3B-Instruct.
2. Guarda el modelo resultante en export/sentinel_master_28l.
3. Extirpa quirúrgicamente el 45.45% de tokens no-STEM (árabe, cirílico, asiático).
4. Reconstruye los binarios GGUF Q8_0 y Q4_K_M en export/output_gguf.
"""

import os
import sys
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from safetensors.torch import load_file, save_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "master_adapters_28l")
TARGET_DIR = os.path.join(BASE_DIR, "export", "sentinel_master_28l")
GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
LLAMA_REPO = os.path.join(BASE_DIR, "export", "llama_repo")
CONVERTER = os.path.join(LLAMA_REPO, "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

def main():
    print("=" * 80)
    print("FUSIÓN Y COMPILACIÓN DEL MODELO MAESTRO SENTINEL (28 CAPAS)")
    print("=" * 80)

    # 1. Fusión en RAM
    print("\n[1/4] Cargando modelo base oficial en RAM (BF16)...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        low_cpu_mem_usage=True
    )

    print("[2/4] Acoplando adaptadores maestros LoRA...")
    peft_model = PeftModel.from_pretrained(base_model, ADAPTERS_DIR)
    final_model = peft_model.merge_and_unload()

    print(f"[3/4] Guardando modelo en {TARGET_DIR}...")
    os.makedirs(TARGET_DIR, exist_ok=True)
    final_model.save_pretrained(TARGET_DIR, safe_serialization=True)
    tokenizer.save_pretrained(TARGET_DIR)

    # 2. Poda de vocabulario extranjero en los pesos guardados
    print("\n[4/4] Ejecutando poda de alfabetos extranjeros no-STEM en el modelo maestro...")
    weights_path = os.path.join(TARGET_DIR, "model.safetensors")
    weights = load_file(weights_path)
    embed_weights = weights["model.embed_tokens.weight"].clone().to(torch.float32)

    total_tokens = len(tokenizer)
    foreign_token_ids = []
    
    ALLOWED_RANGES = [
        (0x0000, 0x007F),  # Basic Latin / ASCII
        (0x0080, 0x00FF),  # Latin-1 Supplement (á, é, í, ó, ú, ñ, ¿, ¡)
        (0x0100, 0x017F),  # Latin Extended-A
        (0x0370, 0x03FF),  # Greek and Coptic (Alfa, Beta, Omega, Pi, Mu)
        (0x2000, 0x206F),  # General Punctuation
        (0x2070, 0x209F),  # Superscripts and Subscripts
        (0x2100, 0x214F),  # Letterlike Symbols
        (0x2190, 0x21FF),  # Arrows
        (0x2200, 0x22FF),  # Mathematical Operators (integral, sumatoria, etc)
        (0x2300, 0x23FF),  # Miscellaneous Technical
    ]

    def is_allowed_char(char):
        code = ord(char)
        return any(start <= code <= end for start, end in ALLOWED_RANGES)

    for token_id in range(total_tokens):
        token_str = tokenizer.decode([token_id])
        if any(not is_allowed_char(c) for c in token_str):
            foreign_token_ids.append(token_id)

    print(f"Extirpando {len(foreign_token_ids)} tokens no-STEM ({len(foreign_token_ids)/total_tokens*100:.2f}% del vocabulario)...")
    for fid in foreign_token_ids:
        embed_weights[fid] = 0.0

    weights["model.embed_tokens.weight"] = embed_weights.to(torch.bfloat16)
    save_file(weights, weights_path)
    print("[OK] Poda de vocabulario completada.")

    # 3. Compilación GGUF
    print("\n" + "=" * 80)
    print("COMPILANDO BINARIOS GGUF MAESTROS PARA SERVIDOR HP UBUNTU")
    print("=" * 80)

    f16_path = os.path.join(GGUF_DIR, "sentinel-master.f16.gguf")
    q8_path = os.path.join(GGUF_DIR, "sentinel-master.Q8_0.gguf")
    q4_path = os.path.join(GGUF_DIR, "sentinel-master.Q4_K_M.gguf")

    print("\nConvirtiendo a GGUF F16...")
    cmd_conv = [sys.executable, CONVERTER, TARGET_DIR, "--outfile", f16_path, "--outtype", "f16"]
    subprocess.run(cmd_conv, cwd=LLAMA_REPO, check=True)

    print("\nCuantizando a Q8_0 (Alta fidelidad didáctica)...")
    subprocess.run([QUANTIZER, f16_path, q8_path, "Q8_0"], check=True)

    print("\nCuantizando a Q4_K_M (Máxima velocidad Core i5)...")
    subprocess.run([QUANTIZER, f16_path, q4_path, "Q4_K_M"], check=True)

    if os.path.exists(f16_path):
        os.remove(f16_path)

    print("\n" + "=" * 80)
    print("¡BINARIOS MAESTROS COMPLETADOS!")
    print(f"Q8_0  : {q8_path} ({os.path.getsize(q8_path)/(1024*1024):.2f} MB)")
    print(f"Q4_K_M: {q4_path} ({os.path.getsize(q4_path)/(1024*1024):.2f} MB)")
    print("=" * 80)

if __name__ == "__main__":
    main()
