#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL Self-Learning Engine (Motor de Auto-Aprendizaje Continuo y Memoria Epistémica)
Permite al modelo:
1. Aprender de sí mismo y de fuentes verificadas en vivo (PyPI, Git, Web Search).
2. Registrar hechos fácticos de forma autónoma mediante Tool Calling ({"tool": "self_learning", ...}).
3. Almacenar el conocimiento en notas legibles de Obsidian (vault/self_learning/) y en buffer JSONL.
4. Recuperar hechos aprendidos en régimen Air-Gapped para erradicar alucinaciones de versiones y librerías.
5. Compilar los aprendizajes en datasets para re-entrenamiento y destilación en adaptadores LoRA.
"""

import os
import re
import json
import time
from datetime import datetime

class SelfLearningEngine:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.vault_dir = os.path.join(base_dir, "vault", "self_learning")
        os.makedirs(self.vault_dir, exist_ok=True)
        self.facts_file = os.path.join(self.vault_dir, "verified_facts.jsonl")

    def record_verified_fact(self, topic, fact, category="library_version", source="web_telemetry", details=None):
        """
        Registra un hecho fáctico verificado.
        Guarda en el archivo JSONL para LoRA y genera una nota Markdown para Obsidian.
        """
        if not topic or not fact:
            return {"status": "error", "message": "Faltan parámetros 'topic' o 'fact'."}

        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "topic": topic.strip(),
            "category": category.strip(),
            "fact": fact.strip(),
            "source": source.strip(),
            "details": details or {}
        }

        # 1. Almacenar en JSONL acumulativo
        with open(self.facts_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # 2. Generar/Actualizar Nota Atómica en Obsidian
        node_filename = f"{topic.replace(' ', '_').replace('/', '_')}.md"
        node_path = os.path.join(self.vault_dir, node_filename)

        obsidian_content = (
            f"---\n"
            f"tipo: auto_aprendizaje_epistemico\n"
            f"tema: \"[[{topic}]]\"\n"
            f"categoria: {category}\n"
            f"fuente: {source}\n"
            f"fecha: {timestamp}\n"
            f"---\n\n"
            f"# Hecho Verificado: [[{topic}]]\n\n"
            f"### Resumen Fáctico:\n{fact}\n\n"
            f"### Telemetría y Detalles:\n"
            f"```json\n{json.dumps(details or {}, indent=2, ensure_ascii=False)}\n```\n\n"
            f"### Origen de Aprendizaje:\n"
            f"- Registrado de forma autónoma por SENTINEL durante la sesión activa.\n"
            f"- Disponible para inferencia inmediata en régimen Air-Gapped.\n"
        )

        with open(node_path, "w", encoding="utf-8") as f:
            f.write(obsidian_content)

        return {
            "status": "ok",
            "action": "record_fact",
            "topic": topic,
            "category": category,
            "node_path": node_path,
            "total_learned_facts": self.count_facts(),
            "message": f"Hecho fáctico sobre '{topic}' aprendido y registrado exitosamente en Obsidian."
        }

    def query_learned_facts(self, query):
        """Busca hechos relevantes aprendidos previamente para inyección en contexto offline."""
        if not os.path.exists(self.facts_file):
            return {"status": "ok", "total_found": 0, "facts": []}

        q_terms = [t.lower() for t in query.lower().split() if len(t) > 2]
        matches = []

        try:
            with open(self.facts_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    text_blob = f"{item.get('topic', '')} {item.get('fact', '')} {item.get('category', '')}".lower()
                    if any(t in text_blob for t in q_terms):
                        matches.append(item)
        except Exception as e:
            return {"status": "error", "message": f"Error al consultar memoria de auto-aprendizaje: {str(e)}"}

        # Devolver las coincidencias más recientes (hasta 3)
        recent_matches = matches[-3:] if len(matches) > 3 else matches
        return {
            "status": "ok",
            "total_found": len(recent_matches),
            "facts": recent_matches
        }

    def count_facts(self):
        """Retorna la cantidad de hechos aprendidos almacenados."""
        if not os.path.exists(self.facts_file):
            return 0
        try:
            with open(self.facts_file, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def export_dataset_for_lora(self, output_file=None):
        """
        Compila los hechos aprendidos en un dataset conversacional de fine-tuning LoRA
        para destilar el conocimiento directamente en los pesos del modelo.
        """
        if output_file is None:
            output_file = os.path.join(self.vault_dir, "lora_self_learned_dataset.jsonl")

        if not os.path.exists(self.facts_file):
            return {"status": "empty", "message": "No hay hechos aprendidos para compilar."}

        count = 0
        with open(self.facts_file, "r", encoding="utf-8") as in_f, open(output_file, "w", encoding="utf-8") as out_f:
            for line in in_f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                topic = item.get("topic", "")
                fact = item.get("fact", "")
                category = item.get("category", "tecnología")

                # Estructura conversacional para el LLM
                sample = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.\n"
                                       "Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]]."
                        },
                        {
                            "role": "user",
                            "content": f"¿Cuáles son las especificaciones, versión y detalles técnicos verificados de [[{topic}]]?"
                        },
                        {
                            "role": "assistant",
                            "content": f"### Conocimiento Verificado: [[{topic}]]\n\n{fact}\n\n"
                                       f"- **Categoría Técnica**: {category}\n"
                                       f"- **Estado de Verificación**: Datos contrastados y asimilados en la memoria fáctica de SENTINEL."
                        }
                    ]
                }
                out_f.write(json.dumps(sample, ensure_ascii=False) + "\n")
                count += 1

        return {
            "status": "ok",
            "samples_compiled": count,
            "dataset_file": output_file,
            "message": f"Dataset de auto-aprendizaje compilado con {count} muestras para entrenamiento LoRA."
        }

    def execute_tool(self, tool_json):
        """Manejador para cuando el LLM emite directamente un Tool Call de auto-aprendizaje."""
        action = tool_json.get("action", "record_fact")
        if action == "record_fact":
            return self.record_verified_fact(
                topic=tool_json.get("topic"),
                fact=tool_json.get("fact") or tool_json.get("content"),
                category=tool_json.get("category", "knowledge"),
                source=tool_json.get("source", "autonomous_agent"),
                details=tool_json.get("details", {})
            )
        elif action == "query_facts":
            return self.query_learned_facts(tool_json.get("query", ""))
        else:
            return {"status": "error", "message": f"Acción '{action}' desconocida en self_learning."}


class CommandMemoryManager:
    """
    Memoria Real y Persistente de Comandos, Flags y Resolución de Errores.
    No es un prompt efímero: guarda en disco (JSONL + Obsidian) cada experiencia
    de comando ejecutado, por qué falló, qué significa cada parámetro y cómo resolverlo.
    Soporta: Linux (Bash/systemd), Windows (PowerShell/CMD) y macOS (Zsh/launchctl).
    """
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.cmd_vault_dir = os.path.join(base_dir, "vault", "self_learning", "commands")
        os.makedirs(self.cmd_vault_dir, exist_ok=True)
        self.history_file = os.path.join(base_dir, "vault", "self_learning", "command_mastery.jsonl")
        self._ensure_baseline_mastery()

    def record_command_lesson(self, command, os_target, status, error_output=None, resolution=None, flags_breakdown=None, key_learnings=None):
        """
        Registra una lección real de comando en disco y genera una nota atómica en Obsidian.
        """
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "command": command.strip(),
            "os_target": os_target.lower().strip(),
            "status": "success" if status in [0, "success", True, "ok"] else "error",
            "error_output": (error_output or "").strip(),
            "resolution": (resolution or "").strip(),
            "flags_breakdown": flags_breakdown or {},
            "key_learnings": (key_learnings or "").strip()
        }

        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Generar nota Obsidian
        slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', command[:40]).strip('_') or "comando"
        node_path = os.path.join(self.cmd_vault_dir, f"{os_target}_{slug}.md")
        flags_md = "\n".join([f"- **`{k}`**: {v}" for k, v in (flags_breakdown or {}).items()]) or "*(Sin flags específicos)*"

        obsidian_note = (
            f"---\n"
            f"tipo: memoria_de_comando\n"
            f"so: {os_target}\n"
            f"estado: {entry['status']}\n"
            f"fecha: {timestamp}\n"
            f"---\n\n"
            f"# Dominio de Comando: `{command}`\n\n"
            f"### 🖥️ Sistema Operativo Objetivo:\n[[{os_target.capitalize()}]]\n\n"
            f"### ⚙️ Desglose de Parámetros y Flags:\n{flags_md}\n\n"
            f"### 🔍 Lección de Diagnóstico / Error Previo:\n"
            f"**Error registrado:** `{error_output or 'Ninguno (ejecución exitosa)'}`\n\n"
            f"**Resolución / Solución Definitiva:**\n{resolution or 'Comando óptimo y validado.'}\n\n"
            f"### 💡 Aprendizaje Clave para Estudiantes:\n{key_learnings or 'Entendimiento del flujo de ejecución en terminal.'}\n"
        )

        with open(node_path, "w", encoding="utf-8") as f:
            f.write(obsidian_note)

        return {"status": "ok", "message": f"Lección de comando registrada en {node_path}"}

    def query_command_lessons(self, query, os_target=None):
        """Busca lecciones y trucos aprendidos sobre un comando o error."""
        if not os.path.exists(self.history_file):
            return []

        tokens = [t.lower() for t in query.lower().split() if len(t) > 1]
        matches = []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    if os_target and entry.get("os_target") != os_target.lower():
                        continue
                    blob = f"{entry.get('command','')} {entry.get('error_output','')} {entry.get('resolution','')} {entry.get('key_learnings','')}".lower()
                    score = sum(1 for t in tokens if t in blob)
                    if score > 0:
                        matches.append((score, entry))
        except Exception:
            return []

        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:3]]

    def get_mastery_context_prompt(self, query, os_target=None):
        """Genera un bloque de memoria real para alimentar el contexto del modelo."""
        lessons = self.query_command_lessons(query, os_target)
        if not lessons:
            return ""

        lines = ["\n[MEMORIA REAL DE COMANDOS Y LECCIONES APRENDIDAS]:"]
        for l in lessons:
            cmd = l.get("command", "")
            res = l.get("resolution", "")
            flags = l.get("flags_breakdown", {})
            f_str = ", ".join([f"`{k}` ({v})" for k, v in flags.items()])
            lines.append(f"- Comando: `{cmd}` | SO: {l.get('os_target','all').upper()}")
            if f_str:
                lines.append(f"  Parámetros clave: {f_str}")
            if res:
                lines.append(f"  Solución/Prevención de errores: {res}")
        return "\n".join(lines) + "\n"

    def _ensure_baseline_mastery(self):
        """Siembra lecciones maestras iniciales para Linux, Windows y macOS si el archivo está vacío."""
        if os.path.exists(self.history_file) and os.path.getsize(self.history_file) > 10:
            return

        baselines = [
            {
                "command": "systemctl status <servicio> -l --no-pager",
                "os_target": "linux",
                "status": "success",
                "flags_breakdown": {
                    "-l": "Full line: no trunca las líneas largas del log en la terminal",
                    "--no-pager": "Envía la salida directa a stdout sin abrir 'less', ideal para scripts automáticos"
                },
                "resolution": "Usar siempre con 'journalctl -xeu <servicio>' para ver la causa raíz exacta cuando un servicio entra en 'failed'.",
                "key_learnings": "Permite inspeccionar el fallo exacto de un daemon sin bloquear la sesión interactiva."
            },
            {
                "command": "Get-Service -Name <servicio> | Select-Object -Property Name, Status, StartType",
                "os_target": "windows",
                "status": "success",
                "flags_breakdown": {
                    "-Name": "Filtra por nombre exacto o con comodines (ej. 'wuauserv*')",
                    "Select-Object": "Proyecta únicamente las propiedades que interesan para no saturar la vista"
                },
                "resolution": "Si el servicio requiere elevación para iniciarse o detenerse, ejecutar PowerShell como Administrador o usar 'Start-Process powershell -Verb RunAs'.",
                "key_learnings": "En Windows, los comandos de PowerShell devuelven objetos reales, no solo texto plano como en CMD."
            },
            {
                "command": "launchctl print system/<label_servicio>",
                "os_target": "macos",
                "status": "success",
                "flags_breakdown": {
                    "print": "Inspecciona el estado detallado del job en launchd (reemplaza al viejo 'launchctl list')",
                    "system/": "Dominio de servicios a nivel de sistema (requiere sudo)"
                },
                "resolution": "En macOS moderno (Monterey/Ventura/Sonoma/Sequoia), nunca usar 'load/unload' depreciados si se puede usar 'bootstrap/bootout' o 'print'.",
                "key_learnings": "launchd es el equivalente unificado de init, systemd y cron en el ecosistema Apple."
            }
        ]

        for b in baselines:
            self.record_command_lesson(
                command=b["command"],
                os_target=b["os_target"],
                status=b["status"],
                flags_breakdown=b.get("flags_breakdown"),
                resolution=b.get("resolution"),
                key_learnings=b.get("key_learnings")
            )


if __name__ == "__main__":
    engine = SelfLearningEngine()
    cmd_mem = CommandMemoryManager()
    print("Probando CommandMemoryManager...")
    ctx = cmd_mem.get_mastery_context_prompt("systemctl status", "linux")
    print("Contexto Recuperado:\n", ctx)

