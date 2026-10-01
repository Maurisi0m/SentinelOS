#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alineamiento DPO (Direct Preference Optimization) con TRL en BF16 Nativo
------------------------------------------------------------------------
- Modelo Base: export/sentinel_stem_ties_merged/
- Dataset: dataset/dpo_stem_dataset.jsonl (Pares Chosen vs Rejected)
- Hardware: RTX 5060 Laptop (8 GB VRAM)
- Salida: export/sentinel_dpo_aligned_1b/
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
import json
import torch

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig
from trl import DPOTrainer, DPOConfig

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_stem_ties_merged")
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "dpo_stem_dataset.jsonl")
OUTPUT_DPO_DIR = os.path.join(BASE_DIR, "export", "sentinel_dpo_aligned_1b")

SYSTEM_PREFIX = (
    "SENTINEL, mentor pedagógico y sistema operativo cognitivo del Laboratorio STEM.\n"
    "Responde con rigor técnico, analogías didácticas, fórmulas LaTeX y tablas Markdown. Cero emojis."
)

def load_dpo_dataset():
    prompts = []
    chosens = []
    rejecteds = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                obj = json.loads(line)
                p = obj.get("prompt", "")
                c = obj.get("chosen", "")
                r = obj.get("rejected", "")
                if p and c and r:
                    full_prompt = f"<|im_start|>system\n{SYSTEM_PREFIX}<|im_end|>\n<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n"
                    prompts.append(full_prompt)
                    chosens.append(c + "<|im_end|>")
                    rejecteds.append(r + "<|im_end|>")
            except Exception:
                continue

    return Dataset.from_dict({
        "prompt": prompts,
        "chosen": chosens,
        "rejected": rejecteds
    })

def main():
    print("=" * 80)
    print("INICIANDO ALINEAMIENTO DPO CON TRL (DIRECT PREFERENCE OPTIMIZATION)")
    print(f"Modelo de Entrada: {MODEL_DIR}")
    print(f"Dataset de Preferencias: {DATASET_PATH}")
    print(f"Destino DPO: {OUTPUT_DPO_DIR}")
    print("=" * 80)

    # 1. Cargar Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. Cargar Dataset
    dpo_dataset = load_dpo_dataset()
    print(f"Pares DPO cargados: {len(dpo_dataset)}")

    # 3. Cargar Modelo Monolítico en BF16 (Una sola copia en VRAM)
    print("\nCargando Modelo Base en BF16 nativo...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR,
        dtype=torch.bfloat16,
        device_map="cuda",
        local_files_only=True
    )

    # 4. Configurar PEFT LoRA para DPO (Permite referencia implícita sin duplicar VRAM)
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM"
    )

    # 5. Configurar DPO
    dpo_config = DPOConfig(
        output_dir=OUTPUT_DPO_DIR,
        beta=0.1,
        learning_rate=5e-5,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=2,
        max_steps=50,
        max_length=512,
        bf16=True,
        logging_steps=1,
        save_strategy="no",
        optim="adamw_torch",
        gradient_checkpointing=True,
        report_to="none"
    )

    dpo_trainer = DPOTrainer(
        model=model,
        ref_model=None,
        peft_config=peft_config,
        args=dpo_config,
        train_dataset=dpo_dataset,
        processing_class=tokenizer
    )

    print("\nEjecutando Optimización de Preferencias Directas (DPO)...")
    dpo_trainer.train()

    print(f"\nFusionando adaptadores DPO en los tensores base monolíticos (merge_and_unload)...")
    os.makedirs(OUTPUT_DPO_DIR, exist_ok=True)
    merged_model = dpo_trainer.model.merge_and_unload()
    merged_model.save_pretrained(OUTPUT_DPO_DIR, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_DPO_DIR)
    print(f"\n[ÉXITO] DPO completado y fusionado en {OUTPUT_DPO_DIR}. Cero sobrecosto de parámetros.")

if __name__ == "__main__":
    main()
