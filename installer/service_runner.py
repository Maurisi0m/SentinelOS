import os
import sys
import subprocess
import shutil
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

BASE_DIR = Path(__file__).resolve().parent.parent

def start_services(background=True):
    print(f"[*] Iniciando plataforma de laboratorio SentinelOS desde {BASE_DIR}...")
    
    # 1. Si Node / npm está disponible, iniciar el servidor unificado de Node
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_path and (BASE_DIR / "package.json").exists():
        print("[*] Iniciando servidor SentinelOS Cockpit (Node.js/Vite en puerto 3000)...")
        if background:
            if sys.platform == "win32":
                subprocess.Popen([npm_path, "run", "dev"], cwd=str(BASE_DIR),
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
            else:
                subprocess.Popen([npm_path, "run", "dev"], cwd=str(BASE_DIR),
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            print("[+] Servidor lanzado en segundo plano: http://localhost:3000")
            return
        else:
            subprocess.run([npm_path, "run", "dev"], cwd=str(BASE_DIR))
            return

    print("[!] Nota: Ejecuta 'npm install' y 'npm run dev' para el frontend web.")

def stop_services():
    print("[*] Deteniendo procesos de SentinelOS...")
    count = 0
    if psutil:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(proc.info.get('cmdline') or []).lower()
                if "server.ts" in cmd or "labsentinel" in cmd or "sentinel" in cmd:
                    if proc.pid != os.getpid():
                        proc.terminate()
                        count += 1
            except Exception:
                pass
    print(f"[+] {count} procesos finalizados.")
