"""SENTINEL AI Service.

Orchestrates:
1. Local SLM reasoning via llama-server (AVX2 native, mmap+mlock) with anti-loop penalties (repeat_penalty).
2. NVIDIA Nemotron Cloud Flagship (nvidia/nemotron-3.5-lightning-30b-a3b) with real server control via agentic tool calling.
3. Persistent Obsidian Knowledge Vault and live system diagnostics.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import socket
import subprocess
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
from vault_manager import get_all_notes, search_notes, save_note, extract_wikilinks
import lora_manager
import research_service
from self_learning_engine import CommandMemoryManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "active_model.json")

OLLAMA_API_URL = "http://127.0.0.1:11434"
LLAMA_SERVER_API_URL = "http://127.0.0.1:8080"

def get_ollama_api_url() -> str:
    """Detecta dinamicamente si Ollama esta corriendo en localhost o en un nodo de la red (ej. Servidor HP)."""
    env_url = os.environ.get("OLLAMA_API_URL") or os.environ.get("OLLAMA_HOST")
    if env_url:
        if not env_url.startswith("http"):
            env_url = f"http://{env_url}"
        return env_url.rstrip("/")

    # 1. Comprobar localhost (11434)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.12)
            if s.connect_ex(("127.0.0.1", 11434)) == 0:
                return "http://127.0.0.1:11434"
    except Exception:
        pass

    # 2. Comprobar Servidor HP en LAN o Tailscale
    candidate_hosts = ["192.168.68.65", "100.113.156.109", "labsentinel.tailc83bd7.ts.net", "192.168.68.68"]
    try:
        from mesh_engine import get_mesh_nodes
        for n in get_mesh_nodes():
            for c in n.get("candidates", []):
                try:
                    import urllib.parse
                    p = urllib.parse.urlparse(c).hostname
                    if p and p not in candidate_hosts:
                        candidate_hosts.append(p)
                except Exception:
                    pass
    except Exception:
        pass

    for host in candidate_hosts:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.25)
                if s.connect_ex((host, 11434)) == 0:
                    return f"http://{host}:11434"
        except Exception:
            continue

    return "http://127.0.0.1:11434"


# NVIDIA NIM Cloud API Config
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "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")
NVIDIA_MODEL = "mistralai/mistral-nemotron"

# Instanciar el administrador de memoria persistente de comandos en disco
cmd_memory = CommandMemoryManager(base_dir=BASE_DIR)

SYSTEM_PROMPT = """Eres SENTINEL, mentor pedagógico y sistema operativo cognitivo del Laboratorio STEM.
Tu misión es educar, inspirar y formar a jóvenes estudiantes en ciencia, ingeniería, programación y control de sistemas.

PERSONALIDAD Y ENFOQUE PEDAGÓGICO:
- Eres entusiasta, cálido, amigable y muy claro, nunca distante ni frío.
- Explicas conceptos complejos usando analogías intuitivas para jóvenes antes de entrar en código o comandos.
- Prohibido el uso de emojis en cualquier circunstancia.
- Usa enlaces dobles de Obsidian: [[Concepto]] para conceptos técnicos, librerías, protocolos y componentes.
- Si el estudiante realiza un saludo simple (ej. "hola", "buenas"), responde cordialmente en una sola oración presentándote como su mentor y preguntando en qué proyecto o concepto técnico desea trabajar hoy.
- Formato de fórmulas: Expresa fórmulas matemáticas rigurosas en notación LaTeX ($...$ para inline, $$...$$ para fórmulas en bloque).
- Estructura: Siempre que compares parámetros, conceptos o datos técnicos, utiliza tablas Markdown limpias (| Columna 1 | Columna 2 |).
- Termina SIEMPRE todas tus ideas y oraciones con punto final. Nunca cortes una frase a medias ni repitas fragmentos en bucle.

RESPUESTA A PREGUNTAS CONCEPTUALES ("¿Qué es X?"):
- Si el estudiante pregunta qué es un concepto, tecnología o protocolo (ej. "¿qué es SSH?", "¿qué es Docker?", "¿qué es la Ley de Ohm?"):
  1. Explica PRIMERO la definición y concepto fundamental con una analogía didáctica intuitiva.
  2. Explica su funcionamiento esencial (arquitectura cliente-servidor, cifrado asimétrico, túnel de datos).
  3. Presenta una TABLA Markdown comparativa con sus características, puertos y casos de uso.
  4. Si corresponde, incluye un ejemplo de comando conciso (máximo 2 a 3 líneas).
  5. PROHIBIDO volcar listas masivas de scripts de bash o código repetitivo cuando te preguntan un concepto teórico.
"""

logger = logging.getLogger("sentinel")

# Estado de actividad de la IA para concentración de recursos en tiempo real
IS_AI_ACTIVE = False
LAST_AI_INTERACTION = 0.0

def is_ai_active() -> bool:
    """Devuelve True si la IA está generando tokens o si interactuó hace menos de 15 segundos."""
    global IS_AI_ACTIVE, LAST_AI_INTERACTION
    return IS_AI_ACTIVE or (time.time() - LAST_AI_INTERACTION < 15.0)


# =========================================================================
# GESTIÓN Y PERSISTENCIA DEL MODELO ACTIVO
# =========================================================================

AVAILABLE_MODELS = [
    {
        "id": "sentinel-pure-stem-1b",
        "name": "Sentinel Pure STEM 1B",
        "description": "Local AVX2 Ultra-Rápido (~20 tok/s) - 100% Offline",
        "type": "local",
        "file": "sentinel-pure-stem-1b.Q4_K_M.gguf",
        "badge": "⚡ 1B Local"
    },
    {
        "id": "sentinel-pure-stem-3b",
        "name": "Sentinel Pure STEM 3B",
        "description": "Local AVX2 Análisis Profundo y Rigor STEM - 100% Offline",
        "type": "local",
        "file": "sentinel-pure-stem.Q4_K_M.gguf",
        "badge": "🧠 3B Local"
    },
    {
        "id": "nvidia-nemotron",
        "name": "NVIDIA Nemotron 3.5 Lightning",
        "description": "Cloud Flagship API - Control de Servidor Agéntico y Razonamiento",
        "type": "cloud",
        "badge": "🚀 NVIDIA Cloud"
    }
]

def get_active_model_id() -> str:
    """Lee el modelo activo persistido en disco."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_model", "sentinel-pure-stem-1b")
    except Exception as e:
        logger.error(f"Error leyendo {CONFIG_FILE}: {e}")
    return "sentinel-pure-stem-1b"

def set_active_model_id(model_id: str) -> bool:
    """Guarda el modelo activo en disco."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"active_model": model_id, "updated_at": time.time()}, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error guardando {CONFIG_FILE}: {e}")
        return False


def check_internet_connectivity(timeout: float = 2.0) -> Dict[str, Any]:
    """Comprueba si el servidor tiene acceso a Internet y mide latencia hacia Cloudflare DNS / NVIDIA API."""
    t0 = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        # 1.1.1.1 port 53 (DNS)
        sock.connect(("1.1.1.1", 53))
        sock.close()
        latency_ms = round((time.time() - t0) * 1000, 1)
        return {"has_internet": True, "latency_ms": latency_ms}
    except Exception as e:
        return {"has_internet": False, "error": str(e), "latency_ms": None}


# =========================================================================
# HERRAMIENTAS AGÉNTICAS DEL SERVIDOR PARA NVIDIA NEMOTRON
# =========================================================================

NEMOTRON_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_klipper_status",
            "description": "Consulta el estado real del servicio Klipper (systemctl) y el repositorio Git local en el servidor",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_system_command",
            "description": "Ejecuta un comando Bash seguro de inspección en el servidor Ubuntu (systemctl, git, df, free, uptime, ls, ps)",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando bash de inspección a ejecutar"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_telemetry",
            "description": "Obtiene la telemetría del servidor HP (CPU, memoria RAM y almacenamiento)",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def run_server_tool(name: str, args: dict) -> dict:
    """Ejecuta una herramienta en el servidor Ubuntu y devuelve datos reales estructurados."""
    if name == "check_klipper_status":
        try:
            svc = subprocess.check_output(["systemctl", "is-active", "klipper"], stderr=subprocess.STDOUT).decode().strip()
        except Exception:
            svc = "inactive"
        
        klipper_candidates = [
            os.path.expanduser("~/klipper"),
            "/home/pi/klipper",
            "/opt/klipper",
            "/home/mauro/klipper"
        ]
        klipper_path = next((p for p in klipper_candidates if os.path.isdir(p)), os.path.expanduser("~/klipper"))

        try:
            git_stat = subprocess.check_output(["git", "-C", klipper_path, "status", "-uno"], stderr=subprocess.STDOUT).decode().strip()
            git_rev = subprocess.check_output(["git", "-C", klipper_path, "rev-parse", "--short", "HEAD"], stderr=subprocess.STDOUT).decode().strip()
            # Fetch updates
            subprocess.run(["git", "-C", klipper_path, "fetch", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            git_behind = subprocess.check_output(["git", "-C", klipper_path, "status", "-uno"], stderr=subprocess.STDOUT).decode().strip()
        except Exception as e:
            git_rev = "unknown"
            git_behind = str(e)
        return {
            "service": svc,
            "current_commit": git_rev,
            "git_status": git_behind,
            "klipper_path": klipper_path
        }
    elif name == "execute_system_command":
        cmd = args.get("command", "").strip()
        allowed_prefixes = ["systemctl", "git", "df", "free", "uptime", "ls", "cat", "ps", "uname", "ip", "journalctl"]
        first_token = cmd.split()[0] if cmd else ""
        if first_token not in allowed_prefixes:
            return {"error": f"Comando '{first_token}' bloqueado por directiva de seguridad. Solo comandos de inspección permitidos."}
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10).decode(errors="replace")
            return {"output": out[:2000]}
        except subprocess.CalledProcessError as e:
            return {"error": f"Código {e.returncode}: {e.output.decode(errors='replace')[:600]}"}
        except Exception as e:
            return {"error": str(e)}
    elif name == "get_system_telemetry":
        try:
            uptime = subprocess.check_output(["uptime"], stderr=subprocess.STDOUT).decode().strip()
            free = subprocess.check_output(["free", "-h"], stderr=subprocess.STDOUT).decode().strip()
            df = subprocess.check_output(["df", "-h", "/"], stderr=subprocess.STDOUT).decode().strip()
            return {"uptime": uptime, "memory": free, "disk": df}
        except Exception as e:
            return {"error": str(e)}
    return {"error": f"Herramienta '{name}' desconocida."}


# =========================================================================
# GREETING & CONTEXT LOGIC
# =========================================================================

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
    q = re.sub(r"[^\w\s]", "", query.lower().strip())
    if not q or len(q) <= 4:
        return True
    return any(re.search(pat, q) for pat in GREETING_PATTERNS)


async def check_ollama_status() -> Dict[str, Any]:
    """Check active model and AI engine status."""
    active_id = get_active_model_id()
    active_meta = next((m for m in AVAILABLE_MODELS if m["id"] == active_id), AVAILABLE_MODELS[0])

    if active_id == "nvidia-nemotron":
        net = check_internet_connectivity()
        return {
            "online": net["has_internet"],
            "active_model": active_meta["name"],
            "model_id": active_id,
            "type": "cloud",
            "has_internet": net["has_internet"],
            "installed_models": [m["name"] for m in AVAILABLE_MODELS]
        }

    # Modelos locales (llama-server o Ollama)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1.2)) as session:
            async with session.get(f"{LLAMA_SERVER_API_URL}/props") as props_resp:
                if props_resp.status == 200:
                    props_data = await props_resp.json()
                    model_path = props_data.get("model_path") or ""
                    model_name = os.path.basename(model_path) if model_path else active_meta["name"]
                    return {
                        "online": True,
                        "active_model": model_name,
                        "model_id": active_id,
                        "type": "local",
                        "installed_models": [m["name"] for m in AVAILABLE_MODELS]
                    }
    except Exception:
        pass

    target_ollama_url = get_ollama_api_url()
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2.0)) as session:
            async with session.get(f"{target_ollama_url}/api/tags") as tags_resp:
                if tags_resp.status == 200:
                    tags_data = await tags_resp.json()
                    models_list = [m["name"] for m in tags_data.get("models", [])]
                    loc = "Local" if "127.0.0.1" in target_ollama_url else "Servidor HP"
                    return {
                        "online": True,
                        "active_model": f"{active_meta['name']} ({loc})",
                        "model_id": active_id,
                        "type": "local",
                        "installed_models": models_list or [m["name"] for m in AVAILABLE_MODELS]
                    }
    except Exception:
        pass

    return {
        "online": False,
        "active_model": active_meta["name"],
        "model_id": active_id,
        "type": active_meta["type"],
        "installed_models": [m["name"] for m in AVAILABLE_MODELS]
    }


def get_vault_context(query: str) -> str:
    """Recupera notas relevantes de la bóveda para enriquecer el turno de usuario solo cuando el contexto lo amerita."""
    notes = search_notes(query)
    # Solo inyectar si hay una nota con alta relevancia semántica (score >= 8: título, ID o tag coincidente)
    relevant_notes = [n for n in notes if n.get("score", 0) >= 8][:2]

    # Recuperar notas de perfil/preferencias solo cuando la consulta alude a la identidad o preferencias del usuario
    q_low = query.lower()
    if any(k in q_low for k in ["mi nombre", "quien soy", "mis preferencias", "mi perfil", "mi configuracion", "recuerdas"]):
        for n in notes:
            if n.get("id", "").lower() in ["perfil", "usuario", "preferencias", "configuracion"] and n not in relevant_notes:
                relevant_notes.insert(0, n)

    if not relevant_notes:
        return ""

    ctx = ["[MEMORIA DE BOVEDA OBSIDIAN (Notas Relevantes)]:"]
    for note in relevant_notes[:2]:
        title = note.get("title", "")
        content = note.get("content", "")[:350]
        ctx.append(f"- [[{title}]]: {content}")
    return "\n".join(ctx)


# =========================================================================
# STREAMING DE GENERACIÓN CONMUTABLE (LOCAL AVX2 / NVIDIA CLOUD)
# =========================================================================

async def chat_with_sentinel_stream(
    messages: List[Dict[str, str]],
    model: str = "sentinel:latest",
    effort: str = "med",
    enable_thinking: bool = False,
    enable_research: bool = False
) -> AsyncGenerator[str, None]:
    """Generador principal de streaming de respuestas."""
    global IS_AI_ACTIVE, LAST_AI_INTERACTION
    IS_AI_ACTIVE = True
    LAST_AI_INTERACTION = time.time()

    active_id = get_active_model_id()
    last_user_msg = messages[-1]["content"] if messages else ""

    try:
        is_user_greeting = is_greeting(last_user_msg)
        vault_ctx = "" if is_user_greeting else get_vault_context(last_user_msg)
        effort_lower = (effort or "med").lower()

        # =====================================================================
        # RUTA 1: NVIDIA NEMOTRON (CLOUD API + AUTO SERVER TOOLS)
        # =====================================================================
        if active_id == "nvidia-nemotron":
            net_stat = check_internet_connectivity()
            if not net_stat["has_internet"]:
                yield "Error de Conectividad: El servidor HP no cuenta con conexion a Internet para comunicarse con NVIDIA Nemotron API. Por favor, conmuta a un modelo local (1B o 3B) desde el selector superior."
                return

            headers = {
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Content-Type": "application/json"
            }

            system_content = (
                "Eres SENTINEL, el copiloto y mentor pedagógico del Laboratorio STEM operando en un servidor Ubuntu HP.\n"
                "DIRECTIVAS ESTRICTAS DE RESPUESTA:\n"
                "1. Responde SIEMPRE en español técnico riguroso, claro y didáctico.\n"
                "2. NO uses ningún emoji.\n"
                "3. Encierra conceptos clave con enlaces dobles de Obsidian: [[Concepto]].\n"
                "4. Expresa fórmulas matemáticas en LaTeX ($...$ para inline, $$...$$ para bloques).\n"
                "5. Presenta comparaciones y datos técnicos en tablas Markdown impecables.\n"
                "6. Si el estudiante pregunta qué es una tecnología o concepto (ej. qué es SSH): explica primero la definición y concepto fundamental, luego su funcionamiento y arquitectura, y presenta una tabla resumen. No te limites a volcar comandos.\n"
            )

            if enable_thinking or effort_lower == "high":
                system_content += "7. Si desarrollas cálculo o análisis profundo, enciérralo entre <think> y </think>. Fuera de <think>, presenta la respuesta final al estudiante.\n"

            nemotron_messages = [{"role": "system", "content": system_content}]

            # Contexto de memoria y herramientas del servidor
            context_prefix = []
            if vault_ctx:
                context_prefix.append(vault_ctx)

            # Si la pregunta se relaciona con Klipper o el estado del servidor, ejecutar telemetría real en vivo:
            lower_msg = last_user_msg.lower()
            if any(k in lower_msg for k in ["klipper", "impresora", "3d", "firmware"]):
                tool_data = run_server_tool("check_klipper_status", {})
                context_prefix.append(f"[ESTADO REAL DE KLIPPER EN SERVIDOR HP]:\n{json.dumps(tool_data, ensure_ascii=False, indent=2)}")
            elif any(k in lower_msg for k in ["servidor", "cpu", "ram", "memoria", "disco", "temperatura", "recursos"]):
                tool_data = run_server_tool("get_telemetry", {})
                context_prefix.append(f"[TELEMETRÍA REAL DEL SERVIDOR HP]:\n{json.dumps(tool_data, ensure_ascii=False, indent=2)}")

            for m in messages[:-1]:
                if m.get("content"):
                    nemotron_messages.append({"role": m["role"], "content": m["content"][:250]})

            enriched_msg = "\n\n".join(context_prefix) + f"\n\nPregunta: {last_user_msg}" if context_prefix else last_user_msg
            nemotron_messages.append({"role": "user", "content": enriched_msg})

            headers = {
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }

            payload = {
                "model": NVIDIA_MODEL,
                "messages": nemotron_messages,
                "temperature": 0.15 if effort_lower != "high" else 0.20,
                "max_tokens": 1200,
                "stream": True
            }

            try:
                connector = aiohttp.TCPConnector(family=socket.AF_INET)
                async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=45)) as session:
                    async with session.post(NVIDIA_API_URL, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            err_text = await resp.text()
                            yield f"Error API NVIDIA ({resp.status}): {err_text[:200]}"
                            return
                        
                        token_buffer = ""
                        async for line_raw in resp.content:
                            line = line_raw.decode("utf-8", errors="replace").strip()
                            if not line or not line.startswith("data: ") or line == "data: [DONE]":
                                continue
                            try:
                                chunk = json.loads(line[6:])
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    token_buffer += content
                                    last_space = max(token_buffer.rfind(" "), token_buffer.rfind("\n"))
                                    if last_space != -1:
                                        yield token_buffer[:last_space + 1]
                                        token_buffer = token_buffer[last_space + 1:]
                            except Exception:
                                continue
                        if token_buffer:
                            yield token_buffer
                        return
            except Exception as e:
                yield f"Error de comunicacion con NVIDIA API: {str(e)}"
                return

        # =====================================================================
        # RUTA 2: MODELOS LOCALES AVX2 (LLAMA-SERVER CON ANTI-BUCLES)
        # =====================================================================
        if is_user_greeting:
            active_model = "sentinel:latest"
            temperature = 0.08
            top_k = 10
            top_p = 0.80

            effort_instruction = ""
            thinking_instruction = ""
        elif effort_lower == "low":
            active_model = "sentinel-fast:latest"
            temperature = 0.12
            top_k = 10
            top_p = 0.80
            effort_instruction = "Responde de forma muy concisa y directa en 2 oraciones."
        elif effort_lower == "high":
            active_model = "sentinel:latest"
            temperature = 0.18
            top_k = 20
            top_p = 0.85
            effort_instruction = (
                "Desarrolla un analisis exhaustivo y riguroso. "
                "Estructura la respuesta usando Markdown profesional, tablas comparativas y formulas matematicas claras en notacion LaTeX ($...$). "
                "Prohibido divagar o repetir conceptos en bucle."
            )
        else:  # med (default)
            active_model = "sentinel:latest"
            temperature = 0.15
            top_k = 15
            top_p = 0.85
            effort_instruction = "Proporciona una explicacion concisa y clara. Utiliza tablas y formulas en notacion LaTeX si aplica."

        # Thinking mode para razonamiento analítico STEM (desactivado para saludos simples)
        thinking_instruction = ""
        if enable_thinking and not is_user_greeting:
            thinking_instruction = (
                "Antes de redactar la respuesta definitiva para el estudiante, debes detallar tu proceso de razonamiento reflexivo dentro de las etiquetas <pensamiento>...</pensamiento>.\n"
                "En el bloque de pensamiento analiza las variables e hipotesis. "
                "Luego, fuera de las etiquetas de pensamiento, presenta tu respuesta final sintetizada y clara al alumno."
            )

        # Live Research Integration (SOLO si el usuario activa el Modo Investigación)
        research_ctx = ""
        research_meta_tag = ""
        is_research_needed = bool(enable_research) and not is_user_greeting
        is_server_query = False
        r_data = None
        if is_research_needed and last_user_msg:
            try:
                r_data = research_service.perform_research(last_user_msg)
                if r_data and r_data.get("type") != "none":
                    is_server_query = (r_data.get("type") == "server")
                    research_ctx = f"[INVESTIGACION EN VIVO ({r_data.get('type', 'web').upper()})]:\n{r_data.get('summary', '')}"
                    meta_obj = {
                        "type": r_data.get("type"),
                        "summary": r_data.get("summary"),
                        "results": r_data.get("results", []),
                        "server": r_data.get("raw") if is_server_query else None
                    }
                    research_meta_tag = f"<!--RESEARCH_META:{json.dumps(meta_obj)}-->\n"
            except Exception as err:
                logger.error(f"Error realizando investigacion: {err}")

        if research_meta_tag:
            yield research_meta_tag

        if is_server_query and r_data:
            report_content = r_data.get("report") or research_service.format_server_update_report(r_data.get("raw", {}))
            tokens = re.split(r'(\s+)', report_content)
            for token in tokens:
                if token:
                    yield token
                    await asyncio.sleep(0.008)
            return

        if is_user_greeting:
            SYSTEM_PROMPT_GREETING = (
                "Eres SENTINEL, mentor pedagógico y copiloto cognitivo del Laboratorio STEM. "
                "El estudiante te ha saludado. Responde cordial, entusiasta y amistosamente en una sola oración dándole la bienvenida y preguntándole en qué concepto técnico, fórmula matemática o proyecto de ingeniería desean trabajar hoy. "
                "Prohibido terminantemente el uso de emojis."
            )
            formatted_messages = [
                {"role": "system", "content": SYSTEM_PROMPT_GREETING},
                {"role": "user", "content": last_user_msg}
            ]
        else:
            # System prompt compacto y de alta densidad para acelerar el prefill en CPU i5 Haswell.
            SYSTEM_PROMPT_LOCAL = (
                "Eres SENTINEL, mentor pedagogico del Laboratorio STEM. "
                "Responde con rigor tecnico, claridad didactica, formulas en LaTeX ($...$ para inline, $$...$$ para bloque) y tablas Markdown limpias. "
                "Usa enlaces dobles de Obsidian: [[Concepto]]. "
                "Prohibido el uso de emojis. Explica primero el concepto antes de cualquier codigo o comando."
            )

            formatted_messages = [
                {"role": "system", "content": SYSTEM_PROMPT_LOCAL}
            ]

            context_prefix_parts = []
            if vault_ctx:
                context_prefix_parts.append(vault_ctx)
            if research_ctx:
                context_prefix_parts.append(research_ctx)

            is_conceptual = any(last_user_msg.lower().strip().startswith(p) for p in ["que es", "¿que es", "que significa", "como funciona", "explica", "definicion", "cual es la ley", "ley de"])
            if not is_conceptual and not research_ctx:
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

        llama_url = f"{LLAMA_SERVER_API_URL}/v1/chat/completions"
        llama_payload = {
            "messages": formatted_messages,
            "cache_prompt": True,
            "stream": True,
            "max_tokens": 450 if is_server_query else 1200,
            "temperature": temperature,
            "top_p": top_p,
            # Sampling calibrado para rigor matemático y cero distorsión de variables:
            "repeat_penalty": 1.08,
            "repeat_last_n": 128,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "stop": ["<|eot_id|>", "<|end_of_text|>", "<|im_end|>", "<|endoftext|>", "Usuario:", "User:"]
        }

        used_llama_server = False
        token_buffer = ""
        is_stream_start = True

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

                                    # Si el modelo inicia erróneamente envolviendo toda la respuesta en ```markdown
                                    if is_stream_start:
                                        s_buf = token_buffer.lstrip()
                                        if s_buf.startswith("```markdown"):
                                            token_buffer = s_buf[11:].lstrip("\r\n")
                                            is_stream_start = False
                                        elif s_buf.startswith("```") and "\n" in s_buf:
                                            first_nl = s_buf.find("\n")
                                            token_buffer = s_buf[first_nl+1:]
                                            is_stream_start = False
                                        elif len(s_buf) > 15:
                                            is_stream_start = False

                                    last_space = max(token_buffer.rfind(" "), token_buffer.rfind("\n"))
                                    if last_space != -1 and not is_stream_start:
                                        word_chunk = token_buffer[:last_space + 1]
                                        token_buffer = token_buffer[last_space + 1:]
                                        yield word_chunk
                            except Exception:
                                continue
                        if token_buffer:
                            clean_end = token_buffer.rstrip()
                            if clean_end.endswith("```") and not clean_end.endswith("```bash"):
                                clean_end = clean_end[:-3].rstrip()
                            if clean_end:
                                yield clean_end
                            token_buffer = ""
        except Exception as err:
            logger.warning(f"llama-server no disponible o error ({err}), usando fallback Ollama...")

        # Fallback a Ollama si llama-server no respondió
        if not used_llama_server:
            ollama_base = get_ollama_api_url()
            url = f"{ollama_base}/api/chat"

            payload = {
                "model": active_model or "sentinel:latest",
                "messages": formatted_messages,
                "stream": True,
                "keep_alive": -1,
                "options": {
                    "num_thread": 4,
                    "num_ctx": 2048,
                    "num_predict": -1,
                    "temperature": temperature,
                    "top_k": top_k,
                    "top_p": top_p,
                    "repeat_penalty": 1.18
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
                                    last_space = max(token_buffer.rfind(" "), token_buffer.rfind("\n"))
                                    if last_space != -1:
                                        word_chunk = token_buffer[:last_space + 1]
                                        token_buffer = token_buffer[last_space + 1:]
                                        yield word_chunk
                                if chunk.get("done", False):
                                    break
                            except Exception:
                                continue
                        if token_buffer:
                            yield token_buffer
            except Exception as err:
                logger.error(f"Error comunicando con Ollama: {err}")
                yield f"Error de conexion con el motor local: {err}"

    finally:
        IS_AI_ACTIVE = False


async def auto_extract_and_learn(user_message: str, ai_response: str) -> Optional[Dict[str, Any]]:
    """Self-learning loop: extrae comandos y actualiza la memoria persistente."""
    try:
        # Detectar comandos ejecutables en la respuesta de la IA
        bash_cmds = re.findall(r"```(?:bash|sh|zsh)?\n(.*?)```", ai_response, re.DOTALL)
        if bash_cmds:
            for block in bash_cmds:
                lines = [l.strip() for l in block.strip().split("\n") if l.strip() and not l.strip().startswith("#")]
                for line in lines:
                    cmd_memory.record_command_execution(line, context=user_message)
            return {"action": "learned_commands", "count": len(bash_cmds)}
    except Exception as e:
        logger.error(f"Error en auto_extract_and_learn: {e}")
    return None
