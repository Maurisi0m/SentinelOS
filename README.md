# SentinelOS (v2.0) - Sistema Operativo Cognitivo Distribuido

Plataforma de infraestructura y telemetria distribuida para centros de computo, laboratorios de investigacion y servidores de mision critica. Integra gestion de flota multi-nodo, descubrimiento de malla por red local o tuneles cifrados, motor de inferencia agentica especializado en terminal y administracion de sistemas, y un panel de control interactivo en tiempo real.

---

## 1. Arquitectura General del Sistema

SentinelOS opera bajo un modelo de arquitectura distribuida hibrida compuesto por tres capas principales:

```
+-----------------------------------------------------------------------------------+
|                            CAPA DE CONTROL Y VISUALIZACION                        |
|   Sentinel Cockpit (React 19 + Vite + Canvas Telemetry + Terminal Interactiva)    |
+-----------------------------------------------------------------------------------+
                                         |
                       HTTP / REST / WebSockets / SSE
                                         |
+-----------------------------------------------------------------------------------+
|                            CAPA DE SERVICIOS Y COMUNICACION                       |
|   Sentinel Backend (FastAPI + AsyncIO + Uvicorn)                                  |
|   - Gestor de Telemetria del Host (CPU, RAM, GPU, Discos, Red, Temperatura)      |
|   - Motor Mesh UDP LAN (Beacon 8002 / Discovery 8001)                             |
|   - Proxy Cifrado Multi-Nodo & Enrutador Satelite con Tokens Bearer              |
|   - Modulo de Descarga WebSocket de Modelos de Inteligencia Artificial           |
|   - Hotspot Wi-Fi Autonomo para Redes Aisladas (Air-Gapped)                       |
+-----------------------------------------------------------------------------------+
                                         |
                   Inferencia Local / Protocolo ReAct Atómico
                                         |
+-----------------------------------------------------------------------------------+
|                            CAPA COGNITIVA Y DE TERMINAL                           |
|   Sentinel-Agentic-1B (GGUF Q4_K_M en Docker Ollama / llama-server AVX2)          |
|   - Protocolo: [THOUGHT] -> [EXECUTE] -> [OUTPUT] (Sin Sobrecarga JSON)          |
|   - Dominio Estricto: Linux, Windows, macOS, Docker, STEM y Cirugia de Archivos   |
|   - Vector de Rechazo Out-of-Domain (Astrologia, Farandula, Poesia, Cocina)       |
+-----------------------------------------------------------------------------------+
```

---

## 2. Frontend: Sentinel Cockpit

El panel de control visual esta construido sobre React 19 y empaquetado con Vite, estilizado con un tema Cyberpunk Dark y tipografia de grado industrial sin dependencias de frameworks CSS externos.

### Caracteristicas Principales
* **Telemetria de Alto Rendimiento:** Visualizacion dinamica de metricas de CPU, memoria fisica, almacenamiento, uso de GPU (NVIDIA NVML e Intel), temperatura de nucleos y procesos activos.
* **Optimizacion de Intervalos de Polling:**
  * Telemetria del nodo local: Sondeo cada 3000 ms.
  * Telemetria de nodos satelite conectados: Sondeo cada 5000 ms para mitigar la saturacion del hilo de renderizado de React en despliegues con mas de dos servidores concurrentes.
  * Verificacion de estado de Internet: Intervalo desacoplado cada 30000 ms con almacenamiento en cache local.
* **Gestor de Modelos de Inteligencia Artificial (Modulo IA DESCARGAR):**
  * Modal integrado para la descarga directa de pesos en formato GGUF u Ollama.
  * Conectividad bidireccional por WebSocket (`/api/ws/model/download`) que transmite en tiempo real la tasa de transferencia, bloques descargados y porcentaje de avance.
  * Presets oficiales integrados, incluyendo el enlace directo al repositorio de Hugging Face (`Maurisi0m/Sentinel-Agentic-1B`).
  * Inyeccion automatica en el contenedor Docker Ollama tras finalizar la transferencia.
* **Terminal Operativa ReAct:** Consola interactiva para envio de instrucciones tecnicas al modelo agentico local, con renderizado de bloques de ejecucion y enlaces tecnicos Obsidian `[[Concepto]]`.
* **Topologia de Red y Escaneo Mesh:** Descubrimiento automatico de servidores satelite mediante beacons UDP en la red local y asignacion automatica a la lista de servidores monitorizados.

---

## 3. Backend: Servidor de Aplicacion y Enrutamiento

El nucleo del servicio esta implementado en Python 3 utilizando FastAPI y ejecutado bajo Uvicorn en el puerto 8001.

### Componentes Funcionales
* **`labsentinel_backend/main.py`:** Punto de entrada del servidor.
  * `GET /api/data`: Entrega instantanea de metricas del host (CPU, memoria, discos, red, GPU, sensores termicos).
  * `GET /api/node/token`: Validacion y entrega de tokens de autenticacion del nodo local (`sntl_live_...`).
  * `GET /api/mesh/nodes` y `POST /api/mesh/heartbeat`: Gestion del mapa de nodos descubiertos via beacon UDP LAN.
  * `POST /api/remote/proxy`: Mecanismo de retransmision segura para consultar servidores satelite cuando existen politicas de aislamiento perimetral.
  * `POST /api/network/hotspot/create`: Despliegue automatico de un punto de acceso Wi-Fi local para operar en entornos sin conexion a internet o router central.
  * `WS /api/ws/model/download`: Canal de comunicacion en tiempo real para recepcion de ordenes de descarga de modelos de lenguaje, ejecucion de subprocesos y transmision de logs al frontend.
* **Seguridad y Control de Acceso:**
  * Configuracion CORS permisiva para integracion fluida entre nodos satelite en subredes locales y tuneles Tailscale.
  * Middleware de autenticacion por cabecera `Authorization: Bearer <token>` para endpoints de administracion y ejecucion.
  * Desacoplamiento de llamadas bloqueantes de red con tiempos de espera estrictos de 3 segundos para evitar caidas del ciclo de eventos AsyncIO.

---

## 4. Capa Cognitiva: Sentinel-Agentic-1B

El motor de lenguaje de SentinelOS fue entrenado especificamente para actuar como operador autonomo de terminal y asistente STEM en infraestructuras locales con recursos computacionales limitados.

### Ficha Tecnica del Modelo
* **Nombre:** Sentinel-Agentic-1B
* **Arquitectura Base:** Llama-3.2-1B-Instruct (Meta AI / Unsloth)
* **Parametros Totales:** 1,230 Millones (1.23B)
* **Formato de Entrega:** GGUF Cuantizado Q4_K_M (808 MB)
* **Repositorio Oficial Hugging Face:** `https://huggingface.co/Maurisi0m/Sentinel-Agentic-1B`
* **Enlace de Descarga Directa:** `https://huggingface.co/Maurisi0m/Sentinel-Agentic-1B/resolve/main/sentinel-agentic-1b.Q4_K_M.gguf`

### Metodologia de Entrenamiento y Convergencia
* **Hardware de Entrenamiento:** GPU NVIDIA GeForce RTX 5060 Laptop (8 GB VRAM, CUDA FP16/BF16).
* **Tecnica de Ajuste:** QLoRA de alta precision sobre los modulos `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` y `lm_head` ($r=64$, $\alpha=128$, dropout 0.05).
* **Optimizador:** Paged AdamW 8-bit con decaimiento cosenoidal y tasa de aprendizaje $2 \times 10^{-4}$.
* **Volumen:** 11,500 steps de optimizacion continua sobre un dataset sintético multi-turno de administracion de sistemas y resolucion de problemas ReAct.
* **Metricas Clave de Convergencia:**
  * **Perdida Inicial (Step 1):** 4.0406
  * **Perdida Final (Step 11,500):** 0.0225 (-99.44% de reduccion de error).
  * **Perplejidad Final:** 1.022 PPL (convergencia determinista).
  * **Precision de Tokens:** 98.4% en comandos de terminal y operadores logicos.
  * **Norma de Gradiente (L2):** Descenso de 10.51 a 0.020, sin explosiones de gradiente ni divergencias numericas.

### Protocolo Operativo ReAct (Sin Tool Calling JSON)
A diferencia de los modelos tradicionales que consumen entre 600 y 1,200 tokens describiendo esquemas JSON, Sentinel-Agentic-1B emplea un protocolo plano basado en etiquetas:
* `[THOUGHT]`: Analisis previo, diagnostico del estado del sistema y seleccion del comando.
* `[EXECUTE]`: Comando raw no interactivo para ejecucion directa en Bash, PowerShell o Docker.
* `[OUTPUT]`: Inyeccion del resultado real capturado por el sistema operativo.

### Desaprendizaje y Rechazo Fuera de Dominio (Machine Unlearning)
Se aplicaron matrices de steering y desaprendizaje estricto para suprimir respuestas conversacionales o temas ajenos al entorno tecnico:
* Consultas de astrologia, chismes, farandula, recetas o poemas son interceptadas y rechazadas deterministamente con el mensaje:
  `Peticion fuera del dominio operacional de SENTINEL. Sistema restringido a STEM y ejecucion de terminal.`

### Rendimiento de Inferencia
* **Servidor HP (CPU AVX2 Pure C++ llama-server):** 46.8 tokens / segundo (Consumo de RAM: 1.1 GB).
* **Laptop RTX 5060 (GPU CUDA vLLM / PyTorch):** 128.4 tokens / segundo (Consumo de VRAM: 1.3 GB).
* **Raspberry Pi 5 (ARM64 Edge):** 18.5 tokens / segundo.

---

## 5. Bateria de Metricas y Evaluacion Comparativa

Los reportes graficos de evaluacion analitica fueron generados a 300 DPI y se encuentran disponibles en el directorio `export/metrics_report/`:

1. `sentinel_comparative_1_loss_convergence.png`:
   * Comparacion de Cross-Entropy Loss (Base: ~3.96 estancado vs Sentinel: 0.0225).
   * Perplejidad comparada (Base: 52.5 vs Sentinel: 1.022).
   * Histograma de densidad de error por secuencia.
   * Curva de tasa de aprendizaje cosenoidal.
2. `sentinel_comparative_2_noise_stability.png`:
   * Indice de ruido residual en representaciones latentes (-98.2% de reduccion).
   * Relacion Señal-Ruido (SNR): De +4.8 dB a +28.6 dB (Zona de alta confianza).
   * Norma del gradiente L2 a lo largo de 11,500 steps.
   * Entropia de prediccion de tokens (reduccion de 3.85 a 0.18 Nats).
3. `sentinel_comparative_3_operational_gain.png`:
   * Precision predictiva en terminal (+63.4% de ganancia neta).
   * Radar de competencias tecnicas (Linux 100%, PowerShell 98.5%, macOS 96%, Archivos 99.2%, Desaprendizaje 100%).
   * Ahorro de recursos (-97.2% tokens prefill, -71% memoria RAM, -67% disco).
   * Throughput comparativo en hardware de servidor.

---

## 6. Instalador, Firewall y Herramienta de Linea de Comandos (CLI)

SentinelOS cuenta con un subsistema de instalacion y mantenimiento multiplataforma desacoplado y no intrusivo.

### Instalador Multiplataforma (`installer/`)
* **Deteccion Automatica de Sistema Operativo:** Compatible con Windows 10/11, Ubuntu 22.04/24.04, Linux Mint, Debian y Arch Linux.
* **Configuracion de Firewall:**
  * **Windows:** Agrega reglas de entrada TCP para los puertos 8001 y 8002 mediante `netsh advfirewall` con perfil `profile=any` y genera excepciones directas para el binario de Python.
  * **Compatibilidad Antivirus de Terceros:** Deteccion automatica de procesos de Avast (`AvastSvc.exe`) y Norton (`Norton Security`), aplicando reglas de paso a nivel de sistema.
  * **Linux:** Apertura de puertos mediante `ufw allow 8001/tcp` e `iptables`.
* **Accesos Directos:** Creacion de accesos directos en el escritorio del usuario actual sin forzar la apertura no deseada del navegador en servidores sin entorno grafico (headless).

### Interfaz de Linea de Comandos (CLI `sentinel`)
El instalador registra el comando `sentinel` de forma nativa en la variable de entorno `PATH` del sistema:

* `sentinel active`: Inicializa y activa los servicios del nodo local en segundo plano.
* `sentinel stop`: Detiene todos los procesos y daemons asociados a SentinelOS.
* `sentinel restart`: Reinicia el backend y los adaptadores de red.
* `sentinel status`: Comprueba el estado de ejecucion, uso de puertos y presencia del proceso principal.
* `sentinel logs`: Muestra el registro de actividad del sistema en tiempo real.
* `sentinel uninstall`: Ejecuta el proceso de desinstalacion completa.

### Desinstalador Atomico
La rutina de desinstalacion (`installer/uninstaller.py`) garantiza la reversion total del entorno:
1. Finalizacion controlada de todos los procesos `uvicorn`, `python` y daemons de Sentinel.
2. Eliminacion de las reglas de firewall creadas en Windows (`netsh`) y Linux (`ufw`).
3. Eliminacion de los accesos directos del escritorio en cualquier plataforma.
4. Supresion de las entradas de registro y variables `PATH` del sistema.
5. Eliminacion de arboles de directorios temporales, archivos de configuracion y cache de compilacion.
6. Sin aperturas forzadas de navegadores web al concluir.

---

## 7. Estructura del Repositorio

```
Sentinel/
├── App.jsx                                 # Componente principal de la interfaz React
├── SentinelCockpit.jsx                     # Panel de telemetria aeroespacial y visualizacion
├── components/
│   └── SentinelCockpit.jsx                 # Componentes modulares del panel de control
├── installer/
│   ├── __init__.py
│   ├── __main__.py                         # Orquestador del proceso de instalacion
│   ├── autostart.py                        # Configuracion de inicio con el sistema
│   ├── cli.py                              # Entrada de comandos globales de terminal (PATH)
│   ├── desktop_shortcut.py                 # Generador multiplataforma de accesos directos
│   ├── firewall.py                         # Gestion de reglas de red y compatibilidad AV
│   ├── node_token.py                       # Generador y validador de tokens Bearer
│   ├── port_guard.py                       # Verificacion y liberacion de puertos en conflicto
│   ├── service_runner.py                   # Lanzador de servicios en segundo plano
│   ├── tailscale.py                        # Vinculacion automatica con red privada cifrada
│   └── uninstaller.py                      # Reversion atomica de cambios en el sistema
├── labsentinel_backend/
│   ├── main.py                             # API FastAPI, WebSocket, beacons UDP y proxy
│   ├── sentinel_service.py                 # Gestion de servicios systemd y monitoreo
│   ├── vault_manager.py                    # Administracion de configuraciones protegidas
│   └── dist/                               # Bundle compilado de produccion del frontend
├── training/
│   ├── agentic_terminal_adapters_1b/       # Checkpoints y pesos LoRA (11,500 steps)
│   │   └── checkpoint-11500/               # Checkpoint final y trainer_state.json
│   ├── train_agentic_terminal_1b.py        # Pipeline de entrenamiento supervisado ReAct
│   ├── comprehensive_test_battery.py       # Suite automatizada de pruebas y calidad
│   └── test_sentinel_inference.py          # Script de validacion de inferencia local
├── export/
│   ├── metrics_report/                     # Graficos comparativos a 300 DPI
│   │   ├── sentinel_comparative_1_loss_convergence.png
│   │   ├── sentinel_comparative_2_noise_stability.png
│   │   └── sentinel_comparative_3_operational_gain.png
│   └── output_gguf/                        # Binarios GGUF cuantizados
├── scratch/
│   ├── update_hp_server.py                 # Script de sincronizacion y despliegue continuo
│   └── web_build/                          # Directorio de construccion Vite del frontend
├── generate_three_deep_comparatives.py     # Generador de analisis comparativos en alta definicion
├── upload_model_hf.py                      # Publicador al Hub de Hugging Face
└── README.md                               # Documentacion tecnica del sistema
```

---

## 8. Despliegue y Puesta en Marcha

### Requisitos del Sistema
* **Sistema Operativo:** Ubuntu 20.04+, Debian 11+, Windows 10/11 (64-bit), macOS Monterey+.
* **Memoria RAM:** Minimo 2 GB (Recomendado 4 GB para ejecucion simultanea de backend y modelo).
* **Almacenamiento:** 1.5 GB de espacio libre en disco.
* **Dependencias:** Python 3.10 o superior, Node.js 18+ (solo para desarrollo de frontend) y Docker (opcional, para aislamiento de Ollama).

### Instrucciones de Instalacion

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/Maurisi0m/SentinelOS.git
   cd SentinelOS
   ```

2. **Instalar dependencias del entorno de ejecucion:**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Ejecutar el instalador del sistema:**
   * En Linux / macOS:
     ```bash
     python -m installer
     ```
   * En Windows:
     ```powershell
     python -m installer
     ```

4. **Operar mediante la linea de comandos global:**
   ```bash
   sentinel active
   sentinel status
   ```

5. **Acceso al Panel de Control:**
   * Abrir en el navegador local: `http://localhost:8001`
   * O acceder a traves del dominio seguro de Tailscale asignado al host.
