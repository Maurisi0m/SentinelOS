#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Dataset Enriquecido en Estructura, Tablas Markdown y Fórmulas LaTeX
para Reentrenamiento de SENTINEL Pure STEM 1B.
"""

import json
import os

SAMPLES = [
    # 1. Termodinámica
    {
        "query": "Explica las cuatro leyes de la termodinámica con sus fórmulas matemáticas exactas y una tabla comparativa.",
        "thought": "El estudiante solicita las cuatro leyes de la termodinámica. Debo estructurar la respuesta con rigor físico formal, especificando el enunciado, la formulación matemática en LaTeX y su significado práctico, cerrando con una tabla comparativa exhaustiva.",
        "answer": """La [[Termodinámica]] es la rama de la física que describe los estados de equilibrio a nivel macroscópico y las transformaciones de energía.

### Leyes Fundamentales de la Termodinámica

1. **Ley Cero (Equilibrio Térmico):**  
   Si dos sistemas están por separado en equilibrio térmico con un tercer sistema, entonces están en equilibrio térmico entre sí. Permite definir la [[Temperatura]]:
   $$T_A = T_C \quad \wedge \quad T_B = T_C \implies T_A = T_B$$

2. **Primera Ley (Conservación de la Energía):**  
   La variación de la energía interna de un sistema termodinámico cerrado es igual a la cantidad de calor transferido al sistema menos el trabajo efectuado por el sistema:
   $$\\Delta U = Q - W$$

3. **Segunda Ley (Entropía y Dirección de Procesos):**  
   En cualquier proceso termodinámico espontáneo en un sistema aislado, la entropía total del sistema y su entorno siempre aumenta o permanece constante:
   $$\\Delta S_{total} \\ge 0, \\quad dS = \\frac{\\delta Q_{rev}}{T}$$

4. **Tercera Ley (Cero Absoluto):**  
   A medida que la temperatura de un cristal perfecto se aproxima al cero absoluto ($0\\text{ K}$), la entropía del sistema tiende a un valor mínimo constante:
   $$\\lim_{T \\to 0} S = 0$$

### Tabla Comparativa de las Leyes Termodinámicas

| Ley | Concepto Físico Principal | Ecuación Fundamental | Variable de Estado Asociada | Implicación Práctica |
| :--- | :--- | :--- | :--- | :--- |
| **Ley Cero** | Equilibrio térmico transitivo | $T_A = T_B$ | [[Temperatura]] ($T$) | Fundamento del funcionamiento del termómetro. |
| **Primera Ley** | Conservación de la energía | $\\Delta U = Q - W$ | [[Energía Interna]] ($U$) | Imposibilidad de máquinas de movimiento perpetuo de 1ª especie. |
| **Segunda Ley** | Irreversibilidad y degradación energética | $\\Delta S \\ge \\int \\frac{dQ}{T}$ | [[Entropía]] ($S$) | Límite máximo de eficiencia para motores térmicos ([[Ciclo de Carnot]]). |
| **Tercera Ley** | Inaccesibilidad del cero absoluto | $\\lim_{T \\to 0} S = 0$ | Entropía residual ($S_0$) | Imposibilidad física de alcanzar $0\\text{ K}$ en pasos finitos. |

Cada una de estas leyes impone restricciones universales sobre el diseño de motores, generadores térmicos y sistemas de refrigeración industrial."""
    },

    # 2. Mecánica Clásica - Energía Cinética y Potencial
    {
        "query": "Calcula la energía cinética y potencial de un cuerpo de 5 kg que cae libremente desde una altura de 20 metros a velocidad de 10 m/s. Muestra el balance en una tabla.",
        "thought": "Se trata de un problema de conservación de la energía mecánica en caída libre. Masa m=5 kg, altura h=20 m, velocidad v=10 m/s. Debo calcular KE y PE y presentar la tabla de balance.",
        "answer": """Para analizar el estado energético del cuerpo utilizamos los principios de la [[Mecánica Clásica]].

### Fórmulas Matemáticas

1. **Energía Cinética ($E_k$):**
   $$E_k = \\frac{1}{2} m v^2$$

2. **Energía Potencial Gravitatoria ($E_p$):**
   $$E_p = m g h$$

3. **Energía Mecánica Total ($E_m$):**
   $$E_m = E_k + E_p$$

Tomando $g = 9.81\\text{ m/s}^2$:
- $E_k = \\frac{1}{2} \\times 5\\text{ kg} \\times (10\\text{ m/s})^2 = 250\\text{ J}$
- $E_p = 5\\text{ kg} \\times 9.81\\text{ m/s}^2 \\times 20\\text{ m} = 981\\text{ J}$
- $E_m = 250\\text{ J} + 981\\text{ J} = 1231\\text{ J}$

### Balance Energético del Sistema

| Parámetro | Símbolo | Expresión Matemática | Valor Calculado | Unidad SI |
| :--- | :--- | :--- | :--- | :--- |
| **Masa del objeto** | $m$ | Dato dado | $5.00$ | $\\text{kg}$ |
| **Velocidad instantánea** | $v$ | Dato dado | $10.00$ | $\\text{m/s}$ |
| **Altura sobre el suelo** | $h$ | Dato dado | $20.00$ | $\\text{m}$ |
| **Aceleración gravitacional** | $g$ | Constante | $9.81$ | $\\text{m/s}^2$ |
| **Energía Cinética** | $E_k$ | $\\frac{1}{2} m v^2$ | $250.00$ | $\\text{Joules (J)}$ |
| **Energía Potencial** | $E_p$ | $m g h$ | $981.00$ | $\\text{Joules (J)}$ |
| **Energía Mecánica Total** | $E_m$ | $E_k + E_p$ | $1231.00$ | $\\text{Joules (J)}$ |

En ausencia de fricción con el aire, la suma $E_m$ permanece invariante a lo largo de toda la trayectoria."""
    },

    # 3. Ley de Ohm y Circuitos
    {
        "query": "Explica la Ley de Ohm, efecto Joule y potencia eléctrica con sus ecuaciones y una tabla de relaciones.",
        "thought": "El usuario consulta sobre las relaciones eléctricas básicas: Ley de Ohm, potencia y efecto Joule. Detallaré las fórmulas en LaTeX y la rueda de fórmulas en una tabla estructurada.",
        "answer": """El comportamiento de circuitos resistivos en corriente continua se rige por la [[Ley de Ohm]] y el principio de disipación térmica de Joule.

### Ecuaciones Fundamentales

1. **Ley de Ohm:** La diferencia de potencial ($V$) es directamente proporcional a la corriente ($I$) y la resistencia ($R$):
   $$V = I \\cdot R$$

2. **Potencia Eléctrica ($P$):**
   $$P = V \\cdot I$$

3. **Efecto Joule (Disipación Térmica):**
   $$P = I^2 \\cdot R = \\frac{V^2}{R}$$

### Tabla de Relaciones y Fórmulas Eléctricas

| Magnitud a Calcular | Símbolo | Fórmula con $V$ e $I$ | Fórmula con $I$ y $R$ | Fórmula con $V$ y $R$ | Unidad SI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Voltaje / Tensión** | $V$ | $V = \\frac{P}{I}$ | $V = I \\cdot R$ | $V = \\sqrt{P \\cdot R}$ | Voltios ($\\text{V}$) |
| **Corriente / Intensidad** | $I$ | $I = \\frac{P}{V}$ | $I = \\frac{V}{R}$ | $I = \\sqrt{\\frac{P}{R}}$ | Amperios ($\\text{A}$) |
| **Resistencia** | $R$ | $R = \\frac{V^2}{P}$ | $R = \\frac{V}{I}$ | $R = \\frac{P}{I^2}$ | Ohmios ($\\Omega$) |
| **Potencia Disipada** | $P$ | $P = V \\cdot I$ | $P = I^2 \\cdot R$ | $P = \\frac{V^2}{R}$ | Vatios ($\\text{W}$) |

Estas expresiones permiten dimensionar resistencias de pull-up, disipadores de calor y fuentes de alimentación en sistemas embebidos."""
    },

    # 4. Klipper y Arquitectura de Impresión 3D
    {
        "query": "Explica la arquitectura interna de Klipper y cómo se comunican Klippy, Moonraker y el MCU. Muestra una tabla comparativa.",
        "thought": "El estudiante pregunta sobre la arquitectura de Klipper. Explicaré el rol del host (Raspberry Pi/servidor), Klippy (Python), Moonraker (servidor de API) y el firmware en el MCU (C), complementando con una tabla de responsabilidades.",
        "answer": """[[Klipper]] es un ecosistema de firmware para impresión 3D que traslada la cinemática pesada y el procesamiento de trayectorias desde el microcontrolador de 8/32 bits hacia una CPU de propósito general.

### Flujo de Datos en el Ecosistema

1. **Host (Klippy):** Proceso en [[Python]] que interpreta G-Code, calcula aceleraciones trapezoidales o con s-curve, gestiona la compensación de resonancias ([[Input Shaping]]) y pre-calcula los pasos de cada motor con precisión de microsegundos.
2. **Moonraker:** Servidor web en Python (Tornado) que expone una API REST y WebSocket entre Klipper y las interfaces de usuario ([[Mainsail]], [[Fluidd]]).
3. **MCU Firmware:** Código optimizado en [[C]] ejecutado en el microcontrolador (STM32, RP2040, ATmega) que solo ejecuta comandos de pasos en instantes de reloj precisos.

### Tabla Arquitectónica de Componentes de Klipper

| Componente | Lenguaje / Runtime | Entorno de Ejecución | Protocolo de Comunicación | Función Crítica |
| :--- | :--- | :--- | :--- | :--- |
| **Klippy** | Python 3 | CPU Host (Linux / Ubuntu) | Socket UNIX (`/tmp/klippy_uds`) | Cinemática, cálculo de pasos, control térmico PID. |
| **Moonraker** | Python 3 (Tornado) | CPU Host (Linux) | HTTP REST / WebSocket (Puerto 7125) | API gateway, gestión de archivos G-Code, cámaras web. |
| **MCU Firmware** | C puro | Microcontrolador (STM32 / RP2040) | USB Serial / UART / CAN-Bus | Generación de pulsos step/dir para drivers paso a paso. |
| **Interfaz (Mainsail/Fluidd)** | JavaScript / Vue / React | Navegador Web | WebSocket hacia Moonraker | Panel de control visual, telemetría y visualización 3D. |

Esta separación evita sobrecargas en la placa controladora y permite velocidades de impresión superiores con menor vibración."""
    },

    # 5. Microcontroladores - Comparativa Hardware
    {
        "query": "Compara las especificaciones de STM32F401, RP2040, ESP32 y ATmega328P en una tabla detallada.",
        "thought": "El usuario necesita comparar los 4 microcontroladores más utilizados en proyectos de laboratorio. Estructuraré la comparativa técnica con arquitectura, frecuencia, memoria, ADC y buses.",
        "answer": """La selección del microcontrolador adecuado para un proyecto STEM depende de los requisitos de procesamiento, consumo, conectividad y número de pines.

### Tabla Comparativa de Microcontroladores

| Característica | ATmega328P (Arduino Uno) | STM32F401 (Black Pill) | RP2040 (Raspberry Pico) | ESP32-WROOM-32 |
| :--- | :--- | :--- | :--- | :--- |
| **Arquitectura** | 8-bit AVR RISC | 32-bit ARM Cortex-M4F | 32-bit Dual ARM Cortex-M0+ | 32-bit Dual Xtensa LX6 |
| **Frecuencia de Reloj** | $16\\text{ MHz}$ | $84\\text{ MHz}$ | $133\\text{ MHz}$ (Overclockable) | $240\\text{ MHz}$ |
| **Memoria Flash** | $32\\text{ KB}$ | $256\\text{ KB}$ | Externa ($2\\text{ MB}$ típ.) | $4\\text{ MB}$ SPI Flash |
| **Memoria SRAM** | $2\\text{ KB}$ | $64\\text{ KB}$ | $264\\text{ KB}$ | $520\\text{ KB}$ |
| **Unidad de Punto Flotante (FPU)** | No (Emulada por software) | Sí (Hardware FPU single-precision) | No | Sí (Hardware FPU) |
| **Conectividad Inalámbrica** | Ninguna | Ninguna | Ninguna (Pico W agrega WiFi) | Wi-Fi $802.11\\text{ b/g/n}$ + Bluetooth 4.2 / BLE |
| **Buses de Comunicación** | 1 UART, 1 SPI, 1 I2C | 3 USART, 3 SPI, 3 I2C, USB OTG | 2 UART, 2 SPI, 2 I2C, 2 PIO | 3 UART, 4 SPI, 2 I2C, 1 CAN (TWAI) |
| **Resolución ADC** | 10-bit (6 canales) | 12-bit (16 canales, $2.4\\text{ MSPS}$) | 12-bit (4 canales) | 12-bit (18 canales SAR) |
| **Voltaje de Operación** | $5.0\\text{ V}$ | $3.3\\text{ V}$ ($5\\text{V}$ tolerant I/O) | $3.3\\text{ V}$ | $3.3\\text{ V}$ |

Para control de motores y Klipper se prefieren [[STM32]] y [[RP2040]] debido a su alta velocidad de reloj y soporte de interrupciones de hardware ultrarrápidas."""
    },

    # 6. Comandos Linux Systemd y Monitorización
    {
        "query": "Explica los comandos esenciales para monitorizar y administrar servicios en Linux Ubuntu con systemctl y journalctl en una tabla.",
        "thought": "El estudiante solicita una guía estructurada de administración de servicios en Linux. Presentaré los comandos en una tabla clara clasificando la acción, la sintaxis y su uso típico.",
        "answer": """En sistemas Linux modernos basados en [[systemd]], la gestión de servicios y el diagnóstico de logs se realiza mediante `systemctl` y `journalctl`.

### Tabla de Comandos de Administración de Servicios

| Acción | Comando Bash | Flags Recomendadas | Descripción / Caso de Uso |
| :--- | :--- | :--- | :--- |
| **Ver estado del servicio** | `systemctl status <servicio>` | `-l --no-pager` | Muestra estado (activo/inactivo), PID y las últimas líneas del registro sin truncar. |
| **Iniciar servicio** | `sudo systemctl start <servicio>` | Ninguna | Arranca el servicio de forma inmediata en segundo plano. |
| **Detener servicio** | `sudo systemctl stop <servicio>` | Ninguna | Envía señal SIGTERM/SIGKILL al proceso para detenerlo. |
| **Reiniciar servicio** | `sudo systemctl restart <servicio>` | Ninguna | Detiene y vuelve a arrancar el daemon (útil tras cambios de configuración). |
| **Recargar configuración** | `sudo systemctl daemon-reload` | Ninguna | Notifica a systemd que vuelva a leer los archivos `.service` en `/etc/systemd/system/`. |
| **Habilitar en el arranque** | `sudo systemctl enable <servicio>` | `--now` (arranca y habilita) | Crea symlinks en `/etc/systemd/system/multi-user.target.wants/` para inicio automático. |
| **Ver logs en tiempo real** | `journalctl -u <servicio> -f` | `-n 50 --no-pager` | Sigue la salida estándar y de error del servicio en tiempo real (similar a `tail -f`). |
| **Ver logs desde el arranque** | `journalctl -u <servicio> -b` | `-p err` (solo errores) | Muestra los eventos registrados únicamente desde el último encendido del servidor. |

Para recargas seguras sin interrumpir clientes conectados (como en Nginx o bases de datos), se puede utilizar `sudo systemctl reload <servicio>` si el servicio soporta recarga en caliente."""
    },

    # 7. Redes y Puertos en Servidor Linux
    {
        "query": "Muestra una tabla con los comandos de red en Linux para auditar puertos abiertos, interfaces y conexiones activas con ss e ip.",
        "thought": "Pregunta de administración de redes en Linux. ss e ip reemplazaron a netstat e ifconfig. Detallaré las flags y comandos en una tabla didáctica.",
        "answer": """Para diagnosticar la red y puertos en un servidor [[Linux]], las herramientas estándar de iproute2 son `ip` y `ss`.

### Tabla de Diagnóstico de Red en Servidor

| Tarea de Diagnóstico | Comando | Flags y Explicación | Salida Esperada |
| :--- | :--- | :--- | :--- |
| **Puertos TCP en escucha** | `ss -tulpn` | `-t` (TCP), `-u` (UDP), `-l` (Listen), `-p` (Proceso), `-n` (Numérico) | Muestra IP, puerto de escucha y PID del daemon que lo tiene abierto. |
| **Conexiones establecidas** | `ss -tan state established` | `-t` (TCP), `-a` (All), `-n` (Numérico) | Lista clientes remotos conectados activamente a servicios del servidor. |
| **Ver direcciones IP e interfaces** | `ip -brief address show` | `-brief` (Formato tabular condensado) | Nombre de interfaz (eth0, wlan0, tailscale0), estado UP/DOWN e IP asignada. |
| **Rutas de enrutamiento** | `ip route show` | Ninguna | Muestra el gateway por defecto (`default via 192.168.1.1 dev eth0`). |
| **Probar resolución DNS** | `resolvectl status` | O `dig +short google.com` | Servidores DNS configurados y tiempos de respuesta de consulta. |
| **Latencia y paquetes perdidos** | `ping -c 4 1.1.1.1` | `-c 4` (Solo 4 paquetes ICMP) | RTT mínimo, medio y máximo con pérdida de paquetes. |

Estos comandos son fundamentales para verificar si servicios como [[Moonraker]] (puerto 7125) o [[llama-server]] (puerto 8080) están accesibles en la red local."""
    },

    # 8. Electromagnetismo - Ecuaciones de Maxwell
    {
        "query": "Explica las cuatro ecuaciones de Maxwell en forma diferencial con sus fórmulas en LaTeX y una tabla resumen.",
        "thought": "El estudiante solicita las Ecuaciones de Maxwell en forma diferencial. Debo detallar la Ley de Gauss eléctrica, Ley de Gauss magnética, Ley de Faraday y Ley de Ampère-Maxwell con tabla comparativa.",
        "answer": """Las cuatro [[Ecuaciones de Maxwell]] unifican la electricidad, el magnetismo y la óptica en un marco coherente de [[Electromagnetismo]].

### Formulación Diferencial

1. **Ley de Gauss para el Campo Eléctrico:**  
   La divergencia del campo eléctrico es proporcional a la densidad de carga volumétrica:
   $$\\nabla \\cdot \\vec{E} = \\frac{\\rho}{\\varepsilon_0}$$

2. **Ley de Gauss para el Campo Magnético:**  
   La divergencia del campo magnético es nula, indicando la ausencia de monopolos magnéticos:
   $$\\nabla \\cdot \\vec{B} = 0$$

3. **Ley de Faraday-Lenz (Inducción):**  
   Un campo magnético variable en el tiempo genera un campo eléctrico rotacional:
   $$\\nabla \\times \\vec{E} = -\\frac{\\partial \\vec{B}}{\\partial t}$$

4. **Ley de Ampère-Maxwell:**  
   Un campo magnético rotacional es generado por corrientes de conducción y por la variación temporal del campo eléctrico ([[Corriente de Desplazamiento]]):
   $$\\nabla \\times \\vec{B} = \\mu_0 \\vec{J} + \\mu_0 \\varepsilon_0 \\frac{\\partial \\vec{E}}{\\partial t}$$

### Tabla Resumen de las Ecuaciones de Maxwell

| Ecuación | Nombre Clásico | Forma Diferencial | Fuente Física | Fenómeno que Explica |
| :--- | :--- | :--- | :--- | :--- |
| **1ª** | [[Ley de Gauss]] | $\\nabla \\cdot \\vec{E} = \\frac{\\rho}{\\varepsilon_0}$ | Carga eléctrica $\\rho$ | Líneas de campo nacen en cargas positivas y mueren en negativas. |
| **2ª** | Gauss Magnético | $\\nabla \\cdot \\vec{B} = 0$ | No existen monopolos | Líneas de campo magnético son cerradas sobre sí mismas. |
| **3ª** | [[Ley de Faraday]] | $\\nabla \\times \\vec{E} = -\\frac{\\partial \\vec{B}}{\\partial t}$ | Flujo magnético variable | Principio de transformadores, alternadores y motores eléctricos. |
| **4ª** | [[Ley de Ampère]]-Maxwell | $\\nabla \\times \\vec{B} = \\mu_0\\vec{J} + \\mu_0\\varepsilon_0\\frac{\\partial\\vec{E}}{\\partial t}$ | Corriente $\\vec{J}$ y $\\frac{\\partial\\vec{E}}{\\partial t}$ | Propagación de ondas electromagnéticas a velocidad de la luz $c = \\frac{1}{\\sqrt{\\mu_0\\varepsilon_0}}$. |

A partir de estas ecuaciones se deduce la velocidad de propagación de las ondas de radio y la luz visible."""
    }
]

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(base_dir, "dataset", "pure_stem_1b_structured.jsonl")
    master_path = os.path.join(base_dir, "dataset", "pure_stem_3b_master.jsonl")
    
    print(f"Cargando dataset maestro desde {master_path}...")
    existing_samples = []
    if os.path.exists(master_path):
        with open(master_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    existing_samples.append(json.loads(line))
    
    print(f"Muestras base existentes: {len(existing_samples)}")
    
    system_prompt = (
        "SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.\n"
        "Tu mision es educar, programar y resolver problemas tecnicos con rigor cientifico, tablas Markdown y precision matematica.\n"
        "DIRECTIVAS: Responde en espanol. Encierra conceptos clave en [[Concepto]]. Expresa formulas en LaTeX ($...$, $$...$$). "
        "Usa tablas Markdown estructuradas para comparar parametros. Prohibido el uso de emojis. Termina con punto final."
    )
    
    new_structured_samples = []
    # Multiplicar los ejemplos estructurados para darle alto peso (strong prior for tables and clean formatting)
    for sample in SAMPLES:
        content_with_thought = f"<pensamiento>\n{sample['thought']}\n</pensamiento>\n\n{sample['answer']}"
        entry = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sample["query"]},
                {"role": "assistant", "content": content_with_thought}
            ]
        }
        # Repetir cada ejemplo con peso para reforzar la atención en Markdown tables
        for _ in range(15):
            new_structured_samples.append(entry)
            
    print(f"Muestras estructuradas con tablas generadas: {len(new_structured_samples)}")
    
    total_dataset = existing_samples + new_structured_samples
    print(f"Dataset consolidado final: {len(total_dataset)} muestras.")
    
    with open(target_path, "w", encoding="utf-8") as out:
        for entry in total_dataset:
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"[EXITO] Dataset guardado en: {target_path}")

if __name__ == "__main__":
    main()
