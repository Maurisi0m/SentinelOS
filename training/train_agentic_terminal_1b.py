#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reentrenamiento Agéntico de Alta Intensidad: SENTINEL-1B-PureSTEM & Terminal Operator
-------------------------------------------------------------------------------------
- Base: Llama 3.2 1B Instruct (desaprendido o snapshot oficial local)
- Datasets Consolidados:
  1. dataset/cross_platform_terminal_dataset.jsonl (ReAct de terminal multiplataforma)
  2. dataset/terminal_corpus/sample_validation.jsonl (muestras maestras de terminal)
  3. dataset/terminal_corpus/terminal_dataset_*.jsonl (11 shards completos de 1.00 GB - 559,156 muestras)
  4. dataset/unlearning_comprehensive_corpus.jsonl (pivotes deterministas de rechazo a no-STEM)
- Optimización: QLoRA 4-bit NF4, Rank 64, Alpha 128, Paged AdamW 8-bit en RTX 5060 Laptop (8GB VRAM)
- Protocolo: Ciclo ReAct plano [THOUGHT] ... [/THOUGHT] [EXECUTE] ... [/EXECUTE] [OUTPUT] ... [/OUTPUT]
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
import glob
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
UNLEARNED_MODEL_DIR = os.path.join(BASE_DIR, "export", "sentinel_1b_unlearned")
BASE_SNAPSHOT_DIR = r"C:\Users\mauro\.cache\huggingface\hub\models--unsloth--Llama-3.2-1B-Instruct\snapshots\5a8abab4a5d6f164389b1079fb721cfab8d7126c"

MODEL_SOURCE = UNLEARNED_MODEL_DIR if os.path.exists(os.path.join(UNLEARNED_MODEL_DIR, "model.safetensors")) else BASE_SNAPSHOT_DIR
OUTPUT_ADAPTERS_DIR = os.path.join(BASE_DIR, "training", "agentic_terminal_adapters_1b")

SYSTEM_PROMPT = (
    "Eres SENTINEL, operador autónomo de sistemas y terminal. "
    "Para interactuar con el sistema operativo debes razonar dentro de [THOUGHT]...[/THOUGHT], "
    "emitir el comando exacto encerrado estrictamente en [EXECUTE]...[/EXECUTE] "
    "y analizar la respuesta que recibas en [OUTPUT]...[/OUTPUT]. "
    "Responde siempre con rigor técnico y enlaces de Obsidian [[Concepto]]. Prohibido el uso de emojis."
)

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

class ConsolidatedSentinelDataset(Dataset):
    def __init__(self, tokenizer, max_length=1024):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.seed_samples = []

        # 1. Cargar trayectorias seed multiplataforma
        cross_platform_path = os.path.join(BASE_DIR, "dataset", "cross_platform_terminal_dataset.jsonl")
        if os.path.exists(cross_platform_path):
            print(f"Cargando trayectorias seed desde {cross_platform_path}...", flush=True)
            with open(cross_platform_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    item = json.loads(line)
                    traj = item.get("trajectory", [])
                    if traj:
                        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + traj
                        self.seed_samples.append(messages)

        # 2. Cargar muestra dorada validada
        validation_sample_path = os.path.join(BASE_DIR, "dataset", "terminal_corpus", "sample_validation.jsonl")
        if os.path.exists(validation_sample_path):
            print(f"Cargando muestras doradas desde {validation_sample_path}...", flush=True)
            with open(validation_sample_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    item = json.loads(line)
                    user_req = item.get("user_request", "")
                    cmds = " && ".join(item.get("commands", [])) if isinstance(item.get("commands"), list) else str(item.get("commands", ""))
                    out = item.get("expected_output", "")
                    exp = item.get("explanation", "")
                    analysis = " ".join(item.get("analysis", [])) if isinstance(item.get("analysis"), list) else str(item.get("analysis", ""))
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_req},
                        {"role": "assistant", "content": f"[THOUGHT] {analysis} [/THOUGHT]\n[EXECUTE] {cmds} [/EXECUTE]"},
                        {"role": "environment", "content": f"[OUTPUT]\n{out}\n[/OUTPUT]"},
                        {"role": "assistant", "content": exp}
                    ]
                    self.seed_samples.append(messages)

        # 3. Cargar pivotes deterministas de desaprendizaje (Rechazo a no-STEM)
        unlearning_path = os.path.join(BASE_DIR, "dataset", "unlearning_comprehensive_corpus.jsonl")
        if os.path.exists(unlearning_path):
            print(f"Cargando pivotes de contención desde {unlearning_path}...", flush=True)
            with open(unlearning_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    item = json.loads(line)
                    inst = item.get("instruction", "")
                    pivot = item.get("refusal_or_pivot", "")
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": inst},
                        {"role": "assistant", "content": pivot}
                    ]
                    self.seed_samples.append(messages)

        # 4. Indexar Shards de 1 GB (terminal_dataset_*.jsonl)
        self.shard_files = sorted(glob.glob(os.path.join(BASE_DIR, "dataset", "terminal_corpus", "terminal_dataset_*.jsonl")))
        print(f"Indexando {len(self.shard_files)} shards del corpus de 1.00 GB...", flush=True)
        self.shard_offsets = []
        for s_idx, sf in enumerate(self.shard_files):
            with open(sf, "rb") as f:
                offset = f.tell()
                line = f.readline()
                while line:
                    if line.strip() and not line.startswith(b'{"dataset"'):
                        self.shard_offsets.append((s_idx, offset))
                    offset = f.tell()
                    line = f.readline()

        self.file_handles = [open(sf, "r", encoding="utf-8") for sf in self.shard_files]
        self.total_samples = len(self.seed_samples) + len(self.shard_offsets)
        print(f"¡Dataset consolidado listo! Total de muestras: {self.total_samples} (1.00 GB de corpus terminal + seed)", flush=True)

    def __len__(self):
        return self.total_samples

    def __getitem__(self, idx):
        if idx < len(self.seed_samples):
            messages = self.seed_samples[idx]
        else:
            s_idx, off = self.shard_offsets[idx - len(self.seed_samples)]
            fh = self.file_handles[s_idx]
            fh.seek(off)
            line = fh.readline()
            item = json.loads(line)
            user_req = item.get("user_request", "")
            cmds = " && ".join(item.get("commands", [])) if isinstance(item.get("commands"), list) else str(item.get("commands", ""))
            out = item.get("expected_output", "")
            exp = item.get("explanation", "")
            analysis = " ".join(item.get("analysis", [])) if isinstance(item.get("analysis"), list) else str(item.get("analysis", ""))
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_req},
                {"role": "assistant", "content": f"[THOUGHT] {analysis} [/THOUGHT]\n[EXECUTE] {cmds} [/EXECUTE]"},
                {"role": "environment", "content": f"[OUTPUT]\n{out}\n[/OUTPUT]"},
                {"role": "assistant", "content": exp}
            ]

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
    print("INICIANDO ENTRENAMIENTO AGÉNTICO RE-ACT TERMINAL & STEM (SENTINEL 1B)")
    print(f"Modelo Origen: {MODEL_SOURCE}")
    print(f"Destino de Adaptadores: {OUTPUT_ADAPTERS_DIR}")
    print("=" * 80)

    tokenizer = AutoTokenizer.from_pretrained(BASE_SNAPSHOT_DIR)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    print("Cargando modelo en 4 bits con cuantización NF4 y optimización VRAM...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_SOURCE,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )

    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_config = LoraConfig(
        r=64,
        lora_alpha=128,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    dataset = ConsolidatedSentinelDataset(tokenizer, max_length=1024)
    collator = DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True)

    training_args = TrainingArguments(
        output_dir=OUTPUT_ADAPTERS_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=10,
        logging_first_step=True,
        num_train_epochs=1,
        warmup_steps=30,
        fp16=False,
        bf16=True,
        save_strategy="steps",
        save_steps=250,
        save_total_limit=3,
        dataloader_num_workers=0,
        report_to="none",
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=collator,
    )

    print("\n[GPU READY] Lanzando ciclo de entrenamiento en NVIDIA GeForce RTX 5060 Laptop...")
    print(f"Total de iteraciones por epoch: {len(dataset) // (2 * 4)} pasos")
    trainer.train()

    print(f"\nGuardando adaptadores agénticos de terminal en {OUTPUT_ADAPTERS_DIR}...")
    os.makedirs(OUTPUT_ADAPTERS_DIR, exist_ok=True)
    model.save_pretrained(OUTPUT_ADAPTERS_DIR)
    tokenizer.save_pretrained(OUTPUT_ADAPTERS_DIR)

    print("=" * 80)
    print(f"[ÉXITO TOTAL] Adaptadores de terminal agéntico guardados en: {OUTPUT_ADAPTERS_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
