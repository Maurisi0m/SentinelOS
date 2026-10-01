#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador del Corpus de Calibración para Matriz de Importancia (iMatrix)
Genera benchmark/imatrix_calibration_stem.txt extrayendo texto denso técnico:
- C Bare-Metal & Seguridad de Memoria.
- Hardware ESP32, Raspberry Pi, Arduino & Buses I2C/SPI/UART.
- Leyes físicas de circuitos, condensadores y modulación PWM.
- Bloques de razonamiento <thought> y sintaxis Obsidian [[Concepto]].
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_TXT = os.path.join(BASE_DIR, "benchmark", "imatrix_calibration_stem.txt")

DATASET_FILES = [
    os.path.join(BASE_DIR, "dataset", "ultimate_sentinel_dataset.jsonl"),
    os.path.join(BASE_DIR, "dataset", "dpo_stem_dataset.jsonl"),
]

def build_corpus():
    texts = []

    # 1. Extraer de datasets JSONL
    for dpath in DATASET_FILES:
        if os.path.exists(dpath):
            with open(dpath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if "messages" in data:
                        for m in data["messages"]:
                            texts.append(m.get("content", ""))
                    if "prompt" in data and "chosen" in data:
                        texts.append(data["prompt"])
                        texts.append(data["chosen"])

    # 2. Agregar párrafos densos de electrónica y C para reforzar pesos críticos
    dense_stem_blocks = [
        """
        #include <stdio.h>
        #include <stdlib.h>
        #include <stdint.h>
        #include "esp_system.h"
        #include "driver/gpio.h"
        #include "driver/spi_master.h"

        // Configuración crítica de registros en memoria bare-metal
        typedef struct {
            uint32_t sensor_id;
            float voltage_ch0;
            float current_mA;
            uint64_t timestamp_us;
        } TelemetryFrame;

        TelemetryFrame* allocate_safe_frame(void) {
            TelemetryFrame* frame = (TelemetryFrame*)malloc(sizeof(TelemetryFrame));
            if (frame == NULL) {
                return NULL;
            }
            frame->sensor_id = 0xA5;
            frame->voltage_ch0 = 3.30f;
            frame->current_mA = 12.5f;
            frame->timestamp_us = 0;
            return frame;
        }

        void free_safe_frame(TelemetryFrame** frame_ptr) {
            if (frame_ptr != NULL && *frame_ptr != NULL) {
                free(*frame_ptr);
                *frame_ptr = NULL;
            }
        }
        """,
        """
        ### Leyes de Kirchoff y Diseño de Filtros RC para Sensores I2C
        Para calcular la frecuencia de corte de un filtro pasabajas pasivo:
        fc = 1 / (2 * PI * R * C)
        Si R = 4.7 kOhms (resistencias de pull-up del bus I2C en líneas SDA y SCL a 3.3V) y la capacitancia de la pista es C = 50 pF:
        fc = 1 / (2 * 3.14159265 * 4700 * 50e-12) = 677.25 kHz.
        Como la velocidad Fast Mode de I2C es de 400 kHz, el ancho de banda del bus queda preservado sin distorsión de flancos de subida.
        Pines de bus I2C estándar en ESP32:
        - GPIO 21: SDA (Serial Data)
        - GPIO 22: SCL (Serial Clock)
        Pines prohibidos de Flash SPI interna: GPIO 6, GPIO 7, GPIO 8, GPIO 9, GPIO 10, GPIO 11.
        """,
        """
        <thought>
        1. Comprobar arquitectura de microcontrolador solicitada: ESP32-WROOM-32.
        2. Tensión nominal lógica: 3.3V LVCMOS. Corriente máxima por pin: 12 mA a 20 mA.
        3. El periférico demandado requiere señal PWM para control de velocidad.
        4. Configurar módulo LEDC: ledcAttach(pin, frequency, resolution).
        5. Frecuencia seleccionada: 20 kHz para evitar zumbido audible en el devanado.
        6. Interponer etapa de potencia con transistor MOSFET canal N IRLZ44N y diodo flyback 1N4007.
        </thought>
        """
    ]

    texts.extend(dense_stem_blocks)

    full_text = "\n\n".join(texts)
    os.makedirs(os.path.dirname(OUTPUT_TXT), exist_ok=True)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(full_text)

    size_kb = os.path.getsize(OUTPUT_TXT) / 1024
    print(f"[CORPUS iMATRIX GENERADO]: {OUTPUT_TXT} ({size_kb:.1f} KB, {len(texts)} bloques técnicos)")

if __name__ == "__main__":
    build_corpus()
