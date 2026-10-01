#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import base64
import time
import paramiko

HOST = "192.168.68.68"
USER = "mauro"
PASS = "Pollito92."

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=22, username=USER, password=PASS)
    return client

def post_task(task_id, desc, command=""):
    client = get_ssh_client()
    payload = {
        "id": task_id,
        "from": "laptop_agent",
        "to": "ssh_agent",
        "description": desc,
        "action_command": command
    }
    b64 = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode('utf-8')).decode('ascii')
    py_code = f"""
import json, base64, sys
from bridge_cli import send_task
data = json.loads(base64.b64decode('{b64}').decode('utf-8'))
send_task(data['from'], data['to'], data['id'], data['description'], data['action_command'])
"""
    b64_code = base64.b64encode(py_code.encode('utf-8')).decode('ascii')
    cmd = f"python3 -c \"import base64; exec(base64.b64decode('{b64_code}').decode('utf-8'))\""
    stdin, stdout, stderr = client.exec_command(f"cd /home/mauro/agent_bridge && {cmd}")
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    client.close()
    if out:
        print(out.strip())
    if err:
        print("ERR:", err.strip())

def check_status():
    client = get_ssh_client()
    stdin, stdout, stderr = client.exec_command("python3 /home/mauro/agent_bridge/bridge_cli.py status")
    out = stdout.read().decode('utf-8', errors='replace').strip()
    sys.stdout.buffer.write((out + "\n").encode('utf-8'))
    client.close()

def get_board():
    client = get_ssh_client()
    stdin, stdout, stderr = client.exec_command("cat /home/mauro/agent_bridge/BLACKBOARD.md")
    out = stdout.read().decode('utf-8', errors='replace').strip()
    sys.stdout.buffer.write((out + "\n").encode('utf-8'))
    client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        check_status()
    elif sys.argv[1] == "status":
        check_status()
    elif sys.argv[1] == "board":
        get_board()
    elif sys.argv[1] == "send" and len(sys.argv) >= 4:
        # python laptop_sync.py send <task_id> <desc> [command]
        tid = sys.argv[2]
        desc = sys.argv[3]
        comm = sys.argv[4] if len(sys.argv) > 4 else ""
        post_task(tid, desc, comm)
    else:
        print("Uso: python laptop_sync.py [status|board|send <id> <desc> [cmd]]")
