#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL-1.5B STEM: Fusión Completa (28L), Ablación Quirúrgica No-STEM y Compilación GGUF
Conserva el 100% del grafo residual intacto (28 capas) para máxima coherencia en español y STEM,
aplicando ablación de embeddings a cero absoluto para términos culinarios y trivia no técnica.
"""

import os
import sys
import json
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from safetensors.torch import load_file, save_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "stem_qwen_adapters")
OUTPUT_DIR = os.path.join(BASE_DIR, "export", "sentinel_qwen_28l")
GGUF_DIR = os.path.join(BASE_DIR, "export", "output_gguf")
LLAMA_REPO = os.path.join(BASE_DIR, "export", "llama_repo")
CONVERTER = os.path.join(LLAMA_REPO, "convert_hf_to_gguf.py")
QUANTIZER = os.path.join(BASE_DIR, "export", "bin", "llama-quantize.exe")
UNWANTED_CORPUS_PATH = os.path.join(BASE_DIR, "dataset", "unwanted_domain_corpus.jsonl")

F16_GGUF = os.path.join(GGUF_DIR, "sentinel-stem-qwen.f16.gguf")
Q4_GGUF = os.path.join(GGUF_DIR, "sentinel-stem-qwen.Q4_K_M.gguf")
Q8_GGUF = os.path.join(GGUF_DIR, "sentinel-stem-qwen.Q8_0.gguf")

def main():
    print("=" * 80)
    print("SENTINEL-1.5B: FUSIÓN 28L INTACTA + ABLACIÓN NO-STEM + COMPILACIÓN GGUF")
    print("=" * 80)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(GGUF_DIR, exist_ok=True)

    # 1. Fusión de Pesos
    print("\n[1/4] Cargando modelo base y adaptadores LoRA STEM...")
    tokenizer = AutoTokenizer.from_pretrained(ADAPTERS_DIR)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Dispositivo: {device}")
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map={"": device},
        low_cpu_mem_usage=True,
    )

    print("Fusionando adaptadores LoRA STEM en modelo base...")
    peft_model = PeftModel.from_pretrained(base_model, ADAPTERS_DIR)
    merged_model = peft_model.merge_and_unload()

    print("Extrayendo tensores del modelo fusionado...")
    state_dict = merged_model.state_dict()

    # 2. Cirugía de Embeddings (Ablación de Tokens no-STEM)
    print("\n[2/4] Aplicando ablación a cero absoluto en tokens culinarios y trivia no técnica...")
    culinary_unwanted_text = (
        "receta recetas cocinar cocina horneado hornear ingredientes sartén cacerola pastel "
        "harina azúcar levadura salsa carbonara pizza margarita gastronomía postre ensalada "
        "cebolla ajo pimienta salteado sofrito caldo estofado horneando repostería galletas "
        "tarta batidora horno cocinero chef horquilla condimento aderezo mantequilla freír "
        "horóscopo astrología farándula chisme telenovela romance poesía amor apasionado"
    )

    unwanted_tokens = set()
    if os.path.exists(UNWANTED_CORPUS_PATH):
        with open(UNWANTED_CORPUS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    for m in data.get("messages", []):
                        unwanted_tokens.update(tokenizer.encode(m["content"], add_special_tokens=False))
                except Exception:
                    pass

    unwanted_tokens.update(tokenizer.encode(culinary_unwanted_text, add_special_tokens=False))

    protected_tokens = set(tokenizer.all_special_ids)
    for c in range(256):
        try:
            protected_tokens.update(tokenizer.encode(chr(c), add_special_tokens=False))
        except Exception:
            pass

    systems_protected = (
        "ls dir cd cat rm cp mv sudo systemctl journalctl ufw iptables ps aux grep awk sed "
        "Get-Process Start-Process Set-Service Stop-Service New-Item Remove-Item "
        "Get-Service Get-WmiObject Get-CimInstance netstat ipconfig ifconfig ping ssh curl "
        "launchctl defaults brew diskutil scp rsync bash sh zsh powershell cmd git python "
        "gcc g++ make cmake nvcc rustc cargo pip apt dnf pacman winget tar unzip chmod chown "
        "int float double void char bool true false return if else while for struct class "
        "def import async await try except lambda NULL None self this const static public "
        "GPIO I2C SPI UART PWM ADC DAC ESP32 Arduino Raspberry Pi Linux Windows macOS Intel AMD NVIDIA"
    )
    protected_tokens.update(tokenizer.encode(systems_protected, add_special_tokens=False))

    ablated_tokens = unwanted_tokens - protected_tokens
    print(f"Total tokens identificados para ablación: {len(ablated_tokens)}")

    embed_tensor = state_dict["model.embed_tokens.weight"].clone().to(torch.float32)
    for tid in ablated_tokens:
        if tid < embed_tensor.shape[0]:
            embed_tensor[tid] = 0.0

    state_dict["model.embed_tokens.weight"] = embed_tensor.to(torch.bfloat16 if device == "cuda" else torch.float32)
    print(f"[OK] {len(ablated_tokens)} embeddings anulados a cero absoluto.")

    # Guardar en export/sentinel_qwen_28l
    print(f"\n[3/4] Guardando modelo completo fusionado en: {OUTPUT_DIR}...")
    save_file(state_dict, os.path.join(OUTPUT_DIR, "model.safetensors"))
    tokenizer.save_pretrained(OUTPUT_DIR)
    merged_model.config.save_pretrained(OUTPUT_DIR)
    
    # Asegurar generation_config
    try:
        merged_model.generation_config.save_pretrained(OUTPUT_DIR)
    except Exception:
        pass

    del state_dict
    del peft_model
    del base_model
    del merged_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 3. Compilación GGUF
    print("\n[4/4] Compilando a binarios GGUF de producción...")
    cmd_convert = [
        sys.executable, CONVERTER,
        OUTPUT_DIR,
        "--outfile", F16_GGUF,
        "--outtype", "f16"
    ]
    res_conv = subprocess.run(cmd_convert, cwd=LLAMA_REPO)
    if res_conv.returncode != 0:
        print("[ERROR] Fallo en conversión GGUF F16.")
        sys.exit(1)

    print("\nCuantizando a Q4_K_M (Máxima agilidad y velocidad)...")
    res_q4 = subprocess.run([QUANTIZER, F16_GGUF, Q4_GGUF, "Q4_K_M"])
    if res_q4.returncode != 0:
        print("[ERROR] Fallo en cuantización Q4_K_M.")
        sys.exit(1)

    print("\nCuantizando a Q8_0 (Máxima fidelidad)...")
    res_q8 = subprocess.run([QUANTIZER, F16_GGUF, Q8_GGUF, "Q8_0"])

    if os.path.exists(F16_GGUF):
        os.remove(F16_GGUF)
        print("Archivo temporal F16 eliminado.")

    print("\n" + "=" * 80)
    print("PROCESO FINALIZADO EXITOSAMENTE:")
    if os.path.exists(Q4_GGUF):
        print(f"Q4_K_M : {Q4_GGUF} ({os.path.getsize(Q4_GGUF)/(1024*1024):.2f} MB)")
    if os.path.exists(Q8_GGUF):
        print(f"Q8_0   : {Q8_GGUF} ({os.path.getsize(Q8_GGUF)/(1024*1024):.2f} MB)")
    print("=" * 80)

if __name__ == "__main__":
    main()
