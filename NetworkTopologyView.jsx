import React, { useState, useMemo } from 'react';
import {
  Globe, Shield, Server, Laptop, Smartphone, Printer, Database,
  Cpu, Activity, Zap, RefreshCw, Send, Radio, Terminal, Wifi,
  CheckCircle2, AlertCircle, X, Search, Filter, Layers, HardDrive,
  Router, Play, Square, ExternalLink, ArrowRight, Cable, ArrowUpRight,
  WifiOff, Disc
} from 'lucide-react';

export default function NetworkTopologyView({ data, handleAction, connectedServers = [], remoteServersData = {} }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [pingLoading, setPingLoading] = useState(false);
  const [pingResult, setPingResult] = useState(null);

  // 1. Construir Topología Completa de Red
  const topologyData = useMemo(() => {
    const nodes = [];
    const links = [];

    // Gateway / Router LAN Central
    const primaryNet = data?.network?.primary || {
      name: 'Ethernet',
      type: 'ethernet',
      speed: 1000,
      ip: '127.0.0.1',
      mac: ''
    };

    // Calcular IP estimada de Gateway a partir de la IP local
    let gatewayIp = '192.168.1.1';
    if (primaryNet.ip && primaryNet.ip.includes('.')) {
      const parts = primaryNet.ip.split('.');
      if (parts.length === 4) {
        gatewayIp = `${parts[0]}.${parts[1]}.${parts[2]}.1`;
      }
    }

    // NODO 0: Router / Gateway WiFi / Switch LAN Principal
    const routerId = 'node-gateway-router';
    nodes.push({
      id: routerId,
      name: 'Gateway / Router Principal',
      type: 'router',
      category: 'infrastructure',
      ip: gatewayIp,
      mac: 'E8:48:B8:C0:01:A2',
      status: 'online',
      latency: 0.8,
      icon: 'router',
      medium: 'infrastructure',
      details: {
        role: 'Puerta de Enlace Predeterminada, Conmutador LAN y Punto de Acceso Wi-Fi 6',
        ip: gatewayIp,
        subnet: '255.255.255.0 (/24)',
        servicios: 'DHCP Server, DNS Cache, NAT Firewall, Wi-Fi 802.11ax MIMO, Switch Gigabit',
        estado: 'Enrutamiento activo y estable'
      },
      x: 500,
      y: 90
    });

    // NODO 1: Host Local / Nodo Maestro (Laptop / Workstation)
    const isMasterWifi = primaryNet.type === 'wifi' ||
      primaryNet.name.toLowerCase().includes('wi-fi') ||
      primaryNet.name.toLowerCase().includes('wlan');
    const masterMedium = isMasterWifi ? 'wifi' : 'ethernet';
    const masterSpeed = primaryNet.speed ? `${primaryNet.speed} Mbps` : (isMasterWifi ? '866 Mbps' : '1000 Mbps');

    const cpuModel = data?.system?.cpu_model || 'Intel/AMD Core Processor';
    const gpuModel = data?.system?.gpu?.has_gpu ? data.system.gpu.model : 'Gráficos Integrados';
    const ramTotalGb = ((data?.system?.memory?.total || 0) / 1024**3).toFixed(1);
    const ramUsedGb = ((data?.system?.memory?.used || 0) / 1024**3).toFixed(1);

    const masterId = 'node-core-master';
    nodes.push({
      id: masterId,
      name: data?.system?.node_name || 'Nodo Maestro (Host)',
      type: 'master',
      category: 'server',
      ip: primaryNet.ip || '127.0.0.1',
      mac: primaryNet.mac || 'N/A',
      status: 'online',
      latency: 0.2,
      icon: isMasterWifi ? 'wifi' : 'server',
      isMaster: true,
      medium: masterMedium,
      resources: {
        cpuModel,
        cpuCores: data?.system?.cpu_cores || 4,
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
        role: 'Panel Maestro de Control, Telemetría y Gobierno',
        sistemaOperativo: data?.system?.platform ? `${data.system.platform}` : 'Host Principal',
        interfazFisica: `${primaryNet.name} (${masterSpeed})`,
        tipoConexion: isMasterWifi ? 'Inalámbrica Wi-Fi 802.11 (5 GHz / 2.4 GHz)' : 'Cableada Ethernet RJ-45 (1 Gbps Full-Duplex)',
        direccionMAC: primaryNet.mac || 'N/A',
        uptime: `${Math.floor((data?.system?.uptime || 0) / 3600)} horas activas`
      },
      x: 320,
      y: 270
    });

    // Enlace Router -> Maestro
    links.push({
      source: routerId,
      target: masterId,
      type: masterMedium,
      label: isMasterWifi ? 'Wi-Fi (Inalámbrico)' : 'Ethernet RJ-45 (1 Gbps)',
      speed: masterSpeed
    });

    // NODO 2: Servidores Remotos Vinculados (e.g. Servidor HP ProLiant, etc.)
    const remoteServers = (connectedServers || []).filter(s => !s.isLocal);
    
    remoteServers.forEach((srv, idx) => {
      const srvId = `node-srv-${srv.id || idx}`;
      const rData = remoteServersData[srv.id]?.data || {};
      const rNet = rData?.network?.primary || {};
      
      // Determinar si el servidor remoto está conectado por Ethernet o Wi-Fi
      const rNetType = (rNet.type || '').toLowerCase();
      const rNetName = (rNet.name || '').toLowerCase();
      const isSrvWifi = rNetType === 'wifi' || rNetName.includes('wl') || rNetName.includes('wifi') || rNetName.includes('wireless');
      const srvMedium = isSrvWifi ? 'wifi' : 'ethernet';
      const srvSpeed = rNet.speed ? `${rNet.speed} Mbps` : (isSrvWifi ? '300 Mbps' : '1000 Mbps');

      const isTs = (srv.url || '').includes('100.') || (srv.url || '').includes('.ts.net');
      const isOnline = remoteServersData[srv.id]?.status === 'online' || srv.status === 'online';

      const srvCpuModel = rData?.system?.cpu_model || 'Intel Xeon / Core Multi-Core';
      const srvCores = rData?.system?.cpu_cores || 8;
      const srvRamTotalGb = rData?.system?.memory?.total ? (rData.system.memory.total / 1024**3).toFixed(1) : '15.6';
      const srvRamUsedGb = rData?.system?.memory?.used ? (rData.system.memory.used / 1024**3).toFixed(1) : '3.2';
      const srvCpuUsage = rData?.metrics_history?.[rData.metrics_history.length - 1]?.cpu || 0;

      // Posicionamiento inteligente y equilibrado para 1, 2 o múltiples servidores
      const remoteCount = connectedServers.filter(s => !s.isLocal).length;
      let xPos, yPos;
      if (remoteCount <= 1) {
        xPos = 740;
        yPos = 280;
      } else if (remoteCount === 2) {
        xPos = 740;
        yPos = idx === 0 ? 190 : 420;
      } else {
        const col = idx % 2;
        const row = Math.floor(idx / 2);
        xPos = 700 + (col * 240);
        yPos = 180 + (row * 210);
      }

      nodes.push({
        id: srvId,
        name: srv.name || `Servidor Remoto ${idx + 1}`,
        type: 'remote_server',
        category: 'server',
        ip: srv.url ? srv.url.replace(/^https?:\/\//, '').replace(/:[0-9]+.*$/, '') : (rNet.ip || '192.168.1.150'),
        mac: rNet.mac || 'N/A',
        status: isOnline ? 'online' : 'offline',
        latency: srv.latency || (isTs ? 12 : 1.8),
        icon: 'server',
        medium: srvMedium,
        resources: {
          cpuModel: srvCpuModel,
          cpuCores: srvCores,
          cpuUsage: srvCpuUsage,
          ramTotalGb: srvRamTotalGb,
          ramUsedGb: srvRamUsedGb,
          uptimeHours: Math.floor((rData?.system?.uptime || 7200) / 3600),
          containersCount: Array.isArray(rData?.containers) ? rData.containers.length : 0
        },
        details: {
          role: 'Servidor Dedicado / Satélite de Laboratorio 24/7',
          servidor: srv.name,
          endpoint: srv.url || 'Conexión Directa LAN',
          interfazFisica: `${rNet.name || 'eth0'} (${srvSpeed})`,
          tipoConexion: isSrvWifi ? 'Inalámbrica Wi-Fi Local' : 'Cableada Ethernet UTP Cat6 Gigabit (LAN)',
          direccionMAC: rNet.mac || 'N/A',
          enlaceSeguro: isTs ? 'Túnel Cifrado WireGuard Mesh (Tailscale)' : 'Enlace Directo de Alta Velocidad LAN'
        },
        x: xPos,
        y: yPos
      });

      // Enlace 1: Conexión física hacia el Router/Gateway LAN
      links.push({
        source: routerId,
        target: srvId,
        type: srvMedium,
        label: isSrvWifi ? 'Wi-Fi LAN' : 'Ethernet Gigabit LAN',
        speed: srvSpeed
      });

      // Enlace 2: Enlace lógico Maestro <-> Servidor Satélite
      links.push({
        source: masterId,
        target: srvId,
        type: isTs ? 'wireguard' : 'peer',
        label: isTs ? 'WireGuard Zero-Trust' : 'Cluster Interconnect',
        speed: isTs ? 'Cifrado E2E' : 'Baja Latencia'
      });

      // Contenedores del Servidor Remoto (si existen)
      const srvContainers = Array.isArray(rData?.containers) ? rData.containers : [];
      srvContainers.slice(0, 3).forEach((c, cIdx) => {
        const cId = `node-srv-${srv.id}-docker-${cIdx}`;
        nodes.push({
          id: cId,
          name: `Docker: ${c.name || 'Contenedor'}`,
          type: 'docker',
          category: 'server',
          ip: c.ports || 'Bridge',
          status: (c.status || '').includes('Up') ? 'online' : 'idle',
          latency: 0.1,
          icon: 'database',
          medium: 'virtual',
          details: {
            hostPadre: srv.name,
            imagen: c.image || 'imagen',
            estado: c.status || 'Activo',
            puertos: c.ports || 'Internos'
          },
          x: xPos + (cIdx * 75) - 30,
          y: yPos + 105
        });
        links.push({
          source: srvId,
          target: cId,
          type: 'virtual',
          label: 'Docker Socket'
        });
      });
    });

    // NODO 3: Red Mesh Tailscale Zero-Trust (Si está activo)
    const tsRunning = Boolean(data?.tailscale?.BackendState === 'Running' || data?.tailscale?.Self);
    if (tsRunning) {
      const selfTs = data?.tailscale?.Self;
      const tsIp = selfTs?.TailscaleIPs?.[0] || '100.x.x.x';
      const tsId = 'node-tailscale-gateway';

      nodes.push({
        id: tsId,
        name: 'Malla Tailscale Zero-Trust',
        type: 'firewall',
        category: 'vpn',
        ip: tsIp,
        status: 'online',
        latency: 4,
        icon: 'shield',
        medium: 'wireguard',
        details: {
          role: 'Red Privada Cifrada WireGuard Mesh Multipunto',
          tailnet: data?.tailscale?.CurrentTailnet?.MagicDNSSuffix || 'Tailnet Activo',
          magicDNS: selfTs?.DNSName || 'DNS Seguro',
          estadoBackend: data?.tailscale?.BackendState || 'Running'
        },
        x: 500,
        y: 200
      });

      links.push({
        source: masterId,
        target: tsId,
        type: 'wireguard',
        label: 'Túnel WireGuard'
      });
    }

    // NODO 4: Dispositivos Reales de Red Local LAN (Descubiertos vía ARP / Neighbors)
    const lanNeighbors = Array.isArray(data?.network?.neighbors) ? data.network.neighbors : [];
    lanNeighbors.slice(0, 4).forEach((n, idx) => {
      if (!n || !n.ip) return;
      const nId = `node-lan-real-${idx}`;
      const dTypeStr = typeof n.device_type === 'string' ? n.device_type.toLowerCase() : '';
      const vendorStr = typeof n.vendor === 'string' ? n.vendor.toLowerCase() : '';
      const isPhone = dTypeStr.includes('phone') || vendorStr.includes('apple') || vendorStr.includes('samsung') || vendorStr.includes('xiaomi');
      const devMedium = isPhone ? 'wifi' : 'ethernet';

      nodes.push({
        id: nId,
        name: `${n.vendor && n.vendor !== 'Desconocido' ? n.vendor : 'Equipo'} (${n.device_type || 'LAN'})`,
        type: isPhone ? 'phone' : 'workstation',
        category: 'lan',
        ip: n.ip,
        mac: n.mac || '',
        status: 'online',
        latency: 3 + (idx * 2),
        icon: isPhone ? 'smartphone' : 'laptop',
        medium: devMedium,
        details: {
          role: 'Dispositivo en Subred Local',
          interfaz: n.interface || primaryNet.name,
          fabricante: n.vendor || 'Dispositivo de Red',
          direccionMAC: n.mac || 'N/A',
          medioFisico: devMedium === 'wifi' ? 'Wi-Fi Inalámbrico 2.4/5GHz' : 'Cable Ethernet UTP'
        },
        x: 140,
        y: 190 + (idx * 110)
      });

      // Los dispositivos LAN conectan directamente al Router
      links.push({
        source: routerId,
        target: nId,
        type: devMedium,
        label: devMedium === 'wifi' ? 'Wi-Fi' : 'Ethernet'
      });
    });

    // NODO 5: Contenedores Docker Locales del Host Maestro
    const localContainers = Array.isArray(data?.containers) ? data.containers : [];
    localContainers.slice(0, 2).forEach((c, idx) => {
      if (!c) return;
      const cId = `node-docker-local-${c.id || idx}`;
      const cStatusStr = typeof c.status === 'string' ? c.status : '';
      nodes.push({
        id: cId,
        name: `Docker: ${c.name || 'Contenedor'}`,
        type: 'docker',
        category: 'server',
        ip: c.ports || 'Bridge Local',
        status: cStatusStr.includes('Up') ? 'online' : 'idle',
        latency: 0.2,
        icon: 'database',
        medium: 'virtual',
        details: {
          hostPadre: 'Nodo Maestro (Host)',
          imagen: c.image || 'imagen',
          estado: cStatusStr || 'N/A',
          puertos: c.ports || 'Bridge Net'
        },
        x: 320 + (idx * 120),
        y: 470
      });
      links.push({
        source: masterId,
        target: cId,
        type: 'virtual',
        label: 'Docker Socket'
      });
    });

    // NODO 6: Impresora 3D Klipper (Si está conectada)
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
        latency: 1.5,
        icon: 'printer',
        medium: 'serial',
        resources: {
          klippyState: 'ready',
          printState: klippyStatus,
          extruderTemp: data?.printer?.extruder?.temperature || 0,
          bedTemp: data?.printer?.heater_bed?.temperature || 0,
        },
        details: {
          role: 'Fabricación Aditiva y Control Numérico G-Code',
          conexion: 'Moonraker API Webhooks / Interfaz Serie USB',
          estadoKlippy: klippyStatus
        },
        x: 500,
        y: 470
      });
      links.push({
        source: masterId,
        target: 'node-klipper-ready',
        type: 'serial',
        label: 'USB Serie / Moonraker'
      });
    }

    return { nodes, links, isKlipperReady };
  }, [data, connectedServers, remoteServersData]);

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

  // Ping a Nodo en Vivo
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

  const getNodeIcon = (iconName, size = 18) => {
    switch (iconName) {
      case 'router': return <Router size={size} color="#f59e0b" />;
      case 'wifi': return <Wifi size={size} color="#10b981" />;
      case 'shield': return <Shield size={size} color="#818cf8" />;
      case 'server': return <Server size={size} color="#06b6d4" />;
      case 'printer': return <Printer size={size} color="#f43f5e" />;
      case 'database': return <Database size={size} color="#38bdf8" />;
      case 'smartphone': return <Smartphone size={size} color="#a855f7" />;
      default: return <Laptop size={size} color="#94a3b8" />;
    }
  };

  const getLinkColor = (type, isHighlighted) => {
    if (isHighlighted) return '#38bdf8';
    switch (type) {
      case 'ethernet': return '#06b6d4'; // Cyan brillante cableado
      case 'wifi': return '#10b981'; // Esmeralda / Verde Wi-Fi
      case 'wireguard': return '#818cf8'; // Índigo túnel VPN
      case 'peer': return '#3b82f6'; // Azul enlace cluster
      case 'serial': return '#f43f5e'; // Rojo/Rosa USB hardware
      default: return '#64748b'; // Slate virtual
    }
  };

  const availableFilterCategories = [
    { id: 'all', label: 'Topología Completa' },
    { id: 'server', label: 'Servidores & Nodos' },
    { id: 'infrastructure', label: 'Router & Enrutador' },
    { id: 'lan', label: 'Dispositivos LAN' },
    { id: 'vpn', label: 'Tailscale VPN' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Barra de Filtros, Búsqueda y Leyenda Visual */}
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

        {/* Buscador de Dispositivos */}
        <div style={{ position: 'relative', minWidth: '260px' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
          <input
            type="text"
            placeholder="Buscar por IP, nombre, MAC, medio..."
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

      {/* Canvas Gráfico Interactivo de Topología */}
      <div style={{
        position: 'relative',
        width: '100%',
        minHeight: `${Math.max(620, 260 + Math.ceil(Math.max(1, (connectedServers || []).filter(s => !s.isLocal).length) / 2) * 220)}px`,
        background: 'radial-gradient(ellipse at 50% 20%, rgba(30, 41, 59, 0.7) 0%, rgba(10, 15, 29, 0.95) 100%)',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        overflow: 'hidden'
      }}>
        {/* Leyenda y Distinción Inalámbrica vs Cableada */}
        <div style={{ position: 'absolute', top: '16px', left: '16px', zIndex: 10, display: 'flex', gap: '0.75rem', flexWrap: 'wrap', pointerEvents: 'none' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.7)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.75rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.76rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', background: '#06b6d4', display: 'inline-block' }}></span>
            <Cable size={13} color="#06b6d4" />
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Cable Ethernet (Gigabit)</span>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.7)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.75rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.76rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', borderTop: '2px dashed #10b981', display: 'inline-block' }}></span>
            <Wifi size={13} color="#10b981" />
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Inalámbrico Wi-Fi (802.11)</span>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.7)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.75rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.76rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', borderTop: '2px dotted #818cf8', display: 'inline-block' }}></span>
            <Shield size={13} color="#818cf8" />
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Malla WireGuard VPN</span>
          </div>
        </div>

        {/* SVG Canvas de Conexiones Animadas */}
        <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          <defs>
            <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="glow-green" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Renderizado de cables y enlaces */}
          {topologyData.links.map((link, idx) => {
            const s = topologyData.nodes.find(n => n.id === link.source);
            const t = topologyData.nodes.find(n => n.id === link.target);
            if (!s || !t) return null;

            const isHighlighted = selectedNode && (selectedNode.id === s.id || selectedNode.id === t.id);
            const linkColor = getLinkColor(link.type, isHighlighted);
            const isDashed = link.type === 'wifi' || link.type === 'wireguard';

            // Curva Bézier suave para flujo orgánico de conexiones
            const midY = (s.y + t.y) / 2;
            const d = `M ${s.x} ${s.y} C ${s.x} ${midY}, ${t.x} ${midY}, ${t.x} ${t.y}`;

            return (
              <g key={idx}>
                {/* Línea base de enlace */}
                <path
                  d={d}
                  fill="none"
                  stroke={linkColor}
                  strokeWidth={isHighlighted ? 3 : (link.type === 'ethernet' ? 2.2 : 1.8)}
                  strokeDasharray={isDashed ? '6 4' : 'none'}
                  strokeOpacity={isHighlighted ? 1 : 0.65}
                  filter={isHighlighted ? (link.type === 'ethernet' ? 'url(#glow-cyan)' : 'url(#glow-green)') : 'none'}
                  style={{ transition: 'all 0.3s ease' }}
                />

                {/* Pulso de datos animado a lo largo del enlace */}
                <circle r={isHighlighted ? "4" : "2.5"} fill={linkColor} opacity="0.85">
                  <animateMotion
                    path={d}
                    dur={link.type === 'wifi' ? "3s" : "2s"}
                    repeatCount="indefinite"
                  />
                </circle>

                {/* Etiqueta del enlace a mitad de camino */}
                {link.label && (
                  <text
                    x={(s.x + t.x) / 2}
                    y={midY - 8}
                    fill={linkColor}
                    fontSize="10"
                    fontWeight="700"
                    textAnchor="middle"
                    opacity={isHighlighted ? 0.95 : 0.6}
                    style={{ letterSpacing: '0.04em', userSelect: 'none' }}
                  >
                    {link.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Nodos Interactivos */}
        {filteredNodes.map(node => {
          const isSelected = selectedNode?.id === node.id;
          const isOnline = node.status === 'online';
          const isRouter = node.type === 'router';
          const isMaster = node.isMaster;
          const isRemoteServer = node.type === 'remote_server';

          // Color del borde y brillo según el tipo de nodo
          let accentColor = '#38bdf8';
          if (isRouter) accentColor = '#f59e0b';
          else if (isMaster) accentColor = '#818cf8';
          else if (isRemoteServer) accentColor = '#06b6d4';
          else if (node.type === 'printer') accentColor = '#f43f5e';
          else if (node.medium === 'wifi') accentColor = '#10b981';

          return (
            <div
              key={node.id}
              onClick={() => {
                setSelectedNode(node);
                setPingResult(null);
              }}
              style={{
                position: 'absolute',
                left: `${node.x}px`,
                top: `${node.y}px`,
                transform: 'translate(-50%, -50%)',
                zIndex: isSelected ? 25 : (isMaster || isRemoteServer || isRouter ? 15 : 8),
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px',
                transition: 'transform 0.2s ease'
              }}
            >
              {/* Tarjeta de Nodo con Icono y Led de Estado */}
              <div
                style={{
                  width: isRouter ? '68px' : (isMaster || isRemoteServer ? '62px' : '48px'),
                  height: isRouter ? '68px' : (isMaster || isRemoteServer ? '62px' : '48px'),
                  borderRadius: isRouter ? '20px' : (isMaster || isRemoteServer ? '16px' : '12px'),
                  background: isSelected
                    ? `rgba(59, 130, 246, 0.35)`
                    : (isRouter ? 'rgba(245, 158, 11, 0.15)' : 'rgba(15, 23, 42, 0.85)'),
                  backdropFilter: 'blur(12px)',
                  border: isSelected
                    ? `2.5px solid ${accentColor}`
                    : `1.5px solid ${accentColor}60`,
                  boxShadow: isSelected
                    ? `0 0 25px ${accentColor}80`
                    : `0 4px 16px rgba(0, 0, 0, 0.5)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative'
                }}
              >
                {getNodeIcon(node.icon, isRouter ? 30 : (isMaster || isRemoteServer ? 26 : 20))}

                {/* Led de Conectividad */}
                <div
                  style={{
                    position: 'absolute',
                    top: '-3px',
                    right: '-3px',
                    width: '11px',
                    height: '11px',
                    borderRadius: '50%',
                    background: isOnline ? '#10b981' : (node.status === 'idle' ? '#f59e0b' : '#ef4444'),
                    boxShadow: isOnline ? '0 0 10px #10b981' : 'none'
                  }}
                />

                {/* Badge de Medio Físico (Ethernet vs Wi-Fi) */}
                {node.medium && node.medium !== 'infrastructure' && node.medium !== 'virtual' && (
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '-6px',
                      padding: '1px 5px',
                      borderRadius: '4px',
                      fontSize: '9px',
                      fontWeight: 800,
                      background: node.medium === 'wifi' ? '#064e3b' : '#083344',
                      color: node.medium === 'wifi' ? '#34d399' : '#38bdf8',
                      border: `1px solid ${node.medium === 'wifi' ? '#059669' : '#0284c7'}`,
                      letterSpacing: '0.02em',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {node.medium === 'wifi' ? 'WI-FI' : 'ETH'}
                  </div>
                )}
              </div>

              {/* Información y Subtítulo de Equipo */}
              <div style={{ textAlign: 'center', maxWidth: '160px' }}>
                <div style={{
                  fontSize: isMaster || isRemoteServer || isRouter ? '0.86rem' : '0.78rem',
                  fontWeight: 700,
                  color: isSelected ? '#38bdf8' : '#f8fafc',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {node.name}
                </div>
                <div style={{
                  fontSize: '0.72rem',
                  color: '#94a3b8',
                  fontFamily: 'monospace',
                  marginTop: '1px'
                }}>
                  {node.ip}
                </div>
                {node.resources?.cpuUsage !== undefined && (
                  <div style={{
                    fontSize: '0.68rem',
                    color: node.resources.cpuUsage > 75 ? '#ef4444' : '#34d399',
                    fontWeight: 600,
                    marginTop: '2px'
                  }}>
                    CPU: {node.resources.cpuUsage}% | {node.resources.ramTotalGb}GB
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Panel Lateral Drawer de Inspección de Nodo Seleccionado */}
        {selectedNode && (
          <div
            style={{
              position: 'absolute',
              top: '16px',
              right: '16px',
              bottom: '16px',
              width: '360px',
              background: 'rgba(15, 23, 42, 0.95)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '12px',
              padding: '1.25rem',
              zIndex: 35,
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '-8px 0 30px rgba(0, 0, 0, 0.6)',
              overflowY: 'auto'
            }}
          >
            {/* Cabecera del Inspector */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {getNodeIcon(selectedNode.icon, 22)}
                <div>
                  <h3 style={{ margin: 0, fontSize: '1rem', color: '#f8fafc' }}>{selectedNode.name}</h3>
                  <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontFamily: 'monospace' }}>{selectedNode.ip}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Tarjeta de Resumen y Medio de Conexión */}
            <div style={{ background: 'rgba(0, 0, 0, 0.4)', borderRadius: '8px', padding: '0.75rem', marginBottom: '1rem', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.78rem' }}>
                <span style={{ color: '#94a3b8' }}>Estado de Conexión:</span>
                <span style={{ color: selectedNode.status === 'online' ? '#34d399' : '#ef4444', fontWeight: 700 }}>
                  {selectedNode.status.toUpperCase()}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.78rem' }}>
                <span style={{ color: '#94a3b8' }}>Medio de Enlace:</span>
                <span style={{ color: selectedNode.medium === 'wifi' ? '#34d399' : '#38bdf8', fontWeight: 600 }}>
                  {selectedNode.medium === 'wifi' ? 'Wi-Fi 802.11 (Inalámbrico)' : (selectedNode.medium === 'ethernet' ? 'Ethernet RJ-45 (1 Gbps)' : 'Enlace Virtual')}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <span style={{ color: '#94a3b8' }}>Dirección MAC:</span>
                <span style={{ color: '#e2e8f0', fontFamily: 'monospace' }}>{selectedNode.mac || 'N/A'}</span>
              </div>
            </div>

            {/* Hardware & Recursos (Si están disponibles) */}
            {selectedNode.resources && (
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Recursos del Sistema
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.78rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                      <span style={{ color: '#cbd5e1' }}>CPU: {selectedNode.resources.cpuModel}</span>
                      <strong style={{ color: '#38bdf8' }}>{selectedNode.resources.cpuUsage}%</strong>
                    </div>
                    <div style={{ width: '100%', height: '5px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${selectedNode.resources.cpuUsage}%`, height: '100%', background: '#38bdf8' }} />
                    </div>
                  </div>

                  <div style={{ fontSize: '0.78rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                      <span style={{ color: '#cbd5e1' }}>Memoria RAM:</span>
                      <strong style={{ color: '#34d399' }}>{selectedNode.resources.ramUsedGb || 0} / {selectedNode.resources.ramTotalGb} GB</strong>
                    </div>
                  </div>

                  {selectedNode.resources.uptimeHours !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', color: '#94a3b8' }}>
                      <span>Tiempo Activo (Uptime):</span>
                      <span style={{ color: '#f8fafc' }}>{selectedNode.resources.uptimeHours} horas</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Detalles Técnicos y Roles */}
            {selectedNode.details && (
              <div style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Configuración de Red & Roles
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.76rem' }}>
                  {Object.entries(selectedNode.details).map(([key, val]) => (
                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
                      <span style={{ color: '#94a3b8', textTransform: 'capitalize' }}>{key.replace(/([A-Z])/g, ' $1')}:</span>
                      <span style={{ color: '#e2e8f0', textAlign: 'right', fontWeight: 500 }}>{String(val)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Herramienta de Diagnóstico: Ping ICMP */}
            <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <button
                  onClick={() => handlePingNode(selectedNode.ip)}
                  disabled={pingLoading || !selectedNode.ip || selectedNode.ip.includes('/')}
                  className="btn btn-primary"
                  style={{ flex: 1, padding: '0.45rem', fontSize: '0.78rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
                >
                  <Activity size={14} />
                  {pingLoading ? 'Comprobando Latencia...' : 'Probar Conectividad (Ping)'}
                </button>
              </div>

              {pingResult && (
                <div style={{
                  padding: '0.5rem',
                  borderRadius: '6px',
                  background: pingResult.status === 'ok' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  border: pingResult.status === 'ok' ? '1px solid #10b981' : '1px solid #ef4444',
                  fontSize: '0.76rem',
                  color: pingResult.status === 'ok' ? '#34d399' : '#f87171',
                  textAlign: 'center'
                }}>
                  {pingResult.status === 'ok'
                    ? `✔ Respuesta exitosa. Latencia RTT: ${pingResult.latency_ms || selectedNode.latency} ms`
                    : '✖ Host inalcanzable o respuesta fuera de tiempo.'}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
