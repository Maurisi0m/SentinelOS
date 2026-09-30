import React, { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import {
  Globe, Shield, Server, Laptop, Smartphone, Printer, Database,
  Cpu, Activity, Zap, RefreshCw, Send, Radio, Terminal, Wifi,
  CheckCircle2, AlertCircle, X, Search, Filter, Layers, HardDrive,
  Router, Play, Square, ExternalLink, ArrowRight, Cable, ArrowUpRight,
  WifiOff, Disc, Share2, Box, Cpu as Chip, Network as NetIcon, Move
} from 'lucide-react';

export default function NetworkTopologyView({ data, handleAction, connectedServers = [], remoteServersData = {} }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [pingLoading, setPingLoading] = useState(false);
  const [pingResult, setPingResult] = useState(null);

  // Estado de Arrastre Libre de Nodos (Drag & Drop interactivo)
  const [customPositions, setCustomPositions] = useState(() => {
    try {
      const saved = localStorage.getItem('sentinel_topology_positions_v2');
      return saved ? JSON.parse(saved) : {};
    } catch (e) {
      return {};
    }
  });
  const [draggingNodeId, setDraggingNodeId] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const canvasRef = useRef(null);

  // Telemetría en tiempo real de tráfico de red
  const netTraffic = data?.network?.traffic || {};
  const downloadKbps = Number(netTraffic.download_kbps || 0);
  const uploadKbps = Number(netTraffic.upload_kbps || 0);
  const totalTrafficKbps = downloadKbps + uploadKbps;
  const netLatencyMs = Number(data?.network?.internet?.latency_ms || 12);

  // Manejadores de arrastre con soporte para ratón y touch
  const handlePointerDown = (e, node) => {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    e.stopPropagation();
    
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const clientX = e.clientX;
    const clientY = e.clientY;
    
    setDraggingNodeId(node.id);
    setDragOffset({
      x: (clientX - rect.left) - node.x,
      y: (clientY - rect.top) - node.y
    });
    
    setSelectedNode(node);
  };

  const handlePointerMove = useCallback((e) => {
    if (!draggingNodeId || !canvasRef.current) return;
    e.preventDefault();
    
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const newX = Math.round(Math.max(45, Math.min(rect.width - 45, mouseX - dragOffset.x)));
    const newY = Math.round(Math.max(45, Math.min(rect.height - 45, mouseY - dragOffset.y)));
    
    setCustomPositions(prev => ({
      ...prev,
      [draggingNodeId]: { x: newX, y: newY }
    }));
  }, [draggingNodeId, dragOffset]);

  const handlePointerUp = useCallback(() => {
    if (draggingNodeId) {
      setDraggingNodeId(null);
      try {
        localStorage.setItem('sentinel_topology_positions_v2', JSON.stringify(customPositions));
      } catch (err) {}
    }
  }, [draggingNodeId, customPositions]);

  const handleResetPositions = () => {
    setCustomPositions({});
    try {
      localStorage.removeItem('sentinel_topology_positions_v2');
    } catch (err) {}
  };

  // 1. Construir Topología Completa de Red y Malla
  const topologyData = useMemo(() => {
    const nodes = [];
    const links = [];

    // Gateway / Router LAN Central
    const primaryNet = data?.network?.primary || {
      name: 'Ethernet',
      type: 'ethernet',
      speed: 1000,
      ip: '192.168.1.100',
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

    // NODO 0: Router / Gateway Wi-Fi / Conmutador LAN Principal
    const routerId = 'node-gateway-router';
    nodes.push({
      id: routerId,
      name: 'Gateway / Router LAN',
      type: 'router',
      category: 'infrastructure',
      ip: gatewayIp,
      mac: 'E8:48:B8:C0:01:A2',
      status: 'online',
      latency: 0.8,
      icon: 'router',
      medium: 'infrastructure',
      details: {
        rol: 'Puerta de Enlace Predeterminada, Conmutador LAN y AP Wi-Fi',
        ip: gatewayIp,
        subred: '255.255.255.0 (/24)',
        servicios: 'DHCP Server, DNS Cache, NAT Firewall, Wi-Fi 6 MIMO, Switch Gigabit',
        estado: 'Enrutamiento activo y estable'
      },
      x: 340,
      y: 75
    });

    // NODO 1: Malla Tailscale Zero-Trust (Mesh Hub)
    const tsRunning = Boolean(data?.tailscale?.BackendState === 'Running' || data?.tailscale?.Self);
    const selfTs = data?.tailscale?.Self;
    const tsIp = selfTs?.TailscaleIPs?.[0] || '100.91.38.108';
    const tsId = 'node-tailscale-gateway';

    if (tsRunning) {
      nodes.push({
        id: tsId,
        name: 'Malla Tailscale Zero-Trust',
        type: 'firewall',
        category: 'vpn',
        ip: tsIp,
        status: 'online',
        latency: 3.5,
        icon: 'shield',
        medium: 'wireguard',
        details: {
          rol: 'Red Privada Cifrada WireGuard Mesh Multipunto',
          tailnet: data?.tailscale?.CurrentTailnet?.MagicDNSSuffix || 'Tailnet Activo',
          magicDNS: selfTs?.DNSName || 'DNS Seguro WireGuard',
          estadoBackend: data?.tailscale?.BackendState || 'Running',
          nodoLocal: selfTs?.HostName || 'AmericaJuarez'
        },
        x: 620,
        y: 75
      });

      // Enlace Router LAN <-> Tailscale Hub (Salida WAN / Cifrado E2E)
      links.push({
        source: routerId,
        target: tsId,
        type: 'wan',
        label: 'WAN / WireGuard E2E',
        speed: '1 Gbps Encrypted'
      });
    }

    // NODO 2: Host Local / Nodo Maestro (Laptop / Workstation Central)
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
    const masterX = 280;
    const masterY = 260;

    nodes.push({
      id: masterId,
      name: data?.system?.node_name || 'Nodo Maestro (Cockpit Host)',
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
        rol: 'Panel Maestro de Control, Telemetría y Coordinación de Malla',
        sistemaOperativo: data?.system?.platform ? `${data.system.platform}` : 'Host Principal',
        interfazFisica: `${primaryNet.name} (${masterSpeed})`,
        tipoConexion: isMasterWifi ? 'Inalámbrica Wi-Fi 802.11 (5 GHz / 2.4 GHz)' : 'Cableada Ethernet RJ-45 (1 Gbps Full-Duplex)',
        direccionMAC: primaryNet.mac || 'N/A',
        tailscaleIP: tsIp,
        uptime: `${Math.floor((data?.system?.uptime || 0) / 3600)} horas activas`
      },
      x: masterX,
      y: masterY
    });

    // Enlace Router -> Maestro (Conexión LAN física)
    links.push({
      source: routerId,
      target: masterId,
      type: masterMedium,
      label: isMasterWifi ? 'Wi-Fi LAN' : 'Ethernet Gigabit',
      speed: masterSpeed
    });

    // Enlace Tailscale Mesh -> Maestro (Túnel cifrado WireGuard)
    if (tsRunning) {
      links.push({
        source: tsId,
        target: masterId,
        type: 'wireguard',
        label: 'Túnel WireGuard Directo',
        speed: 'WireGuard Mesh'
      });
    }

    // NODO 3: Servidores Remotos Conectados al Cockpit (e.g. Servidor HP ProLiant, Satélites)
    const remoteServers = (connectedServers || []).filter(s => !s.isLocal);
    const peerMap = data?.tailscale?.Peer || {};

    const serverPositions = [];

    remoteServers.forEach((srv, idx) => {
      const srvId = `node-srv-${srv.id || idx}`;
      const rData = remoteServersData[srv.id]?.data || {};
      const rNet = rData?.network?.primary || {};
      
      const rNetType = (rNet.type || '').toLowerCase();
      const rNetName = (rNet.name || '').toLowerCase();
      const isSrvWifi = rNetType === 'wifi' || rNetName.includes('wl') || rNetName.includes('wifi') || rNetName.includes('wireless');
      const srvMedium = isSrvWifi ? 'wifi' : 'ethernet';
      const srvSpeed = rNet.speed ? `${rNet.speed} Mbps` : (isSrvWifi ? '300 Mbps' : '1000 Mbps');

      // Comprobar si el servidor está en Tailscale
      const isTs = (srv.url || '').includes('100.') || (srv.url || '').includes('.ts.net');
      const isOnline = remoteServersData[srv.id]?.status === 'online' || srv.status === 'online';

      const srvCpuModel = rData?.system?.cpu_model || 'Intel Xeon / Core Multi-Core';
      const srvCores = rData?.system?.cpu_cores || 8;
      const srvRamTotalGb = rData?.system?.memory?.total ? (rData.system.memory.total / 1024**3).toFixed(1) : '15.6';
      const srvRamUsedGb = rData?.system?.memory?.used ? (rData.system.memory.used / 1024**3).toFixed(1) : '3.2';
      const srvCpuUsage = rData?.metrics_history?.[rData.metrics_history.length - 1]?.cpu || 0;

      // Posicionamiento armónico para Servidores Remotos
      let srvX = 680;
      let srvY = 260;
      if (remoteServers.length === 1) {
        srvX = 680;
        srvY = 260;
      } else if (remoteServers.length === 2) {
        srvX = idx === 0 ? 640 : 860;
        srvY = idx === 0 ? 220 : 330;
      } else {
        const col = idx % 2;
        const row = Math.floor(idx / 2);
        srvX = 620 + (col * 240);
        srvY = 200 + (row * 180);
      }

      serverPositions.push({ id: srvId, x: srvX, y: srvY, name: srv.name, isTs });

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
          rol: 'Servidor Satélite de Cómputo / Laboratorio 24/7',
          servidor: srv.name,
          endpoint: srv.url || 'Conexión Directa LAN',
          interfazFisica: `${rNet.name || 'eth0'} (${srvSpeed})`,
          tipoConexion: isSrvWifi ? 'Inalámbrica Wi-Fi Local' : 'Cableada Ethernet UTP Gigabit',
          direccionMAC: rNet.mac || 'N/A',
          enlaceSeguro: isTs ? 'Túnel Cifrado WireGuard Mesh (Tailscale)' : 'Enlace Directo de Alta Velocidad LAN'
        },
        x: srvX,
        y: srvY
      });

      // Enlace 1: Conexión física hacia el Router/Gateway LAN
      links.push({
        source: routerId,
        target: srvId,
        type: srvMedium,
        label: isSrvWifi ? 'Wi-Fi LAN' : 'Ethernet Gigabit LAN',
        speed: srvSpeed
      });

      // Enlace 2: Enlace de Control Maestro <-> Servidor Satélite
      links.push({
        source: masterId,
        target: srvId,
        type: isTs ? 'wireguard' : 'peer',
        label: isTs ? 'WireGuard Zero-Trust' : 'Cluster P2P Interconnect',
        speed: isTs ? 'Cifrado E2E' : 'Baja Latencia'
      });

      // Enlace 3: Conexión directa a la Malla Tailscale Hub si está en Tailscale
      if (tsRunning && (isTs || srv.url?.includes('ts.net') || srv.url?.includes('100.'))) {
        links.push({
          source: tsId,
          target: srvId,
          type: 'wireguard',
          label: 'Malla Tailscale Mesh',
          speed: 'WireGuard Túnel'
        });
      }

      // Enlace 4: Enlace de Malla entre Servidores Remotos (Inter-Server Mesh)
      if (idx > 0) {
        const prevSrv = serverPositions[idx - 1];
        links.push({
          source: prevSrv.id,
          target: srvId,
          type: isTs ? 'wireguard' : 'peer',
          label: isTs ? 'Inter-Server WireGuard Mesh' : 'Cluster Sync P2P',
          speed: 'Mesh Direct'
        });
      }

      // Contenedores del Servidor Remoto
      const srvContainers = Array.isArray(rData?.containers) ? rData.containers : [];
      srvContainers.slice(0, 2).forEach((c, cIdx) => {
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
          x: srvX + (cIdx * 90) - 45,
          y: srvY + 95
        });
        links.push({
          source: srvId,
          target: cId,
          type: 'virtual',
          label: 'Docker Socket'
        });
      });

      // Impresora 3D Klipper en el Servidor Remoto (si está conectada)
      const rKlipperReady = rData?.moonraker?.klippy_state === 'ready' || rData?.printer?.print_stats;
      if (rKlipperReady) {
        const rPrinterId = `node-klipper-srv-${srv.id}`;
        const rPrintStatus = rData?.printer?.print_stats?.state?.toUpperCase() || 'READY';
        nodes.push({
          id: rPrinterId,
          name: `Klipper 3D (${srv.name})`,
          type: 'printer',
          category: 'hardware',
          ip: `${srv.url ? srv.url.replace(/^https?:\/\//, '').replace(/:[0-9]+.*$/, '') : '192.168.1.x'}:7125`,
          status: 'online',
          latency: 1.5,
          icon: 'printer',
          medium: 'serial',
          resources: {
            klippyState: 'ready',
            printState: rPrintStatus,
            extruderTemp: rData?.printer?.extruder?.temperature || 0,
            bedTemp: rData?.printer?.heater_bed?.temperature || 0,
          },
          details: {
            rol: 'Fabricación Aditiva Klipper 3D Dedicada',
            hostPadre: srv.name,
            conexion: 'Moonraker API / USB Serie MCU Directo',
            estadoKlippy: rPrintStatus,
            temperaturaExtrusor: `${rData?.printer?.extruder?.temperature || 0}°C`,
            temperaturaCama: `${rData?.printer?.heater_bed?.temperature || 0}°C`
          },
          x: srvX + 90,
          y: srvY + 110
        });
        links.push({
          source: srvId,
          target: rPrinterId,
          type: 'serial',
          label: 'USB Serie / Moonraker'
        });
      }
    });

    // NODO 4: Peers de la Red Tailscale descubiertos (Malla WireGuard E2E)
    if (tsRunning && typeof peerMap === 'object') {
      const peersList = Object.values(peerMap);
      let peerIndex = 0;

      peersList.forEach(peer => {
        if (!peer || !peer.HostName) return;
        const peerHost = peer.HostName.toLowerCase();
        
        // Evitar duplicar servidores que ya fueron añadidos en connectedServers
        const alreadyInServers = remoteServers.some(s => 
          (s.name || '').toLowerCase().includes(peerHost) || 
          (s.url || '').toLowerCase().includes(peerHost)
        );
        if (alreadyInServers) return;

        const peerIp = peer.TailscaleIPs?.[0] || '100.x.x.x';
        const isOnline = Boolean(peer.Online);
        const pId = `node-ts-peer-${peerHost}-${peerIndex}`;
        const osStr = (peer.OS || '').toLowerCase();
        const isMobile = osStr.includes('ios') || osStr.includes('android');

        nodes.push({
          id: pId,
          name: `${peer.HostName} (${peer.OS || 'Tailnet'})`,
          type: isMobile ? 'phone' : 'workstation',
          category: 'vpn',
          ip: peerIp,
          status: isOnline ? 'online' : 'idle',
          latency: isOnline ? 18 : null,
          icon: isMobile ? 'smartphone' : 'laptop',
          medium: 'wireguard',
          details: {
            rol: 'Dispositivo / Nodo en la Malla Tailscale',
            sistemaOperativo: peer.OS || 'Desconocido',
            ipTailscale: peerIp,
            estadoMalla: isOnline ? 'Conectado a la Malla WireGuard' : 'En reposo / Desconectado',
            magicDNS: peer.DNSName || `${peerHost}.ts.net`
          },
          x: 910,
          y: 90 + (peerIndex * 85)
        });

        // Enlace desde el Tailscale Hub hacia el Peer
        links.push({
          source: tsId,
          target: pId,
          type: 'wireguard',
          label: 'Túnel WireGuard P2P',
          speed: isOnline ? 'Mesh Direct' : 'Standby'
        });

        peerIndex++;
      });
    }

    // NODO 5: Dispositivos Reales de Red Local LAN (Descubiertos vía ARP / Neighbors)
    const lanNeighbors = Array.isArray(data?.network?.neighbors) ? data.network.neighbors : [];
    lanNeighbors.slice(0, 4).forEach((n, idx) => {
      if (!n || !n.ip) return;
      const nId = `node-lan-real-${idx}`;
      const dTypeStr = typeof n.device_type === 'string' ? n.device_type.toLowerCase() : '';
      const vendorStr = typeof n.vendor === 'string' ? n.vendor.toLowerCase() : '';
      const isPhone = dTypeStr.includes('phone') || vendorStr.includes('apple') || vendorStr.includes('samsung') || vendorStr.includes('xiaomi');
      const isLanPrinter = dTypeStr.includes('printer') || vendorStr.includes('hp') || vendorStr.includes('epson') || vendorStr.includes('canon') || vendorStr.includes('brother');
      const devMedium = isPhone ? 'wifi' : 'ethernet';

      nodes.push({
        id: nId,
        name: isLanPrinter ? `Impresora: ${n.vendor || 'LAN'}` : `${n.vendor && n.vendor !== 'Desconocido' ? n.vendor : 'Equipo'} (${n.device_type || 'LAN'})`,
        type: isLanPrinter ? 'printer' : (isPhone ? 'phone' : 'workstation'),
        category: isLanPrinter ? 'hardware' : 'lan',
        ip: n.ip,
        mac: n.mac || '',
        status: 'online',
        latency: 3 + (idx * 2),
        icon: isLanPrinter ? 'printer' : (isPhone ? 'smartphone' : 'laptop'),
        medium: devMedium,
        details: {
          rol: isLanPrinter ? 'Impresora en Red Local' : 'Dispositivo en Subred Local LAN',
          interfaz: n.interface || primaryNet.name,
          fabricante: n.vendor || 'Dispositivo de Red',
          direccionMAC: n.mac || 'N/A',
          medioFisico: devMedium === 'wifi' ? 'Wi-Fi Inalámbrico 2.4/5GHz' : 'Cable Ethernet UTP'
        },
        x: 100,
        y: 160 + (idx * 95)
      });

      // Los dispositivos LAN conectan directamente al Router
      links.push({
        source: routerId,
        target: nId,
        type: devMedium,
        label: devMedium === 'wifi' ? 'Wi-Fi' : 'Ethernet'
      });
    });

    // NODO 6: Contenedores Docker Locales del Host Maestro
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
        x: masterX - 60 + (idx * 110),
        y: masterY + 140
      });
      links.push({
        source: masterId,
        target: cId,
        type: 'virtual',
        label: 'Docker Socket'
      });
    });

    // NODO 7: Impresora 3D Klipper Local del Host Maestro
    const isMasterKlipperReady = data?.moonraker?.klippy_state === 'ready' || data?.printer?.print_stats;
    if (isMasterKlipperReady) {
      const klippyStatus = data?.printer?.print_stats?.state?.toUpperCase() || 'READY';
      nodes.push({
        id: 'node-klipper-master',
        name: 'Laboratorio Klipper 3D (Local)',
        type: 'printer',
        category: 'hardware',
        ip: 'Puerto 7125 / USB Serial',
        status: 'online',
        latency: 1.2,
        icon: 'printer',
        medium: 'serial',
        resources: {
          klippyState: 'ready',
          printState: klippyStatus,
          extruderTemp: data?.printer?.extruder?.temperature || 0,
          bedTemp: data?.printer?.heater_bed?.temperature || 0,
        },
        details: {
          rol: 'Fabricación Aditiva y Control Numérico G-Code Local',
          conexion: 'Moonraker API Webhooks / Interfaz Serie USB',
          estadoKlippy: klippyStatus,
          temperaturaExtrusor: `${data?.printer?.extruder?.temperature || 0}°C`,
          temperaturaCama: `${data?.printer?.heater_bed?.temperature || 0}°C`
        },
        x: masterX + 110,
        y: masterY + 140
      });
      links.push({
        source: masterId,
        target: 'node-klipper-master',
        type: 'serial',
        label: 'USB Serie / Moonraker'
      });
    }

    // Aplicar coordenadas personalizadas de arrastre libre (Drag & Drop interactivo)
    const positionedNodes = nodes.map(n => {
      const custom = customPositions[n.id];
      return {
        ...n,
        x: custom ? custom.x : n.x,
        y: custom ? custom.y : n.y,
        defaultX: n.x,
        defaultY: n.y
      };
    });

    return { nodes: positionedNodes, links };
  }, [data, connectedServers, remoteServersData, customPositions]);

  // Filtrado de Nodos
  const filteredNodes = useMemo(() => {
    return (topologyData?.nodes || []).filter(n => {
      if (!n) return false;
      if (filterType !== 'all') {
        if (filterType === 'server' && n.category !== 'server') return false;
        if (filterType === 'vpn' && n.category !== 'vpn') return false;
        if (filterType === 'hardware' && n.category !== 'hardware') return false;
        if (filterType === 'lan' && n.category !== 'lan') return false;
        if (filterType === 'infrastructure' && n.category !== 'infrastructure') return false;
      }
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
      case 'database': return <Database size={size} color="#c084fc" />;
      case 'smartphone': return <Smartphone size={size} color="#a855f7" />;
      default: return <Laptop size={size} color="#94a3b8" />;
    }
  };

  const getLinkColor = (type, isHighlighted) => {
    if (isHighlighted) return '#38bdf8';
    switch (type) {
      case 'ethernet': return '#06b6d4'; // Cyan brillante cableado LAN
      case 'wifi': return '#10b981'; // Esmeralda / Verde Wi-Fi
      case 'wireguard': return '#818cf8'; // Índigo túnel VPN Mesh
      case 'peer': return '#3b82f6'; // Azul neón enlace Cluster P2P
      case 'serial': return '#f43f5e'; // Rosa/Carmesí USB Serie Klipper 3D
      case 'wan': return '#f59e0b'; // Ámbar salida WAN
      default: return '#64748b'; // Slate virtual
    }
  };

  const availableFilterCategories = [
    { id: 'all', label: 'Topología Completa' },
    { id: 'server', label: 'Servidores & Cluster Malla' },
    { id: 'vpn', label: 'Malla Tailscale WireGuard' },
    { id: 'hardware', label: 'Impresoras 3D & Hardware' },
    { id: 'lan', label: 'Dispositivos LAN' }
  ];

  // Calcular dinámicamente altura mínima requerida
  const totalNodesCount = topologyData.nodes.length;
  const computedMinHeight = Math.max(680, 420 + Math.ceil(totalNodesCount / 3) * 60);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Barra de Filtros, Búsqueda y Selector de Capas */}
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
      <div 
        ref={canvasRef}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
        style={{
          position: 'relative',
          width: '100%',
          minHeight: `${computedMinHeight}px`,
          background: 'radial-gradient(ellipse at 50% 25%, rgba(30, 41, 59, 0.75) 0%, rgba(10, 15, 29, 0.98) 100%)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          overflow: 'hidden',
          userSelect: 'none'
        }}
      >
        {/* Barra Superior Derecha: Telemetría Real & Control de Arrastre */}
        <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 12, display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.75rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8' }}>
            <Zap size={13} color="#f59e0b" />
            <span>Tráfico: <strong>{totalTrafficKbps > 1024 ? `${(totalTrafficKbps / 1024).toFixed(1)} MB/s` : `${totalTrafficKbps.toFixed(0)} KB/s`}</strong></span>
            <span style={{ color: '#64748b' }}>•</span>
            <span>Ping: <strong style={{ color: '#10b981' }}>{netLatencyMs.toFixed(0)} ms</strong></span>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.65rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px', color: '#94a3b8' }}>
            <Move size={12} color="#38bdf8" />
            <span>Arrastre Interactivo</span>
          </div>

          {Object.keys(customPositions).length > 0 && (
            <button
              onClick={handleResetPositions}
              className="btn btn-secondary"
              style={{ padding: '0.35rem 0.65rem', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(8px)' }}
              title="Restablecer posiciones originales"
            >
              <RefreshCw size={12} /> Restablecer
            </button>
          )}
        </div>

        {/* Leyenda y Distinción Inalámbrica vs Cableada vs Malla */}
        <div style={{ position: 'absolute', top: '16px', left: '16px', zIndex: 10, display: 'flex', gap: '0.65rem', flexWrap: 'wrap', pointerEvents: 'none' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.7rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', background: '#06b6d4', display: 'inline-block' }}></span>
            <Cable size={13} color="#06b6d4" />
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Ethernet Gigabit LAN</span>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.7rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', borderTop: '2px dashed #10b981', display: 'inline-block' }}></span>
            <Wifi size={13} color="#10b981" />
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Wi-Fi 802.11</span>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.7rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', borderTop: '2px dotted #818cf8', display: 'inline-block' }}></span>
            <Shield size={13} color="#818cf8" />
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Malla WireGuard Mesh</span>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.7rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', background: '#3b82f6', display: 'inline-block' }}></span>
            <Share2 size={13} color="#3b82f6" />
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Cluster P2P Mesh</span>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)', padding: '0.35rem 0.7rem', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', background: '#f43f5e', display: 'inline-block' }}></span>
            <Printer size={13} color="#f43f5e" />
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Klipper 3D USB / MCU</span>
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
            <filter id="glow-indigo" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="glow-rose" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Renderizado de cables y enlaces de red */}
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

            let filterUrl = 'none';
            if (isHighlighted) {
              if (link.type === 'ethernet' || link.type === 'peer') filterUrl = 'url(#glow-cyan)';
              else if (link.type === 'wifi') filterUrl = 'url(#glow-green)';
              else if (link.type === 'wireguard') filterUrl = 'url(#glow-indigo)';
              else if (link.type === 'serial') filterUrl = 'url(#glow-rose)';
            }

            // Determinar velocidad y telemetría de tráfico real para este cable específico
            let linkSpeedKbps = 0;
            let packetDur = '2.4s';
            let burstCount = 1;
            let realTrafficLabel = '';
            
            if (link.type === 'ethernet' || link.type === 'wifi') {
              linkSpeedKbps = totalTrafficKbps;
              if (linkSpeedKbps > 500) {
                packetDur = '0.7s';
                burstCount = 3;
              } else if (linkSpeedKbps > 80) {
                packetDur = '1.1s';
                burstCount = 2;
              } else if (linkSpeedKbps > 10) {
                packetDur = '1.8s';
                burstCount = 1;
              } else {
                packetDur = '3.2s';
                burstCount = 1;
              }
              realTrafficLabel = linkSpeedKbps > 1024 
                ? `${(linkSpeedKbps / 1024).toFixed(1)} MB/s ↓`
                : `${linkSpeedKbps.toFixed(0)} KB/s ↓`;
            } else if (link.type === 'peer' || link.type === 'wireguard') {
              const srvObj = Object.values(remoteServersData).find(sv => sv?.data?.system);
              const rNetSpeed = srvObj ? 28 : 12;
              linkSpeedKbps = rNetSpeed;
              packetDur = totalTrafficKbps > 100 ? '1.0s' : '1.9s';
              burstCount = totalTrafficKbps > 100 ? 2 : 1;
              realTrafficLabel = `${netLatencyMs.toFixed(0)} ms • ${linkSpeedKbps} KB/s`;
            } else if (link.type === 'serial') {
              const isPrinting = selectedNode?.resources?.printState === 'PRINTING';
              packetDur = isPrinting ? '0.8s' : '2.8s';
              burstCount = isPrinting ? 2 : 1;
              realTrafficLabel = isPrinting ? '250 kbaud (Imprimiendo)' : 'USB MCU Ready';
            } else {
              packetDur = '2.5s';
              burstCount = 1;
            }

            return (
              <g key={idx}>
                {/* Línea base de enlace */}
                <path
                  d={d}
                  fill="none"
                  stroke={linkColor}
                  strokeWidth={isHighlighted ? 3 : (link.type === 'ethernet' || link.type === 'peer' || link.type === 'serial' ? 2.2 : 1.8)}
                  strokeDasharray={isDashed ? '6 4' : 'none'}
                  strokeOpacity={isHighlighted ? 1 : 0.65}
                  filter={filterUrl}
                  style={{ transition: 'stroke 0.3s ease' }}
                />

                {/* Pulso de datos animado con telemetría en tiempo real */}
                {Array.from({ length: burstCount }).map((_, pIdx) => (
                  <circle
                    key={`p-${idx}-${pIdx}`}
                    r={isHighlighted ? 4.5 : (burstCount > 1 ? 3.2 : 2.6)}
                    fill={linkColor}
                    opacity={0.92 - (pIdx * 0.15)}
                    filter={isHighlighted || burstCount > 1 ? filterUrl : 'none'}
                  >
                    <animateMotion
                      path={d}
                      dur={packetDur}
                      begin={`${pIdx * 0.38}s`}
                      repeatCount="indefinite"
                    />
                  </circle>
                ))}

                {/* Etiqueta del enlace a mitad de camino con velocidad real */}
                {link.label && (
                  <text
                    x={(s.x + t.x) / 2}
                    y={midY - 8}
                    fill={linkColor}
                    fontSize="10"
                    fontWeight="700"
                    textAnchor="middle"
                    opacity={isHighlighted ? 0.95 : 0.75}
                    style={{ letterSpacing: '0.03em', userSelect: 'none', pointerEvents: 'none' }}
                  >
                    {link.label} {realTrafficLabel ? `(${realTrafficLabel})` : ''}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Nodos Interactivos (Arrastrables) */}
        {filteredNodes.map(node => {
          const isSelected = selectedNode?.id === node.id;
          const isDraggingThis = draggingNodeId === node.id;
          const isOnline = node.status === 'online';
          const isRouter = node.type === 'router';
          const isMaster = node.isMaster;
          const isRemoteServer = node.type === 'remote_server';
          const isPrinter = node.type === 'printer';
          const isTsHub = node.id === 'node-tailscale-gateway';

          // Color del borde y brillo según el tipo de nodo
          let accentColor = '#38bdf8';
          if (isRouter) accentColor = '#f59e0b';
          else if (isMaster) accentColor = '#818cf8';
          else if (isRemoteServer) accentColor = '#06b6d4';
          else if (isPrinter) accentColor = '#f43f5e';
          else if (isTsHub) accentColor = '#a855f7';
          else if (node.medium === 'wifi') accentColor = '#10b981';

          return (
            <div
              key={node.id}
              onPointerDown={(e) => handlePointerDown(e, node)}
              onClick={() => {
                setSelectedNode(node);
                setPingResult(null);
              }}
              style={{
                position: 'absolute',
                left: `${node.x}px`,
                top: `${node.y}px`,
                transform: `translate(-50%, -50%) ${isDraggingThis ? 'scale(1.08)' : ''}`,
                zIndex: isDraggingThis ? 50 : (isSelected ? 25 : (isMaster || isRemoteServer || isRouter || isTsHub ? 15 : 8)),
                cursor: isDraggingThis ? 'grabbing' : 'grab',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px',
                userSelect: 'none',
                touchAction: 'none',
                transition: isDraggingThis ? 'none' : 'transform 0.15s ease'
              }}
            >
              {/* Tarjeta de Nodo con Icono y Led de Estado */}
              <div
                style={{
                  width: isRouter || isTsHub ? '68px' : (isMaster || isRemoteServer ? '62px' : (isPrinter ? '56px' : '48px')),
                  height: isRouter || isTsHub ? '68px' : (isMaster || isRemoteServer ? '62px' : (isPrinter ? '56px' : '48px')),
                  borderRadius: isRouter || isTsHub ? '20px' : (isMaster || isRemoteServer ? '16px' : (isPrinter ? '14px' : '12px')),
                  background: isSelected
                    ? `rgba(59, 130, 246, 0.35)`
                    : (isRouter ? 'rgba(245, 158, 11, 0.15)' : (isTsHub ? 'rgba(168, 85, 247, 0.15)' : 'rgba(15, 23, 42, 0.85)')),
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
                {getNodeIcon(node.icon, isRouter || isTsHub ? 30 : (isMaster || isRemoteServer ? 26 : (isPrinter ? 24 : 20)))}

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

                {/* Badge de Medio Físico (Ethernet vs Wi-Fi vs WireGuard vs USB) */}
                {node.medium && node.medium !== 'infrastructure' && node.medium !== 'virtual' && (
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '-6px',
                      padding: '1px 5px',
                      borderRadius: '4px',
                      fontSize: '9px',
                      fontWeight: 800,
                      background: node.medium === 'wifi' ? '#064e3b' : (node.medium === 'wireguard' ? '#312e81' : (node.medium === 'serial' ? '#881337' : '#083344')),
                      color: node.medium === 'wifi' ? '#34d399' : (node.medium === 'wireguard' ? '#a5b4fc' : (node.medium === 'serial' ? '#fda4af' : '#38bdf8')),
                      border: `1px solid ${node.medium === 'wifi' ? '#059669' : (node.medium === 'wireguard' ? '#6366f1' : (node.medium === 'serial' ? '#f43f5e' : '#0284c7'))}`,
                      letterSpacing: '0.02em',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {node.medium === 'wifi' ? 'WI-FI' : (node.medium === 'wireguard' ? 'WG MESH' : (node.medium === 'serial' ? 'USB 3D' : 'ETH'))}
                  </div>
                )}
              </div>

              {/* Información y Subtítulo de Equipo */}
              <div style={{ textAlign: 'center', maxWidth: '170px' }}>
                <div style={{
                  fontSize: isMaster || isRemoteServer || isRouter || isTsHub ? '0.86rem' : '0.78rem',
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
                {isPrinter && node.resources?.extruderTemp !== undefined && (
                  <div style={{
                    fontSize: '0.68rem',
                    color: '#f43f5e',
                    fontWeight: 600,
                    marginTop: '2px'
                  }}>
                    Extruder: {node.resources.extruderTemp}°C | Bed: {node.resources.bedTemp}°C
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
              width: '370px',
              background: 'rgba(15, 23, 42, 0.96)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '12px',
              padding: '1.25rem',
              zIndex: 35,
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '-8px 0 30px rgba(0, 0, 0, 0.65)',
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
                <span style={{ color: selectedNode.medium === 'wifi' ? '#34d399' : (selectedNode.medium === 'wireguard' ? '#a5b4fc' : (selectedNode.medium === 'serial' ? '#f43f5e' : '#38bdf8')), fontWeight: 600 }}>
                  {selectedNode.medium === 'wifi' ? 'Wi-Fi 802.11 (Inalámbrico)' : (selectedNode.medium === 'wireguard' ? 'Túnel WireGuard Mesh Cifrado' : (selectedNode.medium === 'serial' ? 'USB Serie / Moonraker' : (selectedNode.medium === 'ethernet' ? 'Ethernet RJ-45 (1 Gbps)' : 'Enlace Virtual')))}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <span style={{ color: '#94a3b8' }}>Dirección MAC:</span>
                <span style={{ color: '#e2e8f0', fontFamily: 'monospace' }}>{selectedNode.mac || 'N/A'}</span>
              </div>
            </div>

            {/* Conexiones de Malla Activas del Nodo Seleccionado */}
            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Enlaces de Red & Malla
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', background: 'rgba(0, 0, 0, 0.3)', padding: '0.6rem', borderRadius: '8px' }}>
                {topologyData.links
                  .filter(l => l.source === selectedNode.id || l.target === selectedNode.id)
                  .map((lnk, lIdx) => {
                    const otherId = lnk.source === selectedNode.id ? lnk.target : lnk.source;
                    const otherNode = topologyData.nodes.find(n => n.id === otherId);
                    return (
                      <div key={lIdx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', padding: '0.25rem 0.4rem', borderRadius: '4px', background: 'rgba(255,255,255,0.03)' }}>
                        <span style={{ color: '#cbd5e1', fontWeight: 600 }}>{otherNode?.name || otherId}</span>
                        <span style={{ color: getLinkColor(lnk.type, false), fontSize: '0.72rem', fontWeight: 700 }}>
                          {lnk.label || lnk.type}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* Hardware & Recursos (Si están disponibles) */}
            {selectedNode.resources && (
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Recursos del Sistema
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(0, 0, 0, 0.3)', padding: '0.75rem', borderRadius: '8px' }}>
                  {selectedNode.resources.cpuUsage !== undefined && (
                    <div style={{ fontSize: '0.78rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                        <span style={{ color: '#cbd5e1' }}>CPU: {selectedNode.resources.cpuModel}</span>
                        <strong style={{ color: '#38bdf8' }}>{selectedNode.resources.cpuUsage}%</strong>
                      </div>
                      <div style={{ width: '100%', height: '5px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${selectedNode.resources.cpuUsage}%`, height: '100%', background: '#38bdf8' }} />
                      </div>
                    </div>
                  )}

                  {selectedNode.resources.ramTotalGb !== undefined && (
                    <div style={{ fontSize: '0.78rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                        <span style={{ color: '#cbd5e1' }}>Memoria RAM:</span>
                        <strong style={{ color: '#34d399' }}>{selectedNode.resources.ramUsedGb || 0} / {selectedNode.resources.ramTotalGb} GB</strong>
                      </div>
                    </div>
                  )}

                  {selectedNode.resources.uptimeHours !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', color: '#94a3b8' }}>
                      <span>Tiempo Activo (Uptime):</span>
                      <span style={{ color: '#f8fafc' }}>{selectedNode.resources.uptimeHours} horas</span>
                    </div>
                  )}

                  {selectedNode.resources.extruderTemp !== undefined && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.76rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#cbd5e1' }}>Extrusor Hotend:</span>
                        <strong style={{ color: '#f43f5e' }}>{selectedNode.resources.extruderTemp}°C</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#cbd5e1' }}>Cama Térmica:</span>
                        <strong style={{ color: '#f59e0b' }}>{selectedNode.resources.bedTemp}°C</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#cbd5e1' }}>Estado Klipper:</span>
                        <strong style={{ color: '#34d399' }}>{selectedNode.resources.printState}</strong>
                      </div>
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
