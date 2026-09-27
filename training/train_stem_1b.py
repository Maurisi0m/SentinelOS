#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL-1B STEM Fine-Tuning Pipeline
QLoRA sobre Llama-3.2-1B-Instruct con corpus STEM exclusivo
Hardware target: NVIDIA RTX 5060 Laptop (7.9 GB VRAM)

Estrategia:
  - 4-bit NF4 (bitsandbytes) para carga base
  - LoRA r=16 sobre todas las proyecciones de atencion + FFN
  - Dataset: stem_mega_train.jsonl (10k+ muestras)
  - 3 epocas, cosine scheduler, paged_adamw_8bit
  - Exporta adaptadores para merge posterior a GGUF
"""
import os, sys, json, time, torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainerCallback,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_ID    = "Qwen/Qwen2.5-1.5B-Instruct"   # 100% abierto, sin token HF, sin licencia
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "stem_mega_train.jsonl")
OUTPUT_DIR  = os.path.join(BASE_DIR, "training", "stem_qwen_adapters")
METRICS_OUT = os.path.join(BASE_DIR, "benchmark", "stem_qwen_training_metrics.json")

# ── GPU setup ─────────────────────────────────────────────────────────────────
if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.80, 0)  # Cap ~6.3 GB, margen seguro
    torch.cuda.empty_cache()
    print(f"[GPU] {torch.cuda.get_device_name(0)} | VRAM: {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f} GB")
else:
    print("[WARN] CUDA no disponible - se usara CPU (muy lento)")

# ── Callback de metricas ───────────────────────────────────────────────────────
class MetricsCallback(TrainerCallback):
    def __init__(self, path):
        self.path = path
        self.history = []
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.t0 = time.time()

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return
        loss = logs.get("loss")
        if loss is None:
            return
        elapsed = time.time() - self.t0
        entry = {
            "step": state.global_step,
            "max_steps": state.max_steps,
            "progress_pct": round(state.global_step / state.max_steps * 100, 1),
            "loss": round(loss, 5),
            "lr": logs.get("learning_rate"),
            "epoch": round(logs.get("epoch", 0), 3),
            "elapsed_min": round(elapsed / 60, 2),
            "vram_mb": round(torch.cuda.memory_allocated(0) / 1024**2, 1) if torch.cuda.is_available() else 0,
        }
        self.history.append(entry)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)
        eta_min = round((elapsed / state.global_step) * (state.max_steps - state.global_step) / 60, 1) if state.global_step > 0 else "?"
        print(f"  Step {state.global_step}/{state.max_steps} [{entry['progress_pct']}%] "
              f"loss={loss:.4f} | VRAM={entry['vram_mb']}MB | ETA={eta_min}min")

# ── Main ───────────────────────────────────────────────────────────────────────
def run():
    print("=" * 80)
    print("SENTINEL-1B STEM Fine-Tuning")
    print(f"Modelo base : {MODEL_ID}")
    print(f"Dataset     : {DATASET_PATH}")
    print(f"Salida      : {OUTPUT_DIR}")
    print("=" * 80)

    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Dataset no encontrado: {DATASET_PATH}")
        print("        Ejecuta primero: python dataset/build_stem_mega_dataset.py")
        sys.exit(1)

    # Contar muestras
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        n_samples = sum(1 for l in f if l.strip())
    print(f"\n[INFO] Dataset: {n_samples} muestras")

    # ── Tokenizer ──────────────────────────────────────────────────────────────
    print("\n[1/5] Cargando tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # ── Modelo 4-bit NF4 ──────────────────────────────────────────────────────
    print("[2/5] Cargando modelo 1B en 4-bit NF4 en GPU...")
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # ── LoRA quirurgico ────────────────────────────────────────────────────────
    print("[3/5] Aplicando LoRA r=16 en capas de atencion + FFN...")
    lora_cfg = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    # ── Dataset ────────────────────────────────────────────────────────────────
    print("\n[4/5] Cargando y formateando dataset STEM...")
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    def fmt(batch):
        texts = []
        for msgs in batch["messages"]:
            try:
                t = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
                texts.append(t)
            except Exception:
                texts.append("")
        return {"text": texts}

    dataset = dataset.map(fmt, batched=True, remove_columns=dataset.column_names)
    # Filtra por longitud real en tokens para evitar OOM/kills del OS
    def filter_by_length(ex):
        if not ex["text"] or len(ex["text"]) < 50:
            return False
        toks = tokenizer(ex["text"], truncation=False)["input_ids"]
        return 50 <= len(toks) <= 900  # Margen amplio bajo max_length=1024
    dataset = dataset.filter(filter_by_length)
    print(f"  Muestras validas tras filtro de tokens: {len(dataset)}")

    # ── SFTTrainer ────────────────────────────────────────────────────────────
    print("\n[5/5] Iniciando entrenamiento QLoRA...")
    sft_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        dataset_text_field="text",
        max_length=1024,                   # STEM completo sin OOM, ~3-4s/it
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,     # Effective batch = 16
        learning_rate=2e-4,
        num_train_epochs=3,
        warmup_steps=50,
        lr_scheduler_type="cosine",
        fp16=False,
        bf16=True,                         # RTX 5060 soporta BF16 nativo
        save_strategy="epoch",
        save_total_limit=1,
        logging_steps=5,                   # Logs mas frecuentes para monitorear
        dataloader_num_workers=0,
        dataloader_drop_last=True,         # Evita batches parciales que matan el proceso
        report_to="none",
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        seed=42,
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        args=sft_args,
        callbacks=[MetricsCallback(METRICS_OUT)],
    )

    t_start = time.time()
    result = trainer.train()
    elapsed = (time.time() - t_start) / 60

    print("\n" + "=" * 80)
    print("ENTRENAMIENTO COMPLETADO")
    print(f"  Loss final  : {result.training_loss:.5f}")
    print(f"  Tiempo total: {elapsed:.1f} minutos")
    print(f"  Adaptadores : {OUTPUT_DIR}")
    print("=" * 80)

    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("[DONE] Adaptadores STEM-1B guardados.")

if __name__ == "__main__":
    run()
