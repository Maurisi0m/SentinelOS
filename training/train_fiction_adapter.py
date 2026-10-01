#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrenamiento del Adaptador Negativo delta_W_fiction
Captura las direcciones de gradiente de ficción, fantasía, mitos y novelas
para su sustracción matricial en SENTINEL.
"""

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)
from trl import SFTTrainer, SFTConfig

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "fiction_fantasy_corpus.jsonl")
OUTPUT_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "fiction_adapters")
MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"

if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.82, 0)
    torch.cuda.empty_cache()

def main():
    print("=== ENTRENANDO ADAPTADOR NEGATIVO: FICCIÓN Y FANTASÍA ===")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Destino: {OUTPUT_ADAPTERS_DIR}")

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
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)

    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    def format_prompts(batch):
        formatted = []
        for messages in batch["messages"]:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            formatted.append(text)
        return {"text": formatted}

    dataset = dataset.map(format_prompts, batched=True)

    training_args = SFTConfig(
        output_dir=OUTPUT_ADAPTERS_DIR,
        dataset_text_field="text",
        max_length=512,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        learning_rate=3e-4,
        logging_steps=1,
        num_train_epochs=2,
        warmup_steps=1,
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
    )

    print("Extrayendo tensor diferencial delta_W_fiction...")
    train_result = trainer.train()

    print("Guardando adaptador...")
    trainer.model.save_pretrained(OUTPUT_ADAPTERS_DIR)
    tokenizer.save_pretrained(OUTPUT_ADAPTERS_DIR)
    print(f"[OK] delta_W_fiction generado con éxito (Loss: {train_result.training_loss:.4f})")

if __name__ == "__main__":
    main()
