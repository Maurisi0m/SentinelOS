#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL Merge & GGUF Quantization Pipeline
1. Fusiona los adaptadores LoRA entrenados con el modelo base Llama-3.2-3B-Instruct.
2. Exporta el modelo unificado a safetensors en float16.
3. Convierte a GGUF (FP16).
4. Cuantiza directamente a formato Q4_K_M produciendo 'sentinel-stem.Q4_K_M.gguf'.
"""

import os
import sys
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "adapters")
MERGED_DIR = os.path.join(BASE_DIR, "export", "merged_model")
OUTPUT_GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
CONVERT_SCRIPT = os.path.join(BASE_DIR, "export", "llama_repo", "convert_hf_to_gguf.py")
QUANTIZE_EXE = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")

BF16_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-stem.bf16.gguf")
FINAL_Q4_GGUF = os.path.join(OUTPUT_GGUF_DIR, "sentinel-stem.Q4_K_M.gguf")

def step1_merge_adapters():
    print("=== PASO 1: FUSIÓN DE ADAPTADORES LORA ACTUALIZADOS CON MODELO BASE ===")
    if not os.path.exists(ADAPTERS_DIR):
        raise FileNotFoundError(f"No se encontró el directorio de adaptadores en: {ADAPTERS_DIR}")

    os.makedirs(MERGED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_GGUF_DIR, exist_ok=True)

    print(f"Cargando modelo base {BASE_MODEL_ID} en BF16...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="cpu",  # Fusión en memoria RAM para evitar cualquier OOM en GPU
        low_cpu_mem_usage=True,
    )

    print(f"Cargando y acoplando adaptadores LoRA desde {ADAPTERS_DIR}...")
    model = PeftModel.from_pretrained(base_model, ADAPTERS_DIR)
    
    print("Fusionando pesos (merge_and_unload)...")
    merged_model = model.merge_and_unload()

    print(f"Guardando modelo unificado safetensors en {MERGED_DIR}...")
    merged_model.save_pretrained(MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_DIR)
    print("[OK] Fusión completada con éxito.")

def step2_convert_to_gguf():
    print("=== PASO 2: CONVERSIÓN SAFETENSORS A GGUF (BF16) ===")
    python_exe = sys.executable
    cmd = [
        python_exe,
        CONVERT_SCRIPT,
        MERGED_DIR,
        "--outfile", BF16_GGUF,
        "--outtype", "bf16"
    ]
    print("Ejecutando:", " ".join(cmd))
    res = subprocess.run(cmd, check=True)
    if not os.path.exists(BF16_GGUF):
        raise RuntimeError("Fallo al generar el archivo GGUF BF16.")
    size_mb = os.path.getsize(BF16_GGUF) / (1024**2)
    print(f"[OK] GGUF BF16 generado: {BF16_GGUF} ({size_mb:.2f} MB)")

def step3_quantize_q4_k_m():
    print("=== PASO 3: CUANTIZACIÓN A Q4_K_M (sentinel-stem.Q4_K_M.gguf) ===")
    if not os.path.exists(QUANTIZE_EXE):
        raise FileNotFoundError(f"No se encontró el ejecutable: {QUANTIZE_EXE}")

    cmd = [
        QUANTIZE_EXE,
        BF16_GGUF,
        FINAL_Q4_GGUF,
        "Q4_K_M",
        "4" # 4 hilos CPU para no saturar
    ]
    print("Ejecutando:", " ".join(cmd))
    res = subprocess.run(cmd, check=True)

    if not os.path.exists(FINAL_Q4_GGUF):
        raise RuntimeError("Fallo en la cuantización a Q4_K_M.")
    
    size_mb = os.path.getsize(FINAL_Q4_GGUF) / (1024**2)
    size_gb = size_mb / 1024
    print(f"[ÉXITO TOTAL] MODELO ENTREGADO: {FINAL_Q4_GGUF}")
    print(f"Tamaño final: {size_mb:.2f} MB ({size_gb:.2f} GB)")

    # Limpiar archivo temporal intermedio para ahorrar espacio
    if os.path.exists(BF16_GGUF):
        try:
            os.remove(BF16_GGUF)
            print("Archivo temporal BF16 eliminado para ahorrar espacio.")
        except Exception:
            pass

if __name__ == "__main__":
    step1_merge_adapters()
    step2_convert_to_gguf()
    step3_quantize_q4_k_m()
