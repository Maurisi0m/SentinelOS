import torch
import time
import os
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_PATH = os.path.abspath("export/merged_model")

print("=" * 70)
print("TEST DE INFERENCIA NATIVA EN GPU (SIN CUANTIZAR - BFLOAT16 COMPLETO)")
print(f"Dispositivo: {torch.cuda.get_device_name(0)}")
print("=" * 70)

# Ver VRAM disponible antes de cargar
vram_free, vram_total = torch.cuda.mem_get_info()
print(f"VRAM libre inicial: {vram_free / 1024**3:.2f} GB / {vram_total / 1024**3:.2f} GB")

try:
    print("\n[1/3] Cargando Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    
    print("[2/3] Cargando Modelo Completo en BF16 directamente en VRAM GPU...")
    t_load_start = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        low_cpu_mem_usage=True
    )
    t_load = time.time() - t_load_start
    print(f"Modelo cargado en GPU en: {t_load:.2f}s")
    
    vram_after_load, _ = torch.cuda.mem_get_info()
    vram_used_by_model = (vram_free - vram_after_load) / 1024**3
    print(f"VRAM consumida por pesos BF16: {vram_used_by_model:.2f} GB")
    print(f"VRAM libre restante: {vram_after_load / 1024**3:.2f} GB")

    query = "¿Cómo diseñar un convertidor de nivel lógico con MOSFET BSS138 para I2C entre 5V y 3.3V?"
    prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"SENTINEL, sistema operativo cognitivo del Laboratorio STEM.<|eot_id|>\n"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{query}<|eot_id|>\n"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    print("\n[3/3] Generando tokens en GPU con Tensor Cores...")
    torch.cuda.synchronize()
    t_gen_start = time.time()
    
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.2,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    torch.cuda.synchronize()
    t_gen = time.time() - t_gen_start
    
    new_tokens = outputs.shape[1] - inputs.input_ids.shape[1]
    speed = new_tokens / t_gen
    
    print("\n" + "=" * 70)
    print(f"RESULTADOS DE RENDIMIENTO GPU (RTX 5060 - BLACKWELL):")
    print(f"- Tokens generados: {new_tokens}")
    print(f"- Tiempo de generacion: {t_gen:.2f} segundos")
    print(f"- Velocidad real: {speed:.2f} tokens/segundo")
    print("=" * 70)
    
    reply = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    print("\nRESPUESTA GENERADA:\n")
    print(reply[:500] + "...\n")

except Exception as e:
    print(f"\n[ERROR]: {e}")
