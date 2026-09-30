import React, { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { 
  Bot, Square, Send, Mic, MicOff, Volume2, VolumeX, Sparkles, Network, RefreshCw, 
  Layers, Cpu, Database, ArrowUpRight, Maximize2, Minimize2, Brain, Globe, 
  ChevronDown, ChevronRight, Server, ExternalLink, Sliders, Plus, Clock, Trash2, MessageSquare,
  Wifi, WifiOff, Download, CheckCircle2, AlertCircle, X, Terminal, Loader2
} from 'lucide-react';
import SentinelGraphView from './SentinelGraphView';

const DEFAULT_GREETING = [
  {
    role: 'assistant',
    content: 'Saludos. Sistema SENTINEL activo. Los modelos cognitivos STEM (Local 1B / 3B y Cloud Nemotron) y la bóveda Obsidian se encuentran sincronizados. Puedes consultar dudas conceptuales, fórmulas matemáticas o control del servidor.'
  }
];

const sanitizeSessions = (sessions) => {
  if (!Array.isArray(sessions)) return sessions;
  return sessions.map(s => ({
    ...s,
    messages: (s.messages || []).map(m => {
      if (m.role === 'assistant' && (
        m.content.includes('Qwen') || 
        m.content.includes('Obsidiana.') ||
        m.content.includes('Select-Object') ||
        m.content.includes('primera línea de código')
      )) {
        return { ...m, content: DEFAULT_GREETING[0].content };
      }
      return m;
    })
  }));
};

export default function SentinelCockpit({ onExit }) {
  const [subTab, setSubTab] = useState('lab'); // 'lab' | 'graph'
  
  // Historial de Chats con persistencia en localStorage
  const [chatSessions, setChatSessions] = useState(() => {
    try {
      const saved = localStorage.getItem('sentinel_chat_sessions');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return sanitizeSessions(parsed);
      }
    } catch (e) {}
    return [{
      id: 'session_default',
      title: 'Sesión Principal',
      timestamp: Date.now(),
      messages: DEFAULT_GREETING
    }];
  });

  const [activeSessionId, setActiveSessionId] = useState(() => {
    try {
      const saved = localStorage.getItem('sentinel_chat_sessions');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed[0]?.id) return parsed[0].id;
      }
    } catch (e) {}
    return 'session_default';
  });

  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('sentinel_chat_sessions');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed[0]?.messages) return parsed[0].messages;
      }
    } catch (e) {}
    return DEFAULT_GREETING;
  });

  // Guardar mensajes automáticamente en la sesión activa y en localStorage
  useEffect(() => {
    setChatSessions(prev => {
      const updated = prev.map(s => {
        if (s.id === activeSessionId) {
          let title = s.title;
          const firstUserMsg = messages.find(m => m.role === 'user');
          if (firstUserMsg && (title === 'Sesión Principal' || title === 'Nueva Sesión')) {
            title = firstUserMsg.content.slice(0, 24).trim() + (firstUserMsg.content.length > 24 ? '...' : '');
          }
          return { ...s, messages, title };
        }
        return s;
      });
      try {
        localStorage.setItem('sentinel_chat_sessions', JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  }, [messages, activeSessionId]);

  const handleNewChat = () => {
    const newId = 'session_' + Date.now();
    const newSession = {
      id: newId,
      title: 'Nueva Sesión',
      timestamp: Date.now(),
      messages: DEFAULT_GREETING
    };
    setChatSessions(prev => {
      const next = [newSession, ...prev];
      try {
        localStorage.setItem('sentinel_chat_sessions', JSON.stringify(next));
      } catch (e) {}
      return next;
    });
    setActiveSessionId(newId);
    setMessages(DEFAULT_GREETING);
  };

  const handleSelectSession = (id) => {
    if (id === activeSessionId) return;
    const sess = chatSessions.find(s => s.id === id);
    if (sess) {
      setActiveSessionId(id);
      setMessages(sess.messages || DEFAULT_GREETING);
    }
  };

  const handleDeleteSession = (id) => {
    if (chatSessions.length <= 1) return;
    setChatSessions(prev => {
      const filtered = prev.filter(s => s.id !== id);
      try {
        localStorage.setItem('sentinel_chat_sessions', JSON.stringify(filtered));
      } catch (e) {}
      if (id === activeSessionId) {
        const nextActive = filtered[0];
        setActiveSessionId(nextActive.id);
        setMessages(nextActive.messages || DEFAULT_GREETING);
      }
      return filtered;
    });
  };
  const [inputText, setInputText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [avatarState, setAvatarState] = useState('idle');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState(null);
  const [loraStats, setLoraStats] = useState({ total_examples: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);

  // New controls: Effort, Thinking, Research
  const [effort, setEffort] = useState('med'); // 'low' | 'med' | 'high'
  const [enableThinking, setEnableThinking] = useState(false);
  const [enableResearch, setEnableResearch] = useState(false);

  // Explorar Modelos & Conectividad
  const [availableModels, setAvailableModels] = useState([
    { id: 'sentinel-pure-stem-1b', name: 'Sentinel Pure STEM 1B', description: 'Local AVX2 Ultra-Rápido (~20 tok/s) - 100% Offline', type: 'local', badge: '⚡ 1B Local' },
    { id: 'sentinel-pure-stem-3b', name: 'Sentinel Pure STEM 3B', description: 'Local AVX2 Análisis Profundo - 100% Offline', type: 'local', badge: '🧠 3B Local' },
    { id: 'nvidia-nemotron', name: 'NVIDIA Nemotron 3.5 Lightning', description: 'Cloud Flagship API - Control de Servidor Agéntico', type: 'cloud', badge: '🚀 NVIDIA Cloud' }
  ]);
  const [activeModelId, setActiveModelId] = useState('sentinel-pure-stem-1b');
  const [hasInternet, setHasInternet] = useState(true);
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);
  const [isSwitchingModel, setIsSwitchingModel] = useState(false);

  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const recognitionRef = useRef(null);
  const abortControllerRef = useRef(null);
  const chatBottomRef = useRef(null);

  // IA Descargar States
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState("sentinel-agentic-1b:latest");
  const [downloadModelName, setDownloadModelName] = useState("sentinel-agentic-1b");
  const [downloadLogs, setDownloadLogs] = useState([]);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(null);
  const [downloadFinished, setDownloadFinished] = useState(false);
  const [downloadError, setDownloadError] = useState(null);
  const downloadWsRef = useRef(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollTop = logsEndRef.current.scrollHeight;
    }
  }, [downloadLogs]);

  const handleStartDownload = () => {
    if (!downloadUrl.trim() || isDownloading) return;
    setIsDownloading(true);
    setDownloadLogs(["[*] Estableciendo túnel WebSocket con Sentinel backend..."]);
    setDownloadProgress(null);
    setDownloadFinished(false);
    setDownloadError(null);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/model/download`;
    let ws;
    try {
      ws = new WebSocket(wsUrl);
      downloadWsRef.current = ws;
    } catch(err) {
      setDownloadError("No se pudo instanciar WebSocket: " + err.message);
      setIsDownloading(false);
      return;
    }

    ws.onopen = () => {
      setDownloadLogs(prev => [...prev, "[*] Conexión establecida. Transmitiendo parámetros de modelo..."]);
      ws.send(JSON.stringify({
        url: downloadUrl.trim(),
        name: downloadModelName.trim() || 'sentinel-model',
        runtime: 'docker_ollama'
      }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'log') {
          setDownloadLogs(prev => [...prev, msg.message]);
        } else if (msg.type === 'progress') {
          setDownloadProgress(msg);
        } else if (msg.type === 'success') {
          setDownloadLogs(prev => [...prev, `[ÉXITO] ${msg.message}`]);
          setDownloadFinished(true);
          setIsDownloading(false);
          fetchModelInfo();
        } else if (msg.type === 'error') {
          setDownloadError(msg.message);
          setDownloadLogs(prev => [...prev, `[ERROR] ${msg.message}`]);
          setIsDownloading(false);
        }
      } catch (e) {
        setDownloadLogs(prev => [...prev, event.data]);
      }
    };

    ws.onerror = () => {
      setDownloadError("Error de comunicación WebSocket durante la transferencia.");
      setIsDownloading(false);
    };

    ws.onclose = () => {
      setIsDownloading(false);
    };
  };

  const handleCancelDownload = () => {
    if (downloadWsRef.current) {
      try { downloadWsRef.current.close(); } catch(e){}
    }
    setIsDownloading(false);
  };

  const fetchModelInfo = async () => {
    try {
      const res = await fetch('/api/sentinel/models');
      if (res.ok) {
        const data = await res.json();
        if (data.models) setAvailableModels(data.models);
        if (data.active_model) setActiveModelId(data.active_model);
        setHasInternet(!!data.has_internet);
      }
    } catch (e) {
      console.error("Error fetching models:", e);
    }
  };

  const handleSwitchModel = async (modelId) => {
    if (modelId === activeModelId || isSwitchingModel) return;
    setIsSwitchingModel(true);
    try {
      const res = await fetch('/api/sentinel/model/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId })
      });
      if (res.ok) {
        const data = await res.json();
        setActiveModelId(data.active_model);
        setIsModelMenuOpen(false);
        checkStatus();
      } else {
        const err = await res.json();
        alert("Error al conmutar modelo: " + (err.detail || "Error desconocido"));
      }
    } catch (e) {
      alert("Error de conexión al cambiar modelo: " + e.message);
    } finally {
      setIsSwitchingModel(false);
    }
  };

  const checkStatus = async () => {
    try {
      const res = await fetch('/api/sentinel/status');
      if (res.ok) {
        const data = await res.json();
        setOllamaStatus(data);
        if (data.model_id) setActiveModelId(data.model_id);
      }
      const resLora = await fetch('/api/sentinel/lora/status');
      if (resLora.ok) {
        const loraData = await resLora.json();
        setLoraStats(loraData);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    checkStatus();
    fetchModelInfo();
    const interval = setInterval(() => {
      checkStatus();
      fetchModelInfo();
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  // Auto scroll
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  // STT
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const reco = new SpeechRecognition();
      reco.continuous = false;
      reco.interimResults = false;
      reco.lang = 'es-ES';

      reco.onstart = () => {
        setIsListening(true);
        setAvatarState('listening');
      };

      reco.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setInputText(transcript);
          handleSendMessage(transcript);
        }
      };

      reco.onerror = () => {
        setIsListening(false);
        setAvatarState('idle');
      };

      reco.onend = () => {
        setIsListening(false);
        setAvatarState('idle');
      };

      recognitionRef.current = reco;
    }
  }, []);

    const handleStopGenerating = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
    setAvatarState('idle');
  };

const toggleMic = () => {
    if (!recognitionRef.current) {
      alert("El reconocimiento de voz no esta soportado en este navegador.");
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
    } else {
      try {
        recognitionRef.current.start();
      } catch (e) {}
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  const speakText = (text) => {
    return; // Voz silenciada
    if (!voiceEnabled || !('speechSynthesis' in window)) return;

    window.speechSynthesis.cancel();

    // Strip internal thinking tags, research comments, and wikilink brackets
    const cleanSpeech = text
      .replace(/<!--RESEARCH_META:[\s\S]*?-->/g, '')
      .replace(/<pensamiento>[\s\S]*?<\/pensamiento>/g, '')
      .replace(/<pensamiento>[\s\S]*$/g, '')
      .replace(/\[\[(.*?)\]\]/g, '$1')
      .replace(/[*#`_~-]/g, '')
      .replace(/https?:\/\/\S+/g, '')
      .trim();

    if (!cleanSpeech) return;

    const utterance = new SpeechSynthesisUtterance(cleanSpeech);
    utterance.lang = 'es-ES';
    utterance.rate = 1.05;
    utterance.pitch = 0.95;

    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    const ctx = audioCtxRef.current;
    if (ctx.state === 'suspended') ctx.resume();

    if (!analyserRef.current) {
      analyserRef.current = ctx.createAnalyser();
      analyserRef.current.fftSize = 64;
    }

    utterance.onstart = () => setAvatarState('speaking');
    utterance.onend = () => setAvatarState('idle');
    utterance.onerror = () => setAvatarState('idle');

    window.speechSynthesis.speak(utterance);
  };

  const handleSendMessage = async (textToSend = null) => {
    const query = (textToSend || inputText).trim();
    if (!query || isGenerating) return;

    const userMessage = { role: 'user', content: query };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputText('');
    setIsGenerating(true);
    setAvatarState('thinking');

    const assistantMessage = { role: 'assistant', content: '' };
    setMessages([...updatedMessages, assistantMessage]);

    try {
      abortControllerRef.current = new AbortController();
      const res = await fetch('/api/sentinel/chat', {
        signal: abortControllerRef.current.signal,
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: updatedMessages
            .filter((m, idx) => !(idx === 0 && m.role === 'assistant'))
            .map(m => ({ role: m.role, content: m.content })),
          model: 'sentinel:latest',
          effort: effort,
          enable_thinking: enableThinking,
          enable_research: enableResearch
        })
      });

      if (!res.ok || !res.body) {
        throw new Error("No se pudo conectar con el motor local de Sentinel.");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullResponse = '';

      let wordQueue = [];
      let isStreamDone = false;
      const animTimer = setInterval(() => {
        if (!abortControllerRef.current) {
          clearInterval(animTimer);
          return;
        }
        if (wordQueue.length > 0) {
          const take = wordQueue.length > 6 ? 3 : (wordQueue.length > 3 ? 2 : 1);
          fullResponse += wordQueue.splice(0, take).join('');
          setMessages(prev => {
            const next = [...prev];
            next[next.length - 1] = { role: 'assistant', content: fullResponse };
            return next;
          });
        } else if (isStreamDone) {
          clearInterval(animTimer);
        }
      }, 30);

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          isStreamDone = true;
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        const parts = chunk.match(/\S+\s*|\s+/g) || [chunk];
        wordQueue.push(...parts);
      }

      while (wordQueue.length > 0 && abortControllerRef.current) {
        await new Promise(r => setTimeout(r, 20));
      }
      clearInterval(animTimer);

      speakText(fullResponse);

      // Auto-extract and learn considering ONLY the verified response (strips thinking internally)
      fetch('/api/sentinel/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_message: query,
          ai_response: fullResponse
        })
      }).then(() => checkStatus()).catch(() => {});

    } catch (err) {
      if (err.name === 'AbortError' || err.message?.includes('aborted')) {
        setAvatarState('idle');
        return;
      }
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'assistant',
          content: `Aviso: ${err.message}. Comprueba que Ollama este activo en segundo plano.`
        };
        return next;
      });
      setAvatarState('idle');
    } finally {
      setIsGenerating(false);
      setAvatarState('idle');
    }
  };

  const handleConceptSelectFromGraph = (conceptName) => {
    setSubTab('lab');
    const prompt = `Explica en detalle el concepto [[${conceptName}]] y su aplicacion en el laboratorio.`;
    setInputText(prompt);
    handleSendMessage(prompt);
  };

  return (
    <div className="sentinel-cockpit-clean">
      {/* Top Bar */}
      <header className="cockpit-clean-topbar">
        <div className="cockpit-brand-clean">
          <Bot size={22} color="#38bdf8" />
          <div className="brand-titles">
            <h2 className="brand-title-main">SENTINEL</h2>
            <span className="brand-title-sub">SISTEMA COGNITIVO DEL LABORATORIO</span>
          </div>
        </div>

        {/* View switcher */}
        <div className="cockpit-subtabs-clean">
          <button 
            className={`subtab-btn ${subTab === 'lab' ? 'active' : ''}`}
            onClick={() => setSubTab('lab')}
          >
            <Bot size={15} />
            <span>Laboratorio</span>
          </button>
          <button 
            className={`subtab-btn ${subTab === 'graph' ? 'active' : ''}`}
            onClick={() => setSubTab('graph')}
          >
            <Network size={15} />
            <span>Boveda Obsidian</span>
          </button>
        </div>

        {/* Indicators and Fullscreen */}
        <div className="cockpit-tools-row">
          {/* Explorar Modelos Dropdown */}
          <div className="model-selector-container">
            <button 
              type="button" 
              className={`model-selector-btn ${isSwitchingModel ? 'switching' : ''}`}
              onClick={() => setIsModelMenuOpen(!isModelMenuOpen)}
              title="Explorar y cambiar modelo de IA activo"
            >
              <Cpu size={14} color="#38bdf8" />
              <span className="model-selector-name">
                {isSwitchingModel ? "Cambiando motor..." : (availableModels.find(m => m.id === activeModelId)?.badge || "⚡ 1B Local")}
              </span>
              <div 
                className={`status-dot ${hasInternet ? 'online' : 'offline'}`} 
                title={hasInternet ? "Internet Conectado" : "Sin Internet en servidor"}
              ></div>
              <ChevronDown size={13} className={`chevron-icon ${isModelMenuOpen ? 'open' : ''}`} />
            </button>

            {isModelMenuOpen && (
              <div className="model-dropdown-menu">
                <div className="dropdown-header">
                  <span className="dropdown-title">EXPLORAR MODELOS</span>
                  <div className={`dropdown-net-badge ${hasInternet ? 'online' : 'offline'}`}>
                    {hasInternet ? <Wifi size={11} /> : <WifiOff size={11} />}
                    <span>{hasInternet ? "En Línea" : "Sin Internet"}</span>
                  </div>
                </div>

                <div className="model-options-list">
                  {availableModels.map((m) => {
                    const isCloud = m.type === 'cloud';
                    const isDisabled = isCloud && !hasInternet;
                    const isActive = m.id === activeModelId;

                    return (
                      <button
                        key={m.id}
                        type="button"
                        className={`model-option-card ${isActive ? 'active' : ''} ${isDisabled ? 'disabled' : ''}`}
                        disabled={isDisabled || isSwitchingModel}
                        onClick={() => handleSwitchModel(m.id)}
                      >
                        <div className="model-card-top">
                          <span className="model-card-name">{m.name}</span>
                          {isActive && <span className="active-tag">ACTIVO</span>}
                        </div>
                        <span className="model-card-desc">{m.description}</span>
                        {isDisabled && (
                          <div className="offline-notice">
                            <WifiOff size={11} />
                            <span>Requiere Internet en el servidor</span>
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
          <div className="clean-pill">
            <Database size={13} color="#a855f7" />
            <span>{ollamaStatus?.vault_notes_count || 12} Notas</span>
          </div>
          <div className="clean-pill" title="Ejemplos de auto-aprendizaje acumulados">
            <Sparkles size={13} color="#f59e0b" />
            <span>LoRA: {loraStats.total_examples || 0}</span>
          </div>
          <button 
            type="button"
            className="clean-pill"
            style={{
              background: 'rgba(59, 130, 246, 0.18)',
              border: '1px solid rgba(59, 130, 246, 0.45)',
              color: '#60a5fa',
              cursor: 'pointer',
              fontWeight: 700,
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
            onClick={() => setShowDownloadModal(true)}
            title="Descargar y cargar nuevos modelos en Docker Ollama en tiempo real"
          >
            <Download size={13} color="#60a5fa" />
            <span>IA DESCARGAR</span>
          </button>
          <button 
            className="tool-icon-btn"
            onClick={() => {
              setVoiceEnabled(!voiceEnabled);
              if (voiceEnabled) window.speechSynthesis?.cancel();
            }}
            title={voiceEnabled ? "Silenciar voz" : "Activar voz"}
          >
            {voiceEnabled ? <Volume2 size={16} color="#38bdf8"/> : <VolumeX size={16} color="#71717a"/>}
          </button>
          <button 
            className="tool-icon-btn"
            onClick={toggleFullscreen}
            title={isFullscreen ? "Salir de pantalla completa" : "Pantalla completa"}
          >
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>
      </header>

      {/* Main Body */}
      <div className="cockpit-clean-body">
        {subTab === 'graph' ? (
          <SentinelGraphView onSelectConcept={handleConceptSelectFromGraph} />
        ) : (
          <div className="lab-split-layout">
            {/* Left Column: Avatar & Prompts */}
            <div className="lab-sidebar-left">
              <div className="avatar-panel-clean">
                <div className="avatar-panel-title">
                  <span>ESTADO SINAPTICO</span>
                </div>

                <div className="synaptic-telemetry-body">
                  <div className={`synaptic-pulse-orb ${isGenerating ? 'generating' : 'idle'}`}>
                    <div className="orb-core"></div>
                    <div className="orb-ring"></div>
                  </div>
                  <div className="synaptic-status-text">
                    <span className="synaptic-state-label">
                      {isGenerating ? "Generando respuesta..." : "En espera"}
                    </span>
                    <span className="synaptic-sub-label">
                      {isGenerating ? "Motor AVX2 en ejecucion" : "Listo para responder"}
                    </span>
                  </div>
                </div>

                <div className="mic-action-box">
                  {isGenerating ? (
                    <button 
                      type="button"
                      className="clean-mic-btn generating"
                      onClick={handleStopGenerating}
                      title="Pausar o detener la respuesta actual"
                    >
                      <Square size={16} fill="currentColor" />
                      <span>Pausar / Detener Respuesta</span>
                    </button>
                  ) : (
                    <button 
                      type="button"
                      className="clean-mic-btn idle"
                      disabled
                    >
                      <Bot size={16} />
                      <span>Sentinel Listo</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Historial de Chats */}
              <div className="chat-history-clean">
                <div className="history-header-clean">
                  <div className="history-title-clean">
                    <Clock size={13} color="#38bdf8" />
                    <span>Historial de Chats</span>
                  </div>
                  <button 
                    type="button" 
                    className="new-chat-btn-clean"
                    onClick={handleNewChat}
                    title="Iniciar nueva conversación limpia"
                  >
                    <Plus size={12} />
                    <span>Nuevo</span>
                  </button>
                </div>
                <div className="history-sessions-clean">
                  {chatSessions.map((sess) => (
                    <div 
                      key={sess.id}
                      className={`session-item-clean ${activeSessionId === sess.id ? 'active' : ''}`}
                      onClick={() => handleSelectSession(sess.id)}
                    >
                      <MessageSquare size={13} className="sess-icon" />
                      <span className="sess-title" title={sess.title}>{sess.title}</span>
                      {chatSessions.length > 1 && (
                        <button 
                          type="button"
                          className="sess-del-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(sess.id);
                          }}
                          title="Eliminar conversación"
                        >
                          <Trash2 size={12} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Chat Console */}
            <div className="lab-chat-main">
              <div className="chat-scroll-viewport">
                {messages.map((msg, index) => (
                  <div key={index} className={`clean-bubble ${msg.role}`}>
                    <div className="bubble-header-clean">
                      <span className="bubble-author">
                        {msg.role === 'assistant' ? "SENTINEL" : "USUARIO"}
                      </span>
                      {msg.role === 'assistant' && index === messages.length - 1 && isGenerating && (
                        <span className="generating-badge">Generando...</span>
                      )}
                    </div>
                    <div className="bubble-body-clean">
                      <ParsedMessageBody 
                        content={msg.content} 
                        onSelectConcept={handleConceptSelectFromGraph}
                        isGenerating={isGenerating && index === messages.length - 1}
                      />
                    </div>
                  </div>
                ))}
                <div ref={chatBottomRef} />
              </div>

              {/* Controls Bar: Effort, Thinking, Research */}
              <div className="chat-options-bar">
                {/* Effort selector: Low, Med, High */}
                <div className="effort-control-group">
                  <span className="ctrl-label">Esfuerzo:</span>
                  <div className="effort-pills">
                    {[
                      { id: 'low', label: 'Bajo', tip: 'Respuestas ultrarrapidas y concisas (3-6s)' },
                      { id: 'med', label: 'Medio', tip: 'Explicacion didactica equilibrada (por defecto)' },
                      { id: 'high', label: 'Alto', tip: 'Analisis tecnico exhaustivo paso a paso' }
                    ].map(item => (
                      <button
                        key={item.id}
                        type="button"
                        className={`effort-pill-btn ${effort === item.id ? 'active' : ''}`}
                        onClick={() => setEffort(item.id)}
                        title={item.tip}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="options-separator" />

                {/* Thinking Mode Toggle */}
                <button
                  type="button"
                  className={`option-toggle-btn ${enableThinking ? 'active' : ''}`}
                  onClick={() => setEnableThinking(!enableThinking)}
                  title="Permite a la IA reflexionar y mostrar su proceso deductivo antes de la respuesta"
                >
                  <Brain size={14} />
                  <span>Pensamiento</span>
                </button>

                {/* Research Mode Toggle */}
                <button
                  type="button"
                  className={`option-toggle-btn ${enableResearch ? 'active' : ''}`}
                  onClick={() => setEnableResearch(!enableResearch)}
                  title="Permite a Sentinel investigar en la web y verificar el estado y actualizaciones del servidor"
                >
                  <Globe size={14} />
                  <span>Investigacion</span>
                </button>
              </div>

              {/* Input Bar */}
              <form 
                className="chat-bottom-input-bar" 
                onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
              >
                <input 
                  type="text"
                  placeholder={
                    enableResearch 
                      ? "Pregunta o pide investigar en la web o verificar actualizaciones..." 
                      : "Escribe una pregunta para Sentinel..."
                  }
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={isGenerating}
                  className="chat-text-input"
                />
                {isGenerating && (
                  <button 
                    type="button" 
                    className="chat-send-btn pause-active"
                    onClick={handleStopGenerating}
                    title="Pausar respuesta"
                  >
                    <Square size={16} fill="currentColor" />
                  </button>
                )}
                <button 
                  type="submit" 
                  className="chat-send-btn"
                  disabled={isGenerating || !inputText.trim()}
                  title="Enviar"
                >
                  <Send size={16} />
                </button>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* MODAL IA DESCARGAR CON WEBSOCKET Y LOGS EN TIEMPO REAL */}
      {showDownloadModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100000,
          padding: '1.5rem'
        }}>
          <div style={{
            background: 'linear-gradient(145deg, #0d1322, #080d18)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            borderRadius: '14px',
            width: '100%',
            maxWidth: '680px',
            boxShadow: '0 25px 60px rgba(0,0,0,0.8), 0 0 35px rgba(59, 130, 246, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            {/* Header */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '1rem 1.25rem',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              background: 'rgba(15, 23, 42, 0.6)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <div style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #2563eb, #38bdf8)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 12px rgba(56, 189, 248, 0.4)'
                }}>
                  <Download size={18} color="#fff" />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.05rem', color: '#f8fafc', fontWeight: 700 }}>
                    Descargador de Modelos IA & Autocarga Docker
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.72rem', color: '#94a3b8' }}>
                    Descarga en streaming vía WebSocket e inyección automática en Docker Ollama
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  if (isDownloading) handleCancelDownload();
                  setShowDownloadModal(false);
                }}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Body */}
            <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Presets Rápidos */}
              <div>
                <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                  Modelos Rápidos / Recomendados
                </label>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {[
                    { name: 'Sentinel Agentic 1B', id: 'sentinel-agentic-1b:latest', desc: 'GGUF Agéntico Optimizado' },
                    { name: 'Llama 3.2 1B Instruct', id: 'llama3.2:1b', desc: 'Rápido, 1.3 GB' },
                    { name: 'Llama 3.2 3B', id: 'llama3.2:3b', desc: 'Precisión, 2.0 GB' },
                    { name: 'Qwen 2.5 Coder 1.5B', id: 'qwen2.5-coder:1.5b', desc: 'Código & Scripts' }
                  ].map(p => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => {
                        setDownloadUrl(p.id);
                        setDownloadModelName(p.id.split(':')[0]);
                      }}
                      style={{
                        padding: '0.4rem 0.7rem',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        background: downloadUrl === p.id ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                        border: downloadUrl === p.id ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.08)',
                        color: downloadUrl === p.id ? '#60a5fa' : '#cbd5e1',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Input URL / Identificador */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                    URL Hugging Face (.gguf) o Identificador Ollama
                  </label>
                  <input
                    type="text"
                    value={downloadUrl}
                    onChange={(e) => setDownloadUrl(e.target.value)}
                    placeholder="ej. sentinel-agentic-1b:latest o https://huggingface.co/.../model.gguf"
                    disabled={isDownloading}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      background: 'rgba(15, 23, 42, 0.8)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.82rem',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                    Nombre en Docker Ollama
                  </label>
                  <input
                    type="text"
                    value={downloadModelName}
                    onChange={(e) => setDownloadModelName(e.target.value)}
                    placeholder="ej. sentinel-agentic-1b"
                    disabled={isDownloading}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      background: 'rgba(15, 23, 42, 0.8)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.82rem',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              </div>

              {/* Barra de Progreso */}
              {downloadProgress && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8' }}>
                    <span>{downloadProgress.message}</span>
                    <span style={{ color: '#38bdf8', fontWeight: 700 }}>{downloadProgress.percent}%</span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '6px',
                    background: 'rgba(255, 255, 255, 0.08)',
                    borderRadius: '3px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${downloadProgress.percent}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #2563eb, #38bdf8)',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                </div>
              )}

              {/* Consola Terminal de Logs en Tiempo Real */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Terminal size={12} /> Log de Descarga en Vivo (WebSocket)
                  </span>
                  {isDownloading && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', color: '#38bdf8' }}>
                      <Loader2 size={12} className="spin" /> Transmitiendo...
                    </span>
                  )}
                </div>
                <div 
                  ref={logsEndRef}
                  style={{
                    height: '160px',
                    overflowY: 'auto',
                    background: '#040711',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '6px',
                    padding: '0.65rem',
                    fontFamily: 'Consolas, monospace',
                    fontSize: '0.74rem',
                    color: '#94a3b8',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px',
                    userSelect: 'text'
                  }}
                >
                  {downloadLogs.length === 0 ? (
                    <div style={{ color: '#475569', fontStyle: 'italic' }}>
                      Esperando orden de descarga... Los eventos del proceso aparecerán aquí en vivo.
                    </div>
                  ) : (
                    downloadLogs.map((log, i) => {
                      const isErr = log.includes('[ERROR]') || log.includes('Error');
                      const isOk = log.includes('[ÉXITO]') || log.includes('éxito') || log.includes('success');
                      const isInfo = log.includes('[*]');
                      return (
                        <div key={i} style={{
                          color: isErr ? '#f87171' : isOk ? '#34d399' : isInfo ? '#60a5fa' : '#cbd5e1',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-all'
                        }}>
                          {log}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Mensajes de Estado Final */}
              {downloadFinished && (
                <div style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: '6px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.35)',
                  color: '#34d399',
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <CheckCircle2 size={16} />
                  <span>¡Modelo integrado correctamente en Docker Ollama! Ya puedes seleccionarlo en el menú de modelos.</span>
                </div>
              )}

              {downloadError && (
                <div style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: '6px',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  color: '#f87171',
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <AlertCircle size={16} />
                  <span>{downloadError}</span>
                </div>
              )}
            </div>

            {/* Footer Buttons */}
            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.65rem',
              padding: '0.85rem 1.25rem',
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
              background: 'rgba(15, 23, 42, 0.4)'
            }}>
              <button
                type="button"
                onClick={() => {
                  if (isDownloading) handleCancelDownload();
                  setShowDownloadModal(false);
                }}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  background: 'transparent',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#cbd5e1',
                  fontSize: '0.82rem',
                  cursor: 'pointer'
                }}
              >
                {downloadFinished ? 'Cerrar' : 'Cancelar'}
              </button>
              {!downloadFinished && (
                <button
                  type="button"
                  onClick={handleStartDownload}
                  disabled={isDownloading || !downloadUrl.trim()}
                  style={{
                    padding: '0.5rem 1.2rem',
                    borderRadius: '6px',
                    background: isDownloading ? '#1e3a8a' : 'linear-gradient(135deg, #2563eb, #1d4ed8)',
                    border: 'none',
                    color: '#ffffff',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    cursor: isDownloading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    boxShadow: '0 2px 10px rgba(37, 99, 235, 0.4)'
                  }}
                >
                  {isDownloading ? (
                    <>
                      <Loader2 size={14} className="spin" />
                      <span>Descargando...</span>
                    </>
                  ) : (
                    <>
                      <Download size={14} />
                      <span>Iniciar Descarga</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Subcomponent to parse Research Metadata, Thinking Blocks, and Wikilinks
function ParsedMessageBody({ content, onSelectConcept, isGenerating }) {
  const [isThoughtOpen, setIsThoughtOpen] = useState(true);
  const [isResearchOpen, setIsResearchOpen] = useState(false);

  if (!content) return null;

  // 1. Extract Research Metadata if present
  let researchData = null;
  let remaining = content;
  const researchMatch = remaining.match(/<!--RESEARCH_META:([\s\S]*?)-->/);
  if (researchMatch) {
    try {
      researchData = JSON.parse(researchMatch[1]);
      remaining = remaining.replace(researchMatch[0], '').trim();
    } catch (e) {
      console.error("Error parsing research metadata:", e);
    }
  }

  // 2. Extract Thinking Block if present (<pensamiento> or <think>)
  let thoughtText = null;
  let hasClosedThinking = true;
  let finalAnswer = remaining;

  let tagType = null;
  let thoughtStartIdx = remaining.indexOf('<pensamiento>');
  if (thoughtStartIdx !== -1) {
    tagType = 'pensamiento';
  } else {
    thoughtStartIdx = remaining.indexOf('<think>');
    if (thoughtStartIdx !== -1) {
      tagType = 'think';
    }
  }

  if (thoughtStartIdx !== -1 && tagType) {
    const openTagLen = tagType === 'pensamiento' ? 13 : 7;
    const closeTag = tagType === 'pensamiento' ? '</pensamiento>' : '</think>';
    const closeTagLen = tagType === 'pensamiento' ? 14 : 8;

    const thoughtEndIdx = remaining.indexOf(closeTag);
    if (thoughtEndIdx !== -1) {
      hasClosedThinking = true;
      thoughtText = remaining.substring(thoughtStartIdx + openTagLen, thoughtEndIdx).trim();
      finalAnswer = (remaining.substring(0, thoughtStartIdx) + remaining.substring(thoughtEndIdx + closeTagLen)).trim();
    } else {
      // In-flight thinking
      hasClosedThinking = false;
      thoughtText = remaining.substring(thoughtStartIdx + openTagLen).trim();
      finalAnswer = remaining.substring(0, thoughtStartIdx).trim();
    }
  }

  const handleContainerClick = (e) => {
    const wikiBtn = e.target.closest('.wikilink-badge');
    if (wikiBtn) {
      const concept = wikiBtn.getAttribute('data-concept');
      if (concept && onSelectConcept) {
        onSelectConcept(concept);
      }
      return;
    }

    const copyBtn = e.target.closest('.code-copy-btn');
    if (copyBtn) {
      const code = copyBtn.getAttribute('data-code');
      if (code) {
        navigator.clipboard.writeText(decodeURIComponent(code));
        const originalText = copyBtn.innerText;
        copyBtn.innerText = 'Copiado';
        setTimeout(() => {
          copyBtn.innerText = originalText;
        }, 2000);
      }
    }
  };

  const renderMarkdown = (rawText) => {
    if (!rawText) return '';
    try {
      let text = rawText;

      // STEP 1: Protect code blocks (```...```) and inline code (`...`)
      // from math and wikilink parsing so $bash_vars and $(cmd) are never mangled!
      const codePlaceholders = [];
      text = text.replace(/```([\s\S]*?)```/g, (match) => {
        const id = `%%%CODEBLOCK_${codePlaceholders.length}%%%`;
        codePlaceholders.push({ id, content: match });
        return id;
      });
      text = text.replace(/`([^`\n]+)`/g, (match) => {
        const id = `%%%INLINECODE_${codePlaceholders.length}%%%`;
        codePlaceholders.push({ id, content: match });
        return id;
      });

      // STEP 2: Render display/block math $$...$$ and \[...\] outside code blocks
      text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
        try {
          return katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false });
        } catch (e) {
          return match;
        }
      });
      text = text.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
        try {
          return katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false });
        } catch (e) {
          return match;
        }
      });

      // STEP 3: Render inline math $...$ and \(...\) outside code blocks
      text = text.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
        try {
          return katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false });
        } catch (e) {
          return match;
        }
      });
      text = text.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
        try {
          return katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false });
        } catch (e) {
          return match;
        }
      });

      // STEP 4: Transform [[Wikilinks]] into interactive button HTML
      text = text.replace(/\[\[(.*?)\]\]/g, (match, concept) => {
        const cleanName = concept.replace(/_/g, ' ');
        return `<button type="button" class="wikilink-badge" data-concept="${concept}" title="Ver concepto en boveda"><span class="wikilink-dot"></span><span>${cleanName}</span></button>`;
      });

      // STEP 5: Restore code placeholders
      for (let i = codePlaceholders.length - 1; i >= 0; i--) {
        text = text.replace(codePlaceholders[i].id, codePlaceholders[i].content);
      }

      // STEP 6: Parse Markdown to HTML via marked (with GFM tables and line breaks)
      marked.setOptions({ gfm: true, breaks: true });
      let html = marked.parse(text);

      // 5. Transform standard pre/code blocks into clean card with copy button
      html = html.replace(/<pre><code(?:\s+class="language-([^"]*)")?>([\s\S]*?)<\/code><\/pre>/g, (m, lang, codeContent) => {
        const language = lang || 'codigo';
        // Strip HTML entities for raw code in clipboard
        const rawCode = codeContent
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'");
        const encoded = encodeURIComponent(rawCode);
        return `
          <div class="chat-code-block-card">
            <div class="code-block-header">
              <span class="code-lang-tag">${language}</span>
              <button type="button" class="code-copy-btn" data-code="${encoded}">Copiar</button>
            </div>
            <pre class="code-block-pre"><code>${codeContent}</code></pre>
          </div>
        `;
      });

      return html;
    } catch (err) {
      console.error("Error parsing markdown:", err);
      return rawText;
    }
  };

  return (
    <div className="parsed-message-content">
      {/* Research Badge / Card if research was performed */}
      {researchData && (
        <div className="research-source-card">
          <div 
            className="research-card-header" 
            onClick={() => setIsResearchOpen(!isResearchOpen)}
          >
            <div className="research-card-title">
              {researchData.type === 'server' ? (
                <Server size={14} color="#38bdf8" />
              ) : (
                <Globe size={14} color="#10b981" />
              )}
              <span>
                {researchData.type === 'server' 
                  ? "Diagnostico de Servidor en Vivo" 
                  : `Investigacion Web (${researchData.results?.length || 0} fuentes consultadas)`}
              </span>
            </div>
            <button className="expand-toggle-btn">
              {isResearchOpen ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}
            </button>
          </div>

          {isResearchOpen && (
            <div className="research-card-body">
              {researchData.type === 'server' ? (
                <div className="server-status-summary">
                  <p className="server-snippet">{researchData.summary}</p>
                </div>
              ) : (
                <div className="web-sources-list">
                  {researchData.results?.map((item, idx) => (
                    <a 
                      key={idx} 
                      href={item.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="web-source-item"
                    >
                      <div className="source-title-row">
                        <span className="source-title">{item.title}</span>
                        <ExternalLink size={11} />
                      </div>
                      <span className="source-snippet">{item.snippet}</span>
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Thinking Mode Accordion */}
      {thoughtText !== null && (
        <div className={`thought-accordion-card ${!hasClosedThinking ? 'is-thinking' : ''}`}>
          <div 
            className="thought-card-header" 
            onClick={() => setIsThoughtOpen(!isThoughtOpen)}
          >
            <div className="thought-card-title">
              <Brain size={14} className={!hasClosedThinking ? "spin-pulse" : ""} color="#a855f7" />
              <span className="thought-header-text">
                {!hasClosedThinking ? "Proceso de Razonamiento (Pensando...)" : "Proceso de Razonamiento completado"}
              </span>
            </div>
            <button className="expand-toggle-btn">
              {isThoughtOpen ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}
            </button>
          </div>

          {isThoughtOpen && (
            <div className="thought-card-body">
              <pre className="thought-raw-text">{thoughtText}</pre>
            </div>
          )}
        </div>
      )}

      {/* Main Final Answer rendered with complete Markdown */}
      {finalAnswer && (
        <div 
          className="final-answer-markdown"
          onClick={handleContainerClick}
          dangerouslySetInnerHTML={{ __html: renderMarkdown(finalAnswer) }}
        />
      )}
    </div>
  );
}
