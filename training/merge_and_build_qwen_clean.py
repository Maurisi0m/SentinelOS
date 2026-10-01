#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusión Limpia de SENTINEL Qwen2.5-1.5B (28L) y Compilación GGUF de Producción
Usa save_pretrained nativo para preservar la sincronización perfecta de tie_word_embeddings
(model.embed_tokens y lm_head), garantizando la máxima coherencia en español y STEM.
"""

import os
import sys
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "stem_qwen_adapters")
OUTPUT_DIR = os.path.join(BASE_DIR, "export", "sentinel_qwen_fused")
GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
LLAMA_REPO = os.path.join(BASE_DIR, "export", "llama_repo")
CONVERTER = os.path.join(LLAMA_REPO, "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

F16_GGUF = os.path.join(GGUF_DIR, "sentinel-stem-qwen.f16.gguf")
Q4_GGUF = os.path.join(GGUF_DIR, "sentinel-stem-qwen.Q4_K_M.gguf")
Q8_GGUF = os.path.join(GGUF_DIR, "sentinel-stem-qwen.Q8_0.gguf")

def main():
    print("=" * 80)
    print("FUSIÓN LIMPIA Y COMPILACIÓN GGUF DE SENTINEL-1.5B STEM")
    print("=" * 80)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(GGUF_DIR, exist_ok=True)

    # 1. Cargar y Fusionar
    print("\n[1/3] Cargando y fusionando con save_pretrained nativo...")
    tokenizer = AutoTokenizer.from_pretrained(ADAPTERS_DIR)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map={"": device},
        low_cpu_mem_usage=True,
    )

    peft_model = PeftModel.from_pretrained(base_model, ADAPTERS_DIR)
    merged_model = peft_model.merge_and_unload()

    print(f"Guardando modelo en: {OUTPUT_DIR}...")
    merged_model.save_pretrained(OUTPUT_DIR, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_DIR)

    del peft_model
    del base_model
    del merged_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 2. Convertir a GGUF F16
    print("\n[2/3] Convirtiendo a GGUF F16 con convert_hf_to_gguf.py...")
    cmd_convert = [
        sys.executable, CONVERTER,
        OUTPUT_DIR,
        "--outfile", F16_GGUF,
        "--outtype", "f16"
    ]
    res = subprocess.run(cmd_convert, cwd=LLAMA_REPO)
    if res.returncode != 0:
        print("[ERROR] Fallo en convert_hf_to_gguf.")
        sys.exit(1)

    # 3. Cuantizar a Q4_K_M y Q8_0
    print("\n[3/3] Cuantizando a Q4_K_M y Q8_0...")
    subprocess.run([QUANTIZER, F16_GGUF, Q4_GGUF, "Q4_K_M"])
    subprocess.run([QUANTIZER, F16_GGUF, Q8_GGUF, "Q8_0"])

    if os.path.exists(F16_GGUF):
        os.remove(F16_GGUF)

    print("\n" + "=" * 80)
    print("BINARIOS GGUF REGENERADOS LIMPIOS:")
    if os.path.exists(Q4_GGUF):
        print(f"Q4_K_M : {Q4_GGUF} ({os.path.getsize(Q4_GGUF)/(1024*1024):.2f} MB)")
    if os.path.exists(Q8_GGUF):
        print(f"Q8_0   : {Q8_GGUF} ({os.path.getsize(Q8_GGUF)/(1024*1024):.2f} MB)")
    print("=" * 80)

if __name__ == "__main__":
    main()
