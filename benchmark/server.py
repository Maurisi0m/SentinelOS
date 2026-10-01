#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL MLOps & Benchmarking Server
Servidor FastAPI para telemetría de hardware, monitoreo de entrenamiento,
inferencia en tiempo real y benchmarking de tokens/segundo.
"""

import os
import time
import json
import psutil
import torch
import re
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_PATH = os.path.join(BASE_DIR, "benchmark", "training_metrics.json")
ADAPTERS_PATH = os.path.join(BASE_DIR, "training", "adapters")
STATIC_DIR = os.path.join(BASE_DIR, "benchmark", "static")
FINAL_GGUF = os.path.join(BASE_DIR, "export", "output_gguf", "sentinel-stem.Q4_K_M.gguf")

app = FastAPI(title="SENTINEL STEM Benchmarking Center")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.2

# Variable global para modelo en memoria cuando se requiera inferencia
loaded_model = None
loaded_tokenizer = None

def get_system_stats():
    """Obtiene métricas de hardware en tiempo real."""
    vram_alloc = 0.0
    vram_reserved = 0.0
    gpu_name = "NVIDIA GeForce RTX 5060 Laptop GPU"
    
    if torch.cuda.is_available():
        vram_alloc = round(torch.cuda.memory_allocated(0) / (1024**3), 2)
        vram_reserved = round(torch.cuda.memory_reserved(0) / (1024**3), 2)
        gpu_name = torch.cuda.get_device_name(0)

    vm = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=None)

    return {
        "gpu": {
            "name": gpu_name,
            "vram_allocated_gb": vram_alloc,
            "vram_reserved_gb": vram_reserved,
            "vram_total_gb": 8.0,
            "vram_percentage": round((vram_reserved / 8.0) * 100, 1)
        },
        "system": {
            "cpu_usage_percent": cpu_percent,
            "ram_used_gb": round(vm.used / (1024**3), 2),
            "ram_total_gb": round(vm.total / (1024**3), 2),
            "ram_percentage": vm.percent
        }
    }

@app.get("/")
def get_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Dashboard en preparación...</h1>")

@app.get("/api/telemetry")
def api_telemetry():
    return JSONResponse(get_system_stats())

@app.get("/api/training_status")
def api_training_status():
    """Retorna los datos de la curva de pérdida del entrenamiento."""
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return JSONResponse({"status": "available", "history": data})
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)})
    return JSONResponse({"status": "pending", "history": []})

@app.get("/api/model_info")
def api_model_info():
    """Detalla la existencia y características de los artefactos del modelo."""
    gguf_exists = os.path.exists(FINAL_GGUF)
    gguf_size_mb = round(os.path.getsize(FINAL_GGUF) / (1024**2), 2) if gguf_exists else 0
    adapters_exist = os.path.exists(ADAPTERS_PATH) and os.path.exists(os.path.join(ADAPTERS_PATH, "adapter_model.safetensors"))

    return {
        "base_model": "unsloth/Llama-3.2-3B-Instruct",
        "architecture": "LlamaForCausalLM (3.21B params)",
        "quantization_target": "Q4_K_M",
        "gguf_ready": gguf_exists,
        "gguf_path": FINAL_GGUF,
        "gguf_size_mb": gguf_size_mb,
        "adapters_ready": adapters_exist,
    }

@app.post("/api/benchmark")
def api_benchmark(req: PromptRequest):
    """Ejecuta inferencia con medición de latencia y velocidad (tokens/seg)."""
    global loaded_model, loaded_tokenizer
    
    start_time = time.time()
    
    # Carga perezosa si no está en memoria
    if loaded_model is None:
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        bnb_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        loaded_tokenizer = AutoTokenizer.from_pretrained("unsloth/Llama-3.2-3B-Instruct")
        if loaded_tokenizer.pad_token is None:
            loaded_tokenizer.pad_token = loaded_tokenizer.eos_token
            
        loaded_model = AutoModelForCausalLM.from_pretrained(
            "unsloth/Llama-3.2-3B-Instruct",
            quantization_config=bnb_cfg,
            device_map={"": 0},
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        )

    sys_prompt = ("Eres SENTINEL, el sistema operativo cognitivo y tutor pedagógico del Laboratorio STEM. "
                  "Responde en español con rigor científico. Prohibido emojis. Usa [[Concepto_Clave]] para conceptos técnicos.")

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": req.prompt}
    ]
    prompt_text = loaded_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = loaded_tokenizer(prompt_text, return_tensors="pt").to("cuda")

    time_prefill_start = time.time()
    with torch.no_grad():
        output_ids = loaded_model.generate(
            **inputs,
            max_new_tokens=req.max_tokens,
            temperature=req.temperature,
            do_sample=True if req.temperature > 0 else False,
            pad_token_id=loaded_tokenizer.pad_token_id,
            eos_token_id=loaded_tokenizer.eos_token_id,
        )
    total_time = time.time() - time_prefill_start

    generated_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    output_text = loaded_tokenizer.decode(generated_ids, skip_special_tokens=True)
    tokens_generated = len(generated_ids)
    tokens_per_sec = round(tokens_generated / total_time, 2) if total_time > 0 else 0

    # Análisis pedagógico de la respuesta
    obsidian_links = re.findall(r"\[\[(.*?)\]\]", output_text)
    has_emojis = bool(re.search(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]", output_text))

    return {
        "text": output_text,
        "metrics": {
            "tokens_generated": tokens_generated,
            "latency_seconds": round(total_time, 3),
            "tokens_per_second": tokens_per_sec,
            "vram_used_gb": round(torch.cuda.memory_allocated(0) / (1024**3), 2),
            "obsidian_links_found": obsidian_links,
            "emoji_compliance": "PASSED (0 emojis)" if not has_emojis else "FAILED (Emojis detectados)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8501)
