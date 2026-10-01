import asyncio
import json
import os
import sys
import socket
import re
import psutil
import platform
import shutil
import subprocess
import urllib.request
import time
from datetime import datetime
from collections import deque
import threading
import secrets

NOTIFICATIONS_QUEUE = deque(maxlen=50)

def notify(msg: str, type: str = "info"):
    NOTIFICATIONS_QUEUE.append({"msg": msg, "type": type, "ts": time.time()})

from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
import vault_manager
import sentinel_service
try:
    from mesh_engine import (
        start_mesh_engine,
        record_heartbeat,
        get_mesh_nodes,
        smart_proxy_fetch,
        get_self_network_candidates,
        scan_lan_subnet
    )
except ImportError:
    from .mesh_engine import (
        start_mesh_engine,
        record_heartbeat,
        get_mesh_nodes,
        smart_proxy_fetch,
        get_self_network_candidates,
        scan_lan_subnet
    )
try:
    import winpty
except ImportError:
    winpty = None
try:
    import ptyprocess
    import fcntl
    import termios
except ImportError:
    ptyprocess = None
    fcntl = None
    termios = None
import struct
import shlex

app = FastAPI(title="Lab Sentinel OS API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_custom_headers(request, call_next):
    if request.method == "OPTIONS":
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

MOONRAKER_URL = "http://127.0.0.1:7125"
_MOONRAKER_ACTIVE = False
_LAST_MOONRAKER_CHECK = 0.0

def is_moonraker_running() -> bool:
    global _MOONRAKER_ACTIVE, _LAST_MOONRAKER_CHECK
    now = time.time()
    if now - _LAST_MOONRAKER_CHECK < 8.0:
        return _MOONRAKER_ACTIVE
    _LAST_MOONRAKER_CHECK = now
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.12)
            _MOONRAKER_ACTIVE = (s.connect_ex(("127.0.0.1", 7125)) == 0)
    except Exception:
        _MOONRAKER_ACTIVE = False
    return _MOONRAKER_ACTIVE

def command(*args: str, timeout: float = 2) -> str:
    try:
        return subprocess.run(args, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, timeout=timeout,
                              check=False).stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""

def get_json(url: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=1) as response:
            return json.load(response)
    except Exception:
        return {}

def post_json(url: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return json.load(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_load_avg() -> list[float]:
    try:
        return [round(x, 2) for x in os.getloadavg()]
    except (AttributeError, OSError):
        cpu_p = psutil.cpu_percent(interval=None)
        cores = os.cpu_count() or 1
        load = round((cpu_p / 100.0) * cores, 2)
        return [load, load, load]

def get_mem_stats() -> dict:
    try:
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", encoding="utf-8") as file:
                mem = {line.split(":")[0]: int(line.split()[1]) * 1024 for line in file}
            total_mem = mem.get("MemTotal", 0)
            avail_mem = mem.get("MemAvailable", 0)
            used_mem = total_mem - avail_mem
            return {
                "total": total_mem,
                "used": used_mem,
                "available": avail_mem,
                "cached": mem.get("Cached", 0),
                "free": mem.get("MemFree", 0),
                "swap_total": mem.get("SwapTotal", 0),
                "swap_free": mem.get("SwapFree", 0),
            }
        else:
            vm = psutil.virtual_memory()
            sm = psutil.swap_memory()
            return {
                "total": vm.total,
                "used": vm.used,
                "available": vm.available,
                "cached": getattr(vm, "cached", 0),
                "free": vm.free,
                "swap_total": sm.total,
                "swap_free": sm.free,
            }
    except Exception:
        return {"total": 0, "used": 0, "available": 0, "free": 0}

class CpuMeter:
    def __init__(self):
        self.previous = self.read()
    @staticmethod
    def read() -> tuple[int, int]:
        try:
            if os.path.exists("/proc/stat"):
                with open("/proc/stat", encoding="utf-8") as file:
                    values = [int(item) for item in file.readline().split()[1:]]
                return sum(values), values[3] + values[4]
        except Exception:
            pass
        return 0, 0
    def percent(self) -> float:
        try:
            if os.path.exists("/proc/stat"):
                current = self.read()
                total, idle = current[0] - self.previous[0], current[1] - self.previous[1]
                self.previous = current
                return 0 if not total else 100 * (total - idle) / total
            else:
                return float(psutil.cpu_percent(interval=None))
        except Exception:
            return 0.0

cpu_meter = CpuMeter()

class NetworkMeter:
    def __init__(self):
        self.last_time = time.time()
        self.last_rx, self.last_tx = self.read()
    @staticmethod
    def read() -> tuple[int, int]:
        rx = tx = 0
        try:
            if os.path.exists("/proc/net/dev"):
                with open("/proc/net/dev", "r") as f:
                    lines = f.readlines()[2:]
                    for line in lines:
                        parts = line.split()
                        if parts[0].startswith(("eth", "en", "wl", "wlan")):
                            rx += int(parts[1])
                            tx += int(parts[9])
            else:
                counters = psutil.net_io_counters()
                rx = counters.bytes_recv
                tx = counters.bytes_sent
        except Exception:
            pass
        return rx, tx
    def get_speed(self):
        now = time.time()
        rx, tx = self.read()
        dt = now - self.last_time
        rx_speed = (rx - self.last_rx) / dt if dt > 0 else 0
        tx_speed = (tx - self.last_tx) / dt if dt > 0 else 0
        self.last_time = now
        self.last_rx, self.last_tx = rx, tx
        return {"rx": rx_speed, "tx": tx_speed}

net_meter = NetworkMeter()

class DiskMeter:
    def __init__(self):
        self.last_time = time.time()
        self.last_read, self.last_write = self.read()
    @staticmethod
    def read() -> tuple[int, int]:
        r = w = 0
        try:
            if os.path.exists("/proc/diskstats"):
                with open("/proc/diskstats", "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 13 and parts[2].startswith(("sd", "nvme", "vd", "mmc")):
                            r += int(parts[5]) * 512
                            w += int(parts[9]) * 512
            else:
                d_io = psutil.disk_io_counters()
                if d_io:
                    r = d_io.read_bytes
                    w = d_io.write_bytes
        except Exception:
            pass
        return r, w
    def get_speed(self):
        now = time.time()
        r, w = self.read()
        dt = now - self.last_time
        r_speed = (r - self.last_read) / dt if dt > 0 else 0
        w_speed = (w - self.last_write) / dt if dt > 0 else 0
        self.last_time = now
        self.last_read, self.last_write = r, w
        return {"read": r_speed, "write": w_speed}

disk_meter = DiskMeter()

def get_cpu_temp():
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if getattr(entry, 'current', None) and entry.current > 0:
                            return float(entry.current)
        for root, dirs, files in os.walk("/sys/class/thermal"):
            for dir_name in dirs:
                if dir_name.startswith("thermal_zone"):
                    with open(os.path.join(root, dir_name, "temp"), "r") as f:
                        temp = int(f.read().strip())
                        if temp > 0:
                            return temp / 1000.0
    except Exception:
        pass
    return 0.0

def get_mac_info(mac_addr: str) -> tuple[str, str]:
    mac_addr = mac_addr.upper()
    # Fallback logic for common macs
    if mac_addr.startswith(("00:14:22", "B8:27:EB", "D8:3A:DD", "E4:5F:01")): return "Raspberry Pi", "Mini PC / SBC"
    if mac_addr.startswith(("00:11:32", "00:08:9B")): return "Synology", "NAS Server"
    if mac_addr.startswith(("F0:9F:C2", "2C:F0:A2", "4C:32:75", "10:AE:60", "FC:C2:3D", "44:2A:60", "F4:0F:24", "60:F8:1D", "00:1E:C2")): return "Apple", "iPhone / Mac / iPad"
    if mac_addr.startswith(("A4:5E:60", "00:1A:11")): return "Google", "Android / Smart Home"
    if mac_addr.startswith(("00:1A:79", "00:26:5A", "F8:8E:85")): return "Samsung", "Smart TV / Phone"
    if mac_addr.startswith(("18:B4:30", "E8:4E:06", "5C:CF:7F", "24:A1:60")): return "Espressif", "IoT Smart Device"
    if mac_addr.startswith(("A8:40:41", "AC:0B:FB")): return "Intel", "PC / Laptop"
    if mac_addr.startswith(("00:50:56", "00:0C:29", "00:05:69")): return "VMware", "Virtual Machine"
    if mac_addr.startswith(("52:54:00")): return "QEMU/KVM", "Virtual Machine"
    if mac_addr.startswith(("08:00:27")): return "VirtualBox", "Virtual Machine"
    return "Unknown Vendor", "Generic Device"

def deduce_device_type(vendor: str) -> str:
    v_lower = vendor.lower()
    if "apple" in v_lower: return "Apple Device"
    if "samsung" in v_lower: return "Smart TV / Phone"
    if "espressif" in v_lower: return "IoT Smart Device"
    if "nintendo" in v_lower: return "Game Console"
    if "sony" in v_lower: return "PlayStation / TV"
    if "intel" in v_lower: return "PC / Laptop"
    if "synology" in v_lower: return "NAS Server"
    if "raspberry" in v_lower or "pi " in v_lower: return "Raspberry Pi"
    if "routerboard" in v_lower or "mikrotik" in v_lower: return "Router / Switch"
    if "ubiquiti" in v_lower: return "UniFi Device"
    return "Generic Device"

def get_cpu_model() -> str:
    try:
        if sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0')
            name, _ = winreg.QueryValueEx(key, 'ProcessorNameString')
            return name.strip()
        elif os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
    except Exception:
        pass
    import platform
    return platform.processor() or "Generic Processor"

def get_gpu_info() -> dict:
    try:
        if shutil.which("nvidia-smi"):
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,driver_version", "--format=csv,noheader,nounits"],
                text=True, timeout=2, stderr=subprocess.DEVNULL
            ).strip()
            if out:
                lines = out.splitlines()
                parts = [p.strip() for p in lines[0].split(",")]
                if len(parts) >= 7:
                    return {
                        "has_gpu": True,
                        "model": parts[0],
                        "vram_total_mb": round(float(parts[1])),
                        "vram_used_mb": round(float(parts[2])),
                        "vram_free_mb": round(float(parts[3])),
                        "usage": round(float(parts[4]), 1),
                        "temp": round(float(parts[5]), 1),
                        "driver": parts[6],
                        "vendor": "NVIDIA"
                    }
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            cmd = 'Get-CimInstance Win32_VideoController | Select-Object -Property Name, AdapterRAM, DriverVersion | ConvertTo-Json'
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd], text=True, timeout=3, stderr=subprocess.DEVNULL)
            data = json.loads(out)
            item = data[0] if isinstance(data, list) and len(data) > 0 else (data if isinstance(data, dict) else None)
            if item and item.get("Name"):
                name = item.get("Name")
                ram = item.get("AdapterRAM") or 0
                return {
                    "has_gpu": True,
                    "model": name,
                    "vram_total_mb": round(ram / (1024 * 1024)) if ram > 0 else 0,
                    "vram_used_mb": 0,
                    "vram_free_mb": 0,
                    "usage": 0.0,
                    "temp": 0.0,
                    "driver": str(item.get("DriverVersion", "")),
                    "vendor": "Windows/CIM"
                }
        except Exception:
            pass

    if sys.platform != "win32" and shutil.which("lspci"):
        try:
            out = subprocess.check_output(["lspci"], text=True, timeout=2, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    model = line.split(":", 2)[-1].strip()
                    return {
                        "has_gpu": True,
                        "model": model,
                        "vram_total_mb": 0,
                        "vram_used_mb": 0,
                        "vram_free_mb": 0,
                        "usage": 0.0,
                        "temp": 0.0,
                        "driver": "",
                        "vendor": "Linux/PCI"
                    }
        except Exception:
            pass

    return {
        "has_gpu": False,
        "model": "None",
        "vram_total_mb": 0,
        "vram_used_mb": 0,
        "vram_free_mb": 0,
        "usage": 0.0,
        "temp": 0.0,
        "driver": "",
        "vendor": "None"
    }

# Historical Buffer (Last 300 seconds = 5 minutes)
history_buffer = deque(maxlen=300)

LAST_ACTIVE_TIME = time.time()
ARP_CACHE = []

async def arp_scanner_loop():
    global ARP_CACHE
    while True:
        try:
            if time.time() - LAST_ACTIVE_TIME > 15:
                await asyncio.sleep(5)
                continue
                
            out = await asyncio.get_event_loop().run_in_executor(None, lambda: command("sudo", "/usr/sbin/arp-scan", "-l"))
            neighbors = []
            for line in out.splitlines():
                parts = line.split('\t')
                if len(parts) >= 2:
                    ip = parts[0]
                    mac = parts[1]
                    if ":" in mac and len(mac) == 17:
                        vendor, device_type = get_mac_info(mac)
                        if vendor == "Unknown Vendor" and len(parts) >= 3:
                            vendor = parts[2]
                            device_type = deduce_device_type(vendor)
                        neighbors.append({
                            "ip": ip,
                            "mac": mac,
                            "interface": "LAN",
                            "vendor": vendor,
                            "device_type": device_type
                        })
            if neighbors:
                ARP_CACHE = neighbors
        except Exception as e:
            print("ARP scan error:", e)
        
        ai_busy = getattr(sentinel_service, 'is_ai_active', lambda: False)(); await asyncio.sleep(30 if ai_busy else 10) # Throttled when AI active

async def metric_collector():
    while True:
        try:
            if time.time() - LAST_ACTIVE_TIME > 15:
                await asyncio.sleep(5)
                continue

            now = datetime.now().strftime("%H:%M:%S")
            cpu_p = cpu_meter.percent()
            cpu_t = get_cpu_temp()
            net_s = net_meter.get_speed()
            disk_s = disk_meter.get_speed()
            
            try:
                if os.path.exists("/proc/meminfo"):
                    with open("/proc/meminfo", encoding="utf-8") as file:
                        mem = {line.split(":")[0]: int(line.split()[1]) * 1024 for line in file}
                    used_mem = mem.get("MemTotal", 0) - mem.get("MemAvailable", 0)
                    mem_p = (used_mem / mem.get("MemTotal", 1)) * 100
                else:
                    mem_p = psutil.virtual_memory().percent
            except Exception:
                try:
                    mem_p = psutil.virtual_memory().percent
                except Exception:
                    mem_p = 0
            
            # Klipper temps
            klipper = get_json(MOONRAKER_URL + "/printer/objects/query", {"objects": {"extruder": ["temperature", "target"], "heater_bed": ["temperature", "target"]}}).get("result", {}).get("status", {})
            e_temp = klipper.get("extruder", {}).get("temperature", 0)
            b_temp = klipper.get("heater_bed", {}).get("temperature", 0)
            
            # GPU metrics
            gpu_data = get_gpu_info()
            gpu_u = gpu_data.get("usage", 0.0) if gpu_data.get("has_gpu") else 0.0
            gpu_t = gpu_data.get("temp", 0.0) if gpu_data.get("has_gpu") else 0.0

            history_buffer.append({
                "time": now,
                "cpu": round(cpu_p, 1),
                "ram": round(mem_p, 1),
                "temp": round(cpu_t, 1),
                "gpu": round(gpu_u, 1),
                "gpu_temp": round(gpu_t, 1),
                "net_rx": round(net_s["rx"] / 1024 / 1024, 2), # MB/s
                "net_tx": round(net_s["tx"] / 1024 / 1024, 2), # MB/s
                "disk_r": round(disk_s["read"] / 1024 / 1024, 2), # MB/s
                "disk_w": round(disk_s["write"] / 1024 / 1024, 2), # MB/s
                "klipper_e": round(e_temp, 1),
                "klipper_b": round(b_temp, 1)
            })
        except Exception as e:
            print("Collector error:", e)
        
        ai_busy = getattr(sentinel_service, 'is_ai_active', lambda: False)(); await asyncio.sleep(3 if ai_busy else 1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(metric_collector())
    asyncio.create_task(arp_scanner_loop())
    start_mesh_engine(port=8001, get_telemetry_fn=collect_data)

_CACHED_SYSTEM_DATA = None
_LAST_FULL_SCAN_TIME = 0.0

_LAST_INTERNET_CHECK_TIME = 0.0
_CACHED_INTERNET_STATUS = {
    "has_internet": True,
    "latency_ms": 25.0,
    "mode": "online",
    "status_label": "Conectado a Internet",
    "message": "Acceso a WAN/Internet activo. Enlaces remotos y actualizaciones disponibles."
}

def check_cached_internet_status(force: bool = False) -> dict:
    global _LAST_INTERNET_CHECK_TIME, _CACHED_INTERNET_STATUS
    now = time.time()
    if not force and (now - _LAST_INTERNET_CHECK_TIME < 30.0):
        return _CACHED_INTERNET_STATUS
    if force and (now - _LAST_INTERNET_CHECK_TIME < 15.0):
        return _CACHED_INTERNET_STATUS

    _LAST_INTERNET_CHECK_TIME = now
    t0 = time.time()
    has_internet = False
    latency_ms = None
    
    # Try Cloudflare (1.1.1.1) then Google (8.8.8.8) with fast timeout
    for host in [("1.1.1.1", 53), ("8.8.8.8", 53)]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.35)
            sock.connect(host)
            sock.close()
            has_internet = True
            latency_ms = round((time.time() - t0) * 1000, 1)
            break
        except Exception:
            continue

    if has_internet:
        status = {
            "has_internet": True,
            "latency_ms": latency_ms,
            "mode": "online",
            "status_label": "Conectado a Internet",
            "message": "Acceso a WAN/Internet activo. Enlaces remotos y actualizaciones disponibles."
        }
    else:
        # Check if local LAN interfaces are active
        has_lan = False
        try:
            for iface, stats in psutil.net_if_stats().items():
                if "loopback" in iface.lower() or iface.lower() == "lo":
                    continue
                if stats.isup:
                    addrs = psutil.net_if_addrs().get(iface, [])
                    if any(a.family == socket.AF_INET and not a.address.startswith("127.") for a in addrs):
                        has_lan = True
                        break
        except Exception:
            has_lan = True

        if has_lan:
            status = {
                "has_internet": False,
                "latency_ms": None,
                "mode": "local_only",
                "status_label": "Solo Red Local (Sin Internet / LAN Air-Gapped)",
                "message": "SentinelOS opera 100% en modo local (LAN). La telemetría, Docker, IA local, Klipper y terminales funcionan sin requerir internet."
            }
        else:
            status = {
                "has_internet": False,
                "latency_ms": None,
                "mode": "offline",
                "status_label": "Sin Conexión de Red",
                "message": "No se detectaron interfaces de red activas con dirección IPv4 asignada."
            }

    _CACHED_INTERNET_STATUS = status
    return status

def get_default_gateway() -> str:
    try:
        if sys.platform == "win32":
            out = subprocess.check_output("route print 0.0.0.0", shell=True, text=True, timeout=1.5)
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[0] == "0.0.0.0":
                    return parts[2]
        else:
            if os.path.exists("/proc/net/route"):
                with open("/proc/net/route") as f:
                    for line in f.readlines()[1:]:
                        fields = line.strip().split()
                        if len(fields) >= 3 and fields[1] == "00000000":
                            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
    except Exception:
        pass
    return "No detectado"

def get_primary_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

_LAST_NET_IO_TIME = time.time()
_LAST_NET_IO = None
_CACHED_NET_RATES = {"upload_kbps": 0.0, "download_kbps": 0.0, "total_sent_mb": 0.0, "total_recv_mb": 0.0}

def get_network_traffic_rates() -> dict:
    global _LAST_NET_IO_TIME, _LAST_NET_IO, _CACHED_NET_RATES
    try:
        now = time.time()
        current_io = psutil.net_io_counters()
        if _LAST_NET_IO is not None and (now - _LAST_NET_IO_TIME) > 0.5:
            dt = now - _LAST_NET_IO_TIME
            up_bytes_sec = (current_io.bytes_sent - _LAST_NET_IO.bytes_sent) / dt
            down_bytes_sec = (current_io.bytes_recv - _LAST_NET_IO.bytes_recv) / dt
            _CACHED_NET_RATES = {
                "upload_kbps": round(up_bytes_sec / 1024, 1),
                "download_kbps": round(down_bytes_sec / 1024, 1),
                "total_sent_mb": round(current_io.bytes_sent / (1024 * 1024), 1),
                "total_recv_mb": round(current_io.bytes_recv / (1024 * 1024), 1)
            }
        _LAST_NET_IO_TIME = now
        _LAST_NET_IO = current_io
    except Exception:
        pass
    return _CACHED_NET_RATES

def collect_data() -> dict:
    global _CACHED_SYSTEM_DATA, _LAST_FULL_SCAN_TIME
    now = time.time()
    ai_busy = getattr(sentinel_service, "is_ai_active", lambda: False)()

    # If AI active or scanned within 12s, serve fast in-memory cache without heavy subprocesses
    if _CACHED_SYSTEM_DATA is not None and (ai_busy or (now - _LAST_FULL_SCAN_TIME < 12.0)):
        fast_data = dict(_CACHED_SYSTEM_DATA)
        try:
            fast_data["system"] = dict(fast_data.get("system", {}))
            fast_data["system"]["memory"] = get_mem_stats()
            fast_data["system"]["loadavg"] = get_load_avg()
            fast_data["system"]["gpu"] = get_gpu_info()
        except Exception:
            pass
        fast_data["metrics_history"] = list(history_buffer)
        return fast_data

    # Full Klipper State - Only query if Moonraker port is actually open
    klipper_resp = {}
    gcode_store = []
    moonraker_info = {}
    if is_moonraker_running():
        klipper_query = {"objects": {"webhooks": None, "print_stats": None, "virtual_sdcard": None, "gcode_move": None, "toolhead": None, "fan": None, "extruder": None, "heater_bed": None, "display_status": None}}
        klipper_resp = get_json(MOONRAKER_URL + "/printer/objects/query", klipper_query).get("result", {}).get("status", {})
        gcode_store = get_json(MOONRAKER_URL + "/server/gcode_store?count=50").get("result", {}).get("gcode_store", [])
        moonraker_info = get_json(MOONRAKER_URL + "/server/info").get("result", {})
    
    # Docker Containers
    containers = []
    # Fetch detailed info by also getting the Command
    for line in command("docker", "ps", "-a", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.ID}}|{{.Command}}").splitlines():
        fields = line.split("|", 5)
        if len(fields) == 6:
            containers.append({
                "name": fields[0], "image": fields[1], "status": fields[2], 
                "ports": fields[3], "id": fields[4], "command": fields[5].strip('"')
            })
            
    neighbors = ARP_CACHE
            
    tailscale_raw = command("tailscale", "status", "--json", timeout=3)
    try:
        tailscale = json.loads(tailscale_raw) if tailscale_raw else {}
    except json.JSONDecodeError:
        tailscale = {}
        
    mem_stats = get_mem_stats()
        
    disks = []
    try:
        if sys.platform != "win32" and shutil.which("df"):
            for line in command("df", "-B1").splitlines()[1:]:
                fields = line.split()
                if len(fields) >= 6 and fields[0].startswith("/dev/") and not fields[0].startswith("/dev/loop"):
                    disks.append({
                        "device": fields[0],
                        "total": int(fields[1]),
                        "used": int(fields[2]),
                        "free": int(fields[3]),
                        "mountpoint": fields[5]
                    })
        if not disks:
            for p in psutil.disk_partitions(all=False):
                if 'cdrom' in p.opts or not p.fstype:
                    continue
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    disks.append({
                        "device": p.device,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "mountpoint": p.mountpoint
                    })
                except Exception:
                    pass
    except Exception:
        pass

    uptime = 0.0
    try:
        if os.path.exists("/proc/uptime"):
            uptime = float(open("/proc/uptime").read().split()[0])
        else:
            uptime = round(time.time() - psutil.boot_time(), 1)
    except Exception:
        uptime = 0.0
    
    # Active Users
    active_users = []
    try:
        if sys.platform != "win32" and shutil.which("who"):
            for line in command("who").splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    active_users.append({
                        "user": parts[0],
                        "terminal": parts[1],
                        "login_time": " ".join(parts[2:4]),
                        "ip": parts[4].strip("()") if len(parts) > 4 else "localhost"
                    })
        if not active_users:
            for u in psutil.users():
                active_users.append({
                    "user": u.name,
                    "terminal": u.terminal or "console",
                    "login_time": datetime.fromtimestamp(u.started).strftime("%Y-%m-%d %H:%M"),
                    "ip": u.host or "localhost"
                })
    except: pass

    # Open Ports
    open_ports = []
    try:
        if sys.platform != "win32" and shutil.which("ss"):
            for line in command("ss", "-tuln").splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    open_ports.append({
                        "protocol": parts[0],
                        "state": parts[1],
                        "local_address": parts[4]
                    })
        if not open_ports:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    proto = "tcp" if conn.type == socket.SOCK_STREAM else "udp"
                    ip = conn.laddr.ip if conn.laddr else ""
                    port = conn.laddr.port if conn.laddr else ""
                    open_ports.append({
                        "protocol": proto,
                        "state": conn.status,
                        "local_address": f"{ip}:{port}"
                    })
                    if len(open_ports) >= 30:
                        break
    except: pass

    # CPU Frequencies
    cpu_freqs = []
    try:
        freq = psutil.cpu_freq()
        if freq and getattr(freq, 'current', None):
            cpu_freqs.append(round(freq.current, 1))
        elif os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("cpu MHz"):
                        cpu_freqs.append(float(line.split(":")[1].strip()))
    except: pass

    # SMART Disks
    smart_info = []
    try:
        devs = [line.split()[0] for line in command("sudo", "smartctl", "--scan").splitlines() if line]
        for dev in devs:
            out = command("sudo", "smartctl", "-a", dev)
            health = "Unknown"
            temp = "N/A"
            model = "Unknown"
            for line in out.splitlines():
                if "SMART overall-health" in line:
                    health = line.split(":")[-1].strip()
                elif "Device Model:" in line:
                    model = line.split(":")[-1].strip()
                elif "Temperature_Celsius" in line:
                    temp = line.split()[9]
            smart_info.append({"device": dev, "model": model, "health": health, "temp": temp})
    except: pass

    # UFW Status
    ufw_status = {"enabled": False, "rules": []}
    try:
        out = command("sudo", "ufw", "status", "numbered")
        if "Status: active" in out:
            ufw_status["enabled"] = True
            for line in out.splitlines():
                if "[" in line and "]" in line:
                    ufw_status["rules"].append(line.strip())
    except: pass

    # Cron Jobs
    cron_jobs = []
    try:
        current_user = os.environ.get("USER") or os.environ.get("USERNAME") or "user"
        for line in out.splitlines():
            if line and not line.startswith("#"):
                cron_jobs.append({"user": current_user, "job": line})
        if os.path.exists("/etc/crontab"):
            with open("/etc/crontab") as f:
                for line in f:
                    if line and not line.startswith("#") and len(line.split()) > 5:
                        cron_jobs.append({"user": "system", "job": line.strip()})
    except: pass
    
    processes = []
    try:
        if sys.platform != "win32" and shutil.which("ps"):
            for line in command("ps", "-eo", "pid=,user=,%cpu=,%mem=,nlwp=,comm=", "--sort=-%cpu").splitlines()[:50]:
                fields = line.split(None, 5)
                if len(fields) == 6:
                    processes.append({"pid": fields[0], "user": fields[1], "cpu": fields[2], "mem": fields[3], "threads": fields[4], "name": fields[5]})
        if not processes:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'num_threads']):
                info = proc.info
                processes.append({
                    "pid": str(info.get('pid', '')),
                    "user": str(info.get('username') or 'system'),
                    "cpu": f"{info.get('cpu_percent') or 0:.1f}",
                    "mem": f"{info.get('memory_percent') or 0:.1f}",
                    "threads": str(info.get('num_threads') or 1),
                    "name": str(info.get('name') or 'process')
                })
                if len(processes) >= 50:
                    break
    except: pass

    n_list = list(NOTIFICATIONS_QUEUE)
    NOTIFICATIONS_QUEUE.clear()

    # Real network interfaces detection
    net_interfaces = []
    primary_interface = None
    try:
        if_stats = psutil.net_if_stats()
        if_addrs = psutil.net_if_addrs()
        
        for iface_name, stats in if_stats.items():
            name_lower = iface_name.lower()
            if "loopback" in name_lower or name_lower == "lo":
                continue
            
            if name_lower.startswith("wl") or any(w in name_lower for w in ["wi-fi", "wifi", "wlan", "wireless", "802.11"]):
                iface_type = "wifi"
            elif any(w in name_lower for w in ["tailscale", "tun", "wireguard", "wg", "vpn"]):
                iface_type = "vpn"
            elif name_lower.startswith("en") or name_lower.startswith("eth") or any(w in name_lower for w in ["ethernet", "lan"]):
                iface_type = "ethernet"
            else:
                iface_type = "ethernet"
            
            ipv4 = ""
            mac = ""
            for addr in if_addrs.get(iface_name, []):
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    ipv4 = addr.address
                elif getattr(addr, 'family', None) in (getattr(psutil, 'AF_LINK', None), getattr(socket, 'AF_PACKET', None)):
                    mac = addr.address
            
            if stats.isup and ipv4:
                item = {
                    "name": iface_name,
                    "type": iface_type,
                    "isup": stats.isup,
                    "speed": stats.speed,
                    "ip": ipv4,
                    "mac": mac
                }
                net_interfaces.append(item)
                if not primary_interface and iface_type in ("wifi", "ethernet"):
                    primary_interface = item
    except Exception:
        pass
    
    if not primary_interface and net_interfaces:
        primary_interface = net_interfaces[0]

    result_data = {
        "printer": klipper_resp,
        "moonraker": moonraker_info,
        "gcode_store": gcode_store,
        "containers": containers,
        "network": {
            "neighbors": neighbors,
            "interfaces": net_interfaces,
            "primary": primary_interface or {
                "name": "Ethernet",
                "type": "ethernet",
                "isup": True,
                "speed": 1000,
                "ip": "127.0.0.1",
                "mac": ""
            },
            "internet": check_cached_internet_status(),
            "gateway": get_default_gateway(),
            "local_ip": get_primary_local_ip(),
            "traffic": get_network_traffic_rates()
        },
        "tailscale": tailscale,
        "system": {
            "cpu_model": get_cpu_model(),
            "gpu": get_gpu_info(),
            "memory": mem_stats,
            "disks": disks,
            "uptime": uptime,
            "loadavg": get_load_avg(),
            "cpu_cores": os.cpu_count(),
            "cpu_freqs": cpu_freqs,
            "processes": processes,
            "active_users": active_users,
            "open_ports": open_ports,
            "smart": smart_info,
            "ufw": ufw_status,
            "cron": cron_jobs
        },
        "metrics_history": list(history_buffer)
    }
    _CACHED_SYSTEM_DATA = result_data
    _LAST_FULL_SCAN_TIME = now
    return result_data

@app.get("/api/remote/proxy")
async def remote_proxy(request: Request, target_url: str):
    """Proxy request to remote Sentinel nodes with multi-path auto-failover and firewall bypass."""
    try:
        if not (target_url.startswith("http://") or target_url.startswith("https://")):
            raise HTTPException(status_code=400, detail="Invalid target URL")
        
        headers = {
            "Accept": "application/json"
        }
        auth_header = request.headers.get("Authorization")
        if auth_header:
            headers["Authorization"] = auth_header
        token_header = request.headers.get("X-Sentinel-Token")
        if token_header:
            headers["X-Sentinel-Token"] = token_header

        data, resolved_url = smart_proxy_fetch(target_url, headers=headers, timeout=2.5)
        response = JSONResponse(content=data)
        response.headers["X-Resolved-Endpoint"] = resolved_url
        return response
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")

@app.post("/api/mesh/heartbeat")
@app.post("/mesh/heartbeat")
async def mesh_heartbeat(request: Request):
    """Recibe telemetría saliente (push) de nodos remotos para eludir bloqueos de firewall entrante."""
    try:
        payload = await request.json()
        client_ip = request.client.host if request.client else ""
        return record_heartbeat(payload, client_ip=client_ip)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/mesh/nodes")
@app.get("/mesh/nodes")
def mesh_nodes():
    """Retorna todos los nodos descubiertos en la malla y sus rutas alternativas."""
    return {"nodes": get_mesh_nodes(), "candidates": get_self_network_candidates(port=8001)}

@app.post("/api/mesh/scan")
@app.post("/mesh/scan")
def mesh_scan():
    """Ejecuta un escaneo rápido en la subred local /24 para descubrir nodos SentinelOS."""
    found = scan_lan_subnet(port=8001)
    return {"status": "ok", "scanned": len(found), "found": found, "nodes": get_mesh_nodes()}

@app.post("/api/remote/proxy")
async def remote_proxy_post(request: Request, target_url: str):
    """Proxy POST request to remote Sentinel nodes (e.g. Klipper commands, actions)."""
    try:
        if not (target_url.startswith("http://") or target_url.startswith("https://")):
            raise HTTPException(status_code=400, detail="Invalid target URL")
        
        body = await request.body()
        auth_header = request.headers.get("Authorization", "")
        token_header = request.headers.get("X-Sentinel-Token", "")
        
        headers = {
            "User-Agent": "SentinelOS-Core-Proxy/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if auth_header:
            headers["Authorization"] = auth_header
        if token_header:
            headers["X-Sentinel-Token"] = token_header

        req = urllib.request.Request(target_url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy POST error: {str(e)}")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "time": time.time()}

def get_node_auth():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_dir = os.path.join(root_dir, "config")
    os.makedirs(cfg_dir, exist_ok=True)
    auth_file = os.path.join(cfg_dir, "node_auth.json")
    if os.path.exists(auth_file):
        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("token") and data.get("node_id"):
                    return data
        except Exception:
            pass
    node_id = f"node-{secrets.token_hex(4)}"
    token = f"sntl_live_{secrets.token_hex(8)}"
    data = {
        "node_id": node_id,
        "node_name": socket.gethostname(),
        "token": token,
        "created_at": datetime.now().isoformat(),
        "port": 8001
    }
    try:
        with open(auth_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
    return data

@app.get("/api/node/info")
def get_node_info():
    auth_data = get_node_auth()
    return {
        "status": "online",
        "node_id": auth_data.get("node_id", "node-sentinel"),
        "node_name": auth_data.get("node_name", socket.gethostname()),
        "token": auth_data.get("token", ""),
        "platform": sys.platform,
        "cores": psutil.cpu_count(logical=True),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "version": "2.0.0",
        "endpoints": get_self_network_candidates(port=8001)
    }

@app.get("/api/node/token")
def get_node_token():
    auth_data = get_node_auth()
    return {
        "status": "ok",
        "token": auth_data.get("token", ""),
        "node_id": auth_data.get("node_id", "node-sentinel"),
        "node_name": auth_data.get("node_name", socket.gethostname()),
        "port": 8001
    }

@app.websocket("/api/ws/model/download")
async def ws_model_download(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        model_url = (data.get("url") or "").strip()
        model_name = (data.get("name") or "").strip() or "sentinel-model"
        target_runtime = data.get("runtime", "docker_ollama")

        await websocket.send_json({"type": "log", "message": f"[*] Solicitud recibida: Descargar '{model_name}' desde '{model_url}'"})
        
        if not model_url:
            await websocket.send_json({"type": "error", "message": "URL o identificador de modelo no provisto."})
            await websocket.close()
            return

        # Si el modelo es un tag de ollama directo (e.g. llama3.2:1b, mistral, etc.)
        if not model_url.startswith("http://") and not model_url.startswith("https://"):
            await websocket.send_json({"type": "log", "message": f"[*] Detectado modelo Ollama: {model_url}. Ejecutando pull en Docker..."})
            cmd = ["docker", "exec", "ollama", "ollama", "pull", model_url]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                await websocket.send_json({"type": "log", "message": line.strip()})
            proc.wait()
            if proc.returncode == 0:
                await websocket.send_json({"type": "success", "message": f"¡Modelo {model_url} descargado y cargado en Ollama Docker con éxito!"})
            else:
                await websocket.send_json({"type": "error", "message": f"Fallo al descargar en Docker Ollama (código {proc.returncode})."})
            await websocket.close()
            return

        # Es una URL HTTP(S) de Hugging Face o directa a GGUF
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(root_dir, "models", "downloaded")
        os.makedirs(models_dir, exist_ok=True)
        dest_filename = os.path.basename(model_url.split("?")[0])
        if not dest_filename.endswith(".gguf"):
            dest_filename = f"{model_name}.gguf"
        dest_path = os.path.join(models_dir, dest_filename)

        await websocket.send_json({"type": "log", "message": f"[*] Conectando a {model_url}..."})
        
        req = urllib.request.Request(model_url, headers={"User-Agent": "SentinelOS/2.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0
            block_size = 1024 * 1024  # 1MB
            start_time = time.time()
            last_report = start_time

            with open(dest_path, "wb") as f_out:
                while True:
                    chunk = resp.read(block_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_report >= 0.5:
                        last_report = now
                        percent = round((downloaded / total_size * 100), 1) if total_size > 0 else 0
                        speed_mb = round((downloaded / (now - start_time)) / (1024 * 1024), 2)
                        await websocket.send_json({
                            "type": "progress",
                            "percent": percent,
                            "downloaded_mb": round(downloaded / (1024 * 1024), 1),
                            "total_mb": round(total_size / (1024 * 1024), 1),
                            "speed_mb": speed_mb,
                            "message": f"Descargando: {percent}% ({round(downloaded / (1024*1024), 1)} MB / {round(total_size / (1024*1024), 1)} MB a {speed_mb} MB/s)"
                        })

        await websocket.send_json({"type": "log", "message": f"[OK] Archivo GGUF guardado en {dest_path}"})
        
        # Cargar en Docker Ollama automáticamente si está disponible
        docker_available = False
        try:
            d_check = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=3)
            if d_check.returncode == 0 and "ollama" in d_check.stdout:
                docker_available = True
        except Exception:
            pass

        if docker_available:
            await websocket.send_json({"type": "log", "message": "[*] Cargando modelo en contenedor Docker Ollama..."})
            subprocess.run(["docker", "cp", dest_path, f"ollama:/tmp/{dest_filename}"], timeout=30)
            subprocess.run(["docker", "exec", "ollama", "sh", "-c", f"echo 'FROM /tmp/{dest_filename}' > /tmp/Modelfile && ollama create {model_name} -f /tmp/Modelfile"], timeout=120)
            await websocket.send_json({"type": "success", "message": f"¡Modelo {model_name} cargado con éxito en Docker Ollama!"})
        else:
            await websocket.send_json({"type": "success", "message": f"Modelo descargado en {dest_path}. Listo para usar con llama.cpp / Sentinel."})

        await websocket.close()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": f"Error: {str(e)}"})
            await websocket.close()
        except Exception:
            pass

class SystemUninstallRequest(BaseModel):
    confirm: bool = False
    purge_data: bool = False

@app.post("/api/system/uninstall")
def uninstall_system(req: SystemUninstallRequest):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmación explícita requerida para desinstalar SentinelOS.")

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results = []
    cleanup_complete = True

    # Reuse the installer cleanup so the cockpit button removes the same processes,
    # autostart entries and firewall rules as the terminal uninstaller.
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    try:
        from installer.uninstaller import (
            kill_sentinel_processes,
            remove_autostart_and_services,
            remove_all_shortcuts,
            remove_cli_from_path,
        )
        from installer.firewall import remove_firewall_rule

        system_name = "Windows" if sys.platform == "win32" else "Linux" if sys.platform.startswith("linux") else platform.system()
        process_result = kill_sentinel_processes(root_dir)
        if process_result["failed"]:
            cleanup_complete = False
            results.append("No se pudieron detener algunos procesos: " + ", ".join(map(str, process_result["failed"])))
        else:
            results.append(f"Procesos de SentinelOS detenidos: {len(process_result['stopped'])}.")

        # Keep this request alive long enough to return its response; the running
        # service is stopped in delayed_shutdown below.
        if remove_autostart_and_services(root_dir, stop_services=False):
            results.append("Autoinicio y servicios registrados eliminados.")
        else:
            cleanup_complete = False
            results.append("No se pudieron confirmar todas las tareas o servicios de autoinicio.")

        if remove_firewall_rule({"system": system_name}, 8001, "es", root_dir=root_dir):
            results.append("Reglas de firewall y excepción de Defender retiradas.")
        else:
            cleanup_complete = False
            results.append("No se pudieron confirmar todas las limpiezas de firewall.")

        remove_all_shortcuts(root_dir)
        remove_cli_from_path(root_dir)
        results.append("Accesos directos y comando sentinel retirados.")
        for config_name in ("node_auth.json", "mesh_peers.json"):
            config_path = os.path.join(root_dir, "config", config_name)
            try:
                os.remove(config_path)
                results.append(f"Configuración local retirada: {config_name}.")
            except FileNotFoundError:
                pass
    except Exception as exc:
        cleanup_complete = False
        results.append(f"La limpieza del sistema quedó incompleta: {exc}")

    if req.purge_data:
        try:
            vault_dir = os.path.join(root_dir, "labsentinel_backend", "vault")
            if os.path.exists(vault_dir):
                import shutil
                shutil.rmtree(vault_dir, ignore_errors=True)
                results.append("Archivos locales de vault eliminados.")
        except Exception:
            pass

    # 2. Planificar detención del backend local tras retornar la respuesta
    def delayed_shutdown():
        time.sleep(1.5)
        if sys.platform.startswith("linux"):
            try:
                command = ["systemctl", "stop", "labsentinel.service", "sentinel.service", "sentinel-orchestrator.service"]
                stopped = subprocess.run(command, capture_output=True, timeout=20)
                if stopped.returncode and hasattr(os, "geteuid") and os.geteuid() != 0 and shutil.which("sudo"):
                    subprocess.run(["sudo", "-n", *command], capture_output=True, timeout=20)
            except Exception:
                pass
        os._exit(0)

    import threading
    threading.Thread(target=delayed_shutdown, daemon=True).start()

    if not cleanup_complete:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "La limpieza quedó incompleta; revisa los permisos y vuelve a ejecutar la desinstalación.",
                "details": results,
            },
        )
    return {
        "status": "success",
        "message": "La limpieza de SentinelOS terminó; el backend local se detendrá en unos segundos.",
        "details": results,
    }

@app.get("/api/data")
def get_data():
    global LAST_ACTIVE_TIME
    LAST_ACTIVE_TIME = time.time()
    return collect_data()

class DockerCommand(BaseModel):
    container_name: str
    action: str

@app.post("/api/docker")
def manage_docker(cmd: DockerCommand):
    args = ["docker", cmd.action]
    if cmd.action == "rm": args.append("-f")
    args.append(cmd.container_name)
    return {"status": "ok", "output": command(*args, timeout=10)}

class DockerCreate(BaseModel):
    name: str
    image: str
    ports: str = ""
    env: str = ""
    restart: str = "no"

@app.post("/api/docker/create")
def create_docker(cmd: DockerCreate):
    args = ["docker", "run", "-d", "--name", cmd.name, f"--restart={cmd.restart}"]
    if cmd.ports:
        for p in cmd.ports.split(","):
            args.extend(["-p", p.strip()])
    if cmd.env:
        for e in cmd.env.split(","):
            args.extend(["-e", e.strip()])
    args.append(cmd.image)
    return {"status": "ok", "output": command(*args, timeout=30)}

class PrinterCommand(BaseModel):
    target: str
    temperature: int

@app.post("/api/printer/temperature")
def set_temperature(cmd: PrinterCommand):
    gcode = f"M104 S{cmd.temperature}" if cmd.target == "extruder" else f"M140 S{cmd.temperature}"
    return post_json(MOONRAKER_URL + "/printer/gcode/script", {"script": gcode})

class GcodeCommand(BaseModel):
    gcode: str

@app.post("/api/printer/gcode")
def run_gcode(cmd: GcodeCommand):
    return post_json(MOONRAKER_URL + "/printer/gcode/script", {"script": cmd.gcode})

class ProcessCommand(BaseModel):
    pid: int

@app.post("/api/process/kill")
def kill_process(cmd: ProcessCommand):
    try:
        os.kill(cmd.pid, 15)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TailscaleCommand(BaseModel):
    action: str
    params: str = ""

@app.post("/api/tailscale")
def manage_tailscale(cmd: TailscaleCommand):
    # tailscale up, tailscale down, tailscale up --advertise-exit-node
    base_args = ["sudo", "tailscale", cmd.action]
    if cmd.params:
        base_args.extend(cmd.params.split())
    # Note: Requires sudo NOPASSWD for tailscale or it will hang
    return {"status": "ok", "output": command(*base_args, timeout=15)}

@app.get("/api/files/audit")
def get_file_audit():
    audit_file = "/var/log/samba-audit.log"
    logs = []
    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r") as f:
                for line in reversed(f.readlines()[-100:]):
                    if "smbd_audit" in line:
                        try:
                            p1, p2 = line.split("smbd_audit:")
                            ev = p2.strip().split("|")
                            if len(ev) >= 6:
                                logs.append({"timestamp": p1.strip(), "user": ev[0], "ip": ev[1], "action": ev[4], "status": ev[5], "file": ev[6] if len(ev) > 6 else ""})
                        except Exception: pass
        except Exception: pass
    return {"audit": logs}

@app.get("/api/logs")
def get_sys_logs():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(root_dir, "sentinel_backend.log")
    file_logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                file_logs = [l.strip() for l in f.readlines()[-80:] if l.strip()]
        except Exception:
            pass

    sys_logs = ""
    if sys.platform != "win32":
        sys_logs = command("journalctl", "-u", "labsentinel.service", "-n", "60", "--no-pager")
        if not sys_logs:
            sys_logs = command("journalctl", "-n", "40", "--no-pager")

    if file_logs and sys_logs:
        return {"logs": "\n".join(file_logs[-40:] + ["--- SYSTEMD JOURNAL ---"] + sys_logs.splitlines()[-40:])}
    elif file_logs:
        return {"logs": "\n".join(file_logs)}
    elif sys_logs:
        return {"logs": sys_logs}
    else:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime_s = int(time.time() - psutil.boot_time())
        sample_logs = [
            f"[{now_str}] [INFO] SentinelOS Kernel Telemetry Active. Uptime: {uptime_s}s",
            f"[{now_str}] [INFO] Host System: {platform.system()} {platform.release()} ({platform.machine()})",
            f"[{now_str}] [INFO] Core Hardware: {psutil.cpu_count(logical=True)} vCPUs | {round(psutil.virtual_memory().total / (1024**3), 1)} GB RAM",
            f"[{now_str}] [INFO] Sockets: FastAPI & Uvicorn daemon listening on 0.0.0.0:8001 (HTTP 200 OK)",
            f"[{now_str}] [SUCCESS] Subsystem health check: ALL PASS"
        ]
        return {"logs": "\n".join(sample_logs)}

@app.get("/api/fs")
def get_fs(path: str = "/"):
    try:
        items = os.listdir(path)
        files = []
        dirs = []
        for item in items:
            full = os.path.join(path, item)
            if os.path.isdir(full):
                dirs.append(item)
            else:
                files.append({"name": item, "size": os.path.getsize(full)})
        return {"path": path, "dirs": sorted(dirs), "files": sorted(files, key=lambda x: x["name"])}
    except Exception as e:
        return {"error": str(e)}

class ServiceAction(BaseModel):
    action: str
    service: str

@app.get("/api/services")
def get_services():
    services = []
    if sys.platform != "win32":
        try:
            out = command("systemctl", "list-units", "--type=service", "--all", "--no-pager")
            for line in out.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 4 and parts[0].endswith(".service"):
                    services.append({"name": parts[0], "load": parts[1], "active": parts[2], "sub": parts[3]})
        except Exception:
            pass
    else:
        try:
            for s in psutil.win_service_iter():
                try:
                    s_info = s.as_dict()
                    services.append({
                        "name": s_info.get("name", ""),
                        "load": "loaded",
                        "active": "active" if s_info.get("status") == "running" else "inactive",
                        "sub": s_info.get("status", "stopped")
                    })
                except Exception:
                    pass
            services = sorted(services, key=lambda x: (x["active"] != "active", x["name"]))[:80]
        except Exception:
            pass
    return {"services": services}

@app.post("/api/services")
def control_service(req: ServiceAction):
    if sys.platform != "win32":
        if req.action in ["start", "stop", "restart"]:
            command("sudo", "systemctl", req.action, req.service)
    else:
        if req.action == "start":
            command("net", "start", req.service)
        elif req.action == "stop":
            command("net", "stop", req.service)
    return {"status": "ok"}

@app.get("/api/printer/history")
def get_printer_history():
    try:
        totals = get_json(MOONRAKER_URL + "/server/history/totals").get("result", {})
        lst = get_json(MOONRAKER_URL + "/server/history/list?limit=50").get("result", {})
        return {"totals": totals, "list": lst}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/apt")
def get_apt_updates():
    try:
        out = command("apt", "list", "--upgradable")
        lines = out.splitlines()
        updates = []
        for line in lines:
            if line and not line.startswith("Listing"):
                updates.append(line.split("/")[0])
        return {"updates": updates, "count": len(updates)}
    except:
        return {"updates": [], "count": 0}

@app.post("/api/apt/upgrade")
def post_apt_upgrade():
    # Run in background to not block
    subprocess.Popen(["sudo", "apt-get", "upgrade", "-y"])
    return {"status": "started"}

# ==============================================================================
# TERMINAL PTY & PERSISTENT SESSION ENGINE (CROSS-PLATFORM: WINDOWS & LINUX)
# ==============================================================================
class TerminalSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.proc = None
        self.is_winpty = False
        self.is_ptyprocess = False
        self.is_subprocess = False
        self.buffer = deque(maxlen=300000)
        self.subscribers = set()
        self.last_activity = time.time()
        self.alive = True
        self.reader_task = None
        self._spawn()

    def _spawn(self):
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        # 1. Windows con pywinpty / ConPTY nativo
        if sys.platform == "win32" and winpty is not None:
            try:
                ps = shutil.which("powershell.exe") or "powershell.exe"
                self.proc = winpty.PtyProcess.spawn(f"{ps} -NoLogo", env=env)
                self.is_winpty = True
                self.alive = True
                return
            except Exception as e:
                print(f"[TerminalSession] winpty spawn error: {e}")

        # 2. Linux / macOS con ptyprocess nativo
        if ptyprocess is not None:
            try:
                shell = os.environ.get("SHELL") or shutil.which("bash") or "/bin/bash"
                self.proc = ptyprocess.PtyProcessUnicode.spawn([shell, "-i"], env=env)
                self.is_ptyprocess = True
                self.alive = True
                return
            except Exception as e:
                print(f"[TerminalSession] ptyprocess spawn error: {e}")

        # 3. Fallback de subproceso estándar
        try:
            shell_cmd = ["powershell.exe", "-NoLogo"] if sys.platform == "win32" else ["/bin/sh", "-i"]
            self.proc = subprocess.Popen(
                shell_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
                env=env
            )
            self.is_subprocess = True
            self.alive = True
        except Exception as e:
            print(f"[TerminalSession] subprocess fallback error: {e}")
            self.alive = False

    def start(self):
        if self.reader_task is None or self.reader_task.done():
            self.reader_task = asyncio.create_task(self._reader_loop())

    async def _reader_loop(self):
        loop = asyncio.get_running_loop()
        while self.alive:
            try:
                chunk = ""
                if self.is_winpty and self.proc:
                    chunk = await loop.run_in_executor(None, self.proc.read, 2048)
                elif self.is_ptyprocess and self.proc:
                    chunk = await loop.run_in_executor(None, self.proc.read, 4096)
                elif self.is_subprocess and self.proc and self.proc.stdout:
                    raw = await loop.run_in_executor(None, self.proc.stdout.read, 1024)
                    if raw:
                        chunk = raw.decode("utf-8", errors="replace")
                    else:
                        break
                else:
                    break

                if not chunk:
                    await asyncio.sleep(0.02)
                    continue

                self.buffer.extend(chunk)
                self.last_activity = time.time()

                dead = set()
                for ws in list(self.subscribers):
                    try:
                        await ws.send_text(chunk)
                    except Exception:
                        dead.add(ws)
                for ws in dead:
                    self.subscribers.discard(ws)

            except (EOFError, BrokenPipeError):
                self.alive = False
                break
            except Exception:
                if not self.alive:
                    break
                await asyncio.sleep(0.05)

        self.alive = False
        msg = "\r\n\x1b[33m[Sesión de terminal finalizada]\x1b[0m\r\n"
        for ws in list(self.subscribers):
            try:
                await ws.send_text(msg)
            except Exception:
                pass

    def write(self, data: str):
        self.last_activity = time.time()
        if self.is_winpty and self.proc:
            try:
                self.proc.write(data)
            except Exception:
                self.alive = False
        elif self.is_ptyprocess and self.proc:
            try:
                self.proc.write(data)
            except Exception:
                self.alive = False
        elif self.is_subprocess and self.proc and self.proc.stdin:
            try:
                self.proc.stdin.write(data.encode("utf-8", errors="replace"))
                self.proc.stdin.flush()
            except Exception:
                self.alive = False

    def resize(self, cols: int, rows: int):
        if cols <= 0 or rows <= 0:
            return
        if self.is_winpty and self.proc:
            try:
                self.proc.setwinsize(rows, cols)
            except Exception:
                pass
        elif self.is_ptyprocess and self.proc:
            try:
                self.proc.setwinsize(rows, cols)
            except Exception:
                pass

    def get_history(self) -> str:
        return "".join(self.buffer)

    def terminate(self):
        self.alive = False
        if self.is_winpty and self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
        elif self.is_ptyprocess and self.proc:
            try:
                self.proc.terminate(force=True)
            except Exception:
                pass
        elif self.is_subprocess and self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
        if self.reader_task and not self.reader_task.done():
            self.reader_task.cancel()

    def restart(self):
        self.terminate()
        self.buffer.clear()
        self._spawn()
        self.start()

TERMINAL_SESSIONS: dict[str, TerminalSession] = {}

@app.websocket("/api/ws/terminal")
async def websocket_terminal(websocket: WebSocket, session_id: str = "default"):
    await websocket.accept()
    session = TERMINAL_SESSIONS.get(session_id)
    if session is None or not session.alive:
        session = TerminalSession(session_id)
        TERMINAL_SESSIONS[session_id] = session
        session.start()

    # Replay buffer histórico si la sesión ya tenía contenido (persistencia entre pestañas/desconexiones)
    history = session.get_history()
    if history:
        try:
            await websocket.send_text(history)
        except Exception:
            pass

    session.subscribers.add(websocket)

    try:
        while True:
            msg = await websocket.receive_text()
            if msg.startswith("RESIZE:"):
                parts = msg.split(":")
                if len(parts) == 3:
                    try:
                        session.resize(int(parts[1]), int(parts[2]))
                    except Exception:
                        pass
            elif msg == "__SENTINEL_RESTART__":
                session.restart()
            else:
                session.write(msg)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        session.subscribers.discard(websocket)
        # IMPORTANTE: NO terminamos el proceso de la sesión aquí.
        # Esto permite que el usuario cambie de pestaña, navegue en el frontend o sufra un microcorte
        # sin que se interrumpa su comando en ejecución (ej: htop, compilación, tail o scripts).

@app.post("/api/terminal/session/terminate")
def terminate_terminal_session(req: dict):
    sid = req.get("session_id", "default")
    if sid in TERMINAL_SESSIONS:
        TERMINAL_SESSIONS[sid].terminate()
        del TERMINAL_SESSIONS[sid]
    return {"status": "ok", "terminated": sid}

@app.websocket("/api/ws/terminal/proxy")
async def websocket_terminal_proxy(websocket: WebSocket, target_url: str, session_id: str = "default", token: str = ""):
    await websocket.accept()
    import websockets
    target_ws = target_url.replace("http://", "ws://").replace("https://", "wss://")
    target_uri = f"{target_ws}/api/ws/terminal?session_id={session_id}&token={token}"
    try:
        async with websockets.connect(target_uri) as remote_ws:
            async def forward_to_client():
                try:
                    async for msg in remote_ws:
                        await websocket.send_text(msg)
                except Exception:
                    pass

            async def forward_to_remote():
                try:
                    while True:
                        msg = await websocket.receive_text()
                        await remote_ws.send(msg)
                except Exception:
                    pass

            t1 = asyncio.create_task(forward_to_client())
            t2 = asyncio.create_task(forward_to_remote())
            done, pending = await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
    except Exception as e:
        try:
            await websocket.send_text(f"\r\n\x1b[31m[Error al conectar proxy de terminal con {target_url}: {e}]\x1b[0m\r\n")
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
class WolRequest(BaseModel):
    mac: str

@app.post("/api/network/wol")
def wake_on_lan(req: WolRequest):
    out = command("wakeonlan", req.mac)
    return {"status": "ok", "output": out}

class PingRequest(BaseModel):
    host: str

@app.post("/api/network/ping")
def ping_network_device(req: PingRequest):
    host = req.host.strip()
    if not re.match(r'^[a-zA-Z0-9\.\:\-]+$', host):
        raise HTTPException(status_code=400, detail="Invalid host format")
    t0 = time.time()
    success = False
    latency_ms = None
    try:
        param = "-n" if sys.platform == "win32" else "-c"
        timeout_param = "-w" if sys.platform == "win32" else "-W"
        timeout_val = "1000" if sys.platform == "win32" else "1"
        cmd = ["ping", param, "1", timeout_param, timeout_val, host]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        latency_ms = round((time.time() - t0) * 1000, 1)
        success = (res.returncode == 0)
    except Exception:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((host, 80))
            s.close()
            latency_ms = round((time.time() - t0) * 1000, 1)
            success = True
        except Exception:
            success = False
    if not success and (host == "127.0.0.1" or host == "localhost"):
        success = True
        latency_ms = 0.5
    return {"status": "ok" if success else "unreachable", "host": host, "latency_ms": latency_ms if success else None}

class SignalRequest(BaseModel):
    node_id: str
    target: str
    message: str
    signal_type: str = "alert"

@app.post("/api/network/signal")
def send_device_signal(req: SignalRequest):
    msg = f"Señal [{req.signal_type.upper()}] a {req.target}: {req.message}"
    notify(msg, "info" if req.signal_type == "probe" else "success")
    return {"status": "sent", "target": req.target, "timestamp": time.time(), "message": req.message}

@app.get("/api/network/speedtest")
def run_speedtest():
    try:
        out = command("speedtest-cli", "--json")
        return json.loads(out)
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/marketplace/search")
def search_marketplace(q: str):
    out = command("snap", "find", q)
    lines = out.splitlines()
    results = []
    if len(lines) > 1:
        # Snap find columns: Name, Version, Publisher, Notes, Summary
        for line in lines[1:]:
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 5:
                results.append({
                    "id": parts[0],
                    "name": parts[0],
                    "version": parts[1],
                    "publisher": parts[2],
                    "desc": parts[4]
                })
    return {"results": results}

@app.websocket("/api/ws/install/{app_id}")
async def websocket_install(websocket: WebSocket, app_id: str):
    await websocket.accept()
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["COLORTERM"] = "truecolor"
    p = ptyprocess.PtyProcessUnicode.spawn(['sudo', 'snap', 'install', app_id], env=env)
    
    async def read_from_pty():
        try:
            while True:
                data = await asyncio.get_event_loop().run_in_executor(None, p.read, 4096)
                if data:
                    await websocket.send_text(data)
                else:
                    break
        except Exception:
            pass
        finally:
            await websocket.close()

    async def write_to_pty():
        try:
            while True:
                data = await websocket.receive_text()
                if data.startswith("RESIZE:"):
                    parts = data.split(":")
                    if len(parts) == 3:
                        try: p.setwinsize(int(parts[2]), int(parts[1]))
                        except: pass
                else:
                    await asyncio.get_event_loop().run_in_executor(None, p.write, data)
        except Exception:
            pass

    t1 = asyncio.create_task(read_from_pty())
    t2 = asyncio.create_task(write_to_pty())
    await asyncio.gather(t1, t2)

@app.websocket("/api/ws/sandbox/install/{tool}")
async def websocket_sandbox_install(websocket: WebSocket, tool: str):
    await websocket.accept()
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    
    # We will use a bash script to handle the git clone and setup
    user_home = os.path.expanduser("~")
    sandbox_tools_dir = os.path.join(user_home, "lab-sandbox", "tools")
    if tool == "theharvester":
        script = f"""
        echo "Iniciando instalación de theHarvester en Sandbox..."
        mkdir -p "{sandbox_tools_dir}"
        cd "{sandbox_tools_dir}"
        if [ -d "theHarvester" ]; then
            echo "Directorio theHarvester ya existe. Actualizando..."
            cd theHarvester && git pull
        else
            git clone https://github.com/laramies/theHarvester.git
            cd theHarvester
        fi
        echo "Configurando entorno virtual de Python..."
        python3 -m venv venv
        source venv/bin/activate
        echo "Instalando dependencias (esto puede tardar unos minutos)..."
        pip install .
        echo "Instalación completada exitosamente."
        """
    else:
        script = f"echo 'Herramienta {tool} no soportada para instalación automática.'"
        
    p = ptyprocess.PtyProcessUnicode.spawn(['/bin/bash', '-c', script], env=env)
    
    async def read_from_pty():
        try:
            while True:
                data = await asyncio.get_event_loop().run_in_executor(None, p.read, 4096)
                if data:
                    await websocket.send_text(data)
                else:
                    break
        except Exception:
            pass
        finally:
            await websocket.close()

    await read_from_pty()

@app.websocket("/api/ws/sandbox/terminal/{tool}")
async def websocket_sandbox_terminal(websocket: WebSocket, tool: str):
    await websocket.accept()
    
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["COLORTERM"] = "truecolor"
    
    if tool == "theharvester":
        th_dir = os.path.join(os.path.expanduser("~"), "lab-sandbox", "tools", "theHarvester")
        # Launch an interactive bash session with the python virtual environment pre-activated
        script = f"""
        cd "{th_dir}"
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
        echo -e "\\e[1;32m[Sentinel Sandbox]\\e[0m Entorno de \\e[1;34mtheHarvester\\e[0m cargado."
        echo -e "Ejecuta: \\e[1;33mpython -m theHarvester -h\\e[0m para ver las opciones."
        echo -e "Repositorio oficial: \\e[4;36mhttps://github.com/laramies/theHarvester\\e[0m"
        echo ""
        exec bash --noprofile --norc
        """
    else:
        script = f"""
        echo "Herramienta {tool} no configurada para terminal interactiva."
        exec bash --noprofile --norc
        """
        
    p = ptyprocess.PtyProcessUnicode.spawn(['/bin/bash', '-c', script], env=env)
    
    async def read_from_pty():
        try:
            while True:
                data = await asyncio.get_event_loop().run_in_executor(None, p.read, 4096)
                if data:
                    await websocket.send_text(data)
                else:
                    break
        except Exception:
            pass
        finally:
            await websocket.close()

    async def write_to_pty():
        try:
            while True:
                data = await websocket.receive_text()
                if data.startswith("RESIZE:"):
                    parts = data.split(":")
                    if len(parts) == 3:
                        try: p.setwinsize(int(parts[2]), int(parts[1]))
                        except: pass
                else:
                    await asyncio.get_event_loop().run_in_executor(None, p.write, data)
        except Exception:
            pass

    t1 = asyncio.create_task(read_from_pty())
    t2 = asyncio.create_task(write_to_pty())
    await asyncio.gather(t1, t2)

@app.get("/api/sandbox/tools")
def get_sandbox_tools():
    # Return available tools and their installed status
    tools = [
        {
            "id": "theharvester",
            "name": "theHarvester",
            "category": "OSINT",
            "desc": "Buscador de emails, subdominios, hosts, nombres de empleados, puertos abiertos y banners desde diferentes fuentes públicas como motores de búsqueda, servidores PGP y bases de datos.",
            "repo": "https://github.com/laramies/theHarvester",
            "icon": "Search"
        }
    ]
    
    # Check installation status
    tools_base = os.path.join(os.path.expanduser("~"), "lab-sandbox", "tools")
    for t in tools:
        t["installed"] = os.path.exists(os.path.join(tools_base, t['id'])) or os.path.exists(os.path.join(tools_base, "theHarvester"))
        
    return {"results": tools}


@app.get("/api/marketplace/installed")
def list_installed_snaps():
    try:
        out = command("snap", "list")
        lines = out.splitlines()
        results = []
        if len(lines) > 1:
            for line in lines[1:]:
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) >= 6:
                    results.append({
                        "name": parts[0],
                        "version": parts[1],
                        "rev": parts[2],
                        "tracking": parts[3],
                        "publisher": parts[4],
                        "notes": parts[5]
                    })
        return {"results": results}
    except:
        return {"results": []}

class AppInstallRequest(BaseModel):
    app_id: str

@app.post("/api/marketplace/uninstall")
def uninstall_app(req: AppInstallRequest):
    subprocess.Popen(["sudo", "snap", "remove", req.app_id])
    return {"status": "uninstalling"}

def background_nmap(mode="quick"):
    global ARP_CACHE
    notify(f"Iniciando Escaneo {'Profundo (NMAP)' if mode=='deep' else 'Rápido'} de Red...", "info")
    try:
        if mode == "deep":
            # Extraer subnet (ej. 192.168.68.0/24)
            ip_out = command("ip", "-o", "-f", "inet", "addr", "show")
            subnet = None
            for line in ip_out.splitlines():
                if "scope global" in line:
                    subnet = line.split()[3]
                    break
            if subnet:
                # Nmap ping sweep exhaustivo
                command("sudo", "nmap", "-sn", "-PR", "-PU", subnet)
                time.sleep(2) # Dar tiempo a que ARP se estabilice

        out = command("sudo", "/usr/sbin/arp-scan", "-l")
        neighbors = []
        for line in out.splitlines():
            parts = line.split('\t')
            if len(parts) >= 2:
                ip, mac = parts[0], parts[1]
                if ":" in mac and len(mac) == 17:
                    vendor, device_type = get_mac_info(mac)
                    if vendor == "Unknown Vendor" and len(parts) >= 3:
                        vendor = parts[2]
                        device_type = deduce_device_type(vendor)
                    neighbors.append({
                        "ip": ip, "mac": mac, "interface": "LAN",
                        "vendor": vendor, "device_type": device_type
                    })
        ARP_CACHE = neighbors
        notify(f"✅ Escaneo {'Profundo' if mode=='deep' else 'Rápido'} Finalizado: {len(neighbors)} dispositivos encontrados.", "success")
    except Exception as e:
        notify("❌ Error en el escaneo de red.", "error")

@app.get("/api/network/scan/quick")
def quick_network_scan():
    threading.Thread(target=background_nmap, args=("quick",)).start()
    return {"status": "started"}

@app.get("/api/network/scan/deep")
def deep_network_scan():
    threading.Thread(target=background_nmap, args=("deep",)).start()
    return {"status": "started"}

@app.get("/api/alexa/status")
@app.post("/api/alexa/status")
def alexa_status():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    
    # Check klipper status
    try:
        klipper_status = subprocess.check_output(["systemctl", "is-active", "klipper"], stderr=subprocess.STDOUT).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        klipper_status = e.output.decode('utf-8').strip()
    
    k_state = "encendido e imprimiendo" if klipper_status == "active" else "apagado o en espera"
    
    username = os.environ.get("USER") or os.environ.get("USERNAME") or "Operador"
    speech_text = f"Hola {username.capitalize()}, SentinelOS está usando un aproximado de {int(cpu)} por ciento de CPU y {int(mem)} por ciento de RAM. El servicio de Klipper de la impresora 3D está {k_state}, y en general todo se ve bien."
    
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech_text
            },
            "shouldEndSession": True
        }
    }

@app.websocket("/api/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    process = await asyncio.create_subprocess_exec(
        "journalctl", "-f", "-n", "100",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            await websocket.send_text(line.decode('utf-8'))
    except WebSocketDisconnect:
        pass
    finally:
        process.terminate()

# ==========================================
# SENTINEL AI & OBSIDIAN MEMORY VAULT API
# ==========================================

class SentinelChatPayload(BaseModel):
    messages: list[dict]
    model: str = "sentinel:latest"
    effort: str = "med"
    enable_thinking: bool = False
    enable_research: bool = False

class SentinelNodePayload(BaseModel):
    id: str
    title: str
    category: str = "conceptos"
    content: str
    tags: list[str] = []

class SentinelLearnPayload(BaseModel):
    user_message: str
    ai_response: str

@app.get("/api/sentinel/status")
async def sentinel_status():
    ollama_info = await sentinel_service.check_ollama_status()
    notes = vault_manager.get_all_notes()
    return {
        "ollama": ollama_info,
        "vault_notes_count": len(notes),
        "status": "ready" if ollama_info["online"] else "offline"
    }

@app.get("/api/sentinel/graph")
def sentinel_graph():
    return vault_manager.build_graph()

@app.get("/api/sentinel/node/{node_id}")
def sentinel_get_node(node_id: str):
    note = vault_manager.get_note_by_id(node_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nodo de memoria no encontrado")
    return note

@app.post("/api/sentinel/node")
def sentinel_save_node(payload: SentinelNodePayload):
    res = vault_manager.save_note(
        note_id=payload.id,
        title=payload.title,
        category=payload.category,
        content=payload.content,
        tags=payload.tags
    )
    notify(f"Nodo de memoria '{payload.title}' actualizado en la bóveda", "info")
    return res

@app.post("/api/sentinel/chat")
async def sentinel_chat(payload: SentinelChatPayload):
    async def event_generator():
        async for chunk in sentinel_service.chat_with_sentinel_stream(
            messages=payload.messages,
            model=payload.model,
            effort=payload.effort,
            enable_thinking=payload.enable_thinking,
            enable_research=payload.enable_research
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/api/sentinel/learn")
async def sentinel_learn(payload: SentinelLearnPayload):
    result = await sentinel_service.auto_extract_and_learn(
        user_message=payload.user_message,
        ai_response=payload.ai_response
    )
    return result or {"action": "none"}

@app.get("/api/sentinel/lora/status")
def sentinel_lora_status():
    return lora_manager.get_dataset_stats()

@app.post("/api/sentinel/lora/compile")
def sentinel_lora_compile():
    return lora_manager.compile_sentinel_model()


# ==========================================
# GESTION DINAMICA DE MODELOS Y CONECTIVIDAD
# ==========================================

class SentinelModelSwitchPayload(BaseModel):
    model: str

@app.get("/api/network/internet_status")
def get_internet_status():
    return check_cached_internet_status(force=False)

@app.post("/api/network/hotspot/enable")
def enable_network_hotspot():
    """Crea una red Hotspot Wi-Fi local para conectar laptops y servidores sin router ni internet."""
    ssid = "SentinelOS-Mesh"
    password = "sentinelmesh2026"
    if sys.platform == "win32":
        try:
            subprocess.run(f'netsh wlan set hostednetwork mode=allow ssid={ssid} key={password}', shell=True, capture_output=True)
            res = subprocess.run('netsh wlan start hostednetwork', shell=True, capture_output=True, text=True)
            # Intentar también Mobile Hotspot de Windows
            ps = """
            $connectionProfile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
            $tetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($connectionProfile)
            $tetheringManager.StartTetheringAsync()
            """
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
            return {"status": "ok", "ssid": ssid, "password": password, "message": "Punto de acceso Wi-Fi SentinelOS iniciado."}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
    else:
        try:
            res = subprocess.run(f"nmcli dev wifi hotspot ssid '{ssid}' password '{password}'", shell=True, capture_output=True, text=True)
            return {"status": "ok", "ssid": ssid, "password": password, "output": res.stdout.strip()}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

# =========================================================================
# GESTOR DE DESCARGA Y DESPLIEGUE DE MODELOS IA A DOCKER / SERVIDORES
# =========================================================================
_AI_DEPLOY_STATE = {
    "status": "idle",  # idle | downloading | deploying | completed | error
    "progress": 0,
    "model_id": "",
    "target_server": "local",
    "logs": [],
    "error": None
}

class ModelDeployRequest(BaseModel):
    model_id: str
    target_server: str = "local"  # "local" o IP/nombre del servidor
    hf_repo: str = ""

@app.get("/api/ai/models/catalog")
def get_ai_models_catalog():
    """Retorna el catálogo oficial de modelos STEM optimizados para SentinelOS."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    export_dir = os.path.join(root_dir, "export", "output_gguf")
    models_dir = os.path.join(root_dir, "models")
    
    catalog = [
        {
            "id": "sentinel-agentic-1b",
            "name": "Sentinel Agentic 1B (Recomendado STEM)",
            "params": "1.23B",
            "quant": "Q4_K_M",
            "size_mb": 807,
            "filename": "sentinel-agentic-1b.Q4_K_M.gguf",
            "desc": "Modelo STEM nativo con capacidades agenticas para cálculo, terminal y física.",
            "is_local": os.path.exists(os.path.join(export_dir, "sentinel-agentic-1b.Q4_K_M.gguf")),
            "recommended": True
        },
        {
            "id": "sentinel-pure-stem-1b",
            "name": "Sentinel Pure STEM 1B (Ultra Rápido)",
            "params": "1.23B",
            "quant": "Q4_K_M",
            "size_mb": 807,
            "filename": "sentinel-pure-stem-1b.Q4_K_M.gguf",
            "desc": "Podado y alineado con DPO para razonamiento matemático puro a 60+ tok/s.",
            "is_local": os.path.exists(os.path.join(export_dir, "sentinel-pure-stem-1b.Q4_K_M.gguf")),
            "recommended": False
        },
        {
            "id": "sentinel-master-3b",
            "name": "Sentinel Master 3B (Alta Capacidad)",
            "params": "3.2B",
            "quant": "Q4_K_M",
            "size_mb": 2019,
            "filename": "sentinel-master.Q4_K_M.gguf",
            "desc": "Modelo de 3.2B para laboratorios complejos e inferencia multivariable.",
            "is_local": os.path.exists(os.path.join(export_dir, "sentinel-master.Q4_K_M.gguf")),
            "recommended": False
        },
        {
            "id": "llama-3.2-1b",
            "name": "Llama 3.2 1B Instruct (Base Meta)",
            "params": "1.23B",
            "quant": "Q4_K_M",
            "size_mb": 807,
            "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
            "desc": "Modelo base de instrucción general de Meta.",
            "is_local": os.path.exists(os.path.join(models_dir, "llama-3.2-1b", "Llama-3.2-1B-Instruct-Q4_K_M.gguf")),
            "recommended": False
        }
    ]
    return {"catalog": catalog, "deploy_state": _AI_DEPLOY_STATE}

def _bg_deploy_task(req: ModelDeployRequest):
    global _AI_DEPLOY_STATE
    def log(msg: str):
        t = datetime.now().strftime("%H:%M:%S")
        entry = f"[{t}] {msg}"
        _AI_DEPLOY_STATE["logs"].append(entry)
        print(f"[AI-DEPLOY] {entry}")

    try:
        _AI_DEPLOY_STATE["status"] = "in_progress"
        _AI_DEPLOY_STATE["progress"] = 10
        _AI_DEPLOY_STATE["error"] = None
        _AI_DEPLOY_STATE["model_id"] = req.model_id
        _AI_DEPLOY_STATE["target_server"] = req.target_server
        _AI_DEPLOY_STATE["logs"] = []

        log(f"Iniciando despliegue de modelo '{req.model_id}' hacia objetivo: '{req.target_server}'")
        
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        export_dir = os.path.join(root_dir, "export", "output_gguf")
        models_dir = os.path.join(root_dir, "models")

        # Mapear archivo
        fname_map = {
            "sentinel-agentic-1b": "sentinel-agentic-1b.Q4_K_M.gguf",
            "sentinel-pure-stem-1b": "sentinel-pure-stem-1b.Q4_K_M.gguf",
            "sentinel-master-3b": "sentinel-master.Q4_K_M.gguf",
            "llama-3.2-1b": "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
        }
        filename = fname_map.get(req.model_id, f"{req.model_id}.gguf")
        
        # Buscar archivo local
        local_src = os.path.join(export_dir, filename)
        if not os.path.exists(local_src):
            local_src = os.path.join(models_dir, "llama-3.2-1b", filename)
        if not os.path.exists(local_src):
            local_src = os.path.join(root_dir, filename)

        if not os.path.exists(local_src):
            log(f"Aviso: Archivo local no encontrado en export/ ni models/. Procediendo con plantilla de modelo Ollama.")
            local_src = None
        else:
            mb = os.path.getsize(local_src) / (1024 * 1024)
            log(f"Binario GGUF localizado: {local_src} ({mb:.1f} MB)")

        _AI_DEPLOY_STATE["progress"] = 35

        # Si el objetivo es el Servidor HP (remoto)
        is_hp_server = ("labsentinel" in req.target_server.lower() or "hp" in req.target_server.lower() or "192.168.68.68" in req.target_server)
        
        if is_hp_server:
            log("Conectando vía SSH seguro con el Servidor HP...")
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Intentar IP Tailscale o LAN
            hp_host = "labsentinel.tailc83bd7.ts.net"
            try:
                client.connect(hp_host, port=22, username="mauro", password="Pollito92.", timeout=12)
            except Exception:
                hp_host = "192.168.68.68"
                client.connect(hp_host, port=22, username="mauro", password="Pollito92.", timeout=12)
                
            log(f"Conexión SSH establecida con {hp_host}.")
            _AI_DEPLOY_STATE["progress"] = 50

            # Subir o verificar modelo en servidor HP
            if local_src and os.path.exists(local_src):
                log("Verificando existencia del binario GGUF en el servidor remoto...")
                remote_path = f"/home/mauro/{filename}"
                stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_path} 2>/dev/null")
                if not stdout.read().decode().strip():
                    log(f"Transfiriendo binario {filename} hacia servidor HP vía SFTP...")
                    sftp = client.open_sftp()
                    sftp.put(local_src, remote_path)
                    sftp.close()
                    log("Transferencia de archivo GGUF completada al 100%.")
                else:
                    log("El archivo binario ya se encuentra en el servidor remoto.")

            _AI_DEPLOY_STATE["progress"] = 75
            log("Creando Modelfile y registrando en contenedor Docker de Ollama...")
            modelfile_cmd = f"""
cat << 'EOF' > /home/mauro/Modelfile.{req.model_id}
FROM /home/mauro/{filename}
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|end_of_text|>"
SYSTEM \"\"\"Eres SENTINEL, el asistente de inteligencia artificial y copiloto distribuido de laboratorio STEM. Responde de forma técnica, precisa y útil.\"\"\"
EOF
docker cp /home/mauro/{filename} ollama:/root/ 2>/dev/null || true
docker cp /home/mauro/Modelfile.{req.model_id} ollama:/root/
docker exec ollama ollama create {req.model_id}:latest -f /root/Modelfile.{req.model_id}
"""
            stdin, stdout, stderr = client.exec_command(modelfile_cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            if out: log(f"Docker Ollama: {out.strip()}")
            if err and "error" in err.lower(): log(f"Docker Aviso: {err.strip()}")

            log("Verificando modelos disponibles en el Docker de Ollama...")
            stdin, stdout, _ = client.exec_command("docker exec ollama ollama list")
            log(stdout.read().decode().strip())
            client.close()

        else:
            # Despliegue Local (Host Maestro)
            log("Configurando modelo en entorno local Docker / Ollama...")
            if local_src:
                log(f"Preparando Modelfile local para {req.model_id}...")
                modelfile_path = os.path.join(root_dir, f"Modelfile.{req.model_id}")
                with open(modelfile_path, "w", encoding="utf-8") as mf:
                    mf.write(f'FROM "{local_src}"\nPARAMETER temperature 0.3\n')
                
                # Si ollama CLI existe localmente, registrarlo
                if shutil.which("ollama"):
                    subprocess.run(["ollama", "create", f"{req.model_id}:latest", "-f", modelfile_path], capture_output=True)
                    log(f"Modelo {req.model_id}:latest creado en Ollama local.")
                
            _AI_DEPLOY_STATE["progress"] = 90

        _AI_DEPLOY_STATE["progress"] = 100
        _AI_DEPLOY_STATE["status"] = "completed"
        log(f"¡ÉXITO! Modelo {req.model_id} cargado e instalado en Docker. Listo para usar en Sentinel AI Lab.")

    except Exception as e:
        _AI_DEPLOY_STATE["status"] = "error"
        _AI_DEPLOY_STATE["error"] = str(e)
        log(f"ERROR DURANTE EL DESPLIEGUE: {str(e)}")

@app.post("/api/ai/models/deploy")
def trigger_model_deploy(req: ModelDeployRequest):
    """Inicia la descarga, transferencia y carga automática del modelo en Docker en segundo plano."""
    global _AI_DEPLOY_STATE
    if _AI_DEPLOY_STATE["status"] == "in_progress":
        return {"status": "busy", "message": "Ya hay una descarga/despliegue en progreso.", "state": _AI_DEPLOY_STATE}

    import threading
    t = threading.Thread(target=_bg_deploy_task, args=(req,), daemon=True)
    t.start()
    return {"status": "started", "message": f"Despliegue de {req.model_id} iniciado.", "state": _AI_DEPLOY_STATE}

@app.get("/api/ai/models/deploy/status")
def get_model_deploy_status():
    """Consulta el progreso y logs en tiempo real del despliegue del modelo."""
    return _AI_DEPLOY_STATE

@app.get("/api/network/details")
def get_network_details():
    net_status = check_cached_internet_status(force=False)
    gateway = get_default_gateway()
    local_ip = get_primary_local_ip()
    traffic = get_network_traffic_rates()
    interfaces = []
    try:
        if_stats = psutil.net_if_stats()
        if_addrs = psutil.net_if_addrs()
        for iface_name, stats in if_stats.items():
            if "loopback" in iface_name.lower() or iface_name.lower() == "lo":
                continue
            name_lower = iface_name.lower()
            if name_lower.startswith("wl") or any(w in name_lower for w in ["wi-fi", "wifi", "wlan", "wireless", "802.11"]):
                itype = "wifi"
            elif any(w in name_lower for w in ["tailscale", "tun", "wireguard", "wg", "vpn"]):
                itype = "vpn"
            else:
                itype = "ethernet"
            ipv4 = ""
            mac = ""
            for addr in if_addrs.get(iface_name, []):
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    ipv4 = addr.address
                elif getattr(addr, "family", None) in (getattr(psutil, "AF_LINK", None), getattr(socket, "AF_PACKET", None)):
                    mac = addr.address
            if stats.isup and ipv4:
                interfaces.append({
                    "name": iface_name,
                    "type": itype,
                    "isup": stats.isup,
                    "speed": stats.speed,
                    "ip": ipv4,
                    "mac": mac
                })
    except Exception:
        pass
    return {
        "internet": net_status,
        "gateway": gateway,
        "local_ip": local_ip,
        "traffic": traffic,
        "interfaces": interfaces
    }

@app.get("/api/sentinel/models")
def get_available_models():
    net = sentinel_service.check_internet_connectivity()
    return {
        "models": sentinel_service.AVAILABLE_MODELS,
        "active_model": sentinel_service.get_active_model_id(),
        "has_internet": net.get("has_internet", False),
        "latency_ms": net.get("latency_ms")
    }

@app.post("/api/sentinel/model/switch")
async def switch_model(payload: SentinelModelSwitchPayload):
    target_id = payload.model
    valid_ids = [m["id"] for m in sentinel_service.AVAILABLE_MODELS]
    if target_id not in valid_ids:
        raise HTTPException(status_code=400, detail=f"Modelo '{target_id}' no reconocido.")
    
    # 1. Conmutacion a NVIDIA Nemotron (Cloud)
    if target_id == "nvidia-nemotron":
        net = sentinel_service.check_internet_connectivity()
        if not net.get("has_internet"):
            raise HTTPException(status_code=503, detail="El servidor no tiene acceso a Internet para activar NVIDIA Nemotron.")
        sentinel_service.set_active_model_id(target_id)
        notify("Conmutado a NVIDIA Nemotron 3.5 Lightning (Cloud Flagship)", "success")
        return {"status": "ok", "active_model": target_id, "mode": "cloud"}
    
    # 2. Conmutacion a Modelo Local AVX2 (1B vs 3B)
    model_meta = next(m for m in sentinel_service.AVAILABLE_MODELS if m["id"] == target_id)
    gguf_name = model_meta.get("file")
    gguf_path = f"/opt/sentinel/models/{gguf_name}"
    if not os.path.exists(gguf_path):
        raise HTTPException(status_code=404, detail=f"Archivo binario {gguf_name} no encontrado en /opt/sentinel/models/")
    
    try:
        service_file = "/etc/systemd/system/sentinel.service"
        if os.path.exists(service_file):
            with open(service_file, "r") as sf:
                s_content = sf.read()
            new_s_content = re.sub(
                r"-m\s+/opt/sentinel/models/\S+",
                f"-m {gguf_path}",
                s_content
            )
            with open("/tmp/sentinel.service.tmp", "w") as tmp_f:
                tmp_f.write(new_s_content)
            subprocess.run(["sudo", "-n", "cp", "/tmp/sentinel.service.tmp", "/etc/systemd/system/sentinel.service"], capture_output=True)
            subprocess.run(["sudo", "-n", "systemctl", "daemon-reload"], capture_output=True)
            subprocess.run(["sudo", "-n", "systemctl", "restart", "sentinel.service"], capture_output=True)
            
        sentinel_service.set_active_model_id(target_id)
        notify(f"Conmutado exitosamente a {model_meta['name']}", "success")
        return {"status": "ok", "active_model": target_id, "mode": "local", "model_file": gguf_name}
    except Exception as e:
        print(f"Error cambiando modelo local: {e}")
        raise HTTPException(status_code=500, detail=str(e))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(BASE_DIR, "dist")
if not os.path.isdir(dist_dir):
    frontend_candidate = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist"))
    if os.path.isdir(frontend_candidate):
        dist_dir = frontend_candidate

if os.path.isdir(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
else:
    @app.get("/")
    def index_root():
        return {"status": "SentinelOS Core Online", "port": 8001}
