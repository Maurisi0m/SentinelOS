import os, sys, time, subprocess, urllib.request, webbrowser
from installer.service_config import get_service_port

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "labsentinel_backend")
PORT = get_service_port(ROOT_DIR)

def is_running():
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/data", headers={"User-Agent": "SentinelLauncher"})
        with urllib.request.urlopen(req, timeout=30) as r:
            import json
            payload = json.loads(r.read().decode("utf-8"))
            return r.status == 200 and isinstance(payload, dict) and isinstance(payload.get("system"), dict)
    except Exception:
        return False

def main():
    if not is_running():
        # Priorizar pythonw de .venv para evitar abrir consola negra
        if sys.platform == "win32":
            venv_pyw = os.path.join(ROOT_DIR, ".venv", "Scripts", "pythonw.exe")
            venv_py = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
            sys_pyw = sys.executable.replace("python.exe", "pythonw.exe")
            py_bin = venv_pyw if os.path.exists(venv_pyw) else (venv_py if os.path.exists(venv_py) else sys_pyw)
            
            log_file = os.path.join(ROOT_DIR, "sentinel_backend.log")
            log_out = open(log_file, "a", encoding="utf-8")
            
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(PORT)],
                cwd=BACKEND_DIR,
                stdout=log_out,
                stderr=log_out,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
            )
        else:
            venv_py = os.path.join(ROOT_DIR, ".venv", "bin", "python3")
            py_bin = venv_py if os.path.exists(venv_py) else sys.executable
            log_file = os.path.join(ROOT_DIR, "sentinel_backend.log")
            log_out = open(log_file, "a", encoding="utf-8")
            subprocess.Popen(
                [py_bin, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(PORT)],
                cwd=BACKEND_DIR,
                stdout=log_out,
                stderr=log_out,
                start_new_session=True
            )

        # Esperar hasta que el servidor esté listo
        for _ in range(12):
            time.sleep(0.5)
            if is_running():
                break

    webbrowser.open(f"http://127.0.0.1:{PORT}")

if __name__ == "__main__":
    main()
