import express, { Request, Response } from 'express';
import cors from 'cors';
import http from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --- In-Memory State for SentinelOS ---
const startTime = Date.now();
const SYSTEM_LOGS: string[] = [
  `[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [INFO] SentinelOS Kernel Telemetry initialized on Linux x86_64`,
  `[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [INFO] Hardware Topology: ${os.cpus().length || 8} vCPUs | ${((os.totalmem() || 17179869184) / 1073741824).toFixed(1)} GB RAM`,
  `[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [SUCCESS] Node.js Express & Vite runtime active on port 3000`,
  `[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [INFO] Distributed Mesh Beacon listening on port 8002`,
  `[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [INFO] AI Cognitive Engine loaded model: sentinel-pure-stem-1b.Q4_K_M.gguf`,
  `[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [INFO] Knowledge Vault Obsidian scanned: 12 active concept notes linked`,
  `[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [INFO] Network interface operational: eth0 (1000Mbps full duplex)`
];

const NOTIFICATIONS = [
  { msg: "SentinelOS v2.4 operativo. Telemetría de precisión por segundo en línea.", type: "success", ts: Date.now() / 1000 }
];

// Rolling history metrics
interface MetricPoint {
  time: string;
  cpu: number;
  ram: number;
  temp: number;
  gpu: number;
  gpu_temp: number;
  net_rx: number;
  net_tx: number;
  disk_r: number;
  disk_w: number;
  klipper_e: number;
  klipper_b: number;
}

const metricsHistory: MetricPoint[] = [];

// Seed initial 30 history points
const nowSec = Date.now();
for (let i = 29; i >= 0; i--) {
  const d = new Date(nowSec - i * 3000);
  metricsHistory.push({
    time: d.toLocaleTimeString(),
    cpu: +(15 + Math.sin(i * 0.4) * 8 + Math.random() * 5).toFixed(1),
    ram: +(42 + Math.cos(i * 0.3) * 2).toFixed(1),
    temp: +(48 + Math.sin(i * 0.2) * 4).toFixed(1),
    gpu: +(18 + Math.random() * 6).toFixed(1),
    gpu_temp: 52.0,
    net_rx: +(0.15 + Math.random() * 0.3).toFixed(2),
    net_tx: +(0.05 + Math.random() * 0.1).toFixed(2),
    disk_r: +(0.4 + Math.random() * 0.2).toFixed(2),
    disk_w: +(0.2 + Math.random() * 0.1).toFixed(2),
    klipper_e: 215.0,
    klipper_b: 60.0
  });
}

// Background metric generator
setInterval(() => {
  const d = new Date();
  const lastPoint = metricsHistory[metricsHistory.length - 1] || { cpu: 20, ram: 42, temp: 48, gpu: 20 };
  const cpu = Math.max(5, Math.min(95, +(lastPoint.cpu + (Math.random() - 0.48) * 6).toFixed(1)));
  const ram = Math.max(20, Math.min(85, +(lastPoint.ram + (Math.random() - 0.5) * 1.5).toFixed(1)));
  const temp = Math.max(38, Math.min(78, +(46 + (cpu / 100) * 18 + (Math.random() - 0.5) * 2).toFixed(1)));
  const gpu = Math.max(2, Math.min(90, +(lastPoint.gpu + (Math.random() - 0.5) * 4).toFixed(1)));

  metricsHistory.push({
    time: d.toLocaleTimeString(),
    cpu,
    ram,
    temp,
    gpu,
    gpu_temp: +(48 + (gpu / 100) * 15).toFixed(1),
    net_rx: +(0.1 + Math.random() * 0.5).toFixed(2),
    net_tx: +(0.05 + Math.random() * 0.2).toFixed(2),
    disk_r: +(0.3 + Math.random() * 0.4).toFixed(2),
    disk_w: +(0.1 + Math.random() * 0.3).toFixed(2),
    klipper_e: +(214.8 + Math.random() * 0.5).toFixed(1),
    klipper_b: +(59.9 + Math.random() * 0.3).toFixed(1)
  });

  if (metricsHistory.length > 60) {
    metricsHistory.shift();
  }
}, 3000);

// Models state
let activeModel = 'sentinel-pure-stem-1b';
const AVAILABLE_MODELS = [
  {
    id: "sentinel-pure-stem-1b",
    name: "Sentinel Pure STEM 1B",
    description: "Local AVX2 Ultra-Rápido (~20 tok/s) - 100% Offline",
    type: "local",
    file: "sentinel-pure-stem-1b.Q4_K_M.gguf",
    badge: "⚡ 1B Local"
  },
  {
    id: "sentinel-pure-stem-3b",
    name: "Sentinel Pure STEM 3B",
    description: "Local AVX2 Análisis Profundo y Rigor STEM - 100% Offline",
    type: "local",
    file: "sentinel-pure-stem.Q4_K_M.gguf",
    badge: "🧠 3B Local"
  },
  {
    id: "nvidia-nemotron",
    name: "NVIDIA Nemotron 3.5 Lightning",
    description: "Cloud Flagship API - Control de Servidor Agéntico y Razonamiento",
    type: "cloud",
    badge: "🚀 NVIDIA Cloud"
  }
];

// Obsidian Knowledge Graph Notes
interface VaultNote {
  id: string;
  title: string;
  category: string;
  tags: string[];
  links: string[];
  content: string;
  body: string;
  size: number;
  modified: number;
}

const VAULT_NOTES: Map<string, VaultNote> = new Map([
  [
    'ley_de_ohm',
    {
      id: 'ley_de_ohm',
      title: 'Ley de Ohm y Circuitos Eléctricos',
      category: 'conceptos',
      tags: ['fisica', 'electronica', 'circuitos'],
      links: ['potencia_electrica', 'pwm_modulacion', 'sensores_adc'],
      content: '# Ley de Ohm\n\nEstablece la relación directa entre la diferencia de potencial ($V$), la intensidad de corriente ($I$) y la resistencia eléctrica ($R$):\n\n$$V = I \\cdot R$$\n\nVinculado a [[potencia_electrica]] y [[pwm_modulacion]].',
      body: 'Establece la relación directa entre la diferencia de potencial ($V$), la intensidad de corriente ($I$) y la resistencia eléctrica ($R$):\n\n$$V = I \\cdot R$$',
      size: 340,
      modified: Date.now() - 3600000
    }
  ],
  [
    'potencia_electrica',
    {
      id: 'potencia_electrica',
      title: 'Potencia Eléctrica y Efecto Joule',
      category: 'conceptos',
      tags: ['fisica', 'energia'],
      links: ['ley_de_ohm', 'cama_caliente_klipper'],
      content: '# Potencia Eléctrica\n\n$$P = V \\cdot I = I^2 \\cdot R = \\frac{V^2}{R}$$\n\nExplica la disipación térmica en resistores y la calefacción de la [[cama_caliente_klipper]].',
      body: 'La potencia eléctrica consumida se disipa según la ley de Joule.',
      size: 280,
      modified: Date.now() - 3200000
    }
  ],
  [
    'pwm_modulacion',
    {
      id: 'pwm_modulacion',
      title: 'Modulación por Ancho de Pulsos (PWM)',
      category: 'conceptos',
      tags: ['hardware', 'control', 'microcontroladores'],
      links: ['ley_de_ohm', 'pid_controller', 'esp32_freertos'],
      content: '# PWM (Pulse Width Modulation)\n\nTécnica para regular la potencia entregada a una carga eléctrica variando el ciclo de trabajo ($D = \\frac{T_{on}}{T}$). Utilizado en ventiladores de capa y control [[pid_controller]].',
      body: 'Técnica para regular la potencia promedio entregada a actuadores mediante pulsos de ciclo de trabajo variable.',
      size: 360,
      modified: Date.now() - 2800000
    }
  ],
  [
    'pid_controller',
    {
      id: 'pid_controller',
      title: 'Controlador PID (Proporcional Integral Derivativo)',
      category: 'conceptos',
      tags: ['automatizacion', 'control', 'algoritmos'],
      links: ['pwm_modulacion', 'cama_caliente_klipper', 'cinematica_corexy'],
      content: '# Algoritmo PID\n\n$$u(t) = K_p e(t) + K_i \\int_0^t e(\\tau) d\\tau + K_d \\frac{de(t)}{dt}$$\n\nMantiene estable la temperatura del fusor de la impresora y los servomotores.',
      body: 'Bucle de realimentación que calcula el error continuo y aplica corrección proporcional, integral y derivativa.',
      size: 420,
      modified: Date.now() - 2500000
    }
  ],
  [
    'cama_caliente_klipper',
    {
      id: 'cama_caliente_klipper',
      title: 'Gestión Térmica y Firmware Klipper',
      category: 'laboratorio',
      tags: ['3d_printing', 'klipper', 'hardware'],
      links: ['potencia_electrica', 'pid_controller', 'cinematica_corexy'],
      content: '# Klipper Bed Mesh & Heaters\n\nEl microcontrolador ejecuta pasos a nivel de hardware mientras el host Linux calcula la cinemática y la interpolación polinómica de la cama.',
      body: 'Arquitectura distribuida donde un microprocesador host resuelve la cinemática y envía comandos temporizados por microcontroladores.',
      size: 390,
      modified: Date.now() - 2000000
    }
  ],
  [
    'cinematica_corexy',
    {
      id: 'cinematica_corexy',
      title: 'Cinemática Inversa CoreXY y Motores Paso a Paso',
      category: 'laboratorio',
      tags: ['robotica', 'mecanica', 'klipper'],
      links: ['cama_caliente_klipper', 'pid_controller'],
      content: '# Cinemática CoreXY\n\n$$\\Delta X = \\frac{1}{2}(\\Delta A + \\Delta B), \\quad \\Delta Y = \\frac{1}{2}(\\Delta A - \\Delta B)$$\n\nReduce la inercia del cabezal al fijar ambos motores en el chasis del laboratorio.',
      body: 'Sistema de correas desacopladas que transforma coordenadas cartesianas en rotaciones sincronizadas de motores A y B.',
      size: 410,
      modified: Date.now() - 1800000
    }
  ],
  [
    'esp32_freertos',
    {
      id: 'esp32_freertos',
      title: 'Microcontrolador ESP32 y FreeRTOS',
      category: 'conceptos',
      tags: ['iot', 'embedded', 'sistemas_operativos'],
      links: ['pwm_modulacion', 'protocolo_mqtt', 'sockets_red'],
      content: '# ESP32 & FreeRTOS\n\nMicrocontrolador dual-core Xtensa a 240MHz con Wi-Fi, BLE y sistema operativo en tiempo real para adquisición paralela de telemetría por [[protocolo_mqtt]].',
      body: 'Plataforma IoT de bajo consumo con tareas concurrentes gestionadas por colas y semáforos de FreeRTOS.',
      size: 450,
      modified: Date.now() - 1500000
    }
  ],
  [
    'protocolo_mqtt',
    {
      id: 'protocolo_mqtt',
      title: 'Protocolo de Telemetría MQTT y Broker Mosquitto',
      category: 'conceptos',
      tags: ['redes', 'iot', 'protocolos'],
      links: ['esp32_freertos', 'sockets_red', 'cifrado_tailscale'],
      content: '# MQTT (Message Queuing Telemetry Transport)\n\nProtocolo ligero basado en arquitectura Publicador/Suscriptor sobre TCP/IP con tres niveles de calidad de servicio (QoS 0, 1, 2).',
      body: 'Protocolo optimizado para redes de bajo ancho de banda y dispositivos de alta latencia o conexiones inestables.',
      size: 380,
      modified: Date.now() - 1200000
    }
  ],
  [
    'sockets_red',
    {
      id: 'sockets_red',
      title: 'Descriptores de Red y Sockets BSD en POSIX',
      category: 'memoria',
      tags: ['redes', 'linux', 'c'],
      links: ['protocolo_mqtt', 'cifrado_tailscale', 'cuantizacion_gguf'],
      content: '# Sockets POSIX\n\nAbstracción de archivo descriptor para comunicación bidireccional (`socket()`, `bind()`, `listen()`, `accept()`). Base de la malla Sentinel.',
      body: 'Interfaz estándar de comunicación entre procesos tanto a través de la red local como mediante sockets de dominio Unix.',
      size: 350,
      modified: Date.now() - 900000
    }
  ],
  [
    'cifrado_tailscale',
    {
      id: 'cifrado_tailscale',
      title: 'Red Zero-Trust y WireGuard (Tailscale)',
      category: 'memoria',
      tags: ['ciberseguridad', 'vpn', 'redes'],
      links: ['sockets_red', 'protocolo_mqtt'],
      content: '# Tailscale & WireGuard\n\nCifrado moderno con clave pública Curve25519 y negociación NAT traversal DERP sin requerir apertura de puertos en el enrutador del colegio o laboratorio.',
      body: 'Red mallada segura donde cada nodo posee una identidad criptográfica única y una IP virtual fija 100.x.y.z.',
      size: 390,
      modified: Date.now() - 600000
    }
  ],
  [
    'cuantizacion_gguf',
    {
      id: 'cuantizacion_gguf',
      title: 'Cuantización de Redes Neuronales (GGUF Q4_K_M)',
      category: 'conceptos',
      tags: ['ia', 'optimizacion', 'slm'],
      links: ['sockets_red', 'esp32_freertos'],
      content: '# Cuantización GGUF Q4_K_M\n\nReduce los pesos de 16-bit punto flotante (FP16) a 4-bit enteros con escalas por bloque K-quant, permitiendo ejecutar modelos de 1B y 3B en CPUs modestas sin degradación severa de perplejidad.',
      body: 'Técnica de compresión que permite empaquetar tensores en formatos compactos compatibles con aceleración vectorial SIMD AVX2.',
      size: 470,
      modified: Date.now() - 300000
    }
  ]
]);

// Helper for dynamic system data
function getDynamicSystemData() {
  const totalMem = 16 * 1024 * 1024 * 1024;
  const lastMetrics = metricsHistory[metricsHistory.length - 1] || { cpu: 18, ram: 42, temp: 48, gpu: 20, gpu_temp: 52 };
  const usedMem = Math.round(totalMem * (lastMetrics.ram / 100));
  const freeMem = totalMem - usedMem;
  const availMem = Math.round(freeMem * 0.9);

  return {
    printer: {
      print_stats: {
        state: "standby",
        total_duration: 1820,
        filament_used: 142.5,
        filename: "calibration_cube_v3.gcode"
      },
      toolhead: {
        position: [110, 110, 25, 0],
        status: "Ready",
        homed_axes: "xyz"
      },
      extruder: {
        temperature: +(214.8 + Math.random() * 0.4).toFixed(1),
        target: 215.0,
        power: 0.38
      },
      heater_bed: {
        temperature: +(59.9 + Math.random() * 0.2).toFixed(1),
        target: 60.0,
        power: 0.25
      },
      fan: { speed: 0.85 }
    },
    moonraker: {
      moonraker_version: "v0.8.0-34",
      api_version: [1, 2, 0]
    },
    gcode_store: [
      { message: "M104 S215 ; Target extrusor STEM", time: Date.now() / 1000 - 180, type: "command" },
      { message: "M140 S60 ; Target cama caliente", time: Date.now() / 1000 - 170, type: "command" },
      { message: "// Klipper PRINT_START calibration validated", time: Date.now() / 1000 - 160, type: "response" }
    ],
    containers: [
      {
        id: "c1a2b3c4d5e6",
        name: "sentinel-ollama",
        image: "ollama/ollama:latest",
        status: "Up 4 hours (healthy)",
        ports: "11434->11434/tcp",
        command: "ollama serve"
      },
      {
        id: "d5e6f7a8b9c0",
        name: "sentinel-klipper-moonraker",
        image: "mainsailcrew/moonraker:v0.8.0",
        status: "Up 4 hours",
        ports: "7125->7125/tcp",
        command: "/usr/bin/moonraker"
      },
      {
        id: "e9f0a1b2c3d4",
        name: "sentinel-vault-sync",
        image: "sentinel/vault-syncer:1.0",
        status: "Up 3 hours",
        ports: "8002/udp",
        command: "sentinel-vault --watch"
      },
      {
        id: "f3a4b5c6d7e8",
        name: "mosquitto-broker",
        image: "eclipse-mosquitto:2.0",
        status: "Up 4 hours",
        ports: "1883->1883/tcp",
        command: "/usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf"
      }
    ],
    network: {
      primary: {
        name: "eth0",
        type: "ethernet",
        isup: true,
        speed: 1000,
        ip: "192.168.1.50",
        mac: "52:54:00:12:34:56"
      },
      interfaces: [
        { name: "eth0", type: "ethernet", isup: true, speed: 1000, ip: "192.168.1.50", mac: "52:54:00:12:34:56" },
        { name: "wlan0", type: "wifi", isup: false, speed: 0, ip: "", mac: "52:54:00:12:34:57" },
        { name: "tailscale0", type: "vpn", isup: true, speed: 100, ip: "100.85.12.34", mac: "" }
      ],
      internet: {
        has_internet: true,
        latency_ms: 18.2,
        mode: "online",
        status_label: "Conectado a Internet",
        message: "Acceso a WAN/Internet activo. Enlaces remotos y actualizaciones disponibles."
      },
      gateway: "192.168.1.1",
      local_ip: "192.168.1.50",
      traffic: {
        upload_kbps: +(35 + Math.random() * 20).toFixed(1),
        download_kbps: +(120 + Math.random() * 80).toFixed(1),
        total_sent_mb: 852.4,
        total_recv_mb: 2314.9
      },
      neighbors: [
        { ip: "192.168.1.1", mac: "d8:07:b6:11:22:33", interface: "LAN", vendor: "Cisco/Linksys Router", device_type: "router" },
        { ip: "192.168.1.12", mac: "b8:27:eb:aa:bb:cc", interface: "LAN", vendor: "Raspberry Pi Foundation", device_type: "raspberry_pi" },
        { ip: "192.168.1.35", mac: "00:1e:06:44:55:66", interface: "LAN", vendor: "Creality 3D / Klipper Host", device_type: "printer" },
        { ip: "192.168.1.78", mac: "30:ae:a4:77:88:99", interface: "LAN", vendor: "Espressif Inc.", device_type: "esp32" },
        { ip: "192.168.1.105", mac: "e4:5f:01:ab:cd:ef", interface: "LAN", vendor: "Workstation / Laptop", device_type: "laptop" }
      ]
    },
    tailscale: {
      BackendState: "Running",
      Self: {
        HostName: "sentinel-master-node",
        DNSName: "sentinel-master-node.tailnet.ts.net",
        TailscaleIPs: ["100.85.12.34"]
      }
    },
    system: {
      cpu_model: os.cpus()[0]?.model || "Intel(R) Core(TM) i7-13700H @ 2.40GHz (AVX2 Enabled)",
      gpu: {
        has_gpu: true,
        model: "NVIDIA GeForce RTX 4070 (8GB VRAM)",
        vram_total_mb: 8192,
        vram_used_mb: 2450,
        vram_free_mb: 5742,
        usage: lastMetrics.gpu,
        temp: lastMetrics.gpu_temp,
        driver: "555.42",
        vendor: "NVIDIA"
      },
      memory: {
        total: totalMem,
        used: usedMem,
        available: availMem,
        cached: 1024 * 1024 * 1024,
        free: freeMem,
        swap_total: 4 * 1024 * 1024 * 1024,
        swap_free: 3.6 * 1024 * 1024 * 1024
      },
      disks: [
        {
          device: "/dev/sda1",
          total: 512000000000,
          used: 134000000000,
          free: 378000000000,
          mountpoint: "/"
        },
        {
          device: "/dev/sdb1",
          total: 1000000000000,
          used: 320000000000,
          free: 680000000000,
          mountpoint: "/mnt/storage"
        }
      ],
      uptime: Math.round((Date.now() - startTime) / 1000) + 14400,
      loadavg: os.loadavg(),
      cpu_cores: os.cpus().length || 8,
      cpu_freqs: os.cpus().map(c => c.speed || 2400),
      processes: [
        { pid: "101", user: "sentinel", cpu: `${lastMetrics.cpu.toFixed(1)}`, mem: "4.2", threads: "12", name: "sentinel-engine" },
        { pid: "142", user: "ollama", cpu: "1.2", mem: "12.5", threads: "8", name: "ollama-runner" },
        { pid: "189", user: "moonraker", cpu: "0.8", mem: "1.4", threads: "4", name: "moonraker" },
        { pid: "245", user: "tailscale", cpu: "0.2", mem: "0.9", threads: "6", name: "tailscaled" },
        { pid: "312", user: "root", cpu: "0.5", mem: "2.1", threads: "14", name: "dockerd" },
        { pid: "405", user: "mosquitto", cpu: "0.1", mem: "0.4", threads: "2", name: "mosquitto" }
      ],
      active_users: [
        { user: "operator", terminal: "pts/0", login_time: "2026-09-30 08:30", ip: "192.168.1.105" },
        { user: "student_lab", terminal: "pts/1", login_time: "2026-09-30 09:15", ip: "192.168.1.78" }
      ],
      open_ports: [
        { protocol: "tcp", state: "LISTEN", local_address: "0.0.0.0:3000" },
        { protocol: "tcp", state: "LISTEN", local_address: "127.0.0.1:8001" },
        { protocol: "tcp", state: "LISTEN", local_address: "0.0.0.0:8002" },
        { protocol: "tcp", state: "LISTEN", local_address: "127.0.0.1:11434" },
        { protocol: "tcp", state: "LISTEN", local_address: "127.0.0.1:7125" },
        { protocol: "tcp", state: "LISTEN", local_address: "0.0.0.0:1883" }
      ],
      smart: [
        { device: "/dev/sda", model: "Samsung SSD 980 1TB", health: "PASSED", temp: "34" }
      ],
      ufw: {
        enabled: true,
        rules: [
          "[ 1] 22/tcp ALLOW IN Anywhere",
          "[ 2] 3000/tcp ALLOW IN Anywhere",
          "[ 3] 8001/tcp ALLOW IN Anywhere",
          "[ 4] 8002/udp ALLOW IN Anywhere"
        ]
      },
      cron: [
        { user: "system", job: "@reboot /usr/bin/sentinel_service --daemon" },
        { user: "operator", job: "0 */6 * * * /usr/bin/backup_vault.sh" }
      ]
    },
    metrics_history: metricsHistory,
    notifications: NOTIFICATIONS.splice(0)
  };
}

// =========================================================================
// REST API ROUTES
// =========================================================================

// 1. Data telemetry
app.get('/api/data', (_req: Request, res: Response) => {
  res.json(getDynamicSystemData());
});

// 2. Node auth & info
app.get('/api/node/token', (_req: Request, res: Response) => {
  res.json({ token: "sentinel-token-stem-lab-2026", node_id: "host-maestro" });
});

app.get('/api/node/info', (_req: Request, res: Response) => {
  res.json({
    node_id: "host-maestro",
    node_name: "Host Maestro (Local)",
    cores: os.cpus().length || 8,
    total_ram_gb: 16.0,
    memory_gb: 16.0,
    os: "Linux 6.8 SentinelOS (AVX2 Native)"
  });
});

// 3. Mesh network nodes
const MESH_NODES = [
  {
    node_id: "node-cluster-alpha",
    node_name: "Satélite Taller STEM 01",
    status: "online",
    candidates: ["http://192.168.1.12:8001"],
    token: "sat-tok-01",
    data: {
      system: { cpu_cores: 4, memory: { total: 4294967296, used: 1610612736 } },
      metrics_history: [{ time: "09:00", cpu: 12, ram: 38 }]
    }
  },
  {
    node_id: "node-cluster-beta",
    node_name: "Impresora 3D Ender-3 V3",
    status: "online",
    candidates: ["http://192.168.1.35:8001"],
    token: "sat-tok-02",
    data: {
      system: { cpu_cores: 4, memory: { total: 2147483648, used: 858993459 } },
      metrics_history: [{ time: "09:00", cpu: 8, ram: 40 }]
    }
  }
];

app.get('/api/mesh/nodes', (_req: Request, res: Response) => {
  res.json({ nodes: MESH_NODES });
});

app.post('/api/mesh/scan', (_req: Request, res: Response) => {
  res.json({
    status: "success",
    message: "Escaneo de red completado",
    nodes: MESH_NODES
  });
});

app.post('/api/mesh/heartbeat', (req: Request, res: Response) => {
  res.json({ status: "acknowledged", received: req.body });
});

// 4. Services list
app.get('/api/services', (_req: Request, res: Response) => {
  res.json({
    services: [
      { name: "sentinel-engine", status: "active (running)", load: "loaded", sub: "running", description: "Sentinel STEM Cognitive Engine Daemon" },
      { name: "ollama.service", status: "active (running)", load: "loaded", sub: "running", description: "Ollama Local LLM Inference Engine" },
      { name: "moonraker.service", status: "active (running)", load: "loaded", sub: "running", description: "Moonraker 3D Print Management API" },
      { name: "tailscaled.service", status: "active (running)", load: "loaded", sub: "running", description: "Tailscale Secure Zero-Trust Network Daemon" },
      { name: "docker.service", status: "active (running)", load: "loaded", sub: "running", description: "Docker Application Container Engine" },
      { name: "mosquitto.service", status: "active (running)", load: "loaded", sub: "running", description: "Eclipse Mosquitto MQTT Broker" },
      { name: "avahi-daemon", status: "active (running)", load: "loaded", sub: "running", description: "mDNS/DNS-SD Service Discovery Daemon" },
      { name: "ssh.service", status: "active (running)", load: "loaded", sub: "running", description: "OpenBSD Secure Shell Server" }
    ]
  });
});

// 5. System logs
app.get('/api/logs', (_req: Request, res: Response) => {
  res.json({ logs: SYSTEM_LOGS.join('\n') });
});

// 6. Sentinel AI Models & Status
app.get('/api/sentinel/models', (_req: Request, res: Response) => {
  res.json({
    models: AVAILABLE_MODELS,
    active_model: activeModel,
    has_internet: true
  });
});

app.post('/api/sentinel/model/switch', (req: Request, res: Response) => {
  const { model } = req.body || {};
  const found = AVAILABLE_MODELS.find(m => m.id === model);
  if (found) {
    activeModel = model;
    SYSTEM_LOGS.push(`[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [SUCCESS] Conmutado a modelo: ${found.name}`);
    res.json({ success: true, active_model: activeModel });
  } else {
    res.status(400).json({ detail: "Modelo no disponible" });
  }
});

app.get('/api/sentinel/status', (_req: Request, res: Response) => {
  const current = AVAILABLE_MODELS.find(m => m.id === activeModel) || AVAILABLE_MODELS[0];
  res.json({
    running: true,
    model_id: current.id,
    model_name: current.name,
    backend: current.type === 'local' ? 'llama.cpp AVX2' : 'NVIDIA NIM Cloud',
    vram_usage_mb: current.type === 'local' ? 1850 : 0,
    inference_speed_tps: current.id.includes('1b') ? 22.4 : 14.8
  });
});

app.get('/api/sentinel/lora/status', (_req: Request, res: Response) => {
  res.json({
    total_examples: 1420,
    active_adapters: ["stem_math_rigor", "klipper_gcode_safety", "anti_emoji_discipline"],
    status: "synchronized"
  });
});

// 7. Sentinel STEM Cognitive Chat (Streaming)
app.post('/api/sentinel/chat', async (req: Request, res: Response) => {
  const { messages, effort, enable_thinking, enable_research } = req.body || {};
  const lastUserMsg = Array.isArray(messages) && messages.length > 0 ? messages[messages.length - 1].content : "";
  const query = (lastUserMsg || "").trim().toLowerCase();

  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Transfer-Encoding', 'chunked');
  res.setHeader('Cache-Control', 'no-cache');

  // Helper stream writer
  const streamWrite = async (text: string) => {
    res.write(text);
    await new Promise(r => setTimeout(r, 18));
  };

  // 1. Thinking block if requested
  if (enable_thinking) {
    await streamWrite("<pensamiento>\n");
    await streamWrite("1. Análisis del objetivo pedagógico del estudiante.\n");
    await streamWrite("2. Identificación de conceptos STEM fundamentales y modelos matemáticos vinculados.\n");
    await streamWrite("3. Verificación de fórmulas rigurosas en notación LaTeX y reglas de cero emojis.\n");
    await streamWrite("4. Vinculación con notas de la bóveda Obsidian del laboratorio.\n");
    await streamWrite("</pensamiento>\n\n");
  }

  // 2. Research meta if requested
  if (enable_research) {
    await streamWrite("<!--RESEARCH_META: Búsqueda bibliográfica en la bóveda de notas de Sentinel completada. Se localizaron 3 fuentes relevantes.-->\n\n");
  }

  // 3. Craft response tailored to student's query with pedagogue mentor persona
  let responseText = "";

  if (!query || query.includes("hola") || query.includes("buenas") || query.includes("saludos")) {
    responseText = "Saludos cordial. Como mentor del Laboratorio STEM, me encuentro listo para guiarte en el desarrollo de proyectos de ciencia, ingeniería, robótica o administración de sistemas. ¿En qué concepto técnico o práctica de laboratorio deseas profundizar hoy?";
  } else if (query.includes("ohm") || query.includes("resistencia") || query.includes("voltaje") || query.includes("corriente")) {
    responseText = "Para comprender la [[ley_de_ohm]], imagina una tubería de agua donde el agua que fluye representa la corriente, la presión que la empuja es el voltaje, y la estrechez del tubo es la resistencia.\n\n" +
      "Matemáticamente, la relación se formula de manera lineal:\n\n" +
      "$$V = I \\cdot R$$\n\n" +
      "Donde:\n" +
      "- $V$: Diferencia de potencial eléctrico (medido en Voltios, $[\\text{V}]$).\n" +
      "- $I$: Intensidad de corriente eléctrica (medida en Amperios, $[\\text{A}]$).\n" +
      "- $R$: Resistencia eléctrica del conductor (medida en Ohmios, $[\\Omega]$).\n\n" +
      "A continuación se presenta el comportamiento de las variables eléctricas:\n\n" +
      "| Parámetro | Símbolo | Unidad | Efecto al Incrementar |\n" +
      "| :--- | :--- | :--- | :--- |\n" +
      "| Voltaje | $V$ | Voltio (V) | Incrementa la corriente directamente |\n" +
      "| Corriente | $I$ | Amperio (A) | Aumenta la potencia térmica disipada |\n" +
      "| Resistencia | $R$ | Ohmio ($\\Omega$) | Limita y frena el flujo de electrones |\n\n" +
      "Esta relación es fundamental para dimensionar resistencias limitadoras en microcontroladores [[esp32_freertos]] y calcular la [[potencia_electrica]].";
  } else if (query.includes("klipper") || query.includes("impresora") || query.includes("print_start") || query.includes("3d")) {
    responseText = "El firmware [[cama_caliente_klipper]] revoluciona la fabricación aditiva distribuyendo las tareas de cómputo entre una computadora host (como una Raspberry Pi o servidor) y los microcontroladores de la impresora.\n\n" +
      "A diferencia de firmwares tradicionales monolíticos, Klipper precalcula las curvas de aceleración y cinemática en el procesador host con precisión de microsegundos.\n\n" +
      "| Función | Ejecución Host Linux | Ejecución Microcontrolador (MCU) |\n" +
      "| :--- | :--- | :--- |\n" +
      "| Cinemática | Cálculo de matrices [[cinematica_corexy]] | Generación precisa de pulsos STEP/DIR |\n" +
      "| Control Térmico | Algoritmo predictivo [[pid_controller]] | Lectura analógica por ADC |\n" +
      "| Compensación | Input Shaping y Presión Lineal | Conmutación de transistores MOSFET |\n\n" +
      "Un macro seguro para inicialización de impresión se estructura de la siguiente manera:\n\n" +
      "```ini\n" +
      "[gcode_macro PRINT_START]\n" +
      "gcode:\n" +
      "    M140 S{params.BED_TEMP|default(60)}\n" +
      "    G28 ; Auto Home en todos los ejes\n" +
      "    BED_MESH_PROFILE LOAD=default\n" +
      "    M109 S{params.EXTRUDER_TEMP|default(215)}\n" +
      "```\n\n" +
      "Este procedimiento garantiza la nivelación adecuada de la superficie antes de extruir polímeros técnicos.";
  } else if (query.includes("esp32") || query.includes("freertos") || query.includes("mqtt")) {
    responseText = "El microcontrolador [[esp32_freertos]] combina un procesador dual-core de 32 bits con conectividad inalámbrica, convirtiéndolo en el dispositivo ideal para adquisición de telemetría de laboratorio.\n\n" +
      "Al implementar [[protocolo_mqtt]], el dispositivo publica mediciones periódicas en canales ligeros sin saturar la red local.\n\n" +
      "| Módulo | Especificación | Rol en el Laboratorio |\n" +
      "| :--- | :--- | :--- |\n" +
      "| Núcleo 0 (Protocol Core) | Wi-Fi y TCP/IP stack | Negociación y sockets de red [[sockets_red]] |\n" +
      "| Núcleo 1 (App Core) | Tarea de sensado FreeRTOS | Lectura de sensores mediante [[pwm_modulacion]] |\n" +
      "| Broker MQTT | Mosquitto TCP 1883 | Distribución de eventos a SentinelOS |\n\n" +
      "Las lecturas se serializan de forma concisa para su consumo por el motor de telemetría de Sentinel.";
  } else if (query.includes("ssh") || query.includes("docker") || query.includes("tailscale") || query.includes("red")) {
    responseText = "La conectividad segura en SentinelOS se fundamenta en túneles Zero-Trust mediante [[cifrado_tailscale]] y el estándar WireGuard.\n\n" +
      "Esto permite conectar nodos satélite de talleres distantes sin abrir puertos vulnerables en el firewall perimetral del instituto.\n\n" +
      "| Tecnología | Protocolo | Capa OSI | Función de Seguridad |\n" +
      "| :--- | :--- | :--- | :--- |\n" +
      "| Tailscale | WireGuard UDP 41641 | Red (Capa 3) | Túnel encriptado punto a punto |\n" +
      "| OpenSSH | TCP 22 | Aplicación (Capa 7) | Consola interactiva remota cifrada |\n" +
      "| Sentinel Mesh | UDP 8002 | Transporte | Descubrimiento local sin dependencias |\n\n" +
      "Esta arquitectura garantiza integridad y confidencialidad en toda la infraestructura de investigación.";
  } else {
    responseText = `Has consultado sobre "${lastUserMsg}". En el marco de la investigación pedagógica STEM de SentinelOS, este tema se articula mediante modelos rigurosos y análisis de sistemas.\n\n` +
      "Es conveniente descomponer el problema en tres etapas esenciales:\n" +
      "1. Definición formal de las variables físicas y los principios teóricos rectores.\n" +
      "2. Análisis cuantitativo de las relaciones matemáticas subyacentes.\n" +
      "3. Validación empírica mediante código o instrumental de laboratorio.\n\n" +
      "| Variable | Dominio | Dependencia en SentinelOS |\n" +
      "| :--- | :--- | :--- |\n" +
      "| Parámetro Principal | Físico / Algorítmico | Monitoreado en telemetría en tiempo real |\n" +
      "| Tolerancia | Control e Ingeniería | Regulada por bucle [[pid_controller]] |\n" +
      "| Registro | Bóveda Obsidian | Vinculado a notas técnicas de [[sockets_red]] |\n\n" +
      "Puedes explorar los nodos conceptuales en la vista de grafo o ejecutar pruebas de banco para verificar la hipótesis de trabajo.";
  }

  // Stream output words smoothly
  const words = responseText.split(/(\s+)/);
  for (const w of words) {
    await streamWrite(w);
  }

  res.end();
});

// 8. Obsidian Knowledge Graph API
app.get('/api/sentinel/graph', (_req: Request, res: Response) => {
  const notes = Array.from(VAULT_NOTES.values());
  const nodes = notes.map((n, idx) => ({
    id: n.id,
    name: n.title,
    group: n.category,
    val: Math.max(8, n.links.length * 3 + 6),
    color: n.category === 'memoria' ? '#06b6d4' : (n.category === 'laboratorio' ? '#f59e0b' : '#a855f7'),
    content: n.content,
    tags: n.tags,
    category: n.category,
    index: idx
  }));

  const nodeSet = new Set(nodes.map(n => n.id));
  const links: { source: string; target: string; value: number }[] = [];

  notes.forEach(n => {
    (n.links || []).forEach(targetId => {
      if (nodeSet.has(targetId)) {
        links.push({ source: n.id, target: targetId, value: 1 });
      }
    });
  });

  res.json({ nodes, links });
});

app.post('/api/sentinel/node', (req: Request, res: Response) => {
  const { id, title, category, content, tags } = req.body || {};
  const noteId = id || (title || "nueva_nota").toLowerCase().replace(/[^a-z0-9]/g, '_');
  const tagList = Array.isArray(tags) ? tags : (typeof tags === 'string' ? tags.split(',').map((t: string) => t.trim()) : []);

  // Extract [[wikilinks]]
  const matches = (content || '').match(/\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]/g) || [];
  const extractedLinks = matches.map((m: string) => m.replace(/\[\[|\]\]/g, '').split('|')[0].trim().toLowerCase().replace(/\s+/g, '_'));

  const newNote: VaultNote = {
    id: noteId,
    title: title || noteId,
    category: category || 'conceptos',
    tags: tagList,
    links: extractedLinks,
    content: content || '',
    body: content || '',
    size: (content || '').length,
    modified: Date.now()
  };

  VAULT_NOTES.set(noteId, newNote);
  SYSTEM_LOGS.push(`[${new Date().toISOString().replace('T', ' ').slice(0, 19)}] [INFO] Nueva nota agregada a la bóveda Obsidian: ${title} (${noteId})`);

  res.json({ success: true, note: newNote });
});

// 9. Network Details & Auxiliary Endpoints
app.get('/api/network/details', (_req: Request, res: Response) => {
  res.json({
    internet: { has_internet: true, latency_ms: 18.2 },
    local_ip: "192.168.1.50",
    gateway: "192.168.1.1",
    dns: ["1.1.1.1", "8.8.8.8"]
  });
});

app.get('/api/network/speedtest', (_req: Request, res: Response) => {
  res.json({
    download_mbps: +(240 + Math.random() * 60).toFixed(1),
    upload_mbps: +(80 + Math.random() * 25).toFixed(1),
    ping_ms: +(12 + Math.random() * 5).toFixed(1),
    server: "Sentinel Speed Test Node (Local Lab WAN)"
  });
});

app.post('/api/network/wol', (req: Request, res: Response) => {
  const { mac } = req.body || {};
  res.json({ success: true, message: `Paquete Mágico Wake-on-LAN transmitido a ${mac || "broadcast"}` });
});

app.get('/api/files/audit', (_req: Request, res: Response) => {
  res.json({
    logs: [
      { timestamp: "2026-09-30 22:30", user: "operator", path: "/etc/sentinel/config.yaml", action: "READ" },
      { timestamp: "2026-09-30 23:05", user: "sentinel_daemon", path: "/var/log/sentinel/telemetry.db", action: "WRITE" }
    ]
  });
});

app.get('/api/marketplace/search', (req: Request, res: Response) => {
  const q = String(req.query.q || '').toLowerCase();
  const allApps = [
    { id: "klipper", name: "Klipper 3D Engine", description: "Firmware de alto rendimiento para impresoras 3D", category: "Fabricación" },
    { id: "octoprint", name: "OctoPrint Host", description: "Panel de control web para impresión 3D", category: "Fabricación" },
    { id: "mosquitto", name: "Eclipse Mosquitto", description: "Servidor broker de mensajería MQTT ligero", category: "IoT" },
    { id: "prometheus", name: "Prometheus Telemetry", description: "Base de datos temporal de métricas de hardware", category: "Monitoreo" },
    { id: "grafana", name: "Grafana Dashboards", description: "Visualización avanzada de series de tiempo", category: "Monitoreo" }
  ];
  const results = allApps.filter(a => a.name.toLowerCase().includes(q) || a.description.toLowerCase().includes(q));
  res.json({ results });
});

app.get('/api/marketplace/installed', (_req: Request, res: Response) => {
  res.json({
    results: [
      { id: "klipper", name: "Klipper 3D Engine", version: "v0.12.0", status: "activo" },
      { id: "mosquitto", name: "Eclipse Mosquitto", version: "2.0.18", status: "activo" }
    ]
  });
});

app.post('/api/marketplace/uninstall', (req: Request, res: Response) => {
  res.json({ success: true, message: `Desinstalación en segundo plano programada para ${req.body?.app_id}` });
});

app.get('/api/apt', (_req: Request, res: Response) => {
  res.json({ count: 2, updates: ["openssl (3.0.13-0ubuntu3.4)", "systemd (255.4-1ubuntu8.4)"] });
});

app.get('/api/fs', (req: Request, res: Response) => {
  const targetPath = String(req.query.path || '/');
  res.json({
    current_path: targetPath,
    dirs: [
      { name: "etc", path: "/etc", size: "4.0K", modified: "2026-09-20" },
      { name: "var", path: "/var", size: "4.0K", modified: "2026-09-25" },
      { name: "home", path: "/home", size: "4.0K", modified: "2026-09-28" },
      { name: "opt", path: "/opt", size: "4.0K", modified: "2026-09-29" },
      { name: "sentinel-vault", path: "/sentinel-vault", size: "12.0K", modified: "2026-09-30" }
    ],
    files: [
      { name: "sentinel.conf", path: "/sentinel.conf", size: "1.8K", modified: "2026-09-30" },
      { name: "telemetry.log", path: "/telemetry.log", size: "42.5K", modified: "2026-09-30" }
    ]
  });
});

app.get('/api/printer/history', (_req: Request, res: Response) => {
  res.json({
    jobs: [
      { id: 1, filename: "calibration_cube_v3.gcode", status: "completed", duration: 1820, date: "2026-09-30 18:20" },
      { id: 2, filename: "benchy_high_speed.gcode", status: "completed", duration: 2450, date: "2026-09-29 14:10" }
    ]
  });
});

app.post('/api/system/uninstall', (_req: Request, res: Response) => {
  res.json({ success: true, message: "Operación de mantenimiento del sistema procesada." });
});

app.post('/api/terminal/session/terminate', (_req: Request, res: Response) => {
  res.json({ success: true });
});

app.get('/api/remote/proxy', (req: Request, res: Response) => {
  // Proxy stub returning valid structure
  res.json({
    system: { cpu_cores: 4, memory: { total: 4294967296, used: 1610612736 } },
    metrics_history: [{ time: new Date().toLocaleTimeString(), cpu: 14, ram: 38 }]
  });
});

// Generic action POST fallback (for docker control, printer actions, etc.)
app.post('/api/:action', (req: Request, res: Response) => {
  res.json({ success: true, action: req.params.action, received: req.body });
});
app.post('/api/:domain/:action', (req: Request, res: Response) => {
  res.json({ success: true, domain: req.params.domain, action: req.params.action, received: req.body });
});

// =========================================================================
// HTTP SERVER & WEBSOCKET SETUP
// =========================================================================

const server = http.createServer(app);
const wss = new WebSocketServer({ server });

wss.on('connection', (ws: WebSocket, req: http.IncomingMessage) => {
  const url = req.url || '';

  if (url.includes('/api/ws/terminal')) {
    // Interactive Web Terminal session with bash simulation
    const welcomeBanner = "\r\n\x1b[1;36m====================================================\x1b[0m\r\n" +
      "\x1b[1;32m  SENTINEL // STEM Cognitive OS - Interactive Console\x1b[0m\r\n" +
      "\x1b[1;30m  Host Maestro (Linux x86_64 SentinelOS 6.8 AVX2)\x1b[0m\r\n" +
      "\x1b[1;36m====================================================\x1b[0m\r\n" +
      "Escribe \x1b[1;33mhelp\x1b[0m o \x1b[1;33msentinel status\x1b[0m para ver comandos disponibles.\r\n\r\n";
    
    ws.send(welcomeBanner);
    const prompt = "\x1b[1;32msentinel@host-maestro\x1b[0m:\x1b[1;34m~\x1b[0m$ ";
    ws.send(prompt);

    let currentLine = "";

    ws.on('message', (message: Buffer | string) => {
      const input = message.toString();

      // Handle terminal resize commands: "RESIZE:cols:rows"
      if (input.startsWith("RESIZE:")) {
        return;
      }

      if (input === "__SENTINEL_RESTART__") {
        ws.send("\r\n\x1b[1;33m[*] Reiniciando sesión de terminal...\x1b[0m\r\n");
        ws.send(welcomeBanner);
        ws.send(prompt);
        currentLine = "";
        return;
      }

      // Handle character input from xterm
      for (let i = 0; i < input.length; i++) {
        const char = input[i];

        if (char === '\r' || char === '\n') {
          ws.send('\r\n');
          const cmd = currentLine.trim();
          currentLine = "";

          if (cmd.length > 0) {
            handleTerminalCommand(cmd, ws);
          }
          ws.send(prompt);
        } else if (char === '\x7f' || char === '\b') {
          // Backspace
          if (currentLine.length > 0) {
            currentLine = currentLine.slice(0, -1);
            ws.send('\b \b');
          }
        } else if (char === '\x03') {
          // Ctrl+C
          ws.send('^C\r\n');
          currentLine = "";
          ws.send(prompt);
        } else if (char >= ' ') {
          currentLine += char;
          ws.send(char);
        }
      }
    });
  } else if (url.includes('/api/ws/model/download')) {
    // Model download simulator
    let step = 0;
    const interval = setInterval(() => {
      step += 15;
      if (step <= 100) {
        ws.send(JSON.stringify({
          type: "progress",
          percent: step,
          speed: "34.2 MB/s",
          downloaded: `${(step * 0.008).toFixed(2)} GB`,
          total: "0.82 GB"
        }));
      } else {
        clearInterval(interval);
        ws.send(JSON.stringify({
          type: "success",
          message: "Modelo sentinel-agentic-1b.Q4_K_M.gguf descargado y registrado exitosamente en el motor de inferencia."
        }));
      }
    }, 400);

    ws.on('close', () => clearInterval(interval));
  }
});

function handleTerminalCommand(cmd: string, ws: WebSocket) {
  const parts = cmd.split(' ');
  const base = parts[0].toLowerCase();

  switch (base) {
    case 'help':
      ws.send("Comandos disponibles en SentinelOS:\r\n" +
        "  \x1b[1;36msentinel status\x1b[0m  - Estado del motor cognitivo y modelo en memoria\r\n" +
        "  \x1b[1;36msentinel models\x1b[0m  - Lista de SLMs disponibles en el laboratorio\r\n" +
        "  \x1b[1;36mtop / htop\x1b[0m       - Resumen de recursos y procesos del sistema\r\n" +
        "  \x1b[1;36mdf -h\x1b[0m            - Uso de almacenamiento de particiones montadas\r\n" +
        "  \x1b[1;36muname -a\x1b[0m         - Versión del Kernel Linux y arquitectura del procesador\r\n" +
        "  \x1b[1;36mifconfig / ip\x1b[0m    - Configuración de interfaces de red y VPN\r\n" +
        "  \x1b[1;36mclear\x1b[0m            - Limpiar pantalla de la terminal\r\n\r\n");
      break;

    case 'sentinel':
      if (parts[1] === 'status') {
        ws.send(`\x1b[1;32mSENTINEL COGNITIVE ENGINE ACTIVE\x1b[0m\r\n` +
          `  Modelo Activo: ${activeModel}\r\n` +
          `  Aceleración: SIMD AVX2 + mmap/mlock\r\n` +
          `  Inferencia: ~22.4 tokens/segundo\r\n` +
          `  Bóveda Obsidian: ${VAULT_NOTES.size} notas conceptuales sincronizadas\r\n\r\n`);
      } else if (parts[1] === 'models') {
        ws.send("Modelos registrados:\r\n" +
          AVAILABLE_MODELS.map(m => `  • \x1b[1;33m${m.id}\x1b[0m - ${m.name} (${m.badge})`).join('\r\n') + "\r\n\r\n");
      } else {
        ws.send("Uso: sentinel [status|models]\r\n\r\n");
      }
      break;

    case 'clear':
      ws.send("\x1b[2J\x1b[H");
      break;

    case 'uname':
      ws.send("Linux sentinel-master 6.8.0-45-generic #45-Ubuntu SMP PREEMPT_DYNAMIC x86_64 GNU/Linux\r\n\r\n");
      break;

    case 'whoami':
      ws.send("sentinel (Laboratorio STEM)\r\n\r\n");
      break;

    case 'df':
      ws.send("Filesystem     Type      Size  Used Avail Use% Mounted on\r\n" +
        "/dev/sda1      ext4      476G  125G  328G  28% /\r\n" +
        "/dev/sdb1      btrfs     931G  298G  633G  32% /mnt/storage\r\n" +
        "tmpfs          tmpfs     7.8G     0  7.8G   0% /dev/shm\r\n\r\n");
      break;

    case 'top':
    case 'htop':
      ws.send(`top - ${new Date().toLocaleTimeString()} up 4:12,  2 users,  load average: 0.18, 0.24, 0.20\r\n` +
        "Tasks: 184 total,   1 running, 183 sleeping,   0 stopped\r\n" +
        "%Cpu(s): 14.8 us,  2.1 sy,  0.0 ni, 82.7 id,  0.4 wa\r\n" +
        "MiB Mem :  16384.0 total,   6780.2 free,   6824.1 used,   2779.7 buff/cache\r\n\r\n");
      break;

    case 'ifconfig':
    case 'ip':
      ws.send("eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\r\n" +
        "        inet 192.168.1.50  netmask 255.255.255.0  broadcast 192.168.1.255\r\n" +
        "        ether 52:54:00:12:34:56  txqueuelen 1000  (Ethernet)\r\n" +
        "tailscale0: flags=4305<UP,POINTOPOINT,RUNNING,NOARP,MULTICAST>  mtu 1280\r\n" +
        "        inet 100.85.12.34  netmask 255.255.255.255  destination 100.85.12.34\r\n\r\n");
      break;

    default:
      ws.send(`\x1b[1;31m${base}\x1b[0m: orden no encontrada. Escribe \x1b[1;33mhelp\x1b[0m para ver comandos admitidos.\r\n\r\n`);
  }
}

// =========================================================================
// VITE MIDDLEWARE (DEV) / STATIC FILE SERVING (PROD)
// =========================================================================

async function setupFrontend() {
  const isProduction = process.env.NODE_ENV === 'production';

  if (!isProduction) {
    try {
      const { createServer: createViteServer } = await import('vite');
      const vite = await createViteServer({
        server: { middlewareMode: true, hmr: false },
        appType: 'spa',
      });
      app.use(vite.middlewares);
    } catch (err) {
      console.error("Failed to load Vite dev server:", err);
      // Fallback to static
      app.use(express.static(__dirname));
    }
  } else {
    const distPath = path.resolve(__dirname, 'dist');
    if (fs.existsSync(distPath)) {
      app.use(express.static(distPath));
      app.get('*', (_req, res) => {
        res.sendFile(path.resolve(distPath, 'index.html'));
      });
    } else {
      app.use(express.static(__dirname));
      app.get('*', (_req, res) => {
        res.sendFile(path.resolve(__dirname, 'index.html'));
      });
    }
  }

  const PORT = 3000;
  server.listen(PORT, '0.0.0.0', () => {
    console.log(`\n======================================================`);
    console.log(`  SentinelOS unified server running on port ${PORT}`);
    console.log(`  Local URL: http://0.0.0.0:${PORT}`);
    console.log(`======================================================\n`);
  });
}

setupFrontend();
