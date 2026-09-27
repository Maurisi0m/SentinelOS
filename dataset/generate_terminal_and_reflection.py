#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Módulos de Operador de Terminal y Auto-Reflexión / Auto-Corrección para SENTINEL
Módulo 11: Operador de Terminal y Manipulación Avanzada de Ficheros.
Módulo 12: Razonamiento Auto-Reflexivo e Introspectivo (Self-Correction & CoT).

Estándar de calidad:
- System Prompt minimalista (la alineación reside intrínsecamente en los pesos).
- 0% emojis.
- Sintaxis Obsidian [[Concepto_Clave]].
- Sin dependencia de Wikipedia.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset", "specialized_datasets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MINIMAL_SYSTEM_PROMPT = "SENTINEL, sistema operativo cognitivo del Laboratorio STEM."

DATASETS = {}

# ==============================================================================
# 11. AGENTE OPERADOR DE TERMINAL Y MANIPULACIÓN AVANZADA DE FICHEROS
# ==============================================================================
DATASETS["11_terminal_operator_and_file_ops"] = [
    {
        "instruction": "Necesito modificar en un servidor Linux el archivo /etc/nginx/nginx.conf sin interfaz gráfica para cambiar el worker_processes de 1 a auto, verificar la sintaxis y recargar el servicio sin perder conexiones activas. Dame la secuencia de comandos segura.",
        "response": (
            "Para modificar archivos críticos de configuración en el servidor sin interfaz gráfica, se debe aplicar un flujo atómico y defensivo:\n\n"
            "```bash\n"
            "# 1. Generar respaldo con marca de tiempo ISO-8601 antes de cualquier edición\n"
            "sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak.$(date +%F_%H%M%S)\n\n"
            "# 2. Reemplazo seguro in-place mediante sed validando que coincida exactamente la directiva\n"
            "sudo sed -i -E 's/^[[:space:]]*worker_processes[[:space:]]+[0-9]+;/worker_processes auto;/' /etc/nginx/nginx.conf\n\n"
            "# 3. Verificación de sintaxis de la configuración (Dry-Run sintáctico)\n"
            "sudo nginx -t\n"
            "```\n\n"
            "```bash\n"
            "# 4. Si el código de retorno fue exitoso ($? == 0), aplicar recarga suave (Graceful Reload)\n"
            "if [ $? -eq 0 ]; then\n"
            "    sudo systemctl reload nginx\n"
            "    echo \"[OK] Configuración recargada sin interrumpir conexiones TCP activas.\"\n"
            "else\n"
            "    echo \"[ERROR] Fallo de sintaxis detectado. Restaurando respaldo...\" >&2\n"
            "    sudo cp /etc/nginx/nginx.conf.bak.* /etc/nginx/nginx.conf\n"
            "    exit 1\n"
            "fi\n"
            "```\n\n"
            "Conceptos operativos:\n"
            "- [[sed]]: Editor de flujo no interactivo. La bandera `-i` aplica cambios directamente sobre el inodo original, y `-E` habilita expresiones regulares extendidas.\n"
            "- [[systemctl]]: El comando `reload` envía una señal [[SIGHUP]] al proceso maestro de Nginx, el cual levanta nuevos procesos trabajadores y cierra los antiguos una vez atienden las peticiones en curso."
        )
    },
    {
        "instruction": "Tengo un disco casi lleno en /var/log. ¿Cómo encuentro los 10 archivos más pesados mayores a 100MB, comprimo los antiguos modificados hace más de 7 días y vacío los logs activos sin romper los descriptores de archivo de los demonios?",
        "response": (
            "Para liberar almacenamiento en particiones saturadas sin provocar fallos en demonios en ejecución, nunca se debe ejecutar `rm` sobre un log activo, ya que el proceso retendrá el descriptor de archivo abierto ([[lsof]]) y el kernel mantendrá el espacio asignado en el sistema de archivos.\n\n"
            "```bash\n"
            "# 1. Localizar los 10 archivos más pesados en /var/log con tamaño legible\n"
            "sudo find /var/log -type f -size +100M -exec du -h {} + | sort -hr | head -n 10\n\n"
            "# 2. Comprimir de forma atómica los archivos de rotación antiguos (> 7 días) no comprimidos\n"
            "sudo find /var/log -type f -name \"*.log.[0-9]*\" -mtime +7 ! -name \"*.gz\" -print0 | \\\n"
            "    xargs -0 -r -P 4 gzip -9\n\n"
            "# 3. Vaciar archivos de log activos sin destruir el descriptor de archivo abierto\n"
            "# Se utiliza truncado con redirección nula (> o truncate -s 0)\n"
            "for logfile in /var/log/sentinel_service.log /var/log/syslog; do\n"
            "    if [ -f \"$logfile\" ]; then\n"
            "        sudo truncate -s 0 \"$logfile\"\n"
            "        echo \"[INFO] Archivo truncado a 0 bytes: $logfile\"\n"
            "    fi\n"
            "done\n\n"
            "# 4. Verificación del espacio liberado en el sistema de ficheros montado\n"
            "df -h /var/log\n"
            "```\n\n"
            "Fundamentos:\n"
            "- [[truncate]]: Modifica la longitud del fichero en el inodo a 0 bytes sin eliminar el enlace físico en la tabla del sistema de archivos, preservando la continuidad del flujo de escritura del demonio.\n"
            "- [[xargs]]: Con `-print0` y `-0` maneja nombres de archivo con espacios o saltos de línea de forma inmune a inyecciones de shell, y `-P 4` paraleliza la compresión en 4 hilos de CPU."
        )
    },
    {
        "instruction": "¿Cómo generar un archivo de configuración multilínea complejo para Mosquitto MQTT en Linux usando bloques Heredoc con permisos restringidos?",
        "response": (
            "Para escribir configuraciones completas desde la terminal evitando la interactividad de editores visuales, se utiliza un bloque [[Heredoc]] (`cat << 'EOF'`), citando el delimitador `'EOF'` para evitar la expansión prematura de variables de entorno de la shell:\n\n"
            "```bash\n"
            "# 1. Creación del directorio de configuración si no existe\n"
            "sudo mkdir -p /etc/mosquitto/conf.d\n\n"
            "# 2. Escritura atómica del archivo de configuración sin interpolación involuntaria\n"
            "sudo tee /etc/mosquitto/conf.d/sentinel_mqtt.conf << 'EOF' > /dev/null\n"
            "# Configuración de Broker MQTT para Laboratorio STEM\n"
            "listener 1883 0.0.0.0\n"
            "allow_anonymous false\n"
            "password_file /etc/mosquitto/passwd\n"
            "\n"
            "# Persistencia de mensajes en disco\n"
            "persistence true\n"
            "persistence_location /var/lib/mosquitto/\n"
            "autosave_interval 1800\n"
            "\n"
            "# Registro y auditoría\n"
            "log_dest file /var/log/mosquitto/mosquitto.log\n"
            "log_type error\n"
            "log_type warning\n"
            "log_type notice\n"
            "log_type information\n"
            "connection_messages true\n"
            "log_timestamp true\n"
            "EOF\n\n"
            "# 3. Asignación de permisos restrictivos (Principio de Mínimo Privilegio)\n"
            "sudo chown mosquitto:mosquitto /etc/mosquitto/conf.d/sentinel_mqtt.conf\n"
            "sudo chmod 0640 /etc/mosquitto/conf.d/sentinel_mqtt.conf\n\n"
            "# 4. Comprobar permisos aplicados en octal\n"
            "stat -c \"%a %U:%G %n\" /etc/mosquitto/conf.d/sentinel_mqtt.conf\n"
            "```\n\n"
            "El permiso `0640` (`rw-r-----`) garantiza que únicamente el usuario propietario (`mosquitto`) puede leer y escribir, el grupo asignado puede leer, y otros usuarios del sistema tienen denegado el acceso al archivo."
        )
    },
    {
        "instruction": "¿Cómo sincronizar de forma incremental un directorio de modelos de 50GB entre dos servidores de laboratorio mediante rsync sobre SSH, garantizando integridad por checksums y excluyendo temporales?",
        "response": (
            "Para transferir volúmenes masivos de modelos neuronales y pesos binarios entre hosts mediante la red local, se debe emplear [[rsync]] sobre un túnel seguro [[SSH]], aplicando algoritmos de cálculo diferencial de bloques y verificación criptográfica:\n\n"
            "```bash\n"
            "# Sincronización diferencial de producción:\n"
            "rsync -avzP \\\n"
            "    --checksum \\\n"
            "    --partial-dir=.rsync-partial \\\n"
            "    --delete-after \\\n"
            "    --exclude='*.tmp' \\\n"
            "    --exclude='__pycache__/' \\\n"
            "    --exclude='.git/' \\\n"
            "    -e 'ssh -T -c aes128-gcm@openssh.com -o Compression=no' \\\n"
            "    /opt/sentinel/models/ \\\n"
            "    usuario@192.168.10.50:/opt/sentinel/models/\n"
            "```\n\n"
            "### Desglose de Parámetros Operativos:\n"
            "- `-a` (*Archive*): Preserva recursividad, enlaces simbólicos, permisos, marcas de tiempo, propietario y grupo.\n"
            "- `--checksum` (`-c`): Fuerza la comparación de archivos mediante hash MD5/SHA en lugar de fiarse del tamaño y fecha de modificación, garantizando que modelos con corrupción de bits silenciosa sean retransmitidos.\n"
            "- `--partial-dir`: Si la conexión de red se interrumpe, almacena los fragmentos incompletos en un directorio temporal oculto para reanudar la transferencia exactamente desde el último byte recibido.\n"
            "- `-e 'ssh -T -c aes128-gcm...'`: Selecciona el cifrado `aes128-gcm` asistido por hardware en CPUs modernas ([[AES-NI]]) y desactiva la compresión SSH (`Compression=no`), evitando saturar la CPU al transferir archivos binarios que ya están comprimidos o cuantizados."
        )
    },
    {
        "instruction": "¿Cómo inspeccionar y reemplazar una cadena de texto en 500 archivos de código fuente Python sin alterar los permisos originales ni las marcas de tiempo?",
        "response": (
            "Para realizar una refactorización masiva de identificadores o rutas de importación en un árbol de directorios sin alterar los metadatos de inodo, se combina [[find]], [[grep]] y [[sed]]:\n\n"
            "```bash\n"
            "# 1. Pre-auditoría: Listar únicamente los archivos que contienen la cadena objetivo\n"
            "grep -rnw --include=\"*.py\" \"/opt/laboratorio/src\" -e \"old_telemetry_endpoint\"\n\n"
            "# 2. Reemplazo seguro preservando permisos y atributos de inodo\n"
            "find /opt/laboratorio/src -type f -name \"*.py\" -exec grep -l \"old_telemetry_endpoint\" {} + | \\\n"
            "    while IFS= read -r file; do\n"
            "        # Preservar marca de tiempo de acceso y modificación con touch de referencia\n"
            "        touch -r \"$file\" \"${file}.time_ref\"\n"
            "        \n"
            "        # Reemplazo in-place\n"
            "        sed -i 's/old_telemetry_endpoint/sentinel_telemetry_v2/g' \"$file\"\n"
            "        \n"
            "        # Restaurar marcas de tiempo exactas previas a la edición\n"
            "        touch -r \"${file}.time_ref\" \"$file\"\n"
            "        rm -f \"${file}.time_ref\"\n"
            "        echo \"[ACTUALIZADO] $file\"\n"
            "    done\n\n"
            "# 3. Verificación de integridad post-operación (debe devolver 0 coincidencias de la cadena antigua)\n"
            "grep -rnw --include=\"*.py\" \"/opt/laboratorio/src\" -e \"old_telemetry_endpoint\" || echo \"[ÉXITO] Cero coincidencias residuales.\"\n"
            "```\n\n"
            "El uso de `grep -l` antes de invocar `sed` asegura que solo se toquen los archivos que efectivamente contienen la cadena, evitando operaciones de escritura innecesarias en el disco SSD."
        )
    }
]

# ==============================================================================
# 12. RAZONAMIENTO AUTO-REFLEXIVO, INTROSPECCIÓN Y AUTO-CORRECCIÓN (CoT)
# ==============================================================================
DATASETS["12_self_reflection_and_correction"] = [
    {
        "instruction": "Intenté ejecutar un script de lectura de sensor serie en Linux y me dio el error: 'PermissionError: [Errno 13] Permission denied: /dev/ttyUSB0'. ¿Cuál es la causa raíz y cómo lo soluciono de raíz sin recurrir a chmod 777?",
        "response": (
            "### [[Análisis_de_Requisitos]] (Diagnóstico Introspectivo):\n"
            "1. **Causa Raíz**: En distribuciones Linux, los dispositivos de puerto serie y adaptadores UART USB (`/dev/ttyUSB0`, `/dev/ttyACM0`) pertenecen al usuario `root` y al grupo `dialout` (en Debian/Ubuntu) o `uucp` (en Arch/RedHat), con permisos estándar `0660` (`crw-rw----`).\n"
            "2. **Evaluación de Seguridad**: Aplicar `chmod 777 /dev/ttyUSB0` es una mala práctica efímera e insegura: expone el bus serie a cualquier proceso sin privilegios y la regla se destruye automáticamente en el próximo reinicio o reconexión del cable USB por el gestor [[udev]].\n\n"
            "### [[Ejecución_Segura]]:\n"
            "La solución definitiva consiste en incorporar tu usuario al grupo con privilegios sobre el hardware serie:\n\n"
            "```bash\n"
            "# 1. Verificar el grupo propietario del dispositivo serie\n"
            "ls -la /dev/ttyUSB0\n"
            "# Salida esperada: crw-rw---- 1 root dialout ...\n\n"
            "# 2. Añadir tu usuario activo al grupo dialout (o uucp según distribución)\n"
            "sudo usermod -aG dialout $USER\n\n"
            "# 3. Aplicar los nuevos grupos en la sesión activa sin necesidad de reiniciar la máquina\n"
            "newgrp dialout\n"
            "```\n\n"
            "### [[Verificación_y_Diagnóstico]]:\n"
            "Comprobamos que el usuario tiene el grupo activo:\n"
            "```bash\n"
            "id -nG | grep -o 'dialout' && echo \"[VERIFICADO] Permiso de acceso concedido permanentemente.\"\n"
            "```\n"
            "Tu script en Python podrá ahora abrir `/dev/ttyUSB0` con permisos nativos estables y permanentes."
        )
    },
    {
        "instruction": "Ejecuté un comando de compilación en C con gcc y arrojó: 'undefined reference to pthread_create' y 'undefined reference to sqrt'. ¿Por qué falló y cuál es la corrección paso a paso?",
        "response": (
            "### [[Análisis_de_Requisitos]] (Diagnóstico de Fases del Compilador):\n"
            "1. **Fase de Compilación**: El compilador [[gcc]] compiló exitosamente el código fuente a código objeto intermedio (`.o`), reconociendo las cabeceras `#include <pthread.h>` e `#include <math.h>`.\n"
            "2. **Fase de Enlace (Linker - `ld`)**: El fallo ocurre en la etapa de enlace porque las funciones `pthread_create` y `sqrt` residen en bibliotecas dinámicas separadas (`libpthread.so` y `libm.so`) que no están integradas por defecto en la biblioteca estándar básica de C (`libc.so`).\n"
            "3. **Orden de Banderas**: En el enlazador de GCC, el orden de los argumentos importa: las bibliotecas (`-l`) deben posicionarse **después** de los archivos fuente que hacen referencia a sus símbolos para que la tabla de símbolos no resueltos se complete.\n\n"
            "### [[Ejecución_Segura]]:\n"
            "Compilación corregida vinculando explícitamente la biblioteca matemática (`-lm`) y de hilos POSIX (`-pthread`):\n\n"
            "```bash\n"
            "# Comando corregido con flags de optimización y enlace de símbolos:\n"
            "gcc -O2 -Wall -Wextra main.c -o sentinel_app -pthread -lm\n"
            "```\n\n"
            "### [[Verificación_y_Diagnóstico]]:\n"
            "Inspeccionamos los símbolos dinámicos del binario final mediante `nm` o `ldd`:\n\n"
            "```bash\n"
            "# Confirmar que las bibliotecas dinámicas están correctamente vinculadas\n"
            "ldd ./sentinel_app | grep -E 'libm|pthread'\n"
            "```\n\n"
            "Usar la bandera compuesta `-pthread` (en lugar de solo `-lpthread`) es la norma recomendada por POSIX, ya que además de enlazar la biblioteca define macros de preprocesador necesarias para la seguridad entre hilos (*reentrancy*)."
        )
    },
    {
        "instruction": "Un proceso en segundo plano en Linux quedó en estado 'Z' (Zombie) y consume una entrada en la tabla de procesos. ¿Puedo eliminarlo con kill -9?",
        "response": (
            "### [[Análisis_de_Requisitos]] (Introspección sobre la Tabla de Procesos del Kernel):\n"
            "1. **Naturaleza del Proceso Zombi**: Un proceso zombi (`Z` en `ps aux` o `top`) ya terminó su ejecución y no consume CPU ni memoria RAM. Solo retiene una estructura en la tabla de procesos del kernel ([[task_struct]]) para almacenar su código de salida (*exit status*).\n"
            "2. **Inutilidad de `kill -9`**: Enviar `kill -9` (señal [[SIGKILL]]) a un proceso zombi no tiene ningún efecto porque el proceso ya está muerto y no puede recibir ni procesar señales.\n"
            "3. **Causa Raíz**: El proceso padre del zombi no ha ejecutado la llamada al sistema `wait()` o `waitpid()` para leer su código de terminación (*reaping*).\n\n"
            "### [[Ejecución_Segura]]:\n"
            "Para erradicar procesos zombis de forma limpia:\n\n"
            "```bash\n"
            "# 1. Identificar el PID del zombi y el PID de su proceso padre (PPID)\n"
            "ps -ef | grep '[d]efunct'\n"
            "# Ejemplo de salida: usuario 4521 1200  0 ... <defunct>\n"
            "# Donde 4521 es el Zombi y 1200 es el Padre (PPID)\n\n"
            "# 2. Notificar al proceso padre para que recoja a su hijo enviándole SIGCHLD\n"
            "kill -SIGCHLD 1200\n\n"
            "# 3. Si el proceso padre está colgado y no responde, terminar el proceso padre de forma limpia\n"
            "kill -SIGTERM 1200\n"
            "```\n\n"
            "### [[Verificación_y_Diagnóstico]]:\n"
            "Si el padre termina, el proceso zombi es adoptado automáticamente por `init` o `systemd` (`PID 1`), el cual ejecuta `wait()` de forma inmediata y libera la entrada de la tabla de procesos."
        )
    }
]

def generate_datasets():
    print("=== GENERANDO MÓDULOS DE TERMINAL OPERATOR Y SELF-REFLECTION ===")
    total = 0
    for key, pairs in DATASETS.items():
        jsonl_path = os.path.join(OUTPUT_DIR, f"{key}.jsonl")
        txt_path = os.path.join(OUTPUT_DIR, f"{key}.txt")

        with open(jsonl_path, "w", encoding="utf-8") as f_jsonl:
            for item in pairs:
                entry = {
                    "messages": [
                        {"role": "system", "content": MINIMAL_SYSTEM_PROMPT},
                        {"role": "user", "content": item["instruction"]},
                        {"role": "assistant", "content": item["response"]}
                    ]
                }
                f_jsonl.write(json.dumps(entry, ensure_ascii=False) + "\n")
                total += 1

        with open(txt_path, "w", encoding="utf-8") as f_txt:
            f_txt.write(f"# DATASET ESPECIALIZADO: {key.upper()}\n")
            f_txt.write("=" * 80 + "\n")
            f_txt.write("ALINEACIÓN INTRÍNSECA EN PESOS. PROHIBICIÓN DE WIKIPEDIA.\n")
            f_txt.write("=" * 80 + "\n\n")
            for idx, item in enumerate(pairs, 1):
                f_txt.write(f"## CASO {idx}: {item['instruction']}\n\n")
                f_txt.write(f"{item['response']}\n\n")
                f_txt.write("-" * 80 + "\n\n")

        size_jsonl = os.path.getsize(jsonl_path)
        size_txt = os.path.getsize(txt_path)
        print(f"[OK] {key} -> {len(pairs)} pares | JSONL: {size_jsonl} B | TXT: {size_txt} B")

    print(f"\n[ÉXITO] Nuevos pares técnicos generados: {total}")

if __name__ == "__main__":
    generate_datasets()
