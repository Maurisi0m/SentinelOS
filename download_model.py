import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import os

MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
print(f"=== DESCARGANDO / CARGANDO MODELO BASE: {MODEL_ID} ===")

# Configuración de memoria segura para RTX 5060 (8GB VRAM)
if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.80, 0)
    print("Límite de memoria asignado: 80% (~6.5 GB máx.)")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

print("Descargando / Cargando Tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"
print("Tokenizer cargado con éxito.")

print("Descargando / Cargando Modelo Base en 4-bit NF4...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map={"": 0},
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
)

print("Modelo cargado con éxito en GPU!")
allocated = torch.cuda.memory_allocated(0) / (1024**3)
reserved = torch.cuda.memory_reserved(0) / (1024**3)
print(f"VRAM Asignada: {allocated:.2f} GB | VRAM Reservada: {reserved:.2f} GB de 8 GB")
print("=== VERIFICACIÓN COMPLETADA SIN RIESGO DE BSOD ===")
