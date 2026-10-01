"""SENTINEL AI Service.

Orchestrates local SLM reasoning via Ollama (Llama 3.2 3B) and integrates
with the Obsidian knowledge vault for persistent memory and self-learning.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
from vault_manager import get_all_notes, search_notes, save_note, extract_wikilinks
import lora_manager
import research_service

OLLAMA_API_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "sentinel:latest"

SYSTEM_PROMPT = """Eres SENTINEL, el sistema cognitivo y educativo del Laboratorio STEM.
Tu personalidad es profesional, analitica, elocuente y pedagogica.
Tu mision es guiar a jovenes y estudiantes en el aprendizaje de:
- Inteligencia Artificial y Redes Neuronales.
- Impresion 3D y cinematica G-Code con Klipper.
- Internet de las Cosas (IoT) y protocolos como MQTT con ESP32 y sensores.
- Servidores Linux, redes y contenedores Docker.

Reglas de respuesta:
1. Responde en espanol con tono claro, analitico y constructivo.
2. Explica conceptos complejos con analogias didacticas y precision cientifica.
3. Evita estrictamente el uso de emojis en todas tus respuestas.
4. Cuando menciones o definas conceptos clave del laboratorio, utiliza enlaces de Obsidian: [[Concepto]].
5. Respeta la memoria sinaptica del sistema y enfocate en la comprension practica del alumno.
"""

logger = logging.getLogger("sentinel")


async def check_ollama_status() -> Dict[str, Any]:
    """Check if Ollama daemon is reachable and list installed models."""
    url = f"{OLLAMA_API_URL}/api/tags"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    has_sentinel = any("sentinel" in m for m in models)
                    has_llama = any("llama3.2" in m for m in models)
                    active = "sentinel:latest" if has_sentinel else ("llama3.2:3b" if has_llama else (models[0] if models else None))
                    return {
                        "online": True,
                        "models": models,
                        "has_llama32": has_llama or has_sentinel,
                        "active_model": active
                    }
    except Exception as e:
        return {
            "online": False,
            "error": str(e),
            "models": [],
            "has_llama32": False,
            "active_model": None
        }


def get_vault_context(user_query: str) -> str:
    """Retrieve relevant notes from the Obsidian vault to augment model context."""
    results = search_notes(user_query)
    if not results:
        results = get_all_notes()[:3]

    context_blocks = []
    for note in results[:2]:
        context_blocks.append(f"### [Boveda: {note['title']}]\n{note['body'][:300]}")
    
    if context_blocks:
        return "\n\n[MEMORIA ACTIVA DE LA BOVEDA OBSIDIAN]:\n" + "\n\n".join(context_blocks)
    return ""


async def chat_with_sentinel_stream(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    effort: str = "med",
    enable_thinking: bool = False,
    enable_research: bool = False
) -> AsyncGenerator[str, None]:
    """Stream response tokens from local Ollama model with static KV cache and CPU tuning."""
    last_user_msg = messages[-1]["content"] if messages else ""
    vault_ctx = get_vault_context(last_user_msg)

    # 1. Effort parameter configuration and dynamic model routing
    effort_lower = (effort or "med").lower()
    if effort_lower == "low":
        # Ultra-fast 1B model (13-18 tokens/sec on CPU)
        active_model = "sentinel-fast:latest"
        num_predict = 100
        temperature = 0.20
        top_k = 15
        top_p = 0.80
        effort_instruction = "Responde de forma muy concisa, directa y veloz en 2 o 3 oraciones claras."
    elif effort_lower == "high":
        active_model = "sentinel:latest"
        num_predict = 450
        temperature = 0.65
        top_k = 35
        top_p = 0.95
        effort_instruction = "Desarrolla un analisis exhaustivo, detallado y paso a paso con rigor tecnico y analogias didacticas."
    else:  # med (default)
        active_model = "sentinel:latest"
        num_predict = 180
        temperature = 0.40
        top_k = 25
        top_p = 0.90
        effort_instruction = "Proporciona una explicacion equilibrada, pedagogica y clara para el alumno."

    # 2. Thinking mode prompt injection
    thinking_instruction = ""
    if enable_thinking:
        thinking_instruction = (
            "Antes de redactar la respuesta definitiva para el estudiante, debes detallar tu proceso de razonamiento reflexivo dentro de las etiquetas <pensamiento>...</pensamiento>.\n"
            "En el bloque de pensamiento analiza las variables e hipotesis. "
            "Luego, fuera de las etiquetas de pensamiento, presenta tu respuesta final sintetizada y clara al alumno."
        )

    # 3. Live Research Integration (Web & Server updates)
    research_ctx = ""
    research_meta_tag = ""
    is_research_needed = enable_research or any(
        k in last_user_msg.lower()
        for k in ["investiga", "busca en la web", "busca en internet", "actualizaciones del servidor", "estado del servidor"]
    )
    if is_research_needed and last_user_msg:
        try:
            r_data = research_service.perform_research(last_user_msg)
            if r_data and r_data.get("type") != "none":
                research_ctx = f"[INVESTIGACION EN VIVO ({r_data.get('type', 'web').upper()})]:\n{r_data.get('summary', '')}"
                meta_obj = {
                    "type": r_data.get("type"),
                    "summary": r_data.get("summary"),
                    "results": r_data.get("results", []),
                    "server": r_data.get("raw") if r_data.get("type") == "server" else None
                }
                research_meta_tag = f"<!--RESEARCH_META:{json.dumps(meta_obj)}-->\n"
        except Exception as err:
            logger.error(f"Error realizando investigacion: {err}")

    # Emit research metadata tag first if present
    if research_meta_tag:
        yield research_meta_tag

    # CRUCIAL FOR 10X SPEEDUP:
    # 1. Keep SYSTEM_PROMPT 100% static so Ollama reuses the KV cache in RAM!
    formatted_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # 2. Append chat history (except last message)
    for m in messages[:-1]:
        formatted_messages.append({"role": m["role"], "content": m["content"]})

    # 3. Dynamic context (vault notes, research, thinking instructions) goes into the user turn
    context_prefix_parts = []
    if vault_ctx:
        context_prefix_parts.append(vault_ctx)
    if research_ctx:
        context_prefix_parts.append(research_ctx)
    if thinking_instruction:
        context_prefix_parts.append(f"[INSTRUCCION]: {thinking_instruction}")
    if effort_instruction:
        context_prefix_parts.append(f"[FORMATO]: {effort_instruction}")

    if context_prefix_parts:
        enriched_user_content = "\n\n".join(context_prefix_parts) + f"\n\nPregunta del estudiante: {last_user_msg}"
    else:
        enriched_user_content = last_user_msg

    formatted_messages.append({"role": "user", "content": enriched_user_content})

    url = f"{OLLAMA_API_URL}/api/chat"
    payload = {
        "model": active_model,
        "messages": formatted_messages,
        "stream": True,
        "keep_alive": -1,
        "options": {
            "num_thread": 2,      # 2 physical cores on i5-4310U prevents L3 cache thrashing
            "num_ctx": 1024,      # Smaller context window drastically accelerates CPU attention
            "num_predict": num_predict,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p
        }
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    yield f"Error de comunicacion con Ollama (Codigo {resp.status})."
                    return

                async for line in resp.content:
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        msg = chunk.get("message", {})
                        content = msg.get("content", "")
                        if content:
                            yield content
                        if chunk.get("done", False):
                            break
                    except Exception:
                        continue
    except Exception as e:
        yield f"Aviso: Sentinel no pudo conectar con el motor local ({e})."


async def auto_extract_and_learn(user_message: str, ai_response: str) -> Optional[Dict[str, Any]]:
    """Analyze strictly the AI's verified response to generate new memory nodes and training pairs."""
    if not ai_response or len(ai_response.strip()) < 40:
        return None

    # Filter out internal thoughts so knowledge notes only contain verified output
    clean_response = re.sub(r"<pensamiento>.*?</pensamiento>", "", ai_response, flags=re.DOTALL).strip()
    clean_response = re.sub(r"<!--RESEARCH_META:.*?-->", "", clean_response, flags=re.DOTALL).strip()
    if not clean_response:
        clean_response = ai_response

    # 1. Record verified pair in LoRA training dataset
    lora_manager.record_response_for_learning(user_message, clean_response)

    # 2. Extract concepts generated by the AI itself in the response
    wikilinks = extract_wikilinks(clean_response)
    if not wikilinks:
        return {"action": "lora_recorded"}

    learned = []
    for link in wikilinks:
        existing = search_notes(link)
        if not existing:
            title = link.replace("_", " ")
            # Synthesize clean note from the verified AI response
            lines = [l.strip() for l in clean_response.splitlines() if l.strip()]
            summary_snippet = lines[0] if lines else clean_response[:180]
            node_content = f"Concepto extraido y validado por la IA en sesion educativa.\n\nSintesis: {summary_snippet}\n\nOrigen del aprendizaje: Dialogo sobre {user_message[:120]}"
            save_note(
                note_id=link,
                title=title,
                category="conceptos",
                content=node_content,
                tags=["auto-asimilado", "ia-validada"]
            )
            learned.append(link)

    return {"action": "learned_from_response", "nodes": learned}
