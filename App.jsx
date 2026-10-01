import React, { useState, useEffect, useRef } from 'react';
import { LayoutDashboard, Activity, Printer, Database, Network, FolderSearch, Settings, Trash2, Play, Square, RefreshCw, Cpu, HardDrive, Server, ChevronDown, ChevronUp, Power, Shield, Router, Terminal, User, Package, TerminalSquare, Zap, Gauge, ShoppingBag, PowerOff, Bot, PanelLeftClose, PanelLeftOpen, Maximize2, Minimize2, Compass, ChevronLeft, ChevronRight, Check, X, Layers, Plus, CheckCircle2, AlertCircle, AlertTriangle, Cable, Filter, Sliders, Globe, Radio, Key, Copy, Search, Wifi, WifiOff, ArrowUpRight, ArrowDownLeft, ShieldCheck } from 'lucide-react';
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Terminal as TerminalXTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { Rnd } from 'react-rnd';
import '@xterm/xterm/css/xterm.css';
import './index.css';
import SentinelIntro from './components/SentinelIntro';
import SentinelCockpit from './components/SentinelCockpit';
import NetworkTopologyView from './components/NetworkTopologyView';

const API_URL = "/api";
const SERVICE_HTTP_PORT = window.location.port || '80';
const FIRST_RUN = new URLSearchParams(window.location.search).get('first_run') === '1';

if (FIRST_RUN) {
  try {
    localStorage.removeItem('sentinel_connected_servers');
    localStorage.removeItem('sentinel_welcome_seen_v2');
    localStorage.removeItem('sentinel_onboarding_completed');
  } catch (e) {}
  try {
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
  } catch (e) {}
}

const CustomSlider = ({ min, max, step, value, onChangeCommit, onChangeDrag }) => {
  const [localVal, setLocalVal] = React.useState(value);
  const [isDragging, setIsDragging] = React.useState(false);
  React.useEffect(() => { if (!isDragging) setLocalVal(value); }, [value, isDragging]);
  
  const handleChange = (e) => {
    setLocalVal(e.target.value);
    if(onChangeDrag) onChangeDrag(e.target.value);
  };
  
  return (
    <input type="range" className="custom-range" min={min} max={max} step={step} value={localVal}
      onChange={handleChange}
      onMouseDown={() => setIsDragging(true)}
      onMouseUp={(e) => { setIsDragging(false); onChangeCommit(e.target.value); if(onChangeDrag) onChangeDrag(null); }}
      onTouchStart={() => setIsDragging(true)}
      onTouchEnd={(e) => { setIsDragging(false); onChangeCommit(e.target.value); if(onChangeDrag) onChangeDrag(null); }}
      style={{flex: 1}}
    />
  );
};

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [showSentinelIntro, setShowSentinelIntro] = useState(false);
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);
  const [scanningLan, setScanningLan] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isGlobalFullscreen, setIsGlobalFullscreen] = useState(false);
  const [networkSubTab, setNetworkSubTab] = useState('status');

  // Multi-Server Permanent Connections & Telemetry State
  const [connectedServers, setConnectedServers] = useState(() => {
    try {
      const saved = FIRST_RUN ? null : localStorage.getItem('sentinel_connected_servers');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed.map(s => {
            if (s.isLocal || !s.url) return s;
            let u = s.url.trim().replace(/\/+$/, '');
            if (!u.startsWith('http://') && !u.startsWith('https://')) u = `http://${u}`;
            if (!u.includes(':', 7)) u = `${u}:8001`;
            return { ...s, url: u };
          });
        }
      }
    } catch (e) {}
    return [
      { id: 'local', name: 'Host Maestro (Local)', url: '', isLocal: true, status: 'online' }
    ];
  });

  const [remoteServersData, setRemoteServersData] = useState({});
  const [selectedServers, setSelectedServers] = useState(['local']);
  const [serverModalOpen, setServerModalOpen] = useState(false);
  const [newServerForm, setNewServerForm] = useState({ name: '', url: '', token: '' });
  const [serverTestStatus, setServerTestStatus] = useState(null);
  const [serverTestLoading, setServerTestLoading] = useState(false);
  const [meshDiscoveredNodes, setMeshDiscoveredNodes] = useState([]);

  // Multi-Server Logs State
  const [selectedLogServers, setSelectedLogServers] = useState(['local']);
  const [remoteLogs, setRemoteLogs] = useState({});
  const [logViewMode, setLogViewMode] = useState('windows'); // 'windows' | 'tabs' | 'consolidated'
  const [activeLogTab, setActiveLogTab] = useState('local');
  const [logSearchMap, setLogSearchMap] = useState({});
  const [logPausedMap, setLogPausedMap] = useState({});
  const [logCopiedMap, setLogCopiedMap] = useState({});
  const [logClearedMap, setLogClearedMap] = useState({});

  // System Maintenance & Uninstall State
  const [uninstallModalOpen, setUninstallModalOpen] = useState(false);
  const [uninstallConfirmText, setUninstallConfirmText] = useState('');
  const [uninstallPurgeData, setUninstallPurgeData] = useState(false);
  const [uninstallTargetServer, setUninstallTargetServer] = useState('local');
  const [uninstallLoading, setUninstallLoading] = useState(false);
  const [uninstallStatusMsg, setUninstallStatusMsg] = useState(null);
  const [uninstallCompleted, setUninstallCompleted] = useState(false);

  // Multi-Server Containers & System/Services State
  const [selectedDockerServer, setSelectedDockerServer] = useState('all');
  const [selectedTailscaleServer, setSelectedTailscaleServer] = useState('all');
  const [selectedPrinterServer, setSelectedPrinterServer] = useState('auto');
  const [selectedSystemServer, setSelectedSystemServer] = useState('all');
  const [remoteServices, setRemoteServices] = useState({});
  const [procFilterQuery, setProcFilterQuery] = useState('');
  const [procSortField, setProcSortField] = useState('cpu');
  const [serviceFilterQuery, setServiceFilterQuery] = useState('');
  const [localNodeAuth, setLocalNodeAuth] = useState(null);
  const [tokenCopied, setTokenCopied] = useState(false);

  // Cargar token de nodo central al inicio
  useEffect(() => {
    fetch('/api/node/token')
      .then(res => res.json())
      .then(d => {
        if (d && d.token) setLocalNodeAuth(d);
      })
      .catch(() => {});
  }, []);

  // Persistir servidores conectados en localStorage
  useEffect(() => {
    try {
      localStorage.setItem('sentinel_connected_servers', JSON.stringify(connectedServers));
    } catch (e) {}
  }, [connectedServers]);

  // Polling de telemetría de servidores remotos con Malla Inteligente y Ejecución Paralela
  const isPollingRemotesRef = useRef(false);
  useEffect(() => {
    const remotes = connectedServers.filter(s => !s.isLocal);

    const pollRemotes = async () => {
      if (isPollingRemotesRef.current) return;
      isPollingRemotesRef.current = true;

      try {
        // 1. Obtener estado global de la malla y nodos descubiertos
        let meshMap = {};
        try {
          const mRes = await fetch(`${API_URL}/mesh/nodes`, { signal: AbortSignal.timeout(1500) });
          if (mRes.ok) {
            const mData = await mRes.json();
            const nodes = mData.nodes || [];
            setMeshDiscoveredNodes(nodes);
            nodes.forEach(n => {
              if (n.node_id) meshMap[n.node_id.toLowerCase()] = n;
              if (n.node_name) meshMap[n.node_name.toLowerCase()] = n;
              (n.candidates || []).forEach(c => {
                meshMap[c.toLowerCase().replace(/\/+$/, '')] = n;
              });
            });
          }
        } catch (e) {}

        if (remotes.length === 0) return;

        // 2. Ejecución PARALELA para no trabar el dashboard maestro cuando hay 2+ servidores
        await Promise.allSettled(remotes.map(async (srv) => {
          if (!srv.url) return;
          const headers = srv.token ? { 'Authorization': `Bearer ${srv.token}`, 'X-Sentinel-Token': srv.token } : {};
          
          const candidateUrls = [];
          const addCand = (u) => {
            if (!u) return;
            let clean = u.trim().replace(/\/+$/, '');
            if (!clean.startsWith('http://') && !clean.startsWith('https://')) clean = `http://${clean}`;
            if (!clean.includes(':', 7)) clean = `${clean}:8001`;
            if (!candidateUrls.includes(clean)) candidateUrls.push(clean);
          };

          if (srv.activeUrl) addCand(srv.activeUrl);
          addCand(srv.url);
          (srv.candidates || []).forEach(addCand);

          const srvNameLower = (srv.name || '').toLowerCase();
          const srvUrlLower = (srv.url || '').toLowerCase();
          let matchedMeshNode = meshMap[srv.id?.toLowerCase()] || meshMap[srvNameLower];
          if (!matchedMeshNode) {
            for (const [key, n] of Object.entries(meshMap)) {
              if (srvUrlLower.includes(key) || key.includes(srvUrlLower) || srvNameLower.includes(n.node_name?.toLowerCase())) {
                matchedMeshNode = n;
                break;
              }
            }
          }
          if (matchedMeshNode) {
            (matchedMeshNode.candidates || []).forEach(addCand);
            if (!srv.token && matchedMeshNode.token) {
              srv.token = matchedMeshNode.token;
            }
          }

          let fetchSuccess = false;
          let rData = null;
          let confirmedWorkingUrl = null;

          for (const candUrl of candidateUrls) {
            try {
              let res;
              try {
                res = await fetch(`${candUrl}/api/data`, { headers, signal: AbortSignal.timeout(1600) });
              } catch (directErr) {
                res = await fetch(`${API_URL}/remote/proxy?target_url=${encodeURIComponent(candUrl + '/api/data')}`, {
                  headers,
                  signal: AbortSignal.timeout(2200)
                });
              }

              if (res && res.ok) {
                rData = await res.json();
                confirmedWorkingUrl = res.headers?.get('x-resolved-endpoint') || candUrl;
                if (confirmedWorkingUrl.startsWith('http://') || confirmedWorkingUrl.startsWith('https://')) {
                  const base = confirmedWorkingUrl.replace(/\/api\/data.*$/, '').replace(/\/+$/, '');
                  srv.activeUrl = base;
                }
                fetchSuccess = true;
                break;
              }
            } catch (e) {}
          }

          if (!fetchSuccess && matchedMeshNode && matchedMeshNode.status === 'online' && matchedMeshNode.data && Object.keys(matchedMeshNode.data).length > 0) {
            rData = matchedMeshNode.data;
            fetchSuccess = true;
          }

          if (fetchSuccess && rData) {
            setRemoteServersData(prev => {
              const prevNode = prev[srv.id] || {};
              const curHist = prevNode.history || [];
              const lastCpu = rData.metrics_history?.[rData.metrics_history.length - 1]?.cpu ?? 0;
              const lastRam = rData.metrics_history?.[rData.metrics_history.length - 1]?.ram ?? 0;
              const timeStr = new Date().toLocaleTimeString();
              const hist = rData.metrics_history?.length ? rData.metrics_history : [...curHist, { time: timeStr, cpu: lastCpu, ram: lastRam }].slice(-30);

              return {
                ...prev,
                [srv.id]: {
                  data: rData,
                  history: hist,
                  status: 'online',
                  lastSeen: Date.now()
                }
              };
            });

            if (activeTab === 'processes') {
              const targetProcessUrl = srv.activeUrl || srv.url;
              try {
                let sRes;
                try {
                  sRes = await fetch(`${targetProcessUrl}/api/services`, { headers, signal: AbortSignal.timeout(2000) });
                } catch (e) {
                  sRes = await fetch(`${API_URL}/remote/proxy?target_url=${encodeURIComponent(targetProcessUrl + '/api/services')}`, {
                    headers,
                    signal: AbortSignal.timeout(2500)
                  });
                }
                if (sRes && sRes.ok) {
                  const sBody = await sRes.json();
                  setRemoteServices(prev => ({ ...prev, [srv.id]: sBody.services || [] }));
                }
              } catch (e) {}
            }
          } else {
            setRemoteServersData(prev => ({
              ...prev,
              [srv.id]: { ...(prev[srv.id] || {}), status: 'offline' }
            }));
          }
        }));
      } finally {
        isPollingRemotesRef.current = false;
      }
    };

    pollRemotes();
    const interval = setInterval(pollRemotes, 3500);
    return () => clearInterval(interval);
  }, [connectedServers, activeTab]);

  // Polling de logs para servidores remotos
  useEffect(() => {
    if (activeTab !== 'logs') return;
    const remotes = connectedServers.filter(s => !s.isLocal);
    if (remotes.length === 0) return;

    const pollLogs = async () => {
      for (const srv of remotes) {
        if (!srv.url) continue;
        const targetUrl = srv.url.replace(/\/+$/, '');
        try {
          let res;
          const headers = srv.token ? { 'Authorization': `Bearer ${srv.token}`, 'X-Sentinel-Token': srv.token } : {};
          try {
            res = await fetch(`${targetUrl}/api/logs`, { headers, signal: AbortSignal.timeout(3500) });
          } catch (e) {
            res = await fetch(`${API_URL}/remote/proxy?target_url=${encodeURIComponent(targetUrl + '/api/logs')}`, {
              headers,
              signal: AbortSignal.timeout(5000)
            });
          }
          if (res.ok) {
            const body = await res.json();
            const logLines = (body.logs || '').split('\n').filter(Boolean).slice(-60);
            setRemoteLogs(prev => ({
              ...prev,
              [srv.id]: logLines
            }));
          }
        } catch (e) {}
      }
    };

    pollLogs();
    const interval = setInterval(pollLogs, 3000);
    return () => clearInterval(interval);
  }, [activeTab, connectedServers]);

  // Manejadores de selección multi-servidor
  const toggleServerSelection = (srvId) => {
    setSelectedServers(prev => {
      if (prev.includes(srvId)) {
        if (prev.length === 1) return prev;
        return prev.filter(id => id !== srvId);
      } else {
        return [...prev, srvId];
      }
    });
  };

  const selectSingleServer = (srvId) => {
    setSelectedServers([srvId]);
  };

  const selectAllServers = () => {
    setSelectedServers(connectedServers.map(s => s.id));
  };

  const toggleLogServerSelection = (srvId) => {
    setSelectedLogServers(prev => {
      if (prev.includes(srvId)) {
        if (prev.length === 1) return prev;
        return prev.filter(id => id !== srvId);
      } else {
        return [...prev, srvId];
      }
    });
  };

  const selectAllLogServers = () => {
    setSelectedLogServers(connectedServers.map(s => s.id));
  };

  const handleTestServerConnection = async () => {
    if (!newServerForm.url.trim()) return;
    setServerTestLoading(true);
    setServerTestStatus(null);
    let target = newServerForm.url.trim();
    if (!target.startsWith('http://') && !target.startsWith('https://')) {
      target = `http://${target}`;
    }
    if (!target.includes(':', 7)) {
      target = `${target}:8001`;
    }
    target = target.replace(/\/+$/, '');

    const headers = newServerForm.token.trim() ? { 'Authorization': `Bearer ${newServerForm.token.trim()}`, 'X-Sentinel-Token': newServerForm.token.trim() } : {};
    try {
      let res;
      try {
        res = await fetch(`${target}/api/node/info`, { headers, signal: AbortSignal.timeout(4000) });
      } catch (err) {
        res = await fetch(`${API_URL}/remote/proxy?target_url=${encodeURIComponent(target + '/api/node/info')}`, { headers, signal: AbortSignal.timeout(6000) });
      }

      if (res.ok) {
        const info = await res.json();
        setServerTestStatus({
          ok: true,
          msg: `Conexión confirmada con ${info.node_name || 'Nodo Remoto'} (${info.cores || '?'} Núcleos, ${info.total_ram_gb || info.memory_gb || '?'} GB RAM)`
        });
      } else {
        setServerTestStatus({ ok: false, msg: `El servidor respondió con código ${res.status}` });
      }
    } catch (e) {
      setServerTestStatus({ ok: false, msg: 'No se pudo alcanzar el servidor. Verifica IP, puerto y firewall.' });
    } finally {
      setServerTestLoading(false);
    }
  };

  const handleAddServer = (e) => {
    e.preventDefault();
    if (!newServerForm.url.trim()) return;
    let target = newServerForm.url.trim();
    if (!target.startsWith('http://') && !target.startsWith('https://')) {
      target = `http://${target}`;
    }
    if (!target.includes(':', 7)) {
      target = `${target}:8001`;
    }
    target = target.replace(/\/+$/, '');

    const newId = `srv-${Date.now()}`;
    const newEntry = {
      id: newId,
      name: newServerForm.name.trim() || `Servidor ${connectedServers.length}`,
      url: target,
      token: newServerForm.token.trim(),
      isLocal: false,
      status: 'online'
    };

    setConnectedServers(prev => [...prev, newEntry]);
    setSelectedServers(prev => [...prev, newId]);
    setSelectedLogServers(prev => [...prev, newId]);
    setNewServerForm({ name: '', url: '', token: '' });
    setServerTestStatus(null);
    setServerModalOpen(false);
    addNotification(`Servidor ${newEntry.name} conectado permanentemente.`, 'success');
  };

  const handleRemoveServer = (srvId) => {
    if (srvId === 'local') return;
    setConnectedServers(prev => prev.filter(s => s.id !== srvId));
    setSelectedServers(prev => {
      const filtered = prev.filter(id => id !== srvId);
      return filtered.length > 0 ? filtered : ['local'];
    });
    setSelectedLogServers(prev => {
      const filtered = prev.filter(id => id !== srvId);
      return filtered.length > 0 ? filtered : ['local'];
    });
    addNotification('Servidor desconectado del panel.', 'info');
  };

  const handleUninstallSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (uninstallConfirmText.trim().toUpperCase() !== 'DESINSTALAR') return;
    setUninstallLoading(true);
    setUninstallStatusMsg(null);

    try {
      if (uninstallTargetServer === 'local') {
        const res = await fetch(`${API_URL}/system/uninstall`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ confirm: true, purge_data: uninstallPurgeData })
        });
        let respData = {};
        try {
          respData = await res.json();
        } catch (jsonErr) {}
        if (res.ok) {
          setUninstallCompleted(true);
          setUninstallModalOpen(false);
        } else {
          setUninstallStatusMsg({ ok: false, msg: respData.detail || 'Error al ejecutar desinstalación' });
        }
      } else {
        const targetSrv = connectedServers.find(s => s.id === uninstallTargetServer);
        if (targetSrv) {
          try {
            const remoteUrl = `${targetSrv.url}/api/system/uninstall`;
            await fetch(`${API_URL}/remote/proxy?target_url=${encodeURIComponent(remoteUrl)}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ confirm: true, purge_data: uninstallPurgeData })
            });
          } catch (err) {}
          handleRemoveServer(targetSrv.id);
          setUninstallModalOpen(false);
          addNotification(`Servidor ${targetSrv.name} desinstalado y desvinculado exitosamente.`, 'success');
        }
      }
    } catch (err) {
      if (uninstallTargetServer === 'local') {
        // En caso de que el backend local se termine inmediatamente tras la desinstalación
        setUninstallCompleted(true);
        setUninstallModalOpen(false);
      } else {
        setUninstallStatusMsg({ ok: false, msg: 'Error de comunicación: ' + err.message });
      }
    } finally {
      setUninstallLoading(false);
    }
  };

  // Interactive Onboarding Tour State
  const [tourActive, setTourActive] = useState(false);
  const [tourStep, setTourStep] = useState(0);

  const tourSteps = [
    {
      icon: <Compass size={22} color="#3b82f6" />,
      title: "Bienvenido a SentinelOS",
      desc: "SentinelOS es tu sistema operativo unificado para infraestructura de laboratorios, monitoreo de precisión por segundo y cómputo distribuido sin fricciones.",
      badge: "Introducción"
    },
    {
      icon: <Activity size={22} color="#10b981" />,
      title: "Telemetría y Recursos en Vivo",
      desc: "Monitorea la carga en tiempo real de tu procesador (CPU), memoria (RAM) y aceleradores gráficos (GPU), además de tasas de transferencia de red y almacenamiento.",
      badge: "Telemetría"
    },
    {
      icon: <Cpu size={22} color="#8b5cf6" />,
      title: "Topología y Modelos de Hardware",
      desc: "Identifica el modelo exacto de CPU, capacidad de memoria física y GPU dedicada con su memoria VRAM y versión de driver activo.",
      badge: "Hardware"
    },
    {
      icon: <Network size={22} color="#06b6d4" />,
      title: "Nodos Satélite y Red Mesh",
      desc: "Conecta servidores adicionales en diferentes redes usando el comando de vinculación rápida para supervisar tu infraestructura de forma centralizada.",
      badge: "Multi-Servidor"
    },
    {
      icon: <Shield size={22} color="#10b981" />,
      title: "Túnel Seguro Zero-Trust (Tailscale)",
      desc: "Accede al sistema desde cualquier celular o equipo remoto a través de túneles cifrados y MagicDNS sin abrir puertos vulnerables en tu router.",
      badge: "Seguridad"
    },
    {
      icon: <TerminalSquare size={22} color="#f59e0b" />,
      title: "Gobernanza y Agente STEM",
      desc: "Accede a la consola inteligente de laboratorio para ejecutar diagnósticos y coordinar herramientas automatizadas de investigación.",
      badge: "Gobernanza"
    }
  ];

  useEffect(() => {
    try {
      const welcomeSeen = localStorage.getItem('sentinel_welcome_seen_v2');
      if (!welcomeSeen) {
        const timer = setTimeout(() => {
          setShowWelcomeModal(true);
        }, 800);
        return () => clearTimeout(timer);
      }
    } catch (e) {}
  }, []);

  const handleScanLan = async () => {
    setScanningLan(true);
    try {
      const res = await fetch(`${API_URL}/mesh/scan`, { method: 'POST' });
      if (res.ok) {
        const d = await res.json();
        if (d.nodes) setMeshDiscoveredNodes(d.nodes);
        addNotification(`Escaneo LAN completado. ${d.scanned || 0} nodos encontrados en la red.`, 'info');
      }
    } catch (e) {
      addNotification('Error al escanear la red local LAN.', 'error');
    } finally {
      setScanningLan(false);
    }
  };

  useEffect(() => {
    if (!tourActive) return;
    if (tourStep === 0) {
      setActiveTab('overview');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (tourStep === 1) {
      setActiveTab('overview');
      const el = document.getElementById('tour-system-load');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else if (tourStep === 2) {
      setActiveTab('overview');
      const el = document.getElementById('tour-hardware-specs');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else if (tourStep === 3) {
      setActiveTab('network');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (tourStep === 4) {
      setActiveTab('overview');
      const el = document.getElementById('tour-tailscale-widget');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else if (tourStep === 5) {
      setActiveTab('sentinel');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [tourStep, tourActive]);

  const handleSkipTour = () => {
    setTourActive(false);
    try {
      localStorage.setItem('sentinel_onboarding_completed', 'true');
    } catch (e) {}
  };

  const handleNextTour = () => {
    if (tourStep < tourSteps.length - 1) {
      setTourStep(prev => prev + 1);
    } else {
      handleSkipTour();
    }
  };

  const handlePrevTour = () => {
    if (tourStep > 0) {
      setTourStep(prev => prev - 1);
    }
  };

  // Modals & Expansions
  const [dockerModal, setDockerModal] = useState(false);
  const [expandedDocker, setExpandedDocker] = useState(null);

  // Form State
  const [dForm, setDForm] = useState({ name: '', image: '', ports: '', env: '', restart: 'no' });
  const [sysLogs, setSysLogs] = useState("");
  const [fsPath, setFsPath] = useState('/');
  const [fsData, setFsData] = useState({ dirs: [], files: [] });
  const [auditData, setAuditData] = useState([]);
  const [speedtestResult, setSpeedtestResult] = useState(null);
  const [speedtestRunning, setSpeedtestRunning] = useState(false);
  const [wsLogs, setWsLogs] = useState([]);
  const [marketplaceSearch, setMarketplaceSearch] = useState("");
  const [marketplaceResults, setMarketplaceResults] = useState([]);
  const [marketplaceSearching, setMarketplaceSearching] = useState(false);
  const [marketplaceTab, setMarketplaceTab] = useState('store');
  const [installedSnaps, setInstalledSnaps] = useState([]);
  const [servicesData, setServicesData] = useState([]);
  const [isNetworkScanning, setIsNetworkScanning] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [installModalApp, setInstallModalApp] = useState(null);
  const [terminalPopupApp, setTerminalPopupApp] = useState(null); // { app, minimized, status: 'installing'|'completed' }
  const [sandboxTools, setSandboxTools] = useState([]);
  const [sandboxTab, setSandboxTab] = useState('arsenal');
  const [sandboxSessions, setSandboxSessions] = useState([]); // [{id, tool, active: true}]
  const [aptData, setAptData] = useState({ updates: [], count: 0 });
  const [zDist, setZDist] = useState(10);
  const [dragSpeed, setDragSpeed] = useState(null);
  const [dragFan, setDragFan] = useState(null);
  const [printerHistory, setPrinterHistory] = useState(null);
  const terminalRef = React.useRef(null);
  const installTerminalRef = React.useRef(null);

  // Persistent Multi-Server Web Terminals State
  const [terminalTabs, setTerminalTabs] = useState(() => [
    {
      id: 'term-local',
      serverId: 'local',
      serverName: 'Host Maestro (Local)',
      title: 'Host Maestro',
      fontSize: 14,
      status: 'connecting',
      sessionId: 'sentinel-local-main'
    }
  ]);
  const [activeTerminalTabId, setActiveTerminalTabId] = useState('term-local');
  const [isFullscreenTerminal, setIsFullscreenTerminal] = useState(false);
  const [showNewTerminalModal, setShowNewTerminalModal] = useState(false);
  const [networkDetails, setNetworkDetails] = useState(null);
  const [netChecking, setNetChecking] = useState(false);
  const [showNetQuickModal, setShowNetQuickModal] = useState(false);

  const handleCheckNetworkDetails = async () => {
    setNetChecking(true);
    try {
      const res = await fetch(`${API_URL}/network/details`);
      if (res.ok) {
        const d = await res.json();
        setNetworkDetails(d);
        if (d.internet?.has_internet) {
          addNotification(`Conectado a Internet (${d.internet.latency_ms || 25}ms)`, "success");
        } else {
          addNotification("Modo Red Local: Operando 100% en LAN sin Internet", "info");
        }
      }
    } catch (e) {
      addNotification("Error al consultar el estado de red", "error");
    } finally {
      setNetChecking(false);
    }
  };

  // References for Web Terminals
  const webTerminalContainerRefs = React.useRef({});
  const webTerminalInstances = React.useRef({});
  
  // Refs to store actual xterm instances and websockets for sandbox sessions
  const sandboxTerminalsRef = React.useRef({});
  const sandboxWsRef = React.useRef({});
  const sandboxContainerRefs = React.useRef({});

  useEffect(() => {
    let interval;
    if (activeTab === 'logs') {
      const fetchLogs = async () => {
        try {
          const res = await fetch(`${API_URL}/logs`);
          if (res.ok) {
            const body = await res.json();
            const logLines = (body.logs || '').split('\n').filter(Boolean).slice(-100);
            setWsLogs(logLines);
            setSysLogs(body.logs || "");
          }
        } catch(e) {}
      };
      fetchLogs();
      interval = setInterval(fetchLogs, 2000);
    }

    if (activeTab === 'processes') {
      const fetchLocalServices = async () => {
        try {
          const res = await fetch(`${API_URL}/services`);
          if (res.ok) {
            const body = await res.json();
            setServicesData(body.services || []);
          }
        } catch(e) {}
      };
      fetchLocalServices();
      interval = setInterval(fetchLocalServices, 3000);
    }
    
    if (activeTab === 'sandbox') {
      const fetchTools = async () => {
        try {
          const res = await fetch(`${API_URL}/sandbox/tools`);
          if (res.ok) {
             const data = await res.json();
             setSandboxTools(data.results);
          }
        } catch(e) {}
      };
      fetchTools();
      interval = setInterval(fetchTools, 5000);
    }
    return () => clearInterval(interval);
  }, [activeTab]);

  const loadAuditData = async () => {
    try {
      const res = await fetch(`${API_URL}/files/audit`);
      const d = await res.json();
      setAuditData(d.logs || []);
    } catch(e){}
  };

  const handleWoL = async (mac) => {
    try {
      await fetch(`${API_URL}/network/wol`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mac })
      });
      alert("Magic Packet Sent to " + mac);
    } catch (e) { alert("WoL Failed"); }
  };

  const runSpeedtest = async () => {
    setSpeedtestRunning(true);
    try {
      const res = await fetch(`${API_URL}/network/speedtest`);
      const rdata = await res.json();
      setSpeedtestResult(rdata);
    } catch (e) { alert("Speedtest Failed"); }
    setSpeedtestRunning(false);
  };

  const installApp = async (id) => {
    // This is just fallback if needed, actual install runs through websocket now
  };

  const searchMarketplace = async (e) => {
    e.preventDefault();
    if (!marketplaceSearch) return;
    setMarketplaceSearching(true);
    try {
      const res = await fetch(`${API_URL}/marketplace/search?q=${encodeURIComponent(marketplaceSearch)}`);
      const rdata = await res.json();
      setMarketplaceResults(rdata.results || []);
    } catch(e) { console.error(e); }
    setMarketplaceSearching(false);
  };

  const loadInstalledSnaps = async () => {
    try {
      const res = await fetch(`${API_URL}/marketplace/installed`);
      const rdata = await res.json();
      setInstalledSnaps(rdata.results || []);
    } catch(e) { console.error(e); }
  };

  useEffect(() => {
    if (activeTab === 'marketplace' && marketplaceTab === 'installed') {
      loadInstalledSnaps();
    }
  }, [activeTab, marketplaceTab]);

  const uninstallSnap = async (id) => {
    if(!confirm(`Are you sure you want to uninstall ${id}?`)) return;
    try {
      await fetch(`${API_URL}/marketplace/uninstall`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: id })
      });
      addNotification(`Desinstalando ${id} en segundo plano...`, "info");
      setTimeout(loadInstalledSnaps, 5000);
    } catch(e) { addNotification("Falló desinstalación", "error"); }
  };

  const forceNetworkScan = async (mode="quick") => {
    setIsNetworkScanning(true);
    addNotification(`Escaneo ${mode === 'deep' ? 'profundo' : 'rápido'} iniciado en segundo plano.`, "info");
    try {
      await fetch(`${API_URL}/network/scan/${mode}`);
    } catch(e) { console.error(e); }
    setIsNetworkScanning(false);
  };

  const lastAptFetchRef = useRef(0);
  const fetchDataInFlightRef = useRef(false);
  const fetchData = async () => {
    if (fetchDataInFlightRef.current) return;
    fetchDataInFlightRef.current = true;
    try {
      const res = await fetch(`${API_URL}/data`, { signal: AbortSignal.timeout(30000) });
      if (!res.ok) throw new Error(`/api/data respondió HTTP ${res.status}`);
      const rdata = await res.json();
      if (!rdata || typeof rdata !== 'object' || !rdata.system) {
        throw new Error('/api/data respondió, pero no contiene telemetría del sistema');
      }
      setData(rdata);
      setApiError('');
      if (rdata.notifications && rdata.notifications.length > 0) {
        rdata.notifications.forEach(n => addNotification(n.msg, n.type));
      }
      
      // Consultar servicios solo cuando el usuario está en la pestaña procesos
      if (activeTab === 'processes') {
        const svcRes = await fetch(`${API_URL}/services`, { signal: AbortSignal.timeout(2000) });
        if (svcRes.ok) setServicesData((await svcRes.json()).services || []);
      }

      // Consultar paquetes cada 60 segundos como máximo, no cada 2s
      const now = Date.now();
      if (now - lastAptFetchRef.current > 60000) {
        lastAptFetchRef.current = now;
        const aptRes = await fetch(`${API_URL}/apt`, { signal: AbortSignal.timeout(3000) });
        if (aptRes.ok) setAptData(await aptRes.json());
      }

      if (activeTab === 'files') {
        const fsRes = await fetch(`${API_URL}/fs?path=${encodeURIComponent(fsPath)}`, { signal: AbortSignal.timeout(2000) });
        if (fsRes.ok) setFsData(await fsRes.json());
      }

      if (activeTab === 'printer') {
        const histRes = await fetch(`${API_URL}/printer/history`, { signal: AbortSignal.timeout(2000) });
        if (histRes.ok) setPrinterHistory(await histRes.json());
      }
    } catch (e) {
      console.error("fetchData error:", e);
      setApiError(e?.message || 'No se pudo completar la solicitud a /api/data');
    } finally {
      fetchDataInFlightRef.current = false;
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2500);
    return () => clearInterval(interval);
  }, [activeTab, fsPath]);

  const handleAction = async (endpoint, body) => {
    try {
      await fetch(`${API_URL}/${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      fetchData();
    } catch (e) { console.error(e); }
  };

  // Manejo del ciclo de vida de las terminales Web persistentes (Multi-Servidor)
  useEffect(() => {
    terminalTabs.forEach(tab => {
      const el = webTerminalContainerRefs.current[tab.id];
      if (!el) return;

      // Si la terminal ya existe para esta pestaña, sincronizar configuración si cambió
      if (webTerminalInstances.current[tab.id]) {
        const existing = webTerminalInstances.current[tab.id];
        if (existing.term && existing.term.options.fontSize !== tab.fontSize) {
          existing.term.options.fontSize = tab.fontSize;
          existing.fitAddon.fit();
        }
        return;
      }

      // Crear nueva instancia de xterm.js con tema cyberpunk / oscuro premium
      const term = new TerminalXTerm({
        theme: {
          background: '#070b14',
          foreground: '#e2e8f0',
          cursor: '#38bdf8',
          cursorAccent: '#070b14',
          selectionBackground: 'rgba(56, 189, 248, 0.35)',
          black: '#0f172a',
          red: '#ef4444',
          green: '#10b981',
          yellow: '#f59e0b',
          blue: '#3b82f6',
          magenta: '#a855f7',
          cyan: '#06b6d4',
          white: '#f8fafc',
          brightBlack: '#475569',
          brightRed: '#f87171',
          brightGreen: '#34d399',
          brightYellow: '#fbbf24',
          brightBlue: '#60a5fa',
          brightMagenta: '#c084fc',
          brightCyan: '#22d3ee',
          brightWhite: '#ffffff'
        },
        fontFamily: 'Consolas, "Fira Code", monospace',
        fontSize: tab.fontSize || 14,
        lineHeight: 1.25,
        cursorBlink: true,
        cursorStyle: 'block',
        allowTransparency: true
      });

      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(el);
      fitAddon.fit();

      // Determinar WebSocket URL según si es el Host local o un Servidor Remoto de la malla
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      let wsUrl = '';
      if (tab.serverId === 'local') {
        wsUrl = `${protocol}//${window.location.host}/api/ws/terminal?session_id=${tab.sessionId}`;
      } else {
        const srv = connectedServers.find(s => s.id === tab.serverId);
        if (srv && srv.url) {
          // Utilizar el proxy de terminal del backend para evitar problemas de CORS o puertos
          wsUrl = `${protocol}//${window.location.host}/api/ws/terminal/proxy?target_url=${encodeURIComponent(srv.url)}&session_id=${tab.sessionId}&token=${encodeURIComponent(srv.token || '')}`;
        } else {
          wsUrl = `${protocol}//${window.location.host}/api/ws/terminal?session_id=${tab.sessionId}`;
        }
      }

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setTerminalTabs(prev => prev.map(t => t.id === tab.id ? { ...t, status: 'connected' } : t));
        ws.send(`RESIZE:${term.cols}:${term.rows}`);
      };

      ws.onmessage = (e) => {
        term.write(e.data);
      };

      ws.onerror = () => {
        setTerminalTabs(prev => prev.map(t => t.id === tab.id ? { ...t, status: 'error' } : t));
      };

      ws.onclose = () => {
        setTerminalTabs(prev => prev.map(t => t.id === tab.id ? { ...t, status: 'disconnected' } : t));
      };

      term.onData(data => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        }
      });

      const ro = new ResizeObserver(() => {
        try {
          fitAddon.fit();
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(`RESIZE:${term.cols}:${term.rows}`);
          }
        } catch (e) {}
      });
      ro.observe(el);

      webTerminalInstances.current[tab.id] = { term, fitAddon, ws, ro };
    });
  }, [terminalTabs, connectedServers]);

  // Sincronizar foco y redimensionado al volver a la sección 'web-terminal' desde cualquier otra parte
  useEffect(() => {
    if (activeTab === 'web-terminal' && activeTerminalTabId) {
      const activeInstance = webTerminalInstances.current[activeTerminalTabId];
      if (activeInstance) {
        const timer = setTimeout(() => {
          try {
            activeInstance.fitAddon.fit();
            activeInstance.term.focus();
            if (activeInstance.ws && activeInstance.ws.readyState === WebSocket.OPEN) {
              activeInstance.ws.send(`RESIZE:${activeInstance.term.cols}:${activeInstance.term.rows}`);
            }
          } catch (e) {}
        }, 60);
        return () => clearTimeout(timer);
      }
    }
  }, [activeTab, activeTerminalTabId]);

  const handleAddTerminalTab = (server) => {
    const srvId = server.id;
    const isLoc = server.isLocal || srvId === 'local';
    const newTabId = `term-${srvId}-${Date.now()}`;
    const newSessionId = `sentinel-${srvId}-${Date.now()}`;
    const newTab = {
      id: newTabId,
      serverId: srvId,
      serverName: server.name || (isLoc ? 'Host Maestro' : 'Servidor Remoto'),
      title: server.name || (isLoc ? 'Host Maestro' : 'Servidor Remoto'),
      fontSize: 14,
      status: 'connecting',
      sessionId: newSessionId
    };
    setTerminalTabs(prev => [...prev, newTab]);
    setActiveTerminalTabId(newTabId);
    setShowNewTerminalModal(false);
  };

  const handleCloseTerminalTab = (tabId, e) => {
    if (e) e.stopPropagation();
    const inst = webTerminalInstances.current[tabId];
    if (inst) {
      try {
        if (inst.ro) inst.ro.disconnect();
        if (inst.ws) inst.ws.close();
        if (inst.term) inst.term.dispose();
      } catch (err) {}
      delete webTerminalInstances.current[tabId];
    }
    delete webTerminalContainerRefs.current[tabId];

    const tabObj = terminalTabs.find(t => t.id === tabId);
    if (tabObj) {
      try {
        fetch(`${API_URL}/terminal/session/terminate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: tabObj.sessionId })
        }).catch(() => {});
      } catch (e) {}
    }

    setTerminalTabs(prev => {
      const filtered = prev.filter(t => t.id !== tabId);
      if (activeTerminalTabId === tabId) {
        if (filtered.length > 0) {
          setActiveTerminalTabId(filtered[0].id);
        } else {
          const newId = `term-local-${Date.now()}`;
          setActiveTerminalTabId(newId);
          return [{
            id: newId,
            serverId: 'local',
            serverName: 'Host Maestro (Local)',
            title: 'Host Maestro',
            fontSize: 14,
            status: 'connecting',
            sessionId: `sentinel-local-${Date.now()}`
          }];
        }
      }
      return filtered;
    });
  };

  const handleReconnectActiveTerminal = () => {
    const tab = terminalTabs.find(t => t.id === activeTerminalTabId);
    if (!tab) return;
    const inst = webTerminalInstances.current[tab.id];
    if (inst) {
      try {
        if (inst.ro) inst.ro.disconnect();
        if (inst.ws) inst.ws.close();
        if (inst.term) inst.term.dispose();
      } catch (e) {}
      delete webTerminalInstances.current[tab.id];
    }
    setTerminalTabs(prev => prev.map(t => t.id === tab.id ? { ...t, status: 'connecting' } : t));
  };

  const handleClearActiveTerminal = () => {
    const inst = webTerminalInstances.current[activeTerminalTabId];
    if (inst && inst.term) {
      inst.term.clear();
    }
  };

  const handleRestartActiveTerminal = () => {
    const inst = webTerminalInstances.current[activeTerminalTabId];
    if (inst && inst.ws && inst.ws.readyState === WebSocket.OPEN) {
      inst.ws.send("__SENTINEL_RESTART__");
    }
  };

  const handleChangeFontSize = (delta) => {
    setTerminalTabs(prev => prev.map(t => {
      if (t.id === activeTerminalTabId) {
        const newSize = Math.max(11, Math.min(22, (t.fontSize || 14) + delta));
        return { ...t, fontSize: newSize };
      }
      return t;
    }));
  };

  useEffect(() => {
    let ws;
    if (activeTab === 'logs') {
      setWsLogs([]);
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/logs`);
      ws.onmessage = (e) => {
        const txt = e.data;
        setWsLogs(prev => [...prev, txt].slice(-300));
        
        // Alerta roja automática si el log es crítico
        if (txt.includes("CRITICAL") || txt.includes("FATAL") || txt.includes("segfault")) {
           addNotification(`Alerta del Sistema: ${txt.substring(0, 80)}...`, "error");
        }
      };
    }
    return () => { if (ws) ws.close(); };
  }, [activeTab]);

  useEffect(() => {
    // Check all sessions and initialize any that don't have a terminal yet
    sandboxSessions.forEach(session => {
      const el = sandboxContainerRefs.current[session.id];
      if (el && !sandboxTerminalsRef.current[session.id]) {
        const term = new TerminalXTerm({ theme: { background: '#0f172a' } });
        const fitAddon = new FitAddon();
        term.loadAddon(fitAddon);
        term.open(el);
        fitAddon.fit();
        sandboxTerminalsRef.current[session.id] = term;

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/sandbox/terminal/${session.tool.id}`);
        sandboxWsRef.current[session.id] = ws;

        ws.onmessage = (e) => term.write(e.data);
        term.onData(data => { if (ws.readyState === WebSocket.OPEN) ws.send(data); });

        // Resize observer
        const ro = new ResizeObserver(() => {
          try {
            fitAddon.fit();
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(`RESIZE:${term.cols}:${term.rows}`);
            }
          } catch(e) {}
        });
        ro.observe(el);
        
        ws.onclose = () => {
          term.write("\n\r[Conexión terminada. Cierra esta pestaña para limpiar.]\r\n");
        };
      }
    });
  }, [sandboxSessions, sandboxTab]);

  useEffect(() => {
    let ws = null;
    let term = null;
    // Remove minimized dependency so we don't disconnect the terminal
    if (terminalPopupApp?.status === 'installing' && installTerminalRef.current && !installTerminalRef.current.hasChildNodes()) {
      term = new TerminalXTerm({ theme: { background: '#0f172a' } });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(installTerminalRef.current);
      fitAddon.fit();

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      let wsUrl = `${protocol}//${window.location.host}/api/ws/install/${terminalPopupApp.app.id}`;
      // Sandbox tools have a different endpoint
      if (terminalPopupApp.app.repo) {
          wsUrl = `${protocol}//${window.location.host}/api/ws/sandbox/install/${terminalPopupApp.app.id}`;
      }

      ws = new WebSocket(wsUrl);
      
      ws.onmessage = (e) => term.write(e.data);
      term.onData(data => { if (ws.readyState === WebSocket.OPEN) ws.send(data); });
      
      ws.onclose = () => {
        addNotification(`✅ Instalación de ${terminalPopupApp.app.name} finalizada.`, "success");
        setTerminalPopupApp(prev => ({...prev, status: 'completed'}));
      };
    }
    return () => {
      if (ws) ws.close();
      if (term) term.dispose();
    };
  }, [terminalPopupApp?.status, terminalPopupApp?.app?.id]);

  if (loading && !data) return <div style={{padding: '2rem'}}>Conectando con SentinelOS en {window.location.origin}…</div>;
  if (!data) return (
    <div style={{ padding: '2rem', color: '#e2e8f0', maxWidth: '720px', margin: '12vh auto' }}>
      <h2 style={{ marginBottom: '0.6rem' }}>System Offline. Cannot connect to backend.</h2>
      <p style={{ color: '#94a3b8' }}>Cockpit está intentando conectar con el backend de este equipo.</p>
      <p style={{ color: '#fca5a5', overflowWrap: 'anywhere' }}>{apiError || `No hay respuesta de ${window.location.origin}/api/data`}</p>
      <button className="btn btn-primary" onClick={() => { setLoading(true); fetchData(); }}>Reintentar conexión</button>
    </div>
  );

  const history = data.metrics_history || [];
  const current = history[history.length - 1] || { cpu: 0, ram: 0, temp: 0, net_rx: 0, net_tx: 0, disk_r: 0, disk_w: 0 };
  const cores = data.system.cpu_cores || 1;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(255,255,255,0.1)', padding: '0.5rem', borderRadius: '8px', zIndex: 1000 }}>
          <p style={{margin: 0, color: '#94a3b8', fontSize: '0.8rem'}}>{label}</p>
          {payload.map((p, i) => (
            <p key={i} style={{margin: '0.2rem 0', color: p.color, fontWeight: 'bold'}}>{p.name}: {p.value}</p>
          ))}
        </div>
      );
    }
    return null;
  };

  // --- SUB-RENDERS ---

  const renderOverview = () => {
    // Widget Data Calculations
    const dockerUp = data.containers?.filter(c => c.status.includes('Up')).length || 0;
    const dockerTotal = data.containers?.length || 0;
    const isKlipperReady = data.moonraker?.klippy_state === 'ready';
    const klippyStatus = isKlipperReady ? (data.printer?.print_stats?.state?.toUpperCase() || 'IDLE') : 'OFFLINE';
    const tsOnline = data.tailscale?.Peer ? Object.values(data.tailscale.Peer).filter(p => p.Online).length : 0;
    const uptimeSecs = data.system?.uptime || 0;
    const uptimeDays = Math.floor(uptimeSecs / 86400);
    const uptimeHours = Math.floor((uptimeSecs % 86400) / 3600);

    const isVistaCompleta = selectedServers.length === connectedServers.length && connectedServers.length > 1;
    const isMultiSelected = selectedServers.length > 1;

    return (
      <>
        {/* Barra Superior de Control y Filtros Multi-Servidor */}
        <div className="multi-server-control-bar">
          <div className="server-chip-group">
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Rendimiento:
            </span>

            {connectedServers.length > 1 && (
              <button
                className={`server-filter-chip ${isVistaCompleta ? 'vista-completa active' : ''}`}
                onClick={selectAllServers}
                title="Ver el rendimiento consolidado de todos los equipos y servidores en pantalla completa"
              >
                <Layers size={14} /> Vista Completa ({connectedServers.length} Nodos)
              </button>
            )}

            {connectedServers.map((srv) => {
              const isSelected = selectedServers.includes(srv.id);
              const isOnline = srv.isLocal ? true : remoteServersData[srv.id]?.status !== 'offline';

              return (
                <button
                  key={srv.id}
                  className={`server-filter-chip ${isSelected ? 'active' : ''}`}
                  onClick={() => toggleServerSelection(srv.id)}
                  onDoubleClick={() => selectSingleServer(srv.id)}
                  title={`Click para alternar en vista, doble click para ver únicamente ${srv.name}`}
                >
                  <div
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: isOnline ? '#10b981' : '#ef4444',
                      boxShadow: isOnline ? '0 0 6px #10b981' : 'none'
                    }}
                  />
                  {isSelected && <Check size={13} color="#60a5fa" />}
                  <span>{srv.name}</span>
                </button>
              );
            })}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            {localNodeAuth?.token && (
              <button
                className="btn btn-secondary"
                onClick={() => setServerModalOpen(true)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  fontSize: '0.82rem',
                  padding: '0.4rem 0.85rem',
                  borderColor: 'rgba(234, 179, 8, 0.4)',
                  color: '#fbbf24',
                  background: 'rgba(234, 179, 8, 0.08)'
                }}
                title="Ver o copiar el Token PIN de vinculación de este Servidor Maestro"
              >
                <Key size={14} /> Token PIN Malla
              </button>
            )}
            <button
              className="btn btn-secondary"
              onClick={() => setServerModalOpen(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontSize: '0.82rem',
                padding: '0.4rem 0.85rem'
              }}
            >
              <Server size={14} /> Conectar Servidor Remoto
            </button>
          </div>
        </div>

        {/* 1. VISTA MULTI-SERVIDOR / VISTA COMPLETA (Grid Comparativo) */}
        {isMultiSelected ? (
          <>
            {/* Resumen Global del Clúster / Red de Nodos */}
            <div className="cluster-summary-banner">
              <div className="cluster-stat-card">
                <div className="cluster-stat-icon" style={{ background: 'rgba(59, 130, 246, 0.2)' }}>
                  <Cpu size={22} color="#60a5fa" />
                </div>
                <div>
                  <div className="stat-label">Núcleos de Cómputo Clúster</div>
                  <div className="stat-value" style={{ color: '#60a5fa', fontSize: '1.4rem' }}>
                    {selectedServers.reduce((acc, id) => {
                      if (id === 'local') return acc + (data?.system?.cpu_cores || 1);
                      return acc + (remoteServersData[id]?.data?.system?.cpu_cores || 0);
                    }, 0)} Cores
                  </div>
                </div>
              </div>

              <div className="cluster-stat-card">
                <div className="cluster-stat-icon" style={{ background: 'rgba(16, 185, 129, 0.2)' }}>
                  <Database size={22} color="#34d399" />
                </div>
                <div>
                  <div className="stat-label">Memoria RAM Total Clúster</div>
                  <div className="stat-value" style={{ color: '#34d399', fontSize: '1.4rem' }}>
                    {(selectedServers.reduce((acc, id) => {
                      if (id === 'local') return acc + ((data?.system?.memory?.total || 0) / 1024**3);
                      return acc + ((remoteServersData[id]?.data?.system?.memory?.total || 0) / 1024**3);
                    }, 0)).toFixed(1)} GB
                  </div>
                </div>
              </div>

              <div className="cluster-stat-card">
                <div className="cluster-stat-icon" style={{ background: 'rgba(168, 85, 247, 0.2)' }}>
                  <Activity size={22} color="#a855f7" />
                </div>
                <div>
                  <div className="stat-label">Carga CPU Promedio</div>
                  <div className="stat-value" style={{ color: '#a855f7', fontSize: '1.4rem' }}>
                    {(selectedServers.reduce((acc, id) => {
                      if (id === 'local') return acc + (current.cpu || 0);
                      const srvHist = remoteServersData[id]?.history || [];
                      const lastCpu = srvHist[srvHist.length - 1]?.cpu ?? 0;
                      return acc + lastCpu;
                    }, 0) / selectedServers.length).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="cluster-stat-card">
                <div className="cluster-stat-icon" style={{ background: 'rgba(245, 158, 11, 0.2)' }}>
                  <Server size={22} color="#fbbf24" />
                </div>
                <div>
                  <div className="stat-label">Nodos en Visualización</div>
                  <div className="stat-value" style={{ color: '#fbbf24', fontSize: '1.4rem' }}>
                    {selectedServers.filter(id => id === 'local' || remoteServersData[id]?.status !== 'offline').length} / {selectedServers.length} Online
                  </div>
                </div>
              </div>
            </div>

            {/* Cuadrícula Comparativa de Nodos */}
            <div className="multi-node-grid">
              {selectedServers.map((srvId) => {
                const srv = connectedServers.find(s => s.id === srvId) || { id: srvId, name: srvId, isLocal: false };
                const isLocalNode = srv.isLocal;
                const nodeData = isLocalNode ? data : remoteServersData[srvId]?.data;
                const nodeHistory = isLocalNode ? history : (remoteServersData[srvId]?.history || []);
                const lastMetric = nodeHistory[nodeHistory.length - 1] || { cpu: 0, ram: 0, temp: 0, net_rx: 0, net_tx: 0, disk_r: 0, disk_w: 0 };
                const nodeCores = nodeData?.system?.cpu_cores || 1;
                const cpuUsage = lastMetric.cpu ?? 0;
                const ramUsage = lastMetric.ram ?? 0;
                const ramTotalGb = ((nodeData?.system?.memory?.total || 0) / 1024**3).toFixed(1);
                const ramUsedGb = ((nodeData?.system?.memory?.used || 0) / 1024**3).toFixed(1);
                const isOnline = isLocalNode ? true : remoteServersData[srvId]?.status !== 'offline';
                const primaryIface = nodeData?.network?.primary || { name: 'Ethernet', type: 'ethernet', speed: 1000 };
                const isWifiNode = primaryIface.type === 'wifi';

                return (
                  <div key={srvId} className="node-performance-card">
                    <div className="node-card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ background: isLocalNode ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)', padding: '0.5rem', borderRadius: '8px' }}>
                          <Server size={20} color={isLocalNode ? '#60a5fa' : '#34d399'} />
                        </div>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>{srv.name}</h3>
                            <span style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              padding: '0.15rem 0.45rem',
                              borderRadius: '4px',
                              background: isLocalNode ? 'rgba(59, 130, 246, 0.2)' : 'rgba(168, 85, 247, 0.2)',
                              color: isLocalNode ? '#60a5fa' : '#c084fc',
                              border: isLocalNode ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid rgba(168, 85, 247, 0.3)'
                            }}>
                              {isLocalNode ? 'Nodo Maestro' : 'Servidor Remoto'}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                            {srv.url || primaryIface.ip || '127.0.0.1'} • {isWifiNode ? 'Wi-Fi' : 'Ethernet'} {primaryIface.speed ? `${primaryIface.speed} Mbps` : ''}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: isOnline ? '#34d399' : '#ef4444' }}>
                          {isOnline ? 'ONLINE' : 'OFFLINE'}
                        </span>
                        <div
                          style={{
                            width: '9px',
                            height: '9px',
                            borderRadius: '50%',
                            background: isOnline ? '#10b981' : '#ef4444',
                            boxShadow: isOnline ? '0 0 8px #10b981' : 'none'
                          }}
                        />
                      </div>
                    </div>

                    <div className="node-gauge-group">
                      <div className="node-gauge-box">
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>CPU ({nodeCores}C)</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 700, color: cpuUsage > 85 ? '#ef4444' : '#38bdf8', margin: '0.2rem 0' }}>
                          {cpuUsage}%
                        </div>
                        <div className="btop-bar-container" style={{ height: '6px' }}>
                          <div className="btop-bar-fill" style={{ width: `${Math.min(cpuUsage, 100)}%`, background: cpuUsage > 85 ? '#ef4444' : '#38bdf8' }} />
                        </div>
                      </div>

                      <div className="node-gauge-box">
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>RAM ({ramTotalGb}G)</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 700, color: ramUsage > 85 ? '#ef4444' : '#34d399', margin: '0.2rem 0' }}>
                          {ramUsage}%
                        </div>
                        <div className="btop-bar-container" style={{ height: '6px' }}>
                          <div className="btop-bar-fill" style={{ width: `${Math.min(ramUsage, 100)}%`, background: ramUsage > 85 ? '#ef4444' : '#34d399' }} />
                        </div>
                      </div>

                      <div className="node-gauge-box">
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>TEMPERATURA</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 700, color: (lastMetric.temp || 0) > 75 ? '#ef4444' : '#f59e0b', margin: '0.2rem 0' }}>
                          {lastMetric.temp ? `${lastMetric.temp}°C` : 'Normal'}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                          {nodeData?.system?.uptime ? `${Math.floor(nodeData.system.uptime / 3600)}h Uptime` : 'Activo'}
                        </div>
                      </div>
                    </div>

                    <div style={{ height: 140, background: 'rgba(0,0,0,0.25)', borderRadius: '8px', padding: '0.4rem 0.6rem' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={nodeHistory}>
                          <defs>
                            <linearGradient id={`gradCpu-${srvId}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.35} />
                              <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id={`gradRam-${srvId}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#34d399" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                          <XAxis dataKey="time" hide />
                          <YAxis domain={[0, 100]} hide />
                          <Tooltip content={<CustomTooltip />} />
                          <Area type="monotone" dataKey="cpu" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill={`url(#gradCpu-${srvId})`} name="CPU %" />
                          <Area type="monotone" dataKey="ram" stroke="#34d399" strokeWidth={1.5} fillOpacity={1} fill={`url(#gradRam-${srvId})`} name="RAM %" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: '#94a3b8', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '0.5rem' }}>
                      <span title={nodeData?.system?.cpu_model || 'CPU'}>
                        {nodeData?.system?.cpu_model ? (nodeData.system.cpu_model.length > 25 ? nodeData.system.cpu_model.slice(0, 23) + '...' : nodeData.system.cpu_model) : 'Procesador Principal'}
                      </span>
                      <span>RAM: {ramUsedGb} GB / {ramTotalGb} GB</span>
                      <button
                        onClick={() => selectSingleServer(srvId)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#38bdf8',
                          fontSize: '0.76rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          padding: 0
                        }}
                      >
                        Ver Detallado &rarr;
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Gráfica Comparativa Consolidada de CPU entre Servidores */}
            <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
              <div className="panel-header" style={{ justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Activity size={20} color="#38bdf8" />
                  <h2>Comparativa de Carga de CPU en Tiempo Real (Malla de Servidores)</h2>
                </div>
                <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                  {selectedServers.map((srvId, idx) => {
                    const srv = connectedServers.find(s => s.id === srvId) || { name: srvId };
                    const colors = ['#38bdf8', '#10b981', '#a855f7', '#f59e0b', '#ec4899'];
                    const color = colors[idx % colors.length];
                    return (
                      <div key={srvId} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: color }} />
                        <span>{srv.name}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} />
                    <Tooltip content={<CustomTooltip />} />
                    {selectedServers.map((srvId, idx) => {
                      const srv = connectedServers.find(s => s.id === srvId) || { name: srvId };
                      const colors = ['#38bdf8', '#10b981', '#a855f7', '#f59e0b', '#ec4899'];
                      const color = colors[idx % colors.length];
                      if (srvId === 'local') {
                        return <Line key={srvId} type="monotone" dataKey="cpu" stroke={color} strokeWidth={2.5} dot={false} name={srv.name} />;
                      }
                      return (
                        <Line
                          key={srvId}
                          type="monotone"
                          data={remoteServersData[srvId]?.history || []}
                          dataKey="cpu"
                          stroke={color}
                          strokeWidth={2}
                          dot={false}
                          name={srv.name}
                        />
                      );
                    })}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        ) : (
          /* 2. VISTA DE 1 SOLO SERVIDOR */
          selectedServers[0] !== 'local' ? (
            (() => {
              const srvId = selectedServers[0];
              const srv = connectedServers.find(s => s.id === srvId);
              const srvData = remoteServersData[srvId]?.data || {};
              const srvHistory = remoteServersData[srvId]?.history || [];
              const srvCurrent = srvHistory[srvHistory.length - 1] || { cpu: 0, ram: 0, temp: 0, net_rx: 0, net_tx: 0, disk_r: 0, disk_w: 0 };
              const srvCores = srvData.system?.cpu_cores || 1;
              const isOnline = remoteServersData[srvId]?.status !== 'offline';

              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div className="glass-panel" style={{ padding: '1rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <Server size={24} color="#10b981" />
                      <div>
                        <h2 style={{ margin: 0, fontSize: '1.2rem', color: '#ffffff' }}>{srv?.name}</h2>
                        <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontFamily: 'monospace' }}>{srv?.url}</span>
                      </div>
                    </div>
                    <span style={{
                      padding: '0.3rem 0.8rem',
                      borderRadius: '6px',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      background: isOnline ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: isOnline ? '#34d399' : '#f87171',
                      border: isOnline ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(239, 68, 68, 0.4)'
                    }}>
                      {isOnline ? 'CONECTADO Y OPERATIVO' : 'SIN CONEXIÓN'}
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
                    <div className="glass-panel">
                      <div className="panel-header"><Cpu /><h2>Carga de CPU y Hardware Remoto</h2></div>
                      <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1rem' }}>
                        <div><div className="stat-label">CPU ({srvCores} Cores)</div><div className="stat-value" style={{ color: '#3b82f6', fontSize: '1.5rem' }}>{srvCurrent.cpu}%</div></div>
                        <div><div className="stat-label">RAM</div><div className="stat-value" style={{ color: '#10b981', fontSize: '1.5rem' }}>{srvCurrent.ram}%</div></div>
                        <div><div className="stat-label">Temperatura</div><div className="stat-value" style={{ color: '#f59e0b', fontSize: '1.5rem' }}>{srvCurrent.temp ? `${srvCurrent.temp}°C` : 'Normal'}</div></div>
                      </div>
                      <div style={{ height: 260 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={srvHistory}>
                            <defs>
                              <linearGradient id="colorCpuRemote" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/><stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/></linearGradient>
                              <linearGradient id="colorRamRemote" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/><stop offset="95%" stopColor="#10b981" stopOpacity={0}/></linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="time" hide />
                            <YAxis domain={[0, 100]} hide />
                            <Tooltip content={<CustomTooltip />} />
                            <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fillOpacity={1} fill="url(#colorCpuRemote)" name="CPU %" />
                            <Area type="monotone" dataKey="ram" stroke="#10b981" fillOpacity={1} fill="url(#colorRamRemote)" name="RAM %" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="glass-panel">
                      <div className="panel-header"><Database /><h2>Memoria y Swap Remoto</h2></div>
                      <div style={{ fontFamily: 'monospace', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                            <span>Uso RAM: {(((srvData.system?.memory?.used || 0) / 1024**3)).toFixed(1)} GiB</span>
                            <span>Total: {(((srvData.system?.memory?.total || 0) / 1024**3)).toFixed(1)} GiB</span>
                          </div>
                          <div className="btop-bar-container" style={{ height: '16px' }}>
                            <div className="btop-bar-fill" style={{ width: `${Math.min(srvCurrent.ram || 0, 100)}%`, background: '#10b981' }} />
                          </div>
                        </div>

                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
                          <div style={{ color: '#94a3b8', fontSize: '0.8rem', marginBottom: '0.5rem', fontWeight: 700 }}>PROPIEDADES DEL SISTEMA</div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', margin: '0.3rem 0' }}>
                            <span style={{ color: '#64748b' }}>CPU Model:</span>
                            <span style={{ color: '#ffffff' }}>{srvData.system?.cpu_model || 'Servidor ProLiant / Xeon'}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', margin: '0.3rem 0' }}>
                            <span style={{ color: '#64748b' }}>Núcleos:</span>
                            <span style={{ color: '#38bdf8' }}>{srvCores} Cores Físicos / Lógicos</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', margin: '0.3rem 0' }}>
                            <span style={{ color: '#64748b' }}>Uptime:</span>
                            <span style={{ color: '#34d399' }}>{Math.floor((srvData.system?.uptime || 0) / 3600)} Horas Activas</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()
          ) : (
            /* Vista del Host Local */
            <>
              <div className="widget-grid">
                <div className="summary-widget">
                  <div className="widget-icon"><Power size={24}/></div>
                  <div className="widget-info">
                    <span className="widget-title">Uptime</span>
                    <span className="widget-value">{uptimeDays}d {uptimeHours}h</span>
                  </div>
                </div>
                <div className="summary-widget">
                  <div className="widget-icon"><Database size={24}/></div>
                  <div className="widget-info">
                    <span className="widget-title">Docker</span>
                    <span className="widget-value" style={{color: dockerUp > 0 ? 'var(--success)' : ''}}>{dockerUp} / {dockerTotal} UP</span>
                  </div>
                </div>
                {isKlipperReady && (
                  <div className="summary-widget">
                    <div className="widget-icon"><Printer size={24}/></div>
                    <div className="widget-info">
                      <span className="widget-title">3D Printer</span>
                      <span className="widget-value" style={{color: isKlipperReady ? 'var(--success)' : 'var(--danger)'}}>{klippyStatus}</span>
                    </div>
                  </div>
                )}
                <div className="summary-widget" id="tour-tailscale-widget">
                  <div className="widget-icon"><Shield size={24}/></div>
                  <div className="widget-info">
                    <span className="widget-title">VPN Tailscale</span>
                    <span className="widget-value" style={{color: 'var(--accent)'}}>{tsOnline} PEERS</span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '1.5rem' }}>
                <div className="glass-panel" id="tour-system-load">
                  <div className="panel-header"><Cpu /><h2>System Load & Hardware Telemetry</h2></div>
                  <div style={{display: 'flex', flexWrap: 'wrap', gap: '1.5rem', marginBottom: '1rem'}}>
                    <div><div className="stat-label">CPU ({cores} Cores)</div><div className="stat-value" style={{color: '#3b82f6', fontSize: '1.5rem'}}>{current.cpu}%</div></div>
                    <div><div className="stat-label">RAM</div><div className="stat-value" style={{color: '#10b981', fontSize: '1.5rem'}}>{current.ram}%</div></div>
                    <div><div className="stat-label">CPU Temp</div><div className="stat-value" style={{color: '#f59e0b', fontSize: '1.5rem'}}>{current.temp}°C</div></div>
                    {data.system?.gpu?.has_gpu && (
                      <div>
                        <div className="stat-label">GPU ({data.system.gpu.model ? (data.system.gpu.model.length > 20 ? data.system.gpu.model.slice(0, 18) + '...' : data.system.gpu.model) : 'GPU'})</div>
                        <div className="stat-value" style={{color: '#a855f7', fontSize: '1.5rem'}}>
                          {current.gpu ?? data.system.gpu.usage ?? 0}%
                        </div>
                      </div>
                    )}
                    {data.system?.gpu?.has_gpu && (current.gpu_temp || data.system.gpu.temp) > 0 && (
                      <div>
                        <div className="stat-label">GPU Temp</div>
                        <div className="stat-value" style={{color: '#ec4899', fontSize: '1.5rem'}}>
                          {current.gpu_temp || data.system.gpu.temp}°C
                        </div>
                      </div>
                    )}
                  </div>
                  <div style={{ height: 280 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={history}>
                        <defs>
                          <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/><stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/></linearGradient>
                          <linearGradient id="colorRam" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/><stop offset="95%" stopColor="#10b981" stopOpacity={0}/></linearGradient>
                          <linearGradient id="colorGpu" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/><stop offset="95%" stopColor="#a855f7" stopOpacity={0}/></linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="time" hide />
                        <YAxis hide />
                        <Tooltip content={<CustomTooltip />} />
                        <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fillOpacity={1} fill="url(#colorCpu)" name="CPU %" />
                        <Area type="monotone" dataKey="ram" stroke="#10b981" fillOpacity={1} fill="url(#colorRam)" name="RAM %" />
                        {data.system?.gpu?.has_gpu && (
                          <Area type="monotone" dataKey="gpu" stroke="#a855f7" fillOpacity={1} fill="url(#colorGpu)" name="GPU %" />
                        )}
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Hardware Specifications Badges */}
                  <div id="tour-hardware-specs" style={{
                    display: 'grid',
                    gridTemplateColumns: data.system?.gpu?.has_gpu ? 'repeat(auto-fit, minmax(180px, 1fr))' : 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '0.85rem',
                    marginTop: '1.25rem',
                    paddingTop: '1rem',
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)'
                  }}>
                    {/* CPU Specs */}
                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem 0.9rem', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem', color: '#3b82f6', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.04em' }}>
                        <Cpu size={14} /> PROCESADOR (CPU)
                      </div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={data.system?.cpu_model || 'Intel/AMD Processor'}>
                        {data.system?.cpu_model || 'Procesador Principal'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        <span>{cores} Núcleos</span> • <span>{data.system?.cpu_freqs?.[0] ? `${data.system.cpu_freqs[0]} MHz` : 'Frecuencia Dinámica'}</span>
                      </div>
                    </div>

                    {/* RAM Specs */}
                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem 0.9rem', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem', color: '#10b981', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.04em' }}>
                        <Database size={14} /> MEMORIA (RAM)
                      </div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                        {((data.system?.memory?.total || 0) / 1024**3).toFixed(1)} GB Total
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        <span style={{ color: '#10b981' }}>{((data.system?.memory?.used || 0) / 1024**3).toFixed(1)} GB en uso</span> • <span>{((data.system?.memory?.available || 0) / 1024**3).toFixed(1)} GB libres</span>
                      </div>
                    </div>

                    {/* GPU Specs */}
                    {data.system?.gpu?.has_gpu && (
                      <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem 0.9rem', borderRadius: '8px', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem', color: '#a855f7', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.04em' }}>
                          <Zap size={14} /> ACELERADOR (GPU)
                        </div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={data.system.gpu.model}>
                          {data.system.gpu.model || 'GPU Dedicada'}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                          <span>{data.system.gpu.vram_total_mb ? `${(data.system.gpu.vram_total_mb / 1024).toFixed(1)} GB VRAM` : 'Aceleración Directa'}</span>
                          {data.system.gpu.driver ? <span> • Driver {data.system.gpu.driver}</span> : null}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="glass-panel">
                  <div className="panel-header"><Network /><h2>Network I/O</h2></div>
                  <div style={{display: 'flex', gap: '2rem', marginBottom: '1rem'}}>
                    <div><div className="stat-label">Download</div><div className="stat-value" style={{color: '#8b5cf6', fontSize: '1.5rem'}}>{current.net_rx} MB/s</div></div>
                    <div><div className="stat-label">Upload</div><div className="stat-value" style={{color: '#ec4899', fontSize: '1.5rem'}}>{current.net_tx} MB/s</div></div>
                  </div>
                  <div style={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={history}>
                        <defs>
                          <linearGradient id="colorRx" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/><stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/></linearGradient>
                          <linearGradient id="colorTx" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ec4899" stopOpacity={0.3}/><stop offset="95%" stopColor="#ec4899" stopOpacity={0}/></linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="time" hide />
                        <YAxis hide />
                        <Tooltip content={<CustomTooltip />} />
                        <Area type="monotone" dataKey="net_rx" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorRx)" name="Down (MB/s)" />
                        <Area type="monotone" dataKey="net_tx" stroke="#ec4899" fillOpacity={1} fill="url(#colorTx)" name="Up (MB/s)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="glass-panel">
                  <div className="panel-header"><HardDrive /><h2>Storage I/O</h2></div>
                  <div style={{display: 'flex', gap: '2rem', marginBottom: '1rem'}}>
                    <div><div className="stat-label">Read</div><div className="stat-value" style={{color: '#06b6d4', fontSize: '1.5rem'}}>{current.disk_r} MB/s</div></div>
                    <div><div className="stat-label">Write</div><div className="stat-value" style={{color: '#f43f5e', fontSize: '1.5rem'}}>{current.disk_w} MB/s</div></div>
                    <div style={{marginLeft: 'auto', textAlign:'right'}}><div className="stat-label">Used Space</div><div className="stat-value" style={{fontSize: '1.1rem'}}>{((data.system.disks && data.system.disks[0]?.used)/1024**3 || 0).toFixed(1)} GB / {((data.system.disks && data.system.disks[0]?.total)/1024**3 || 0).toFixed(0)} GB</div></div>
                  </div>
                  <div style={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={history}>
                        <defs>
                          <linearGradient id="colorR" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/><stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/></linearGradient>
                          <linearGradient id="colorW" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/><stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/></linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="time" hide />
                        <YAxis hide />
                        <Tooltip content={<CustomTooltip />} />
                        <Area type="step" dataKey="disk_r" stroke="#06b6d4" fillOpacity={1} fill="url(#colorR)" name="Read (MB/s)" />
                        <Area type="step" dataKey="disk_w" stroke="#f43f5e" fillOpacity={1} fill="url(#colorW)" name="Write (MB/s)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                
                <div className="glass-panel">
                  <div className="panel-header"><Activity /><h2>Load Average ({cores} Cores)</h2></div>
                  <div style={{display: 'flex', gap: '2rem', justifyContent:'center', marginTop:'2rem'}}>
                    <div style={{textAlign:'center'}}>
                      <div className="stat-value" style={{fontSize: '2rem', color: data.system.loadavg[0] > cores ? 'var(--danger)' : 'var(--text-primary)'}}>{data.system.loadavg[0].toFixed(2)}</div>
                      <div className="stat-label">1 Min</div>
                    </div>
                    <div style={{textAlign:'center'}}>
                      <div className="stat-value" style={{fontSize: '2rem', color: data.system.loadavg[1] > cores ? 'var(--warning)' : 'var(--text-primary)'}}>{data.system.loadavg[1].toFixed(2)}</div>
                      <div className="stat-label">5 Min</div>
                    </div>
                    <div style={{textAlign:'center'}}>
                      <div className="stat-value" style={{fontSize: '2rem', color: data.system.loadavg[2] > cores ? 'var(--warning)' : 'var(--text-primary)'}}>{data.system.loadavg[2].toFixed(2)}</div>
                      <div className="stat-label">15 Min</div>
                    </div>
                  </div>
                </div>
                <div className="glass-panel">
                  <div className="panel-header"><Database /><h2>Memory & Swap</h2></div>
                  <div style={{fontFamily: 'monospace', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                    <div>
                      <div style={{display:'flex', justifyContent:'space-between', marginBottom:'0.2rem'}}>
                        <span>Used: {(data.system.memory.used/1024**3).toFixed(1)} GiB</span>
                        <span>Total: {(data.system.memory.total/1024**3).toFixed(1)} GiB</span>
                      </div>
                      <div className="btop-bar-container" style={{height:'16px'}}>
                        <div className="btop-bar-fill" style={{width: `${(data.system.memory.used/data.system.memory.total)*100}%`, background: '#10b981'}}></div>
                      </div>
                      <div style={{display:'flex', justifyContent:'space-between', marginTop:'0.2rem', color:'var(--text-secondary)'}}>
                        <span>Avail: {(data.system.memory.available/1024**3).toFixed(1)} GiB</span>
                        <span>Cached: {(data.system.memory.cached/1024**3).toFixed(1)} GiB</span>
                        <span>Free: {(data.system.memory.free/1024**3).toFixed(1)} GiB</span>
                      </div>
                    </div>
                    <div>
                      <div style={{display:'flex', justifyContent:'space-between', marginBottom:'0.2rem'}}>
                        <span>Swap Used: {((data.system.memory.swap_total - data.system.memory.swap_free)/1024**3).toFixed(1)} GiB</span>
                        <span>Total: {(data.system.memory.swap_total/1024**3).toFixed(1)} GiB</span>
                      </div>
                      <div className="btop-bar-container" style={{height:'16px'}}>
                        <div className="btop-bar-fill" style={{width: `${data.system.memory.swap_total > 0 ? ((data.system.memory.swap_total - data.system.memory.swap_free)/data.system.memory.swap_total)*100 : 0}%`, background: '#f59e0b'}}></div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="glass-panel">
                  <div className="panel-header"><HardDrive /><h2>Disks & Mounts</h2></div>
                  <div style={{fontFamily: 'monospace', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '1rem', overflowY:'auto', maxHeight:'300px'}}>
                    {data.system.disks?.map((d, i) => {
                       const usedPct = (d.used / d.total) * 100;
                       const color = usedPct > 90 ? '#ef4444' : usedPct > 70 ? '#f59e0b' : '#3b82f6';
                       return (
                         <div key={i}>
                           <div style={{display:'flex', justifyContent:'space-between', marginBottom:'0.2rem'}}>
                             <span><span style={{color:'var(--text-secondary)'}}>{d.device}</span> <span style={{fontWeight:'bold'}}>{d.mountpoint}</span></span>
                             <span>{usedPct.toFixed(0)}% ({(d.free/1024**3).toFixed(1)}G free)</span>
                           </div>
                           <div className="btop-bar-container" style={{height:'10px'}}>
                             <div className="btop-bar-fill" style={{width: `${usedPct}%`, background: color}}></div>
                           </div>
                         </div>
                       );
                    })}
                  </div>
                </div>

                <div className="glass-panel">
                  <div className="panel-header"><Activity /><h2>S.M.A.R.T. Health</h2></div>
                  <table className="os-table">
                    <thead><tr><th>Device</th><th>Model</th><th>Health</th><th>Temp</th></tr></thead>
                    <tbody>
                      {data.system.smart?.map((d, i) => (
                        <tr key={i}>
                          <td style={{fontFamily: 'monospace', color: 'var(--text-secondary)'}}>{d.device}</td>
                          <td>{d.model}</td>
                          <td style={{color: d.health === 'PASSED' ? 'var(--success)' : 'var(--danger)', fontWeight: 'bold'}}>{d.health}</td>
                          <td style={{color: 'var(--warning)'}}>{d.temp}°C</td>
                        </tr>
                      ))}
                      {(!data.system.smart || data.system.smart.length === 0) && (
                        <tr><td colSpan="4" style={{textAlign: 'center', color: 'var(--text-secondary)'}}>No SMART data available</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="glass-panel">
                  <div className="panel-header"><User /><h2>Active Users</h2></div>
                  <table className="os-table">
                    <thead><tr><th>User</th><th>Terminal</th><th>Login Time</th><th>IP</th></tr></thead>
                    <tbody>
                      {data.system.active_users?.map((u, i) => (
                        <tr key={i}>
                          <td style={{fontWeight: 'bold', color: 'var(--accent)'}}>{u.user}</td>
                          <td>{u.terminal}</td>
                          <td>{u.login_time}</td>
                          <td style={{fontFamily: 'monospace'}}>{u.ip}</td>
                        </tr>
                      ))}
                      {(!data.system.active_users || data.system.active_users.length === 0) && (
                        <tr><td colSpan="4" style={{textAlign: 'center', color: 'var(--text-secondary)'}}>No active users</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="glass-panel">
                  <div className="panel-header"><Cpu /><h2>CPU Frequencies</h2></div>
                  <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem'}}>
                    {data.system.cpu_freqs?.map((freq, i) => (
                      <div key={i} style={{background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', textAlign: 'center'}}>
                        <div style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.25rem'}}>Core {i}</div>
                        <div style={{color: 'var(--accent)', fontFamily: 'monospace', fontSize: '1.2rem'}}>{freq.toFixed(0)} MHz</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )
        )}
      </>
    );
  };

  const renderPrinter = () => {
    // 1. Descubrir todas las instancias de Klipper / Moonraker disponibles en el cluster
    const allKlipperPrinters = [];

    // Nodo local (Host Maestro)
    const isLocalKlippy = data?.moonraker?.klippy_state === 'ready' || data?.printer?.print_stats;
    if (isLocalKlippy || data?.moonraker?.klippy_state) {
      allKlipperPrinters.push({
        id: 'local',
        name: 'Host Maestro (Local)',
        isLocal: true,
        data: data,
        moonraker: data.moonraker || {},
        printer: data.printer || {},
        klippy_state: data.moonraker?.klippy_state || (data.printer?.print_stats ? 'ready' : 'offline'),
        url: API_URL
      });
    }

    // Servidores satélites remotos conectados (ej. Servidor HP ProLiant, Raspberry Pi)
    Object.entries(remoteServersData).forEach(([srvId, srvObj]) => {
      const srv = connectedServers.find(s => s.id === srvId) || { id: srvId, name: srvId };
      const rData = srvObj?.data;
      const isRemoteKlippy = rData?.moonraker?.klippy_state === 'ready' || rData?.printer?.print_stats;
      if (isRemoteKlippy || rData?.moonraker?.klippy_state) {
        allKlipperPrinters.push({
          id: srvId,
          name: srv.name || srvId,
          isLocal: false,
          data: rData,
          moonraker: rData.moonraker || {},
          printer: rData.printer || {},
          klippy_state: rData.moonraker?.klippy_state || (rData.printer?.print_stats ? 'ready' : 'offline'),
          url: srv.url || ''
        });
      }
    });

    // 2. Determinar la impresora activa:
    // Si el usuario seleccionó una específica se usa, de lo contrario se auto-selecciona la primera lista para imprimir
    let activePrinter = null;
    if (selectedPrinterServer !== 'auto') {
      activePrinter = allKlipperPrinters.find(p => p.id === selectedPrinterServer);
    }
    if (!activePrinter) {
      activePrinter = allKlipperPrinters.find(p => p.klippy_state === 'ready') || allKlipperPrinters[0] || null;
    }

    // Enrutador de comandos 3D multi-servidor (local y satélites)
    const handlePrinterAction = async (endpoint, payload) => {
      if (!activePrinter) return;
      if (activePrinter.isLocal) {
        return handleAction(endpoint, payload);
      }
      const targetUrl = activePrinter.url.replace(/\/+$/, '');
      const srv = connectedServers.find(s => s.id === activePrinter.id);
      const headers = { 'Content-Type': 'application/json' };
      if (srv?.token) {
        headers['Authorization'] = `Bearer ${srv.token}`;
        headers['X-Sentinel-Token'] = srv.token;
      }
      try {
        const directRes = await fetch(`${targetUrl}/api/${endpoint.replace(/^api\//, '')}`, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(4000)
        });
        if (!directRes.ok) throw new Error(`HTTP ${directRes.status}`);
      } catch (err) {
        try {
          await fetch(`${API_URL}/remote/proxy?target_url=${encodeURIComponent(targetUrl + '/api/' + endpoint.replace(/^api\//, ''))}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
            signal: AbortSignal.timeout(5000)
          });
        } catch (proxyErr) {
          console.error("Error al enviar comando a impresora remota:", proxyErr);
        }
      }
    };

    const handleAction = handlePrinterAction;

    // Si no hay ninguna impresora Klipper lista en ningún servidor del cluster
    if (!activePrinter || activePrinter.klippy_state !== 'ready') {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Selector de servidor si hay nodos con Klipper aunque estén desconectados */}
          {allKlipperPrinters.length > 0 && (
            <div className="glass-panel" style={{ padding: '0.75rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <Printer size={20} color="#f43f5e" />
                <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f8fafc' }}>Seleccionar Servidor con Impresora 3D:</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {allKlipperPrinters.map(p => (
                  <button
                    key={p.id}
                    className={`server-filter-chip ${activePrinter?.id === p.id ? 'active' : ''}`}
                    onClick={() => setSelectedPrinterServer(p.id)}
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
                  >
                    {p.name} ({p.klippy_state})
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '55vh', textAlign: 'center', padding: '2.5rem 1.5rem' }}>
            <div style={{ background: 'rgba(244, 63, 94, 0.1)', padding: '1.25rem', borderRadius: '50%', marginBottom: '1.25rem' }}>
              <Printer size={52} color="#f43f5e" />
            </div>
            <h2 style={{ color: '#f8fafc', margin: '0 0 0.5rem 0', fontSize: '1.35rem' }}>Klipper / Moonraker No Detectado en Este Equipo</h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '580px', lineHeight: 1.6, fontSize: '0.92rem', margin: '0 0 1.5rem 0' }}>
              Si tienes tu impresora 3D conectada mediante USB o MCU a otro servidor en tu red (por ejemplo tu servidor HP, Raspberry Pi u Orange Pi), SentinelOS la detectará y mostrará automáticamente en este Dashboard Maestro una vez que vincules ese equipo.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', width: '100%', maxWidth: '680px', marginBottom: '1.75rem', textAlign: 'left' }}>
              <div style={{ background: 'rgba(0, 0, 0, 0.35)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '1rem' }}>
                <div style={{ color: '#38bdf8', fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.35rem' }}>1. Instala SentinelOS en el Servidor</div>
                <div style={{ color: '#94a3b8', fontSize: '0.8rem', lineHeight: 1.4 }}>
                  Al instalar con rol Servidor o Malla, SentinelOS escanea automáticamente el puerto 7125 (Moonraker) y los dispositivos USB MCU.
                </div>
              </div>

              <div style={{ background: 'rgba(0, 0, 0, 0.35)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '1rem' }}>
                <div style={{ color: '#10b981', fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.35rem' }}>2. Vincula el Servidor al Cockpit</div>
                <div style={{ color: '#94a3b8', fontSize: '0.8rem', lineHeight: 1.4 }}>
                  Presiona el botón inferior, escribe la IP del servidor (o su MagicDNS Tailscale) y su PIN. El panel 3D se activará en vivo.
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
              <button 
                className="btn btn-primary" 
                onClick={() => setServerModalOpen(true)}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0.6rem 1.25rem' }}
              >
                <Plus size={16} /> Conectar Servidor Satélite con Klipper
              </button>
              <button 
                className="btn" 
                onClick={fetchData}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0.6rem 1.25rem' }}
              >
                <RefreshCw size={16} /> Reintentar Detección
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Telemetría en tiempo real de la impresora activa (local o remota)
    const printerData = activePrinter.printer || {};
    const stats = printerData.print_stats || {};
    const sd = printerData.virtual_sdcard || {};
    const toolhead = printerData.toolhead || {};
    const fan = printerData.fan || {};
    const gcode_move = printerData.gcode_move || {};
    const display_status = printerData.display_status || {};
    const ext = printerData.extruder || {};
    const bed = printerData.heater_bed || {};
    
    const progress = (display_status.progress || sd.progress || 0) * 100;
    const isPrinting = stats.state === 'printing';
    
    // Formateo de tiempo
    const formatTime = (sec) => {
        if (!sec) return '--';
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        return `${h}:${m.toString().padStart(2, '0')}`;
    };

    return (
      <div style={{display: 'flex', flexDirection: 'column', gap: '1.25rem'}}>
        {/* Barra Superior: Selector Multi-Servidor de Impresoras 3D */}
        <div className="glass-panel" style={{ padding: '0.75rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Printer size={22} color="#f43f5e" />
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem' }}>Control Maestro de Impresión 3D (Klipper)</h2>
              <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                Servidor Activo: <strong style={{ color: '#38bdf8' }}>{activePrinter.name}</strong> • Estado MCU: <strong style={{ color: '#10b981' }}>{activePrinter.klippy_state.toUpperCase()}</strong> • Endpoint: <span style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>{activePrinter.url || 'Local'}</span>
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.76rem', color: '#94a3b8', fontWeight: 600 }}>Impresora / Nodo:</span>
            {allKlipperPrinters.map(p => (
              <button
                key={p.id}
                className={`server-filter-chip ${activePrinter.id === p.id ? 'active' : ''}`}
                onClick={() => setSelectedPrinterServer(p.id)}
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <span className={`status-indicator ${p.klippy_state === 'ready' ? 'status-online' : 'status-offline'}`} style={{ width: '7px', height: '7px' }}></span>
                {p.name}
              </button>
            ))}
          </div>
        </div>

        <div style={{display: 'grid', gridTemplateColumns: 'minmax(300px, 350px) 1fr minmax(300px, 350px)', gap: '1.5rem', alignItems: 'start'}}>
        
        {/* LEFT COLUMN */}
        <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
          
          <div className="glass-panel" style={{padding: 0, overflow: 'hidden'}}>
            <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                {/* Circular Progress Placeholder */}
                <div style={{width: '32px', height: '32px', borderRadius: '50%', border: `4px solid ${isPrinting ? 'var(--primary)' : '#334155'}`, borderTopColor: isPrinting ? 'var(--accent)' : '#334155', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem'}}>
                  {progress.toFixed(0)}%
                </div>
                <h3 style={{margin: 0, color: isPrinting ? 'var(--accent)' : 'var(--text-secondary)'}}>{isPrinting ? 'Printing' : 'Standby'}</h3>
              </div>
            </div>
            <div style={{padding: '1rem'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem', wordBreak: 'break-all'}}>
                <Printer size={16}/> {stats.filename || 'No file selected'}
              </div>
              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', textAlign: 'center', marginBottom: '1rem'}}>
                <div>
                  <div style={{color: 'var(--text-secondary)', fontSize: '0.8rem'}}>Speed</div>
                  <div style={{fontWeight: 'bold'}}>{(gcode_move.speed_factor * 100 || 100).toFixed(0)}%</div>
                </div>
                <div>
                  <div style={{color: 'var(--text-secondary)', fontSize: '0.8rem'}}>Flow</div>
                  <div style={{fontWeight: 'bold'}}>{(gcode_move.extrude_factor * 100 || 100).toFixed(0)}%</div>
                </div>
                <div>
                  <div style={{color: 'var(--text-secondary)', fontSize: '0.8rem'}}>Total</div>
                  <div style={{fontWeight: 'bold'}}>{formatTime(stats.print_duration)}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{padding: 0, overflow: 'hidden'}}>
            <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem'}}>
              <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem'}}><TerminalSquare size={18}/> Toolhead</h3>
            </div>
            <div style={{padding: '1rem'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#a1a1aa', fontSize: '0.85rem'}}>
                <RefreshCw size={14} /> Position: absolute
              </div>
              <div style={{display: 'flex', gap: '0.5rem', marginBottom: '1rem'}}>
                {['X', 'Y', 'Z'].map((axis, i) => (
                  <div key={axis} style={{position: 'relative', border: '1px solid #3f3f46', borderRadius: '4px', padding: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flex: 1}}>
                    <div style={{fontSize: '1rem', fontWeight: 'bold', color: '#e4e4e7'}}>{axis}</div>
                    <div style={{fontSize: '1.1rem', fontWeight: 'bold', color: '#fff'}}>{(toolhead.position?.[i] || 0).toFixed(2)}</div>
                    <div style={{position: 'absolute', top: '-0.5rem', right: '0.5rem', background: 'var(--panel-bg, #18181b)', padding: '0 0.25rem', fontSize: '0.7rem', color: '#a1a1aa'}}>
                      [ {(toolhead.position?.[i] || 0).toFixed(2)} ]
                    </div>
                  </div>
                ))}
              </div>
              
              <div style={{display: 'flex', gap: '1rem', justifyContent: 'center'}}>
                {/* D-Pad SVG */}
                <div style={{position: 'relative', width: '280px', height: '280px'}}>
                  <button style={{position:'absolute', top:0, left:0, background:'#3f3f46', border:'none', width:'40px', height:'40px', borderRadius:'4px', clipPath:'polygon(0 0, 100% 0, 0 100%)', cursor:'pointer'}} onClick={() => handleAction('printer/gcode', {gcode:'G28 X'})} title="Home X">
                    <span style={{position:'absolute', top:'2px', left:'4px', color:'#a1a1aa', fontSize:'12px', fontWeight:'bold'}}>X</span>
                  </button>
                  <button style={{position:'absolute', top:0, right:0, background:'#3f3f46', border:'none', width:'40px', height:'40px', borderRadius:'4px', clipPath:'polygon(0 0, 100% 0, 100% 100%)', cursor:'pointer'}} onClick={() => handleAction('printer/gcode', {gcode:'G28 Y'})} title="Home Y">
                    <span style={{position:'absolute', top:'2px', right:'4px', color:'#a1a1aa', fontSize:'12px', fontWeight:'bold'}}>Y</span>
                  </button>
                  <button style={{position:'absolute', bottom:0, left:0, background:'#3f3f46', border:'none', width:'40px', height:'40px', borderRadius:'4px', clipPath:'polygon(0 0, 0 100%, 100% 100%)', cursor:'pointer'}} onClick={() => handleAction('printer/gcode', {gcode:'G28 X Y'})} title="Home XY">
                    <span style={{position:'absolute', bottom:'2px', left:'4px', color:'#a1a1aa', fontSize:'10px', fontWeight:'bold'}}>XY</span>
                  </button>
                  <button style={{position:'absolute', bottom:0, right:0, background:'#3f3f46', border:'none', width:'40px', height:'40px', borderRadius:'4px', clipPath:'polygon(100% 0, 100% 100%, 0 100%)', cursor:'pointer'}} onClick={() => handleAction('printer/gcode', {gcode:'G28 Z'})} title="Home Z">
                    <span style={{position:'absolute', bottom:'2px', right:'4px', color:'#a1a1aa', fontSize:'12px', fontWeight:'bold'}}>Z</span>
                  </button>

                  <svg width="280" height="280" viewBox="0 0 300 300" style={{cursor: 'pointer'}} onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const dx = (e.clientX - rect.left) - rect.width/2;
                    const dy = (e.clientY - rect.top) - rect.height/2;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist < 30) return handleAction('printer/gcode', {gcode: 'G28'});
                    const rRatio = dist / (rect.width/2);
                    let amt = 0;
                    if (rRatio < 0.2) return; else if (rRatio < 0.4) amt = 1; else if (rRatio < 0.6) amt = 10; else if (rRatio < 0.8) amt = 50; else if (rRatio <= 1.0) amt = 100; else return;
                    const ang = Math.atan2(dy, dx) * 180 / Math.PI;
                    if (ang > -135 && ang <= -45) handleAction('printer/gcode', {gcode: `G91\\nG1 Y${amt} F3000\\nG90`});
                    else if (ang > -45 && ang <= 45) handleAction('printer/gcode', {gcode: `G91\\nG1 X${amt} F3000\\nG90`});
                    else if (ang > 45 && ang <= 135) handleAction('printer/gcode', {gcode: `G91\\nG1 Y-${amt} F3000\\nG90`});
                    else handleAction('printer/gcode', {gcode: `G91\\nG1 X-${amt} F3000\\nG90`});
                  }}>
                    <circle cx="150" cy="150" r="140" fill="#3f3f46" />
                    <circle cx="150" cy="150" r="110" fill="#27272a" />
                    <circle cx="150" cy="150" r="80" fill="#3f3f46" />
                    <circle cx="150" cy="150" r="50" fill="#27272a" />
                    <circle cx="150" cy="150" r="25" fill="#18181b" />
                    <line x1="20" y1="20" x2="280" y2="280" stroke="#18181b" strokeWidth="12" />
                    <line x1="280" y1="20" x2="20" y2="280" stroke="#18181b" strokeWidth="12" />
                    <text x="150" y="32" fill="#a1a1aa" fontSize="14" textAnchor="middle" fontWeight="bold" pointerEvents="none">100</text>
                    <text x="150" y="62" fill="#a1a1aa" fontSize="14" textAnchor="middle" fontWeight="bold" pointerEvents="none">50</text>
                    <text x="150" y="92" fill="#a1a1aa" fontSize="14" textAnchor="middle" fontWeight="bold" pointerEvents="none">10</text>
                    <text x="150" y="122" fill="#a1a1aa" fontSize="14" textAnchor="middle" fontWeight="bold" pointerEvents="none">1</text>
                  </svg>
                </div>

                {/* Z Controls */}
                <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem', width: '45px'}}>
                  <div style={{background: '#3f3f46', borderRadius: '4px', overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
                    {[50, 10, 1, 0.1].map(v => (
                      <button key={v} onClick={() => setZDist(v)} style={{
                        padding: '0.3rem 0', border: 'none', 
                        background: zDist === v ? '#a1a1aa' : 'transparent',
                        color: zDist === v ? '#18181b' : '#a1a1aa',
                        fontWeight: 'bold', cursor: 'pointer', fontSize: '0.75rem'
                      }}>{v}</button>
                    ))}
                  </div>
                  
                  <button onClick={() => handleAction('printer/gcode', {gcode: 'M84'})} style={{background: '#3f3f46', borderRadius: '50%', width: '45px', height: '45px', display: 'flex', justifyContent: 'center', alignItems: 'center', border: 'none', cursor: 'pointer'}} title="Motor Off">
                    <PowerOff size={18} color="#a1a1aa" />
                  </button>
                  
                  <div style={{background: '#3f3f46', borderRadius: '4px', flex: 1, display: 'flex', flexDirection: 'column', height: '90px'}}>
                    {[1,2,3,4,5].map(i => (
                      <button key={i} 
                        onClick={() => {
                          if(i===1) handleAction('printer/gcode', {gcode: `G91\\nG1 Z${zDist} F600\\nG90`});
                          if(i===5) handleAction('printer/gcode', {gcode: `G91\\nG1 Z-${zDist} F600\\nG90`});
                        }}
                        style={{
                          flex: 1, border: 'none', 
                          borderBottom: i < 5 ? '1px solid #18181b' : 'none', 
                          background: 'transparent', cursor: (i===1||i===5)?'pointer':'default', 
                          display: 'flex', justifyContent: 'center', alignItems: 'center'
                      }}>
                        {i === 1 && <ChevronUp size={18} color="#a1a1aa" />}
                        {i === 5 && <ChevronDown size={18} color="#a1a1aa" />}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* Z-Offset & Speed Factor Additions */}
              <div style={{marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: '#e4e4e7', fontWeight: 'bold'}}>
                  <Database size={16} color="#a1a1aa" /> Z-Offset: {(data.printer?.gcode_move?.homing_origin?.[2] || 0).toFixed(3)}
                </div>
                
                <div style={{display: 'flex', flexDirection: 'column', gap: '0', background: 'transparent', border: '1px solid #3f3f46', borderRadius: '4px', overflow: 'hidden'}}>
                  <div style={{display: 'flex', borderBottom: '1px solid #3f3f46'}}>
                    {['+0.005', '+0.01', '+0.025', '+0.05'].map((val, i) => (
                      <button key={val} onClick={() => handleAction('printer/gcode', {gcode: `SET_GCODE_OFFSET Z_ADJUST=${val} MOVE=1`})} style={{flex: 1, padding: '0.5rem 0', background: 'transparent', border: 'none', borderRight: i < 3 ? '1px solid #3f3f46' : 'none', color: '#e4e4e7', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.2rem', fontSize: '0.85rem', fontWeight: 'bold'}}>
                        {i === 0 && <ChevronUp size={14} />} {val}
                      </button>
                    ))}
                  </div>
                  <div style={{display: 'flex'}}>
                    {['-0.005', '-0.01', '-0.025', '-0.05'].map((val, i) => (
                      <button key={val} onClick={() => handleAction('printer/gcode', {gcode: `SET_GCODE_OFFSET Z_ADJUST=${val} MOVE=1`})} style={{flex: 1, padding: '0.5rem 0', background: 'transparent', border: 'none', borderRight: i < 3 ? '1px solid #3f3f46' : 'none', color: '#e4e4e7', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.2rem', fontSize: '0.85rem', fontWeight: 'bold'}}>
                        {i === 0 && <ChevronDown size={14} />} {val}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)'}}>
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#e4e4e7', fontWeight: 'bold'}}>
                      <Gauge size={16} color="#a1a1aa" /> Speed factor
                    </div>
                    <button onClick={() => handleAction('printer/gcode', {gcode: 'M220 S100'})} style={{background: 'transparent', border: '1px solid #3f3f46', borderRadius: '4px', padding: '0.2rem 0.5rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 'bold'}}>
                      {(dragSpeed !== null ? parseFloat(dragSpeed) : (gcode_move.speed_factor * 100 || 100)).toFixed(0)} % <RefreshCw size={12} />
                    </button>
                  </div>
                  
                  <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                    <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '1.2rem', cursor: 'pointer'}} onClick={() => handleAction('printer/gcode', {gcode: `M220 S${Math.max(10, (gcode_move.speed_factor*100 || 100) - 10)}`})}>−</span>
                    <CustomSlider min="10" max="300" step="1" value={(gcode_move.speed_factor * 100 || 100)} onChangeDrag={setDragSpeed} onChangeCommit={(val) => handleAction('printer/gcode', {gcode: `M220 S${val}`})} />
                    <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '1.2rem', cursor: 'pointer'}} onClick={() => handleAction('printer/gcode', {gcode: `M220 S${Math.min(300, (gcode_move.speed_factor*100 || 100) + 10)}`})}>+</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* CENTER COLUMN */}
        <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
          
          <div className="glass-panel" style={{padding: 0, overflow: 'hidden'}}>
            <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem', justifyContent: 'space-between'}}>
              <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem'}}><Activity size={18}/> Temperatures</h3>
              <button className="btn btn-danger" style={{padding: '0.2rem 0.75rem', fontSize: '0.8rem'}} onClick={() => {
                handleAction('printer/temperature', {target: 'extruder', temperature: 0});
                handleAction('printer/temperature', {target: 'heater_bed', temperature: 0});
              }}>COOLDOWN</button>
            </div>
            
            <div style={{padding: '1rem'}}>
              <table style={{width: '100%', textAlign: 'left', borderCollapse: 'collapse', marginBottom: '1rem'}}>
                <thead>
                  <tr style={{color: 'var(--text-secondary)', fontSize: '0.85rem', borderBottom: '1px solid rgba(255,255,255,0.05)'}}>
                    <th style={{paddingBottom: '0.5rem'}}>Name</th>
                    <th style={{paddingBottom: '0.5rem'}}>Current</th>
                    <th style={{paddingBottom: '0.5rem'}}>Target</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{paddingTop: '0.5rem', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                      <div style={{width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444'}}></div> Extruder
                    </td>
                    <td style={{paddingTop: '0.5rem', verticalAlign: 'top'}}>{ext.temperature?.toFixed(1)}°C</td>
                    <td style={{paddingTop: '0.5rem', verticalAlign: 'top'}}>
                      <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                        <div style={{display: 'flex', alignItems: 'center', gap: '0.25rem'}}>
                          <span style={{color: '#a1a1aa'}}>{ext.target?.toFixed(1)}°C</span>
                          <input type="number" 
                                 id="ext_target_input"
                                 style={{width: '60px', marginLeft: 'auto', background: 'rgba(0,0,0,0.3)', border: '1px solid #3f3f46', borderRadius: '4px', color: '#fff', padding: '0.2rem', textAlign: 'right'}} 
                                 placeholder="Set..."
                                 onKeyDown={(e) => {
                                   if(e.key === 'Enter' && e.target.value) {
                                     handleAction('printer/temperature', {target: 'extruder', temperature: parseFloat(e.target.value)});
                                     e.target.value = '';
                                   }
                                 }}
                          />
                          <button className="btn" style={{padding: '0.2rem 0.5rem', background: 'var(--accent)', color: 'white', fontSize: '0.75rem', border: 'none', borderRadius: '4px', cursor: 'pointer'}} 
                            onClick={() => {
                              const val = document.getElementById('ext_target_input').value;
                              if(val) {
                                 handleAction('printer/temperature', {target: 'extruder', temperature: parseFloat(val)});
                                 document.getElementById('ext_target_input').value = '';
                              }
                            }}
                          >Set</button>
                        </div>
                        <div style={{display: 'flex', gap: '0.25rem', justifyContent: 'flex-end'}}>
                          <button style={{padding: '0.1rem 0.4rem', fontSize: '0.7rem', background: '#3f3f46', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer'}} onClick={() => handleAction('printer/temperature', {target: 'extruder', temperature: 0})}>Off</button>
                          <button style={{padding: '0.1rem 0.4rem', fontSize: '0.7rem', background: '#3f3f46', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer'}} onClick={() => handleAction('printer/temperature', {target: 'extruder', temperature: 200})}>200</button>
                          <button style={{padding: '0.1rem 0.4rem', fontSize: '0.7rem', background: '#3f3f46', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer'}} onClick={() => handleAction('printer/temperature', {target: 'extruder', temperature: 210})}>210</button>
                        </div>
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td style={{paddingTop: '0.5rem', color: '#3b82f6', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                      <div style={{width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6'}}></div> Heater Bed
                    </td>
                    <td style={{paddingTop: '0.5rem', verticalAlign: 'top'}}>{bed.temperature?.toFixed(1)}°C</td>
                    <td style={{paddingTop: '0.5rem', verticalAlign: 'top'}}>
                      <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                        <div style={{display: 'flex', alignItems: 'center', gap: '0.25rem'}}>
                          <span style={{color: '#a1a1aa'}}>{bed.target?.toFixed(1)}°C</span>
                          <input type="number" 
                                 id="bed_target_input"
                                 style={{width: '60px', marginLeft: 'auto', background: 'rgba(0,0,0,0.3)', border: '1px solid #3f3f46', borderRadius: '4px', color: '#fff', padding: '0.2rem', textAlign: 'right'}} 
                                 placeholder="Set..."
                                 onKeyDown={(e) => {
                                   if(e.key === 'Enter' && e.target.value) {
                                     handleAction('printer/temperature', {target: 'heater_bed', temperature: parseFloat(e.target.value)});
                                     e.target.value = '';
                                   }
                                 }}
                          />
                          <button className="btn" style={{padding: '0.2rem 0.5rem', background: 'var(--accent)', color: 'white', fontSize: '0.75rem', border: 'none', borderRadius: '4px', cursor: 'pointer'}} 
                            onClick={() => {
                              const val = document.getElementById('bed_target_input').value;
                              if(val) {
                                 handleAction('printer/temperature', {target: 'heater_bed', temperature: parseFloat(val)});
                                 document.getElementById('bed_target_input').value = '';
                              }
                            }}
                          >Set</button>
                        </div>
                        <div style={{display: 'flex', gap: '0.25rem', justifyContent: 'flex-end'}}>
                          <button style={{padding: '0.1rem 0.4rem', fontSize: '0.7rem', background: '#3f3f46', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer'}} onClick={() => handleAction('printer/temperature', {target: 'heater_bed', temperature: 0})}>Off</button>
                          <button style={{padding: '0.1rem 0.4rem', fontSize: '0.7rem', background: '#3f3f46', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer'}} onClick={() => handleAction('printer/temperature', {target: 'heater_bed', temperature: 60})}>60</button>
                          <button style={{padding: '0.1rem 0.4rem', fontSize: '0.7rem', background: '#3f3f46', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer'}} onClick={() => handleAction('printer/temperature', {target: 'heater_bed', temperature: 100})}>100</button>
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>

              <div style={{ height: 250, background: 'rgba(0,0,0,0.3)', borderRadius: '4px', padding: '1rem 0.5rem 0.5rem 0' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="time" tick={{fill: '#64748b', fontSize: 10}} />
                    <YAxis tick={{fill: '#64748b', fontSize: 10}} domain={[0, 300]} width={40} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="klipper_e" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="klipper_b" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '350px'}}>
            <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem'}}>
              <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem'}}><Terminal size={18}/> Console</h3>
            </div>
            
            <div style={{flex: 1, padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontFamily: 'monospace', fontSize: '0.85rem', background: '#0f172a'}}>
              {(data.gcode_store || []).slice().reverse().map((g, i) => (
                <div key={i} style={{color: g.type === 'command' ? 'var(--accent)' : 'var(--text-secondary)'}}>
                  {g.message}
                </div>
              ))}
              {(!data.gcode_store || data.gcode_store.length === 0) && (
                 <div style={{color: 'var(--text-secondary)'}}>No G-Code history available.</div>
              )}
            </div>

            <div style={{padding: '0.75rem', background: 'rgba(0,0,0,0.4)', borderTop: '1px solid rgba(255,255,255,0.05)'}}>
              <form onSubmit={(e) => {
                e.preventDefault();
                const inp = e.target.elements.gcodecmd;
                if(inp.value) {
                  handleAction('printer/gcode', {gcode: inp.value});
                  inp.value = '';
                }
              }} style={{display: 'flex', gap: '0.5rem'}}>
                <input name="gcodecmd" type="text" className="os-input" placeholder="Send G-code..." style={{flex: 1, fontFamily: 'monospace'}} autoComplete="off" />
                <button type="submit" className="btn btn-primary"><Play size={16} fill="white" /></button>
              </form>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN */}
        <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
          
          <div className="glass-panel" style={{padding: 0, overflow: 'hidden'}}>
            <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem'}}>
              <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem'}}><Settings size={18}/> Macros</h3>
            </div>
            <div style={{padding: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap'}}>
               <button className="btn" style={{background: 'var(--primary)'}} onClick={() => handleAction('printer/gcode', {gcode: 'SET_PAUSE_AT_LAYER'})}>PAUSE AT LAYER</button>
               <button className="btn" style={{background: 'var(--primary)'}} onClick={() => handleAction('printer/gcode', {gcode: 'CANCEL_PRINT'})}>CANCEL PRINT</button>
               <button className="btn" style={{background: '#334155'}} onClick={() => handleAction('printer/gcode', {gcode: 'M84'})}>MOTOR OFF</button>
            </div>
          </div>

          <div className="glass-panel" style={{padding: 0, overflow: 'hidden'}}>
            <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem'}}>
              <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem'}}><Settings size={18}/> Machine</h3>
            </div>
            <div style={{padding: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'}}>
               <div style={{background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px'}}>
                  <div style={{color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '0.2rem'}}>Velocity</div>
                  <div style={{fontWeight: 'bold'}}>{toolhead.max_velocity || 300} mm/s</div>
               </div>
               <div style={{background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px'}}>
                  <div style={{color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '0.2rem'}}>Accel</div>
                  <div style={{fontWeight: 'bold'}}>{toolhead.max_accel || 3000} mm/s²</div>
               </div>
               <div style={{background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px', gridColumn: '1 / -1'}}>
                  <div style={{color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '0.2rem'}}>Sq. Corner Velocity</div>
                  <div style={{fontWeight: 'bold'}}>{toolhead.square_corner_velocity || 5} mm/s</div>
               </div>
            </div>
          </div>
          
          <div className="glass-panel" style={{padding: 0, overflow: 'hidden'}}>
            <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem'}}>
              <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem'}}><Settings size={18}/> Miscellaneous</h3>
            </div>
            <div style={{padding: '1rem'}}>
               <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
                 <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#e4e4e7', fontWeight: 'bold'}}>
                   <Gauge size={16} color="#a1a1aa" /> Fan Speed
                 </div>
                 <button onClick={() => handleAction('printer/gcode', {gcode: 'M106 S0'})} style={{background: 'transparent', border: '1px solid #3f3f46', borderRadius: '4px', padding: '0.2rem 0.5rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 'bold'}}>
                   {(dragFan !== null ? (parseFloat(dragFan)/255*100) : ((fan.speed || 0)*100)).toFixed(0)} % <RefreshCw size={12} />
                 </button>
               </div>
               
               <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                 <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '1.2rem', cursor: 'pointer'}} onClick={() => handleAction('printer/gcode', {gcode: `M106 S${Math.max(0, (fan.speed*255 || 0) - 25)}`})}>−</span>
                 <CustomSlider min="0" max="255" step="1" value={(fan.speed || 0)*255} onChangeDrag={setDragFan} onChangeCommit={(val) => handleAction('printer/gcode', {gcode: `M106 S${val}`})} />
                 <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '1.2rem', cursor: 'pointer'}} onClick={() => handleAction('printer/gcode', {gcode: `M106 S${Math.min(255, (fan.speed*255 || 0) + 25)}`})}>+</span>
               </div>
            </div>
          </div>
          </div>
        </div>

        {/* STATISTICS & HISTORY */}
        {printerHistory && (
          <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '1.5rem'}}>
            <div className="glass-panel" style={{padding: 0, overflow: 'hidden'}}>
              <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem'}}>
                 <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem'}}><Activity size={18}/> Statistics</h3>
              </div>
              <div style={{padding: '1.5rem', display: 'flex', gap: '2rem'}}>
                 <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem', justifyContent: 'center'}}>
                    <div style={{display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem'}}>
                       <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '0.85rem'}}>Total Print Time</span>
                       <span style={{fontWeight: 'bold', fontSize: '0.85rem'}}>{formatTime(printerHistory.totals?.job_totals?.total_print_time)}</span>
                    </div>
                    <div style={{display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem'}}>
                       <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '0.85rem'}}>Longest Print Time</span>
                       <span style={{fontWeight: 'bold', fontSize: '0.85rem'}}>{formatTime(printerHistory.totals?.job_totals?.longest_print)}</span>
                    </div>
                    <div style={{display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem'}}>
                       <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '0.85rem'}}>Print Time - Ø</span>
                       <span style={{fontWeight: 'bold', fontSize: '0.85rem'}}>{formatTime(printerHistory.totals?.job_totals?.total_print_time / Math.max(1, printerHistory.totals?.job_totals?.total_jobs))}</span>
                    </div>
                    <div style={{display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem'}}>
                       <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '0.85rem'}}>Total Filament Used</span>
                       <span style={{fontWeight: 'bold', fontSize: '0.85rem'}}>{(printerHistory.totals?.job_totals?.total_filament_used / 1000).toFixed(1)} m</span>
                    </div>
                    <div style={{display: 'flex', justifyContent: 'space-between'}}>
                       <span style={{color: '#a1a1aa', fontWeight: 'bold', fontSize: '0.85rem'}}>Total Jobs</span>
                       <span style={{fontWeight: 'bold', fontSize: '0.85rem'}}>{printerHistory.totals?.job_totals?.total_jobs}</span>
                    </div>
                 </div>

                 <div style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
                    <div style={{height: '180px', width: '100%'}}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                           <Pie data={[
                               {name: 'Completed', value: printerHistory.list?.jobs?.filter(j => j.status === 'completed').length || 0},
                               {name: 'Cancelled', value: printerHistory.list?.jobs?.filter(j => j.status === 'cancelled').length || 0},
                               {name: 'Server Exit', value: printerHistory.list?.jobs?.filter(j => j.status === 'server_exit').length || 0},
                               {name: 'In Progress', value: printerHistory.list?.jobs?.filter(j => j.status === 'in_progress').length || 0}
                             ].filter(d => d.value > 0)} 
                             cx="50%" cy="50%" innerRadius={50} outerRadius={70} dataKey="value" stroke="none"
                           >
                              <Cell fill="#a1a1aa" />
                              <Cell fill="#3f3f46" />
                              <Cell fill="#e4e4e7" />
                              <Cell fill="#71717a" />
                           </Pie>
                           <Tooltip contentStyle={{background: '#0f172a', border: '1px solid #3f3f46'}} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                 </div>

                 <div style={{flex: 1}}>
                    {/* Placeholder for bar chart in the future */}
                 </div>
              </div>
            </div>

            <div className="glass-panel" style={{padding: 0, overflow: 'hidden'}}>
               <div className="panel-header" style={{background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem'}}>
                  <h3 style={{margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem'}}><Database size={18}/> Print History</h3>
               </div>
               <div style={{padding: '0', overflowX: 'auto'}}>
                 <table style={{width: '100%', textAlign: 'left', borderCollapse: 'collapse'}}>
                   <thead>
                     <tr style={{color: 'var(--text-secondary)', fontSize: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)'}}>
                       <th style={{padding: '0.75rem 1rem', width: '30px'}}></th>
                       <th style={{padding: '0.75rem 1rem'}}>Filename</th>
                       <th style={{padding: '0.75rem 1rem'}}>Start Time</th>
                       <th style={{padding: '0.75rem 1rem'}}>Estimated Time</th>
                       <th style={{padding: '0.75rem 1rem'}}>Print Time</th>
                       <th style={{padding: '0.75rem 1rem'}}>Filament Used</th>
                       <th style={{padding: '0.75rem 1rem'}}>Slicer</th>
                     </tr>
                   </thead>
                   <tbody>
                     {(printerHistory.list?.jobs || []).map((job, i) => (
                       <tr key={i} style={{borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.85rem'}}>
                         <td style={{padding: '0.75rem 1rem', textAlign: 'center'}}>
                           {job.status === 'completed' && <span style={{color: '#10b981'}}>✔</span>}
                           {job.status === 'cancelled' && <span style={{color: '#f59e0b'}}>▲</span>}
                           {job.status === 'server_exit' && <span style={{color: '#ef4444'}}>■</span>}
                           {job.status === 'in_progress' && <span style={{color: '#3b82f6'}}>⟳</span>}
                         </td>
                         <td style={{padding: '0.75rem 1rem', wordBreak: 'break-all'}}>{job.filename}</td>
                         <td style={{padding: '0.75rem 1rem'}}>{new Date(job.start_time * 1000).toLocaleString()}</td>
                         <td style={{padding: '0.75rem 1rem'}}>{formatTime(job.metadata?.estimated_time)}</td>
                         <td style={{padding: '0.75rem 1rem'}}>{job.print_duration > 0 ? formatTime(job.print_duration) : '—'}</td>
                         <td style={{padding: '0.75rem 1rem'}}>{(job.filament_used / 1000).toFixed(2)} m</td>
                         <td style={{padding: '0.75rem 1rem'}}>{job.metadata?.slicer}<br/><span style={{color:'var(--text-secondary)', fontSize:'0.75rem'}}>{job.metadata?.slicer_version?.trim()}</span></td>
                       </tr>
                     ))}
                   </tbody>
                 </table>
               </div>
            </div>
          </div>
        )}

      </div>
    );
  };

  const renderDocker = () => {
    // Unificar contenedores de todos los servidores registrados
    const allContainers = [];
    (data?.containers || []).forEach(c => {
      allContainers.push({
        ...c,
        serverId: 'local',
        serverName: 'Host Maestro (Local)',
        isLocal: true
      });
    });

    Object.entries(remoteServersData).forEach(([srvId, srvObj]) => {
      const srvName = connectedServers.find(s => s.id === srvId)?.name || srvId;
      (srvObj?.data?.containers || []).forEach(c => {
        allContainers.push({
          ...c,
          serverId: srvId,
          serverName: srvName,
          isLocal: false
        });
      });
    });

    const filteredContainers = selectedDockerServer === 'all'
      ? allContainers
      : allContainers.filter(c => c.serverId === selectedDockerServer);

    const handleDockerAction = async (c, action) => {
      if (c.isLocal) {
        handleAction('docker', { container_name: c.name, action });
      } else {
        const srv = connectedServers.find(s => s.id === c.serverId);
        if (!srv || !srv.url) return;
        const targetUrl = srv.url.replace(/\/+$/, '');
        try {
          const headers = { 'Content-Type': 'application/json' };
          if (srv.token) {
            headers['Authorization'] = `Bearer ${srv.token}`;
            headers['X-Sentinel-Token'] = srv.token;
          }
          await fetch(`${targetUrl}/api/docker`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ container_name: c.name, action })
          });
        } catch (e) {
          console.error("Error al controlar contenedor remoto:", e);
        }
      }
    };

    return (
      <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {dockerModal && (
          <div className="modal-overlay">
            <div className="glass-panel modal-content">
              <h2 style={{ marginBottom: '1.5rem' }}>Crear Contenedor Docker</h2>
              <input className="modal-input" placeholder="Nombre (ej. webserver)" value={dForm.name} onChange={e => setDForm({ ...dForm, name: e.target.value })} />
              <input className="modal-input" placeholder="Imagen (ej. nginx:latest)" value={dForm.image} onChange={e => setDForm({ ...dForm, image: e.target.value })} />
              <input className="modal-input" placeholder="Puertos (ej. 8080:80, 443:443)" value={dForm.ports} onChange={e => setDForm({ ...dForm, ports: e.target.value })} />
              <input className="modal-input" placeholder="Variables de Entorno (ej. ENV=production)" value={dForm.env} onChange={e => setDForm({ ...dForm, env: e.target.value })} />
              <select className="modal-input" value={dForm.restart} onChange={e => setDForm({ ...dForm, restart: e.target.value })}>
                <option value="no">Reinicio: No</option>
                <option value="always">Reinicio: Siempre</option>
                <option value="unless-stopped">Reinicio: Salvo Detención Manual</option>
              </select>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button className="btn btn-primary" onClick={() => {
                  handleAction('docker/create', dForm);
                  setDockerModal(false);
                  setDForm({ name: '', image: '', ports: '', env: '', restart: 'no' });
                }}>Desplegar</button>
                <button className="btn" onClick={() => setDockerModal(false)}>Cancelar</button>
              </div>
            </div>
          </div>
        )}

        <div className="panel-header" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Database size={24} color="#06b6d4" />
            <div>
              <h2 style={{ margin: 0 }}>Docker Containers & Microservicios</h2>
              <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                Monitoreo multi-servidor de contenedores ({filteredContainers.length} detectados)
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: 'rgba(0,0,0,0.3)', padding: '0.25rem 0.5rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ fontSize: '0.76rem', color: '#94a3b8', fontWeight: 600 }}>Servidor:</span>
              <button
                className={`server-filter-chip ${selectedDockerServer === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedDockerServer('all')}
                style={{ padding: '0.25rem 0.6rem', fontSize: '0.76rem' }}
              >
                Todos ({connectedServers.length})
              </button>
              {connectedServers.map(srv => (
                <button
                  key={srv.id}
                  className={`server-filter-chip ${selectedDockerServer === srv.id ? 'active' : ''}`}
                  onClick={() => setSelectedDockerServer(srv.id)}
                  style={{ padding: '0.25rem 0.6rem', fontSize: '0.76rem' }}
                >
                  {srv.name}
                </button>
              ))}
            </div>

            <button className="btn btn-primary" onClick={() => setDockerModal(true)}>
              + Nuevo Contenedor
            </button>
          </div>
        </div>

        <table className="os-table">
          <thead>
            <tr>
              <th style={{ width: '180px' }}>Servidor / Host</th>
              <th>Contenedor</th>
              <th>Imagen</th>
              <th>Puertos</th>
              <th>Estado</th>
              <th style={{ textAlign: 'center' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filteredContainers.map((c, i) => (
              <React.Fragment key={`${c.serverId}-${c.id || i}`}>
                <tr onClick={() => setExpandedDocker(expandedDocker === `${c.serverId}-${c.name}` ? null : `${c.serverId}-${c.name}`)} style={{ cursor: 'pointer' }}>
                  <td>
                    <span style={{
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.74rem',
                      fontWeight: 700,
                      background: c.isLocal ? 'rgba(59, 130, 246, 0.2)' : 'rgba(6, 182, 212, 0.2)',
                      color: c.isLocal ? '#60a5fa' : '#38bdf8',
                      border: `1px solid ${c.isLocal ? 'rgba(59, 130, 246, 0.4)' : 'rgba(6, 182, 212, 0.4)'}`
                    }}>
                      {c.serverName}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {expandedDocker === `${c.serverId}-${c.name}` ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    {c.name}
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: '0.82rem' }}>{c.image}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#cbd5e1' }}>{c.ports || 'Bridge'}</td>
                  <td>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                      color: (c.status || '').includes('Up') ? 'var(--success)' : 'var(--danger)',
                      fontWeight: 600
                    }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: (c.status || '').includes('Up') ? '#10b981' : '#ef4444' }} />
                      {c.status}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'center' }} onClick={e => e.stopPropagation()}>
                      {(c.status || '').includes('Up') ? (
                        <button className="btn" title="Detener Contenedor" onClick={() => handleDockerAction(c, 'stop')}><Square size={13} /></button>
                      ) : (
                        <button className="btn" title="Iniciar Contenedor" onClick={() => handleDockerAction(c, 'start')}><Play size={13} /></button>
                      )}
                      <button className="btn" title="Reiniciar" onClick={() => handleDockerAction(c, 'restart')}><RefreshCw size={13} /></button>
                      <button className="btn btn-danger" title="Eliminar Contenedor" onClick={() => { if (confirm(`¿Eliminar contenedor ${c.name}?`)) handleDockerAction(c, 'rm'); }}><Trash2 size={13} /></button>
                    </div>
                  </td>
                </tr>
                {expandedDocker === `${c.serverId}-${c.name}` && (
                  <tr className="expanded-row">
                    <td colSpan="6" style={{ padding: '1rem', background: 'rgba(0,0,0,0.3)' }}>
                      <div className="stat-row"><span className="stat-label">ID Contenedor</span><span className="stat-value" style={{ fontFamily: 'monospace' }}>{c.id}</span></div>
                      <div className="stat-row"><span className="stat-label">Puertos Expuestos</span><span className="stat-value">{c.ports || 'Ninguno'}</span></div>
                      <div className="stat-row"><span className="stat-label">Comando de Arranque</span><span className="stat-value" style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>{c.command}</span></div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
            {filteredContainers.length === 0 && (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '2.5rem', color: '#94a3b8' }}>
                  No se detectaron contenedores Docker en el servidor seleccionado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  };

  const renderBtopServer = (srv, srvData, srvServices) => {
    const srvSys = srvData?.system || srvData || {};
    const procs = Array.isArray(srvSys.processes) ? srvSys.processes : (Array.isArray(srvData?.processes) ? srvData.processes : []);
    const cpuModel = srvSys.cpu_model || 'Procesador Principal';
    const cpuCores = srvSys.cpu_cores || 4;

    const lastCpuMetric = srv.isLocal
      ? (history[history.length - 1]?.cpu ?? current?.cpu ?? 0)
      : (remoteServersData[srv.id]?.history?.slice(-1)[0]?.cpu ?? 0);
    const cpuUsage = Math.round(Number(lastCpuMetric) || 0);

    const memObj = srvSys.memory || srvData?.memory || {};
    const memTotal = Number(memObj.total) || 1;
    const memUsed = Number(memObj.used) || 0;
    const ramTotalGb = (memTotal / (1024**3)).toFixed(1);
    const ramUsedGb = (memUsed / (1024**3)).toFixed(1);
    const ramPercent = memObj.percent !== undefined ? Math.round(Number(memObj.percent)) : Math.min(100, Math.round((memUsed / memTotal) * 100));
    const ramAvailGb = (Math.max(0, memTotal - memUsed) / (1024**3)).toFixed(1);

    const rawLoad = srvSys.loadavg || srvData?.loadavg || [0.1, 0.2, 0.15];
    const loadAvgStr = Array.isArray(rawLoad) ? rawLoad.map(x => Number(x).toFixed(2)).join(' ') : String(rawLoad || '0.0');

    const uptimeSec = Number(srvSys.uptime || srvData?.uptime || 0);
    const uptimeHrs = Math.floor(uptimeSec / 3600);

    const netObj = srvData?.network || srvSys.network || {};
    const primaryNet = netObj.primary || { name: 'eth0', ip: '127.0.0.1', speed: 1000, type: 'ethernet' };

    const gpuInfo = srvSys.gpu || srvData?.gpu || {};
    const cpuTempStr = gpuInfo.temp ? `${gpuInfo.temp}°C` : '42°C';

    const disksArr = Array.isArray(srvSys.disks) ? srvSys.disks : (Array.isArray(srvData?.disks) ? srvData.disks : []);
    const rootDisk = disksArr[0] || null;
    const diskTotalGb = rootDisk?.total ? (Number(rootDisk.total) / (1024**3)).toFixed(0) : '0';
    const diskUsedGb = rootDisk?.used ? (Number(rootDisk.used) / (1024**3)).toFixed(0) : '0';
    const diskPercent = rootDisk?.total ? Math.min(100, Math.round((Number(rootDisk.used) / Number(rootDisk.total)) * 100)) : 25;

    // Filtrar y ordenar procesos de forma 100% segura contra tipos numéricos
    const filteredProcs = procs.filter(p => {
      if (!procFilterQuery) return true;
      const q = String(procFilterQuery).toLowerCase();
      const nameStr = String(p.name || '').toLowerCase();
      const pidStr = String(p.pid || '');
      const userStr = String(p.user || p.username || '').toLowerCase();
      return nameStr.includes(q) || pidStr.includes(q) || userStr.includes(q);
    }).sort((a, b) => {
      if (procSortField === 'cpu') return (parseFloat(b.cpu) || 0) - (parseFloat(a.cpu) || 0);
      if (procSortField === 'mem') return (parseFloat(b.mem) || 0) - (parseFloat(a.mem) || 0);
      return (parseInt(b.pid) || 0) - (parseInt(a.pid) || 0);
    });

    // Filtrar servicios
    const filteredServices = (srvServices || []).filter(s => {
      if (!serviceFilterQuery) return true;
      const q = String(serviceFilterQuery).toLowerCase();
      return String(s.name || '').toLowerCase().includes(q) || String(s.active || '').toLowerCase().includes(q);
    });

    const isLocal = srv.isLocal;
    const srvThemeColor = isLocal ? '#38bdf8' : '#34d399';

    return (
      <div
        key={srv.id}
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          background: 'rgba(10, 15, 29, 0.85)',
          backdropFilter: 'blur(12px)',
          border: `1px solid ${srvThemeColor}40`,
          borderRadius: '12px',
          padding: '1.25rem',
          boxShadow: '0 8px 30px rgba(0, 0, 0, 0.5)'
        }}
      >
        {/* Barra Superior estilo Terminal btop */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(0, 0, 0, 0.5)',
          padding: '0.6rem 1rem',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          flexWrap: 'wrap',
          gap: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{ display: 'flex', gap: '4px' }}>
              <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }}></span>
              <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }}></span>
              <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
            </div>
            <span style={{ fontWeight: 800, fontSize: '0.88rem', color: srvThemeColor, letterSpacing: '0.04em' }}>
              [{srv.name.toUpperCase()}]
            </span>
            <span style={{ fontSize: '0.76rem', color: '#94a3b8', fontFamily: 'monospace' }}>
              {primaryNet.ip} • {primaryNet.type === 'wifi' ? 'Wi-Fi' : 'Ethernet'}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.76rem', fontFamily: 'monospace', color: '#cbd5e1' }}>
            <span>Uptime: <strong style={{ color: '#38bdf8' }}>{uptimeHrs}h</strong></span>
            <span>Load: <strong style={{ color: '#f59e0b' }}>{loadAvgStr}</strong></span>
            <span>CPU Temp: <strong style={{ color: '#34d399' }}>{cpuTempStr}</strong></span>
          </div>
        </div>

        {/* Grid de Métricas de Hardware estilo btop (CPU + MEM + DISK) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
          {/* Panel CPU */}
          <div style={{ background: 'rgba(0,0,0,0.4)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.8rem' }}>
              <span style={{ color: '#94a3b8', fontWeight: 700 }}>CPU Usage ({cpuCores} Cores)</span>
              <strong style={{ color: cpuUsage > 80 ? '#ef4444' : (cpuUsage > 50 ? '#f59e0b' : '#34d399'), fontFamily: 'monospace' }}>
                {cpuUsage}%
              </strong>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden', marginBottom: '0.4rem' }}>
              <div style={{
                width: `${Math.min(cpuUsage, 100)}%`,
                height: '100%',
                background: cpuUsage > 80 ? '#ef4444' : (cpuUsage > 50 ? '#f59e0b' : '#10b981'),
                transition: 'width 0.4s ease'
              }} />
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {cpuModel}
            </div>
          </div>

          {/* Panel Memoria RAM */}
          <div style={{ background: 'rgba(0,0,0,0.4)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.8rem' }}>
              <span style={{ color: '#94a3b8', fontWeight: 700 }}>Memoria RAM</span>
              <strong style={{ color: '#38bdf8', fontFamily: 'monospace' }}>
                {ramUsedGb} / {ramTotalGb} GB ({ramPercent}%)
              </strong>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden', marginBottom: '0.4rem' }}>
              <div style={{
                width: `${Math.min(ramPercent, 100)}%`,
                height: '100%',
                background: ramPercent > 85 ? '#ef4444' : '#38bdf8',
                transition: 'width 0.4s ease'
              }} />
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace' }}>
              Disponible: {ramAvailGb} GB
            </div>
          </div>

          {/* Panel Almacenamiento */}
          <div style={{ background: 'rgba(0,0,0,0.4)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.8rem' }}>
              <span style={{ color: '#94a3b8', fontWeight: 700 }}>Disco Raíz (/)</span>
              <strong style={{ color: '#a855f7', fontFamily: 'monospace' }}>
                {rootDisk ? `${diskUsedGb} / ${diskTotalGb} GB` : 'Activo'}
              </strong>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden', marginBottom: '0.4rem' }}>
              <div style={{
                width: `${diskPercent}%`,
                height: '100%',
                background: '#a855f7',
                transition: 'width 0.4s ease'
              }} />
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
              Red: {primaryNet.name} ({primaryNet.speed || 1000} Mbps)
            </div>
          </div>
        </div>

        {/* Tabla de Procesos estilo btop */}
        <div style={{ background: 'rgba(0, 0, 0, 0.4)', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
          <div style={{
            padding: '0.6rem 0.85rem',
            background: 'rgba(0, 0, 0, 0.3)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.5rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={16} color={srvThemeColor} />
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>
                Procesos Activos ({filteredProcs.length})
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Ordenar:</span>
              <button
                onClick={() => setProcSortField('cpu')}
                style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '0.72rem',
                  cursor: 'pointer',
                  background: procSortField === 'cpu' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                  border: procSortField === 'cpu' ? '1px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                  color: procSortField === 'cpu' ? '#60a5fa' : '#94a3b8'
                }}
              >
                CPU%
              </button>
              <button
                onClick={() => setProcSortField('mem')}
                style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '0.72rem',
                  cursor: 'pointer',
                  background: procSortField === 'mem' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                  border: procSortField === 'mem' ? '1px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                  color: procSortField === 'mem' ? '#60a5fa' : '#94a3b8'
                }}
              >
                RAM%
              </button>
              <button
                onClick={() => setProcSortField('pid')}
                style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '0.72rem',
                  cursor: 'pointer',
                  background: procSortField === 'pid' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                  border: procSortField === 'pid' ? '1px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                  color: procSortField === 'pid' ? '#60a5fa' : '#94a3b8'
                }}
              >
                PID
              </button>
            </div>
          </div>

          <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
            <table className="os-table btop-table">
              <thead>
                <tr>
                  <th style={{ width: '60px' }}>PID</th>
                  <th style={{ width: '90px' }}>Usuario</th>
                  <th style={{ width: '50px' }}>Thr</th>
                  <th style={{ width: '130px' }}>CPU %</th>
                  <th style={{ width: '130px' }}>RAM %</th>
                  <th>Comando</th>
                  <th style={{ width: '40px', textAlign: 'center' }}>Kill</th>
                </tr>
              </thead>
              <tbody>
                {filteredProcs.slice(0, 35).map(p => {
                  const cpuVal = parseFloat(p.cpu) || 0;
                  const memVal = parseFloat(p.mem) || 0;
                  const cpuColor = cpuVal > 80 ? '#ef4444' : (cpuVal > 50 ? '#f59e0b' : '#10b981');
                  const memColor = memVal > 80 ? '#ef4444' : (memVal > 50 ? '#f59e0b' : '#3b82f6');
                  return (
                    <tr key={`${srv.id}-proc-${p.pid}`}>
                      <td style={{ color: srvThemeColor, fontFamily: 'monospace', fontWeight: 700 }}>{p.pid}</td>
                      <td style={{ color: '#94a3b8', fontSize: '0.76rem' }}>{p.user}</td>
                      <td style={{ color: '#64748b', fontSize: '0.74rem' }}>{p.threads}</td>
                      <td>
                        <div className="btop-bar-container">
                          <div className="btop-bar-fill" style={{ width: `${Math.min(cpuVal, 100)}%`, background: cpuColor }} />
                          <div className="btop-bar-text">{p.cpu}%</div>
                        </div>
                      </td>
                      <td>
                        <div className="btop-bar-container">
                          <div className="btop-bar-fill" style={{ width: `${Math.min(memVal, 100)}%`, background: memColor }} />
                          <div className="btop-bar-text">{p.mem}%</div>
                        </div>
                      </td>
                      <td style={{ color: '#f8fafc', fontFamily: 'monospace', fontSize: '0.8rem' }}>{p.name}</td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          className="btn btn-danger"
                          style={{ padding: '0.15rem 0.4rem', margin: '0 auto' }}
                          onClick={() => {
                            if (confirm(`¿Terminar proceso ${p.name} (PID ${p.pid})?`)) {
                              if (isLocal) {
                                handleAction('process/kill', { pid: parseInt(p.pid) });
                              }
                            }
                          }}
                        >
                          <Trash2 size={11} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Tabla de Servicios del Sistema estilo btop */}
        <div style={{ background: 'rgba(0, 0, 0, 0.4)', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
          <div style={{
            padding: '0.6rem 0.85rem',
            background: 'rgba(0, 0, 0, 0.3)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Settings size={16} color="#818cf8" />
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>
                Servicios del Sistema ({filteredServices.length})
              </span>
            </div>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>systemd / daemons</span>
          </div>

          <div style={{ maxHeight: '220px', overflowY: 'auto' }}>
            <table className="os-table">
              <thead>
                <tr>
                  <th>Servicio</th>
                  <th>Carga</th>
                  <th>Estado</th>
                  <th>Sub-estado</th>
                  <th style={{ textAlign: 'center' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredServices.slice(0, 30).map((s, idx) => (
                  <tr key={`${srv.id}-svc-${s.name || idx}`}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.8rem', color: '#e2e8f0' }}>{s.name}</td>
                    <td style={{ color: '#94a3b8', fontSize: '0.76rem' }}>{s.load}</td>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        color: s.active === 'active' ? '#34d399' : (s.active === 'failed' ? '#ef4444' : '#94a3b8'),
                        fontWeight: 600,
                        fontSize: '0.78rem'
                      }}>
                        <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: s.active === 'active' ? '#10b981' : (s.active === 'failed' ? '#ef4444' : '#64748b') }} />
                        {s.active}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.76rem', color: '#cbd5e1' }}>{s.sub}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.35rem', justifyContent: 'center' }}>
                        {s.sub !== 'running' && (
                          <button className="btn" title="Iniciar" onClick={() => handleAction('services', { service: s.name, action: 'start' })}><Play size={12} /></button>
                        )}
                        {s.sub === 'running' && (
                          <button className="btn" title="Detener" onClick={() => handleAction('services', { service: s.name, action: 'stop' })}><Square size={12} /></button>
                        )}
                        <button className="btn" title="Reiniciar" onClick={() => handleAction('services', { service: s.name, action: 'restart' })}><RefreshCw size={12} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredServices.length === 0 && (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '1.5rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                      Cargando o no se registraron servicios activos para este nodo.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderSystemServices = () => {
    // Determinar qué servidores renderizar
    const serversToRender = [];
    if (selectedSystemServer === 'all') {
      serversToRender.push({
        id: 'local',
        name: 'Host Maestro (Local)',
        isLocal: true,
        data: data,
        services: servicesData
      });
      connectedServers.filter(s => !s.isLocal).forEach(srv => {
        serversToRender.push({
          id: srv.id,
          name: srv.name,
          isLocal: false,
          data: remoteServersData[srv.id]?.data || {},
          services: remoteServices[srv.id] || []
        });
      });
    } else if (selectedSystemServer === 'local') {
      serversToRender.push({
        id: 'local',
        name: 'Host Maestro (Local)',
        isLocal: true,
        data: data,
        services: servicesData
      });
    } else {
      const srv = connectedServers.find(s => s.id === selectedSystemServer);
      if (srv) {
        serversToRender.push({
          id: srv.id,
          name: srv.name,
          isLocal: false,
          data: remoteServersData[srv.id]?.data || {},
          services: remoteServices[srv.id] || []
        });
      }
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Barra Superior con Selector de Servidores y Filtro Rápido */}
        <div className="glass-panel" style={{ padding: '0.75rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Servidores btop:
            </span>
            <button
              className={`server-filter-chip ${selectedSystemServer === 'all' ? 'active' : ''}`}
              onClick={() => setSelectedSystemServer('all')}
              style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
            >
              <Layers size={13} /> Vista Dual / Lado a Lado ({connectedServers.length})
            </button>
            {connectedServers.map(srv => (
              <button
                key={srv.id}
                className={`server-filter-chip ${selectedSystemServer === srv.id ? 'active' : ''}`}
                onClick={() => setSelectedSystemServer(srv.id)}
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
              >
                {srv.name}
              </button>
            ))}
          </div>

          <div style={{ position: 'relative', minWidth: '220px' }}>
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
            <input
              type="text"
              placeholder="Buscar procesos o servicios..."
              value={procFilterQuery}
              onChange={e => {
                setProcFilterQuery(e.target.value);
                setServiceFilterQuery(e.target.value);
              }}
              style={{
                width: '100%',
                padding: '0.4rem 0.75rem 0.4rem 2rem',
                borderRadius: '6px',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                fontSize: '0.82rem',
                outline: 'none'
              }}
            />
          </div>
        </div>

        {/* Renderizado de Dashboards de Servidores (Grid Lado a Lado si hay múltiples) */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: serversToRender.length > 1 ? 'repeat(auto-fit, minmax(min(100%, 480px), 1fr))' : '1fr',
          gap: '1.5rem'
        }}>
          {serversToRender.map(s => renderBtopServer(s, s.data, s.services))}
        </div>

      <div className="glass-panel" style={{padding: '1rem'}}>
        <div className="panel-header" style={{justifyContent: 'space-between', marginBottom: '0.5rem'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}><Package /><h2>APT / Package Manager</h2></div>
          <button className="btn btn-primary" disabled={!aptData || aptData.count === 0} onClick={() => {if(confirm("Start upgrade in background?")) handleAction('apt/upgrade', {})}}>
            Upgrade All ({aptData?.count || 0})
          </button>
        </div>
        <div style={{maxHeight: '200px', overflowY: 'auto', background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px'}}>
          {aptData?.count > 0 ? (
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
              {(aptData?.updates || []).map((pkg, i) => (
                <span key={i} style={{background: 'var(--bg-secondary)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.85rem', color: 'var(--text-secondary)'}}>{pkg}</span>
              ))}
            </div>
          ) : (
            <div style={{color: 'var(--success)', textAlign: 'center', padding: '1rem'}}>System is up to date!</div>
          )}
        </div>
      </div>

      <div className="glass-panel" style={{overflowY: 'auto', maxHeight: '400px', padding: '1rem'}}>
        <div className="panel-header" style={{marginBottom: '0.5rem'}}><Activity /><h2>Cron Jobs / Programador de Tareas</h2></div>
        <table className="os-table">
          <thead><tr><th>User</th><th>Job</th></tr></thead>
          <tbody>
            {(data?.system?.cron || []).map((c, i) => (
              <tr key={i}>
                <td style={{color: 'var(--accent)', fontWeight: 'bold'}}>{c.user}</td>
                <td style={{fontFamily: 'monospace', fontSize: '0.85rem'}}>{c.job}</td>
              </tr>
            ))}
            {(!data?.system?.cron || data.system.cron.length === 0) && (
              <tr><td colSpan="2" style={{textAlign: 'center', color: 'var(--text-secondary)'}}>No cron jobs found</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Danger Zone: Desinstalación del Sistema */}
      <div className="glass-panel" style={{ padding: '1.25rem', border: '1px solid rgba(239, 68, 68, 0.35)', background: 'linear-gradient(180deg, rgba(239, 68, 68, 0.05) 0%, rgba(15, 23, 42, 0.6) 100%)' }}>
        <div className="panel-header" style={{ marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertTriangle size={24} color="#ef4444" />
            <div>
              <h2 style={{ color: '#f87171', margin: 0, fontSize: '1.1rem' }}>Mantenimiento y Desinstalación de SentinelOS</h2>
              <p style={{ margin: '0.2rem 0 0', color: '#94a3b8', fontSize: '0.82rem' }}>
                Detener demonios en segundo plano, remover autoinicio (systemd en Linux o Programador de Tareas en Windows) y desinstalar el programa.
              </p>
            </div>
          </div>
          <button
            className="btn btn-danger"
            onClick={() => {
              setUninstallTargetServer('local');
              setUninstallConfirmText('');
              setUninstallModalOpen(true);
            }}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.1rem', fontWeight: 600 }}
          >
            <Trash2 size={16} /> Desinstalar Programa
          </button>
        </div>
      </div>
    </div>
    );
  };

  const renderNetworkStatusCard = () => {
    const net = networkDetails || data?.network || {};
    const internet = net.internet || {
      has_internet: true,
      latency_ms: 25,
      mode: 'online',
      status_label: 'Conectado a Internet',
      message: 'Acceso a WAN/Internet activo. Enlaces remotos y actualizaciones disponibles.'
    };
    const hasInternet = Boolean(internet.has_internet);
    const localIp = net.local_ip || net.primary?.ip || '127.0.0.1';
    const gateway = net.gateway || '192.168.1.1';
    const traffic = net.traffic || { upload_kbps: 0, download_kbps: 0, total_sent_mb: 0, total_recv_mb: 0 };
    const interfaces = net.interfaces && net.interfaces.length > 0 ? net.interfaces : (data?.network?.interfaces || []);
    const tsIp = data?.tailscale?.Self?.TailscaleIPs?.[0] || (data?.tailscale?.Self?.Addresses?.[0]) || 'No activa';

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* Banner Principal de Conectividad a Internet / Modo Local */}
        <div style={{
          background: hasInternet
            ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.05) 100%)'
            : 'linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(245, 158, 11, 0.06) 100%)',
          border: hasInternet ? '1px solid rgba(16, 185, 129, 0.35)' : '1px solid rgba(59, 130, 246, 0.35)',
          borderRadius: '12px',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, minWidth: '280px' }}>
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: hasInternet ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: hasInternet ? '1px solid #10b981' : '1px solid #3b82f6',
              boxShadow: hasInternet ? '0 0 16px rgba(16, 185, 129, 0.3)' : '0 0 16px rgba(59, 130, 246, 0.3)'
            }}>
              {hasInternet ? <Globe size={26} color="#34d399" /> : <Shield size={26} color="#60a5fa" />}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: hasInternet ? '#34d399' : '#60a5fa' }}>
                  {hasInternet ? 'CONECTADO A INTERNET (WAN ACTIVA)' : 'MODO SOBERANO / RED LOCAL PURA (AIR-GAPPED)'}
                </h3>
                <span style={{
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  background: hasInternet ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)',
                  color: hasInternet ? '#6ee7b7' : '#fcd34d',
                  border: hasInternet ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(245, 158, 11, 0.4)'
                }}>
                  {hasInternet ? `Latencia: ${internet.latency_ms || 25} ms` : '100% Funcional sin Internet'}
                </span>
              </div>
              <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.82rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                {hasInternet
                  ? 'El servidor tiene enlace directo hacia Internet público. Actualizaciones, agentes remotos y túneles Tailscale están operativos.'
                  : 'SentinelOS está operando con total soberanía en tu red local (LAN). La telemetría, Docker, terminales, IA local y Klipper funcionan sin internet.'}
              </p>
            </div>
          </div>

          <button
            onClick={handleCheckNetworkDetails}
            disabled={netChecking}
            className="btn btn-secondary"
            style={{
              padding: '0.55rem 1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.82rem',
              fontWeight: 600,
              background: 'rgba(255,255,255,0.06)',
              borderColor: 'rgba(255,255,255,0.15)'
            }}
          >
            <RefreshCw size={14} className={netChecking ? "spin" : ""} color="#38bdf8" />
            {netChecking ? 'Comprobando...' : 'Comprobar Conectividad Ahora'}
          </button>
        </div>

        {/* Grid de 4 Métricas Clave de Red */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.85rem' }}>
          {/* IP Local (LAN) */}
          <div className="glass-panel" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
              <Router size={20} color="#38bdf8" />
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>IP Local (LAN)</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace', letterSpacing: '0.03em' }}>{localIp}</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Interfaz: {net.primary?.name || 'Ethernet'}</div>
            </div>
          </div>

          {/* Puerta de Enlace (Gateway) */}
          <div className="glass-panel" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(168, 85, 247, 0.3)' }}>
              <Activity size={20} color="#c084fc" />
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Puerta de Enlace (Gateway)</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace', letterSpacing: '0.03em' }}>{gateway}</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Router / Switch Local</div>
            </div>
          </div>

          {/* Tailscale Mesh VPN */}
          <div className="glass-panel" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              <Shield size={20} color="#34d399" />
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>IP Tailscale (Malla)</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace', letterSpacing: '0.03em' }}>
                {tsIp}
              </div>
              <div style={{ fontSize: '0.7rem', color: tsIp !== 'No activa' ? '#34d399' : '#64748b' }}>
                {tsIp !== 'No activa' ? 'Enlace P2P Seguro Activo' : 'Red LAN directa'}
              </div>
            </div>
          </div>

          {/* Tráfico en Tiempo Real */}
          <div className="glass-panel" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
              <Zap size={20} color="#fbbf24" />
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Tráfico de Red en Vivo</div>
              <div style={{ fontSize: '0.92rem', fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace', display: 'flex', gap: '0.6rem' }}>
                <span style={{ color: '#38bdf8' }}>↑ {traffic.upload_kbps || 0} KB/s</span>
                <span style={{ color: '#34d399' }}>↓ {traffic.download_kbps || 0} KB/s</span>
              </div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
                Total: {traffic.total_sent_mb || 0} MB env / {traffic.total_recv_mb || 0} MB rec
              </div>
            </div>
          </div>
        </div>

        {/* Lista de Interfaces de Red Detectadas */}
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '0.95rem', color: '#e2e8f0' }}>
              <Cable size={18} color="#38bdf8" />
              <span>Interfaces de Red Físicas y Virtuales</span>
            </div>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              {interfaces.length} interfaz(ces) detectada(s)
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', color: '#64748b', fontSize: '0.72rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '0.6rem' }}>Tipo</th>
                  <th style={{ padding: '0.6rem' }}>Nombre</th>
                  <th style={{ padding: '0.6rem' }}>Dirección IPv4</th>
                  <th style={{ padding: '0.6rem' }}>Dirección MAC</th>
                  <th style={{ padding: '0.6rem' }}>Velocidad Enlace</th>
                  <th style={{ padding: '0.6rem' }}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {interfaces.map((iface, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '0.6rem' }}>
                      <span style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        background: iface.type === 'wifi' ? 'rgba(245, 158, 11, 0.15)' : iface.type === 'vpn' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                        color: iface.type === 'wifi' ? '#fbbf24' : iface.type === 'vpn' ? '#34d399' : '#60a5fa'
                      }}>
                        {iface.type}
                      </span>
                    </td>
                    <td style={{ padding: '0.6rem', fontWeight: 600, color: '#f1f5f9' }}>{iface.name}</td>
                    <td style={{ padding: '0.6rem', fontFamily: 'monospace', color: '#38bdf8' }}>{iface.ip || 'Sin IP'}</td>
                    <td style={{ padding: '0.6rem', fontFamily: 'monospace', color: '#94a3b8' }}>{iface.mac || 'N/A'}</td>
                    <td style={{ padding: '0.6rem', color: '#cbd5e1' }}>
                      {iface.speed ? `${iface.speed} Mbps` : 'Auto'}
                    </td>
                    <td style={{ padding: '0.6rem' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        color: iface.isup ? '#34d399' : '#94a3b8',
                        fontWeight: 600,
                        fontSize: '0.75rem'
                      }}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: iface.isup ? '#10b981' : '#64748b' }} />
                        {iface.isup ? 'ACTIVA / UP' : 'INACTIVA'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Tarjeta Educativa de Soberanía y Red Aislada */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '10px',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.85rem'
        }}>
          <Shield size={20} color="#38bdf8" style={{ marginTop: '2px', flexShrink: 0 }} />
          <div style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: '1.45' }}>
            <strong style={{ color: '#f8fafc' }}>¿Requiere SentinelOS conexión permanente a Internet?</strong>
            <br />
            <strong>No.</strong> SentinelOS fue diseñado para ser 100% soberano y autónomo. Todos los componentes (monitoreo de hardware, telemetría, Docker, terminales, control de impresión 3D Klipper y modelos de IA locales) funcionan sin necesidad de conexión externa. La conexión a Internet solo es requerida opcionalmente si deseas utilizar Tailscale para acceso remoto fuera de la LAN o para descargar actualizaciones.
          </div>
        </div>
      </div>
    );
  };

  const renderNetwork = () => {
    if (!data) {
      return (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
          <RefreshCw size={28} color="#3b82f6" style={{ animation: 'spin 1.5s linear infinite' }} />
          <p style={{ marginTop: '1rem', color: '#94a3b8' }}>Cargando telemetría de red y topología...</p>
        </div>
      );
    }

    // Unificar nodos y peers de Tailscale de todos los servidores registrados (Malla Global)
    const allTsPeers = [];
    const tsSources = [];

    const isLocalTsActive = Boolean(data?.tailscale?.BackendState === 'Running' || data?.tailscale?.Self);
    if (isLocalTsActive || data?.tailscale?.Self) {
      tsSources.push({ id: 'local', name: 'Host Maestro (Local)', tailnet: data.tailscale?.CurrentTailnet?.MagicDNSSuffix || 'Tailnet Local' });
      if (data?.tailscale?.Self) {
        allTsPeers.push({
          ...data.tailscale.Self,
          HostName: `${data.tailscale.Self.HostName} (Self - Host Maestro)`,
          serverId: 'local',
          serverName: 'Host Maestro (Local)',
          isSelf: true
        });
      }
      if (data?.tailscale?.Peer) {
        Object.values(data.tailscale.Peer).forEach(p => {
          if (p && p.HostName) {
            allTsPeers.push({
              ...p,
              serverId: 'local',
              serverName: 'Host Maestro (Local)',
              isSelf: false
            });
          }
        });
      }
    }

    Object.entries(remoteServersData).forEach(([srvId, srvObj]) => {
      const srvName = connectedServers.find(s => s.id === srvId)?.name || srvId;
      const rTs = srvObj?.data?.tailscale;
      const isRemoteTsActive = Boolean(rTs?.BackendState === 'Running' || rTs?.Self);
      if (isRemoteTsActive) {
        tsSources.push({ id: srvId, name: srvName, tailnet: rTs?.CurrentTailnet?.MagicDNSSuffix || 'Tailnet Remota' });
        if (rTs?.Self) {
          allTsPeers.push({
            ...rTs.Self,
            HostName: `${rTs.Self.HostName} (Self - ${srvName})`,
            serverId: srvId,
            serverName: srvName,
            isSelf: true
          });
        }
        if (rTs?.Peer) {
          Object.values(rTs.Peer).forEach(p => {
            if (p && p.HostName) {
              allTsPeers.push({
                ...p,
                serverId: srvId,
                serverName: srvName,
                isSelf: false
              });
            }
          });
        }
      }
    });

    const uniqueTsPeers = [];
    const seenIps = new Set();
    allTsPeers.forEach(p => {
      const ip = (p.TailscaleIPs || [])[0] || p.HostName;
      if (selectedTailscaleServer === 'all') {
        if (!seenIps.has(ip)) {
          seenIps.add(ip);
          uniqueTsPeers.push(p);
        }
      } else if (p.serverId === selectedTailscaleServer) {
        uniqueTsPeers.push(p);
      }
    });

    const activeTailnet = (selectedTailscaleServer !== 'all' 
      ? tsSources.find(s => s.id === selectedTailscaleServer)?.tailnet 
      : null) 
      || data?.tailscale?.CurrentTailnet?.MagicDNSSuffix 
      || tsSources[0]?.tailnet 
      || 'Desconectado';

    const handleTailscaleAction = async (action, params) => {
      const targetSrvId = selectedTailscaleServer === 'all' ? 'local' : selectedTailscaleServer;
      if (targetSrvId === 'local') {
        handleAction('tailscale', { action, params });
      } else {
        const srv = connectedServers.find(s => s.id === targetSrvId);
        if (!srv || !srv.url) return;
        const targetUrl = srv.url.replace(/\/+$/, '');
        try {
          const headers = { 'Content-Type': 'application/json' };
          if (srv.token) {
            headers['Authorization'] = `Bearer ${srv.token}`;
            headers['X-Sentinel-Token'] = srv.token;
          }
          await fetch(`${targetUrl}/api/action`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ action: 'tailscale', payload: { action, params } })
          });
        } catch (e) {
          console.error("Error al controlar Tailscale en servidor remoto:", e);
        }
      }
    };

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Sub-navegación de Red y Topología */}
        <div className="glass-panel" style={{ padding: '0.6rem 1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {[
            { id: 'status', label: 'Estado & Conectividad', icon: <Globe size={16} /> },
            { id: 'topology', label: 'Diagrama de Topología Visual', icon: <Layers size={16} /> },
            { id: 'tailscale', label: 'Tailscale VPN', icon: <Shield size={16} /> },
            { id: 'lan', label: 'Dispositivos LAN & Puertos', icon: <Router size={16} /> },
            { id: 'speedtest', label: 'Speedtest', icon: <Gauge size={16} /> },
            { id: 'all', label: 'Vista Completa', icon: <Activity size={16} /> }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setNetworkSubTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '0.45rem 0.9rem',
                borderRadius: '6px',
                fontSize: '0.84rem',
                fontWeight: 600,
                cursor: 'pointer',
                background: networkSubTab === tab.id ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                border: networkSubTab === tab.id ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.08)',
                color: networkSubTab === tab.id ? '#60a5fa' : '#cbd5e1',
                transition: 'all 0.2s ease'
              }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* 0. Estado de Conectividad, Internet e Interfaces de Red */}
        {(networkSubTab === 'status' || networkSubTab === 'all') && (
          renderNetworkStatusCard()
        )}

        {/* 1. Vista de Topología Visual Interactiva (Nodos, Sondas, Señales y Recursos) */}
        {(networkSubTab === 'topology' || networkSubTab === 'all') && (
          <NetworkTopologyView data={data} handleAction={handleAction} connectedServers={connectedServers} remoteServersData={remoteServersData} />
        )}

        {/* 2. Gestor Tailscale VPN Multi-Servidor */}
        {(networkSubTab === 'tailscale' || networkSubTab === 'all') && (
          <div className="glass-panel">
            <div className="panel-header" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Shield color="#38bdf8" />
                <div>
                  <h2 style={{ margin: 0 }}>Tailscale VPN Manager & Malla Zero-Trust</h2>
                  <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                    Sincronización multi-servidor ({uniqueTsPeers.length} peers detectados en {tsSources.length} nodos activos)
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: 'rgba(0,0,0,0.3)', padding: '0.25rem 0.5rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <span style={{ fontSize: '0.76rem', color: '#94a3b8', fontWeight: 600 }}>Servidor:</span>
                  <button
                    className={`server-filter-chip ${selectedTailscaleServer === 'all' ? 'active' : ''}`}
                    onClick={() => setSelectedTailscaleServer('all')}
                    style={{ padding: '0.25rem 0.6rem', fontSize: '0.76rem' }}
                  >
                    Malla Global ({connectedServers.length})
                  </button>
                  {connectedServers.map(srv => (
                    <button
                      key={srv.id}
                      className={`server-filter-chip ${selectedTailscaleServer === srv.id ? 'active' : ''}`}
                      onClick={() => setSelectedTailscaleServer(srv.id)}
                      style={{ padding: '0.25rem 0.6rem', fontSize: '0.76rem' }}
                    >
                      {srv.name}
                    </button>
                  ))}
                </div>

                <button className="btn btn-primary" onClick={() => handleTailscaleAction('up')}>TS Up</button>
                <button className="btn" onClick={() => handleTailscaleAction('up', '--advertise-exit-node')}>Advertise Exit Node</button>
                <button className="btn btn-danger" onClick={() => handleTailscaleAction('down')}>TS Down</button>
              </div>
            </div>
            <div className="stat-row" style={{ marginBottom: '1rem', marginTop: '0.75rem' }}>
              <span className="stat-label">Tailnet Red:</span>
              <span className="stat-value" style={{ color: 'var(--accent)', fontWeight: 600 }}>{activeTailnet}</span>
            </div>
            <table className="os-table">
              <thead>
                <tr>
                  <th>Peer / Nodo</th>
                  <th>Servidor Origen</th>
                  <th>Sistema Operativo</th>
                  <th>IP Tailscale (IPv4)</th>
                  <th>Estado / Última Conexión</th>
                </tr>
              </thead>
              <tbody>
                {uniqueTsPeers.map((peer, idx) => (
                  <tr key={idx}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div className={`status-indicator ${peer.Online ? 'status-online' : 'status-offline'}`}></div>
                        <span style={{ fontWeight: peer.isSelf ? 'bold' : 'normal', color: peer.isSelf ? '#38bdf8' : 'inherit' }}>
                          {peer.HostName}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.74rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: peer.serverId === 'local' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(16, 185, 129, 0.15)', color: peer.serverId === 'local' ? '#60a5fa' : '#34d399', border: '1px solid rgba(255,255,255,0.06)' }}>
                        {peer.serverName}
                      </span>
                    </td>
                    <td>{peer.OS || 'N/A'}</td>
                    <td style={{ fontFamily: 'monospace', color: '#38bdf8' }}>{(peer.TailscaleIPs || [])[0]}</td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {peer.LastSeen ? new Date(peer.LastSeen).toLocaleString() : 'Activo (En línea)'}
                    </td>
                  </tr>
                ))}
                {uniqueTsPeers.length === 0 && (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                      Tailscale no está activo o configurado en los servidores seleccionados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* 3. Speedtest */}
        {(networkSubTab === 'speedtest' || networkSubTab === 'all') && (
          <div className="glass-panel">
            <div className="panel-header" style={{justifyContent: 'space-between'}}>
              <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center'}}>
                <Gauge /><h2>Internet Speedtest</h2>
              </div>
              <button className="btn btn-primary" onClick={runSpeedtest} disabled={speedtestRunning}>
                {speedtestRunning ? "Testing..." : "Run Speedtest"}
              </button>
            </div>
            {speedtestResult && speedtestResult.ping && (
              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginTop: '1rem', textAlign: 'center'}}>
                <div className="stat-card" style={{padding: '1rem'}}>
                  <div style={{fontSize: '0.9rem', color: 'var(--text-secondary)'}}>Ping</div>
                  <div style={{fontSize: '1.5rem', fontWeight: 'bold'}}>{speedtestResult.ping.toFixed(1)} ms</div>
                </div>
                <div className="stat-card" style={{padding: '1rem'}}>
                  <div style={{fontSize: '0.9rem', color: 'var(--text-secondary)'}}>Download</div>
                  <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--success)'}}>{(speedtestResult.download / 1e6).toFixed(2)} Mbps</div>
                </div>
                <div className="stat-card" style={{padding: '1rem'}}>
                  <div style={{fontSize: '0.9rem', color: 'var(--text-secondary)'}}>Upload</div>
                  <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent)'}}>{(speedtestResult.upload / 1e6).toFixed(2)} Mbps</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 4. Dispositivos LAN, Firewall y Puertos Abiertos */}
        {(networkSubTab === 'lan' || networkSubTab === 'all') && (
          <>
            <div className="glass-panel" style={{position: 'relative'}}>
              <div className="panel-header" style={{justifyContent: 'space-between'}}>
                <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center'}}><Router /><h2>Local LAN Devices</h2></div>
                <div style={{display: 'flex', gap: '0.5rem'}}>
                  <button className="btn btn-secondary" onClick={() => forceNetworkScan('quick')} disabled={isNetworkScanning}>
                     {isNetworkScanning ? 'Scanning...' : <><RefreshCw size={16}/> Quick Scan</>}
                  </button>
                  <button className="btn btn-primary" onClick={() => forceNetworkScan('deep')} disabled={isNetworkScanning}>
                     {isNetworkScanning ? 'Scanning...' : <><RefreshCw size={16}/> Deep Scan</>}
                  </button>
                </div>
              </div>
              {isNetworkScanning && (
                <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: '4px', background: 'var(--bg-lighter)', overflow: 'hidden', borderRadius: '8px 8px 0 0'}}>
                  <div style={{height: '100%', background: 'var(--accent)', animation: 'pulse 1s infinite', width: '50%'}}></div>
                </div>
              )}
              <table className="os-table" style={{opacity: isNetworkScanning ? 0.5 : 1}}>
                <thead><tr><th>IP</th><th>MAC</th><th>Interface</th><th>Vendor</th><th>Device Type</th><th>Acciones</th></tr></thead>
                <tbody>
                  {data.network?.neighbors?.map(n => (
                    <tr key={n.ip}>
                      <td>{n.ip}</td>
                      <td style={{fontSize: '0.85rem', fontFamily: 'monospace'}}>{n.mac}</td>
                      <td style={{color: 'var(--text-secondary)'}}>{n.interface}</td>
                      <td style={{color: 'var(--text-secondary)'}}>{n.vendor}</td>
                      <td style={{color: 'var(--accent)', fontWeight: 500}}>{n.device_type}</td>
                      <td style={{textAlign: 'right'}}>
                        <button className="btn" title="Wake-on-LAN" style={{padding: '0.2rem 0.5rem'}} onClick={() => handleWoL(n.mac)}><Zap size={14}/></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="glass-panel">
              <div className="panel-header"><Shield /><h2>UFW Firewall Status: <span style={{color: data.system.ufw?.enabled ? 'var(--success)' : 'var(--danger)'}}>{data.system.ufw?.enabled ? 'ACTIVE' : 'INACTIVE'}</span></h2></div>
              <table className="os-table">
                <thead><tr><th>Rule</th></tr></thead>
                <tbody>
                  {data.system.ufw?.rules?.map((r, i) => (
                    <tr key={i}>
                      <td style={{fontFamily: 'monospace'}}>{r}</td>
                    </tr>
                  ))}
                  {(!data.system.ufw?.rules || data.system.ufw.rules.length === 0) && (
                    <tr><td style={{textAlign: 'center', color: 'var(--text-secondary)'}}>No firewall rules or UFW inactive.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="glass-panel">
              <div className="panel-header"><Database /><h2>Open Ports (Listening)</h2></div>
              <table className="os-table">
                <thead><tr><th>Protocol</th><th>State</th><th>Local Address:Port</th></tr></thead>
                <tbody>
                  {data.system.open_ports?.map((p, i) => (
                    <tr key={i}>
                      <td style={{fontWeight: 'bold'}}>{p.protocol}</td>
                      <td style={{color: 'var(--success)'}}>{p.state}</td>
                      <td style={{fontFamily: 'monospace', color: 'var(--accent)'}}>{p.local_address}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    );
  };

  const renderLogs = () => {
    // 1. Recopilar listas de líneas por servidor
    const localLines = (wsLogs && wsLogs.length > 0)
      ? wsLogs
      : (sysLogs ? sysLogs.split('\n').filter(Boolean) : []);

    const serverLogMap = {
      'local': {
        server: connectedServers.find(s => s.id === 'local') || { id: 'local', name: 'Host Maestro (Local)', isLocal: true, status: 'online' },
        lines: logClearedMap['local'] ? [] : localLines,
        badgeColor: '#60a5fa'
      }
    };

    connectedServers.filter(s => !s.isLocal).forEach((srv, sIdx) => {
      const colors = ['#34d399', '#a855f7', '#f59e0b', '#ec4899'];
      const badgeColor = colors[sIdx % colors.length] || '#34d399';
      serverLogMap[srv.id] = {
        server: srv,
        lines: logClearedMap[srv.id] ? [] : (remoteLogs[srv.id] || []),
        badgeColor
      };
    });

    const isVistaCompletaLogs = selectedLogServers.length === connectedServers.length && connectedServers.length > 1;
    const serversToDisplay = connectedServers.filter(s => selectedLogServers.includes(s.id));

    // Función auxiliar para copiar logs de una ventana
    const handleCopyWindowLogs = (srvId, lines) => {
      try {
        navigator.clipboard.writeText(lines.join('\n'));
        setLogCopiedMap(prev => ({ ...prev, [srvId]: true }));
        setTimeout(() => {
          setLogCopiedMap(prev => ({ ...prev, [srvId]: false }));
        }, 2000);
      } catch (e) {}
    };

    // Función auxiliar para limpiar la ventana
    const handleClearWindowLogs = (srvId) => {
      setLogClearedMap(prev => ({ ...prev, [srvId]: true }));
    };

    // Renderizar una ventana de terminal individual para un servidor específico
    const renderTerminalWindow = (srvId) => {
      const srvData = serverLogMap[srvId];
      if (!srvData) return null;
      const srv = srvData.server;
      const allLines = srvData.lines || [];
      const searchQuery = (logSearchMap[srvId] || '').toLowerCase();
      const isPaused = Boolean(logPausedMap[srvId]);
      const isCopied = Boolean(logCopiedMap[srvId]);

      const visibleLines = allLines.filter(line => {
        if (!searchQuery) return true;
        return line.toLowerCase().includes(searchQuery);
      });

      return (
        <div
          key={srvId}
          className="glass-panel"
          style={{
            display: 'flex',
            flexDirection: 'column',
            borderRadius: '10px',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            background: 'rgba(10, 15, 29, 0.92)',
            overflow: 'hidden',
            minHeight: '440px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
          }}
        >
          {/* Barra de Título Estilo Mac / Terminal Cyberpunk */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.6rem 0.9rem',
            background: 'rgba(15, 23, 42, 0.95)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            flexWrap: 'wrap',
            gap: '0.5rem'
          }}>
            {/* Controles de ventana y Título */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <div style={{ display: 'flex', gap: '5px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Server size={14} color={srvData.badgeColor} />
                <span style={{ fontSize: '0.84rem', fontWeight: 700, color: '#f8fafc' }}>
                  {srv.name}
                </span>
                <span style={{
                  fontSize: '0.68rem',
                  fontWeight: 700,
                  padding: '1px 6px',
                  borderRadius: '4px',
                  background: `${srvData.badgeColor}20`,
                  color: srvData.badgeColor,
                  border: `1px solid ${srvData.badgeColor}40`
                }}>
                  {srv.isLocal ? 'HOST MAESTRO' : 'SATÉLITE'}
                </span>
              </div>
            </div>

            {/* Herramientas de la Ventana: Filtro, Copiar, Limpiar, Pausar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <div style={{ position: 'relative', width: '140px' }}>
                <Search size={11} style={{ position: 'absolute', left: '7px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
                <input
                  type="text"
                  placeholder="Filtrar logs..."
                  value={logSearchMap[srvId] || ''}
                  onChange={e => setLogSearchMap(prev => ({ ...prev, [srvId]: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '0.25rem 0.5rem 0.25rem 1.4rem',
                    fontSize: '0.72rem',
                    borderRadius: '4px',
                    background: 'rgba(0, 0, 0, 0.4)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#ffffff',
                    outline: 'none'
                  }}
                />
              </div>

              <button
                onClick={() => setLogPausedMap(prev => ({ ...prev, [srvId]: !prev[srvId] }))}
                className="btn btn-secondary"
                style={{ padding: '0.25rem 0.45rem', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                title={isPaused ? "Reanudar auto-scroll" : "Pausar auto-scroll"}
              >
                {isPaused ? <Play size={11} color="#10b981" /> : <Square size={11} color="#f59e0b" />}
                <span style={{ fontSize: '0.68rem' }}>{isPaused ? 'Pausado' : 'En vivo'}</span>
              </button>

              <button
                onClick={() => handleCopyWindowLogs(srvId, allLines)}
                className="btn btn-secondary"
                style={{ padding: '0.25rem 0.45rem', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                title="Copiar contenido de esta terminal"
              >
                {isCopied ? <Check size={11} color="#10b981" /> : <Copy size={11} />}
                <span style={{ fontSize: '0.68rem' }}>{isCopied ? 'Copiado' : 'Copiar'}</span>
              </button>

              <button
                onClick={() => handleClearWindowLogs(srvId)}
                className="btn btn-secondary"
                style={{ padding: '0.25rem 0.45rem', fontSize: '0.72rem' }}
                title="Limpiar ventana"
              >
                <Trash2 size={11} color="#ef4444" />
              </button>
            </div>
          </div>

          {/* Área de Visualización de Logs de la Ventana */}
          <div style={{
            flex: 1,
            padding: '0.85rem',
            overflowY: 'auto',
            fontFamily: 'Consolas, "Fira Code", monospace',
            fontSize: '0.8rem',
            lineHeight: '1.45',
            background: 'rgba(3, 7, 18, 0.88)',
            color: '#cbd5e1',
            display: 'flex',
            flexDirection: 'column-reverse',
            maxHeight: logViewMode === 'tabs' ? '68vh' : '520px'
          }}>
            <div>
              {visibleLines.length > 0 ? visibleLines.map((line, idx) => {
                let color = '#cbd5e1';
                let fontWeight = 400;
                const l = line.toLowerCase();
                if (l.includes('crit') || l.includes('fatal')) { color = '#ef4444'; fontWeight = 700; }
                else if (l.includes('error') || l.includes('fail')) { color = '#f97316'; fontWeight = 600; }
                else if (l.includes('warn')) color = '#eab308';
                else if (l.includes('info') || l.includes('success')) color = '#38bdf8';
                else if (l.includes('http') || l.includes('get ') || l.includes('post ')) color = '#a5b4fc';

                return (
                  <div
                    key={`${srvId}-line-${idx}`}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.65rem',
                      padding: '2px 0',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.03)'
                    }}
                  >
                    <span style={{ color: '#475569', fontSize: '0.72rem', userSelect: 'none', width: '28px', textAlign: 'right' }}>
                      {idx + 1}
                    </span>
                    <span style={{ color, fontWeight, flex: 1, wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>
                      {line}
                    </span>
                  </div>
                );
              }) : (
                <div style={{ color: '#64748b', textAlign: 'center', padding: '2rem 1rem', fontSize: '0.8rem' }}>
                  {logClearedMap[srvId]
                    ? 'Terminal despejada por el usuario. Nuevos eventos aparecerán aquí.'
                    : (searchQuery
                      ? `No se encontraron coincidencias para "${searchQuery}".`
                      : 'Esperando flujo de registros en vivo para este servidor...')}
                </div>
              )}
            </div>
          </div>

          {/* Pie de Ventana con Estado de Stream */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '0.35rem 0.9rem',
            background: 'rgba(15, 23, 42, 0.85)',
            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            fontSize: '0.7rem',
            color: '#64748b',
            fontFamily: 'monospace'
          }}>
            <span>Líneas activas: <strong style={{ color: '#94a3b8' }}>{visibleLines.length}</strong></span>
            <span>{srv.url ? srv.url : 'http://127.0.0.1:8001'}</span>
          </div>
        </div>
      );
    };

    // Modo Consolidado (Stream único mezclado si lo eligen)
    const combinedLogEntries = [];
    if (localLines.length > 0) {
      localLines.forEach((line, idx) => {
        combinedLogEntries.push({
          id: `local-${idx}`,
          serverId: 'local',
          serverName: 'LOCAL',
          text: line,
          colorBadge: '#60a5fa'
        });
      });
    }
    Object.entries(remoteLogs).forEach(([srvId, lines]) => {
      const srvObj = connectedServers.find(s => s.id === srvId) || { name: srvId };
      const colors = ['#34d399', '#a855f7', '#f59e0b', '#ec4899'];
      const srvIdx = connectedServers.findIndex(s => s.id === srvId);
      const colorBadge = colors[srvIdx % colors.length] || '#34d399';
      lines.forEach((line, idx) => {
        combinedLogEntries.push({
          id: `${srvId}-${idx}`,
          serverId: srvId,
          serverName: srvObj.name.toUpperCase(),
          text: line,
          colorBadge
        });
      });
    });
    const visibleEntries = combinedLogEntries.filter(entry => selectedLogServers.includes(entry.serverId));

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', minHeight: '85vh' }}>
        {/* Barra Superior con Selector de Modo de Ventanas y Servidores */}
        <div className="glass-panel" style={{ padding: '0.75rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Terminal size={22} color="#38bdf8" />
            <div>
              <h2 style={{ margin: 0, fontSize: '1.05rem', color: '#f8fafc' }}>Terminal de Logs por Servidor</h2>
              <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                Monitoreo de flujo y telemetría por ventanas independientes
              </span>
            </div>
          </div>

          {/* Selector de Modo de Disposición de Ventanas */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', background: 'rgba(0, 0, 0, 0.4)', borderRadius: '6px', padding: '2px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <button
                className={`server-filter-chip ${logViewMode === 'windows' ? 'active' : ''}`}
                onClick={() => setLogViewMode('windows')}
                style={{ padding: '0.3rem 0.65rem', fontSize: '0.76rem', borderRadius: '4px' }}
                title="Mostrar cada servidor en su propia ventana en pantalla dividida"
              >
                <Layers size={13} /> Ventanas Separadas
              </button>
              <button
                className={`server-filter-chip ${logViewMode === 'tabs' ? 'active' : ''}`}
                onClick={() => setLogViewMode('tabs')}
                style={{ padding: '0.3rem 0.65rem', fontSize: '0.76rem', borderRadius: '4px' }}
                title="Mostrar una pestaña individual por cada servidor"
              >
                <Server size={13} /> Pestañas
              </button>
              <button
                className={`server-filter-chip ${logViewMode === 'consolidated' ? 'active' : ''}`}
                onClick={() => setLogViewMode('consolidated')}
                style={{ padding: '0.3rem 0.65rem', fontSize: '0.76rem', borderRadius: '4px' }}
                title="Ver flujo unificado de todos los servidores en una sola lista"
              >
                <Share2 size={13} /> Stream Único
              </button>
            </div>

            {/* Chips de Selección de Servidores Activos */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
              {connectedServers.length > 1 && (
                <button
                  className={`server-filter-chip ${isVistaCompletaLogs ? 'vista-completa active' : ''}`}
                  onClick={selectAllLogServers}
                  style={{ padding: '0.3rem 0.6rem', fontSize: '0.76rem' }}
                >
                  Todos ({connectedServers.length})
                </button>
              )}
              {connectedServers.map(srv => {
                const isSelected = selectedLogServers.includes(srv.id);
                return (
                  <button
                    key={srv.id}
                    className={`server-filter-chip ${isSelected ? 'active' : ''}`}
                    onClick={() => toggleLogServerSelection(srv.id)}
                    style={{ padding: '0.3rem 0.6rem', fontSize: '0.76rem' }}
                  >
                    {isSelected && <Check size={11} color="#60a5fa" />}
                    <span>{srv.name}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* 1. MODO VENTANAS SEPARADAS (SPLIT PANES / GRID DE VENTANAS INDEPENDIENTES) */}
        {logViewMode === 'windows' && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: serversToDisplay.length > 1 ? 'repeat(auto-fit, minmax(min(100%, 540px), 1fr))' : '1fr',
            gap: '1.25rem',
            flex: 1
          }}>
            {serversToDisplay.map(srv => renderTerminalWindow(srv.id))}
          </div>
        )}

        {/* 2. MODO PESTAÑAS (TABS INDIVIDUALES A PANTALLA COMPLETA) */}
        {logViewMode === 'tabs' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', flex: 1 }}>
            <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '0.5rem' }}>
              {serversToDisplay.map(srv => (
                <button
                  key={srv.id}
                  onClick={() => setActiveLogTab(srv.id)}
                  style={{
                    padding: '0.4rem 0.9rem',
                    borderRadius: '6px',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: activeLogTab === srv.id ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                    border: activeLogTab === srv.id ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.08)',
                    color: activeLogTab === srv.id ? '#60a5fa' : '#94a3b8'
                  }}
                >
                  {srv.name}
                </button>
              ))}
            </div>
            {renderTerminalWindow(activeLogTab)}
          </div>
        )}

        {/* 3. MODO CONSOLIDADO (FLUJO UNIFICADO DE TODOS LOS SERVIDORES) */}
        {logViewMode === 'consolidated' && (
          <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '520px', padding: '1rem' }}>
            <div style={{
              flex: 1,
              background: 'rgba(3, 7, 18, 0.88)',
              padding: '1rem',
              borderRadius: '8px',
              overflowY: 'auto',
              fontFamily: 'monospace',
              fontSize: '0.82rem',
              whiteSpace: 'pre-wrap',
              color: '#d1d5db',
              display: 'flex',
              flexDirection: 'column-reverse'
            }}>
              <div>
                {visibleEntries.length > 0 ? visibleEntries.map((entry) => {
                  let color = 'inherit';
                  let fontWeight = 'normal';
                  const l = entry.text.toLowerCase();
                  if (l.includes('crit') || l.includes('fatal')) { color = '#ef4444'; fontWeight = 'bold'; }
                  else if (l.includes('error') || l.includes('fail')) color = '#f97316';
                  else if (l.includes('warn')) color = '#eab308';
                  else if (l.includes('info') || l.includes('success')) color = '#38bdf8';

                  return (
                    <div key={entry.id} style={{ color, fontWeight, paddingBottom: '0.25rem', marginBottom: '0.25rem', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                      <span style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        padding: '0.1rem 0.4rem',
                        borderRadius: '4px',
                        background: `${entry.colorBadge}20`,
                        color: entry.colorBadge,
                        border: `1px solid ${entry.colorBadge}50`,
                        whiteSpace: 'nowrap'
                      }}>
                        [{entry.serverName}]
                      </span>
                      <span style={{ flex: 1 }}>{entry.text}</span>
                    </div>
                  );
                }) : <div style={{ color: 'var(--text-secondary)' }}>Esperando flujo de registros de los servidores seleccionados...</div>}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderMarketplace = () => {
    return (
      <div className="glass-panel" style={{height: '100%', minHeight: '85vh', display: 'flex', flexDirection: 'column'}}>
        <div className="panel-header" style={{justifyContent: 'space-between', marginBottom: '1.5rem'}}>
          <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center'}}><Package /><h2>Ubuntu Snap Store</h2></div>
          <div className="tab-menu" style={{display: 'flex', gap: '1rem', background: 'rgba(0,0,0,0.3)', padding: '0.2rem', borderRadius: '8px'}}>
            <button className={`btn ${marketplaceTab==='store'?'btn-primary':'btn-secondary'}`} onClick={()=>setMarketplaceTab('store')}>Store</button>
            <button className={`btn ${marketplaceTab==='installed'?'btn-primary':'btn-secondary'}`} onClick={()=>setMarketplaceTab('installed')}>Installed</button>
          </div>
        </div>

        {marketplaceTab === 'store' && (
          <>
            <form onSubmit={searchMarketplace} style={{display: 'flex', gap: '0.5rem', marginBottom: '2rem'}}>
              <input type="text" className="os-input" placeholder="Search Snap Store... (e.g. nextcloud, docker)" value={marketplaceSearch} onChange={e => setMarketplaceSearch(e.target.value)} style={{flex: 1}}/>
              <button type="submit" className="btn btn-primary" disabled={marketplaceSearching}>{marketplaceSearching ? 'Searching...' : 'Search'}</button>
            </form>
            
            {marketplaceResults.length === 0 && !marketplaceSearching ? (
              <div style={{textAlign: 'center', color: 'var(--text-secondary)', padding: '3rem', flex: 1}}>
                <ShoppingBag size={48} style={{opacity: 0.5, marginBottom: '1rem'}}/>
                <h3>Search the global Ubuntu Snap Store</h3>
                <p>Try searching for "nextcloud", "docker", "spotify", or "microk8s".</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                {marketplaceResults.map(app => (
                  <div key={app.id} className="app-card" style={{display: 'flex', flexDirection: 'column', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px'}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem'}}>
                      <div style={{background: 'rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '12px'}}><Package size={32}/></div>
                      <div style={{flex: 1}}>
                        <h3 style={{margin: 0, fontSize: '1.2rem'}}>{app.name}</h3>
                        <span style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>v{app.version}</span>
                      </div>
                    </div>
                    <div style={{fontSize: '0.8rem', color: 'var(--success)', marginBottom: '1rem'}}>by {app.publisher}</div>
                    <p style={{color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', flex: 1}}>{app.desc}</p>
                    
                    {(() => {
                      const isInstalled = installedSnaps.some(s => s.name === app.id);
                      return (
                        <button 
                          className={`btn ${isInstalled ? 'btn-secondary' : 'btn-primary'}`} 
                          style={{width: '100%', padding: '0.75rem', opacity: isInstalled ? 0.7 : 1, cursor: isInstalled ? 'not-allowed' : 'pointer'}} 
                          disabled={isInstalled}
                          onClick={() => setInstallModalApp(app)}
                        >
                          {isInstalled ? '✅ Instalado' : 'Install via Snap'}
                        </button>
                      );
                    })()}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {marketplaceTab === 'installed' && (
          <div style={{ flex: 1, overflowY: 'auto' }}>
            <table className="os-table">
              <thead><tr><th>App Name</th><th>Version</th><th>Publisher</th><th>Notes</th><th>Action</th></tr></thead>
              <tbody>
                {installedSnaps.map(app => (
                  <tr key={app.name}>
                    <td style={{fontWeight: 'bold', color: 'var(--accent)'}}>{app.name}</td>
                    <td>{app.version}</td>
                    <td style={{color: 'var(--text-secondary)'}}>{app.publisher}</td>
                    <td style={{color: 'var(--text-secondary)'}}>{app.notes}</td>
                    <td>
                      <button className="btn btn-danger" style={{padding: '0.3rem 0.6rem'}} onClick={() => uninstallSnap(app.name)}><Trash2 size={14}/> Uninstall</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{textAlign: 'center', marginTop: '1rem'}}>
               <button className="btn" onClick={loadInstalledSnaps}><RefreshCw size={14}/> Refresh</button>
            </div>
          </div>
        )}

      </div>
    );
  };

  const renderSandbox = () => {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
          <button className={`btn ${sandboxTab === 'arsenal' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setSandboxTab('arsenal')}>Arsenal (Herramientas)</button>
          <button className={`btn ${sandboxTab === 'command' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setSandboxTab('command')}>Command Center</button>
        </div>

        {sandboxTab === 'arsenal' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {sandboxTools.map(tool => (
              <div key={tool.id} className="app-card" style={{display: 'flex', flexDirection: 'column', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem'}}>
                  <div style={{background: 'rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '12px'}}><Shield size={32}/></div>
                  <div style={{flex: 1}}>
                    <h3 style={{margin: 0, fontSize: '1.2rem'}}>{tool.name}</h3>
                    <span style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>{tool.category}</span>
                  </div>
                </div>
                <div style={{fontSize: '0.8rem', color: 'var(--accent)', marginBottom: '1rem'}}>{tool.repo}</div>
                <p style={{color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', flex: 1}}>{tool.desc}</p>
                
                <button 
                  className={`btn ${tool.installed ? 'btn-secondary' : 'btn-primary'}`} 
                  style={{width: '100%', padding: '0.75rem', opacity: tool.installed ? 0.7 : 1, cursor: tool.installed ? 'pointer' : 'pointer'}} 
                  onClick={() => {
                    if (tool.installed) {
                      // Create a new terminal session
                      const sessionId = `${tool.id}-${Date.now()}`;
                      setSandboxSessions(prev => [...prev, { id: sessionId, tool, active: true }]);
                      setSandboxTab('command');
                    } else {
                      setTerminalPopupApp({ app: tool, minimized: false, status: 'installing' });
                    }
                  }}
                >
                  {tool.installed ? 'Seleccionar / Abrir Terminal' : 'Clonar e Instalar'}
                </button>
              </div>
            ))}
          </div>
        )}

        {sandboxTab === 'command' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
            {sandboxSessions.length === 0 ? (
              <div style={{textAlign: 'center', color: 'var(--text-secondary)', padding: '3rem'}}>
                <TerminalSquare size={48} style={{opacity: 0.5, marginBottom: '1rem'}}/>
                <h3>Ninguna Terminal Activa</h3>
                <p>Ve al Arsenal y selecciona una herramienta para iniciar una sesión.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
                {sandboxSessions.map(session => (
                  <div 
                    key={session.id} 
                    onClick={() => setSandboxSessions(prev => prev.map(s => ({...s, active: s.id === session.id})))}
                    style={{ 
                      padding: '0.5rem 1rem', 
                      background: session.active ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <Terminal size={14} />
                    {session.tool.name}
                    <div 
                      onClick={(e) => {
                        e.stopPropagation();
                        // Cleanup term and ws
                        if (sandboxWsRef.current[session.id]) sandboxWsRef.current[session.id].close();
                        if (sandboxTerminalsRef.current[session.id]) sandboxTerminalsRef.current[session.id].dispose();
                        setSandboxSessions(prev => {
                          const next = prev.filter(s => s.id !== session.id);
                          if (next.length > 0 && session.active) next[next.length - 1].active = true;
                          return next;
                        });
                      }}
                      style={{ padding: '2px', marginLeft: '0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}
                    >
                      <Trash2 size={12} color="var(--danger)" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Terminals have been moved to the root os-content so they never unmount */}
          </div>
        )}
      </div>
    );
  };

  const renderServerModal = () => (
    <div className="server-modal-backdrop" onClick={() => setServerModalOpen(false)}>
      <div className="server-modal-box" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Server size={22} color="#3b82f6" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#ffffff' }}>Gestión de Servidores y Red Mesh</h3>
          </div>
          <button
            onClick={() => setServerModalOpen(false)}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Token PIN de Vinculación de este Nodo Core */}
        {localNodeAuth?.token && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(234, 179, 8, 0.08) 0%, rgba(202, 138, 4, 0.03) 100%)',
            border: '1px solid rgba(234, 179, 8, 0.35)',
            borderRadius: '10px',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#fbbf24', fontWeight: 700, fontSize: '0.85rem' }}>
                <Key size={16} /> Token PIN de este Servidor Maestro
              </div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                ID: {localNodeAuth.node_id}
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.4' }}>
              Usa este <strong>Token PIN</strong> para conectar servidores secundarios / satélites durante su instalación seleccionando la opción <em>"Servidor Secundario / Satélite"</em>:
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(0, 0, 0, 0.45)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              padding: '0.45rem 0.85rem',
              gap: '0.75rem'
            }}>
              <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontSize: '0.92rem', letterSpacing: '0.05em', userSelect: 'all', fontWeight: 600 }}>
                {localNodeAuth.token}
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  navigator.clipboard.writeText(localNodeAuth.token);
                  setTokenCopied(true);
                  setTimeout(() => setTokenCopied(false), 2500);
                }}
                style={{
                  padding: '0.3rem 0.75rem',
                  fontSize: '0.78rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  borderColor: tokenCopied ? '#10b981' : 'rgba(255, 255, 255, 0.15)',
                  color: tokenCopied ? '#34d399' : '#e2e8f0'
                }}
              >
                {tokenCopied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                {tokenCopied ? '¡Copiado!' : 'Copiar Token'}
              </button>
            </div>
          </div>
        )}

        {/* Servidores Actuales */}
        <div>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '0.6rem' }}>
            Servidores Conectados Actualmente ({connectedServers.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {connectedServers.map(srv => {
              const isOnline = srv.isLocal ? true : remoteServersData[srv.id]?.status !== 'offline';
              return (
                <div
                  key={srv.id}
                  style={{
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '0.75rem 1rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isOnline ? '#10b981' : '#ef4444', boxShadow: isOnline ? '0 0 8px rgba(16,185,129,0.5)' : 'none' }} />
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem' }}>{srv.name}</span>
                        <span style={{
                          fontSize: '0.68rem',
                          padding: '0.1rem 0.4rem',
                          borderRadius: '4px',
                          fontWeight: 700,
                          background: isOnline ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                          color: isOnline ? '#34d399' : '#f87171',
                          border: `1px solid ${isOnline ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                        }}>
                          {isOnline ? 'ONLINE' : 'DESCONECTADO'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>
                        {srv.isLocal ? '127.0.0.1 (Nodo Local Maestro)' : srv.url}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {srv.isLocal ? (
                      <span style={{ fontSize: '0.75rem', color: '#60a5fa', fontWeight: 700 }}>PRINCIPAL</span>
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              const targetUrl = srv.url.replace(/\/+$/, '');
                              const headers = srv.token ? { 'Authorization': `Bearer ${srv.token}`, 'X-Sentinel-Token': srv.token } : {};
                              let res;
                              try {
                                res = await fetch(`${targetUrl}/api/node/info`, { headers, signal: AbortSignal.timeout(3500) });
                              } catch(e) {
                                res = await fetch(`${API_URL}/remote/proxy?target_url=${encodeURIComponent(targetUrl + '/api/node/info')}`, { headers, signal: AbortSignal.timeout(5000) });
                              }
                              if (res.ok) {
                                addNotification(`Nodo ${srv.name} responde correctamente.`, 'success');
                              } else {
                                addNotification(`Nodo ${srv.name} respondió con error ${res.status}.`, 'warning');
                              }
                            } catch(e) {
                              addNotification(`No se pudo contactar a ${srv.name}. Revisa IP y firewall.`, 'error');
                            }
                          }}
                          className="btn btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                          title="Probar conectividad inmediata"
                        >
                          Probar
                        </button>
                        <button
                          onClick={() => handleRemoveServer(srv.id)}
                          className="btn btn-danger"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          Desconectar
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Nodos Detectados en Malla / Tailscale */}
        {(() => {
          const unconnectedMeshNodes = meshDiscoveredNodes.filter(n => !connectedServers.some(s => s.url?.includes(n.node_name) || (n.candidates && n.candidates.some(c => s.url?.includes(c.replace(/https?:\/\//, '').replace(/:.*$/, ''))))));
          return (
            <div style={{
              background: 'rgba(16, 185, 129, 0.05)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: '10px',
              padding: '0.85rem 1rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.6rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Activity size={15} /> Nodos Detectados en la Red / Malla (1-Clic para Conectar)
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    disabled={scanningLan}
                    onClick={handleScanLan}
                    style={{
                      fontSize: '0.72rem',
                      padding: '0.25rem 0.55rem',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      borderColor: 'rgba(52, 211, 153, 0.4)',
                      color: '#34d399',
                      background: 'rgba(52, 211, 153, 0.1)'
                    }}
                    title="Escanear la subred local (Wi-Fi/Ethernet) en busca de otros equipos con SentinelOS"
                  >
                    <RefreshCw size={12} className={scanningLan ? 'spin' : ''} />
                    {scanningLan ? 'Escaneando LAN...' : 'Escanear Red LAN'}
                  </button>
                  <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>UDP Beacon + Subred</span>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                {unconnectedMeshNodes.length === 0 ? (
                  <div style={{ fontSize: '0.78rem', color: '#94a3b8', fontStyle: 'italic', padding: '0.4rem 0.2rem' }}>
                    {scanningLan ? 'Buscando servidores activos en la subred local...' : 'No se han detectado otros nodos aún. Si instalaste SentinelOS en otra PC de la red, presiona "Escanear Red LAN" o conéctala directamente por IP abajo.'}
                  </div>
                ) : (
                  unconnectedMeshNodes.map((node, idx) => (
                    <div key={idx} style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.5rem 0.75rem',
                      background: 'rgba(0, 0, 0, 0.35)',
                      border: '1px solid rgba(16, 185, 129, 0.2)',
                      borderRadius: '6px'
                    }}>
                      <div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>
                          {node.node_name} <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>({node.platform || 'linux'})</span>
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace' }}>
                          {node.candidates?.[0] || 'http://' + node.node_name + ':8001'}
                        </div>
                      </div>
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={() => {
                          const targetUrl = node.candidates?.[0] || `http://${node.node_name}:8001`;
                          const newId = `srv-${Date.now()}`;
                          const newEntry = {
                            id: newId,
                            name: node.node_name,
                            url: targetUrl,
                            token: '',
                            isLocal: false,
                            status: 'online',
                            candidates: node.candidates || []
                          };
                          setConnectedServers(prev => [...prev, newEntry]);
                          setSelectedServers(prev => [...prev, newId]);
                          setSelectedLogServers(prev => [...prev, newId]);
                          addNotification(`Nodo ${node.node_name} vinculado a la malla con éxito.`, 'success');
                        }}
                        style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem', background: '#059669', borderColor: '#10b981' }}
                      >
                        + Conectar a Malla
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })()}

        {/* Formulario para agregar nuevo servidor */}
        <form onSubmit={handleAddServer} style={{ background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: '10px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#60a5fa', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Plus size={15} /> Vincular Servidor, Satélite u otro Cockpit
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
              Conecta otro Cockpit SentinelOS (Modo Híbrido/Maestro) o un nodo satélite para controlarlo en malla.
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Nombre del Servidor</label>
            <input
              type="text"
              placeholder="ej. Servidor HP ProLiant, Nodo GPU Ubuntu..."
              className="os-input"
              value={newServerForm.name}
              onChange={e => setNewServerForm(prev => ({ ...prev, name: e.target.value }))}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Dirección URL / IP y Puerto</label>
            <input
              type="text"
              placeholder="ej. http://192.168.1.150:8001 o http://labsentinel.tailc83bd7.ts.net:8001"
              className="os-input"
              value={newServerForm.url}
              onChange={e => setNewServerForm(prev => ({ ...prev, url: e.target.value }))}
              required
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Token de Autenticación / Mesh Key (Opcional)</label>
            <input
              type="password"
              placeholder="sntl_live_... (token generado por el instalador)"
              className="os-input"
              value={newServerForm.token}
              onChange={e => setNewServerForm(prev => ({ ...prev, token: e.target.value }))}
              style={{ width: '100%' }}
            />
          </div>

          {serverTestStatus && (
            <div style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '6px',
              fontSize: '0.78rem',
              background: serverTestStatus.ok ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: serverTestStatus.ok ? '#34d399' : '#f87171',
              border: serverTestStatus.ok ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)'
            }}>
              {serverTestStatus.msg}
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.25rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleTestServerConnection}
              disabled={serverTestLoading || !newServerForm.url.trim()}
              style={{ flex: 1, padding: '0.5rem' }}
            >
              {serverTestLoading ? 'Probando...' : 'Probar Conexión'}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!newServerForm.url.trim()}
              style={{ flex: 1, padding: '0.5rem' }}
            >
              Guardar y Conectar
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const renderWelcomeModal = () => (
    <div className="server-modal-backdrop" onClick={() => setShowWelcomeModal(false)}>
      <div 
        className="server-modal-box" 
        onClick={e => e.stopPropagation()} 
        style={{ 
          maxWidth: '780px', 
          border: '1px solid rgba(59, 130, 246, 0.4)', 
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(59, 130, 246, 0.15)',
          background: 'linear-gradient(145deg, #0d121f, #090c14)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'linear-gradient(135deg, #2563eb, #10b981)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 15px rgba(37, 99, 235, 0.4)' }}>
              <ShieldCheck size={22} color="#ffffff" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#f8fafc', fontWeight: 700 }}>Bienvenido a SentinelOS Cockpit</h3>
              <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>Tu Centro de Comando Unificado para Monitoreo de Servidores, Redes e Infraestructura</p>
            </div>
          </div>
          <button
            onClick={() => {
              try { localStorage.setItem('sentinel_welcome_seen_v2', 'true'); } catch (e) {}
              setShowWelcomeModal(false);
            }}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '6px' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Resumen del nodo actual */}
        <div style={{
          marginTop: '1.1rem',
          padding: '0.9rem 1.1rem',
          borderRadius: '10px',
          background: 'rgba(59, 130, 246, 0.06)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.8rem'
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#60a5fa', fontWeight: 700, letterSpacing: '0.05em' }}>
              Nodo Conectado Actualmente (Host Maestro)
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
              {data?.system?.hostname || 'Sentinel Host'} <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 400 }}>({data?.system?.os || 'Sistema Operativo'})</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>
              IP: {data?.network?.local_ip || '127.0.0.1'} | Puerto: {SERVICE_HTTP_PORT} | Firewall: Abierto
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '0.35rem 0.75rem', borderRadius: '20px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', fontWeight: 600 }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }}></span> En Línea
            </span>
          </div>
        </div>

        {/* 4 Pilares de Monitoreo */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.85rem', marginTop: '1.1rem' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '0.9rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#60a5fa', fontWeight: 600, fontSize: '0.88rem' }}>
              <Cpu size={16} /> Telemetría Hardware
            </div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.4rem', lineHeight: '1.4' }}>
              Monitoreo en tiempo real de CPU por núcleo, RAM, Discos NVMe/HDD, Sensores de Temperatura y Procesos de alto consumo.
            </div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '0.9rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontWeight: 600, fontSize: '0.88rem' }}>
              <Network size={16} /> Topología de Red LAN
            </div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.4rem', lineHeight: '1.4' }}>
              Mapeo interactivo de Gateways, Malla Tailscale, Impresoras de red, Contenedores Docker y Servidores vinculados.
            </div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '0.9rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fbbf24', fontWeight: 600, fontSize: '0.88rem' }}>
              <Terminal size={16} /> Logs Multi-Ventana
            </div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.4rem', lineHeight: '1.4' }}>
              Consolas de terminal independientes por servidor con pausa en vivo, búsqueda de texto, copia a portapapeles y pestañas.
            </div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '0.9rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a78bfa', fontWeight: 600, fontSize: '0.88rem' }}>
              <Server size={16} /> Malla Multi-Servidor
            </div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.4rem', lineHeight: '1.4' }}>
              Autodescubrimiento en la LAN vía UDP, compatibilidad cruzada Windows/Linux y acceso directo sin dependencias manuales.
            </div>
          </div>
        </div>

        {/* Acciones principales */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.4rem', paddingTop: '1rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)', flexWrap: 'wrap', gap: '0.8rem' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
            Puedes volver a ver esta guía o el recorrido en cualquier momento con el botón <strong>"Guía & Tour"</strong> en la barra superior.
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              className="btn btn-secondary"
              onClick={() => {
                try { localStorage.setItem('sentinel_welcome_seen_v2', 'true'); } catch (e) {}
                setShowWelcomeModal(false);
              }}
              style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
            >
              Entrar al Cockpit
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                try { localStorage.setItem('sentinel_welcome_seen_v2', 'true'); } catch (e) {}
                setShowWelcomeModal(false);
                setTourStep(0);
                setTourActive(true);
              }}
              style={{ fontSize: '0.85rem', padding: '0.5rem 1.2rem', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <Compass size={15} /> Iniciar Recorrido Guiado
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderUninstallModal = () => (
    <div className="server-modal-backdrop" onClick={() => !uninstallLoading && setUninstallModalOpen(false)}>
      <div className="server-modal-box" onClick={e => e.stopPropagation()} style={{ maxWidth: '520px', border: '1px solid rgba(239, 68, 68, 0.35)', boxShadow: '0 20px 40px rgba(239, 68, 68, 0.15)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <AlertTriangle size={22} color="#ef4444" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#f87171' }}>Desinstalar SentinelOS</h3>
          </div>
          <button
            onClick={() => !uninstallLoading && setUninstallModalOpen(false)}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '8px', padding: '0.85rem 1rem', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.5 }}>
            <p style={{ margin: '0 0 0.5rem', fontWeight: 600, color: '#f87171' }}>
              Atención: Esta acción desmantelará los servicios del sistema.
            </p>
            <ul style={{ margin: 0, paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <li>Detendrá los procesos en segundo plano de SentinelOS y liberará los puertos 8001 / 8080.</li>
              <li>Eliminará el inicio automático en el sistema (systemd en Linux o Programador de Tareas / Inicio en Windows).</li>
              <li>Desvinculará este nodo de la red de monitoreo.</li>
            </ul>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem', fontWeight: 600 }}>
              Equipo / Nodo a Desinstalar:
            </label>
            <select
              className="os-input"
              value={uninstallTargetServer}
              onChange={e => setUninstallTargetServer(e.target.value)}
              disabled={uninstallLoading}
              style={{ width: '100%', background: '#0f172a', color: '#f8fafc', padding: '0.6rem 0.75rem', borderRadius: '6px' }}
            >
              <option value="local">Host Local (Este equipo)</option>
              {connectedServers.filter(s => !s.isLocal).map(s => (
                <option key={s.id} value={s.id}>{s.name} ({s.url})</option>
              ))}
            </select>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.82rem', color: '#cbd5e1', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={uninstallPurgeData}
              onChange={e => setUninstallPurgeData(e.target.checked)}
              disabled={uninstallLoading}
              style={{ accentColor: '#ef4444', width: '16px', height: '16px' }}
            />
            <span>Eliminar también archivos de configuración y datos temporales locales (Vault)</span>
          </label>

          <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#e2e8f0', marginBottom: '0.4rem' }}>
              Para confirmar la desinstalación, escribe <strong style={{ color: '#ef4444', letterSpacing: '1px' }}>DESINSTALAR</strong>:
            </label>
            <input
              type="text"
              className="os-input"
              placeholder="Escribe DESINSTALAR aquí..."
              value={uninstallConfirmText}
              onChange={e => setUninstallConfirmText(e.target.value)}
              disabled={uninstallLoading}
              style={{ width: '100%', letterSpacing: '0.5px' }}
            />
          </div>

          {uninstallStatusMsg && (
            <div style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '6px',
              fontSize: '0.8rem',
              background: uninstallStatusMsg.ok ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: uninstallStatusMsg.ok ? '#34d399' : '#f87171',
              border: uninstallStatusMsg.ok ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)'
            }}>
              {uninstallStatusMsg.msg}
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setUninstallModalOpen(false)}
              disabled={uninstallLoading}
              style={{ flex: 1, padding: '0.6rem' }}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={handleUninstallSubmit}
              disabled={uninstallLoading || uninstallConfirmText.trim().toUpperCase() !== 'DESINSTALAR'}
              style={{
                flex: 1.4,
                padding: '0.6rem',
                opacity: (uninstallConfirmText.trim().toUpperCase() === 'DESINSTALAR' && !uninstallLoading) ? 1 : 0.45,
                cursor: (uninstallConfirmText.trim().toUpperCase() === 'DESINSTALAR' && !uninstallLoading) ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
            >
              <Trash2 size={16} />
              {uninstallLoading ? 'Desinstalando...' : 'Confirmar y Desinstalar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const isKlipperReady = Boolean(
    data?.moonraker?.klippy_state === 'ready' || 
    data?.printer?.print_stats ||
    Object.values(remoteServersData).some(s => s?.data?.moonraker?.klippy_state === 'ready' || s?.data?.printer?.print_stats)
  );

  const navItems = [
    { id: 'sentinel', icon: <Bot size={20} color="#00f0ff"/>, label: 'SENTINEL AI', isSentinel: true },
    { id: 'overview', icon: <LayoutDashboard size={20}/>, label: 'Dashboard' },
    { id: 'printer', icon: <Printer size={20} color={isKlipperReady ? '#f43f5e' : undefined}/>, label: '3D Printer', isLive: isKlipperReady },
    { id: 'docker', icon: <Database size={20}/>, label: 'Containers' },
    { id: 'processes', icon: <Activity size={20}/>, label: 'System & Services' },
    { id: 'network', icon: <Network size={20}/>, label: 'Network & VPN' },
    { id: 'marketplace', icon: <ShoppingBag size={20}/>, label: 'Marketplace' },
    { id: 'sandbox', icon: <Shield size={20}/>, label: 'Centro de Operaciones' },
    { id: 'files', icon: <FolderSearch size={20}/>, label: 'File Audit' },
    { id: 'logs', icon: <Terminal size={20}/>, label: 'System Logs' },
    { id: 'web-terminal', icon: <TerminalSquare size={20}/>, label: 'Web Terminal' },
  ];

  if (uninstallCompleted) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0a0f1d',
        color: '#f8fafc',
        fontFamily: 'Inter, system-ui, sans-serif',
        padding: '2rem',
        textAlign: 'center'
      }}>
        <div style={{
          maxWidth: '520px',
          background: 'rgba(15, 23, 42, 0.85)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '2.5rem',
          boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
        }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
            <CheckCircle2 size={36} color="#10b981" />
          </div>
          <h2 style={{ fontSize: '1.5rem', margin: '0 0 0.75rem', color: '#ffffff' }}>SentinelOS Desinstalado</h2>
          <p style={{ color: '#94a3b8', lineHeight: 1.6, margin: '0 0 1.25rem', fontSize: '0.92rem' }}>
            Los servicios en segundo plano fueron detenidos y el inicio automático ha sido removido exitosamente del sistema.
          </p>
          <p style={{ color: '#64748b', fontSize: '0.82rem', margin: '0 0 1.75rem' }}>
            Los puertos y recursos locales han quedado liberados. Ya puedes cerrar esta pestaña del navegador.
          </p>
          <button
            onClick={() => window.close()}
            className="btn btn-primary"
            style={{ padding: '0.65rem 1.4rem', fontSize: '0.88rem' }}
          >
            Cerrar Ventana
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="os-container">
      {/* La guía aparece en primera ejecución o cuando el instalador reinicia la bienvenida. */}
      {showWelcomeModal && renderWelcomeModal()}

      {/* Modal de Conexión y Gestión de Servidores */}
      {serverModalOpen && renderServerModal()}

      {/* Modal de Desinstalación del Sistema */}
      {uninstallModalOpen && renderUninstallModal()}

      {/* Toast Notifications */}
      <div className="toast-container">
        {notifications.map(n => (
          <div key={n.id} className={`toast ${n.type}`}>
            {n.msg}
          </div>
        ))}
      </div>

      {/* Install Modal (Confirmación) */}
      {installModalApp && (
        <div className="modal-overlay" onClick={() => setInstallModalApp(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="panel-header" style={{borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', marginBottom: '1rem'}}>
              <h2>Instalar Aplicación</h2>
            </div>
            <p>¿Estás seguro de que deseas instalar <strong>{installModalApp.name}</strong> versión <em>{installModalApp.version}</em>?</p>
            <p style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>Esta operación se ejecutará en una ventana de terminal arrastrable.</p>
            <div style={{display: 'flex', gap: '1rem', marginTop: '2rem', justifyContent: 'flex-end'}}>
              <button className="btn btn-secondary" onClick={() => setInstallModalApp(null)}>Cancelar</button>
              <button className="btn btn-primary" onClick={() => {
                setTerminalPopupApp({ app: installModalApp, minimized: false, status: 'installing' });
                setInstallModalApp(null);
              }}>Confirmar e Instalar</button>
            </div>
          </div>
        </div>
      )}

      {/* Terminal Popup (React-RND) */}
      {terminalPopupApp && (
        <Rnd
          default={{
            x: window.innerWidth / 2 - 250,
            y: window.innerHeight / 2 - 200,
            width: 500,
            height: terminalPopupApp.minimized ? 48 : 400,
          }}
          minWidth={300}
          minHeight={terminalPopupApp.minimized ? 48 : 200}
          bounds="window"
          dragHandleClassName="terminal-drag-handle"
          style={{ zIndex: 9999 }}
          enableResizing={!terminalPopupApp.minimized}
        >
          <div className="glass-panel" style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
            <div className="terminal-drag-handle" style={{ 
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
              padding: '12px 16px', background: 'rgba(0, 0, 0, 0.4)', 
              borderBottom: '1px solid rgba(255, 255, 255, 0.05)', cursor: 'move' 
            }}>
              <h3 style={{ margin: 0, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Terminal size={16}/> 
                {terminalPopupApp.status === 'completed' ? `Completado: ${terminalPopupApp.app.name}` : 
                 (terminalPopupApp.app.runMode ? `Ejecutando ${terminalPopupApp.app.name}...` : `Instalando ${terminalPopupApp.app.name}...`)}
              </h3>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <div onClick={(e) => { e.stopPropagation(); setTerminalPopupApp(p => ({...p, minimized: !p.minimized})); }} style={{cursor: 'pointer'}}>
                  {terminalPopupApp.minimized ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
                </div>
                <div onClick={(e) => { e.stopPropagation(); setTerminalPopupApp(null); }} style={{cursor: 'pointer'}}>
                  <Trash2 size={16} color="var(--danger)"/>
                </div>
              </div>
            </div>
            
            <div style={{ padding: '16px', display: terminalPopupApp.minimized ? 'none' : 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
              {(terminalPopupApp.status === 'installing' || terminalPopupApp.status === 'running') && (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <p style={{ color: 'var(--accent)', marginBottom: '0.5rem', animation: 'pulse 1s infinite', fontSize: '0.85rem' }}>
                    {terminalPopupApp.app.runMode ? "⏳ Ejecutando proceso..." : "⏳ Ejecutando en terminal (Requiere tu atención para contraseñas o Y/n)"}
                  </p>
                  <div ref={installTerminalRef} style={{ flex: 1, background: '#0f172a', borderRadius: '4px', overflow: 'hidden' }} />
                </div>
              )}

              {terminalPopupApp.status === 'completed' && (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ color: 'var(--success)', marginBottom: '1rem' }}><Package size={48}/></div>
                  <h3 style={{ margin: 0 }}>¡Proceso Terminado!</h3>
                  <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '1rem' }}>El proceso de <strong>{terminalPopupApp.app.name}</strong> ha concluido correctamente. Puedes cerrar esta ventana.</p>
                </div>
              )}
            </div>
          </div>
        </Rnd>
      )}

      <aside className={`os-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="os-brand">
          <Server color="var(--accent)" size={26}/>
          {!sidebarCollapsed && <h1>LabSentinel OS</h1>}
          <button 
            className="sidebar-collapse-btn" 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? "Expandir barra lateral" : "Minimizar barra lateral"}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
        </div>
        <nav>
          {navItems.map(item => (
            <div 
              key={item.id} 
              className={`nav-item ${item.isSentinel ? 'sentinel-nav-item' : ''} ${activeTab === item.id ? 'active' : ''}`} 
              onClick={() => {
                if (item.id === 'sentinel' && activeTab !== 'sentinel') {
                  setShowSentinelIntro(true);
                }
                setActiveTab(item.id);
              }}
              title={sidebarCollapsed ? item.label : undefined}
            >
              {item.icon}
              {!sidebarCollapsed && <span style={{fontWeight: item.isSentinel ? 700 : 500}}>{item.label}</span>}
              {!sidebarCollapsed && item.isSentinel && <span className="sentinel-nav-badge">IA</span>}
              {!sidebarCollapsed && item.isLive && (
                <span style={{ marginLeft: 'auto', background: '#f43f5e', color: '#fff', fontSize: '0.62rem', fontWeight: 700, padding: '1px 5px', borderRadius: '4px', letterSpacing: '0.04em' }}>
                  LIVE
                </span>
              )}
            </div>
          ))}
        </nav>

        <div style={{ marginTop: 'auto', padding: '0.65rem 0.75rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <button
            onClick={() => {
              setUninstallTargetServer('local');
              setUninstallConfirmText('');
              setUninstallModalOpen(true);
            }}
            title={sidebarCollapsed ? "Desinstalar SentinelOS" : undefined}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              gap: '0.65rem',
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              color: '#f87171',
              padding: '0.45rem 0.65rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.78rem',
              fontWeight: 500,
              transition: 'all 0.2s'
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.18)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.08)'}
          >
            <Trash2 size={15} color="#ef4444" />
            {!sidebarCollapsed && <span>Desinstalar SentinelOS</span>}
          </button>
        </div>
      </aside>
      <main className="os-main">
        <header className="os-topbar">
          <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
            {sidebarCollapsed && (
              <button 
                className="sidebar-expand-pill" 
                onClick={() => setSidebarCollapsed(false)}
                title="Expandir menú"
              >
                <PanelLeftOpen size={16} />
              </button>
            )}
            <h2 style={{margin: 0, fontSize: '1.1rem'}}>{navItems.find(i => i.id === activeTab)?.label}</h2>
          </div>
          <div style={{display: 'flex', gap: '0.75rem', alignItems: 'center', fontSize: '0.9rem'}}>
            <button 
              className="topbar-fullscreen-btn"
              onClick={() => {
                setTourStep(0);
                setTourActive(true);
              }}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0.35rem 0.75rem', borderRadius: '6px', background: 'rgba(59, 130, 246, 0.15)', border: '1px solid rgba(59, 130, 246, 0.3)', color: '#60a5fa', cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600 }}
              title="Iniciar recorrido guiado por el sistema"
            >
              <Compass size={15} /> Recorrido
            </button>
            <button 
              className="topbar-fullscreen-btn"
              onClick={() => {
                if (!document.fullscreenElement) {
                  document.documentElement.requestFullscreen().catch(() => {});
                  setIsGlobalFullscreen(true);
                } else {
                  document.exitFullscreen().catch(() => {});
                  setIsGlobalFullscreen(false);
                }
              }}
              title={isGlobalFullscreen ? "Salir de pantalla completa" : "Pantalla completa"}
            >
              {isGlobalFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
            {/* Indicador de Red e Internet en Tiempo Real */}
            {(() => {
              const netInfo = networkDetails || data?.network;
              const hasNet = netInfo?.internet?.has_internet ?? true;
              const latency = netInfo?.internet?.latency_ms;
              const localIp = netInfo?.local_ip || netInfo?.primary?.ip || '127.0.0.1';
              const gateway = netInfo?.gateway || '192.168.1.1';
              const tsIp = data?.tailscale?.Self?.TailscaleIPs?.[0] || 'No activa';

              return (
                <div style={{ position: 'relative' }}>
                  <div 
                    onClick={() => setShowNetQuickModal(!showNetQuickModal)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      padding: '0.3rem 0.75rem',
                      borderRadius: '20px',
                      background: hasNet ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
                      border: hasNet ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
                      cursor: 'pointer',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      color: hasNet ? '#34d399' : '#fbbf24',
                      userSelect: 'none',
                      transition: 'all 0.2s ease'
                    }}
                    title="Clic para ver detalles de red, IP y estado de Internet"
                  >
                    <span style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: hasNet ? '#10b981' : '#f59e0b',
                      boxShadow: hasNet ? '0 0 8px #10b981' : '0 0 8px #f59e0b'
                    }} />
                    <Globe size={13} />
                    <span>
                      {hasNet 
                        ? `Internet: Online (${latency ? latency + 'ms' : 'OK'})`
                        : 'Modo LAN (Sin Internet)'}
                    </span>
                  </div>

                  {/* Popover Rápido de Red */}
                  {showNetQuickModal && (
                    <div 
                      onClick={e => e.stopPropagation()}
                      style={{
                        position: 'absolute',
                        top: 'calc(100% + 8px)',
                        right: 0,
                        width: '290px',
                        background: 'rgba(15, 23, 42, 0.98)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '10px',
                        boxShadow: '0 12px 32px rgba(0,0,0,0.6)',
                        padding: '0.9rem',
                        zIndex: 9999,
                        color: '#e2e8f0',
                        cursor: 'default',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.65rem'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '0.45rem' }}>
                        <div style={{ fontWeight: 700, fontSize: '0.84rem', color: '#60a5fa', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Router size={15} /> Red & Conectividad
                        </div>
                        <button 
                          onClick={(e) => { e.stopPropagation(); setShowNetQuickModal(false); }}
                          style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '2px' }}
                        >
                          <X size={14} />
                        </button>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.78rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94a3b8' }}>Salida Internet:</span>
                          <span style={{ fontWeight: 700, color: hasNet ? '#34d399' : '#fbbf24' }}>
                            {hasNet ? `Conectado (${latency ? latency + 'ms' : 'OK'})` : 'Solo Red Local (Air-Gapped)'}
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94a3b8' }}>IP Local (LAN):</span>
                          <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#38bdf8' }}>{localIp}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94a3b8' }}>Gateway (Router):</span>
                          <span style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>{gateway}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94a3b8' }}>Tailscale VPN:</span>
                          <span style={{ fontFamily: 'monospace', color: tsIp !== 'No activa' ? '#34d399' : '#64748b' }}>{tsIp}</span>
                        </div>
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowNetQuickModal(false);
                          setActiveTab('network');
                          setNetworkSubTab('status');
                        }}
                        className="btn btn-primary"
                        style={{ width: '100%', padding: '0.45rem', fontSize: '0.76rem', marginTop: '0.2rem', justifyContent: 'center' }}
                      >
                        Ver Panel Completo de Red
                      </button>
                    </div>
                  )}
                </div>
              );
            })()}
            <div className="status-indicator status-online"></div>
            Server Connected
          </div>
        </header>
        <div className="os-content">
          {activeTab === 'sentinel' && <SentinelCockpit onExit={() => setActiveTab('overview')} />}
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'printer' && renderPrinter()}
          {activeTab === 'docker' && renderDocker()}
          {activeTab === 'processes' && renderSystemServices()}
          {activeTab === 'network' && renderNetwork()}
          {activeTab === 'marketplace' && renderMarketplace()}
          {activeTab === 'sandbox' && renderSandbox()}
          {/* Persistent Multi-Server Web Terminal View (NEVER unmounted to preserve running processes, background output, and terminal state) */}
          <div style={{
            display: activeTab === 'web-terminal' ? 'flex' : 'none',
            flex: 1,
            flexDirection: 'column',
            height: isFullscreenTerminal ? '100vh' : '85vh',
            position: isFullscreenTerminal ? 'fixed' : 'relative',
            top: isFullscreenTerminal ? 0 : 'auto',
            left: isFullscreenTerminal ? 0 : 'auto',
            right: isFullscreenTerminal ? 0 : 'auto',
            bottom: isFullscreenTerminal ? 0 : 'auto',
            zIndex: isFullscreenTerminal ? 99999 : 'auto',
            background: isFullscreenTerminal ? '#030712' : 'transparent',
            padding: isFullscreenTerminal ? '1rem' : 0
          }}>
            <div className="glass-panel" style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              padding: 0,
              overflow: 'hidden',
              borderRadius: isFullscreenTerminal ? '0' : '10px',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)'
            }}>
              {/* Barra Superior de la Terminal Multi-Servidor */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.6rem 0.9rem',
                background: 'rgba(15, 23, 42, 0.95)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                flexWrap: 'wrap',
                gap: '0.6rem'
              }}>
                {/* Controles de ventana Mac y Pestañas de Servidores */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', flex: 1 }}>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />
                    <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
                    <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
                  </div>

                  {/* Pestañas de Terminales */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                    {terminalTabs.map(tab => {
                      const isActive = tab.id === activeTerminalTabId;
                      const statusColor = tab.status === 'connected' ? '#10b981' : tab.status === 'connecting' ? '#f59e0b' : '#ef4444';
                      return (
                        <div
                          key={tab.id}
                          onClick={() => setActiveTerminalTabId(tab.id)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.45rem',
                            padding: '0.35rem 0.75rem',
                            borderRadius: '6px',
                            background: isActive ? 'rgba(59, 130, 246, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                            border: isActive ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.08)',
                            color: isActive ? '#f8fafc' : '#94a3b8',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            userSelect: 'none',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: statusColor, display: 'inline-block' }} />
                          <Server size={12} color={isActive ? '#60a5fa' : '#64748b'} />
                          <span>{tab.title}</span>
                          <span style={{
                            fontSize: '0.62rem',
                            padding: '1px 4px',
                            borderRadius: '3px',
                            background: 'rgba(0,0,0,0.3)',
                            color: '#cbd5e1'
                          }}>
                            {tab.serverId === 'local' ? 'LOCAL' : 'REMOTO'}
                          </span>
                          {terminalTabs.length > 1 && (
                            <button
                              onClick={(e) => handleCloseTerminalTab(tab.id, e)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                color: '#94a3b8',
                                cursor: 'pointer',
                                padding: '1px',
                                marginLeft: '2px',
                                display: 'flex',
                                alignItems: 'center',
                                borderRadius: '3px'
                              }}
                              title="Cerrar terminal"
                            >
                              <X size={12} />
                            </button>
                          )}
                        </div>
                      );
                    })}

                    {/* Botón para Añadir Nueva Terminal */}
                    <div style={{ position: 'relative' }}>
                      <button
                        onClick={() => setShowNewTerminalModal(!showNewTerminalModal)}
                        className="btn btn-secondary"
                        style={{ padding: '0.3rem 0.55rem', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                        title="Abrir nueva sesión de terminal"
                      >
                        <Plus size={12} />
                        <span>Nueva Terminal</span>
                        <ChevronDown size={11} />
                      </button>

                      {/* Dropdown de Selección de Servidor para Nueva Terminal */}
                      {showNewTerminalModal && (
                        <div style={{
                          position: 'absolute',
                          top: '100%',
                          left: 0,
                          marginTop: '4px',
                          background: 'rgba(15, 23, 42, 0.98)',
                          border: '1px solid rgba(255, 255, 255, 0.15)',
                          borderRadius: '8px',
                          boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                          zIndex: 1000,
                          minWidth: '220px',
                          padding: '0.4rem'
                        }}>
                          <div style={{ padding: '0.35rem 0.5rem', fontSize: '0.7rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
                            Conectar Terminal a:
                          </div>
                          {connectedServers.map(srv => (
                            <div
                              key={srv.id}
                              onClick={() => handleAddTerminalTab(srv)}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                padding: '0.45rem 0.6rem',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '0.78rem',
                                color: '#e2e8f0',
                                transition: 'background 0.15s ease'
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(59, 130, 246, 0.2)'}
                              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                            >
                              <Server size={13} color="#38bdf8" />
                              <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600 }}>{srv.name}</div>
                                <div style={{ fontSize: '0.68rem', color: '#64748b' }}>{srv.isLocal ? 'Host Maestro (Local)' : (srv.url || 'Satélite')}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Acciones de la Terminal Activa */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                  {/* Botones de zoom de fuente */}
                  <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.4)', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <button
                      onClick={() => handleChangeFontSize(-1)}
                      style={{ background: 'transparent', border: 'none', color: '#94a3b8', padding: '0.25rem 0.4rem', cursor: 'pointer', fontSize: '0.72rem' }}
                      title="Reducir fuente"
                    >
                      A-
                    </button>
                    <span style={{ fontSize: '0.68rem', color: '#64748b', padding: '0 2px' }}>
                      {terminalTabs.find(t => t.id === activeTerminalTabId)?.fontSize || 14}px
                    </span>
                    <button
                      onClick={() => handleChangeFontSize(1)}
                      style={{ background: 'transparent', border: 'none', color: '#94a3b8', padding: '0.25rem 0.4rem', cursor: 'pointer', fontSize: '0.72rem' }}
                      title="Aumentar fuente"
                    >
                      A+
                    </button>
                  </div>

                  <button
                    onClick={handleClearActiveTerminal}
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                    title="Limpiar pantalla"
                  >
                    <Trash2 size={11} />
                    <span>Limpiar</span>
                  </button>

                  <button
                    onClick={handleReconnectActiveTerminal}
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                    title="Reconectar sesión"
                  >
                    <RefreshCw size={11} color="#38bdf8" />
                    <span>Reconectar</span>
                  </button>

                  <button
                    onClick={handleRestartActiveTerminal}
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                    title="Reiniciar shell"
                  >
                    <Zap size={11} color="#f59e0b" />
                    <span>Reiniciar Shell</span>
                  </button>

                  <button
                    onClick={() => setIsFullscreenTerminal(!isFullscreenTerminal)}
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                    title={isFullscreenTerminal ? "Salir de pantalla completa" : "Pantalla completa"}
                  >
                    {isFullscreenTerminal ? <Minimize2 size={11} /> : <Maximize2 size={11} />}
                  </button>
                </div>
              </div>

              {/* Contenedores de Terminales DOM (Uno por cada pestaña, solo la activa visible) */}
              <div style={{ flex: 1, position: 'relative', background: '#070b14', overflow: 'hidden' }}>
                {terminalTabs.map(tab => (
                  <div
                    key={tab.id}
                    ref={el => { webTerminalContainerRefs.current[tab.id] = el; }}
                    style={{
                      display: tab.id === activeTerminalTabId ? 'block' : 'none',
                      width: '100%',
                      height: '100%',
                      padding: '0.65rem',
                      boxSizing: 'border-box'
                    }}
                  />
                ))}
              </div>

              {/* Pie de Terminal con Notificación de Persistencia */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.35rem 0.9rem',
                background: 'rgba(15, 23, 42, 0.85)',
                borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                fontSize: '0.7rem',
                color: '#64748b',
                fontFamily: 'monospace'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Shield size={11} color="#10b981" />
                  <span>Sesión persistente activa: Puedes navegar a otras pestañas sin perder tu trabajo o comandos en ejecución.</span>
                </div>
                <span>
                  {terminalTabs.find(t => t.id === activeTerminalTabId)?.serverName} ({terminalTabs.find(t => t.id === activeTerminalTabId)?.serverId})
                </span>
              </div>
            </div>
          </div>

          {/* Persistent Sandbox Terminals (Always rendered to avoid destroying the connection, hidden with CSS) */}
          <div style={{ display: (activeTab === 'sandbox' && sandboxTab === 'command') ? 'block' : 'none', flex: 1 }}>
            {sandboxSessions.map(session => (
              <div 
                key={session.id} 
                className="glass-panel" 
                style={{ 
                  display: session.active ? 'flex' : 'none', 
                  flexDirection: 'column', 
                  height: '600px',
                  width: '100%'
                }}
              >
                <div className="panel-header" style={{ marginBottom: '0.5rem', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Play size={18} />
                    <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{session.tool.name} Workspace</h2>
                  </div>
                  <a href={session.tool.repo} target="_blank" rel="noreferrer" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px', textDecoration: 'none' }}>
                    Ver Repo / Instrucciones ↗
                  </a>
                </div>
                <div 
                  ref={el => { sandboxContainerRefs.current[session.id] = el; }}
                  style={{ flex: 1, background: '#0f172a', borderRadius: '4px', overflow: 'hidden', padding: '0.5rem' }} 
                />
              </div>
            ))}
          </div>

          {activeTab === 'files' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
              <div className="glass-panel">
                <div className="panel-header"><FolderSearch /><h2>File Explorer</h2></div>
                <div style={{marginBottom: '1rem', display: 'flex', gap: '0.5rem'}}>
                  <button className="btn" onClick={() => {
                    const parts = fsPath.split('/').filter(Boolean);
                    parts.pop();
                    setFsPath('/' + parts.join('/'));
                  }}>Up (..)</button>
                  <input type="text" className="os-input" value={fsPath} onChange={e => setFsPath(e.target.value)} style={{flex: 1}}/>
                </div>
                <table className="os-table">
                  <thead><tr><th>Name</th><th>Type</th><th>Size (Bytes)</th></tr></thead>
                  <tbody>
                    {fsData.dirs?.map((d, i) => (
                      <tr key={'d'+i} onClick={() => setFsPath(fsPath === '/' ? '/' + d : fsPath + '/' + d)} style={{cursor:'pointer', color:'var(--accent)'}}>
                        <td style={{fontWeight:'bold'}}>📁 {d}</td><td>DIR</td><td>-</td>
                      </tr>
                    ))}
                    {fsData.files?.map((f, i) => (
                      <tr key={'f'+i}>
                        <td>📄 {f.name}</td><td>FILE</td><td style={{fontFamily:'monospace'}}>{f.size}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="glass-panel">
              <div className="panel-header"><FolderSearch /><h2>Network File Audit</h2></div>
              <p style={{color: 'var(--text-secondary)', marginBottom: '1rem'}}>Tracking SMB/Network modifications in real-time.</p>
              <table className="os-table">
                <thead><tr><th>Time</th><th>User</th><th>IP Address</th><th>Action</th><th>File</th></tr></thead>
                <tbody>
                  {auditData.length === 0 ? (
                    <tr><td colSpan="5" style={{textAlign:'center', color:'var(--text-secondary)'}}>No network file modifications detected yet.</td></tr>
                  ) : auditData.map((log, idx) => (
                    <tr key={idx}>
                      <td style={{fontSize:'0.85rem'}}>{log.timestamp}</td>
                      <td>{log.user}</td>
                      <td style={{color:'var(--accent)'}}>{log.ip}</td>
                      <td><span className="status-warning">{log.action}</span></td>
                      <td style={{wordBreak: 'break-all'}}>{log.file}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </div>
          )}
        </div>
      </main>

      {/* Sentinel Jarvis Intro Modal */}
      {showSentinelIntro && (
        <SentinelIntro onComplete={() => setShowSentinelIntro(false)} />
      )}

      {/* Sentinel Interactive Onboarding Tour Modal */}
      {tourActive && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 99999,
          maxWidth: '430px',
          width: 'calc(100vw - 48px)',
          background: 'rgba(15, 23, 42, 0.94)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(59, 130, 246, 0.4)',
          borderRadius: '12px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(59, 130, 246, 0.25)',
          padding: '1.25rem',
          color: '#f8fafc',
          animation: 'fadeIn 0.3s ease-out'
        }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div style={{ background: 'rgba(59, 130, 246, 0.15)', padding: '0.4rem', borderRadius: '8px' }}>
                {tourSteps[tourStep].icon}
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#60a5fa', fontWeight: 700 }}>
                  {tourSteps[tourStep].badge} • Paso {tourStep + 1} de {tourSteps.length}
                </span>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                  {tourSteps[tourStep].title}
                </h3>
              </div>
            </div>
            <button 
              onClick={handleSkipTour} 
              style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
              title="Cerrar recorrido"
            >
              <X size={18} />
            </button>
          </div>

          {/* Description */}
          <p style={{ fontSize: '0.88rem', lineHeight: '1.45', color: '#cbd5e1', margin: '0 0 1rem 0' }}>
            {tourSteps[tourStep].desc}
          </p>

          {/* Progress dots */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '1.1rem' }}>
            {tourSteps.map((_, i) => (
              <div 
                key={i}
                onClick={() => setTourStep(i)}
                style={{
                  height: '4px',
                  flex: i === tourStep ? 2 : 1,
                  background: i === tourStep ? '#3b82f6' : 'rgba(255, 255, 255, 0.15)',
                  borderRadius: '2px',
                  cursor: 'pointer',
                  transition: 'all 0.25s ease'
                }}
              />
            ))}
          </div>

          {/* Footer Controls */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <button
              onClick={handlePrevTour}
              disabled={tourStep === 0}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '0.45rem 0.85rem',
                borderRadius: '6px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: tourStep === 0 ? '#64748b' : '#e2e8f0',
                cursor: tourStep === 0 ? 'not-allowed' : 'pointer',
                fontSize: '0.82rem',
                fontWeight: 600
              }}
            >
              <ChevronLeft size={15} /> Atrás
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button
                onClick={handleSkipTour}
                style={{
                  padding: '0.45rem 0.85rem',
                  borderRadius: '6px',
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '0.82rem'
                }}
              >
                Omitir
              </button>
              <button
                onClick={handleNextTour}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '0.45rem 1rem',
                  borderRadius: '6px',
                  background: '#2563eb',
                  border: 'none',
                  color: '#ffffff',
                  cursor: 'pointer',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  boxShadow: '0 2px 8px rgba(37, 99, 235, 0.4)'
                }}
              >
                {tourStep === tourSteps.length - 1 ? (
                  <>Comenzar <Check size={15} /></>
                ) : (
                  <>Siguiente <ChevronRight size={15} /></>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
