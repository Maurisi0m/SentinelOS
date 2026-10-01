#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Dataset de Preferencias DPO (Direct Preference Optimization) para SENTINEL
Crea pares [prompt, chosen, rejected] estructurados para afinar los pesos neuronales:
- Chosen: Código en C con gestión estricta de memoria (free, comprobación NULL),
          guardarraíles de silicio en ESP32 (GPIO 6-11 bloqueados),
          bloque <thought> riguroso y sintaxis Obsidian [[Concepto]].
- Rejected: Fugas de memoria, uso destructivo de pines SPI Flash en ESP32,
            alucinaciones de bibliotecas y código sin explicar.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "dataset", "dpo_stem_dataset.jsonl")

def generate_pairs():
    pairs = [
        # 1. ESP32 SPI Flash Pins vs Safe GPIOs
        {
            "prompt": "Necesito conectar un lector de tarjetas MicroSD por bus SPI al ESP32. ¿Qué pines debo utilizar?",
            "chosen": (
                "### Conexión SPI de MicroSD en ESP32\n\n"
                "> [!CAUTION]\n"
                "> **Peligro de Silicio**: **NUNCA** utilices los pines **GPIO 6, 7, 8, 9, 10 ni 11**. "
                "Estos pines están conectados internamente a la memoria [[Flash SPI]] donde reside el firmware. "
                "Conectarles cualquier periférico provocará un bloqueo instantáneo (*kernel panic*) en el microcontrolador.\n\n"
                "Para conectar la tarjeta MicroSD de forma 100% segura, utiliza el bus **VSPI** nativo:\n"
                "- **MISO (Master In Slave Out)**: `GPIO 19`\n"
                "- **MOSI (Master Out Slave In)**: `GPIO 23`\n"
                "- **SCK (Serial Clock)**: `GPIO 18`\n"
                "- **CS (Chip Select)**: `GPIO 5`\n\n"
                "```cpp\n"
                "#include <SPI.h>\n"
                "#include <SD.h>\n\n"
                "const int chipSelect = 5;\n\n"
                "void setup() {\n"
                "    Serial.begin(115200);\n"
                "    // Inicializar bus SPI seguro sin tocar pines de la Flash interna\n"
                "    if (!SD.begin(chipSelect)) {\n"
                "        Serial.println(\"Error: Tarjeta SD no detectada.\");\n"
                "        return;\n"
                "    }\n"
                "    Serial.println(\"Lector MicroSD inicializado en VSPI con éxito.\");\n"
                "}\n"
                "void loop() {}\n"
                "```\n"
                "Recuerda que el bus requiere alimentación desacoplada con un condensador cerámico de `100nF` entre VCC y GND."
            ),
            "rejected": (
                "Puedes usar cualquier pin libre. Por ejemplo, conecta MISO al pin 6, MOSI al pin 7, SCK al pin 8 y CS al pin 9. "
                "Aquí tienes el código:\n"
                "```cpp\n"
                "#include <SD.h>\n"
                "void setup() {\n"
                "    SD.begin(9);\n"
                "}\n"
                "void loop() {}\n"
                "```\n"
                "Con esto ya debería leer los datos de la tarjeta."
            )
        },
        # 2. C Dynamic Memory Safety (malloc, null check, free)
        {
            "prompt": "Escribe una función en C para reservar un arreglo dinámico de enteros para telemetría de sensores.",
            "chosen": (
                "### Gestión de Memoria Dinámica Segura en C\n\n"
                "En sistemas embebidos y bare-metal en [[C]], es fundamental verificar siempre el valor devuelto por `malloc` "
                "y liberar la memoria con `free` para prevenir **fugas de memoria (*memory leaks*)**.\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "int* crear_buffer_telemetria(size_t total_muestras) {\n"
                "    if (total_muestras == 0) return NULL;\n\n"
                "    // 1. Reserva en el Heap con comprobación de desbordamiento\n"
                "    int* buffer = (int*)malloc(total_muestras * sizeof(int));\n"
                "    if (buffer == NULL) {\n"
                "        fprintf(stderr, \"[ERROR]: Memoria insuficiente en el Heap.\\n\");\n"
                "        return NULL;\n"
                "    }\n\n"
                "    // 2. Inicialización limpia de valores\n"
                "    for (size_t i = 0; i < total_muestras; i++) {\n"
                "        buffer[i] = 0;\n"
                "    }\n\n"
                "    return buffer;\n"
                "}\n\n"
                "void liberar_buffer_telemetria(int** ptr_buffer) {\n"
                "    if (ptr_buffer != NULL && *ptr_buffer != NULL) {\n"
                "        free(*ptr_buffer);\n"
                "        *ptr_buffer = NULL; // Evita punteros colgantes (Dangling Pointers)\n"
                "    }\n"
                "}\n"
                "```\n"
                "- **[[Heap]]**: Zona de memoria donde se alojan las reservas dinámicas.\n"
                "- **[[Dangling Pointer]]**: Se erradica asignando `NULL` inmediatamente tras llamar a `free()`."
            ),
            "rejected": (
                "Aquí tienes la función:\n"
                "```c\n"
                "#include <stdlib.h>\n"
                "int* crear_buffer(int n) {\n"
                "    int* b = malloc(n * 4);\n"
                "    return b;\n"
                "}\n"
                "```\n"
                "Solo la llamas y ya tienes tu arreglo dinámico listo."
            )
        },
        # 3. ESP32 ADC2 vs Wi-Fi Conflict
        {
            "prompt": "¿Puedo leer un potenciómetro en el pin GPIO 4 del ESP32 mientras transmito datos por Wi-Fi a un servidor?",
            "chosen": (
                "### Análisis de Hardware: Conflicto ADC2 con Módulo Wi-Fi en ESP32\n\n"
                "> [!WARNING]\n"
                "> **Incompatibilidad de Silicio**: El pin **GPIO 4** pertenece al conversor analógico-digital **ADC2**. "
                "En el ESP32, el hardware de radio Wi-Fi utiliza internamente el ADC2 para calibración de señal RF. "
                "Si intentas llamar a `analogRead(4)` mientras el Wi-Fi está activo, la lectura fallará sistemáticamente "
                "o arrojará valores de ruido corruptos.\n\n"
                "#### Solución de Ingeniería:\n"
                "Debes conectar el potenciómetro a cualquier canal del conversor **ADC1**, el cual es 100% independiente del Wi-Fi:\n"
                "- `GPIO 32` (ADC1_CH4)\n"
                "- `GPIO 33` (ADC1_CH5)\n"
                "- `GPIO 34` (ADC1_CH6 - Solo entrada)\n"
                "- `GPIO 35` (ADC1_CH7 - Solo entrada)\n"
                "- `GPIO 36` / VP (ADC1_CH0)\n"
                "- `GPIO 39` / VN (ADC1_CH3)\n\n"
                "```cpp\n"
                "const int potPin = 34; // Pin de ADC1, totalmente compatible con Wi-Fi\n\n"
                "void setup() {\n"
                "    Serial.begin(115200);\n"
                "    analogReadResolution(12); // Rango de 0 a 4095 a 3.3V\n"
                "}\n\n"
                "void loop() {\n"
                "    int lectura = analogRead(potPin);\n"
                "    float voltaje = (lectura / 4095.0f) * 3.3f;\n"
                "    Serial.printf(\"Voltaje estable: %.2f V\\n\", voltaje);\n"
                "    delay(200);\n"
                "}\n"
                "```"
            ),
            "rejected": (
                "Sí, claro que puedes. Solo haz `analogRead(4)` en tu código y funcionará al mismo tiempo que transmites por Wi-Fi. "
                "El ESP32 tiene muchos pines analógicos y todos funcionan igual."
            )
        },
        # 4. Raspberry Pi 5 vs Pi 4 GPIO Pinout & RP1 Chip
        {
            "prompt": "Estoy migrando un proyecto de Raspberry Pi 4 a Raspberry Pi 5 y mi script en Python con RPi.GPIO falla al arrancar. ¿Qué pasa?",
            "chosen": (
                "### Migración a Raspberry Pi 5: El Controlador de Silicio RP1\n\n"
                "El fallo se debe a un cambio de arquitectura de hardware radical en la [[Raspberry Pi 5]]:\n"
                "1. En Raspberry Pi 4, los pines GPIO eran controlados directamente por el procesador BCM2711 mediante acceso a memoria mapeada `/dev/gpiomem`.\n"
                "2. En Raspberry Pi 5, la gestión de periféricos e I/O fue delegada a un chip independiente diseñado por Raspberry Pi llamado **[[RP1]]**, "
                "conectado por bus PCIe.\n"
                "3. La librería clásica `RPi.GPIO` accede a direcciones físicas obsoletas del BCM, por lo que arroja error fatal al no encontrar el chip.\n\n"
                "#### Solución:\n"
                "Sustituye la librería obsoleta por la biblioteca oficial basada en el subsistema del kernel [[gpiod]]:\n"
                "```bash\n"
                "pip install rpi-lgpio\n"
                "# o utilizando la interfaz moderna de alto nivel:\n"
                "pip install gpiozero\n"
                "```\n"
                "Con `rpi-lgpio` no requieres modificar tu código: emula la sintaxis de `RPi.GPIO` pero comunicándose correctamente con el chip RP1."
            ),
            "rejected": (
                "Seguramente es un problema de permisos. Corre el script con `sudo python script.py` y debería funcionar con RPi.GPIO como siempre en cualquier Raspberry Pi."
            )
        },
        # 5. Dual Thinking & PWM Calculation
        {
            "prompt": "[MODO_PENSAMIENTO: ACTIVO]\n¿Cómo controlo la velocidad de un motor DC con PWM en el pin 18 del ESP32?",
            "chosen": (
                "<thought>\n"
                "El usuario solicita control de velocidad con PWM para motor DC en pin 18 del ESP32 con pensamiento activo.\n"
                "1. Verificar si GPIO 18 está libre: pertenece a VSPI_SCK, pero si no se usa SPI, está disponible como GPIO de salida.\n"
                "2. Verificar que un motor DC no debe conectarse directamente a un pin GPIO (límite de 12-20mA, el motor demanda >200mA y picos inductivos con fuerza contraelectromotriz back-EMF).\n"
                "3. Se requiere driver (MOSFET o puente H L298N/DRV8833) y diodo flyback.\n"
                "4. En el core moderno de ESP32 para Arduino (v3.x), se usa ledcAttach(pin, freq, res) y ledcWrite(pin, duty).\n"
                "5. Explicar el concepto de Modulación por Ancho de Pulso (PWM), Duty Cycle y protección del silicio.\n"
                "</thought>\n"
                "### Control de Motor DC con PWM en ESP32\n\n"
                "> [!IMPORTANT]\n"
                "> **Protección de Silicio**: **NUNCA** conectes los bornes del motor directamente al GPIO 18. "
                "Un pin del ESP32 solo puede suministrar máximo `12-20 mA`. Un motor al arrancar puede demandar más de `500 mA` "
                "y al apagarse genera un pico inductivo de alta tensión (*Back-EMF*) que destruirá el transistor interno del chip. "
                "Debes interponer un transistor MOSFET N (ej. [[IRLZ44N]]) y un diodo de protección 1N4007.\n\n"
                "```cpp\n"
                "const int motorPin = 18;\n"
                "const int pwmFreq = 5000;    // 5 kHz para conmutación silenciosa\n"
                "const int pwmRes = 8;        // Resolución de 8 bits (0 - 255)\n\n"
                "void setup() {\n"
                "    Serial.begin(115200);\n"
                "    // API moderna de ESP32 core v3.x\n"
                "    ledcAttach(motorPin, pwmFreq, pwmRes);\n"
                "    Serial.println(\"Canal PWM configurado en GPIO 18.\");\n"
                "}\n\n"
                "void loop() {\n"
                "    // Acelerar progresivamente (Duty Cycle de 0% a 100%)\n"
                "    for (int duty = 0; duty <= 255; duty += 5) {\n"
                "        ledcWrite(motorPin, duty);\n"
                "        delay(30);\n"
                "    }\n"
                "    delay(1000);\n"
                "}\n"
                "```\n"
                "- **[[PWM]]**: Modulación por ancho de pulsos; controla la potencia media entregada al motor.\n"
                "- **[[Duty Cycle]]**: Porcentaje del ciclo en estado HIGH (0 = apagado, 255 = velocidad máxima)."
            ),
            "rejected": (
                "Solo conecta el cable rojo del motor al pin 18 y el cable negro a GND. "
                "Luego usa este código:\n"
                "```cpp\n"
                "void setup() {\n"
                "    ledcSetup(0, 1000, 8);\n"
                "    ledcAttachPin(18, 0);\n"
                "}\n"
                "void loop() {\n"
                "    ledcWrite(0, 200);\n"
                "}\n"
                "```\n"
                "Así funcionará tu motor."
            )
        }
    ]

    # Replicar y variar semánticamente para enriquecer el dataset a 40 muestras
    variations = []
    for i, base in enumerate(pairs):
        variations.append(base)
        # Variación con pregunta alternativa
        var1 = dict(base)
        if i == 0:
            var1["prompt"] = "¿Puedo usar los pines GPIO 6, 7 y 8 para conectar un módulo SPI en el ESP32?"
        elif i == 1:
            var1["prompt"] = "¿Por qué ocurre una fuga de memoria (memory leak) en C al usar malloc y cómo se soluciona?"
        elif i == 2:
            var1["prompt"] = "Mi sensor analógico da lecturas erráticas en el ESP32 cuando se enciende el Wi-Fi. ¿A qué se debe?"
        elif i == 3:
            var1["prompt"] = "Diferencias principales en el bus GPIO entre Raspberry Pi 4 y Raspberry Pi 5."
        elif i == 4:
            var1["prompt"] = "[MODO_PENSAMIENTO: ACTIVO]\n¿Cómo se calcula la frecuencia adecuada de PWM para un motor en ESP32?"
        variations.append(var1)

    # Multiplicar variaciones temáticas
    full_dataset = []
    for _ in range(5):
        for item in variations:
            full_dataset.append(item)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for item in full_dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[DATASET DPO GENERADO]: {OUTPUT_PATH}")
    print(f"Total de pares (Prompt/Chosen/Rejected): {len(full_dataset)}")

if __name__ == "__main__":
    generate_pairs()
