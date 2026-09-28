import React, { useState, useMemo } from 'react';
import {
  Globe, Shield, Server, Laptop, Smartphone, Printer, Database,
  Cpu, Activity, Zap, RefreshCw, Send, Radio, Terminal, Wifi,
  CheckCircle2, AlertCircle, X, Search, Filter, Layers, HardDrive,
  Router, Play, Square, ExternalLink, ArrowRight, Cable
} from 'lucide-react';

export default function NetworkTopologyView({ data, handleAction, connectedServers = [] }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [pingLoading, setPingLoading] = useState(false);
  const [pingResult, setPingResult] = useState(null);
  const [signalMessage, setSignalMessage] = useState('');
  const [signalSending, setSignalSending] = useState(false);
  const [signalStatus, setSignalStatus] = useState(null);

  // 1. Extraer Topología Real del Ecosistema SentinelOS
  const topologyData = useMemo(() => {
    const nodes = [];
    const links = [];

    // Detectar Interfaz de Red Primaria Real del Host
    const primaryNet = data?.network?.primary || {
      name: 'Ethernet',
      type: 'ethernet',
      speed: 1000,
      ip: '127.0.0.1',
      mac: ''
    };
    const isWifi = primaryNet.type === 'wifi';
    const ifaceSpeed = primaryNet.speed ? `${primaryNet.speed} Mbps` : 'Activa';

    // Nodo Central 1: Host Local / Nodo Maestro
    const cpuModel = data?.system?.cpu_model || 'Intel/AMD Processor';
    const gpuModel = data?.system?.gpu?.has_gpu ? data.system.gpu.model : 'Acelerador Integrado';
    const ramTotalGb = ((data?.system?.memory?.total || 0) / 1024**3).toFixed(1);
    const ramUsedGb = ((data?.system?.memory?.used || 0) / 1024**3).toFixed(1);

    nodes.push({
      id: 'node-core-master',
      name: data?.system?.node_name || 'Nodo Maestro (Host)',
      type: 'master',
      category: 'server',
      ip: primaryNet.ip || '127.0.0.1',
      mac: primaryNet.mac || '',
      status: 'online',
      latency: 0.2,
      icon: isWifi ? 'wifi' : 'server',
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
        interfazFisica: `${primaryNet.name} (${ifaceSpeed})`,
        tipoConexion: isWifi ? 'Inalámbrica Wi-Fi 802.11' : 'Cableada Ethernet Gigabit',
        direccionMAC: primaryNet.mac || 'N/A',
        uptime: `${Math.floor((data?.system?.uptime || 0) / 3600)} horas activas`
      },
      x: 480,
      y: 280
    });

    // 2. Servidores Remotos Conectados Permanentemente
    const remoteServers = (connectedServers || []).filter(s => !s.isLocal);
    remoteServers.forEach((srv, idx) => {
      const srvId = `node-srv-${srv.id || idx}`;
      const isTs = srv.url?.includes('100.') || srv.url?.includes('.ts.net');
      const isLan = srv.url?.includes('192.168.') || srv.url?.includes('10.') || srv.url?.includes('172.');
      const connLabel = isTs ? 'Túnel WireGuard VPN' : (isLan ? 'Enlace Directo LAN' : 'Enlace Seguro WAN');

      const yOffset = 180 + (idx * 110);
      nodes.push({
        id: srvId,
        name: srv.name || `Servidor Remoto ${idx + 1}`,
        type: 'remote_server',
        category: 'server',
        ip: srv.url || srv.ip || 'Host Remoto',
        status: srv.status || 'online',
        latency: srv.latency || (isTs ? 14 : 4),
        icon: isTs ? 'shield' : 'server',
        details: {
          role: 'Servidor Satélite Vinculado',
          tipoConexion: connLabel,
          endpoint: srv.url || 'http://...',
          estadoAuth: srv.token ? 'Token de Acceso Verificado' : 'Sin Token'
        },
        x: 760,
        y: yOffset
      });

      links.push({
        source: 'node-core-master',
        target: srvId,
        label: isTs ? 'WireGuard Mesh' : 'Ethernet / LAN'
      });
    });

    // 3. Red Mesh Tailscale Zero-Trust (Solo si está activo)
    const tsRunning = Boolean(data?.tailscale?.BackendState === 'Running' || data?.tailscale?.Self);
    if (tsRunning) {
      const selfTs = data?.tailscale?.Self;
      const tsIp = selfTs?.TailscaleIPs?.[0] || '100.x.x.x';

      nodes.push({
        id: 'node-tailscale-gateway',
        name: 'Túnel Tailscale Zero-Trust',
        type: 'firewall',
        category: 'vpn',
        ip: tsIp,
        status: 'online',
        latency: 6,
        icon: 'shield',
        details: {
          role: 'Malla VPN Cifrada WireGuard',
          tailnet: data?.tailscale?.CurrentTailnet?.MagicDNSSuffix || 'Tailnet Activo',
          magicDNS: selfTs?.DNSName || 'DNS Seguro',
          estadoBackend: data?.tailscale?.BackendState || 'Running'
        },
        x: 480,
        y: 100
      });
      links.push({
        source: 'node-core-master',
        target: 'node-tailscale-gateway',
        label: 'Túnel Seguro WireGuard'
      });

      // Peers de Tailscale Reales (Máquinas del usuario)
      const peers = data?.tailscale?.Peer ? Object.values(data.tailscale.Peer) : [];
      peers.slice(0, 3).forEach((p, idx) => {
        if (!p) return;
        const pId = `node-ts-peer-${idx}`;
        const isOnline = Boolean(p.Online);
        const pIp = p.TailscaleIPs?.[0] || '100.x.x.x';
        const dType = (p.OS || '').toLowerCase();
        const isMobile = dType.includes('ios') || dType.includes('android');

        nodes.push({
          id: pId,
          name: p.HostName || `Cliente ${p.OS || 'VPN'}`,
          type: isMobile ? 'smartphone' : 'laptop',
          category: 'vpn',
          ip: pIp,
          status: isOnline ? 'online' : 'offline',
          latency: isOnline ? 18 + (idx * 6) : 999,
          icon: isMobile ? 'smartphone' : 'laptop',
          details: {
            role: 'Dispositivo Vinculado en Malla',
            sistemaOperativo: p.OS || 'Desconocido',
            ultimoAcceso: p.LastSeen ? new Date(p.LastSeen).toLocaleString() : 'Conectado ahora',
            enlace: 'Zero-Trust WireGuard'
          },
          x: 200 + (idx * 280),
          y: 30
        });
        links.push({
          source: 'node-tailscale-gateway',
          target: pId,
          label: 'WireGuard'
        });
      });
    }

    // 4. Dispositivos Reales de Red Local LAN (Descubiertos vía ARP)
    const lanNeighbors = Array.isArray(data?.network?.neighbors) ? data.network.neighbors : [];
    lanNeighbors.slice(0, 4).forEach((n, idx) => {
      if (!n || !n.ip) return;
      const nId = `node-lan-real-${idx}`;
      const dTypeStr = typeof n.device_type === 'string' ? n.device_type.toLowerCase() : '';
      const vendorStr = typeof n.vendor === 'string' ? n.vendor.toLowerCase() : '';
      const isPhone = dTypeStr.includes('phone') || vendorStr.includes('apple') || vendorStr.includes('samsung');

      nodes.push({
        id: nId,
        name: `${n.vendor && n.vendor !== 'Desconocido' ? n.vendor : 'Equipo'} (${n.device_type || 'LAN'})`,
        type: isPhone ? 'phone' : 'workstation',
        category: 'lan',
        ip: n.ip,
        mac: n.mac || '',
        status: 'online',
        latency: 4 + (idx * 2),
        icon: isPhone ? 'smartphone' : 'laptop',
        details: {
          role: 'Dispositivo en Subred Local',
          interfaz: n.interface || primaryNet.name,
          fabricante: n.vendor || 'Dispositivo de Red',
          direccionMAC: n.mac || 'N/A',
          medioFisico: isWifi ? 'Wi-Fi Local' : 'Ethernet UTP'
        },
        x: 180,
        y: 200 + (idx * 90)
      });
      links.push({
        source: 'node-core-master',
        target: nId,
        label: isWifi ? 'Wi-Fi LAN' : 'Ethernet LAN'
      });
    });

    // 5. Contenedores Docker Reales (Solo si existen contenedores reales activos)
    const containers = Array.isArray(data?.containers) ? data.containers : [];
    containers.slice(0, 2).forEach((c, idx) => {
      if (!c) return;
      const cId = `node-docker-${c.id || idx}`;
      const cStatusStr = typeof c.status === 'string' ? c.status : '';
      nodes.push({
        id: cId,
        name: `Docker: ${c.name || 'Contenedor'}`,
        type: 'docker',
        category: 'server',
        ip: c.ports || 'Bridge Local',
        status: cStatusStr.includes('Up') ? 'online' : 'idle',
        latency: 0.5,
        icon: 'database',
        details: {
          role: 'Servicio Contenerizado',
          imagen: c.image || 'imagen',
          estado: cStatusStr || 'N/A',
          puertos: c.ports || 'Bridge Net'
        },
        x: 480 + (idx * 160),
        y: 470
      });
      links.push({
        source: 'node-core-master',
        target: cId,
        label: 'Docker Socket'
      });
    });

    // 6. Klipper 3D Printer: Solo se agrega si el usuario lo tiene instalado y activo
    const isKlipperReady = data?.moonraker?.klippy_state === 'ready';
    if (isKlipperReady) {
      const klippyStatus = data?.printer?.print_stats?.state?.toUpperCase() || 'READY';
      nodes.push({
        id: 'node-klipper-ready',
        name: 'Laboratorio Klipper 3D',
        type: 'printer',
        category: 'hardware',
        ip: 'Puerto 7125 / USB Serial',
        status: 'online',
        latency: 2,
        icon: 'printer',
        resources: {
          klippyState: 'ready',
          printState: klippyStatus,
          extruderTemp: data?.printer?.extruder?.temperature || 0,
          bedTemp: data?.printer?.heater_bed?.temperature || 0,
        },
        details: {
          role: 'Fabricación Aditiva y Control G-Code',
          conexion: 'Moonraker API Webhooks',
          estadoKlippy: klippyStatus
        },
        x: 760,
        y: 390
      });
      links.push({
        source: 'node-core-master',
        target: 'node-klipper-ready',
        label: 'Moonraker API 7125'
      });
    }

    return { nodes, links, isKlipperReady };
  }, [data, connectedServers]);

  // Filtrado de Nodos Activos
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

  // Acciones en Vivo: Ping
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

  // Enviar Señal en Vivo
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
        setSignalStatus({ type: 'success', msg: 'Señal transmitida exitosamente' });
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
      case 'wifi': return <Wifi size={size} color="#06b6d4" />;
      case 'shield': return <Shield size={size} color="#34d399" />;
      case 'server': return <Server size={size} color="#818cf8" />;
      case 'router': return <Router size={size} color="#f59e0b" />;
      case 'printer': return <Printer size={size} color="#f43f5e" />;
      case 'database': return <Database size={size} color="#06b6d4" />;
      case 'smartphone': return <Smartphone size={size} color="#a855f7" />;
      default: return <Laptop size={size} color="#94a3b8" />;
    }
  };

  // Categorías dinámicas disponibles
  const availableFilterCategories = useMemo(() => {
    const list = [
      { id: 'all', label: 'Topología Completa' },
      { id: 'server', label: 'Servidores & Core' }
    ];
    const hasVpn = topologyData.nodes.some(n => n.category === 'vpn');
    if (hasVpn) list.push({ id: 'vpn', label: 'Tailscale VPN' });

    const hasLan = topologyData.nodes.some(n => n.category === 'lan');
    if (hasLan) list.push({ id: 'lan', label: 'Dispositivos LAN' });

    if (topologyData.isKlipperReady) {
      list.push({ id: 'hardware', label: 'Periféricos 3D' });
    }
    return list;
  }, [topologyData]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Barra de Filtros y Búsqueda */}
      <div className="glass-panel" style={{ padding: '0.85rem 1.25rem', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Filtrar Capas:
          </span>
          {availableFilterCategories.map(f => (
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
      <div style={{ position: 'relative', width: '100%', minHeight: '580px', background: 'rgba(15, 23, 42, 0.75)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
        {/* Leyenda y Estadísticas de Malla */}
        <div style={{ position: 'absolute', top: '16px', left: '16px', zIndex: 10, display: 'flex', gap: '0.75rem', pointerEvents: 'none' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.65)', backdropFilter: 'blur(8px)', padding: '0.4rem 0.85rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.78rem', color: '#94a3b8' }}>
            Nodos Activos: <strong style={{ color: '#38bdf8' }}>{topologyData.nodes.length}</strong>
          </div>
          <div style={{ background: 'rgba(0, 0, 0, 0.65)', backdropFilter: 'blur(8px)', padding: '0.4rem 0.85rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.78rem', color: '#94a3b8' }}>
            Interfaz Host: <strong style={{ color: '#34d399' }}>{data?.network?.primary?.name || 'Ethernet'} ({data?.network?.primary?.speed || 1000} Mbps)</strong>
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

        {/* Nodos Interactivos */}
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

      {/* Inspector Lateral de Dispositivo Seleccionado */}
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

          {/* Detalles de Conexión del Dispositivo */}
          {selectedNode.details && (
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px', padding: '1rem', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Propiedades de Red
              </div>
              <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.45' }}>
                {Object.entries(selectedNode.details).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', margin: '0.3rem 0' }}>
                    <span style={{ color: '#64748b', textTransform: 'capitalize' }}>{k.replace(/([A-Z])/g, ' $1')}:</span>
                    <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Panel de Control y Emisión de Señales / Acciones Reales */}
          <div style={{ background: 'rgba(59, 130, 246, 0.06)', borderRadius: '8px', padding: '1rem', border: '1px solid rgba(59, 130, 246, 0.25)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#60a5fa', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Control y Emisión de Señales
            </div>

            {/* Botón Ping de Latencia en Vivo */}
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

            {/* Enviar Notificación o Comando Remoto */}
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

            {/* Acciones Especiales: Wake-on-LAN */}
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
