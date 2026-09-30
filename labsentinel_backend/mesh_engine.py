# -*- coding: utf-8 -*-
"""
SENTINEL OS - MESH ENGINE (Autonomous Self-Healing Network Bridge)
Garantiza conectividad continua y resiliente entre todos los nodos Sentinel:
1. Multi-Path Auto-Resolver: Si una IP (LAN o Tailscale) falla o está bloqueada por firewall,
   conmuta automáticamente a candidatos alternativos (Tailscale IP, MagicDNS, LAN IP, mDNS).
2. Reverse Push Telemetry: Si los puertos entrantes están bloqueados (ej. Windows Defender Firewall),
   el nodo empuja su telemetría hacia los peers por conexiones salientes (outbound),
   eliminando cualquier bloqueo de firewall o aislamiento AP.
3. Tailscale Cross-Bridge: Descubre peers de Tailscale automáticamente y los puentea
   para clientes o navegadores que no tienen Tailscale instalado.
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
import psutil

# Registro en memoria de nodos de la malla
_MESH_LOCK = threading.Lock()
_MESH_NODES = {}          # node_id -> { info, metrics, last_seen, active_url, candidates }
_CONFIGURED_PEERS = set() # URLs de peers a los que enviar telemetría saliente
_TS_CACHE = {"data": {}, "time": 0.0}

def get_tailscale_peers() -> dict:
    """Obtiene la lista de peers y auto-información de Tailscale de forma ultra-rápida (en caché por 5s)."""
    global _TS_CACHE
    now = time.time()
    if now - _TS_CACHE["time"] < 5.0 and _TS_CACHE["data"]:
        return _TS_CACHE["data"]

    result = {"self": {}, "peers": {}, "map_by_ip": {}, "map_by_name": {}}
    try:
        cmd = ["tailscale", "status", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2.5)
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
    """Descubre todas las URLs alcanzables para este nodo (LAN, Wi-Fi, Tailscale, mDNS)."""
    candidates = []
    seen = set()

    def add_url(u):
        u = u.strip().rstrip("/")
        if u and u not in seen:
            seen.add(u)
            candidates.append(u)

    # 1. Tailscale IP y DNS
    ts = get_tailscale_peers().get("self", {})
    for tip in ts.get("ips", []):
        if ":" not in tip:
            add_url(f"http://{tip}:{port}")
        else:
            add_url(f"http://[{tip}]:{port}")
    if ts.get("dns"):
        add_url(f"http://{ts['dns']}:{port}")

    # 2. Interfaces LAN y Wi-Fi de psutil
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if a.family == socket.AF_INET:
                    ip = a.address
                    if ip != "127.0.0.1" and not ip.startswith("169.254."):
                        add_url(f"http://{ip}:{port}")
    except Exception:
        pass

    # 3. Hostname y mDNS
    try:
        h = socket.gethostname()
        if h:
            add_url(f"http://{h}:{port}")
            add_url(f"http://{h}.local:{port}")
    except Exception:
        pass

    return candidates

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
            "data": payload.get("data") or payload.get("metrics") or {}
        }
    return {"status": "ok", "node_id": node_id, "timestamp": now}

def get_mesh_nodes() -> list[dict]:
    """Retorna la lista de todos los nodos conocidos y su estado actual."""
    now = time.time()
    nodes = []
    with _MESH_LOCK:
        for nid, info in list(_MESH_NODES.items()):
            is_active = (now - info.get("last_seen", 0)) < 40.0
            nodes.append({
                **info,
                "status": "online" if is_active else "offline"
            })
    return nodes

def get_candidate_urls_for_target(target_url: str) -> list[str]:
    """
    Dada una URL que falló (ej. http://192.168.68.73:8001/api/data),
    encuentra todas las rutas alternativas viables (Tailscale, LAN, mDNS).
    """
    try:
        parsed = urllib.parse.urlparse(target_url)
        host = parsed.hostname or ""
        port = parsed.port or 8001
        path = parsed.path or "/"
        query = f"?{parsed.query}" if parsed.query else ""
    except Exception:
        return [target_url]

    candidates = [target_url]
    host_lower = host.lower()

    # 1. Buscar en MESH_NODES si alguna máquina registrada tiene esta IP o nombre
    with _MESH_LOCK:
        for nid, n in _MESH_NODES.items():
            names_to_match = [nid.lower(), n.get("node_name", "").lower()]
            match = any(host_lower in nm or nm in host_lower for nm in names_to_match)
            if not match:
                for c in n.get("candidates", []):
                    if host_lower in c.lower():
                        match = True
                        break
            if match:
                for c in n.get("candidates", []):
                    c_clean = c.rstrip("/")
                    full_alt = f"{c_clean}{path}{query}"
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

    # 3. Intentar mDNS (.local) si el host no es ya una IP
    if not any(c.isdigit() for c in host.split(".")):
        alt = f"http://{host}.local:{port}{path}{query}"
        if alt not in candidates:
            candidates.append(alt)

    return candidates

def smart_proxy_fetch(target_url: str, headers: dict = None, timeout: float = 3.0) -> tuple[dict, str]:
    """
    Intenta obtener respuesta de target_url. Si falla por timeout, firewall o red,
    itera instantáneamente sobre todas las rutas alternativas (Tailscale, LAN, MagicDNS)
    hasta conseguir respuesta exitosa.
    """
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
                    # Si funcionó una ruta alternativa, registrarla en MESH_NODES
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

    # Si todas las rutas de red fallaron, comprobar si el path es de telemetría y tenemos datos del reverse heartbeat
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

class MeshSyncWorker(threading.Thread):
    """
    Hilo en segundo plano autónomo que:
    1. Envía periódicamente telemetría saliente (heartbeat) a peers conocidos (evitando firewalls entrantes).
    2. Descubre nuevos peers en Tailscale y los sincroniza.
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

    def run(self):
        time.sleep(2.0)
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
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        auth_file = os.path.join(root_dir, "config", "node_auth.json")
        auth_data = {}
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    auth_data = json.load(f)
            except Exception:
                pass

        node_id = auth_data.get("node_id", f"node-{socket.gethostname()}")
        node_name = auth_data.get("node_name", socket.gethostname())
        token = auth_data.get("token", "")

        payload = {
            "node_id": node_id,
            "node_name": node_name,
            "platform": sys.platform,
            "port": self.port,
            "token": token,
            "cores": psutil.cpu_count(logical=True),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "endpoints": self_candidates,
            "metrics": telemetry,
            "timestamp": time.time()
        }

        # 3. Descubrir peers de Tailscale dinámicamente
        ts = get_tailscale_peers()
        for p_name, p_data in ts.get("peers", {}).items():
            if p_data.get("online"):
                for ip in p_data.get("ips", []):
                    _CONFIGURED_PEERS.add(f"http://{ip}:{self.port}")
                if p_data.get("dns"):
                    _CONFIGURED_PEERS.add(f"http://{p_data['dns']}:{self.port}")

        # 4. Enviar heartbeat a todos los peers
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SentinelOS-Mesh-Heartbeat/2.0",
            "X-Sentinel-Token": token
        }

        for peer_base in list(_CONFIGURED_PEERS):
            # No enviarse a uno mismo
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

def start_mesh_engine(port: int = 8001, get_telemetry_fn=None) -> MeshSyncWorker:
    global _GLOBAL_WORKER
    if _GLOBAL_WORKER is None:
        _GLOBAL_WORKER = MeshSyncWorker(port=port, get_telemetry_fn=get_telemetry_fn)
        _GLOBAL_WORKER.start()
    return _GLOBAL_WORKER
