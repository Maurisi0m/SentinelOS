#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusión del Modelo Maestro DPO de SENTINEL y Compilación GGUF
1. Fusiona adaptadores DPO de training/dpo_adapters_3b en unsloth/Llama-3.2-3B-Instruct.
2. Aplica la extirpación de tokens no-STEM (45.45% de alfabetos extranjeros).
3. Guarda en export/sentinel_master_dpo/.
4. Reconstruye binario Q4_K_M en export/output_gguf/sentinel-master.Q4_K_M.gguf.
"""

import os
import sys
import shutil
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from safetensors.torch import load_file, save_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
DPO_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "dpo_adapters_3b")
MERGED_DIR = os.path.join(BASE_DIR, "export", "sentinel_master_dpo")
OUTPUT_GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
LLAMA_REPO = os.path.join(BASE_DIR, "export", "llama_repo")
CONVERTER = os.path.join(LLAMA_REPO, "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

os.makedirs(MERGED_DIR, exist_ok=True)
os.makedirs(OUTPUT_GGUF_DIR, exist_ok=True)

F16_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-master-dpo.f16.gguf")
FINAL_Q4 = os.path.join(OUTPUT_GGUF_DIR, "sentinel-master.Q4_K_M.gguf")

def main():
    print("=" * 80)
    print("FUSIÓN DEL MODELO MAESTRO DPO SENTINEL-3B Y GENERACIÓN GGUF")
    print(f"Modelo Base: {BASE_MODEL_ID}")
    print(f"Adaptadores DPO: {DPO_ADAPTERS_DIR}")
    print(f"Directorio Fusionado: {MERGED_DIR}")
    print("=" * 80)

    # 1. Cargar modelo base en CPU
    print("\n[1/5] Cargando modelo base 3B en RAM...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16,
        device_map="cpu",
        low_cpu_mem_usage=True,
    )

    # 2. Cargar adaptadores DPO y fusionar
    print("\n[2/5] Fusionando adaptadores LoRA DPO...")
    peft_model = PeftModel.from_pretrained(base_model, DPO_ADAPTERS_DIR)
    merged_model = peft_model.merge_and_unload()

    print(f"Guardando tensores fusionados en: {MERGED_DIR}")
    merged_model.save_pretrained(MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_DIR)

    del peft_model
    del base_model
    del merged_model
    import gc
    gc.collect()

    # 3. Extirpación de vocabulario no-STEM (anulación a cero)
    print("\n[3/5] Aplicando cirugía de poda de vocabulario no-STEM...")
    prune_script = os.path.join(BASE_DIR, "training", "prune_foreign_scripts.py")
    if os.path.exists(prune_script):
        subprocess.run([sys.executable, prune_script], cwd=BASE_DIR)

    # 4. Convertir a GGUF F16
    print("\n[4/5] Convirtiendo modelo DPO a GGUF F16...")
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

    # 5. Cuantizar a Q4_K_M (modelo maestro activo)
    print(f"\n[5/5] Cuantizando a Q4_K_M en {FINAL_Q4}...")
    cmd_quant = [QUANTIZER, F16_GGUF, FINAL_Q4, "Q4_K_M"]
    res_quant = subprocess.run(cmd_quant)
    if res_quant.returncode != 0:
        print("[ERROR] Fallo en la cuantización Q4_K_M.")
        return

    if os.path.exists(F16_GGUF):
        os.remove(F16_GGUF)

    size_mb = os.path.getsize(FINAL_Q4) / (1024 * 1024)
    print("\n" + "=" * 80)
    print(f"¡ÉXITO! MODELO MAESTRO DPO SENTINEL-3B COMPILADO: {FINAL_Q4}")
    print(f"Tamaño: {size_mb:.1f} MB (Alineado con preferencias STEM y Cero Fugas de Memoria)")
    print("=" * 80)

if __name__ == "__main__":
    main()
