#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador del Módulo 13: IoT, Placas de Desarrollo y Conectividad Multiplataforma para SENTINEL
Cubre exhaustivamente:
- Placas: Arduino (AVR/ARM), Raspberry Pi 4/5/Pico, NVIDIA Jetson (Nano/Orin), ESP32 (S3/C3/C6), STM32, Teensy.
- Conectividad en Linux (udev rules, by-id, dmesg, minicom, picocom, screen).
- Conectividad en macOS (/dev/cu.* vs /dev/tty.*, screen, ioreg, system_profiler).
- Conectividad en Windows (PowerShell PnP, .NET SerialPort, plink, drivers CH340/FTDI/CP210x).
- Puenteo de hardware USB hacia WSL2 con usbipd-win.
- Protección eléctrica: Level shifters 3.3V vs 5V, divisores de tensión, límites de corriente GPIO.
- NVIDIA Jetson: Modo Force Recovery, depuración por UART de depuración y SDK JetPack.

Estándares:
- System Prompt minimalista (alineación intrínseca en pesos).
- 0% emojis.
- Sintaxis Obsidian [[Concepto_Clave]].
- Sin Wikipedia (referencias a Datasheets, TRMs oficiales de Espressif, Raspberry Pi, NVIDIA, Microchip, STMicroelectronics).
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset", "specialized_datasets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MINIMAL_SYSTEM_PROMPT = "SENTINEL, sistema operativo cognitivo del Laboratorio STEM."

IOT_CASES = [
    {
        "instruction": "¿Cuáles son las diferencias arquitectónicas, eléctricas y de propósito entre Arduino (ATmega328P), ESP32-S3, Raspberry Pi 5 y NVIDIA Jetson Orin Nano?",
        "response": (
            "En el laboratorio de ingeniería y robótica, la selección de la placa de desarrollo depende de si el requerimiento es control en tiempo real determinista a nivel de registros, conectividad inalámbrica en el borde (*Edge IoT*), procesamiento computacional de propósito general o aceleración de inteligencia artificial:\n\n"
            "### Comparativa Arquitectónica y Eléctrica:\n\n"
            "| Parámetro | [[Arduino_Uno_R3]] | [[ESP32-S3]] | [[Raspberry_Pi_5]] | [[NVIDIA_Jetson_Orin_Nano]] |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **Tipo de Procesador** | Microcontrolador ([[MCU]]) | Microcontrolador ([[MCU]]) | Microcomputador ([[SBC]]) | Módulo de Cómputo IA ([[SOM]]) |\n"
            "| **Arquitectura** | 8-bit AVR ([[ATmega328P]]) | 32-bit Xtensa LX7 Dual-Core | 64-bit ARM Cortex-A76 Quad | 64-bit ARM Cortex-A78AE 6-Core |\n"
            "| **Frecuencia Reloj** | 16 MHz | Hasta 240 MHz | 2.4 GHz | Hasta 1.5 GHz |\n"
            "| **Memoria RAM** | 2 KB SRAM | 512 KB SRAM (+ 8MB PSRAM) | 4 GB u 8 GB LPDDR4X | 4 GB u 8 GB LPDDR5 (68 GB/s) |\n"
            "| **GPU / IA** | Ninguna | Instrucciones SIMD / Vectoriales | VideoCore VII (OpenGL/Vulkan) | GPU NVIDIA Ampere (1024 CUDA Cores + 32 Tensor Cores) |\n"
            "| **Voltaje Lógico GPIO** | **5.0 V** (Tolerante) | **3.3 V** (No tolerante a 5V) | **3.3 V** (No tolerante a 5V) | **3.3 V / 1.8 V** (No tolerante a 5V) |\n"
            "| **Sistema Operativo** | Código Bare-Metal / C++ | FreeRTOS nativo / ESP-IDF | Linux ([[Raspberry_Pi_OS]]) | Linux for Tegra ([[L4T]] / Ubuntu 22.04 LTS) |\n"
            "| **Alimentación Típica** | 7-12V (Vin) o 5V USB (0.2W) | 5V USB (0.5W - 1W) | 5V / 5A USB-C PD (15W - 25W) | 9V - 20V DC Barrel Jack (7W - 15W) |\n\n"
            "### Criterio de Selección Operativo:\n"
            "1. **Arduino Uno / Nano**: Muestreo analógico simple, control de relés y actuadores donde se requiera robustez eléctrica de 5V y tolerancia a sobretensiones accidentales.\n"
            "2. **ESP32-S3**: Nodos de sensores remotos [[IoT]], transmisión de telemetría por [[MQTT]] con cifrado [[TLS_1.3]], periféricos capacitivos y visión por cámara ([[OV2640]]) de bajo costo.\n"
            "3. **Raspberry Pi 5**: Servidor local de laboratorio, brokers Mosquitto centrales, pasarelas web, firmware de control de cinemática [[Klipper]] y controladores de visión básica.\n"
            "4. **NVIDIA Jetson Orin Nano**: Inferencia de modelos de visión artificial en tiempo real (detección de objetos YOLO a 60 FPS, segmentación semántica) y robótica autónoma con ROS 2 ([[Robot_Operating_System]])."
        )
    },
    {
        "instruction": "¿Cómo detectar, diagnosticar permisos y conectarse por terminal a cualquier placa serial (ESP32, Arduino, STM32) en Linux (Bash) sin entornos gráficos?",
        "response": (
            "En sistemas operativos [[Linux]], el kernel expone los convertidores USB a UART (chips [[CH340]], [[CP2102]], [[FT232R]] o USB CDC nativo) bajo el subsistema `tty`.\n\n"
            "### 1. Monitoreo en Tiempo Real de la Conexión Física:\n"
            "Abre una terminal y ejecuta el visor de eventos del kernel antes de enchufar la placa:\n"
            "```bash\n"
            "sudo dmesg -wH\n"
            "```\n"
            "Al conectar el dispositivo, el subsistema USB emitirá trazas similares a:\n"
            "`usb 1-2: ch341-uart converter now attached to ttyUSB0` o `cdc_acm 1-2:1.0: ttyACM0: USB ACM device`.\n\n"
            "### 2. Identificación Inmutable por Identificador de Hardware (/dev/serial/by-id/):\n"
            "Nunca se debe fiar de nombres volátiles como `/dev/ttyUSB0` o `/dev/ttyUSB1`, ya que su orden cambia si se reinicia el equipo con múltiples placas conectadas. Se utiliza la ruta canónica por identificador de hardware:\n"
            "```bash\n"
            "ls -la /dev/serial/by-id/\n"
            "# Salida: usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 -> ../../ttyUSB0\n"
            "```\n\n"
            "### 3. Solución Definitiva de Permisos sin 'chmod 777' (Grupo dialout y Reglas udev):\n"
            "```bash\n"
            "# Añadir el usuario al grupo con privilegios sobre la interfaz serial\n"
            "sudo usermod -aG dialout $USER\n"
            "newgrp dialout\n"
            "\n"
            "# Crear regla udev para garantizar permisos 0666 a programadores USB (ejemplo CH340: Vendor 1a86, Product 7523)\n"
            "sudo tee /etc/udev/rules.d/99-serial-lab.rules << 'EOF'\n"
            "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"1a86\", ATTRS{idProduct}==\"7523\", MODE=\"0666\", GROUP=\"dialout\"\n"
            "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"10c4\", ATTRS{idProduct}==\"ea60\", MODE=\"0666\", GROUP=\"dialout\"\n"
            "EOF\n"
            "sudo udevadm control --reload-rules && sudo udevadm trigger\n"
            "```\n\n"
            "### 4. Conexión de Terminal por Terminal CLI:\n"
            "Utilizando herramientas especializadas de consola:\n"
            "```bash\n"
            "# Con picocom (Recomendado para desarrollo de microcontroladores):\n"
            "# --echo-newline (-c): emula retorno de carro\n"
            "# Para salir: Ctrl+A seguido de Ctrl+X\n"
            "picocom -b 115200 /dev/serial/by-id/usb-Silicon_Labs_CP2102* -c\n"
            "\n"
            "# Con screen (Alternativa universal instalada por defecto):\n"
            "# Para salir: Ctrl+A seguido de '\\' (confirmar con 'y')\n"
            "screen /dev/ttyUSB0 115200\n"
            "```"
        )
    },
    {
        "instruction": "¿Cómo detectar y abrir una consola serial con una placa de desarrollo en macOS (Zsh) y cuál es la diferencia crítica entre los dispositivos /dev/tty.* y /dev/cu.*?",
        "response": (
            "En [[macOS]] (basado en el kernel Darwin/BSD), la pila de controladores seriales implementa una distinción histórica de telefonía y módems que causa bloqueos comunes si no se comprende adecuadamente.\n\n"
            "### 1. La Diferencia Crítica: `/dev/tty.*` frente a `/dev/cu.*`:\n"
            "- **`/dev/tty.usbserial-*` (Teletype / Inbound)**: Diseñado históricamente para recibir llamadas telefónicas entrantes en módems. Al abrir este descriptor en el sistema operativo, la llamada bloquea el proceso hasta que la línea de hardware detecta la señal [[DCD]] (*Data Carrier Detect*). En un microcontrolador que no maneja señal DCD por hardware, abrir este puerto deja la terminal permanentemente congelada.\n"
            "- **`/dev/cu.usbserial-*` (Calling Unit / Outbound)**: Diseñado para realizar llamadas salientes. **Ignora por completo la señal DCD** y abre el descriptor de archivo de forma inmediata sin esperar señales de portadora telefónica. **En macOS se debe usar siempre `/dev/cu.*` para conectar a microcontroladores.**\n\n"
            "### 2. Detección de Dispositivos Conectados en Terminal (Zsh):\n"
            "```bash\n"
            "# Listar todas las interfaces seriales USB Calling Unit conectadas\n"
            "ls -la /dev/cu.*\n"
            "# Salidas típicas:\n"
            "# /dev/cu.usbserial-0001 (Controladores FTDI / Silicon Labs CP2102)\n"
            "# /dev/cu.usbmodem1101   (Arduino Uno R4 / ESP32-S3 USB CDC nativo)\n"
            "# /dev/cu.wchusbserial*  (Controladores económicos CH340)\n"
            "\n"
            "# Inspeccionar árbol de dispositivos USB a nivel de hardware en macOS:\n"
            "system_profiler SPUSBDataType | grep -A 8 -B 2 -E 'CH340|CP210|FT232|USB Serial'\n"
            "```\n\n"
            "### 3. Apertura de Terminal de Telemetría con Screen:\n"
            "```bash\n"
            "# Conexión a 115200 baudios\n"
            "screen /dev/cu.usbserial-0001 115200\n"
            "```\n\n"
            "### 4. Salida Limpia para Evitar el Bloqueo del Puerto ('Resource Busy'):\n"
            "Si cierras la ventana de la terminal de macOS sin desconectar `screen`, el proceso queda huérfano y retiene el descriptor con el error `Resource busy`.\n"
            "- **Salida correcta**: Presiona la combinación `Ctrl + A` y luego escribe `\\` (barra invertida), confirmando con `y`.\n"
            "- **Recuperación si el puerto quedó tomado**: Busca el PID del proceso colgado y termínalo:\n"
            "```bash\n"
            "lsof | grep /dev/cu.usbserial\n"
            "kill -9 <PID_DETECTADO>\n"
            "```"
        )
    },
    {
        "instruction": "¿Cómo interactuar con placas seriales en Windows mediante PowerShell sin software de terceros, y cómo puentear dispositivos USB físicos hacia WSL2 con usbipd?",
        "response": (
            "En entornos de desarrollo sobre [[Windows]], la interacción con placas embebidas puede realizarse de forma nativa en [[PowerShell]] o canalizándola hacia máquinas virtuales [[WSL2]] mediante redirección de bus USB sobre IP.\n\n"
            "### 1. Detección de Puertos COM en PowerShell:\n"
            "```powershell\n"
            "# Inspeccionar puertos COM activos y descripción de controladores Plug-and-Play\n"
            "Get-PnpDevice -Class 'Ports' -Status OK | Select-Object Name, DeviceID\n"
            "\n"
            "# Obtener únicamente los nombres de puerto serial disponibles en .NET\n"
            "[System.IO.Ports.SerialPort]::GetPortNames()\n"
            "```\n\n"
            "### 2. Lectura y Escritura por Terminal Nativa en PowerShell (.NET):\n"
            "```powershell\n"
            "$portName = \"COM4\"\n"
            "$baudRate = 115200\n"
            "$serial = New-Object System.IO.Ports.SerialPort $portName, $baudRate, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One\n"
            "$serial.ReadTimeout = 3000\n"
            "\n"
            "try {\n"
            "    $serial.Open()\n"
            "    Write-Host \"[CONECTADO] Escuchando telemetría en $portName... (Ctrl+C para detener)\"\n"
            "    while ($true) {\n"
            "        try {\n"
            "            $line = $serial.ReadLine()\n"
            "            Write-Host \"[TELEMETRÍA] $line\"\n"
            "        } catch [TimeoutException] {\n"
            "            # Continuar esperando datos si el microcontrolador envía de forma esporádica\n"
            "        }\n"
            "    }\n"
            "} finally {\n"
            "    $serial.Close()\n"
            "    $serial.Dispose()\n"
            "    Write-Host \"[INFO] Puerto serial cerrado de forma segura.\"\n"
            "}\n"
            "```\n\n"
            "### 3. Conexión y Puenteo de Dispositivos USB hacia WSL2 con `usbipd-win`:\n"
            "Para programar un ESP32 o Arduino con herramientas de Linux (`esptool.py`, `avrdude`) directamente dentro de WSL2:\n\n"
            "1. **En PowerShell con privilegios de Administrador (Host Windows)**:\n"
            "```powershell\n"
            "# Listar dispositivos USB conectados y sus identificadores de bus (BUSID)\n"
            "usbipd list\n"
            "\n"
            "# Vincular el bus del adaptador serial (ejemplo BUSID 1-4)\n"
            "usbipd bind --busid 1-4\n"
            "\n"
            "# Adjuntar el dispositivo a la instancia activa de WSL2\n"
            "usbipd attach --wsl --busid 1-4\n"
            "```\n\n"
            "2. **Dentro de la terminal de WSL2 (Linux)**:\n"
            "```bash\n"
            "# Verificar que el hardware USB fue transferido al kernel de Linux en WSL2\n"
            "lsusb\n"
            "ls -la /dev/ttyUSB* /dev/ttyACM*\n"
            "```\n\n"
            "3. **Desconexión al terminar (en Windows)**:\n"
            "```powershell\n"
            "usbipd detach --busid 1-4\n"
            "```"
        )
    },
    {
        "instruction": "Explica el peligro de conectar un Arduino de 5V a un ESP32 o Raspberry Pi de 3.3V, y cómo diseñar un convertidor de nivel lógico (Level Shifter) con MOSFETs BSS138 o divisores resistivos.",
        "response": (
            "Los microcontroladores y computadores monoplaca modernos ([[ESP32]], [[Raspberry_Pi]], [[STM32]], [[RP2040]]) operan con lógica [[CMOS]] de **3.3 V** (o inferior). "
            "Sus pines de entrada y salida ([[GPIO]]) integran diodos internos de protección contra descargas electrostáticas ([[ESD]]) conectados entre el pin y el riel $V_{DD}$ (3.3V).\n\n"
            "### Mecanismo Físico de Destrucción Eléctrica:\n"
            "Si se conecta directamente una salida digital en estado ALTO de 5V (ej. el pin TX de un [[Arduino_Uno]]) a un pin de 3.3V de un ESP32:\n"
            "1. El voltaje de 5V supera el potencial de ruptura del diodo de fijación interno ($V_{DD} + 0.3\\text{V} = 3.6\\text{V}$).\n"
            "2. El diodo entra en conducción directa no controlada, derivando corrientes destructivas (de decenas a cientos de miliamperios) hacia el regulador interno de 3.3V.\n"
            "3. Se produce una avalancha térmica (*Thermal Runaway*) o ruptura dieléctrica de la compuerta de óxido de silicio ([[SiO2]]), destruyendo permanentemente el pin GPIO o quemando el procesador.\n\n"
            "### Solución 1: Divisor de Tensión Resistivo (Unidireccional - ej. Señales TX de 5V a RX de 3.3V):\n"
            "Para señales unidireccionales de baja a media frecuencia (como líneas UART):\n"
            "```text\n"
            "Señal 5V (TX Arduino) ----[ R1: 1.8 kΩ ]----+----> Señal 3.3V (RX ESP32)\n"
            "                                             |\n"
            "                                        [ R2: 3.3 kΩ ]\n"
            "                                             |\n"
            "                                            GND (Tierra común obligatoria)\n"
            "```\n"
            "Cálculo analítico por ley de Ohm:\n"
            "$$V_{out} = V_{in} \\cdot \\frac{R_2}{R_1 + R_2} = 5.0\\text{ V} \\cdot \\frac{3300}{1800 + 3300} = 5.0 \\cdot \\frac{3300}{5100} \\approx 3.235\\text{ V}$$\n"
            "Este valor se sitúa dentro de la región segura de nivel lógico alto ($0.7 \\cdot V_{DD} \\le V_{IH} \\le V_{DD}$).\n\n"
            "### Solución 2: Convertidor Bidireccional Activo con MOSFET ([[BSS138]]) para buses I2C:\n"
            "En buses bidireccionales con drenador abierto ([[Open-Drain]]) como [[I2C]] (líneas SDA y SCL), un divisor resistivo falla porque la línea debe transmitir en ambos sentidos. Se utiliza un transistor MOSFET de canal N:\n"
            "```text\n"
            "             3.3V (LV)                         5.0V (HV)\n"
            "                |                                 |\n"
            "             [10kΩ]                            [10kΩ]\n"
            "                |                                 |\n"
            "Línea 3.3V <----+--- (Source) [ MOSFET N ] (Drain) +----> Línea 5.0V\n"
            "                              (Gate) |\n"
            "                                     |\n"
            "                                    3.3V\n"
            "```\n\n"
            "- **Estado Reposo (Ambos lados en ALTO)**: La compuerta (Gate) y la fuente (Source) están a 3.3V ($V_{GS} = 0\\text{V}$). El transistor está en corte; cada línea se eleva a su respectivo riel mediante sus resistencias pull-up.\n"
            "- **El lado de 3.3V conmuta a BAJO (0V)**: $V_S = 0\\text{V}$, $V_G = 3.3\\text{V} \\implies V_{GS} = 3.3\\text{V} > V_{th}$. El canal se activa y drena la línea de 5V a tierra (0V).\n"
            "- **El lado de 5V conmuta a BAJO (0V)**: El diodo de cuerpo (*body diode*) del MOSFET entra en conducción polarizado en directa, bajando el lado de 3.3V a ~0.6V; inmediatamente $V_{GS}$ supera el umbral y el canal N se satura, llevando el lado de 3.3V a 0V pleno."
        )
    },
    {
        "instruction": "¿Cómo configurar y depurar una placa NVIDIA Jetson (Orin Nano / Nano) mediante su puerto serie UART de depuración y flashearla en modo Force Recovery?",
        "response": (
            "Las plataformas de cómputo embebido [[NVIDIA_Jetson]] no utilizan BIOS convencional x86, sino un microcódigo de arranque escalonado ([[Tegra_Bootloader]]) gestionado por microcontroladores internos (*Boot ROM* -> *Tegra Bootloader* -> *UEFI* -> *Kernel Linux*).\n\n"
            "### 1. Conexión a la Consola Serial de Depuración (UART Debug Header):\n"
            "En caso de que el sistema operativo no arranque la interfaz de red o el servidor gráfico X11/Wayland colapse, la consola serie expone todos los mensajes de arranque del kernel antes del init de systemd:\n\n"
            "- **Cabecera de Pines de Depuración (ej. J44 o conector de 12 pines según placa)**:\n"
            "  - Pin TX de la Jetson $\\rightarrow$ Pin RX del convertidor USB-TTL (3.3V).\n"
            "  - Pin RX de la Jetson $\\rightarrow$ Pin TX del convertidor USB-TTL (3.3V).\n"
            "  - Pin GND de la Jetson $\\rightarrow$ Pin GND del convertidor (Tierra de referencia obligatoria).\n"
            "  - **¡NUNCA conectar el pin VCC/5V del cable!** Se alimenta la Jetson exclusivamente por su conector DC dedicado.\n\n"
            "Parámetros de conexión serial:\n"
            "- Baudios: **115200**\n"
            "- Bits de datos: **8**, Paridad: **Ninguna**, Bits de parada: **1**, Control de flujo: **Ninguno**.\n"
            "Comando en Linux/macOS: `picocom -b 115200 /dev/ttyUSB0` o `screen /dev/cu.usbserial-0001 115200`.\n\n"
            "### 2. Procedimiento para Entrar en Modo 'Force Recovery' (Flasheo de Firmware):\n"
            "El modo de recuperación por hardware permite transferir la imagen base del sistema operativo [[JetPack]] y el árbol de dispositivos ([[Device_Tree]] / `.dtb`) desde una computadora host (Ubuntu x86_64) hacia el chip eMMC o unidad NVMe M.2:\n\n"
            "1. Apagar la alimentación eléctrica de la Jetson.\n"
            "2. Localizar la cabecera de botones de la placa (Header de pines para Power, Reset y Recovery).\n"
            "3. Conectar mediante un puente físico (*jumper*) el pin **FC REC** (*Force Recovery*) con **GND**.\n"
            "4. Conectar el cable USB de datos (USB-C o Micro-USB) desde el puerto OTG de la Jetson hacia la PC host.\n"
            "5. Aplicar alimentación eléctrica (botón Power).\n"
            "6. Retirar el jumper entre FC REC y GND tras 2 segundos.\n\n"
            "### 3. Verificación en la Computadora Host Linux:\n"
            "```bash\n"
            "# Verificar que el chip de NVIDIA Tegra fue reconocido en modo APX Recovery\n"
            "lsusb | grep -i 'Nvidia Corp.'\n"
            "# Salida esperada: ID 0955:7023 NVidia Corp. (El ID de producto varía según el chip Orin/Xavier/Nano)\n"
            "```\n\n"
            "Una vez verificado el ID `0955:XXXX`, se puede ejecutar el script de flasheo del SDK Manager o la utilidad por línea de comandos:\n"
            "```bash\n"
            "sudo ./flash.sh jetson-orin-nano-devkit mmcblk0p1\n"
            "```"
        )
    }
]

def generate_iot_dataset():
    print("=== GENERANDO MÓDULO 13: IOT Y PLACAS DE DESARROLLO PARA SENTINEL ===")
    key = "13_iot_hardware_and_board_connections"
    jsonl_path = os.path.join(OUTPUT_DIR, f"{key}.jsonl")
    txt_path = os.path.join(OUTPUT_DIR, f"{key}.txt")

    with open(jsonl_path, "w", encoding="utf-8") as f_jsonl:
        for item in IOT_CASES:
            entry = {
                "messages": [
                    {"role": "system", "content": MINIMAL_SYSTEM_PROMPT},
                    {"role": "user", "content": item["instruction"]},
                    {"role": "assistant", "content": item["response"]}
                ]
            }
            f_jsonl.write(json.dumps(entry, ensure_ascii=False) + "\n")

    with open(txt_path, "w", encoding="utf-8") as f_txt:
        f_txt.write(f"# DATASET ESPECIALIZADO: {key.upper()}\n")
        f_txt.write("=" * 80 + "\n")
        f_txt.write("IOT, CONEXIONES A ARDUINO, RASPBERRY PI, NVIDIA JETSON, ESP32 Y STM32.\n")
        f_txt.write("CONECTIVIDAD EN WINDOWS, LINUX (BASH), MACOS Y GESTIÓN ELÉCTRICA DE SEÑALES.\n")
        f_txt.write("=" * 80 + "\n\n")
        for idx, item in enumerate(IOT_CASES, 1):
            f_txt.write(f"## CASO {idx}: {item['instruction']}\n\n")
            f_txt.write(f"{item['response']}\n\n")
            f_txt.write("-" * 80 + "\n\n")

    size_jsonl = os.path.getsize(jsonl_path)
    size_txt = os.path.getsize(txt_path)
    print(f"[OK] {key} -> {len(IOT_CASES)} pares | JSONL: {size_jsonl} B | TXT: {size_txt} B")

if __name__ == "__main__":
    generate_iot_dataset()
