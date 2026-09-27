#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrenamiento DoRA (Weight-Decomposed Low-Rank Adaptation) en BF16 Nativo
------------------------------------------------------------------------
- Arquitectura Base: Llama 3.2 1B Instruct (1.23B parámetros)
- Hardware: NVIDIA GeForce RTX 5060 Laptop (Blackwell SM 12.0, 8 GB VRAM)
- Dataset: sentinel_pure_stem_cot_tripartite.jsonl (2072 muestras prístinas)
- Precisión: bfloat16 nativo
- Salida: training/dora_adapters_1b/
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
import time
import torch

# Forzar salida sin búfer
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    TrainerCallback
)
from peft import LoraConfig, get_peft_model

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "sentinel_pure_stem_cot_tripartite.jsonl")
OUTPUT_DIR = os.path.join(BASE_DIR, "training", "dora_adapters_1b")
MODEL_ID = "unsloth/Llama-3.2-1B-Instruct"

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

class SentinelCotPretokenizedDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=1024):
        self.features = []
        print(f"Cargando y pre-tokenizando dataset desde {jsonl_path}...", flush=True)
        t0 = time.time()
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    messages = obj.get("messages", [])
                    if not messages:
                        continue
                    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                    tokens = tokenizer(text, max_length=max_length, truncation=True)
                    ids = tokens["input_ids"]
                    mask = tokens["attention_mask"]
                    self.features.append({
                        "input_ids": ids,
                        "attention_mask": mask,
                        "labels": list(ids)
                    })
                except Exception:
                    continue
        t1 = time.time()
        print(f"Pre-tokenizadas {len(self.features)} muestras en {t1 - t0:.2f}s.", flush=True)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx]

class SentinelProgressCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            loss = logs.get("loss", "N/A")
            lr = logs.get("learning_rate", 0.0)
            vram = torch.cuda.max_memory_allocated() / (1024**2)
            print(f"[Step {state.global_step}/{state.max_steps}] Loss: {loss} | LR: {lr:.2e} | VRAM: {vram:.1f} MB", flush=True)

def main():
    print("=" * 80, flush=True)
    print("INICIANDO ENTRENAMIENTO DoRA EN BF16 NATIVO (BLACKWELL RTX 5060)", flush=True)
    print(f"Modelo Base: {MODEL_ID}", flush=True)
    print(f"Dataset: {DATASET_PATH}", flush=True)
    print(f"Destino Adaptadores: {OUTPUT_DIR}", flush=True)
    print("=" * 80, flush=True)

    t_start = time.time()

    # 1. Cargar Tokenizer local
    print("\n[1/4] Inicializando Tokenizer...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. Cargar Dataset Pre-tokenizado
    train_dataset = SentinelCotPretokenizedDataset(DATASET_PATH, tokenizer, max_length=1024)

    # 3. Cargar Modelo Base en BF16 Nativo local
    print("\n[2/4] Cargando Modelo Base en torch.bfloat16...", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        dtype=torch.bfloat16,
        device_map="cuda",
        local_files_only=True,
        use_cache=False
    )
    model.enable_input_require_grads()

    # 4. Configurar DoRA
    print("\n[3/4] Configurando DoRA (Descomposición de Magnitud y Dirección)...", flush=True)
    dora_config = LoraConfig(
        r=32,
        lora_alpha=64,
        lora_dropout=0.05,
        use_dora=True,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj"
        ],
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, dora_config)
    model.print_trainable_parameters()

    # 5. Argumentos de Entrenamiento
    print("\n[4/4] Configurando Trainer con Paged AdamW 8-bit y BF16...", flush=True)
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        learning_rate=2.5e-4,
        lr_scheduler_type="cosine",
        warmup_steps=5,
        max_steps=60,
        bf16=True,
        logging_steps=5,
        save_strategy="no",
        optim="paged_adamw_8bit",
        dataloader_num_workers=0,
        gradient_checkpointing=True,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, pad_to_multiple_of=8),
        callbacks=[SentinelProgressCallback()]
    )

    print("\nEjecutando Fine-Tuning DoRA...", flush=True)
    trainer.train()

    print(f"\nGuardando adaptadores DoRA calibrados en {OUTPUT_DIR}...", flush=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    elapsed = time.time() - t_start
    print(f"\n[ÉXITO] Entrenamiento DoRA completado en {elapsed:.2f} segundos.", flush=True)
    print(f"VRAM Pico Utilizada: {torch.cuda.max_memory_allocated() / (1024**2):.2f} MB", flush=True)

if __name__ == "__main__":
    main()
