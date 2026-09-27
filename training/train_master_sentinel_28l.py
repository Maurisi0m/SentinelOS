#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Fine-Tuning Maestro para SENTINEL (28 Capas Pristinas)
Entrena sobre el modelo base oficial unsloth/Llama-3.2-3B-Instruct (arquitectura completa y sin daño estructural):
1. Inyección de Pensamiento Dual (<thought> bajo demanda con [MODO_PENSAMIENTO: ACTIVO]).
2. Guardarraíles de silicio para ESP32 (GPIO 6-11 bloqueados) y Raspberry Pi 5 (RP1 chip).
3. Memoria segura en C Bare-Metal (Heap vs .rodata, Valgrind, punteros).
4. Herramientas agénticas (write_file, edit_file, bash_execute, package_manager, obsidian_memory).
"""

import os
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
from trl import SFTTrainer, SFTConfig

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "healing_thought_c_dataset.jsonl")
OUTPUT_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "master_adapters_28l")
METRICS_PATH = os.path.join(BASE_DIR, "benchmark", "training_master_metrics.json")

if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.82, 0)
    torch.cuda.empty_cache()

class MetricsLoggerCallback(TrainerCallback):
    def __init__(self, output_file):
        self.output_file = output_file
        self.history = []
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            entry = {
                "step": state.global_step,
                "max_steps": state.max_steps,
                "loss": logs.get("loss", None),
                "learning_rate": logs.get("learning_rate", None),
                "epoch": logs.get("epoch", None),
                "vram_allocated_mb": round(torch.cuda.memory_allocated(0) / (1024**2), 2) if torch.cuda.is_available() else 0,
            }
            if entry["loss"] is not None:
                self.history.append(entry)
                with open(self.output_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, indent=2)

def run_training():
    print("=" * 80)
    print("INICIANDO ENTRENAMIENTO MAESTRO SENTINEL (28 CAPAS - MÁXIMA COHERENCIA)")
    print(f"Modelo Base: {MODEL_ID}")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Destino Adaptadores: {OUTPUT_ADAPTERS_DIR}")
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

    print("\n[1/4] Cargando arquitectura completa de 28 capas en 4-bit NF4...")
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
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("\n[2/4] Formateando dataset conversacional con chat template oficial...")
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    def format_prompts(batch):
        formatted_texts = []
        for messages in batch["messages"]:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            formatted_texts.append(text)
        return {"text": formatted_texts}

    dataset = dataset.map(format_prompts, batched=True)

    # 3 épocas para asimilación completa de sintaxis y razonamiento profundo
    training_args = SFTConfig(
        output_dir=OUTPUT_ADAPTERS_DIR,
        dataset_text_field="text",
        max_length=1024,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        num_train_epochs=3,
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

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        args=training_args,
        callbacks=[MetricsLoggerCallback(METRICS_PATH)],
    )

    print("\n[3/4] Optimizando pesos neuronales en RTX 5060...")
    train_result = trainer.train()

    print("\n[4/4] Guardando adaptadores maestros LoRA...")
    trainer.model.save_pretrained(OUTPUT_ADAPTERS_DIR)
    tokenizer.save_pretrained(OUTPUT_ADAPTERS_DIR)

    final_info = {
        "status": "completed",
        "train_loss": train_result.training_loss,
        "global_step": train_result.global_step,
        "adapters_dir": OUTPUT_ADAPTERS_DIR
    }
    with open(os.path.join(OUTPUT_ADAPTERS_DIR, "training_summary.json"), "w", encoding="utf-8") as f:
        json.dump(final_info, f, indent=2)

    print(f"\n[ÉXITO] Adaptadores maestros guardados en: {OUTPUT_ADAPTERS_DIR}")
    print(f"Pérdida final de entrenamiento (Loss): {train_result.training_loss:.4f}")

if __name__ == "__main__":
    run_training()
