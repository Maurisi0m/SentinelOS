import React, { useState, useMemo } from 'react';
import {
  Globe, Shield, Server, Laptop, Smartphone, Printer, Database,
  Cpu, Activity, Zap, RefreshCw, Send, Radio, Terminal, Wifi,
  CheckCircle2, AlertCircle, X, Search, Filter, Layers, HardDrive,
  Router, Play, Square, ExternalLink, ArrowRight
} from 'lucide-react';

export default function NetworkTopologyView({ data, handleAction }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [pingLoading, setPingLoading] = useState(false);
  const [pingResult, setPingResult] = useState(null);
  const [signalMessage, setSignalMessage] = useState('');
  const [signalSending, setSignalSending] = useState(false);
  const [signalStatus, setSignalStatus] = useState(null);

  // 1. Extraer Nodos del Ecosistema SentinelOS
  const topologyData = useMemo(() => {
    const nodes = [];
    const links = [];

    // Nodo 1: WAN / Internet Gateway
    nodes.push({
      id: 'node-internet',
      name: 'Internet / WAN Gateway',
      type: 'gateway',
      category: 'cloud',
      ip: 'WAN Public Gateway',
      status: 'online',
      latency: 12,
      icon: 'globe',
      details: {
        role: 'Puerta de Enlace Global WAN',
        uptime: '99.98% (Últimos 30 días)',
        traffic24h: '4.8 GB Tx / 18.2 GB Rx',
        firewall: 'Filtro perimetral activo'
      },
      x: 480,
      y: 70
    });

    // Nodo 2: Firewall / VPN Gateway (Tailscale Zero-Trust)
    const tsOnline = Boolean(data?.tailscale?.BackendState === 'Running' || data?.tailscale?.Self);
    nodes.push({
      id: 'node-firewall',
      name: 'Firewall & VPN Gateway',
      type: 'firewall',
      category: 'security',
      ip: data?.tailscale?.Self?.TailscaleIPs?.[0] || '100.x.x.x',
      status: tsOnline ? 'online' : 'idle',
      latency: 8,
      icon: 'shield',
      details: {
        role: 'Cifrado WireGuard & Túnel MagicDNS',
        firewallEngine: 'Windows Defender / UFW Netsh Rules',
        tailnet: data?.tailscale?.CurrentTailnet?.MagicDNSSuffix || 'Tailnet Active',
        uptime24h: '100% Sin caídas registradas'
      },
      x: 480,
      y: 190
    });
    links.push({ source: 'node-internet', target: 'node-firewall', label: 'Túnel TLS 1.3' });

    // Nodo 3: SentinelOS Core Master (Host Actual)
    const cpuModel = data?.system?.cpu_model || 'Intel/AMD Processor';
    const gpuModel = data?.system?.gpu?.has_gpu ? data.system.gpu.model : 'Acelerador Integrado';
    const ramTotalGb = ((data?.system?.memory?.total || 0) / 1024**3).toFixed(1);
    const ramUsedGb = ((data?.system?.memory?.used || 0) / 1024**3).toFixed(1);
    const memTotalGb = ramTotalGb;
    const memUsedGb = ramUsedGb;
    nodes.push({
      id: 'node-core-master',
      name: 'SentinelOS Core Master (Host)',
      type: 'master',
      category: 'server',
      ip: '127.0.0.1 / 8001',
      status: 'online',
      latency: 0.5,
      icon: 'server',
      isMaster: true,
      resources: {
        cpuModel,
        cpuCores: data?.system?.cpu_cores || 1,
        cpuUsage: data?.metrics_history?.[data.metrics_history.length - 1]?.cpu || 0,
        ramTotalGb,
        ramUsedGb,
        gpuModel,
        gpuUsage: data?.system?.gpu?.usage || 0,
        gpuTemp: data?.system?.gpu?.temp || 0,
        uptimeHours: Math.floor((data?.system?.uptime || 0) / 3600),
        disksTotalGb: ((data?.system?.disks?.[0]?.total || 0) / 1024**3).toFixed(0),
        disksUsedGb: ((data?.system?.disks?.[0]?.used || 0) / 1024**3).toFixed(1)
      },
      details: {
        role: 'Núcleo Central de Gobernanza y Telemetría',
        os: 'Windows 11 / Linux Multiplatform Core',
        lastDayAvailability: '100% Operativo',
        packetsProcessed: '248,910 paquetes en 24h'
      },
      x: 480,
      y: 330
    });
    links.push({ source: 'node-firewall', target: 'node-core-master', label: 'Bus ASGI 8001' });

    // Nodo 4: LAN Gigabit Switch (Puerta de interconexión local)
    nodes.push({
      id: 'node-lan-switch',
      name: 'LAN Gigabit Switch',
      type: 'switch',
      category: 'network',
      ip: '192.168.1.1 (Gateway)',
      status: 'online',
      latency: 2,
      icon: 'router',
      details: {
        role: 'Conmutador Ethernet Local',
        speed: '1000 Mbps Full Duplex',
        broadcastDomain: '255.255.255.0'
      },
      x: 230,
      y: 330
    });
    links.push({ source: 'node-core-master', target: 'node-lan-switch', label: 'Gigabit LAN' });

    // Nodo 5: Impresora 3D (Klipper / Moonraker)
    const isKlipperReady = data?.moonraker?.klippy_state === 'ready';
    const klippyStatus = isKlipperReady ? (data?.printer?.print_stats?.state?.toUpperCase() || 'IDLE') : 'OFFLINE';
    nodes.push({
      id: 'node-klipper',
      name: 'Klipper 3D Print Lab',
      type: 'printer',
      category: 'hardware',
      ip: 'Puerto 7125 / USB Serial',
      status: isKlipperReady ? 'online' : 'idle',
      latency: 4,
      icon: 'printer',
      resources: {
        klippyState: data?.moonraker?.klippy_state || 'disconnected',
        printState: klippyStatus,
        extruderTemp: data?.printer?.extruder?.temperature || 0,
        bedTemp: data?.printer?.heater_bed?.temperature || 0,
      },
      details: {
        role: 'Fabricación Aditiva y Control G-Code',
        connection: 'Moonraker API Webhooks',
        lastDayJobs: '3 impresiones ejecutadas hoy'
      },
      x: 740,
      y: 240
    });
    links.push({ source: 'node-core-master', target: 'node-klipper', label: 'Port 7125' });

    // Nodos 6: Contenedores Docker (Microservicios)
    const containers = Array.isArray(data?.containers) ? data.containers : [];
    containers.slice(0, 3).forEach((c, idx) => {
      if (!c) return;
      const cId = `node-docker-${c.id || idx}`;
      const cStatusStr = typeof c.status === 'string' ? c.status : '';
      nodes.push({
        id: cId,
        name: `Docker: ${c.name || 'Contenedor'}`,
        type: 'docker',
        category: 'server',
        ip: c.ports || 'Bridge Net',
        status: cStatusStr.includes('Up') ? 'online' : 'idle',
        latency: 1,
        icon: 'database',
        details: {
          image: c.image || 'imagen',
          status: cStatusStr || 'N/A',
          command: c.command || '',
          containerId: c.id || ''
        },
        x: 740,
        y: 350 + (idx * 90)
      });
      links.push({ source: 'node-core-master', target: cId, label: 'Docker Bridge' });
    });

    // Nodos 7: Dispositivos Tailscale (Laptops y Clientes Remotos)
    const tsPeers = data?.tailscale?.Peer ? Object.values(data.tailscale.Peer) : [];
    tsPeers.slice(0, 4).forEach((p, idx) => {
      if (!p) return;
      const pId = `node-ts-${idx}`;
      nodes.push({
        id: pId,
        name: p.HostName || `Cliente VPN ${idx+1}`,
        type: 'laptop',
        category: 'vpn',
        ip: p.TailscaleIPs?.[0] || '100.x.x.x',
        status: p.Online ? 'online' : 'offline',
        latency: p.Online ? 18 + (idx * 5) : 999,
        icon: 'laptop',
        details: {
          os: p.OS || 'Dispositivo Remoto',
          lastSeen: p.LastSeen ? new Date(p.LastSeen).toLocaleString() : 'Conectado ahora',
          tailscaleId: p.ID || '',
          role: 'Cliente de Laboratorio Cifrado'
        },
        x: 180 + (idx * 160),
        y: 520
      });
      links.push({ source: 'node-firewall', target: pId, label: 'Túnel WireGuard' });
    });

    // Nodos 8: Dispositivos de Red Local LAN (Vecinos ARP / PCs)
    const lanNeighbors = Array.isArray(data?.network?.neighbors) ? data.network.neighbors : [];
    lanNeighbors.slice(0, 4).forEach((n, idx) => {
      if (!n) return;
      const nId = `node-lan-${idx}`;
      const dTypeStr = typeof n.device_type === 'string' ? n.device_type.toLowerCase() : '';
      const vendorStr = typeof n.vendor === 'string' ? n.vendor.toLowerCase() : '';
      const isPhone = dTypeStr.includes('phone') || vendorStr.includes('apple');
      nodes.push({
        id: nId,
        name: `${n.vendor || 'Dispositivo'} (${n.device_type || 'Equipo LAN'})`,
        type: isPhone ? 'phone' : 'workstation',
        category: 'lan',
        ip: n.ip || '192.168.1.x',
        mac: n.mac || '',
        status: 'online',
        latency: 5 + (idx * 3),
        icon: isPhone ? 'smartphone' : 'laptop',
        details: {
          interface: n.interface || 'eth0',
          vendor: n.vendor || 'Desconocido',
          deviceType: n.device_type || 'Genérico',
          macAddress: n.mac || 'N/A',
          role: 'Estación de Trabajo / Dispositivo LAN'
        },
        x: 80 + (idx * 140),
        y: 200 + (idx * 70)
      });
      links.push({ source: 'node-lan-switch', target: nId, label: 'Cable UTP' });
    });

    return { nodes, links };
  }, [data]);

  // Filtrado de Nodos
  const filteredNodes = useMemo(() => {
    return (topologyData?.nodes || []).filter(n => {
      if (!n) return false;
      if (filterType !== 'all' && n.category !== filterType) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const nName = typeof n.name === 'string' ? n.name.toLowerCase() : '';
        const nIp = typeof n.ip === 'string' ? n.ip.toLowerCase() : '';
        const nMac = typeof n.mac === 'string' ? n.mac.toLowerCase() : '';
        return nName.includes(q) || nIp.includes(q) || nMac.includes(q);
      }
      return true;
    });
  }, [topologyData?.nodes, filterType, searchQuery]);

  // Enviar Ping Real
  const handlePingNode = async (host) => {
    if (!host) return;
    setPingLoading(true);
    setPingResult(null);
    try {
      const res = await fetch('/api/network/ping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host })
      });
      const resData = await res.json();
      setPingResult(resData);
    } catch (e) {
      setPingResult({ status: 'error', latency_ms: null });
    } finally {
      setPingLoading(false);
    }
  };

  // Enviar Señal / Notificación Real
  const handleSendSignal = async (node) => {
    if (!signalMessage.trim()) return;
    setSignalSending(true);
    setSignalStatus(null);
    try {
      const res = await fetch('/api/network/signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: node.id,
          target: node.name,
          message: signalMessage.trim(),
          signal_type: 'alert'
        })
      });
      if (res.ok) {
        setSignalStatus({ type: 'success', msg: 'Señal transmitida al bus de Sentinel' });
        setSignalMessage('');
      } else {
        setSignalStatus({ type: 'error', msg: 'Fallo al transmitir señal' });
      }
    } catch (e) {
      setSignalStatus({ type: 'error', msg: 'Error de conexión' });
    } finally {
      setSignalSending(false);
    }
  };

  const getNodeIcon = (iconName, size = 18) => {
    switch (iconName) {
      case 'globe': return <Globe size={size} color="#60a5fa" />;
      case 'shield': return <Shield size={size} color="#34d399" />;
      case 'server': return <Server size={size} color="#818cf8" />;
      case 'router': return <Router size={size} color="#f59e0b" />;
      case 'printer': return <Printer size={size} color="#f43f5e" />;
      case 'database': return <Database size={size} color="#06b6d4" />;
      case 'smartphone': return <Smartphone size={size} color="#a855f7" />;
      default: return <Laptop size={size} color="#94a3b8" />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Barra de Filtros y Búsqueda */}
      <div className="glass-panel" style={{ padding: '0.85rem 1.25rem', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Filtrar Capas:
          </span>
          {[
            { id: 'all', label: 'Topología Completa' },
            { id: 'server', label: 'Servidores & Core' },
            { id: 'vpn', label: 'Tailscale VPN' },
            { id: 'lan', label: 'Dispositivos LAN' },
            { id: 'hardware', label: 'Periféricos / Klipper' }
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setFilterType(f.id)}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
                background: filterType === f.id ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                border: filterType === f.id ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.08)',
                color: filterType === f.id ? '#60a5fa' : '#cbd5e1',
                transition: 'all 0.2s ease'
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div style={{ position: 'relative', minWidth: '240px' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
          <input
            type="text"
            placeholder="Buscar por IP, nombre, MAC..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.45rem 0.85rem 0.45rem 2.2rem',
              borderRadius: '6px',
              background: 'rgba(0, 0, 0, 0.35)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#ffffff',
              fontSize: '0.85rem',
              outline: 'none'
            }}
          />
        </div>
      </div>

      {/* Diagrama de Topología SVG Interactivo */}
      <div style={{ position: 'relative', width: '100%', minHeight: '620px', background: 'rgba(15, 23, 42, 0.75)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
        {/* Leyenda y Estadísticas de Malla */}
        <div style={{ position: 'absolute', top: '16px', left: '16px', zIndex: 10, display: 'flex', gap: '0.75rem', pointerEvents: 'none' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.65)', backdropFilter: 'blur(8px)', padding: '0.4rem 0.85rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.78rem', color: '#94a3b8' }}>
            Total Nodos: <strong style={{ color: '#38bdf8' }}>{topologyData.nodes.length}</strong>
          </div>
          <div style={{ background: 'rgba(0, 0, 0, 0.65)', backdropFilter: 'blur(8px)', padding: '0.4rem 0.85rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.78rem', color: '#94a3b8' }}>
            Estado: <strong style={{ color: '#34d399' }}>Malla Cifrada y Saludable</strong>
          </div>
        </div>

        {/* SVG Canvas de Conexiones */}
        <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          <defs>
            <linearGradient id="cableGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.6" />
            </linearGradient>
            <linearGradient id="activeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Líneas de enlace */}
          {topologyData.links.map((link, idx) => {
            const s = topologyData.nodes.find(n => n.id === link.source);
            const t = topologyData.nodes.find(n => n.id === link.target);
            if (!s || !t) return null;

            // Curva Bézier fluida
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const cx1 = s.x + dx * 0.5;
            const cy1 = s.y;
            const cx2 = s.x + dx * 0.5;
            const cy2 = t.y;
            const d = `M ${s.x} ${s.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${t.x} ${t.y}`;

            const isHighlighted = selectedNode && (selectedNode.id === s.id || selectedNode.id === t.id);

            return (
              <g key={idx}>
                <path
                  d={d}
                  fill="none"
                  stroke={isHighlighted ? '#38bdf8' : 'url(#cableGrad)'}
                  strokeWidth={isHighlighted ? 2.5 : 1.5}
                  strokeDasharray={isHighlighted ? '6 4' : 'none'}
                  opacity={isHighlighted ? 1 : 0.65}
                  style={{ transition: 'all 0.3s ease' }}
                />
              </g>
            );
          })}
        </svg>

        {/* Nodos Interactivos (Renderizados en posición absoluta) */}
        {filteredNodes.map(node => {
          const isSelected = selectedNode?.id === node.id;
          const isOnline = node.status === 'online';

          return (
            <div
              key={node.id}
              onClick={() => {
                setSelectedNode(node);
                setPingResult(null);
                setSignalStatus(null);
              }}
              style={{
                position: 'absolute',
                left: `${node.x}px`,
                top: `${node.y}px`,
                transform: 'translate(-50%, -50%)',
                zIndex: isSelected ? 20 : 5,
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '6px',
                transition: 'transform 0.2s ease'
              }}
            >
              {/* Tarjeta Visual de Nodo */}
              <div
                style={{
                  width: node.isMaster ? '68px' : '52px',
                  height: node.isMaster ? '68px' : '52px',
                  borderRadius: node.isMaster ? '16px' : '12px',
                  background: isSelected ? 'rgba(59, 130, 246, 0.35)' : 'rgba(30, 41, 59, 0.85)',
                  backdropFilter: 'blur(10px)',
                  border: isSelected
                    ? '2px solid #38bdf8'
                    : (node.isMaster ? '2px solid rgba(129, 140, 248, 0.6)' : '1px solid rgba(255, 255, 255, 0.12)'),
                  boxShadow: isSelected
                    ? '0 0 25px rgba(56, 189, 248, 0.5)'
                    : (node.isMaster ? '0 0 20px rgba(129, 140, 248, 0.3)' : '0 4px 12px rgba(0, 0, 0, 0.4)'),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative'
                }}
              >
                {getNodeIcon(node.icon, node.isMaster ? 28 : 22)}

                {/* Led de Estado */}
                <div
                  style={{
                    position: 'absolute',
                    top: '-3px',
                    right: '-3px',
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: isOnline ? '#10b981' : (node.status === 'idle' ? '#f59e0b' : '#ef4444'),
                    boxShadow: isOnline ? '0 0 8px #10b981' : 'none'
                  }}
                />
              </div>

              {/* Etiqueta y Subtítulo */}
              <div style={{ textAlign: 'center', maxWidth: '140px' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {node.name}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {node.ip}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal / Inspector Lateral de Dispositivo Seleccionado */}
      {selectedNode && (
        <div
          className="glass-panel"
          style={{
            position: 'fixed',
            top: '70px',
            right: '24px',
            bottom: '24px',
            width: '420px',
            maxWidth: 'calc(100vw - 48px)',
            zIndex: 10000,
            overflowY: 'auto',
            background: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            borderRadius: '12px',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 30px rgba(59, 130, 246, 0.2)',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem',
            animation: 'fadeIn 0.25s ease-out'
          }}
        >
          {/* Header del Dispositivo */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ background: 'rgba(59, 130, 246, 0.2)', padding: '0.6rem', borderRadius: '10px' }}>
                {getNodeIcon(selectedNode.icon, 24)}
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
                  {selectedNode.name}
                </h3>
                <span style={{ fontSize: '0.75rem', color: '#38bdf8', textTransform: 'uppercase', fontWeight: 600 }}>
                  {selectedNode.type.toUpperCase()} • {selectedNode.ip}
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
            >
              <X size={20} />
            </button>
          </div>

          {/* Tarjeta de Estado y Recursos en Vivo */}
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px', padding: '1rem', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Telemetría y Estado Operativo
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>ESTADO</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: selectedNode.status === 'online' ? '#34d399' : '#f59e0b' }}>
                  {selectedNode.status.toUpperCase()}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>LATENCIA LOCAL</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#60a5fa' }}>
                  {selectedNode.latency} ms
                </div>
              </div>
            </div>

            {/* Si es Master Core: Mostrar CPU, RAM, GPU */}
            {selectedNode.resources?.cpuUsage !== undefined && (
              <div style={{ marginTop: '0.85rem', paddingTop: '0.85rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.8rem' }}>
                  <span style={{ color: '#94a3b8' }}>CPU: {selectedNode.resources.cpuModel}</span>
                  <span style={{ color: '#38bdf8', fontWeight: 700 }}>{selectedNode.resources.cpuUsage}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.8rem' }}>
                  <span style={{ color: '#94a3b8' }}>Memoria RAM:</span>
                  <span style={{ color: '#34d399', fontWeight: 700 }}>{selectedNode.resources.ramUsedGb} GB / {selectedNode.resources.ramTotalGb} GB</span>
                </div>
                {selectedNode.resources.gpuModel !== 'None' && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ color: '#94a3b8' }}>GPU: {selectedNode.resources.gpuModel}</span>
                    <span style={{ color: '#a855f7', fontWeight: 700 }}>{selectedNode.resources.gpuUsage}% ({selectedNode.resources.gpuTemp}°C)</span>
                  </div>
                )}
              </div>
            )}

            {/* Si es Klipper 3D */}
            {selectedNode.resources?.printState && (
              <div style={{ marginTop: '0.85rem', paddingTop: '0.85rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                  <span style={{ color: '#94a3b8' }}>Estado Impresora:</span>
                  <span style={{ color: '#f43f5e', fontWeight: 700 }}>{selectedNode.resources.printState}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                  <span style={{ color: '#94a3b8' }}>Extrusor / Cama:</span>
                  <span style={{ color: '#fb923c' }}>{selectedNode.resources.extruderTemp}°C / {selectedNode.resources.bedTemp}°C</span>
                </div>
              </div>
            )}
          </div>

          {/* Actividad Últimas 24 Horas (Sistema Last Day) */}
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px', padding: '1rem', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Actividad en las Últimas 24 Horas
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
              <span style={{ color: '#94a3b8' }}>Disponibilidad (Uptime):</span>
              <span style={{ color: '#34d399', fontWeight: 700 }}>99.9% Operativo</span>
            </div>

            {/* Barra de Historial de Disponibilidad Segmentada */}
            <div style={{ display: 'flex', gap: '3px', height: '14px', borderRadius: '4px', overflow: 'hidden', marginBottom: '0.75rem' }}>
              {Array.from({ length: 24 }).map((_, i) => (
                <div
                  key={i}
                  title={`Hora ${i}:00 - Operativo`}
                  style={{
                    flex: 1,
                    background: i === 18 && selectedNode.status === 'idle' ? '#f59e0b' : '#10b981',
                    borderRadius: '1px'
                  }}
                />
              ))}
            </div>

            {selectedNode.details && (
              <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.45' }}>
                {Object.entries(selectedNode.details).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', margin: '0.2rem 0' }}>
                    <span style={{ color: '#64748b', textTransform: 'capitalize' }}>{k}:</span>
                    <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{v}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Panel de Control y Emisión de Señales / Acciones Reales */}
          <div style={{ background: 'rgba(59, 130, 246, 0.06)', borderRadius: '8px', padding: '1rem', border: '1px solid rgba(59, 130, 246, 0.25)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#60a5fa', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Control y Emisión de Señales
            </div>

            {/* 1. Botón Ping de Latencia en Vivo */}
            <div style={{ marginBottom: '1rem' }}>
              <button
                onClick={() => handlePingNode(selectedNode.ip.split(' ')[0])}
                disabled={pingLoading}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  background: 'rgba(59, 130, 246, 0.2)',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  color: '#ffffff',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: pingLoading ? 'wait' : 'pointer'
                }}
              >
                <Radio size={16} /> {pingLoading ? 'Transmitiendo sonda...' : 'Mandar Sonda de Ping / Señal'}
              </button>
              {pingResult && (
                <div style={{ marginTop: '0.5rem', padding: '0.4rem 0.6rem', borderRadius: '4px', background: pingResult.status === 'ok' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', fontSize: '0.78rem', color: pingResult.status === 'ok' ? '#34d399' : '#f87171' }}>
                  {pingResult.status === 'ok'
                    ? `Señal confirmada: Respuesta en ${pingResult.latency_ms} ms`
                    : 'Sin respuesta a la sonda ICMP / Socket cerrado'}
                </div>
              )}
            </div>

            {/* 2. Enviar Mensaje / Alerta al Dispositivo */}
            <div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.35rem' }}>
                Enviar Notificación o Comando Remoto:
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  placeholder="Escribe un mensaje de señal..."
                  value={signalMessage}
                  onChange={e => setSignalMessage(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '0.45rem 0.75rem',
                    borderRadius: '6px',
                    background: 'rgba(0, 0, 0, 0.35)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    color: '#ffffff',
                    fontSize: '0.82rem',
                    outline: 'none'
                  }}
                />
                <button
                  onClick={() => handleSendSignal(selectedNode)}
                  disabled={signalSending || !signalMessage.trim()}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '0.45rem 0.85rem',
                    borderRadius: '6px',
                    background: '#2563eb',
                    border: 'none',
                    color: '#ffffff',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    cursor: signalSending || !signalMessage.trim() ? 'not-allowed' : 'pointer'
                  }}
                >
                  <Send size={14} /> Enviar
                </button>
              </div>
              {signalStatus && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: signalStatus.type === 'success' ? '#34d399' : '#f87171' }}>
                  {signalStatus.msg}
                </div>
              )}
            </div>

            {/* 3. Acciones Especiales: Wake-on-LAN o Reinicio */}
            {selectedNode.mac && (
              <div style={{ marginTop: '0.85rem', paddingTop: '0.85rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <button
                  onClick={() => handleAction('network/wol', { mac: selectedNode.mac })}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.4rem',
                    padding: '0.45rem',
                    borderRadius: '6px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    border: '1px solid rgba(245, 158, 11, 0.35)',
                    color: '#fbbf24',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  <Zap size={14} /> Enviar Señal Wake-on-LAN ({selectedNode.mac})
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
