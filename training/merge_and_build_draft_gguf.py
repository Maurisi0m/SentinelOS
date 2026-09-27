#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusión del Modelo Borrador SENTINEL-1B y Compilación GGUF (Q4_K_M)
1. Fusiona adaptadores de training/draft_adapters_1b en unsloth/Llama-3.2-1B-Instruct.
2. Guarda el modelo fusionado en export/sentinel_draft_1b/.
3. Convierte a GGUF F16 y cuantiza a Q4_K_M en export/output_gguf/.
"""

import os
import sys
import shutil
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "unsloth/Llama-3.2-1B-Instruct"
ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "draft_adapters_1b")
MERGED_DIR = os.path.join(BASE_DIR, "export", "sentinel_draft_1b")
OUTPUT_GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
LLAMA_REPO = os.path.join(BASE_DIR, "export", "llama_repo")
CONVERTER = os.path.join(LLAMA_REPO, "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

os.makedirs(MERGED_DIR, exist_ok=True)
os.makedirs(OUTPUT_GGUF_DIR, exist_ok=True)

F16_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-draft-1b.f16.gguf")
Q4_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-draft-1b.Q4_K_M.gguf")

def main():
    print("=" * 80)
    print("FUSIÓN DEL MODELO BORRADOR SENTINEL-1B Y GENERACIÓN GGUF")
    print(f"Modelo Base: {BASE_MODEL_ID}")
    print(f"Adaptadores: {ADAPTERS_DIR}")
    print(f"Directorio Fusionado: {MERGED_DIR}")
    print("=" * 80)

    # 1. Cargar modelo base en CPU/RAM
    print("\n[1/4] Cargando modelo base 1B en RAM...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16,
        device_map="cpu",
        low_cpu_mem_usage=True,
    )

    # 2. Cargar adaptadores y fusionar
    print("\n[2/4] Fusionando adaptadores LoRA del borrador...")
    peft_model = PeftModel.from_pretrained(base_model, ADAPTERS_DIR)
    merged_model = peft_model.merge_and_unload()

    print(f"Guardando tensores fusionados en: {MERGED_DIR}")
    merged_model.save_pretrained(MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_DIR)

    del peft_model
    del base_model
    del merged_model
    import gc
    gc.collect()

    # 3. Convertir a GGUF F16
    print("\n[3/4] Convirtiendo modelo a GGUF F16...")
    cmd_convert = [
        sys.executable, CONVERTER,
        MERGED_DIR,
        "--outfile", F16_GGUF,
        "--outtype", "f16"
    ]
    res_conv = subprocess.run(cmd_convert, cwd=LLAMA_REPO)
    if res_conv.returncode != 0:
        print("[ERROR] Fallo en la conversión a GGUF.")
        return

    # 4. Cuantizar a Q4_K_M (Ultra-liviano para draft)
    print(f"\n[4/4] Cuantizando a Q4_K_M en {Q4_GGUF}...")
    cmd_quant = [QUANTIZER, F16_GGUF, Q4_GGUF, "Q4_K_M"]
    res_quant = subprocess.run(cmd_quant)
    if res_quant.returncode != 0:
        print("[ERROR] Fallo en la cuantización Q4_K_M.")
        return

    # Limpiar el temporal F16
    if os.path.exists(F16_GGUF) and os.path.exists(Q4_GGUF):
        os.remove(F16_GGUF)

    size_mb = os.path.getsize(Q4_GGUF) / (1024 * 1024)
    print("\n" + "=" * 80)
    print(f"¡ÉXITO! MODELO BORRADOR SENTINEL-1B COMPILADO: {Q4_GGUF}")
    print(f"Tamaño: {size_mb:.1f} MB (Optimizado para Speculative Decoding a 100+ tok/s)")
    print("=" * 80)

if __name__ == "__main__":
    main()
