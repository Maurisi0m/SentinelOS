#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL Master Agentic Fine-Tuning Pipeline
Entrena las capacidades agénticas (Tool Calling, control de hardware, resolución de librerías,
pedagogía de laboratorio y memoria Obsidian) directamente en las sinapsis de Llama 3.2 3B.
Optimizado para NVIDIA RTX 5060 con PyTorch Blackwell sm_120 (CUDA 12.8, BF16).
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
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "master_agentic_dataset.jsonl")
OUTPUT_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "agentic_adapters")
METRICS_PATH = os.path.join(BASE_DIR, "benchmark", "training_agentic_metrics.json")
MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"

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
    print("INICIANDO ENTRENAMIENTO AGÉNTICO Y PEDAGÓGICO DE SENTINEL")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Destino: {OUTPUT_ADAPTERS_DIR}")
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

    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    def format_prompts(batch):
        formatted_texts = []
        for messages in batch["messages"]:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            formatted_texts.append(text)
        return {"text": formatted_texts}

    dataset = dataset.map(format_prompts, batched=True)

    training_args = SFTConfig(
        output_dir=OUTPUT_ADAPTERS_DIR,
        dataset_text_field="text",
        max_length=1024,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        num_train_epochs=2,
        warmup_steps=2,
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

    print("\nIniciando optimización LoRA para imprimir comportamiento agéntico en el modelo...")
    train_result = trainer.train()

    print("\nGuardando adaptadores LoRA entrenados...")
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

    print(f"\n[ÉXITO] Adaptadores agénticos guardados en: {OUTPUT_ADAPTERS_DIR}")
    print(f"Pérdida final de entrenamiento (Loss): {train_result.training_loss:.4f}")

if __name__ == "__main__":
    run_training()
