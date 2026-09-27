# Gran Benchmark Comparativo en CPU (Simulación Servidor HP Intel Core i5)
**Condiciones de Silicio**: 100% CPU (`-ngl 0`, 0 MB VRAM) | 4 Hilos OpenMP (`-t 4`) | Flash Attention CPU (`--flash-attn on`) | KV Cache Q8 (`-ctk q8_0 -ctv q8_0`)
---
## 1. Resumen Global de Rendimiento y Calidad
| Modelo | Vel. Prompt Media | Vel. Generación Media | Precisión Técnica Media | Enlaces Obsidian Medios | CoT Reflexivo |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Base Llama-3.2-3B Instruct** | 65.5 tok/s | **18.7 tok/s** | **80.8%** | 1.0 | ❌ No |
| **Sentinel-STEM (SFT)** | 67.4 tok/s | **18.8 tok/s** | **56.7%** | 3.0 | ❌ No |
| **Sentinel-Root-Pruned (26L)** | 71.4 tok/s | **20.1 tok/s** | **65.8%** | 5.7 | ❌ No |
| **Sentinel-Master-Ultimate (Todos los Tweaks)** | 67.9 tok/s | **18.9 tok/s** | **87.5%** | 3.7 | ❌ No |
| **Sentinel-Master + Draft 1B (Speculative)** | 55.3 tok/s | **18.0 tok/s** | **70.0%** | 3.3 | ❌ No |

---
## 2. Desglose: Nivel 1 (Básico - Linux & Bash)
> **Prompt**: *Explica qué es Bash y cómo navegar por la terminal en Linux. Detalla los comandos fundamentales para moverte por el sistema de archivos (pwd, ls, cd), crear y manipular archivos (mkdir, touch, cp, mv, rm), con ejemplos claros paso a paso para un estudiante de laboratorio STEM.*

| Modelo | Tiempo Total | Vel. Prompt | Vel. Generación | Precisión | Obsidian | CoT |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Base Llama-3.2-3B Instruct | 29.3s | 62.8 tok/s | **18.4 tok/s** | 100.0% | 1 | ❌ |
| Sentinel-STEM (SFT) | 26.13s | 64.1 tok/s | **18.4 tok/s** | 100.0% | 4 | ❌ |
| Sentinel-Root-Pruned (26L) | 23.53s | 72.2 tok/s | **19.6 tok/s** | 100.0% | 5 | ❌ |
| Sentinel-Master-Ultimate (Todos los Tweaks) | 25.14s | 67.3 tok/s | **18.4 tok/s** | 100.0% | 9 | ❌ |
| Sentinel-Master + Draft 1B (Speculative) | 36.91s | 55.7 tok/s | **17.6 tok/s** | 100.0% | 8 | ❌ |

### Respuestas Generadas en este Nivel:
#### 🔹 Base Llama-3.2-3B Instruct
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Explica qué es Bash y cómo navegar por la terminal en Linux. Detalla los comandos fundamentales para moverte por el sistema de archivos (pwd, ls, cd), crear y manipular archivos (mkdir, touch, cp, mv, rm), con ejemplos claros paso a ... (truncated)
**Bash y Navegación en la Terminal**
Bash (Bourne-Again SHell) es un sistema operativo de línea de comandos (shell) que se utiliza en Linux y otros sistemas operativos. Es un entorno de línea de comandos que permite a los usuarios interactuar con el sistema operativo y realizar tareas administrativas y de programación.
**Navegación en la Terminal**
La terminal es la ventana donde se ejecutan los comandos Bash. Para navegar por la terminal, debes conocer algunos comandos fundamentales. A continuación, te explicaré cómo hacerlo:
...
```
#### 🔹 Sentinel-STEM (SFT)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Explica qué es Bash y cómo navegar por la terminal en Linux. Detalla los comandos fundamentales para moverte por el sistema de archivos (pwd, ls, cd), crear y manipular archivos (mkdir, touch, cp, mv, rm), con ejemplos claros paso a ... (truncated)
### Introducción a Bash y Terminal en Linux
Bash (Bourne-Again SHell) es el shell por defecto en sistemas operativos [[Linux]] y macOS. Su nombre proviene de la evolución del shell original [[Bourne]] y el reenfocado en seguridad ([[POSIX]]).
### 1. Navegación de Directorios (`cd`, `pwd`, `ls`)
#### 1.1 `cd` (Change Directory):
...
```
#### 🔹 Sentinel-Root-Pruned (26L)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Explica qué es Bash y cómo navegar por la terminal en Linux. Detalla los comandos fundamentales para moverte por el sistema de archivos (pwd, ls, cd), crear y manipular archivos (mkdir, touch, cp, mv, rm), con ejemplos claros paso a ... (truncated)
### 1. [[Concepto]]: [[Dirigir_Diretorias]] (cd)
```bash
cd /var/www/html
cd /opt/stemlab
...
```
#### 🔹 Sentinel-Master-Ultimate (Todos los Tweaks)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Explica qué es Bash y cómo navegar por la terminal en Linux. Detalla los comandos fundamentales para moverte por el sistema de archivos (pwd, ls, cd), crear y manipular archivos (mkdir, touch, cp, mv, rm), con ejemplos claros paso a ... (truncated)
### Introducción a [[Bash]] y Navegación en la Terminal de [[Linux]]
En el ecosistema de desarrollo de [[Sistemas Embebidos]] y laboratorio, la terminal es la consola que conoce. [[Bash]] (Batch en inglés) es el sistema de control de línea que ejecuta comandos para el procesador [[CPU]] directamente.
#### 1. ¿Qué es [[Bash]]?
- [[Bash]] es un intérprete de comandos que lee una línea de comandos de teclado, la ejecuta y muestra la salida en la pantalla.
...
```
#### 🔹 Sentinel-Master + Draft 1B (Speculative)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Explica qué es Bash y cómo navegar por la terminal en Linux. Detalla los comandos fundamentales para moverte por el sistema de archivos (pwd, ls, cd), crear y manipular archivos (mkdir, touch, cp, mv, rm), con ejemplos claros paso a ... (truncated)
### Introducción a [[Bash]] y Navegación en la Terminal de [[Linux]]
En el ecosistema de desarrollo de [[Sistemas Embebidos]] y laboratorio, la terminal es el centro de control donde se ejecutan comandos, se mueven archivos y se monitorean periféricos. [[Bash]] (Batch en inglés) es el lenguaje de ejecución por lineas que actúa como interfaz entre el usuario y el [[Kernel]].
#### 1. ¿Qué es [[Bash]]?
[[Bash]] es un intérprete de comandos que ejecuta instrucciones de laboratorio, automatizando flujos de trabajo y procesando datos en masa. Su sintaxis única combina comandos de sistema con variables, condicionales y bucles en un lenguaje legible y eficiente.
...
```

---
## 2. Desglose: Nivel 2 (Intermedio - Programación C & Gestión de Memoria)
> **Prompt**: *Escribe una función en C para implementar un búfer dinámico que se duplique automáticamente cuando esté lleno. Explica en detalle por qué la asignación directa 'ptr = realloc(ptr, new_size)' es una vulnerabilidad crítica, cómo evitar fugas de memoria si realloc devuelve NULL usando un puntero temporal, y añade la validación de punteros nulos.*

| Modelo | Tiempo Total | Vel. Prompt | Vel. Generación | Precisión | Obsidian | CoT |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Base Llama-3.2-3B Instruct | 25.62s | 66.0 tok/s | **18.9 tok/s** | 80.0% | 1 | ❌ |
| Sentinel-STEM (SFT) | 25.38s | 71.4 tok/s | **19.2 tok/s** | 20.0% | 1 | ❌ |
| Sentinel-Root-Pruned (26L) | 23.71s | 68.3 tok/s | **20.2 tok/s** | 60.0% | 5 | ❌ |
| Sentinel-Master-Ultimate (Todos los Tweaks) | 23.91s | 68.3 tok/s | **19.4 tok/s** | 100.0% | 1 | ❌ |
| Sentinel-Master + Draft 1B (Speculative) | 37.09s | 51.3 tok/s | **18.4 tok/s** | 60.0% | 1 | ❌ |

### Respuestas Generadas en este Nivel:
#### 🔹 Base Llama-3.2-3B Instruct
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Escribe una función en C para implementar un búfer dinámico que se duplique automáticamente cuando esté lleno. Explica en detalle por qué la asignación directa 'ptr = realloc(ptr, new_size)' es una vulnerabilidad crítica, cóm ... (truncated)
**Implementación de un búfer dinámico en C**
A continuación, se presenta una función en C que implementa un búfer dinámico que se duplica automáticamente cuando esté lleno. La función utiliza la función `realloc` para reasignar la memoria del búfer.
```c
#include <stdio.h>
...
```
#### 🔹 Sentinel-STEM (SFT)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Escribe una función en C para implementar un búfer dinámico que se duplique automáticamente cuando esté lleno. Explica en detalle por qué la asignación directa 'ptr = realloc(ptr, new_size)' es una vulnerabilidad crítica, cóm ... (truncated)
Implementación segura de búfer dinámico en C:
```c
#include <stdio.h>
#include <stdlib.h>
...
```
#### 🔹 Sentinel-Root-Pruned (26L)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Escribe una función en C para implementar un búfer dinámico que se duplique automáticamente cuando esté lleno. Explica en detalle por qué la asignación directa 'ptr = realloc(ptr, new_size)' es una vulnerabilidad crítica, cóm ... (truncated)
Concepto fundamental: [[Realloc]] (Reallocation) opera mediante [[Reassignamiento_de_Memory]] ([[Reassignamiento_Seguro]]):
```c
void* realloc(void* ptr, size_t size) {
    size_t new_size = size;
...
```
#### 🔹 Sentinel-Master-Ultimate (Todos los Tweaks)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Escribe una función en C para implementar un búfer dinámico que se duplique automáticamente cuando esté lleno. Explica en detalle por qué la asignación directa 'ptr = realloc(ptr, new_size)' es una vulnerabilidad crítica, cóm ... (truncated)
### Gestión Segura de Memoria con realloc en C
La asignación directa de `ptr = realloc(ptr, new_size)` es una vulnerabilidad crítica que conduce a fugas de memoria si `realloc` devuelve `NULL`. A continuación, se explica por qué y cómo mitigar el riesgo.
#### 1. La Vulnerabilidad de la Asignación Directa
Cuando `realloc` no encuentra memoria contigua disponible en el heap, devuelve `NULL`. Sin embargo, la sintaxis común en C impide el bloqueeo de la ejecución:
...
```
#### 🔹 Sentinel-Master + Draft 1B (Speculative)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Escribe una función en C para implementar un búfer dinámico que se duplique automáticamente cuando esté lleno. Explica en detalle por qué la asignación directa 'ptr = realloc(ptr, new_size)' es una vulnerabilidad crítica, cóm ... (truncated)
### Gestión Segura de Memoria con realloc en C
La asignación directa de `ptr = realloc(ptr, new_size)` es una vulnerabilidad crítica que conduce a fugas de memoria si `realloc` devuelve `NULL`. A continuación, se explica por qué y cómo mitigar el riesgo.
#### 1. La Vulnerabilidad de la Asignación Directa
Cuando se llama a `realloc`, si el bloque de memoria original no puede ser reemplazado por un bloque más grande, devuelve `NULL`. Sin embargo, la sintaxis común en C impide el return value:
...
```

---
## 2. Desglose: Nivel 3 (Avanzado - Arquitectura ESP32, I2C, FreeRTOS & Física)
> **Prompt**: *Diseña una tarea en FreeRTOS para un ESP32 que lea por bus I2C un sensor a 100 kHz y calcule el valor RMS de una señal sinusoidal muestreada. Explica las restricciones físicas del hardware: 1) por qué se requieren resistencias de pull-up externas y qué ocurre si se usa un valor muy alto como 100k, 2) por qué los pines GPIO 6 a 11 están estrictamente prohibidos para periféricos, y 3) cómo evitar que el Watchdog Timer (WDT) reinicie el microcontrolador durante el procesamiento.*

| Modelo | Tiempo Total | Vel. Prompt | Vel. Generación | Precisión | Obsidian | CoT |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Base Llama-3.2-3B Instruct | 28.9s | 67.7 tok/s | **18.7 tok/s** | 62.5% | 1 | ❌ |
| Sentinel-STEM (SFT) | 27.84s | 66.8 tok/s | **18.8 tok/s** | 50.0% | 4 | ❌ |
| Sentinel-Root-Pruned (26L) | 25.98s | 73.6 tok/s | **20.4 tok/s** | 37.5% | 7 | ❌ |
| Sentinel-Master-Ultimate (Todos los Tweaks) | 28.51s | 68.0 tok/s | **18.8 tok/s** | 62.5% | 1 | ❌ |
| Sentinel-Master + Draft 1B (Speculative) | 40.81s | 58.9 tok/s | **18.1 tok/s** | 50.0% | 1 | ❌ |

### Respuestas Generadas en este Nivel:
#### 🔹 Base Llama-3.2-3B Instruct
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Diseña una tarea en FreeRTOS para un ESP32 que lea por bus I2C un sensor a 100 kHz y calcule el valor RMS de una señal sinusoidal muestreada. Explica las restricciones físicas del hardware: 1) por qué se requieren resistencias de  ... (truncated)
**Tarea en FreeRTOS para ESP32**
**Objetivo:** Leer por bus I2C un sensor a 100 kHz y calcular el valor RMS de una señal sinusoidal muestreada.
**Restricciones físicas del hardware**
### 1. Resistencias de pull-up externas
...
```
#### 🔹 Sentinel-STEM (SFT)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Diseña una tarea en FreeRTOS para un ESP32 que lea por bus I2C un sensor a 100 kHz y calcule el valor RMS de una señal sinusoidal muestreada. Explica las restricciones físicas del hardware: 1) por qué se requieren resistencias de  ... (truncated)
Concepto [[FreeRTOS]]:
Implementación en [[C]] con [[FreeRTOS]]:
```c
#include <FreeRTOS.h>
...
```
#### 🔹 Sentinel-Root-Pruned (26L)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Diseña una tarea en FreeRTOS para un ESP32 que lea por bus I2C un sensor a 100 kHz y calcule el valor RMS de una señal sinusoidal muestreada. Explica las restricciones físicas del hardware: 1) por qué se requieren resistencias de  ... (truncated)
Concepto fundamental:
- [[FreeRTOS]]: Sistema operacional real-time (RTOS) basADO EN C, compatible directamente desde [[ESP32]].
- [[I2C]]: Bus interconexiones sin interferencias electromagnéticas (EMC) mediante protocolo [[Pulse-Width Modulation]] (PWM).
- [[RMS]]: Valor promedio cuadrática (root mean square) calcula valores absoluta, eliminizando oscilaciones sinusoidales.
...
```
#### 🔹 Sentinel-Master-Ultimate (Todos los Tweaks)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Diseña una tarea en FreeRTOS para un ESP32 que lea por bus I2C un sensor a 100 kHz y calcule el valor RMS de una señal sinusoidal muestreada. Explica las restricciones físicas del hardware: 1) por qué se requieren resistencias de  ... (truncated)
### 1. Restricciones Físicas y de Silicio del Hardware con ESP32
#### A. Resistencias de Pull-Up en Bus I2C y Peligro de 100k
- **Por qué se requieren resistencias de pull-up externas?**
  - En bus I2C, los transistores internos de los microcontroladores actúan como **drenadores**. Cuando una onda se mueve hacia el maestro (periférico), el transistador se pone **en parado** (en alto). Para que la onda regrese hacia el esclavo (sensor), el transistador debe **bajar** (a bajo). Sin resistencia de pull-up, el transistador permanece en parado, y la onda no se mueve.
...
```
#### 🔹 Sentinel-Master + Draft 1B (Speculative)
```markdown
add a text file
  /glob <pattern>     add text files using globbing pattern
> <|start_header_id|>system<|end_header_id|>
SENTINEL, mentor y sistema operativo cognitivo del Laboratorio STEM.
Enfoque didáctico para estudiantes, desglose de tecnicismos y uso de sintaxis Obsidian [[Concepto]].<|eot_id|><|start_header_id|>user<|end_header_id|>
Diseña una tarea en FreeRTOS para un ESP32 que lea por bus I2C un sensor a 100 kHz y calcule el valor RMS de una señal sinusoidal muestreada. Explica las restricciones físicas del hardware: 1) por qué se requieren resistencias de  ... (truncated)
### 1. Restricciones Físicas y de Silicio del Hardware con ESP32
#### A. Resistencias de Pull-Up en Bus I2C y Peligro de 100k
- **Por qué se requieren resistencias de pull-up externas?**: En bus I2C, los dispositivos pueden estar en estado de *high* (3.3V lógico) o *low* (0V lógico). El bus se mueve hacia el estado de bajo cuando el master envía una señal. Sin resistencia de pull-up, el bus permanecería en *high* hasta que el slave se ponga a *low*. Si el bus permaneciera así, el bus se alimentaría de la batería interna del ESP32 (1.8V aproximadamente) hasta que se agotara. El bus I2C funciona a 100 kHz, por lo que el tiempo que tarda el bus en moverse de *high* a *low* o viceversa es de 10 microseconds. La corriente que fluye por la resistencia es de 1.8/10µ = 180 µA. Una resistencia de 4.7k no movería el bus en un millón de veces por segundo, causando el desgaste de la fuente interna.
- **¿Qué ocurre si se usa un valor muy alto como 100k?**: Usar 100k de resistencia haría que el bus se mueva solo una cuincena de mil veces por segundo. La corriente requerida sería 1.8/0.01 = 1800
```

---
## 3. Conclusiones de Ingeniería y Veredicto Final
- **Velocidad y Latencia en Intel Core i5**: Gracias a la aceleración de Flash Attention CPU y KV Cache Q8, los modelos alcanzan velocidades de entre **17.5 y 20.3 tokens/segundo** en pura CPU sin necesidad de GPU.
- **Calidad y Precisión Técnica**: El modelo **Sentinel-Master-Ultimate (con todos los tweaks)** lidera en la prevención de bugs críticos en C (`realloc` seguro con puntero temporal) y en la protección de hardware del ESP32 (bloqueo estricto de GPIO 6-11), además de formatear de manera pedagógica con sintaxis Obsidian `[[Concepto]]`.
