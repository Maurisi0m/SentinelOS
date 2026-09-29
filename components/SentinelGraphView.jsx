import React, { useState, useEffect, useRef } from 'react';
import { Search, Plus, RefreshCw, ZoomIn, ZoomOut, Maximize2, Tag, BookOpen, X, ArrowUpRight, Sliders, Eye, EyeOff } from 'lucide-react';

export default function SentinelGraphView({ onSelectConcept }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedNode, setSelectedNode] = useState(null);
  const [newModalOpen, setNewModalOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  
  // Simulation parameters (Obsidian style)
  const [linkDistance, setLinkDistance] = useState(150);
  const [repulsionStrength, setRepulsionStrength] = useState(900);

  const [newNodeForm, setNewNodeForm] = useState({ id: '', title: '', category: 'conceptos', tags: '', content: '' });

  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const nodesRef = useRef([]);
  const linksRef = useRef([]);
  const isDraggingCanvasRef = useRef(false);
  const draggedNodeRef = useRef(null);
  const mousePosRef = useRef({ x: 0, y: 0 });
  const hoveredNodeRef = useRef(null);
  const animFrameRef = useRef(null);

  // ResizeObserver for responsive, crisp canvas rendering
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleResize = () => {
      const rect = container.getBoundingClientRect();
      const canvas = canvasRef.current;
      if (canvas && rect.width > 0 && rect.height > 0) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }
    };

    handleResize();
    const observer = new ResizeObserver(() => handleResize());
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/sentinel/graph');
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
        initSimulation(data.nodes, data.links);
      }
    } catch (e) {
      console.error("Error cargando grafo:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  const initSimulation = (rawNodes, rawLinks) => {
    const count = rawNodes.length;
    // Initial distributed radial positioning
    const nodes = rawNodes.map((n, i) => {
      const angle = (i / Math.max(1, count)) * Math.PI * 2 + (i % 2) * 0.4;
      const radius = 170 + (i % 3) * 70 + Math.random() * 40;
      return {
        ...n,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        radius: Math.max(7, Math.min(14, (n.val || 8) * 0.6 + 4))
      };
    });

    const nodeMap = new Map(nodes.map(n => [n.id.toLowerCase(), n]));

    const links = rawLinks.map(l => ({
      source: nodeMap.get(typeof l.source === 'string' ? l.source.toLowerCase() : l.source.id.toLowerCase()),
      target: nodeMap.get(typeof l.target === 'string' ? l.target.toLowerCase() : l.target.id.toLowerCase()),
      value: l.value || 1
    })).filter(l => l.source && l.target);

    // Warmup relaxation ticks for immediate natural layout
    for (let step = 0; step < 70; step++) {
      runPhysicsStep(nodes, links, linkDistance, repulsionStrength);
    }

    nodesRef.current = nodes;
    linksRef.current = links;
  };

  // Force simulation calculation
  const runPhysicsStep = (nodes, links, targetDist, repulsePower) => {
    // 1. Many-body Coulomb repulsion
    const maxRepulsionDist = 480;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let distSq = dx * dx + dy * dy;
        if (distSq === 0) {
          dx = (Math.random() - 0.5) * 2;
          dy = (Math.random() - 0.5) * 2;
          distSq = dx * dx + dy * dy;
        }
        const dist = Math.sqrt(distSq);
        if (dist < maxRepulsionDist) {
          const force = repulsePower / (distSq + 250);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx -= fx;
          a.vy -= fy;
          b.vx += fx;
          b.vy += fy;
        }
      }
    }

    // 2. Spring Links
    const springK = 0.022;
    for (let i = 0; i < links.length; i++) {
      const link = links[i];
      let dx = link.target.x - link.source.x;
      let dy = link.target.y - link.source.y;
      let dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const diff = (dist - targetDist) * springK;
      const fx = (dx / dist) * diff;
      const fy = (dy / dist) * diff;
      link.source.vx += fx;
      link.source.vy += fy;
      link.target.vx -= fx;
      link.target.vy -= fy;
    }

    // 3. Centroid dampening & center preservation
    let sumX = 0, sumY = 0;
    for (let i = 0; i < nodes.length; i++) {
      sumX += nodes[i].x;
      sumY += nodes[i].y;
    }
    const cx = sumX / (nodes.length || 1);
    const cy = sumY / (nodes.length || 1);

    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      // Gentle center anchor (prevents infinite drifting)
      n.vx -= n.x * 0.00035;
      n.vy -= n.y * 0.00035;

      // Centroid drift correction
      n.x -= cx * 0.008;
      n.y -= cy * 0.008;

      if (n !== draggedNodeRef.current) {
        n.vx *= 0.82; // damping
        n.vy *= 0.82;
        n.x += n.vx;
        n.y += n.vy;
      }
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const tick = () => {
      const nodes = nodesRef.current;
      const links = linksRef.current;
      const tf = transformRef.current;

      runPhysicsStep(nodes, links, linkDistance, repulsionStrength);

      // Render Obsidian Style Graph
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.translate(canvas.width / 2 + tf.x, canvas.height / 2 + tf.y);
      ctx.scale(tf.k, tf.k);

      // 1. Draw Links (Obsidian dark gray lines with highlight)
      links.forEach((l) => {
        const isHighlight = selectedNode && (l.source.id === selectedNode.id || l.target.id === selectedNode.id);
        ctx.strokeStyle = isHighlight ? 'rgba(168, 130, 255, 0.75)' : 'rgba(255, 255, 255, 0.09)';
        ctx.lineWidth = isHighlight ? 1.6 : 0.85;

        ctx.beginPath();
        ctx.moveTo(l.source.x, l.source.y);
        ctx.lineTo(l.target.x, l.target.y);
        ctx.stroke();
      });

      // 2. Draw Nodes
      nodes.forEach(n => {
        const isSelected = selectedNode && selectedNode.id === n.id;
        const isHovered = hoveredNodeRef.current && hoveredNodeRef.current.id === n.id;
        const isMatchSearch = searchQuery && (
          n.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          n.id.toLowerCase().includes(searchQuery.toLowerCase())
        );

        let opacity = 1.0;
        if (selectedCategory !== 'all' && n.group !== selectedCategory) opacity = 0.18;
        if (searchQuery && !isMatchSearch) opacity = 0.18;

        ctx.globalAlpha = opacity;

        // Obsidian node colors
        let nodeColor = '#a855f7'; // purple for concepts
        if (n.group === 'memoria') nodeColor = '#06b6d4'; // cyan
        if (n.group === 'laboratorio') nodeColor = '#f59e0b'; // amber
        if (n.group === 'discovered') nodeColor = '#64748b';

        // Glow on hover or selection
        if (isSelected || isHovered) {
          ctx.fillStyle = nodeColor;
          ctx.shadowColor = nodeColor;
          ctx.shadowBlur = 12;
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius + (isSelected ? 3 : 2), 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        } else {
          ctx.fillStyle = nodeColor;
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.globalAlpha = 1.0;
      });

      // 3. Draw Labels ALWAYS by default with clean Obsidian badge styling
      if (showLabels) {
        nodes.forEach(n => {
          const isSelected = selectedNode && selectedNode.id === n.id;
          const isHovered = hoveredNodeRef.current && hoveredNodeRef.current.id === n.id;
          const isMatchSearch = searchQuery && (
            n.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            n.id.toLowerCase().includes(searchQuery.toLowerCase())
          );

          let labelOpacity = 0.88;
          if (selectedCategory !== 'all' && n.group !== selectedCategory) labelOpacity = 0.15;
          if (searchQuery && !isMatchSearch) labelOpacity = 0.15;
          if (tf.k < 0.65 && !isSelected && !isHovered) labelOpacity = 0.4;

          ctx.save();
          ctx.globalAlpha = labelOpacity;
          ctx.font = `${isSelected ? '600 12px' : '500 11px'} Inter, system-ui, -apple-system, sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';

          const text = n.name;
          const textMetrics = ctx.measureText(text);
          const textWidth = textMetrics.width;
          const badgeY = n.y + n.radius + 12;

          // Subtle dark pill background so text is crystal clear over dark lines
          ctx.fillStyle = isSelected ? 'rgba(39, 39, 42, 0.92)' : 'rgba(18, 18, 22, 0.78)';
          ctx.beginPath();
          ctx.roundRect(n.x - textWidth / 2 - 5, badgeY - 7, textWidth + 10, 15, 3);
          ctx.fill();

          if (isSelected) {
            ctx.strokeStyle = '#a855f7';
            ctx.lineWidth = 1;
            ctx.stroke();
          }

          ctx.fillStyle = isSelected ? '#ffffff' : (isHovered ? '#38bdf8' : '#e4e4e7');
          ctx.fillText(text, n.x, badgeY);
          ctx.restore();
        });
      }

      ctx.restore();
      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [selectedNode, searchQuery, selectedCategory, showLabels, linkDistance, repulsionStrength]);

  const getTransformedMouse = (clientX, clientY) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const tf = transformRef.current;
    const rawX = clientX - rect.left - canvas.width / 2 - tf.x;
    const rawY = clientY - rect.top - canvas.height / 2 - tf.y;
    return { x: rawX / tf.k, y: rawY / tf.k };
  };

  const findNodeUnderMouse = (pos) => {
    const nodes = nodesRef.current;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = pos.x - n.x;
      const dy = pos.y - n.y;
      if (dx * dx + dy * dy <= (n.radius + 7) * (n.radius + 7)) {
        return n;
      }
    }
    return null;
  };

  const handleMouseDown = (e) => {
    const pos = getTransformedMouse(e.clientX, e.clientY);
    const node = findNodeUnderMouse(pos);
    if (node) {
      draggedNodeRef.current = node;
      setSelectedNode(node);
    } else {
      isDraggingCanvasRef.current = true;
      mousePosRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseMove = (e) => {
    const pos = getTransformedMouse(e.clientX, e.clientY);
    hoveredNodeRef.current = findNodeUnderMouse(pos);

    if (draggedNodeRef.current) {
      draggedNodeRef.current.x = pos.x;
      draggedNodeRef.current.y = pos.y;
      draggedNodeRef.current.vx = 0;
      draggedNodeRef.current.vy = 0;
    } else if (isDraggingCanvasRef.current) {
      const dx = e.clientX - mousePosRef.current.x;
      const dy = e.clientY - mousePosRef.current.y;
      transformRef.current.x += dx;
      transformRef.current.y += dy;
      mousePosRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseUp = () => {
    draggedNodeRef.current = null;
    isDraggingCanvasRef.current = false;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
    const newK = Math.max(0.35, Math.min(2.8, transformRef.current.k * zoomFactor));
    transformRef.current.k = newK;
  };

  const resetView = () => {
    transformRef.current = { x: 0, y: 0, k: 1 };
    setSelectedNode(null);
  };

  const handleCreateNode = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/sentinel/node', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: newNodeForm.id || newNodeForm.title.toLowerCase().replace(/\s+/g, '_'),
          title: newNodeForm.title,
          category: newNodeForm.category,
          content: newNodeForm.content,
          tags: newNodeForm.tags.split(',').map(t => t.trim()).filter(Boolean)
        })
      });
      if (res.ok) {
        setNewModalOpen(false);
        setNewNodeForm({ id: '', title: '', category: 'conceptos', tags: '', content: '' });
        fetchGraph();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="obsidian-graph-root" ref={containerRef}>
      {/* Obsidian-Style Clean Top Header */}
      <div className="obsidian-toolbar">
        <div className="obsidian-search">
          <Search size={14} color="#71717a" />
          <input
            type="text"
            placeholder="Buscar en la boveda..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button className="clear-search-btn" onClick={() => setSearchQuery('')}><X size={13}/></button>
          )}
        </div>

        {/* Categories */}
        <div className="obsidian-filters">
          {[
            { id: 'all', label: 'Todos' },
            { id: 'conceptos', label: 'Conceptos STEM' },
            { id: 'memoria', label: 'Memoria Persistente' }
          ].map(cat => (
            <button
              key={cat.id}
              className={`obsidian-filter-btn ${selectedCategory === cat.id ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat.id)}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="obsidian-controls">
          <button 
            className={`obsidian-ctrl-btn ${showLabels ? 'active' : ''}`}
            onClick={() => setShowLabels(!showLabels)} 
            title={showLabels ? "Ocultar etiquetas" : "Mostrar etiquetas"}
          >
            {showLabels ? <Eye size={15} /> : <EyeOff size={15} />}
          </button>
          <button 
            className={`obsidian-ctrl-btn ${showSettings ? 'active' : ''}`}
            onClick={() => setShowSettings(!showSettings)} 
            title="Ajustes de fuerzas Obsidian"
          >
            <Sliders size={15} />
          </button>
          <button className="obsidian-ctrl-btn" onClick={() => { transformRef.current.k = Math.min(2.8, transformRef.current.k * 1.15); }} title="Acercar">
            <ZoomIn size={15} />
          </button>
          <button className="obsidian-ctrl-btn" onClick={() => { transformRef.current.k = Math.max(0.35, transformRef.current.k * 0.85); }} title="Alejar">
            <ZoomOut size={15} />
          </button>
          <button className="obsidian-ctrl-btn" onClick={resetView} title="Centrar">
            <Maximize2 size={15} />
          </button>
          <button className="obsidian-ctrl-btn" onClick={fetchGraph} title="Recargar">
            <RefreshCw size={15} className={loading ? "spin" : ""} />
          </button>
          <button className="obsidian-new-btn" onClick={() => setNewModalOpen(true)}>
            <Plus size={15} />
            <span>Nota</span>
          </button>
        </div>
      </div>

      {/* Obsidian Graph Physics Settings Floating Box */}
      {showSettings && (
        <div className="obsidian-settings-card">
          <div className="settings-card-header">
            <span>Fuerzas del Grafo</span>
            <button onClick={() => setShowSettings(false)} className="settings-close-btn"><X size={14}/></button>
          </div>
          <div className="settings-item">
            <div className="settings-label-row">
              <span>Distancia de enlaces</span>
              <span className="settings-val">{linkDistance}px</span>
            </div>
            <input 
              type="range" 
              min="80" 
              max="260" 
              value={linkDistance} 
              onChange={(e) => setLinkDistance(Number(e.target.value))}
              className="settings-slider"
            />
          </div>
          <div className="settings-item">
            <div className="settings-label-row">
              <span>Fuerza de repulsion</span>
              <span className="settings-val">{repulsionStrength}</span>
            </div>
            <input 
              type="range" 
              min="400" 
              max="1600" 
              value={repulsionStrength} 
              onChange={(e) => setRepulsionStrength(Number(e.target.value))}
              className="settings-slider"
            />
          </div>
        </div>
      )}

      {/* Canvas Area */}
      <div className="obsidian-canvas-container" onWheel={handleWheel}>
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="obsidian-canvas"
        />

        {/* Minimalist Footnote */}
        <div className="obsidian-footer-stats">
          <span>{graphData.nodes?.length || 0} notas</span>
          <span>&bull;</span>
          <span>{graphData.links?.length || 0} conexiones</span>
        </div>
      </div>

      {/* Inspector Panel with fixed scroll */}
      {selectedNode && (
        <div className="obsidian-inspector-panel">
          <div className="inspector-top-row">
            <span className="inspector-group-tag">{selectedNode.group}</span>
            <button className="inspector-close-btn" onClick={() => setSelectedNode(null)}><X size={16}/></button>
          </div>

          <h3 className="inspector-node-title">{selectedNode.name}</h3>

          {selectedNode.tags?.length > 0 && (
            <div className="inspector-tags-row">
              {selectedNode.tags.map((t, idx) => (
                <span key={idx} className="tag-pill">#{t}</span>
              ))}
            </div>
          )}

          {/* Scrollable body */}
          <div className="inspector-body-scrollable">
            <p className="inspector-snippet-text">{selectedNode.snippet || "Sin contenido registrado."}</p>
          </div>

          <div className="inspector-bottom-actions">
            {onSelectConcept && (
              <button 
                className="inspector-ask-btn"
                onClick={() => onSelectConcept(selectedNode.name)}
              >
                <span>Consultar concepto a Sentinel</span>
                <ArrowUpRight size={14} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Clean Modal for new Note */}
      {newModalOpen && (
        <div className="modal-overlay" onClick={() => setNewModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '520px', background: '#18181b', border: '1px solid #27272a' }}>
            <div className="panel-header" style={{ borderBottom: '1px solid #27272a', paddingBottom: '0.75rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.05rem', color: '#f4f4f5' }}>Nueva Nota en Boveda Obsidian</h2>
              <button className="close-btn" onClick={() => setNewModalOpen(false)}><X size={16}/></button>
            </div>
            <form onSubmit={handleCreateNode} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginTop: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>Titulo de la Nota:</label>
                <input 
                  type="text" 
                  required
                  placeholder="Ej: Sensores Infrarrojos"
                  value={newNodeForm.title}
                  onChange={e => setNewNodeForm({...newNodeForm, title: e.target.value})}
                  className="sentinel-input"
                />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>Categoria:</label>
                  <select 
                    value={newNodeForm.category}
                    onChange={e => setNewNodeForm({...newNodeForm, category: e.target.value})}
                    className="sentinel-input"
                  >
                    <option value="conceptos">Conceptos STEM</option>
                    <option value="memoria">Memoria Persistente</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>Etiquetas:</label>
                  <input 
                    type="text" 
                    placeholder="sensores, hardware"
                    value={newNodeForm.tags}
                    onChange={e => setNewNodeForm({...newNodeForm, tags: e.target.value})}
                    className="sentinel-input"
                  />
                </div>
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>Contenido Markdown (admite enlaces [[Nota]]):</label>
                <textarea 
                  rows={6}
                  required
                  placeholder="Escribe la definicion o conceptos vinculados..."
                  value={newNodeForm.content}
                  onChange={e => setNewNodeForm({...newNodeForm, content: e.target.value})}
                  className="sentinel-input"
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button type="button" className="sentinel-btn-skip" onClick={() => setNewModalOpen(false)}>Cancelar</button>
                <button type="submit" className="sentinel-btn-primary">Guardar Nota</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
