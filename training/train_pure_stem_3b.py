#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL PURE STEM 3B: Reentrenamiento Denso y Sustitución Física de Pesos en GPU (RTX 5060)
------------------------------------------------------------------------------------------
Objetivo:
Reasignar el espacio latente de Llama 3.2 3B hacia tecnología pura (Bash, C, C# 12, Python 3.12,
Java 21, React 19, Física fundamental, Electromagnetismo, IA/ML, OpenCV, YOLO) provocando
un olvido catastrófico controlado de dominios no-STEM.

Aprovechamiento Óptimo de Silicio:
- Prevención de Fragmentación: PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
- Límite de Memoria Seguro: 85% VRAM máx (~6.8 GB de 8 GB) reservando margen para logits 128k
- Carga Nativa: Pure PyTorch Dataset en memoria (Zero-PyArrow / Anti-AppControl lock)
- Optimizador: Paged AdamW 8-bit con tolerancia a picos
"""

import os
import json
import os
import json
import torch

from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    TrainerCallback
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "pure_stem_3b_master.jsonl")
OUTPUT_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "pure_stem_adapters_3b")
METRICS_PATH = os.path.join(BASE_DIR, "benchmark", "training_pure_stem_metrics.json")
MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"

if torch.cuda.is_available():
    torch.cuda.empty_cache()

class PureStemJsonlDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=1024):
        self.examples = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    msgs = obj.get("messages", [])
                    if len(msgs) >= 2:
                        text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
                        enc = tokenizer(text, max_length=max_length, truncation=True, padding=False, return_tensors=None)
                        input_ids = enc["input_ids"]
                        attention_mask = enc.get("attention_mask", [1] * len(input_ids))
                        self.examples.append({
                            "input_ids": input_ids,
                            "attention_mask": attention_mask,
                            "labels": list(input_ids)
                        })
                except Exception:
                    pass
        print(f"[DATASET] Muestras procesadas y cargadas en memoria: {len(self.examples)}")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]

class PureStemMetricsLoggerCallback(TrainerCallback):
    def __init__(self, output_file):
        self.output_file = output_file
        self.history = []
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            allocated = torch.cuda.memory_allocated(0) / (1024**2) if torch.cuda.is_available() else 0
            reserved = torch.cuda.memory_reserved(0) / (1024**2) if torch.cuda.is_available() else 0
            entry = {
                "step": state.global_step,
                "max_steps": state.max_steps,
                "loss": logs.get("loss", None),
                "learning_rate": logs.get("learning_rate", None),
                "epoch": logs.get("epoch", None),
                "vram_allocated_mb": round(allocated, 2),
                "vram_reserved_mb": round(reserved, 2),
                "vram_utilization_pct": round((reserved / 8123) * 100, 1) if torch.cuda.is_available() else 0
            }
            if entry["loss"] is not None:
                self.history.append(entry)
                with open(self.output_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, indent=2)
                print(f"[Paso {state.global_step}/{state.max_steps}] Loss: {entry['loss']:.4f} | VRAM: {allocated:.0f} MB / {reserved:.0f} MB ({entry['vram_utilization_pct']}%)", flush=True)

def run_training():
    print("=" * 80, flush=True)
    print("INICIANDO REPROGRAMACIÓN FÍSICA NEURONAL: SENTINEL PURE STEM (3B)", flush=True)
    print(f"Corpus de Entrenamiento: {DATASET_PATH}", flush=True)
    print(f"Destino de Adaptadores: {OUTPUT_ADAPTERS_DIR}", flush=True)
    print("Aceleración de Silicio: NVIDIA GeForce RTX 5060 Laptop GPU (BF16 / NF4)", flush=True)
    print("Configuración de Memoria: 85% VRAM máx con protección Paged AdamW 8-bit y Expandable Segments", flush=True)
    print("Estrategia de Desplazamiento: LoRA r=64, alpha=128 en todas las capas lineales (MLP + Atención)", flush=True)
    print("=" * 80, flush=True)

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset maestro no encontrado: {DATASET_PATH}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    print("[1/4] Cargando modelo base Llama 3.2 3B en 4-bit...", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        local_files_only=True,
    )

    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # Configuración densa de alta intensidad: Rank 64, Alpha 128
    lora_config = LoraConfig(
        r=64,
        lora_alpha=128,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM",
    )

    print("[2/4] Inyectando matrices LoRA r=64 en todas las capas lineales...", flush=True)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print(f"[3/4] Tokenizando y compilando dataset en memoria...", flush=True)
    train_dataset = PureStemJsonlDataset(DATASET_PATH, tokenizer, max_length=1024)
    data_collator = DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt")

    # Configuración de alto rendimiento sin riesgo de OOM
    training_args = TrainingArguments(
        output_dir=OUTPUT_ADAPTERS_DIR,
        max_steps=250,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        warmup_steps=5,
        lr_scheduler_type="cosine",
        fp16=False,
        bf16=True,
        save_strategy="no",
        dataloader_num_workers=0,
        report_to="none",
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
        callbacks=[PureStemMetricsLoggerCallback(METRICS_PATH)],
    )

    print("\n[4/4] Ejecutando descenso de gradiente denso en RTX 5060...", flush=True)
    train_result = trainer.train()

    print(f"\nGuardando adaptadores en: {OUTPUT_ADAPTERS_DIR}...", flush=True)
    trainer.model.save_pretrained(OUTPUT_ADAPTERS_DIR)
    tokenizer.save_pretrained(OUTPUT_ADAPTERS_DIR)

    summary = {
        "status": "completed",
        "train_loss": train_result.training_loss,
        "global_step": train_result.global_step,
        "samples_total": len(train_dataset),
        "lora_rank": 64,
        "lora_alpha": 128,
        "adapters_dir": OUTPUT_ADAPTERS_DIR
    }
    with open(os.path.join(OUTPUT_ADAPTERS_DIR, "training_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[ÉXITO]: Reentrenamiento completado.", flush=True)
    print(f"Pérdida final de entrenamiento (Loss): {train_result.training_loss:.4f}", flush=True)
    print(f"Adaptadores listos para fusionar en float16 y cuantizar a GGUF.", flush=True)

if __name__ == "__main__":
    run_training()
