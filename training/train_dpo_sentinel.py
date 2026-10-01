#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Alineamiento DPO (Direct Preference Optimization) en GPU RTX 5060
Entrena el modelo maestro SENTINEL para discriminar rigurosamente entre:
- Código C con memory leaks vs C seguro con free/NULL check.
- Uso destructivo de pines SPI Flash ESP32 vs pines de bus VSPI seguros.
- Explicaciones con razonamiento <thought> vs respuestas sin auto-reflexión.
"""

import os
import sys
import json
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainerCallback
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)
from trl import DPOTrainer, DPOConfig

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "dpo_stem_dataset.jsonl")
OUTPUT_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "dpo_adapters_3b")
METRICS_PATH = os.path.join(BASE_DIR, "benchmark", "training_dpo_metrics.json")

if torch.cuda.is_available():
    torch.cuda.empty_cache()

class DPOMetricsCallback(TrainerCallback):
    def __init__(self, output_file):
        self.output_file = output_file
        self.history = []
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            entry = {
                "step": state.global_step,
                "loss": logs.get("loss", None),
                "learning_rate": logs.get("learning_rate", None),
                "rewards_chosen": logs.get("rewards/chosen", None),
                "rewards_rejected": logs.get("rewards/rejected", None),
                "rewards_accuracies": logs.get("rewards/accuracies", None),
                "rewards_margins": logs.get("rewards/margins", None),
                "epoch": logs.get("epoch", None),
                "vram_allocated_mb": round(torch.cuda.memory_allocated(0) / (1024**2), 2) if torch.cuda.is_available() else 0,
            }
            if entry["loss"] is not None or entry["rewards_chosen"] is not None:
                self.history.append(entry)
                with open(self.output_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, indent=2)

def run_dpo_training():
    print("=" * 80)
    print("INICIANDO ALINEAMIENTO DPO EN GPU NVIDIA RTX 5060 (OPTIMIZACIÓN DE PREFERENCIAS)")
    print(f"Modelo Base: {MODEL_ID}")
    print(f"Dataset DPO: {DATASET_PATH}")
    print(f"Destino Adaptadores: {OUTPUT_ADAPTERS_DIR}")
    print(f"GPU Activa: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print("=" * 80)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    print("\n[1/3] Cargando modelo en 4-bit para DPO...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )

    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    print("\n[2/3] Cargando dataset de pares [prompt, chosen, rejected]...")
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    dpo_args = DPOConfig(
        output_dir=OUTPUT_ADAPTERS_DIR,
        learning_rate=5e-6,
        beta=0.1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_train_epochs=2,
        logging_steps=1,
        warmup_steps=2,
        lr_scheduler_type="cosine",
        fp16=False,
        bf16=True,
        save_strategy="no",
        dataloader_num_workers=0,
        report_to="none",
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        max_length=512,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # Con PEFT en QLoRA, DPO usa el modelo base adaptado implícito
        args=dpo_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=lora_config,
        callbacks=[DPOMetricsCallback(METRICS_PATH)],
    )

    print("\n[3/3] Ejecutando optimización por refuerzo de preferencias (DPO)...")
    train_result = trainer.train()

    print("\nGuardando adaptadores DPO...")
    trainer.model.save_pretrained(OUTPUT_ADAPTERS_DIR)
    tokenizer.save_pretrained(OUTPUT_ADAPTERS_DIR)

    print("\n" + "=" * 80)
    print("ALINEAMIENTO DPO COMPLETADO CON ÉXITO")
    print(f"Loss Final: {train_result.training_loss:.4f}")
    print(f"Adaptadores guardados en: {OUTPUT_ADAPTERS_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    run_dpo_training()
