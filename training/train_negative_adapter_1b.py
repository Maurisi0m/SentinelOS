#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrenamiento del Adaptador Negativo para Llama-3.2-1B-Instruct
Captura la dirección de gradiente del espacio latente NO-STEM (farándula, romance,
astrología, deportes de entretenimiento, cocina casual, New Age, etc.)
para su posterior sustracción matricial o desalineación de representaciones.
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
    DataCollatorForSeq2Seq
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "unlearning_comprehensive_corpus.jsonl")
OUTPUT_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "negative_adapters_1b")
MODEL_ID = r"C:\Users\mauro\.cache\huggingface\hub\models--unsloth--Llama-3.2-1B-Instruct\snapshots\5a8abab4a5d6f164389b1079fb721cfab8d7126c"

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

class UnlearningDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []

        print(f"Cargando corpus de desaprendizaje desde {jsonl_path}...", flush=True)
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                instruction = item.get("instruction", "")
                unwanted_target = item.get("unwanted_target", "")
                if instruction and unwanted_target:
                    messages = [
                        {"role": "user", "content": instruction},
                        {"role": "assistant", "content": unwanted_target}
                    ]
                    self.samples.append(messages)

        print(f"Total de muestras de desaprendizaje cargadas: {len(self.samples)}", flush=True)

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

def main():
    print("=" * 80)
    print("=== ENTRENAMIENTO DE ADAPTADOR NEGATIVO (DESAPRENDIZAJE NO-STEM) ===")
    print(f"Modelo Base: {MODEL_ID}")
    print(f"Corpus Negativo: {DATASET_PATH}")
    print(f"Directorio de Destino: {OUTPUT_ADAPTERS_DIR}")
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

    print("Cargando modelo base Llama 3.2 1B en 4-bit para capturar dirección de gradiente no deseado...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
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
    model.print_trainable_parameters()

    dataset = UnlearningDataset(DATASET_PATH, tokenizer, max_length=512)
    collator = DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True)

    training_args = TrainingArguments(
        output_dir=OUTPUT_ADAPTERS_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        learning_rate=3e-4,
        logging_steps=5,
        num_train_epochs=2,
        warmup_steps=2,
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
        train_dataset=dataset,
        data_collator=collator,
    )

    print("\nIniciando entrenamiento del adaptador negativo...")
    trainer.train()

    print(f"\nGuardando pesos del adaptador negativo en {OUTPUT_ADAPTERS_DIR}...")
    os.makedirs(OUTPUT_ADAPTERS_DIR, exist_ok=True)
    model.save_pretrained(OUTPUT_ADAPTERS_DIR)
    tokenizer.save_pretrained(OUTPUT_ADAPTERS_DIR)
    print("=" * 80)
    print("[ÉXITO] Adaptador negativo entrenado y guardado correctamente.")
    print("=" * 80)

if __name__ == "__main__":
    main()
