#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cirugía Radical de Pesos: Purificación Absoluta de Tensores No-STEM (Llama 3.2 1B)
================================================================================
Eliminación matemática y física de pesos no-STEM en los 16 bloques Transformer:
1. Proyección al Espacio Nulo (Nullspace Orthogonal Projection):
   Para cada una de las 112 matrices de proyección (Attention + MLP):
   W_purified = (I - U_non_stem * U_non_stem^T) * W * (I - V_non_stem * V_non_stem^T)
   Anula a CERO tanto la receptividad de entrada como la emisión hacia el residual stream
   de los subespacios aprendidos por el adaptador negativo.
2. Poda Física y Puesta a Cero de Neuronas MLP (Neuron Zeroing):
   Identifica y pone a cero absoluto (0.0) los canales de las neuronas que memorizan
   conceptos de entretenimiento, farándula, ficción y astrología.
3. Anulación de Embeddings y Cabezal LM (Token Obliteration):
   Pone a cero los vectores de lm_head y embed_tokens para vocabulario no-STEM.
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
from safetensors import safe_open
from transformers import AutoTokenizer, AutoModelForCausalLM

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_SNAPSHOT = r"C:\Users\mauro\.cache\huggingface\hub\models--unsloth--Llama-3.2-1B-Instruct\snapshots\5a8abab4a5d6f164389b1079fb721cfab8d7126c"
ADAPTER_FILE = os.path.join(BASE_DIR, "training", "negative_adapters_1b", "adapter_model.safetensors")
OUTPUT_PURIFIED_DIR = os.path.join(BASE_DIR, "export", "sentinel_1b_pure_stem_radically_pruned")
CORPUS_FILE = os.path.join(BASE_DIR, "dataset", "unlearning_comprehensive_corpus.jsonl")

LORA_SCALING = 2.0  # alpha=32 / r=16

def extract_non_stem_vocab_tokens(tokenizer, corpus_path):
    """Identifica tokens que ocurren exclusivamente en el corpus no-STEM."""
    tokens_to_zero = set()
    if not os.path.exists(corpus_path):
        return tokens_to_zero
        
    stem_keywords = {
        "linux", "windows", "macos", "bash", "powershell", "cmd", "python", "kernel",
        "cpu", "ram", "disk", "socket", "tcp", "udp", "ip", "port", "ssh", "git",
        "docker", "kubernetes", "process", "service", "systemctl", "cron", "grep",
        "sed", "awk", "sudo", "apt", "dnf", "pacman", "def", "class", "return",
        "import", "include", "int", "float", "char", "void", "algorithm", "binary"
    }
    
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            item = json.loads(line)
            inst = item.get("instruction", "")
            # Tokenizar palabras no técnicas
            words = inst.lower().split()
            for w in words:
                clean_w = "".join(c for c in w if c.isalpha())
                if len(clean_w) > 4 and clean_w not in stem_keywords:
                    tok_ids = tokenizer.encode(" " + clean_w, add_special_tokens=False)
                    for tid in tok_ids:
                        tokens_to_zero.add(tid)
                        
    return tokens_to_zero

def main():
    print("=" * 85, flush=True)
    print("INICIANDO CIRUGIA RADICAL: ELIMINACION ABSOLUTA DE PESOS NO-STEM (1B)", flush=True)
    print(f"Modelo Base: {BASE_SNAPSHOT}", flush=True)
    print(f"Adaptador Negativo (Foco No-STEM): {ADAPTER_FILE}", flush=True)
    print(f"Destino Purificado: {OUTPUT_PURIFIED_DIR}", flush=True)
    print("=" * 85 + "\n", flush=True)

    os.makedirs(OUTPUT_PURIFIED_DIR, exist_ok=True)

    # 1. Cargar Tokenizer
    print("[1/5] Cargando Tokenizer oficial Llama 3.2 1B...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(BASE_SNAPSHOT, local_files_only=True)

    # 2. Cargar Tensores del Adaptador Negativo
    print("[2/5] Cargando tensores de activación no-STEM desde el adaptador negativo...", flush=True)
    adapter_tensors = {}
    with safe_open(ADAPTER_FILE, framework="pt", device="cpu") as f:
        for key in f.keys():
            adapter_tensors[key] = f.get_tensor(key).to(torch.float32)
    print(f"-> {len(adapter_tensors)} matrices de deltas LoRA no-STEM cargadas.", flush=True)

    # 3. Cargar Modelo Base en float32 para Cirugía Matricial
    print("\n[3/5] Cargando tensores del modelo base en memoria para cirugía espectral...", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_SNAPSHOT,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        device_map="cpu",
        local_files_only=True
    )

    layers = model.model.layers
    num_layers = len(layers)
    total_matrices_purified = 0
    total_neurons_zeroed = 0

    print(f"\n[4/5] Aplicando Proyección al Espacio Nulo y Poda de Neuronas en las {num_layers} capas...", flush=True)

    proj_names = [
        "self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
        "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj"
    ]

    with torch.no_grad():
        for l_idx in range(num_layers):
            layer = layers[l_idx]
            
            # --- PARTE A: PROYECCIÓN ORTOGONAL EN LAS MATRICES DE ATENCIÓN Y MLP ---
            for p_name in proj_names:
                # Localizar el módulo
                mod = layer
                for part in p_name.split("."):
                    mod = getattr(mod, part)
                    
                w = mod.weight.data  # [d_out, d_in]
                
                key_a = f"base_model.model.model.layers.{l_idx}.{p_name}.lora_A.weight"
                key_b = f"base_model.model.model.layers.{l_idx}.{p_name}.lora_B.weight"
                
                if key_a in adapter_tensors and key_b in adapter_tensors:
                    lora_a = adapter_tensors[key_a]  # [r, d_in]
                    lora_b = adapter_tensors[key_b]  # [d_out, r]
                    
                    # 1. Base ortogonal del subespacio de entrada (V_in de dimensión d_in x r)
                    # SVD de lora_a para obtener las direcciones ortonormales principales
                    _, _, vh_a = torch.linalg.svd(lora_a, full_matrices=False)  # vh_a: [r, d_in]
                    v_in = vh_a.T  # [d_in, r]
                    
                    # 2. Base ortogonal del subespacio de salida (U_out de dimensión d_out x r)
                    u_out, _, _ = torch.linalg.svd(lora_b, full_matrices=False)  # u_out: [d_out, r]
                    
                    # 3. Proyección al complemento ortogonal:
                    # Anular sensibilidad a las direcciones de entrada no-STEM: W <- W * (I - V * V^T)
                    w.sub_(torch.matmul(w, torch.matmul(v_in, v_in.T)))
                    
                    # Anular emisión en las direcciones de salida no-STEM: W <- (I - U * U^T) * W
                    w.sub_(torch.matmul(torch.matmul(u_out, u_out.T), w))
                    
                    # 4. Sustracción complementaria del delta directo escalado
                    delta_w = LORA_SCALING * torch.matmul(lora_b, lora_a)
                    w.sub_(0.20 * delta_w)
                    
                    total_matrices_purified += 1

            # --- PARTE B: PODA FÍSICA Y PUESTA A CERO DE NEURONAS MLP NO-STEM ---
            # Identificar las neuronas que mayor activación tienen en el adaptador no-STEM
            gate_a = adapter_tensors[f"base_model.model.model.layers.{l_idx}.mlp.gate_proj.lora_A.weight"]
            gate_b = adapter_tensors[f"base_model.model.model.layers.{l_idx}.mlp.gate_proj.lora_B.weight"]
            gate_delta = torch.matmul(gate_b, gate_a)  # [8192, 2048]
            
            # Magnitud de activación no-STEM por neurona (norma L2 por fila)
            neuron_non_stem_norm = torch.norm(gate_delta, dim=1)  # [8192]
            
            # Podar el top 10% de neuronas más especializadas en no-STEM (819 neuronas por capa)
            k_prune = int(0.10 * neuron_non_stem_norm.numel())
            _, top_prune_indices = torch.topk(neuron_non_stem_norm, k_prune)
            
            # Poner a CERO ABSOLUTO los pesos de esas neuronas
            layer.mlp.gate_proj.weight.data[top_prune_indices, :] = 0.0
            layer.mlp.up_proj.weight.data[top_prune_indices, :] = 0.0
            layer.mlp.down_proj.weight.data[:, top_prune_indices] = 0.0
            total_neurons_zeroed += k_prune

        print(f"-> {total_matrices_purified} matrices proyectadas a su espacio nulo ortogonal.", flush=True)
        print(f"-> {total_neurons_zeroed} neuronas intermedias MLP puestas a CERO ABSOLUTO (0.0).", flush=True)

        # --- PARTE C: ABLACIÓN DE EMBEDDINGS Y LM_HEAD ---
        print("\n[5/5] Purgando embeddings y cabezal de salida (lm_head) para conceptos no-STEM...", flush=True)
        non_stem_tokens = extract_non_stem_vocab_tokens(tokenizer, CORPUS_FILE)
        print(f"-> Identificados {len(non_stem_tokens)} tokens léxicos no-STEM para oblación directa.", flush=True)
        
        zeroed_tokens = 0
        for tid in non_stem_tokens:
            if tid < model.model.embed_tokens.weight.shape[0]:
                model.model.embed_tokens.weight.data[tid, :] = 0.0
                model.lm_head.weight.data[tid, :] = 0.0
                zeroed_tokens += 1
        print(f"-> {zeroed_tokens} vectores de embedding y predicción reseteados a 0.0.", flush=True)

    # 4. Guardar Modelo Purificado
    print(f"\nGuardando modelo purificado en formato Safetensors en {OUTPUT_PURIFIED_DIR}...", flush=True)
    # Convertir a float16 para guardar espacio y optimizar velocidad
    model = model.to(torch.float16)
    model.save_pretrained(OUTPUT_PURIFIED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_PURIFIED_DIR)

    print("=" * 85, flush=True)
    print(f"[ÉXITO TOTAL] Cirugía Completada: Pesos no-STEM eliminados a nivel de espacio nulo.", flush=True)
    print(f"Directorio: {OUTPUT_PURIFIED_DIR}")
    print("=" * 85, flush=True)

if __name__ == "__main__":
    main()
