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

def start_services(background=True, port=3000):
    print(f"[*] Iniciando plataforma de laboratorio SentinelOS desde {BASE_DIR}...")
    
    # 1. Si Node / npm está disponible y node_modules está instalado, usar Node
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    node_modules = BASE_DIR / "node_modules"
    if npm_path and node_modules.exists() and (BASE_DIR / "package.json").exists():
        print(f"[*] Iniciando servidor SentinelOS Cockpit (Node.js/Vite en puerto {port})...")
        if background:
            if sys.platform == "win32":
                subprocess.Popen([npm_path, "run", "dev"], cwd=str(BASE_DIR),
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
            else:
                subprocess.Popen([npm_path, "run", "dev"], cwd=str(BASE_DIR),
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            print(f"[+] Servidor lanzado en segundo plano: http://localhost:{port}")
            return port
        else:
            subprocess.run([npm_path, "run", "dev"], cwd=str(BASE_DIR))
            return port

    # 2. Servidor nativo Python (0 dependencias externas, ideal para estudiantes con solo Git y Python)
    print(f"[*] Iniciando servidor nativo de laboratorio en Python (puerto {port})...")
    server_script = BASE_DIR / "installer" / "server_py.py"
    if background:
        if sys.platform == "win32":
            subprocess.Popen([sys.executable, str(server_script)], cwd=str(BASE_DIR),
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
        else:
            subprocess.Popen([sys.executable, str(server_script)], cwd=str(BASE_DIR),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        print(f"[+] Servidor nativo Python activo: http://localhost:{port}")
        return port
    else:
        subprocess.run([sys.executable, str(server_script)], cwd=str(BASE_DIR))
        return port

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
