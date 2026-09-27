#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL Multi-Agent Collaboration Bridge (Local Laptop <-> Remote SSH Server)
Permite la coordinación y resolución colaborativa entre:
- Agente Laptop (Entrenamiento LoRA, GPU RTX 5060, Fusión GGUF, Calibración)
- Agente Servidor SSH (Kernel Linux, systemd, llama-server, Hardware, RAM, Benchmarking)
"""

import os
import sys
import json
import time
from datetime import datetime

BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
BOARD_FILE = os.path.join(BRIDGE_DIR, "BLACKBOARD.md")
STATE_FILE = os.path.join(BRIDGE_DIR, "bridge_state.json")

def init_bridge():
    os.makedirs(BRIDGE_DIR, exist_ok=True)
    if not os.path.exists(STATE_FILE):
        state = {
            "last_updated": datetime.now().isoformat(),
            "active_task": None,
            "laptop_status": "ONLINE",
            "ssh_agent_status": "IDLE",
            "history": []
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

def load_state():
    init_bridge()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    state["last_updated"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def update_board(last_event=""):
    state = load_state()
    active = state.get("active_task") or {}
    
    content = f"""# SENTINEL - TABLERO DE COLABORACION MULTI-AGENTE (BLACKBOARD)
*Ultima sincronizacion: {state.get('last_updated')}*

---

## ESTADO DE LOS AGENTES
- [LAPTOP] Agente Laptop (Windows / GPU RTX 5060): `{state.get('laptop_status', 'UNKNOWN')}`
- [SERVER] Agente Servidor (Ubuntu / SSH Core i5): `{state.get('ssh_agent_status', 'UNKNOWN')}`

---

## TAREA ACTIVA
- **ID:** `{active.get('id', 'Ninguna')}`
- **Origen:** `{active.get('from', 'N/A')}` -> **Destino:** `{active.get('to', 'N/A')}`
- **Estado:** `{active.get('status', 'SIN_TAREA')}`
- **Descripcion:**
> {active.get('description', 'Esperando instrucciones de trabajo.')}

- **Instrucciones / Comandos sugeridos:**
```bash
{active.get('action_command', '# Sin comando asignado')}
```

---

## RESULTADO / RESPUESTA DEL AGENTE RECEPTOR
```
{active.get('result', 'Esperando ejecucion...')}
```

---

## HISTORIAL DE COMUNICACION
"""
    for item in reversed(state.get("history", [])[-10:]):
        content += f"- [{item.get('ts')}] ({item.get('sender')} -> {item.get('receiver')}): {item.get('message')}\n"

    with open(BOARD_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def send_task(sender, receiver, task_id, desc, command=""):
    state = load_state()
    task = {
        "id": task_id,
        "from": sender,
        "to": receiver,
        "status": "PENDING",
        "description": desc,
        "action_command": command,
        "result": "En espera de que el agente receptor inicie la tarea.",
        "created_at": datetime.now().isoformat()
    }
    state["active_task"] = task
    state["history"].append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "sender": sender,
        "receiver": receiver,
        "message": f"Nueva tarea enviada [{task_id}]: {desc}"
    })
    save_state(state)
    update_board()
    print(f"[OK] Tarea [{task_id}] registrada exitosamente en {BOARD_FILE}")

def complete_task(agent_name, result_text, status="DONE"):
    state = load_state()
    if not state.get("active_task"):
        print("[AVISO] No hay ninguna tarea activa para completar.")
        return
    state["active_task"]["status"] = status
    state["active_task"]["result"] = result_text
    state["active_task"]["completed_at"] = datetime.now().isoformat()
    state["history"].append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "sender": agent_name,
        "receiver": state["active_task"]["from"],
        "message": f"Tarea finalizada ({status}): {result_text[:120]}"
    })
    save_state(state)
    update_board()
    print(f"[OK] Tarea completada por {agent_name}. Blackboard actualizado.")

def read_status():
    state = load_state()
    active = state.get("active_task")
    print("=" * 60)
    print(f"ESTADO MULTI-AGENTE - {state.get('last_updated')}")
    print(f"Laptop: {state.get('laptop_status')} | SSH Servidor: {state.get('ssh_agent_status')}")
    if active:
        print(f"Tarea activa: [{active.get('id')}] ({active.get('status')})")
        print(f"De: {active.get('from')} Para: {active.get('to')}")
        print(f"Descripción: {active.get('description')}")
        print(f"Resultado: {active.get('result')}")
    else:
        print("No hay tareas pendientes.")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        read_status()
    else:
        cmd = sys.argv[1]
        if cmd == "status":
            read_status()
        elif cmd == "send" and len(sys.argv) >= 5:
            # python bridge_cli.py send <to> <task_id> <desc> [command]
            receiver = sys.argv[2]
            task_id = sys.argv[3]
            desc = sys.argv[4]
            comm = sys.argv[5] if len(sys.argv) > 5 else ""
            send_task("laptop_agent", receiver, task_id, desc, comm)
        elif cmd == "done" and len(sys.argv) >= 3:
            # python bridge_cli.py done <result>
            complete_task("ssh_agent", sys.argv[2])
        elif cmd == "board":
            init_bridge()
            if not os.path.exists(BOARD_FILE):
                update_board()
            with open(BOARD_FILE, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print("Uso:")
            print("  python bridge_cli.py status")
            print("  python bridge_cli.py send <ssh_agent|laptop_agent> <id> <descripcion> [comando]")
            print("  python bridge_cli.py done 'Resultado de la ejecución'")
