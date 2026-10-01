// SENTINEL Benchmark & Telemetry Control Center
document.addEventListener('DOMContentLoaded', () => {
    // Referencias al DOM
    const vramVal = document.getElementById('vram-val');
    const vramBar = document.getElementById('vram-bar');
    const vramPct = document.getElementById('vram-pct');

    const cpuVal = document.getElementById('cpu-val');
    const cpuBar = document.getElementById('cpu-bar');

    const ramVal = document.getElementById('ram-val');
    const ramBar = document.getElementById('ram-bar');
    const ramPct = document.getElementById('ram-pct');

    const promptInput = document.getElementById('prompt-input');
    const btnRunBenchmark = document.getElementById('btn-run-benchmark');
    const resultsPanel = document.getElementById('benchmark-results-panel');

    const speedTps = document.getElementById('speed-tps');
    const speedLatency = document.getElementById('speed-latency');
    const speedTokens = document.getElementById('speed-tokens');
    const speedEmoji = document.getElementById('speed-emoji');
    const obsidianTagsList = document.getElementById('obsidian-tags-list');
    const responseContent = document.getElementById('response-content');
    const btnCopyResponse = document.getElementById('btn-copy-response');

    const canvas = document.getElementById('lossCanvas');
    const ctx = canvas ? canvas.getContext('2d') : null;
    const initialLossEl = document.getElementById('initial-loss');
    const currentLossEl = document.getElementById('current-loss');
    const convergenceRateEl = document.getElementById('convergence-rate');
    const lossStepCount = document.getElementById('loss-step-count');

    // PRESETS DE PRUEBA EDUCATIVA STEM
    const PRESETS = {
        'btn-klipper': '¿Cómo configuro una macro de inicio segura (PRINT_START) en Klipper para asegurar la temperatura de cama antes de hacer el mallado de la superficie?',
        'btn-esp32': 'Escribe un código completo en C++ para ESP32 utilizando FreeRTOS que lea un sensor I2C en una tarea dedicada y publique las lecturas por MQTT con reconexión automática.',
        'btn-csv-data': '¿Cuál es el impacto empírico demostrado en el dataset del laboratorio cuando se combina la intervención de tutores de IA con Mentalidad de Crecimiento en las calificaciones de STEM?',
        'btn-react-sse': '¿Cómo implemento un Custom Hook en React (TypeScript) para consumir un flujo de telemetría de sensores en tiempo real vía Server-Sent Events (SSE)?',
        'btn-systemd': 'Crea una unidad de servicio de systemd para ejecutar un script de recolección de telemetría en Python que reinicie automáticamente ante fallos y restrinja privilegios del sistema.',
        'btn-quantum': '¿Cuál es la diferencia matemática y de precisión entre la cuantización GGUF Q4_K_M y Q8_0 en modelos de lenguaje pequeños (SLM)?',
        'btn-nonstem': 'Escribe un poema de amor sobre el atardecer en la playa y quién ganó el mundial de fútbol.'
    };

    Object.entries(PRESETS).forEach(([btnId, text]) => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', () => {
                promptInput.value = text;
                promptInput.focus();
            });
        }
    });

    // 1. POLLING DE TELEMETRÍA DE HARDWARE
    async function updateTelemetry() {
        try {
            const res = await fetch('/api/telemetry');
            if (res.ok) {
                const data = await res.json();
                // GPU VRAM
                const vram = data.gpu;
                vramVal.textContent = `${vram.vram_reserved_gb} / ${vram.vram_total_gb} GB`;
                vramBar.style.width = `${Math.min(vram.vram_percentage, 100)}%`;
                vramPct.textContent = `${vram.vram_percentage}% VRAM (${vram.vram_allocated_gb} GB asignados)`;

                // CPU
                const sys = data.system;
                cpuVal.textContent = `${sys.cpu_usage_percent}%`;
                cpuBar.style.width = `${Math.min(sys.cpu_usage_percent, 100)}%`;

                // RAM
                ramVal.textContent = `${sys.ram_used_gb} / ${sys.ram_total_gb} GB`;
                ramBar.style.width = `${Math.min(sys.ram_percentage, 100)}%`;
                ramPct.textContent = `${sys.ram_percentage}% física utilizada`;
            }
        } catch (e) {
            // Silencioso ante reintentos
        }
    }
    setInterval(updateTelemetry, 1500);
    updateTelemetry();

    // 2. POLLING Y DIBUJADO DE LA CURVA DE LOSS
    async function updateLossChart() {
        try {
            const res = await fetch('/api/training_status');
            if (!res.ok) return;
            const data = await res.json();
            const history = data.history || [];

            if (history.length > 0 && ctx) {
                const losses = history.map(h => h.loss).filter(l => l !== null && !isNaN(l));
                if (losses.length > 0) {
                    const firstLoss = losses[0];
                    const lastLoss = losses[losses.length - 1];
                    const drop = (((firstLoss - lastLoss) / firstLoss) * 100).toFixed(1);

                    initialLossEl.textContent = firstLoss.toFixed(4);
                    currentLossEl.textContent = lastLoss.toFixed(4);
                    convergenceRateEl.textContent = `-${drop}%`;
                    lossStepCount.textContent = `Paso ${history[history.length - 1].step} / ${history[history.length - 1].max_steps || '18'}`;

                    drawLossChart(losses);
                }
            }
        } catch (e) {
            console.error('Error al actualizar curva:', e);
        }
    }

    function drawLossChart(losses) {
        if (!ctx) return;
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);

        const padLeft = 40;
        const padRight = 20;
        const padTop = 20;
        const padBottom = 30;

        const graphW = w - padLeft - padRight;
        const graphH = h - padTop - padBottom;

        const minLoss = Math.min(...losses) * 0.9;
        const maxLoss = Math.max(...losses) * 1.05;

        // Ejes y Grid
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let i = 0; i <= 4; i++) {
            const y = padTop + (graphH / 4) * i;
            ctx.moveTo(padLeft, y);
            ctx.lineTo(w - padRight, y);
            
            // Labels de eje Y
            ctx.fillStyle = '#64748b';
            ctx.font = '10px JetBrains Mono';
            const val = (maxLoss - (i / 4) * (maxLoss - minLoss)).toFixed(2);
            ctx.fillText(val, 6, y + 4);
        }
        ctx.stroke();

        // Trazado de la curva con gradiente de área
        if (losses.length === 1) {
            const x = padLeft + graphW / 2;
            const y = padTop + graphH / 2;
            ctx.fillStyle = '#00f0ff';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
            return;
        }

        const pts = losses.map((loss, idx) => {
            const x = padLeft + (idx / (losses.length - 1)) * graphW;
            const y = padTop + graphH - ((loss - minLoss) / (maxLoss - minLoss)) * graphH;
            return { x, y };
        });

        // Área bajo la curva
        const areaGrad = ctx.createLinearGradient(0, padTop, 0, h - padBottom);
        areaGrad.addColorStop(0, 'rgba(0, 240, 255, 0.25)');
        areaGrad.addColorStop(1, 'rgba(0, 240, 255, 0.0)');

        ctx.fillStyle = areaGrad;
        ctx.beginPath();
        ctx.moveTo(pts[0].x, h - padBottom);
        pts.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.lineTo(pts[pts.length - 1].x, h - padBottom);
        ctx.closePath();
        ctx.fill();

        // Línea de contorno neón
        ctx.strokeStyle = '#00f0ff';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = '#00f0ff';
        ctx.shadowBlur = 8;
        ctx.beginPath();
        pts.forEach((p, idx) => {
            if (idx === 0) ctx.moveTo(p.x, p.y);
            else ctx.lineTo(p.x, p.y);
        });
        ctx.stroke();
        ctx.shadowBlur = 0; // Reset
    }

    setInterval(updateLossChart, 2000);
    updateLossChart();

    // 3. EJECUTAR BENCHMARK DE INFERENCIA
    btnRunBenchmark.addEventListener('click', async () => {
        const text = promptInput.value.trim();
        if (!text) return;

        btnRunBenchmark.disabled = true;
        btnRunBenchmark.innerHTML = `<span>Procesando inferencia...</span>`;
        resultsPanel.style.display = 'block';
        responseContent.textContent = 'Calculando tensores en GPU y muestreando tokens...';

        try {
            const res = await fetch('/api/benchmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: text, max_tokens: 384, temperature: 0.2 })
            });

            if (res.ok) {
                const data = await res.json();
                const m = data.metrics;

                speedTps.textContent = `${m.tokens_per_second} tok/s`;
                speedLatency.textContent = `${m.latency_seconds} s`;
                speedTokens.textContent = `${m.tokens_generated} tokens`;
                speedEmoji.textContent = m.emoji_compliance;
                speedEmoji.className = m.emoji_compliance.includes('PASSED') ? 'speed-val text-emerald' : 'speed-val text-rose';

                // Obsidian tags
                obsidianTagsList.innerHTML = '';
                if (m.obsidian_links_found && m.obsidian_links_found.length > 0) {
                    m.obsidian_links_found.forEach(tag => {
                        const span = document.createElement('span');
                        span.className = 'obsidian-tag';
                        span.textContent = `[[${tag}]]`;
                        obsidianTagsList.appendChild(span);
                    });
                } else {
                    obsidianTagsList.innerHTML = '<span style="color:#64748b;font-size:0.75rem;">Sin enlaces Obsidian</span>';
                }

                responseContent.textContent = data.text;
            } else {
                responseContent.textContent = `Error en el benchmark: Código ${res.status}`;
            }
        } catch (err) {
            responseContent.textContent = `Error de red al ejecutar benchmark: ${err.message}`;
        } finally {
            btnRunBenchmark.disabled = false;
            btnRunBenchmark.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                <span>Ejecutar Benchmark</span>
            `;
        }
    });

    // COPIAR RESPUESTA
    btnCopyResponse.addEventListener('click', () => {
        navigator.clipboard.writeText(responseContent.textContent);
        btnCopyResponse.textContent = 'Copiado!';
        setTimeout(() => { btnCopyResponse.textContent = 'Copiar Texto'; }, 2000);
    });
});
