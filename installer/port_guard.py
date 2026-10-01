import socket
import sys

try:
    import psutil
except ImportError:
    psutil = None

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def release_port(port: int) -> bool:
    """Intenta liberar el puerto cerrando procesos conflictivos huérfanos."""
    if not psutil:
        return False
    killed = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['pid'] <= 4:
                continue
            for conn in proc.net_connections(kind='inet'):
                if conn.laddr and conn.laddr.port == port:
                    print(f"[*] Liberando puerto {port} ocupado por {proc.info['name']} (PID {proc.info['pid']})...")
                    proc.terminate()
                    proc.wait(timeout=2)
                    killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
    return killed

def check_and_prepare_ports(ports=(8001, 8002, 3000)):
    for port in ports:
        if is_port_in_use(port):
            print(f"[!] Puerto {port} ocupado. Verificando liberación automática...")
            release_port(port)
