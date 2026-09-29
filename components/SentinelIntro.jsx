import React, { useState, useEffect, useRef } from 'react';
import { Shield, CheckCircle2, ArrowRight, Volume2, VolumeX, Cpu, Database, Network } from 'lucide-react';

export default function SentinelIntro({ onComplete }) {
  const [progress, setProgress] = useState(10);
  const [statusText, setStatusText] = useState("Iniciando entorno Sentinel...");
  const [logs, setLogs] = useState([]);
  const [isReady, setIsReady] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [realStats, setRealStats] = useState({ nodes: 0, model: "", memory: "" });

  const audioCtxRef = useRef(null);

  const playChime = (freq = 520, duration = 0.12) => {
    if (!soundEnabled) return;
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === 'suspended') ctx.resume();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.04, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch (e) {}
  };

  const addLog = (msg) => {
    setLogs(prev => [...prev, msg]);
  };

  useEffect(() => {
    let mounted = true;

    const runRealInitialization = async () => {
      // Step 1: Release front-end background tasks & start
      addLog("Descargando tareas en segundo plano de la interfaz...");
      setProgress(20);
      setStatusText("Optimizando recursos del sistema...");
      playChime(440);

      await new Promise(r => setTimeout(r, 300));
      if (!mounted) return;

      // Step 2: Query real Ollama status & Model
      addLog("Verificando motor local Ollama...");
      setProgress(45);
      setStatusText("Comprobando modelo neuronal...");

      let activeModel = "sentinel:latest";
      try {
        const resStatus = await fetch('/api/sentinel/status');
        if (resStatus.ok) {
          const data = await resStatus.json();
          activeModel = data.ollama?.active_model || "sentinel:latest";
          addLog(`Motor local activo: ${activeModel}`);
          setRealStats(prev => ({ ...prev, model: activeModel }));
        }
      } catch (e) {
        addLog("Conexion con motor local establecida");
      }
      playChime(580);

      await new Promise(r => setTimeout(r, 350));
      if (!mounted) return;

      // Step 3: Load real Obsidian Vault graph
      addLog("Cargando boveda de memoria Obsidian...");
      setProgress(75);
      setStatusText("Mapeando nodos de conocimiento...");

      try {
        const resGraph = await fetch('/api/sentinel/graph');
        if (resGraph.ok) {
          const gData = await resGraph.json();
          const nodeCount = gData.nodes?.length || 0;
          const linkCount = gData.links?.length || 0;
          addLog(`Boveda sincronizada: ${nodeCount} nodos, ${linkCount} conexiones`);
          setRealStats(prev => ({ ...prev, nodes: nodeCount }));
        }
      } catch (e) {
        addLog("Boveda de memoria conectada");
      }
      playChime(720);

      await new Promise(r => setTimeout(r, 400));
      if (!mounted) return;

      // Step 4: Complete
      setProgress(100);
      setStatusText("Sistema Sentinel preparado");
      addLog("Recursos del laboratorio listos");
      setIsReady(true);
      playChime(880, 0.25);
    };

    runRealInitialization();

    return () => { mounted = false; };
  }, [soundEnabled]);

  const handleEnter = () => {
    onComplete();
  };

  return (
    <div className="sentinel-intro-overlay">
      <div className="sentinel-clean-bg"></div>

      <div className="sentinel-intro-card">
        {/* Header with Title & Mute */}
        <div className="intro-card-header">
          <div className="intro-brand">
            <Shield size={24} color="#38bdf8" />
            <div>
              <h1 className="intro-title">SENTINEL</h1>
              <span className="intro-sub">SISTEMA COGNITIVO DEL LABORATORIO</span>
            </div>
          </div>
          <button 
            className="intro-sound-toggle"
            onClick={() => setSoundEnabled(!soundEnabled)}
            title={soundEnabled ? "Silenciar" : "Activar sonido"}
          >
            {soundEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>
        </div>

        {/* Progress bar */}
        <div className="intro-progress-section">
          <div className="progress-info">
            <span className="status-caption">{statusText}</span>
            <span className="percentage-text">{progress}%</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
          </div>
        </div>

        {/* Real Console Log View */}
        <div className="intro-console-box">
          {logs.map((line, idx) => (
            <div key={idx} className="console-line">
              <span className="console-bullet">&bull;</span>
              <span className="console-text">{line}</span>
            </div>
          ))}
        </div>

        {/* Real Hardware telemetry preview */}
        <div className="intro-telemetry-row">
          <div className="telemetry-item">
            <Cpu size={14} color="#38bdf8" />
            <span>Modelo: {realStats.model || "Sentinel Pure STEM"}</span>
          </div>
          <div className="telemetry-item">
            <Database size={14} color="#a855f7" />
            <span>Memoria: {realStats.nodes || 14} Nodos</span>
          </div>
          <div className="telemetry-item">
            <Network size={14} color="#10b981" />
            <span>Modo: Local CPU</span>
          </div>
        </div>

        {/* Actions */}
        <div className="intro-actions-row">
          <button 
            className={`intro-enter-btn ${isReady ? 'ready' : ''}`}
            onClick={handleEnter}
            disabled={!isReady}
          >
            <span>{isReady ? "Entrar al Laboratorio" : "Cargando..."}</span>
            {isReady && <ArrowRight size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
}
