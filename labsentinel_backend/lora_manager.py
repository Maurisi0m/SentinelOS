"""LoRA and Memory Adaptation Manager for SENTINEL.

Manages fine-tuning datasets, self-learning synthesis from verified AI responses,
and Ollama custom model/adapter creation from scratch.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import vault_manager

DATASET_FILE = vault_manager.VAULT_DIR / "memoria" / "lora_dataset.jsonl"
MODELFILE_PATH = vault_manager.VAULT_DIR / "memoria" / "Modelfile.sentinel"
BASE_MODEL = "llama3.2:3b"
TARGET_MODEL = "sentinel:latest"

logger = logging.getLogger("sentinel.lora")


def init_dataset_if_missing():
    """Ensure dataset file exists with initial high-quality STEM pairs."""
    if not DATASET_FILE.exists():
        DATASET_FILE.parent.mkdir(parents=True, exist_ok=True)
        initial_pairs = [
            {
                "instruction": "Que es SENTINEL y cual es su funcion en el laboratorio?",
                "response": "SENTINEL es el sistema cognitivo del laboratorio escolar STEM, encargado de coordinar la memoria, guiar a los estudiantes en conceptos de IA, IoT, impresion 3D con Klipper y administracion de servidores Linux.",
                "source": "verified_knowledge"
            },
            {
                "instruction": "Como se relaciona Klipper con el codigo G en impresion 3D?",
                "response": "Klipper traslada los calculos cinematicos pesados hacia el procesador del servidor, ejecutando comandos G-Code con precision para controlar micropasos y aceleraciones de los motores.",
                "source": "verified_knowledge"
            },
            {
                "instruction": "Cual es la funcion del protocolo MQTT en IoT?",
                "response": "MQTT es un protocolo de mensajeria ligero basado en publicacion y suscripcion que permite a microcontroladores como ESP32 transmitir telemetria de sensores de forma instantanea al broker Mosquitto.",
                "source": "verified_knowledge"
            }
        ]
        with open(DATASET_FILE, "w", encoding="utf-8") as f:
            for pair in initial_pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")


init_dataset_if_missing()


def record_response_for_learning(user_query: str, verified_ai_response: str) -> bool:
    """Record high-quality verified response to dataset for self-learning."""
    if len(verified_ai_response.strip()) < 30:
        return False

    entry = {
        "instruction": user_query.strip(),
        "response": verified_ai_response.strip(),
        "source": "self_learned_response"
    }

    with open(DATASET_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return True


def get_dataset_stats() -> Dict[str, Any]:
    """Return dataset size and recent instruction pairs."""
    count = 0
    recent = []
    if DATASET_FILE.exists():
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    count += 1
                    try:
                        recent.append(json.loads(line))
                    except Exception:
                        pass
    return {
        "total_examples": count,
        "recent_samples": recent[-5:] if recent else [],
        "dataset_path": str(DATASET_FILE),
        "target_model": TARGET_MODEL
    }


def compile_sentinel_model(custom_adapter_path: Optional[str] = None) -> Dict[str, Any]:
    """Build and optimize the Sentinel model in Ollama from scratch."""
    stats = get_dataset_stats()
    
    # Generate system prompt containing accumulated memory summaries
    notes = vault_manager.get_all_notes()
    concept_list = ", ".join([f"[[{n['id']}]]" for n in notes[:12]])

    system_prompt = f"""Eres SENTINEL, el sistema cognitivo y educativo del Laboratorio STEM.
Tu mision es guiar a estudiantes en conceptos de ciencia, computacion, Inteligencia Artificial, Klipper (impresion 3D), IoT (MQTT) y servidores Linux.
Tu memoria y conocimientos activos abarcan: {concept_list}.
Reglas de comunicacion:
1. Explica conceptos con rigor, claridad y entusiasmo pedagogico.
2. Evita usar emojis en tus respuestas.
3. Cuando establezcas conceptos clave del laboratorio, relacionalos usando sintaxis de enlace de Obsidian: [[Concepto]].
4. Se preciso, conciso y responde directamente a la necesidad del alumno."""

    modelfile_content = f"""FROM {BASE_MODEL}
PARAMETER num_ctx 2048
PARAMETER num_thread 4
PARAMETER temperature 0.6
PARAMETER top_k 30
PARAMETER top_p 0.9
PARAMETER stop "<|start_header_id|>"
PARAMETER stop "<|end_header_id|>"
PARAMETER stop "<|eot_id|>"
SYSTEM \"\"\"{system_prompt}\"\"\"
"""
    if custom_adapter_path and os.path.exists(custom_adapter_path):
        modelfile_content += f"\nADAPTER {custom_adapter_path}\n"

    MODELFILE_PATH.write_text(modelfile_content, encoding="utf-8")

    # Run ollama create inside the running docker container
    cmd = f'docker exec ollama sh -c "cat << \'EOF\' > /tmp/Modelfile\n{modelfile_content}\nEOF\nollama create {TARGET_MODEL} -f /tmp/Modelfile"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {
            "success": res.returncode == 0,
            "output": res.stdout.strip(),
            "error": res.stderr.strip() if res.returncode != 0 else None,
            "target_model": TARGET_MODEL,
            "dataset_count": stats["total_examples"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
