#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL Antigravity Reactive Bridge Listener
Permite que ambas instancias de Antigravity IDE (Laptop y Remote SSH)
se reactiven automáticamente (Reactive Wakeup) cuando haya una tarea o respuesta.
"""

import os
import sys
import json
import time

BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BRIDGE_DIR, "bridge_state.json")

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def wait_for_event(agent_role, timeout=300):
    """
    Bloquea hasta que haya un evento relevante para el agente y sale con código 0.
    - Si agent_role == 'ssh_agent': Espera una tarea PENDING dirigida a 'ssh_agent'.
    - Si agent_role == 'laptop_agent': Espera que la tarea activa pase a 'DONE'.
    """
    start_time = time.time()
    last_task_id = None
    last_status = None

    # Leer estado inicial
    init_state = load_state()
    active = init_state.get("active_task")
    if active:
        last_task_id = active.get("id")
        last_status = active.get("status")

        # Si ya hay una tarea PENDING para ssh_agent pendiente de ejecutar
        if agent_role == "ssh_agent" and last_status == "PENDING" and active.get("to") == "ssh_agent":
            print(f"[REACTIVE WAKEUP] Tarea pendiente detectada inmediatamente:")
            print(json.dumps(active, indent=2, ensure_ascii=False))
            sys.exit(0)

    print(f"[{agent_role.upper()}] Escuchando eventos en el puente... (Timeout: {timeout}s)")
    sys.stdout.flush()

    while time.time() - start_time < timeout:
        state = load_state()
        active = state.get("active_task")

        if active:
            curr_id = active.get("id")
            curr_status = active.get("status")
            curr_to = active.get("to")
            curr_from = active.get("from")

            if agent_role == "ssh_agent":
                # SSH Agent despierta cuando hay una nueva tarea PENDING para él
                if curr_status == "PENDING" and curr_to == "ssh_agent":
                    print(f"\n[REACTIVE WAKEUP - SSH AGENT] Nueva tarea recibida:")
                    print(f"ID: {curr_id}")
                    print(f"De: {curr_from}")
                    print(f"Descripción: {active.get('description')}")
                    print(f"Comando sugerido: {active.get('action_command')}")
                    print("=" * 60)
                    sys.exit(0)

            elif agent_role == "laptop_agent":
                # Laptop Agent despierta cuando la tarea pasa a DONE
                if curr_status == "DONE" and curr_from == "laptop_agent":
                    print(f"\n[REACTIVE WAKEUP - LAPTOP AGENT] Tarea completada por {active.get('to')}:")
                    print(f"ID: {curr_id}")
                    print(f"Resultado:\n{active.get('result')}")
                    print("=" * 60)
                    sys.exit(0)

        time.sleep(0.5)

    print("[TIMEOUT] No se recibieron eventos en el tiempo establecido.")
    sys.exit(1)

if __name__ == "__main__":
    role = "ssh_agent"
    timeout = 300
    if len(sys.argv) > 1:
        role = sys.argv[1]
    if len(sys.argv) > 2:
        timeout = int(sys.argv[2])
    wait_for_event(role, timeout)
