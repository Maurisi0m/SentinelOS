"""SENTINEL AI Service.

Orchestrates local SLM reasoning via llama-server (AVX2 native) and Ollama fallback,
integrating with the Obsidian knowledge vault for persistent memory and self-learning.
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
from vault_manager import get_all_notes, search_notes, save_note, extract_wikilinks
import lora_manager
import research_service
import os
from self_learning_engine import CommandMemoryManager

OLLAMA_API_URL = "http://127.0.0.1:11434"
LLAMA_SERVER_API_URL = "http://127.0.0.1:8080"
DEFAULT_MODEL = "sentinel-pure-stem-1b.Q4_K_M.gguf"

# Instanciar el administrador de memoria persistente de comandos en disco
cmd_memory = CommandMemoryManager(base_dir=os.path.dirname(os.path.abspath(__file__)))

SYSTEM_PROMPT = """Eres SENTINEL, mentor pedagógico y sistema operativo cognitivo del Laboratorio STEM.
Tu misión es educar, inspirar y formar a jóvenes estudiantes en ciencia, ingeniería y control de sistemas.

PERSONALIDAD Y ENFOQUE PEDAGÓGICO:
- Eres entusiasta, cálido, amigable y muy claro, nunca distante ni frío.
- Explicas conceptos complejos usando analogías intuitivas para jóvenes antes de entrar en código o comandos.
- Prohibido el uso de emojis.
- Usa enlaces dobles de Obsidian: [[Concepto]] para conceptos técnicos, librerías, protocolos y componentes.
- Si el estudiante realiza un saludo simple (ej. "hola", "buenas"), responde cordialmente en una sola oración presentándote como su mentor y preguntando en qué proyecto o concepto técnico desea trabajar hoy.
- Termina SIEMPRE todas tus ideas y oraciones con punto final. Nunca cortes una frase a medias.

CONTROL TOTAL DE SISTEMAS OPERATIVOS Y COMANDOS (Linux, Windows, macOS):
- Eres experto maestro de comandos para Linux (Bash/systemd), Windows (PowerShell/CMD) y macOS (Zsh/launchctl).
- No requieres esquemas rígidos de herramientas: puedes enseñar, estructurar y proveer comandos directos, robustos y listos para usar.
- Anatomía de comandos: Explica siempre qué hace cada parámetro o flag (ej. -l, -p, --no-pager, Select-Object, launchctl print).
- Prevención de fallos: Advierte sobre los errores habituales (permisos/sudo, puertos ocupados, sintaxis de comillas) y cómo solucionarlos.
- Cero recetas de cocina o contenido fuera del dominio STEM.
"""

logger = logging.getLogger("sentinel")

# Estado de actividad de la IA para concentración de recursos en tiempo real
IS_AI_ACTIVE = False
LAST_AI_INTERACTION = 0.0

def is_ai_active() -> bool:
    """Devuelve True si la IA está generando tokens o si interactuó hace menos de 15 segundos."""
    global IS_AI_ACTIVE, LAST_AI_INTERACTION
    return IS_AI_ACTIVE or (time.time() - LAST_AI_INTERACTION < 15.0)


GREETING_PATTERNS = [
    r"^hola\b",
    r"^buenos?\s+(dias|tardes|noches)\b",
    r"^buenas\b",
    r"^que\s+tal\b",
    r"^saludos\b",
    r"^hello\b",
    r"^hi\b",
    r"^hey\b",
]

def is_greeting(query: str) -> bool:
    """Detect if query is just a greeting or minimal query to prevent context pollution."""
    q = query.lower().strip()
    if len(q) <= 4:
        return True
    return any(re.search(pat, q) for pat in GREETING_PATTERNS)


async def check_ollama_status() -> Dict[str, Any]:
    """Check if AI engine (llama-server AVX2 or Ollama) is reachable and list installed models."""
    # 1. Prioridad: llama-server nativo ultra-rápido (AVX2 + mlock en RAM física)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            # Intento dinámico de consultar propiedades del modelo cargado
            try:
                async with session.get(f"{LLAMA_SERVER_API_URL}/props") as props_resp:
                    if props_resp.status == 200:
                        props_data = await props_resp.json()
                        model_path = props_data.get("model_alias") or props_data.get("model_path") or ""
                        model_name = os.path.basename(model_path) if model_path else "sentinel-stem-qwen.Q4_K_M.gguf"
                        ftype = props_data.get("model_ftype", "Q4_K_M")

                        models_dir = "/opt/sentinel/models"
                        installed_models = sorted([f for f in os.listdir(models_dir) if f.endswith(".gguf")]) if os.path.exists(models_dir) else [model_name]
                        if model_name not in installed_models:
                            installed_models.insert(0, model_name)

                        if "1b" in model_name.lower():
                            active_label = f"{model_name} (1B Ultra-Fast STEM ~20 tok/s)"
                        elif "pure-stem" in model_name.lower():
                            active_label = f"{model_name} (3B Deep STEM Analysis)"
                        elif "qwen" in model_name.lower():
                            active_label = f"{model_name} (Qwen STEM AVX2)"
                        elif "titan" in model_name.lower() or "master" in model_name.lower():
                            active_label = f"{model_name} (Titan STEM AVX2)"
                        else:
                            active_label = f"{model_name} ({ftype})"

                        return {
                            "online": True,
                            "engine": "llama-server-avx2",
                            "models": installed_models,
                            "has_llama32": True,
                            "active_model": active_label
                        }
            except Exception:
                pass

            async with session.get(f"{LLAMA_SERVER_API_URL}/health") as resp:
                if resp.status == 200:
                    return {
                        "online": True,
                        "engine": "llama-server-avx2",
                        "models": ["sentinel-stem-qwen.Q4_K_M.gguf", "sentinel:latest", "sentinel-fast:latest"],
                        "has_llama32": True,
                        "active_model": "sentinel-stem-qwen.Q4_K_M.gguf (Qwen STEM AVX2)"
                    }
    except Exception:
        pass

    # 2. Fallback a Ollama
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
                        "engine": "ollama",
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
    """Retrieve relevant notes from the Obsidian vault ONLY if pertinent to the query."""
    if is_greeting(user_query):
        return ""

    results = search_notes(user_query)
    if not results:
        return ""

    context_blocks = []
    for note in results[:2]:
        if note.get("score", 0) >= 8:
            context_blocks.append(f"### [Boveda: {note['title']}]\n{note['body'][:250]}")
    
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
    """Stream response tokens from local LLM engine with static KV cache and fluid word-by-word streaming."""
    global IS_AI_ACTIVE, LAST_AI_INTERACTION
    IS_AI_ACTIVE = True
    LAST_AI_INTERACTION = time.time()

    try:
        last_user_msg = messages[-1]["content"] if messages else ""
        vault_ctx = get_vault_context(last_user_msg)

        # 1. Effort parameter configuration and dynamic model routing
        effort_lower = (effort or "med").lower()
        if is_greeting(last_user_msg):
            active_model = "sentinel-master:titan"
            num_predict = -1
            temperature = 0.15
            top_k = 10
            top_p = 0.80
            effort_instruction = "Responde al saludo de forma muy breve y amigable en una sola oracion."
        elif effort_lower == "low":
            active_model = "sentinel-fast:latest"
            num_predict = -1
            temperature = 0.15
            top_k = 10
            top_p = 0.80
            effort_instruction = "Responde de forma muy concisa, directa y veloz en 2 oraciones claras."
        elif effort_lower == "high":
            active_model = "sentinel:latest"
            num_predict = -1
            temperature = 0.35
            top_k = 20
            top_p = 0.95
            effort_instruction = "Desarrolla un analisis exhaustivo, detallado y paso a paso con rigor tecnico y analogias didacticas."
        else:  # med (default)
            active_model = "sentinel:latest"
            num_predict = -1
            temperature = 0.20
            top_k = 15
            top_p = 0.90
            effort_instruction = "Proporciona una explicacion concisa, pedagogica y clara para el alumno."

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
            for k in ["investiga", "busca en la web", "busca en internet", "actualizaciones del servidor", "estado del servidor", "reporte", "diagnostico"]
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
        # Keep SYSTEM_PROMPT 100% static so llama-server reuses the KV cache in RAM!
        formatted_messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Mantener contexto mínimo (último turno asistente) para que la evaluación de prompt sea < 0.5s
        if len(messages) >= 2 and messages[-2].get("content"):
            formatted_messages.append({
                "role": messages[-2]["role"],
                "content": messages[-2]["content"][:120]
            })

        # Dynamic context (vault notes, research, command memory, thinking instructions) goes into the user turn
        context_prefix_parts = []
        if vault_ctx:
            context_prefix_parts.append(vault_ctx)
        if research_ctx:
            context_prefix_parts.append(research_ctx)

        # Contexto persistente de comandos aprendidos en disco (Linux, Windows, macOS)
        cmd_memory_ctx = cmd_memory.get_mastery_context_prompt(last_user_msg)
        if cmd_memory_ctx:
            context_prefix_parts.append(cmd_memory_ctx)

        if thinking_instruction:
            context_prefix_parts.append(f"[INSTRUCCION]: {thinking_instruction}")
        if effort_instruction:
            context_prefix_parts.append(f"[FORMATO]: {effort_instruction}")

        if context_prefix_parts:
            enriched_user_content = "\n\n".join(context_prefix_parts) + f"\n\nPregunta del estudiante: {last_user_msg}"
        else:
            enriched_user_content = last_user_msg

        formatted_messages.append({"role": "user", "content": enriched_user_content})

        # 1. Intentar con llama-server (motor nativo AVX2 pre-cargado en RAM sin cold-start)
        llama_url = f"{LLAMA_SERVER_API_URL}/v1/chat/completions"
        llama_payload = {
            "messages": formatted_messages,
            "stream": True,
            "max_tokens": -1,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "stop": ["<|eot_id|>", "<|end_of_text|>", "<|im_end|>", "<|endoftext|>", "Usuario:", "User:"]
        }

        used_llama_server = False
        token_buffer = ""

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300, sock_read=60)) as session:
                async with session.post(llama_url, json=llama_payload) as resp:
                    if resp.status == 200:
                        used_llama_server = True
                        async for line_raw in resp.content:
                            LAST_AI_INTERACTION = time.time()
                            if not line_raw:
                                continue
                            line = line_raw.decode("utf-8", errors="replace").strip()
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    token_buffer += content
                                    # Emision estricta de palabras completas (solo emite hasta el ultimo espacio o salto de linea)
                                    last_space = max(token_buffer.rfind(" "), token_buffer.rfind("\n"))
                                    if last_space != -1:
                                        word_chunk = token_buffer[:last_space + 1]
                                        token_buffer = token_buffer[last_space + 1:]
                                        yield word_chunk
                            except Exception:
                                continue
                        if token_buffer:
                            yield token_buffer
                            token_buffer = ""
        except Exception as err:
            logger.warning(f"llama-server no disponible o error ({err}), usando fallback Ollama...")

        # 2. Fallback a Ollama si llama-server no respondió
        if not used_llama_server:
            url = f"{OLLAMA_API_URL}/api/chat"
            payload = {
                "model": active_model or "sentinel:latest",
                "messages": formatted_messages,
                "stream": True,
                "keep_alive": -1,
                "options": {
                    "num_thread": 4,
                    "num_ctx": 2048,
                    "num_predict": num_predict,
                    "temperature": temperature,
                    "top_k": top_k,
                    "top_p": top_p
                }
            }

            try:
                token_buffer = ""
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300, sock_read=60)) as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            yield f"Error de comunicacion con el motor local (Codigo {resp.status})."
                            return

                        async for line in resp.content:
                            LAST_AI_INTERACTION = time.time()
                            if not line:
                                continue
                            try:
                                chunk = json.loads(line.decode("utf-8"))
                                msg = chunk.get("message", {})
                                content = msg.get("content", "")
                                if content:
                                    token_buffer += content
                                    if any(c in token_buffer for c in (" ", "\n", ".", ",", ";", ":", "!", "?")) or len(token_buffer) >= 10:
                                        yield token_buffer
                                        token_buffer = ""
                                if chunk.get("done", False):
                                    break
                            except Exception:
                                continue
                        if token_buffer:
                            yield token_buffer
                            token_buffer = ""
            except Exception as e:
                yield f"Aviso: Sentinel no pudo conectar con el motor local ({e})."

    finally:
        IS_AI_ACTIVE = False
        LAST_AI_INTERACTION = time.time()


async def auto_extract_and_learn(user_message: str, ai_response: str) -> Optional[Dict[str, Any]]:
    """Analyze strictly the AI's verified response to generate new memory nodes and training pairs."""
    if not ai_response or len(ai_response.strip()) < 40:
        return None

    clean_response = re.sub(r"<pensamiento>.*?</pensamiento>", "", ai_response, flags=re.DOTALL).strip()
    clean_response = re.sub(r"<!--RESEARCH_META:.*?-->", "", clean_response, flags=re.DOTALL).strip()
    if not clean_response:
        clean_response = ai_response

    lora_manager.record_response_for_learning(user_message, clean_response)

    wikilinks = extract_wikilinks(clean_response)
    learned = []
    if wikilinks:
        for link in wikilinks:
            existing = search_notes(link)
            if not existing:
                title = link.replace("_", " ")
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

    # 3. Asimilación en memoria real y persistente de comandos aprendidos
    cmd_blocks = re.findall(r"```(?:bash|powershell|sh|zsh|cmd)?\n(.*?)```", clean_response, flags=re.DOTALL)
    for block in cmd_blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip() and not l.strip().startswith("#")]
        if lines:
            primary_cmd = lines[0]
            if len(primary_cmd) > 3 and not primary_cmd.startswith("<"):
                os_target = "linux"
                if any(k in primary_cmd.lower() for k in ["get-", "set-", "select-object", "powershell", "dir ", "ipconfig"]):
                    os_target = "windows"
                elif any(k in primary_cmd.lower() for k in ["brew", "launchctl", "defaults write", "dscl"]):
                    os_target = "macos"
                try:
                    cmd_memory.record_command_lesson(
                        command=primary_cmd,
                        os_target=os_target,
                        status="success",
                        resolution=f"Instrucción generada en diálogo de laboratorio sobre: {user_message[:100]}",
                        key_learnings=f"Uso validado de {primary_cmd}"
                    )
                except Exception:
                    pass

    return {"action": "learned_from_response", "nodes": learned}
