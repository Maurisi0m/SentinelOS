#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Fusión, Conversión a GGUF y Cuantización: SENTINEL-1B-PureSTEM & Terminal Operator
--------------------------------------------------------------------------------------------
1. Carga el modelo base desaprendido (export/sentinel_1b_unlearned).
2. Fusiona los adaptadores LoRA agénticos (training/agentic_terminal_adapters_1b).
3. Guarda el modelo fusionado en Safetensors de precisión completa (export/sentinel_agentic_1b_merged).
4. Convierte a GGUF F16 mediante export/llama_repo/convert_hf_to_gguf.py.
5. Cuantiza a Q4_K_M mediante export/bin/llama-quantize.exe.
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

import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNLEARNED_MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_1b_unlearned")
BASE_SNAPSHOT_DIR = r"C:\Users\mauro\.cache\huggingface\hub\models--unsloth--Llama-3.2-1B-Instruct\snapshots\5a8abab4a5d6f164389b1079fb721cfab8d7126c"
BASE_MODEL_TO_USE = UNLEARNED_MODEL_DIR if os.path.exists(os.path.join(UNLEARNED_MODEL_DIR, "model.safetensors")) else BASE_SNAPSHOT_DIR

# Buscar automáticamente el checkpoint más reciente
checkpoint_dirs = sorted(
    glob.glob(os.path.join(BASE_DIR, "training", "agentic_terminal_adapters_1b", "checkpoint-*")),
    key=lambda d: int(os.path.basename(d).split("-")[-1]) if "-" in os.path.basename(d) and os.path.basename(d).split("-")[-1].isdigit() else 0
)
ADAPTERS_DIR = checkpoint_dirs[-1] if checkpoint_dirs else os.path.join(BASE_DIR, "training", "agentic_terminal_adapters_1b")

MERGED_DIR = os.path.join(BASE_DIR, "export", "sentinel_agentic_1b_merged")
OUTPUT_GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")

CONVERTER = os.path.join(BASE_DIR, "export", "llama_repo", "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

F16_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-agentic-1b.f16.gguf")
FINAL_Q4 = os.path.join(OUTPUT_GGUF_DIR, "sentinel-agentic-1b.Q4_K_M.gguf")

def main():
    print("=" * 80)
    print("FUSIÓN Y COMPILACIÓN GGUF: SENTINEL-1B-PureSTEM & Terminal Operator")
    print(f"Modelo Base: {BASE_MODEL_TO_USE}")
    print(f"Adaptadores Agénticos (Checkpoint): {ADAPTERS_DIR}")
    print(f"Destino Fusionado: {MERGED_DIR}")
    print(f"Destino GGUF Final: {FINAL_Q4}")
    print("=" * 80)

    os.makedirs(MERGED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_GGUF_DIR, exist_ok=True)

    print("\n[1/4] Cargando modelo base en CPU (torch.float16)...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_TO_USE,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="cpu"
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_SNAPSHOT_DIR if os.path.exists(BASE_SNAPSHOT_DIR) else BASE_MODEL_TO_USE)

    print("[2/4] Fusionando adaptadores LoRA de terminal en los tensores base...")
    model = PeftModel.from_pretrained(base_model, ADAPTERS_DIR)
    merged_model = model.merge_and_unload()

    print(f"Guardando modelo fusionado standalone en {MERGED_DIR}...")
    merged_model.save_pretrained(MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_DIR)

    print("\n[3/4] Convirtiendo modelo fusionado a formato binario GGUF F16...")
    conv_cmd = [
        sys.executable,
        CONVERTER,
        MERGED_DIR,
        "--outfile", F16_GGUF,
        "--outtype", "f16"
    ]
    res = subprocess.run(conv_cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.returncode != 0:
        print("[ERROR en convert_hf_to_gguf]:", res.stderr)
        sys.exit(res.returncode)
    print(f"[OK] F16 GGUF generado: {F16_GGUF} (Tamaño: {os.path.getsize(F16_GGUF) / (1024**2):.2f} MB)")

    print(f"\n[4/4] Cuantizando hacia Q4_K_M mediante {QUANTIZER}...")
    q_cmd = [QUANTIZER, F16_GGUF, FINAL_Q4, "Q4_K_M"]
    res_q = subprocess.run(q_cmd, capture_output=True, text=True)
    if res_q.stdout:
        print(res_q.stdout)
    if res_q.returncode != 0:
        print("[ERROR en llama-quantize]:", res_q.stderr)
        sys.exit(res_q.returncode)
        
    print("=" * 80)
    print(f"[ÉXITO TOTAL] Binario compilado y cuantizado listo para despliegue:")
    print(f"-> {FINAL_Q4} (Tamaño: {os.path.getsize(FINAL_Q4) / (1024**2):.2f} MB)")
    print("=" * 80)

if __name__ == "__main__":
    main()
