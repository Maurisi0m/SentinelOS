# -*- coding: utf-8 -*-
"""
SENTINEL OS - MESH & NETWORK DISCOVERY ENGINE v2.0
Garantiza conectividad continua y resiliente en TODOS los escenarios:
1. Tailscale VPN: Conexión cifrada zero-trust a través de IPs 100.x.x.x y MagicDNS (*.ts.net).
2. Red Local (LAN / Wi-Fi) sin Tailscale:
   - Descubrimiento automático zero-config mediante Beacon UDP Broadcast en puerto 8003.
   - Escáner ultrarrápido paralelo de subred LAN (/24) para entornos con aislamiento AP.
3. Sin Conexión / Modo Fuera de Línea (Offline):
   - Operación 100% autónoma en bucle local (127.0.0.1 / localhost:8001).
   - Timeouts ultracortos sin bloqueos de DNS o excepciones de red no controladas.
4. Auto-Failover y Reverse Push:
   - Si una ruta falla, conmuta automáticamente entre LAN, Tailscale, IPv6 y mDNS.
   - Envío saliente (reverse heartbeat) cada 3s para eludir firewalls restrictivos.
"""

import os
import sys
import time
import json
import socket
import threading
import subprocess
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import psutil

# Registro en memoria de nodos de la malla
_MESH_LOCK = threading.Lock()
_MESH_NODES = {}          # node_id -> { info, metrics, last_seen, active_url, candidates, source }
_CONFIGURED_PEERS = set() # URLs base de peers (ej. "http://192.168.1.50:8001")
_TS_CACHE = {"data": {}, "time": 0.0}

LAN_BEACON_PORT = 8003
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEERS_FILE = os.path.join(ROOT_DIR, "config", "mesh_peers.json")

def _get_auth_data() -> dict:
    auth_file = os.path.join(ROOT_DIR, "config", "node_auth.json")
    if os.path.exists(auth_file):
        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "node_id": f"node-{socket.gethostname().lower()}",
        "node_name": socket.gethostname(),
        "token": ""
    }

def load_persisted_peers():
    """Carga los peers guardados previamente en disco."""
    if os.path.exists(PEERS_FILE):
        try:
            with open(PEERS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, list):
                    for u in saved:
                        if isinstance(u, str) and u.startswith("http"):
                            _CONFIGURED_PEERS.add(u.strip().rstrip("/"))
        except Exception:
            pass

def save_persisted_peers():
    """Guarda los peers conocidos en disco para que persistan entre reinicios."""
    try:
        os.makedirs(os.path.dirname(PEERS_FILE), exist_ok=True)
        with open(PEERS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(_CONFIGURED_PEERS), f, indent=2)
    except Exception:
        pass

def get_tailscale_peers() -> dict:
    """Obtiene la lista de peers y auto-información de Tailscale de forma ultra-rápida (en caché por 4s)."""
    global _TS_CACHE
    now = time.time()
    if now - _TS_CACHE["time"] < 4.0 and _TS_CACHE["data"]:
        return _TS_CACHE["data"]

    result = {"self": {}, "peers": {}, "map_by_ip": {}, "map_by_name": {}}
    try:
        cmd = ["tailscale", "status", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=0.9)
        if res.returncode == 0:
            raw = json.loads(res.stdout)
            self_node = raw.get("Self", {})
            s_name = self_node.get("HostName", "").lower()
            s_dns = self_node.get("DNSName", "").rstrip(".").lower()
            s_ips = self_node.get("TailscaleIPs", [])
            result["self"] = {
                "hostname": s_name,
                "dns": s_dns,
                "ips": s_ips,
                "online": self_node.get("Online", True)
            }

            for p_id, p in raw.get("Peer", {}).items():
                h_name = p.get("HostName", "").lower()
                dns_name = p.get("DNSName", "").rstrip(".").lower()
                ips = p.get("TailscaleIPs", [])
                p_entry = {
                    "hostname": h_name,
                    "dns": dns_name,
                    "ips": ips,
                    "online": p.get("Online", False)
                }
                result["peers"][h_name] = p_entry
                if dns_name:
                    result["map_by_name"][dns_name] = p_entry
                result["map_by_name"][h_name] = p_entry
                for ip in ips:
                    result["map_by_ip"][ip] = p_entry
    except Exception:
        pass

    _TS_CACHE = {"data": result, "time": now}
    return result

def get_self_network_candidates(port: int = 8001) -> list[str]:
    """Descubre todas las URLs alcanzables para este nodo (Tailscale, LAN, Wi-Fi, Loopback)."""
    candidates = []
    seen = set()

    def add_url(u):
        u = u.strip().rstrip("/")
        if u and u not in seen:
            seen.add(u)
            candidates.append(u)

    # 1. Tailscale IP y MagicDNS (si está disponible)
    ts = get_tailscale_peers().get("self", {})
    for tip in ts.get("ips", []):
        if ":" not in tip:
            add_url(f"http://{tip}:{port}")
        else:
            add_url(f"http://[{tip}]:{port}")
    if ts.get("dns"):
        add_url(f"http://{ts['dns']}:{port}")

    # 2. Interfaces LAN y Wi-Fi reales mediante psutil
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if a.family == socket.AF_INET:
                    ip = a.address
                    if ip != "127.0.0.1" and not ip.startswith("169.254."):
                        add_url(f"http://{ip}:{port}")
    except Exception:
        pass

    # 3. Hostname local y mDNS
    try:
        h = socket.gethostname()
        if h:
            add_url(f"http://{h}:{port}")
            add_url(f"http://{h}.local:{port}")
    except Exception:
        pass

    # 4. Loopback garantizado (Modo Offline / Localhost siempre disponible)
    add_url(f"http://127.0.0.1:{port}")
    add_url(f"http://localhost:{port}")

    return candidates

def get_broadcast_addresses() -> list[str]:
    """Obtiene las direcciones de broadcast de todas las subredes activas (ej. 192.168.1.255)."""
    bcasts = ["255.255.255.255"]
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if a.family == socket.AF_INET and a.broadcast:
                    if a.broadcast not in bcasts:
                        bcasts.append(a.broadcast)
    except Exception:
        pass
    return bcasts

def get_local_subnet_prefixes() -> list[str]:
    """Obtiene los prefijos de subred local /24 (ej. '192.168.1.', '10.0.0.')."""
    prefixes = []
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if a.family == socket.AF_INET:
                    ip = a.address
                    if ip != "127.0.0.1" and not ip.startswith("169.254.") and not ip.startswith("100."):
                        parts = ip.split(".")
                        if len(parts) == 4:
                            pfx = f"{parts[0]}.{parts[1]}.{parts[2]}."
                            if pfx not in prefixes:
                                prefixes.append(pfx)
    except Exception:
        pass
    return prefixes

def record_heartbeat(payload: dict, client_ip: str = "") -> dict:
    """Registra o actualiza el estado de un nodo remoto que empujó su telemetría saliente."""
    node_id = payload.get("node_id") or f"node-{payload.get('node_name', 'unknown')}"
    node_name = payload.get("node_name", "Nodo Remoto")
    port = payload.get("port", 8001)

    candidates = list(payload.get("endpoints", []))
    if client_ip and client_ip != "127.0.0.1":
        client_url = f"http://{client_ip}:{port}"
        if client_url not in candidates:
            candidates.insert(0, client_url)

    now = time.time()
    with _MESH_LOCK:
        existing = _MESH_NODES.get(node_id, {})
        merged_candidates = list(dict.fromkeys(candidates + existing.get("candidates", [])))
        _MESH_NODES[node_id] = {
            "node_id": node_id,
            "node_name": node_name,
            "platform": payload.get("platform", "unknown"),
            "status": "online",
            "cores": payload.get("cores"),
            "total_ram_gb": payload.get("total_ram_gb"),
            "token": payload.get("token", ""),
            "last_seen": now,
            "active_url": existing.get("active_url") or (candidates[0] if candidates else ""),
            "candidates": merged_candidates,
            "data": payload.get("metrics") or existing.get("data"),
            "source": existing.get("source") or "reverse_heartbeat"
        }

    # Registrar en peers para sincronización mutua
    for c in candidates:
        if c.startswith("http"):
            _CONFIGURED_PEERS.add(c.rstrip("/"))
    save_persisted_peers()

    return {"status": "ok", "ack": now, "node_id": node_id}

def get_mesh_nodes() -> list[dict]:
    """Retorna la lista de todos los nodos conocidos y su estado actual."""
    now = time.time()
    result = []
    with _MESH_LOCK:
        for nid, n in list(_MESH_NODES.items()):
            is_active = (now - n.get("last_seen", 0)) < 35.0
            n_copy = dict(n)
            n_copy["status"] = "online" if is_active else "offline"
            result.append(n_copy)
    return result

def get_candidate_urls_for_target(target_url: str) -> list[str]:
    """Genera rutas de conexión alternativas para el nodo destino."""
    candidates = [target_url]
    try:
        parsed = urllib.parse.urlparse(target_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or ""
        query = f"?{parsed.query}" if parsed.query else ""
        host_lower = host.lower()
    except Exception:
        return candidates

    # 1. Buscar en MESH_NODES
    with _MESH_LOCK:
        for nid, n in _MESH_NODES.items():
            names = [nid.lower(), n.get("node_name", "").lower()]
            match = any(host_lower in nm or nm in host_lower for nm in names)
            if not match:
                for c in n.get("candidates", []):
                    if host_lower in c.lower():
                        match = True
                        break
            if match:
                for c in n.get("candidates", []):
                    full_alt = f"{c.rstrip('/')}{path}{query}"
                    if full_alt not in candidates:
                        candidates.append(full_alt)

    # 2. Buscar en Tailscale Peers
    ts = get_tailscale_peers()
    matched_peer = None
    if host_lower in ts.get("map_by_ip", {}):
        matched_peer = ts["map_by_ip"][host_lower]
    elif host_lower in ts.get("map_by_name", {}):
        matched_peer = ts["map_by_name"][host_lower]
    else:
        for p_name, p_data in ts.get("peers", {}).items():
            if p_name in host_lower or host_lower in p_name:
                matched_peer = p_data
                break

    if matched_peer:
        for tip in matched_peer.get("ips", []):
            host_str = f"[{tip}]" if ":" in tip else tip
            alt = f"http://{host_str}:{port}{path}{query}"
            if alt not in candidates:
                if ":" not in tip:
                    candidates.insert(1, alt)
                else:
                    candidates.append(alt)
        if matched_peer.get("dns"):
            alt = f"http://{matched_peer['dns']}:{port}{path}{query}"
            if alt not in candidates:
                candidates.append(alt)

    return candidates

def smart_proxy_fetch(target_url: str, headers: dict = None, timeout: float = 2.0) -> tuple[dict, str]:
    """Intenta contactar un nodo remoto probando sus rutas candidatas en orden."""
    headers = headers or {}
    candidates = get_candidate_urls_for_target(target_url)

    last_err = None
    for cand_url in candidates:
        try:
            req = urllib.request.Request(cand_url, headers={**headers, "User-Agent": "SentinelOS-Mesh-Proxy/2.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    raw = resp.read()
                    data = json.loads(raw.decode("utf-8"))
                    try:
                        parsed = urllib.parse.urlparse(cand_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
                        with _MESH_LOCK:
                            for nid, n in _MESH_NODES.items():
                                if any(base_url in c for c in n.get("candidates", [])):
                                    n["active_url"] = base_url
                                    n["last_seen"] = time.time()
                    except Exception:
                        pass
                    return data, cand_url
        except Exception as e:
            last_err = e

    # Si la conexión directa falló, verificar si tenemos datos del reverse heartbeat
    try:
        parsed = urllib.parse.urlparse(target_url)
        path = parsed.path or ""
        host_lower = (parsed.hostname or "").lower()
        if path.startswith("/api/data") or path.startswith("/api/node/info"):
            now = time.time()
            with _MESH_LOCK:
                for nid, n in _MESH_NODES.items():
                    is_match = (host_lower in nid.lower() or host_lower in n.get("node_name", "").lower())
                    if not is_match:
                        for c in n.get("candidates", []):
                            if host_lower in c.lower():
                                is_match = True
                                break
                    if is_match and (now - n.get("last_seen", 0) < 45.0):
                        cached = n.get("data")
                        if cached:
                            return cached, f"mesh-heartbeat://{nid}"
    except Exception:
        pass

    raise last_err or Exception("All candidate mesh paths timed out.")

# =========================================================================
# 1. LAN AUTO-DISCOVERY VIA UDP BROADCAST (Cero Configuración en LAN/Wi-Fi)
# =========================================================================

class LanBeaconSender(threading.Thread):
    """Emite un paquete UDP broadcast cada 4s para anunciar este nodo en la red local."""
    def __init__(self, port: int = 8001):
        super().__init__(daemon=True, name="SentinelLanBeaconSender")
        self.port = port
        self.running = True

    def run(self):
        time.sleep(1.0)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            try:
                auth = _get_auth_data()
                candidates = get_self_network_candidates(self.port)
                payload = {
                    "sentinel_beacon": "v2",
                    "node_id": auth.get("node_id"),
                    "node_name": auth.get("node_name"),
                    "platform": sys.platform,
                    "port": self.port,
                    "token": auth.get("token", ""),
                    "endpoints": [c for c in candidates if "127.0.0.1" not in c and "localhost" not in c],
                    "timestamp": time.time()
                }
                msg = json.dumps(payload).encode("utf-8")
                
                # Enviar a todas las direcciones de broadcast de subred
                for bcast in get_broadcast_addresses():
                    try:
                        sock.sendto(msg, (bcast, LAN_BEACON_PORT))
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(4.0)

class LanBeaconListener(threading.Thread):
    """Escucha paquetes de beacon de otros nodos en la red local y los vincula automáticamente."""
    def __init__(self, port: int = 8001):
        super().__init__(daemon=True, name="SentinelLanBeaconListener")
        self.port = port
        self.running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass
        try:
            # En Windows SO_BROADCAST en listener permite recibir paquetes broadcast
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("0.0.0.0", LAN_BEACON_PORT))
        except Exception:
            return

        sock.settimeout(3.0)
        self_auth = _get_auth_data()
        self_node_id = self_auth.get("node_id")

        while self.running:
            try:
                data, addr = sock.recvfrom(4096)
                payload = json.loads(data.decode("utf-8", errors="ignore"))
                if payload.get("sentinel_beacon") != "v2":
                    continue

                r_id = payload.get("node_id")
                # Ignorar beacons provenientes de este mismo nodo
                if r_id == self_node_id or (r_id and r_id.endswith(socket.gethostname().lower())):
                    continue

                r_name = payload.get("node_name", "Nodo LAN")
                r_port = payload.get("port", 8001)
                sender_ip = addr[0]
                candidates = payload.get("endpoints", [])
                primary_url = f"http://{sender_ip}:{r_port}"
                if primary_url not in candidates:
                    candidates.insert(0, primary_url)

                now = time.time()
                with _MESH_LOCK:
                    existing = _MESH_NODES.get(r_id, {})
                    merged_candidates = list(dict.fromkeys(candidates + existing.get("candidates", [])))
                    _MESH_NODES[r_id] = {
                        "node_id": r_id,
                        "node_name": r_name,
                        "platform": payload.get("platform", "unknown"),
                        "status": "online",
                        "token": payload.get("token", ""),
                        "last_seen": now,
                        "active_url": primary_url,
                        "candidates": merged_candidates,
                        "data": existing.get("data"),
                        "source": "lan_beacon"
                    }

                # Agregar a peers para enviar telemetría saliente recíproca
                _CONFIGURED_PEERS.add(primary_url)
                save_persisted_peers()
            except socket.timeout:
                continue
            except Exception:
                time.sleep(1.0)

# =========================================================================
# 2. ESCÁNER RÁPIDO DE SUBRED LAN (Para redes con aislamiento de broadcast)
# =========================================================================

def scan_lan_subnet(port: int = 8001) -> list[dict]:
    """Escanea concurrentemente las subredes locales /24 para detectar otros nodos SentinelOS."""
    prefixes = get_local_subnet_prefixes()
    if not prefixes:
        return []

    self_auth = _get_auth_data()
    self_id = self_auth.get("node_id")
    found_nodes = []

    def probe_ip(ip: str):
        url = f"http://{ip}:{port}/api/node/token"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SentinelSubnetScanner"})
            with urllib.request.urlopen(req, timeout=0.4) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("status") == "ok":
                        node_id = data.get("node_id") or f"node-{ip}"
                        if node_id != self_id:
                            entry = {
                                "node_id": node_id,
                                "node_name": data.get("node_name", ip),
                                "url": f"http://{ip}:{port}",
                                "token": data.get("token", ""),
                                "source": "subnet_scan"
                            }
                            found_nodes.append(entry)
                            with _MESH_LOCK:
                                _MESH_NODES[node_id] = {
                                    "node_id": node_id,
                                    "node_name": entry["node_name"],
                                    "status": "online",
                                    "last_seen": time.time(),
                                    "active_url": entry["url"],
                                    "candidates": [entry["url"]],
                                    "token": entry["token"],
                                    "source": "subnet_scan"
                                }
                            _CONFIGURED_PEERS.add(entry["url"])
        except Exception:
            pass

    ips_to_scan = []
    for pfx in prefixes:
        for last in range(1, 255):
            ips_to_scan.append(f"{pfx}{last}")

    with ThreadPoolExecutor(max_workers=35) as executor:
        executor.map(probe_ip, ips_to_scan)

    if found_nodes:
        save_persisted_peers()

    return found_nodes

# =========================================================================
# 3. MESH SYNC WORKER (Reverse Heartbeat y Sincronización)
# =========================================================================

class MeshSyncWorker(threading.Thread):
    """
    Hilo en segundo plano autónomo que:
    1. Envía periódicamente telemetría saliente (heartbeat) a peers conocidos.
    2. Sincroniza peers de Tailscale dinámicamente.
    """
    def __init__(self, port: int = 8001, get_telemetry_fn=None):
        super().__init__(daemon=True, name="SentinelMeshSyncWorker")
        self.port = port
        self.get_telemetry_fn = get_telemetry_fn
        self.running = True

    def add_peer(self, url: str):
        if url:
            clean = url.strip().rstrip("/")
            _CONFIGURED_PEERS.add(clean)
            save_persisted_peers()

    def run(self):
        load_persisted_peers()
        time.sleep(2.0)
        # Ejecutar un escaneo inicial silencioso de subred en segundo plano
        threading.Thread(target=scan_lan_subnet, kwargs={"port": self.port}, daemon=True).start()

        while self.running:
            try:
                self.sync_cycle()
            except Exception:
                pass
            time.sleep(3.5)

    def sync_cycle(self):
        # 1. Obtener telemetría propia
        telemetry = {}
        if self.get_telemetry_fn:
            try:
                telemetry = self.get_telemetry_fn()
            except Exception:
                pass

        # 2. Preparar payload de heartbeat
        self_candidates = get_self_network_candidates(self.port)
        auth = _get_auth_data()

        payload = {
            "node_id": auth.get("node_id"),
            "node_name": auth.get("node_name"),
            "platform": sys.platform,
            "port": self.port,
            "token": auth.get("token", ""),
            "cores": psutil.cpu_count(logical=True),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "endpoints": [c for c in self_candidates if "127.0.0.1" not in c and "localhost" not in c],
            "metrics": telemetry,
            "timestamp": time.time()
        }

        # 3. Descubrir peers de Tailscale dinámicamente si está disponible
        ts = get_tailscale_peers()
        for p_name, p_data in ts.get("peers", {}).items():
            if p_data.get("online"):
                for ip in p_data.get("ips", []):
                    _CONFIGURED_PEERS.add(f"http://{ip}:{self.port}")
                if p_data.get("dns"):
                    _CONFIGURED_PEERS.add(f"http://{p_data['dns']}:{self.port}")

        # 4. Enviar heartbeat a todos los peers configurados
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SentinelOS-Mesh-Heartbeat/2.0",
            "X-Sentinel-Token": auth.get("token", "")
        }

        for peer_base in list(_CONFIGURED_PEERS):
            if any(peer_base.rstrip("/") == c.rstrip("/") for c in self_candidates):
                continue
            try:
                hb_url = f"{peer_base}/api/mesh/heartbeat"
                req = urllib.request.Request(hb_url, data=data_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=1.8) as resp:
                    pass
            except Exception:
                pass

_GLOBAL_WORKER = None
_GLOBAL_BEACON_SENDER = None
_GLOBAL_BEACON_LISTENER = None

def start_mesh_engine(port: int = 8001, get_telemetry_fn=None) -> MeshSyncWorker:
    """Inicia el motor de malla completo: Reverse Heartbeat + LAN UDP Beacon + Subnet Scanner."""
    global _GLOBAL_WORKER, _GLOBAL_BEACON_SENDER, _GLOBAL_BEACON_LISTENER

    if _GLOBAL_WORKER is None:
        _GLOBAL_WORKER = MeshSyncWorker(port=port, get_telemetry_fn=get_telemetry_fn)
        _GLOBAL_WORKER.start()

    if _GLOBAL_BEACON_SENDER is None:
        _GLOBAL_BEACON_SENDER = LanBeaconSender(port=port)
        _GLOBAL_BEACON_SENDER.start()

    if _GLOBAL_BEACON_LISTENER is None:
        _GLOBAL_BEACON_LISTENER = LanBeaconListener(port=port)
        _GLOBAL_BEACON_LISTENER.start()

    return _GLOBAL_WORKER
