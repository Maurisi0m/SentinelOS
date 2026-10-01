#!/usr/bin/env python3
"""
SENTINEL STEM Mega-Dataset Builder
Combina datasets propios + descarga datasets publicos STEM de HuggingFace
Meta: 10,000+ muestras instruccion-respuesta en formato ChatML

Fuentes:
  Propias:  healing_thought_c, master_agentic, mega_lora, titan_unified,
            lora_dataset, deep_reasoning_r1, dpo_stem, agentic_coding, tool_calling
  Publicas: iamtarun/python_code_instructions_18k_alpaca (filtrado)
            codeparrot/github-code-clean (Python/C/C++ snippets)
            teknium/OpenHermes-2.5 (filtrado por categoria STEM)
"""
import os, json, random, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE, "dataset")
OUT = os.path.join(DATASET_DIR, "stem_mega_train.jsonl")

SYSTEM_PROMPT = (
    "SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.\n"
    "Tu mision es educar, programar, operar el laboratorio con maxima excelencia tecnica y pedagogica.\n"
    "DIRECTIVAS: Responde en espanol con rigor cientifico. "
    "Encierra conceptos clave en [[Concepto]]. Cero emojis. "
    "Estilo analitico y didactico. Solo temas STEM: ciencia, tecnologia, "
    "ingenieria, matematicas, IA, programacion, computo, telecomunicaciones, electronica."
)

# ── 1. Datasets propios a incluir (excluye fiction, trivia, unwanted) ──────────
OWN_FILES = [
    "healing_thought_c_dataset.jsonl",
    "master_agentic_dataset.jsonl",
    "mega_lora_dataset.jsonl",
    "titan_unified_dataset.jsonl",
    "lora_dataset.jsonl",
    "deep_reasoning_r1_dataset.jsonl",
    "dpo_stem_dataset.jsonl",
    "agentic_coding_dataset.jsonl",
    "tool_calling_dataset.jsonl",
    "ultimate_sentinel_dataset.jsonl",
]

samples = []

print("[1/4] Cargando datasets propios STEM...")
for fname in OWN_FILES:
    path = os.path.join(DATASET_DIR, fname)
    if not os.path.exists(path):
        print(f"  [SKIP] No existe: {fname}")
        continue
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                msgs = obj.get("messages", [])
                if len(msgs) >= 2:
                    # Normalizar: asegurarse que system prompt es el de SENTINEL
                    has_system = any(m.get("role") == "system" for m in msgs)
                    if not has_system:
                        msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + msgs
                    else:
                        # Reemplazar system con el estandar SENTINEL
                        for i, m in enumerate(msgs):
                            if m.get("role") == "system":
                                msgs[i]["content"] = SYSTEM_PROMPT
                                break
                    samples.append({"messages": msgs})
                    count += 1
            except json.JSONDecodeError:
                pass
    print(f"  [OK] {fname}: {count} muestras")

print(f"\n  Subtotal propias: {len(samples)} muestras")

# ── 2. Datasets publicos de HuggingFace ────────────────────────────────────────
print("\n[2/4] Descargando datasets publicos STEM de HuggingFace...")

try:
    from datasets import load_dataset
    
    # ── 2a. Python code instructions (18k alpaca format) ──
    print("  Cargando iamtarun/python_code_instructions_18k_alpaca...")
    ds_py = load_dataset("iamtarun/python_code_instructions_18k_alpaca", split="train", trust_remote_code=True)
    added_py = 0
    for ex in ds_py:
        instruction = ex.get("instruction", "").strip()
        output = ex.get("output", "").strip()
        if not instruction or not output:
            continue
        if len(output) < 80:
            continue  # Respuestas muy cortas no aportan
        samples.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": output}
            ]
        })
        added_py += 1
        if added_py >= 3000:
            break
    print(f"  [OK] python_code_instructions: {added_py} muestras")

    # ── 2b. OpenHermes 2.5 - filtrar solo categorias STEM ──
    STEM_KEYWORDS = [
        "python", "code", "programming", "algorithm", "function", "class",
        "network", "protocol", "tcp", "udp", "http", "api", "server",
        "arduino", "esp32", "microcontroller", "gpio", "i2c", "uart", "pwm",
        "linux", "bash", "shell", "docker", "kubernetes", "git",
        "machine learning", "neural", "deep learning", "pytorch", "tensorflow",
        "math", "algebra", "calculus", "differential", "integral", "matrix",
        "physics", "quantum", "electromagnetic", "circuit", "resistor",
        "sql", "database", "json", "xml", "yaml", "regex",
        "c language", "c++", "rust", "assembly", "memory", "pointer",
        "oscilloscope", "multimeter", "sensor", "motor", "servo", "pid",
        "cybersecurity", "encryption", "hash", "ssl", "tls", "firewall",
        "iot", "mqtt", "modbus", "canbus", "ethernet",
    ]

    print("  Cargando teknium/OpenHermes-2.5 (filtrando STEM)...")
    ds_hermes = load_dataset("teknium/OpenHermes-2.5", split="train", trust_remote_code=True)
    added_hermes = 0
    for ex in ds_hermes:
        convs = ex.get("conversations", [])
        if not convs or len(convs) < 2:
            continue
        # Tomar solo si hay keyword STEM
        text_check = " ".join(
            str(c.get("value", "")).lower() for c in convs
        )
        if not any(kw in text_check for kw in STEM_KEYWORDS):
            continue
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for c in convs:
            role = "user" if c.get("from") in ("human", "user") else "assistant"
            msgs.append({"role": role, "content": c.get("value", "").strip()})
        if len(msgs) >= 3:
            samples.append({"messages": msgs})
            added_hermes += 1
        if added_hermes >= 4000:
            break
    print(f"  [OK] OpenHermes-2.5 STEM: {added_hermes} muestras")

except Exception as e:
    print(f"  [WARN] Error descargando HF: {e}")
    print("  Continuando solo con datos propios...")

# ── 3. Shuffle y guardado ──────────────────────────────────────────────────────
print(f"\n[3/4] Mezclando y guardando {len(samples)} muestras totales...")
random.seed(42)
random.shuffle(samples)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

size_mb = os.path.getsize(OUT) / 1024**2
print(f"[4/4] Dataset guardado: {OUT}")
print(f"      Total muestras: {len(samples)}")
print(f"      Tamano: {size_mb:.1f} MB")
print("\n[DONE] stem_mega_train.jsonl listo para entrenamiento.")
