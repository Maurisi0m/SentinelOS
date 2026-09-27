import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Activity, Printer, Database, Network, FolderSearch, Settings, Trash2, Play, Square, RefreshCw, Cpu, HardDrive, Server, ChevronDown, ChevronUp, Power, Shield, Router, Terminal, User, Package, TerminalSquare, Zap, Gauge, ShoppingBag, PowerOff, Bot, PanelLeftClose, PanelLeftOpen, Maximize2, Minimize2, Compass, ChevronLeft, ChevronRight, Check, X, Layers } from 'lucide-react';
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
  const [activeTab, setActiveTab] = useState('overview');
  const [showSentinelIntro, setShowSentinelIntro] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isGlobalFullscreen, setIsGlobalFullscreen] = useState(false);
  const [networkSubTab, setNetworkSubTab] = useState('topology');

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
      const completed = localStorage.getItem('sentinel_onboarding_completed');
      if (!completed) {
        const timer = setTimeout(() => {
          setTourActive(true);
          setTourStep(0);
        }, 1200);
        return () => clearTimeout(timer);
      }
    } catch (e) {}
  }, []);

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
          if (res.ok) setSysLogs((await res.json()).logs || "");
        } catch(e) {}
      };
      fetchLogs();
      interval = setInterval(fetchLogs, 2000);
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

  const fetchData = async () => {
    try {
      const res = await fetch(`${API_URL}/data`);
      const rdata = await res.json();
      setData(rdata);
      if (rdata.notifications && rdata.notifications.length > 0) {
        rdata.notifications.forEach(n => addNotification(n.msg, n.type));
      }
      
      const svcRes = await fetch(`${API_URL}/services`);
      if (svcRes.ok) setServicesData((await svcRes.json()).services || []);

      const aptRes = await fetch(`${API_URL}/apt`);
      if (aptRes.ok) setAptData(await aptRes.json());

      if (activeTab === 'files') {
        const fsRes = await fetch(`${API_URL}/fs?path=${encodeURIComponent(fsPath)}`);
        if (fsRes.ok) setFsData(await fsRes.json());
      }

      if (activeTab === 'printer') {
        const histRes = await fetch(`${API_URL}/printer/history`);
        if (histRes.ok) setPrinterHistory(await histRes.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (endpoint, body) => {
    try {
      await fetch(`${API_URL}/${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      fetchData();
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    if (activeTab === 'web-terminal' && terminalRef.current) {
      if (terminalRef.current.childElementCount > 0) return;
      const term = new TerminalXTerm({
        theme: { background: '#0f172a', foreground: '#e2e8f0', cursor: '#f59e0b' },
        fontFamily: 'monospace', fontSize: 14
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(terminalRef.current);
      fitAddon.fit();

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/terminal`);
      ws.onopen = () => { ws.send(`RESIZE:${term.cols}:${term.rows}`); };
      ws.onmessage = (e) => { term.write(e.data); };
      term.onData(data => { if (ws.readyState === WebSocket.OPEN) ws.send(data); });
      
      const resizeObserver = new ResizeObserver(() => {
        fitAddon.fit();
        if (ws.readyState === WebSocket.OPEN) ws.send(`RESIZE:${term.cols}:${term.rows}`);
      });
      resizeObserver.observe(terminalRef.current);

      return () => {
        ws.close();
        resizeObserver.disconnect();
        term.dispose();
      };
    }
  }, [activeTab]);

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

  if (loading && !data) return <div style={{padding: '2rem'}}>Booting Lab Sentinel OS...</div>;
  if (!data) return <div style={{padding: '2rem'}}>System Offline. Cannot connect to backend.</div>;

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

    return (
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
          <div className="summary-widget">
            <div className="widget-icon"><Printer size={24}/></div>
            <div className="widget-info">
              <span className="widget-title">3D Printer</span>
              <span className="widget-value" style={{color: isKlipperReady ? 'var(--success)' : 'var(--danger)'}}>{klippyStatus}</span>
            </div>
          </div>
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
  );
  };

  const renderPrinter = () => {
    const isKlippyReady = data.moonraker?.klippy_state === 'ready';
    
    if (!isKlippyReady) {
      return (
        <div className="glass-panel" style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh'}}>
          <Power size={64} color="var(--text-secondary)" style={{marginBottom: '1rem'}} />
          <h2 style={{color: 'var(--text-secondary)'}}>Klipper is Offline</h2>
          <p style={{color: 'var(--text-secondary)'}}>Turn on the 3D Printer to access the dashboard.</p>
          <div className="stat-value" style={{marginTop: '1rem', color: 'var(--danger)'}}>State: {data.moonraker?.klippy_state?.toUpperCase() || 'UNKNOWN'}</div>
        </div>
      );
    }

    const stats = data.printer?.print_stats || {};
    const sd = data.printer?.virtual_sdcard || {};
    const toolhead = data.printer?.toolhead || {};
    const fan = data.printer?.fan || {};
    const gcode_move = data.printer?.gcode_move || {};
    const display_status = data.printer?.display_status || {};
    const ext = data.printer?.extruder || {};
    const bed = data.printer?.heater_bed || {};
    
    const progress = (display_status.progress || sd.progress || 0) * 100;
    const isPrinting = stats.state === 'printing';
    
    // Time formatting
    const formatTime = (sec) => {
        if (!sec) return '--';
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        return `${h}:${m.toString().padStart(2, '0')}`;
    };

    return (
      <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
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

  const renderDocker = () => (
    <div className="glass-panel">
      {dockerModal && (
        <div className="modal-overlay">
          <div className="glass-panel modal-content">
            <h2 style={{marginBottom: '1.5rem'}}>Create Container</h2>
            <input className="modal-input" placeholder="Container Name (e.g. webserver)" value={dForm.name} onChange={e=>setDForm({...dForm, name: e.target.value})} />
            <input className="modal-input" placeholder="Image (e.g. nginx:latest)" value={dForm.image} onChange={e=>setDForm({...dForm, image: e.target.value})} />
            <input className="modal-input" placeholder="Ports (e.g. 8080:80, 443:443)" value={dForm.ports} onChange={e=>setDForm({...dForm, ports: e.target.value})} />
            <input className="modal-input" placeholder="Environment Vars (e.g. MYSQL_ROOT_PASSWORD=sec, TZ=UTC)" value={dForm.env} onChange={e=>setDForm({...dForm, env: e.target.value})} />
            <select className="modal-input" value={dForm.restart} onChange={e=>setDForm({...dForm, restart: e.target.value})}>
              <option value="no">Restart: No</option>
              <option value="always">Restart: Always</option>
              <option value="unless-stopped">Restart: Unless Stopped</option>
            </select>
            <div style={{display: 'flex', gap: '1rem', marginTop: '1.5rem'}}>
              <button className="btn btn-primary" onClick={() => {
                handleAction('docker/create', dForm);
                setDockerModal(false);
                setDForm({ name: '', image: '', ports: '', env: '', restart: 'no' });
              }}>Deploy</button>
              <button className="btn" onClick={() => setDockerModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      <div className="panel-header" style={{justifyContent: 'space-between'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}><Database /><h2>Docker Engine</h2></div>
        <button className="btn btn-primary" onClick={() => setDockerModal(true)}>+ New Container</button>
      </div>
      <table className="os-table">
        <thead><tr><th>Name</th><th>Image</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>
          {data.containers.map(c => (
            <React.Fragment key={c.id}>
              <tr onClick={() => setExpandedDocker(expandedDocker === c.name ? null : c.name)} style={{cursor: 'pointer'}}>
                <td style={{fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                  {expandedDocker === c.name ? <ChevronUp size={16}/> : <ChevronDown size={16}/>} {c.name}
                </td>
                <td style={{color: 'var(--text-secondary)'}}>{c.image}</td>
                <td><span style={{color: c.status.includes('Up') ? 'var(--success)' : 'var(--danger)'}}>{c.status}</span></td>
                <td>
                  <div style={{display: 'flex', gap: '0.5rem'}} onClick={e => e.stopPropagation()}>
                    {c.status.includes('Up') ? (
                      <button className="btn" onClick={() => handleAction('docker', {container_name: c.name, action: 'stop'})}><Square size={14}/></button>
                    ) : (
                      <button className="btn" onClick={() => handleAction('docker', {container_name: c.name, action: 'start'})}><Play size={14}/></button>
                    )}
                    <button className="btn" onClick={() => handleAction('docker', {container_name: c.name, action: 'restart'})}><RefreshCw size={14}/></button>
                    <button className="btn btn-danger" onClick={() => {if(confirm("Delete container?")) handleAction('docker', {container_name: c.name, action: 'rm'})}}><Trash2 size={14}/></button>
                  </div>
                </td>
              </tr>
              {expandedDocker === c.name && (
                <tr className="expanded-row">
                  <td colSpan="4" style={{padding: '1rem', background: 'rgba(0,0,0,0.2)'}}>
                    <div className="stat-row"><span className="stat-label">ID</span><span className="stat-value">{c.id}</span></div>
                    <div className="stat-row"><span className="stat-label">Ports</span><span className="stat-value">{c.ports || 'None mapped'}</span></div>
                    <div className="stat-row"><span className="stat-label">Command</span><span className="stat-value" style={{fontFamily: 'monospace', fontSize:'0.85rem'}}>{c.command}</span></div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderSystemServices = () => {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
        <div className="glass-panel" style={{overflowY: 'auto', maxHeight: '500px', padding: '1rem'}}>
        <div className="panel-header" style={{marginBottom: '0.5rem'}}><Activity /><h2>Task Manager (btop style)</h2></div>
        <table className="os-table btop-table">
          <thead>
            <tr>
              <th style={{width: '60px'}}>PID</th>
              <th style={{width: '100px'}}>User</th>
              <th style={{width: '60px'}}>Thr</th>
              <th style={{width: '150px'}}>CPU %</th>
              <th style={{width: '150px'}}>RAM %</th>
              <th>Command</th>
              <th style={{width: '50px', textAlign: 'center'}}>Kill</th>
            </tr>
          </thead>
          <tbody>
            {data.system.processes.map(p => {
              const cpuVal = parseFloat(p.cpu) || 0;
              const memVal = parseFloat(p.mem) || 0;
              // btop colors: green < 50, yellow < 80, red > 80
              const cpuColor = cpuVal > 80 ? '#ef4444' : cpuVal > 50 ? '#f59e0b' : '#10b981';
              const memColor = memVal > 80 ? '#ef4444' : memVal > 50 ? '#f59e0b' : '#3b82f6';
              return (
                <tr key={p.pid}>
                  <td style={{color: 'var(--accent)'}}>{p.pid}</td>
                  <td style={{color: 'var(--text-secondary)'}}>{p.user}</td>
                  <td style={{color: 'var(--text-secondary)'}}>{p.threads}</td>
                  <td>
                    <div className="btop-bar-container">
                      <div className="btop-bar-fill" style={{width: `${Math.min(cpuVal, 100)}%`, background: cpuColor}}></div>
                      <div className="btop-bar-text">{p.cpu}%</div>
                    </div>
                  </td>
                  <td>
                    <div className="btop-bar-container">
                      <div className="btop-bar-fill" style={{width: `${Math.min(memVal, 100)}%`, background: memColor}}></div>
                      <div className="btop-bar-text">{p.mem}%</div>
                    </div>
                  </td>
                  <td style={{color: 'var(--text-primary)'}}>{p.name}</td>
                  <td style={{textAlign: 'center'}}>
                    <button className="btn btn-danger" style={{padding: '0.2rem 0.5rem', margin: '0 auto'}} onClick={() => {if(confirm(`Kill ${p.name}?`)) handleAction('process/kill', {pid: parseInt(p.pid)})}}><Trash2 size={12}/></button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="glass-panel" style={{overflowY: 'auto', maxHeight: '500px', padding: '1rem'}}>
        <div className="panel-header" style={{marginBottom: '0.5rem'}}><Settings /><h2>Systemd Services</h2></div>
        <table className="os-table">
          <thead><tr><th>Service</th><th>Load</th><th>Active</th><th>Sub</th><th>Action</th></tr></thead>
          <tbody>
            {servicesData?.map((s, i) => (
              <tr key={i}>
                <td style={{fontFamily: 'monospace', fontWeight: 'bold'}}>{s.name}</td>
                <td style={{color: 'var(--text-secondary)'}}>{s.load}</td>
                <td style={{color: s.active === 'active' ? 'var(--success)' : (s.active === 'failed' ? 'var(--danger)' : 'var(--text-secondary)')}}>{s.active}</td>
                <td>{s.sub}</td>
                <td>
                  <div style={{display: 'flex', gap: '0.5rem'}}>
                    {s.sub !== 'running' && <button className="btn" onClick={() => handleAction('services', {service: s.name, action: 'start'})}><Play size={14}/></button>}
                    {s.sub === 'running' && <button className="btn" onClick={() => handleAction('services', {service: s.name, action: 'stop'})}><Square size={14}/></button>}
                    <button className="btn" onClick={() => handleAction('services', {service: s.name, action: 'restart'})}><RefreshCw size={14}/></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="glass-panel" style={{padding: '1rem'}}>
        <div className="panel-header" style={{justifyContent: 'space-between', marginBottom: '0.5rem'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}><Package /><h2>APT Package Manager</h2></div>
          <button className="btn btn-primary" disabled={aptData.count === 0} onClick={() => {if(confirm("Start upgrade in background?")) handleAction('apt/upgrade', {})}}>
            Upgrade All ({aptData.count})
          </button>
        </div>
        <div style={{maxHeight: '200px', overflowY: 'auto', background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px'}}>
          {aptData.count > 0 ? (
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
              {aptData.updates.map((pkg, i) => (
                <span key={i} style={{background: 'var(--bg-secondary)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.85rem', color: 'var(--text-secondary)'}}>{pkg}</span>
              ))}
            </div>
          ) : (
            <div style={{color: 'var(--success)', textAlign: 'center', padding: '1rem'}}>System is up to date!</div>
          )}
        </div>
      </div>

      <div className="glass-panel" style={{overflowY: 'auto', maxHeight: '400px', padding: '1rem'}}>
        <div className="panel-header" style={{marginBottom: '0.5rem'}}><Activity /><h2>Cron Jobs</h2></div>
        <table className="os-table">
          <thead><tr><th>User</th><th>Job</th></tr></thead>
          <tbody>
            {data.system.cron?.map((c, i) => (
              <tr key={i}>
                <td style={{color: 'var(--accent)', fontWeight: 'bold'}}>{c.user}</td>
                <td style={{fontFamily: 'monospace', fontSize: '0.85rem'}}>{c.job}</td>
              </tr>
            ))}
            {(!data.system.cron || data.system.cron.length === 0) && (
              <tr><td colSpan="2" style={{textAlign: 'center', color: 'var(--text-secondary)'}}>No cron jobs found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
    );
  };

  const renderNetwork = () => {
    // Inject Self into Tailscale Peers if exists
    const tsPeers = data.tailscale?.Peer ? Object.values(data.tailscale.Peer) : [];
    if (data.tailscale?.Self) {
      tsPeers.unshift({ ...data.tailscale.Self, HostName: `${data.tailscale.Self.HostName} (Self)` });
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Sub-navegación de Red y Topología */}
        <div className="glass-panel" style={{ padding: '0.6rem 1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {[
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

        {/* 1. Vista de Topología Visual Interactiva (Nodos, Sondas, Señales y Recursos) */}
        {(networkSubTab === 'topology' || networkSubTab === 'all') && (
          <NetworkTopologyView data={data} handleAction={handleAction} />
        )}

        {/* 2. Gestor Tailscale VPN */}
        {(networkSubTab === 'tailscale' || networkSubTab === 'all') && (
          <div className="glass-panel">
            <div className="panel-header" style={{justifyContent: 'space-between'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}><Shield /><h2>Tailscale VPN Manager</h2></div>
              <div style={{display: 'flex', gap: '0.5rem'}}>
                <button className="btn btn-primary" onClick={() => handleAction('tailscale', {action: 'up'})}>TS Up</button>
                <button className="btn" onClick={() => handleAction('tailscale', {action: 'up', params: '--advertise-exit-node'})}>Advertise Exit Node</button>
                <button className="btn btn-danger" onClick={() => handleAction('tailscale', {action: 'down'})}>TS Down</button>
              </div>
            </div>
            <div className="stat-row" style={{marginBottom: '1rem'}}><span className="stat-label">Tailnet</span><span className="stat-value" style={{color: 'var(--accent)'}}>{data.tailscale?.CurrentTailnet?.MagicDNSSuffix || 'Disconnected'}</span></div>
            <table className="os-table">
              <thead><tr><th>Peer</th><th>OS</th><th>IP (IPv4)</th><th>Last Seen</th></tr></thead>
              <tbody>
                {tsPeers.map((peer, idx) => (
                  <tr key={idx}>
                    <td><div style={{display:'flex', alignItems:'center', gap:'0.5rem'}}><div className={`status-indicator ${peer.Online ? 'status-online' : 'status-offline'}`}></div><span style={{fontWeight: peer.HostName.includes('(Self)') ? 'bold' : 'normal'}}>{peer.HostName}</span></div></td>
                    <td>{peer.OS}</td>
                    <td>{(peer.TailscaleIPs || [])[0]}</td>
                    <td style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>{peer.LastSeen ? new Date(peer.LastSeen).toLocaleString() : 'Active'}</td>
                  </tr>
                ))}
                {tsPeers.length === 0 && <tr><td colSpan="4" style={{textAlign: 'center', color: 'var(--text-secondary)'}}>Tailscale is offline or not configured.</td></tr>}
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
    return (
      <div className="glass-panel" style={{height: '85vh', display: 'flex', flexDirection: 'column'}}>
        <div className="panel-header" style={{marginBottom: '0.5rem'}}><Terminal size={24}/><h2>System Logs (Live Stream)</h2></div>
        <div style={{
          flex: 1,
          background: 'rgba(0,0,0,0.5)',
          padding: '1rem',
          borderRadius: '8px',
          overflowY: 'auto',
          fontFamily: 'monospace',
          fontSize: '0.85rem',
          whiteSpace: 'pre-wrap',
          color: '#d1d5db',
          display: 'flex',
          flexDirection: 'column-reverse'
        }}>
          <div>
            {wsLogs.length > 0 ? wsLogs.map((line, i) => {
              let color = 'inherit';
              let fontWeight = 'normal';
              const l = line.toLowerCase();
              if (l.includes('crit') || l.includes('fatal')) { color = '#ef4444'; fontWeight = 'bold'; }
              else if (l.includes('error') || l.includes('fail')) color = '#f97316';
              else if (l.includes('warn')) color = '#eab308';
              else if (l.includes('info') || l.includes('success')) color = '#3b82f6';
              return <div key={i} style={{color, fontWeight, paddingBottom: '0.2rem', borderBottom: '1px solid rgba(255,255,255,0.05)'}}>{line}</div>;
            }) : <div style={{color:'var(--text-secondary)'}}>Listening for logs...</div>}
          </div>
        </div>
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

  const navItems = [
    { id: 'sentinel', icon: <Bot size={20} color="#00f0ff"/>, label: 'SENTINEL AI', isSentinel: true },
    { id: 'overview', icon: <LayoutDashboard size={20}/>, label: 'Dashboard' },
    { id: 'printer', icon: <Printer size={20}/>, label: '3D Printer' },
    { id: 'docker', icon: <Database size={20}/>, label: 'Containers' },
    { id: 'processes', icon: <Activity size={20}/>, label: 'System & Services' },
    { id: 'network', icon: <Network size={20}/>, label: 'Network & VPN' },
    { id: 'marketplace', icon: <ShoppingBag size={20}/>, label: 'Marketplace' },
    { id: 'sandbox', icon: <Shield size={20}/>, label: 'Centro de Operaciones' },
    { id: 'files', icon: <FolderSearch size={20}/>, label: 'File Audit' },
    { id: 'logs', icon: <Terminal size={20}/>, label: 'System Logs' },
    { id: 'web-terminal', icon: <TerminalSquare size={20}/>, label: 'Web Terminal' },
  ];

  return (
    <div className="os-container">
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
            </div>
          ))}
        </nav>
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
          {activeTab === 'logs' && renderLogs()}
          {activeTab === 'web-terminal' && (
            <div className="glass-panel" style={{height: '85vh', display: 'flex', flexDirection: 'column'}}>
              <div className="panel-header" style={{marginBottom: '0.5rem'}}><TerminalSquare size={24}/><h2>Root Terminal (Bash)</h2></div>
              <div ref={terminalRef} style={{flex: 1, padding: '0.5rem', background: '#0f172a', borderRadius: '8px', overflow: 'hidden'}} />
            </div>
          )}

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
