#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reentrenamiento de Alta Intensidad para Reprogramación Física Neuronal: SENTINEL PURE STEM (1B)
-----------------------------------------------------------------------------------------------
- Arquitectura Base: Llama 3.2 1B Instruct (1.23B parámetros)
- Objetivo: 100% STEM, electrónica, Linux, microcontroladores, lenguajes modernos y física exacta
- Optimización: Paged AdamW 8-bit, Rank 64, Alpha 128 en todas las proyecciones lineales
- Velocidad esperada en CPU: ~20 tokens/segundo (respuestas completas en 6-8s)
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
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "pure_stem_1b_structured.jsonl")
OUTPUT_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "pure_stem_adapters_1b")
METRICS_PATH = os.path.join(BASE_DIR, "benchmark", "training_pure_stem_1b_metrics.json")
MODEL_ID = "unsloth/Llama-3.2-1B-Instruct"

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

class PureStemJsonlDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=1024):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []

        print(f"Cargando dataset desde {jsonl_path}...", flush=True)
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                messages = obj.get("messages", [])
                if messages:
                    self.samples.append(messages)

        print(f"Total de muestras estructuradas: {len(self.samples)}", flush=True)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        messages = self.samples[idx]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )

        tokens = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt"
        )

        input_ids = tokens["input_ids"].squeeze(0)
        attention_mask = tokens["attention_mask"].squeeze(0)
        labels = input_ids.clone()

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels
        }


class VRAMMonitorCallback(TrainerCallback):
    def __init__(self, output_file):
        self.output_file = output_file
        self.history = []
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    def on_step_end(self, args, state, control, **kwargs):
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024 ** 2)
            reserved = torch.cuda.memory_reserved() / (1024 ** 2)
            max_vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 2)
            vram_utilization_pct = (reserved / max_vram) * 100
        else:
            allocated = reserved = max_vram = vram_utilization_pct = 0.0

        current_loss = None
        current_lr = None
        if state.log_history:
            for entry in reversed(state.log_history):
                if "loss" in entry:
                    current_loss = entry["loss"]
                    current_lr = entry.get("learning_rate", 0.0)
                    break

        entry = {
            "step": state.global_step,
            "max_steps": state.max_steps,
            "loss": current_loss,
            "learning_rate": current_lr,
            "epoch": state.epoch,
            "vram_allocated_mb": round(allocated, 2),
            "vram_reserved_mb": round(reserved, 2),
            "vram_utilization_pct": round(vram_utilization_pct, 1)
        }

        if entry["loss"] is not None:
            self.history.append(entry)
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
            print(f"[Paso {state.global_step}/{state.max_steps}] Loss: {entry['loss']:.4f} | VRAM: {allocated:.0f} MB / {reserved:.0f} MB ({entry['vram_utilization_pct']}%)", flush=True)


def run_training():
    print("=" * 80, flush=True)
    print("INICIANDO REPROGRAMACIÓN FÍSICA NEURONAL: SENTINEL PURE STEM (1B)", flush=True)
    print(f"Corpus de Entrenamiento: {DATASET_PATH}", flush=True)
    print(f"Destino de Adaptadores: {OUTPUT_ADAPTERS_DIR}", flush=True)
    print("Aceleración de Silicio: NVIDIA GeForce RTX 5060 Laptop GPU (BF16 / NF4)", flush=True)
    print("Objetivo: Modelo de Ultra-Velocidad (20 tok/s) en servidor HP", flush=True)
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

    print("[1/4] Cargando modelo base Llama 3.2 1B en 4-bit...", flush=True)
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
        task_type="CAUSAL_LM"
    )

    print("[2/4] Inyectando adaptadores LoRA de alta intensidad...", flush=True)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("[3/4] Preparando DataLoader nativo...", flush=True)
    dataset = PureStemJsonlDataset(DATASET_PATH, tokenizer, max_length=1024)
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        pad_to_multiple_of=8,
        return_tensors="pt",
        padding=True
    )

    training_args = TrainingArguments(
        output_dir=OUTPUT_ADAPTERS_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        max_steps=250,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_steps=5,
        optim="paged_adamw_8bit",
        bf16=True,
        logging_steps=1,
        save_strategy="no",
        report_to="none",
        dataloader_pin_memory=False,
        gradient_checkpointing=True,
        max_grad_norm=1.0,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
        callbacks=[VRAMMonitorCallback(METRICS_PATH)]
    )

    print("\n[4/4] Iniciando optimización de gradientes...", flush=True)
    train_result = trainer.train()

    print(f"\nGuardando adaptadores en: {OUTPUT_ADAPTERS_DIR}...", flush=True)
    trainer.model.save_pretrained(OUTPUT_ADAPTERS_DIR)
    tokenizer.save_pretrained(OUTPUT_ADAPTERS_DIR)

    summary = {
        "model_id": MODEL_ID,
        "train_runtime_sec": train_result.metrics.get("train_runtime", 0),
        "final_loss": train_result.metrics.get("train_loss", 0),
        "max_steps": 250,
        "rank": 64,
        "alpha": 128,
        "target_hardware": "HP Ubuntu (Intel i5-4310U) ~20 tok/s"
    }
    with open(os.path.join(OUTPUT_ADAPTERS_DIR, "training_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80, flush=True)
    print(f"[ÉXITO]: Reentrenamiento 1B completado. Pérdida final: {summary['final_loss']:.4f}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    run_training()
