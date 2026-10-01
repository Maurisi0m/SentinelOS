#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL MESH SATELLITE AGENT
Daemon ultraligero para servidores secundarios en laboratorios escolares y de investigación.
Transmite telemetría en tiempo real (CPU, RAM, GPU, Discos, Sesiones activas) y permite ejecución
de comandos remotos autorizados desde el Core de SentinelOS.
"""
import os, sys, time, json, socket, subprocess, platform
import urllib.request

CORE_URL = os.environ.get("SENTINEL_CORE_URL", "http://127.0.0.1:8001")
TOKEN = os.environ.get("SENTINEL_MESH_TOKEN", "default_secret")
NODE_NAME = os.environ.get("SENTINEL_NODE_NAME", platform.node())

def get_telemetry():
    # 1. CPU & Load
    load1, load5, load15 = (0, 0, 0)
    if hasattr(os, "getloadavg"):
        load1, load5, load15 = os.getloadavg()

    # 2. RAM & Swap via /proc/meminfo or system
    mem_total, mem_free, mem_avail = (0, 0, 0)
    if os.path.exists("/proc/meminfo"):
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        m = {}
        for l in lines:
            parts = l.split(":")
            if len(parts) == 2:
                m[parts[0].strip()] = parts[1].strip().split()[0]
        mem_total = int(m.get("MemTotal", 0)) // 1024
        mem_free = int(m.get("MemFree", 0)) // 1024
        mem_avail = int(m.get("MemAvailable", mem_free)) // 1024

    # 3. GPU (nvidia-smi si existe)
    gpu_info = []
    try:
        smi = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL
        )
        for line in smi.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpu_info.append({
                    "name": parts[0],
                    "util_percent": int(parts[1]),
                    "mem_used_mb": int(parts[2]),
                    "mem_total_mb": int(parts[3]),
                    "temp_c": int(parts[4])
                })
    except Exception:
        pass

    # 4. Sesiones Activas
    active_sessions = []
    try:
        who = subprocess.check_output(["who"], text=True, stderr=subprocess.DEVNULL)
        for line in who.strip().splitlines():
            if line:
                active_sessions.append(line.split()[0])
    except Exception:
        pass

    return {
        "node_id": NODE_NAME,
        "os": platform.system(),
        "release": platform.release(),
        "arch": platform.machine(),
        "uptime": time.time(),
        "load": [load1, load5, load15],
        "memory": {
            "total_mb": mem_total,
            "available_mb": mem_avail,
            "used_mb": max(mem_total - mem_avail, 0),
            "usage_percent": round((1 - (mem_avail / max(mem_total, 1))) * 100, 1)
        },
        "gpus": gpu_info,
        "sessions": list(set(active_sessions))
    }

def register_and_loop():
    print(f"[*] Iniciando Sentinel Satellite Agent en {NODE_NAME}...")
    print(f"[*] Conectando con Sentinel Core en {CORE_URL}...")
    
    url = f"{CORE_URL}/api/mesh/heartbeat"
    while True:
        try:
            payload = get_telemetry()
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {TOKEN}"
                }
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp_data = json.loads(resp.read().decode())
                # Si el Core envió un comando para ejecutar en este nodo:
                cmd = resp_data.get("pending_command")
                if cmd:
                    print(f"[*] Ejecutando comando remoto autorizado: {cmd}")
                    out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    # Reportar salida de regreso al Core
                    ack_req = urllib.request.Request(
                        f"{CORE_URL}/api/mesh/command_result",
                        data=json.dumps({"node_id": NODE_NAME, "stdout": out.stdout, "stderr": out.stderr, "returncode": out.returncode}).encode(),
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}
                    )
                    urllib.request.urlopen(ack_req, timeout=5)
        except Exception as e:
            # Fallo transitorio de red, reintentar silenciosamente
            pass
        time.sleep(3)

if __name__ == "__main__":
    register_and_loop()
