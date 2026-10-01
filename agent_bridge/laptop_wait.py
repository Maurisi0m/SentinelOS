#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import paramiko

HOST = "192.168.68.68"
USER = "mauro"
PASS = "Pollito92."

def wait_for_ssh_agent(timeout=300):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=22, username=USER, password=PASS)
    cmd = f"python3 /home/mauro/agent_bridge/bridge_listener.py laptop_agent {timeout}"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    client.close()
    
    if out:
        print(out.strip())
    if err:
        print("ERR:", err.strip())

if __name__ == "__main__":
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    wait_for_ssh_agent(t)
