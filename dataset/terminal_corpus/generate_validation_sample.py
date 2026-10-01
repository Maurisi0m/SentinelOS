#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador y Generador de Muestra de Alta Calidad para el Dataset de Control de Terminal.
Esquema de Validación Estricto:
- Formato: JSONL (1 muestra por línea)
- Campos: id, os, distribution, shell, difficulty, category, subcategory, example_type,
          user_request, context, analysis, commands, expected_output, verification,
          failure_cases, alternatives, explanation.
- Coherencia técnica absoluta: comandos reales, salidas realistas, 0% emojis, [[Conceptos]].
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_SAMPLE_FILE = os.path.join(BASE_DIR, "terminal_corpus", "sample_validation.jsonl")

REQUIRED_FIELDS = [
    "id", "os", "distribution", "shell", "difficulty", "category",
    "subcategory", "example_type", "user_request", "context",
    "analysis", "commands", "expected_output", "verification",
    "failure_cases", "alternatives", "explanation"
]

VALID_OS = {"linux", "windows", "macos", "cross_platform"}
VALID_SHELLS = {"bash", "sh", "zsh", "fish", "powershell", "cmd"}
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced", "expert"}
VALID_TYPES = {
    "instruction_to_command",
    "instruction_to_multistep",
    "error_to_diagnosis",
    "output_to_interpretation",
    "state_to_action",
    "failed_to_corrected",
    "cross_platform_translation",
    "interactive_session",
    "troubleshooting_recovery",
    "planning_orchestration"
}

def validate_sample(item):
    for f in REQUIRED_FIELDS:
        if f not in item:
            raise ValueError(f"Campo requerido ausente: {f}")
    if item["os"] not in VALID_OS:
        raise ValueError(f"OS invalido: {item['os']}")
    if item["shell"] not in VALID_SHELLS:
        raise ValueError(f"Shell invalido: {item['shell']}")
    if item["difficulty"] not in VALID_DIFFICULTIES:
        raise ValueError(f"Dificultad invalida: {item['difficulty']}")
    if item["example_type"] not in VALID_TYPES:
        raise ValueError(f"Tipo de ejemplo invalido: {item['example_type']}")
    
    ctx = item["context"]
    for cf in ["cwd", "user", "privileges", "system_state"]:
        if cf not in ctx or not isinstance(ctx[cf], str):
            raise ValueError(f"Contexto invalido o incompleto en {cf}")
            
    if not isinstance(item["commands"], list) or len(item["commands"]) == 0:
        raise ValueError("commands debe ser una lista no vacia")
    if not isinstance(item["analysis"], list) or len(item["analysis"]) == 0:
        raise ValueError("analysis debe ser una lista no vacia")
    if not isinstance(item["verification"], list) or len(item["verification"]) == 0:
        raise ValueError("verification debe ser una lista no vacia")
    if not isinstance(item["failure_cases"], list) or len(item["failure_cases"]) == 0:
        raise ValueError("failure_cases debe ser una lista no vacia")
    for fc in item["failure_cases"]:
        for k in ["error", "cause", "recovery"]:
            if k not in fc:
                raise ValueError(f"failure_case carece de {k}")
    if not isinstance(item["alternatives"], list) or len(item["alternatives"]) == 0:
        raise ValueError("alternatives debe ser una lista no vacia")
    if "[[" not in item["explanation"]:
        raise ValueError("explanation debe contener enlaces Obsidian [[Concepto]]")
    return True

VALIDATION_SAMPLES = [
    # 1. Ubuntu / Bash: SSH Port hardening and configuration reload (instruction_to_multistep)
    {
        "id": "terminal_00000001",
        "os": "linux",
        "distribution": "ubuntu",
        "shell": "bash",
        "difficulty": "intermediate",
        "category": "security_hardening",
        "subcategory": "ssh_configuration",
        "example_type": "instruction_to_multistep",
        "user_request": "Cambia el puerto SSH del servidor de 22 a 2222, valida la sintaxis y recarga el servicio sin perder la sesión activa.",
        "context": {
            "cwd": "/etc/ssh",
            "user": "sysadmin",
            "privileges": "sudo",
            "system_state": "Ubuntu 24.04 LTS, OpenSSH 9.6p1 instalado, servicio ssh.service en ejecución en puerto 22."
        },
        "analysis": [
            "Crear un respaldo atómico previo del archivo de configuración /etc/ssh/sshd_config.",
            "Utilizar sed para modificar o insertar la directiva Port en 2222 de forma determinista.",
            "Invocar el validador sintáctico sshd -t para asegurar que no existan errores de parseo antes de recargar.",
            "Recargar el servicio ssh mediante systemctl reload para mantener las sesiones de control TCP existentes.",
            "Consultar con ss o netstat que el socket TCP escuche activamente en el puerto 2222."
        ],
        "commands": [
            "sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak_$(date +%F)",
            "sudo sed -i 's/^#\\?Port .*/Port 2222/' /etc/ssh/sshd_config",
            "sudo sshd -t",
            "sudo systemctl reload ssh",
            "sudo ss -lntp | grep ':2222'"
        ],
        "expected_output": "LISTEN 0      128          0.0.0.0:2222       0.0.0.0:*    users:((\"sshd\",pid=1024,fd=3))\nLISTEN 0      128             [::]:2222          [::]:*    users:((\"sshd\",pid=1024,fd=4))",
        "verification": [
            "El comando sshd -t retorna código de salida 0 sin emitir advertencias de sintaxis.",
            "El comando ss -lntp confirma sockets LISTEN en 0.0.0.0:2222 y [::]:2222 vinculados al proceso sshd."
        ],
        "failure_cases": [
            {
                "error": "sshd -t: /etc/ssh/sshd_config line 15: Bad configuration option: Porrt",
                "cause": "Error tipográfico en la directiva de configuración.",
                "recovery": "Restaurar el respaldo previo con 'sudo cp /etc/ssh/sshd_config.bak_* /etc/ssh/sshd_config' y corregir la ortografía."
            },
            {
                "error": "Failed to reload ssh.service: Unit ssh.service not found",
                "cause": "En distribuciones derivadas de Debian antiguas la unidad se denomina sshd en lugar de ssh.",
                "recovery": "Ejecutar 'sudo systemctl reload sshd.service'."
            }
        ],
        "alternatives": [
            "Editar interactivamente el archivo mediante 'sudo nano /etc/ssh/sshd_config'.",
            "Ubicar un archivo complementario en el directorio modular '/etc/ssh/sshd_config.d/2222-port.conf' soportado en OpenSSH moderno."
        ],
        "explanation": "La administración segura de [[OpenSSH]] exige siempre una verificación preventiva con `sshd -t` antes de aplicar cambios en producción. Al utilizar `reload` en lugar de `restart`, [[systemd]] envía una señal `SIGHUP` al proceso maestro, lo que reasigna los sockets de escucha sin abortar las conexiones establecidas por administradores remotos."
    },

    # 2. Windows PowerShell: CIM telemetry and memory inspection (output_to_interpretation)
    {
        "id": "terminal_00000002",
        "os": "windows",
        "distribution": "windows_11",
        "shell": "powershell",
        "difficulty": "intermediate",
        "category": "processes_and_services",
        "subcategory": "memory_telemetry",
        "example_type": "output_to_interpretation",
        "user_request": "Interpreta la salida de consumo de memoria de procesos en PowerShell e indica cuál proceso presenta fugas o alto consumo.",
        "context": {
            "cwd": "C:\\Windows\\System32",
            "user": "Administrator",
            "privileges": "Elevated",
            "system_state": "Windows 11 Enterprise x64, 16GB RAM física instalada."
        },
        "analysis": [
            "Ejecutar Get-Process con proyección de WorkingSet64 y PrivateMemorySize64 ordenados de forma descendente.",
            "Interpretar los valores numéricos convirtiendo bytes a megabytes.",
            "Distinguir entre memoria de conjunto de trabajo (Working Set) y memoria privada no compartida (Private Bytes)."
        ],
        "commands": [
            "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 Id, ProcessName, @{Name='WorkingSet_MB';Expression={[math]::Round($_.WorkingSet64/1MB,2)}}, @{Name='Private_MB';Expression={[math]::Round($_.PrivateMemorySize64/1MB,2)}} | Format-Table -AutoSize"
        ],
        "expected_output": "   Id ProcessName WorkingSet_MB Private_MB\n   -- ----------- ------------- ----------\n12404 sqlservr          4850.12    5120.40\n 8920 python            1840.50    1920.10\n 3140 msedge             980.20     850.30\n 1028 dwm                420.15     380.00\n  760 explorer           210.40     190.20",
        "verification": [
            "La tabla proyectada contiene exactamente las columnas solicitadas calculadas en MB con precisión de 2 decimales.",
            "El proceso 'sqlservr' (PID 12404) lidera el consumo con 4.85 GB de Working Set y 5.12 GB de memoria privada."
        ],
        "failure_cases": [
            {
                "error": "Get-Process : Access is denied",
                "cause": "La sesión de PowerShell no se ejecutó con privilegios de Administrador para auditar procesos del sistema.",
                "recovery": "Iniciar PowerShell mediante 'Run as Administrator' (elevación UAC)."
            }
        ],
        "alternatives": [
            "Utilizar el comando clásico 'tasklist /v /fi \"MEMUSAGE gt 500000\"' desde CMD.",
            "Consultar la clase WMI 'Get-CimInstance Win32_PerfFormattedData_PerfProc_Process'."
        ],
        "explanation": "En [[PowerShell]], el pipeline opera sobre instancias de objetos .NET (`System.Diagnostics.Process`), permitiendo realizar cálculos numéricos nativos mediante `[math]::Round`. La métrica `WorkingSet64` representa la memoria física actualmente residente en RAM, mientras que `PrivateMemorySize64` mide la memoria comprometida que no puede ser compartida con otros procesos."
    },

    # 3. Windows CMD: Process Port Kill and Netstat Diagnostic (error_to_diagnosis)
    {
        "id": "terminal_00000003",
        "os": "windows",
        "distribution": "windows_server",
        "shell": "cmd",
        "difficulty": "beginner",
        "category": "processes_and_services",
        "subcategory": "port_termination",
        "example_type": "error_to_diagnosis",
        "user_request": "Al iniciar una aplicación en CMD obtengo el error 'bind: address already in use: 8080'. Diagnostica qué proceso retiene el puerto y finalízalo.",
        "context": {
            "cwd": "C:\\Server",
            "user": "Operador",
            "privileges": "Administrator",
            "system_state": "Windows Server 2022 Datacenter, puerto TCP 8080 en conflicto."
        },
        "analysis": [
            "Identificar el número de PID en la última columna de netstat -ano filtrando por el puerto :8080.",
            "Determinar el nombre del ejecutable asociado al PID mediante tasklist.",
            "Finalizar el proceso forzadamente y de raíz utilizando taskkill con las banderas /F y /PID."
        ],
        "commands": [
            "netstat -ano | findstr :8080",
            "tasklist /FI \"PID eq 14892\"",
            "taskkill /F /PID 14892",
            "netstat -ano | findstr :8080"
        ],
        "expected_output": "  TCP    0.0.0.0:8080           0.0.0.0:0              LISTENING       14892\n\nNombre de imagen               PID Nombre de sesión Núm. de ses   Uso de mem\n========================= ======== ================ =========== ============\nnode.exe                     14892 Services                   0      84,210 KB\n\nCORRECTO: se finalizó el proceso con PID 14892.",
        "verification": [
            "El segundo llamado a netstat -ano | findstr :8080 devuelve código 1 (sin salida), confirmando la liberación del socket."
        ],
        "failure_cases": [
            {
                "error": "ERROR: No se pudo terminar el proceso con PID 14892. Motivo: Acceso denegado.",
                "cause": "El proceso pertenece a una cuenta de servicio de mayor privilegio (SYSTEM).",
                "recovery": "Abrir una consola CMD con privilegios elevados de Administrador."
            }
        ],
        "alternatives": [
            "Usar PowerShell: 'Get-NetTCPConnection -LocalPort 8080 | Stop-Process -Force'.",
            "Usar Resource Monitor (resmon.exe) en la pestaña Red."
        ],
        "explanation": "El conflicto `bind: address already in use` ocurre cuando un proceso previo mantiene abierto un descriptor de socket TCP sin liberar el enlace (`SO_REUSEADDR`). En [[CMD]], `netstat -ano` exhibe la columna numérica del PID, permitiendo la interoperabilidad con `taskkill` mediante canalizaciones o ejecución directa."
    },

    # 4. Linux Arch: Pacman PGP Corrupted Keyring Recovery (troubleshooting_recovery)
    {
        "id": "terminal_00000004",
        "os": "linux",
        "distribution": "arch",
        "shell": "bash",
        "difficulty": "advanced",
        "category": "package_management",
        "subcategory": "keyring_repair",
        "example_type": "troubleshooting_recovery",
        "user_request": "En Arch Linux el comando 'pacman -Syu' falla con error 'invalid or corrupted package (PGP signature)'. Repara el llavero criptográfico y actualiza el sistema.",
        "context": {
            "cwd": "/home/mauro",
            "user": "mauro",
            "privileges": "sudo",
            "system_state": "Arch Linux Rolling, bases de datos sin actualizar por 6 meses, firmas Web of Trust desfasadas."
        },
        "analysis": [
            "El síntoma indica que las claves GPG locales de los mantenedores de paquetes expiraron o sufrieron desincronización.",
            "Eliminar la base de datos gnupg de pacman localmente corrupta en /etc/pacman.d/gnupg.",
            "Inicializar un llavero limpio mediante 'pacman-key --init'.",
            "Repoblar las claves maestras oficiales con 'pacman-key --populate archlinux'.",
            "Descargar e instalar la versión más reciente del paquete archlinux-keyring de forma prioritaria.",
            "Proceder con la sincronización completa del sistema 'pacman -Su'."
        ],
        "commands": [
            "sudo rm -rf /etc/pacman.d/gnupg",
            "sudo pacman-key --init",
            "sudo pacman-key --populate archlinux",
            "sudo pacman -Sy --noconfirm archlinux-keyring",
            "sudo pacman -Su --noconfirm"
        ],
        "expected_output": "gpg: Generating pacman keyring...\ngpg: Keyring populated with 154 master keys.\n:: Synchronizing package databases...\n core [######################] 100%\n extra [#####################] 100%\nresolving dependencies...\nlooking for conflicting packages...\n:: Starting full system upgrade...\n(1/1) upgrading archlinux-keyring\n(142/142) upgrading system packages...",
        "verification": [
            "pacman-key --populate archlinux concluye con código de retorno 0.",
            "pacman -Su completa la transacción sin abortos por comprobación de firmas SHA256/PGP."
        ],
        "failure_cases": [
            {
                "error": "gpg: keyserver receive failed: Server indicated a failure",
                "cause": "El servidor de claves por defecto de GPG está bloqueado por el firewall o caído.",
                "recovery": "Configurar un keyserver alternativo como 'hkps://keyserver.ubuntu.com' en /etc/pacman.d/gnupg/gpg.conf."
            }
        ],
        "alternatives": [
            "Deshabilitar temporalmente la verificación en /etc/pacman.conf estableciendo 'SigLevel = Never' (práctica desaconsejada por seguridad excepto en entornos aislados)."
        ],
        "explanation": "En [[Arch_Linux]], la integridad de los paquetes binarios `.pkg.tar.zst` se valida mediante firmas [[PGP]]. Si el sistema pasa un tiempo prolongado sin sincronizar, las claves de firma de los desarrolladores expiran en el llavero local, impidiendo que [[pacman]] complete las transacciones hasta que se regenere la infraestructura de confianza con `pacman-key`."
    },

    # 5. Linux Fedora / RHEL: Firewall-cmd and SELinux port labeling (planning_orchestration)
    {
        "id": "terminal_00000005",
        "os": "linux",
        "distribution": "fedora",
        "shell": "bash",
        "difficulty": "advanced",
        "category": "defensive_security",
        "subcategory": "selinux_firewalld",
        "example_type": "planning_orchestration",
        "user_request": "En Fedora/RHEL, configura un servicio web personalizado en el puerto TCP 8085 permitiendo el tráfico en firewalld y autorizando el socket en SELinux.",
        "context": {
            "cwd": "/root",
            "user": "root",
            "privileges": "root",
            "system_state": "Fedora 40 Server, SELinux en modo Enforcing, firewalld activo en zona public."
        },
        "analysis": [
            "Planificar la apertura en la capa perimetral (firewalld) con persistencia permanente.",
            "Recargar las reglas dinámicas de firewalld.",
            "Planificar la autorización en el subsistema de control de acceso obligatorio (SELinux).",
            "Verificar qué tipos de puertos corresponden a tráfico HTTP en semanage (http_port_t).",
            "Asignar la etiqueta http_port_t al puerto TCP 8085 mediante semanage port.",
            "Verificar tanto la regla de firewall como la política de SELinux."
        ],
        "commands": [
            "firewall-cmd --permanent --add-port=8085/tcp",
            "firewall-cmd --reload",
            "semanage port -a -t http_port_t -p tcp 8085",
            "semanage port -l | grep http_port_t",
            "firewall-cmd --list-ports"
        ],
        "expected_output": "success\nsuccess\nhttp_port_t                    tcp      8085, 80, 81, 443, 488, 8008, 8009, 8443, 9000\n8085/tcp",
        "verification": [
            "firewall-cmd --list-ports muestra explícitamente '8085/tcp'.",
            "semanage port -l lista el puerto 8085 asociado al contexto de tipo 'http_port_t'."
        ],
        "failure_cases": [
            {
                "error": "ValueError: Port tcp/8085 already defined",
                "cause": "El puerto ya tiene asignada otra etiqueta en la directiva de SELinux.",
                "recovery": "Utilizar la bandera de modificación 'semanage port -m -t http_port_t -p tcp 8085'."
            },
            {
                "error": "semanage: command not found",
                "cause": "Falta la suite de utilidades de gestión de políticas de SELinux.",
                "recovery": "Instalar con 'dnf install -y policycoreutils-python-utils'."
            }
        ],
        "alternatives": [
            "Usar iptables manual (desaconsejado en RHEL/Fedora ya que entra en conflicto con nftables/firewalld).",
            "Deshabilitar SELinux (práctica totalmente desaconsejada en producción)."
        ],
        "explanation": "En la familia Enterprise Linux ([[RHEL]], [[Fedora]], [[Rocky_Linux]]), habilitar un puerto en el firewall no basta: el subsistema [[SELinux]] bloquea llamadas de sistema `bind()` en puertos no estándar a menos que el tipo de contexto (`http_port_t`) sea asignado formalmente con `semanage`."
    },

    # 6. Linux Alpine: Minimalist Container Package and Service Management (instruction_to_command)
    {
        "id": "terminal_00000006",
        "os": "linux",
        "distribution": "alpine",
        "shell": "sh",
        "difficulty": "beginner",
        "category": "package_management",
        "subcategory": "apk_openrc",
        "example_type": "instruction_to_command",
        "user_request": "En Alpine Linux, actualiza el índice de paquetes e instala curl y jq sin almacenar archivos temporales en caché.",
        "context": {
            "cwd": "/",
            "user": "root",
            "privileges": "root",
            "system_state": "Alpine Linux 3.20 en contenedor OCI ligero, gestor de paquetes apk activo."
        },
        "analysis": [
            "En Alpine Linux no se utiliza apt ni dnf, sino el gestor binario apk.",
            "Para evitar desperdiciar espacio en imágenes de contenedores, se utiliza la bandera --no-cache.",
            "La bandera --no-cache descarga el índice de paquetes en memoria RAM y borra los ficheros .apk tras la instalación."
        ],
        "commands": [
            "apk add --no-cache curl jq",
            "curl --version | head -n 1 && jq --version"
        ],
        "expected_output": "fetch https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/APKINDEX.tar.gz\nfetch https://dl-cdn.alpinelinux.org/alpine/v3.20/community/x86_64/APKINDEX.tar.gz\n(1/5) Installing ca-certificates (20240705-r0)\n(2/5) Installing brotli-libs (1.1.0-r2)\n(3/5) Installing libcurl (8.9.1-r1)\n(4/5) Installing curl (8.9.1-r1)\n(5/5) Installing jq (1.7.1-r0)\nExecuting busybox-1.36.1-r29.trigger\nOK: 12 MiB in 21 packages\ncurl 8.9.1 (x86_64-alpine-linux-musl)\njq-1.7.1",
        "verification": [
            "El gestor apk concluye con mensaje 'OK'.",
            "Las utilidades devuelven sus respectivas versiones vinculadas a la biblioteca C musl."
        ],
        "failure_cases": [
            {
                "error": "UNSATISFIED DEPENDENCIES",
                "cause": "Repositorios de Alpine desfasados o no configurados en /etc/apk/repositories.",
                "recovery": "Verificar la conectividad de red y ejecutar 'apk update'."
            }
        ],
        "alternatives": [
            "Ejecutar 'apk update && apk add curl jq && rm -rf /var/cache/apk/*' (método heredado equivalente a --no-cache)."
        ],
        "explanation": "[[Alpine_Linux]] utiliza [[apk]] y la biblioteca [[musl]] libc en sustitución de glibc. La instrucción `apk add --no-cache` es la práctica estándar en entornos [[Docker]] para mantener el tamaño de la capa de sistema de archivos en el mínimo indispensable."
    },

    # 7. Hardware & Serial: STM32/Arduino USB Serial Communication and dmesg (hardware_management)
    {
        "id": "terminal_00000007",
        "os": "linux",
        "distribution": "debian",
        "shell": "bash",
        "difficulty": "intermediate",
        "category": "hardware_management",
        "subcategory": "serial_usb_iot",
        "example_type": "state_to_action",
        "user_request": "Se conectó una placa microcontroladora (STM32 / Arduino) por USB pero el usuario no puede abrir el puerto /dev/ttyUSB0 por error de permisos. Diagnostica y otorga acceso permanente.",
        "context": {
            "cwd": "/home/developer",
            "user": "developer",
            "privileges": "sudo",
            "system_state": "Debian 12 Bookworm, convertidor USB-Serial CH340/FTDI recién conectado."
        },
        "analysis": [
            "Inspeccionar los eventos del kernel con dmesg para confirmar la detección del convertidor serie y el nombre del nodo /dev/ttyUSB* o /dev/ttyACM*.",
            "Auditar los permisos y el grupo propietario del nodo de dispositivo con ls -l.",
            "En Debian/Ubuntu los dispositivos serie pertenecen al grupo 'dialout'.",
            "Añadir al usuario actual al grupo dialout mediante usermod -aG.",
            "Aplicar las reglas de udev si es necesario para evitar reinicios de sesión."
        ],
        "commands": [
            "dmesg | grep -E 'ttyUSB|ttyACM' | tail -n 3",
            "ls -l /dev/ttyUSB0",
            "sudo usermod -aG dialout $USER",
            "id $USER"
        ],
        "expected_output": "[  142.501230] ch341 1-1.2:1.0: ch341-uart converter detected\n[  142.502010] usb 1-1.2: ch341-uart converter now attached to ttyUSB0\ncrw-rw---- 1 root dialout 188, 0 Sep 26 17:10 /dev/ttyUSB0\nuid=1000(developer) gid=1000(developer) groups=1000(developer),20(dialout),27(sudo)",
        "verification": [
            "dmesg confirma la vinculación del driver 'ch341-uart' a 'ttyUSB0'.",
            "El comando id refleja la inclusión del identificador secundario en el grupo 'dialout'."
        ],
        "failure_cases": [
            {
                "error": "dmesg: read kernel buffer failed: Permission denied",
                "cause": "En kernels modernos el acceso al buffer dmesg requiere privilegios de superusuario si dmesg_restrict=1.",
                "recovery": "Ejecutar con sudo: 'sudo dmesg | grep -E \"ttyUSB|ttyACM\"'."
            }
        ],
        "alternatives": [
            "Crear una regla udev en '/etc/udev/rules.d/99-usb-serial.rules' con 'MODE=\"0666\"' para acceso universal sin requerir pertenencia al grupo."
        ],
        "explanation": "En sistemas [[Linux]], la comunicación con [[Arduino]], [[STM32]] o [[Raspberry_Pi]] a través de buses UART/USB genera nodos de caracteres bajo `/dev/ttyUSB[0-9]` o `/dev/ttyACM[0-9]`. La seguridad POSIX delega el acceso de lectura y escritura al grupo `dialout`; asignar la pertenencia de usuario con `usermod -aG` es la solución canónica para desarrollo de firmware sin utilizar sudo en el IDE."
    },

    # 8. macOS Darwin: Launchd daemon lifecycle and APFS volume audit (troubleshooting_recovery)
    {
        "id": "terminal_00000008",
        "os": "macos",
        "distribution": "macos_sonoma",
        "shell": "zsh",
        "difficulty": "advanced",
        "category": "processes_and_services",
        "subcategory": "launchd_apfs",
        "example_type": "troubleshooting_recovery",
        "user_request": "En macOS Sonoma, un servicio LaunchDaemon en /Library/LaunchDaemons/com.lab.agent.plist no arranca tras reiniciar. Audita su estado con launchctl, recárgalo forzadamente y valida el almacenamiento APFS.",
        "context": {
            "cwd": "/Users/admin",
            "user": "admin",
            "privileges": "sudo",
            "system_state": "macOS 14.5 Sonoma (Darwin 23.5.0), Apple Silicon M3, APFS cifrado con FileVault."
        },
        "analysis": [
            "En macOS moderno, los comandos heredados launchctl load/unload están obsoletos y son reemplazados por bootstrap/bootout.",
            "Auditar el estado actual del servicio en el dominio system con 'launchctl print system/com.lab.agent'.",
            "Desregistrar la instancia colgada con 'launchctl bootout system/com.lab.agent' si existiese.",
            "Registrar nuevamente el servicio mediante 'launchctl bootstrap system /Library/LaunchDaemons/com.lab.agent.plist'.",
            "Forzar la ejecución inmediata y monitoreo con 'launchctl kickstart -k system/com.lab.agent'.",
            "Auditar el espacio libre del contenedor APFS con 'diskutil apfs list'."
        ],
        "commands": [
            "sudo launchctl print system/com.lab.agent || true",
            "sudo launchctl bootout system/com.lab.agent 2>/dev/null || true",
            "sudo launchctl bootstrap system /Library/LaunchDaemons/com.lab.agent.plist",
            "sudo launchctl kickstart -k system/com.lab.agent",
            "sudo launchctl print system/com.lab.agent | grep 'state ='",
            "diskutil apfs list | grep -E 'Container Reference|Capacity In Use'"
        ],
        "expected_output": "state = running\n    APFS Container Reference:     disk3\n    Capacity In Use By Volumes:   184201004800 B (184.2 GB) (38.2%)",
        "verification": [
            "launchctl print confirma 'state = running'.",
            "diskutil apfs list confirma que el contenedor principal mantiene un uso inferior al 40% con espacio libre."
        ],
        "failure_cases": [
            {
                "error": "Bootstrap failed: 5: Input/output error",
                "cause": "Los permisos del archivo plist no son 644 o el propietario no es root:wheel.",
                "recovery": "Ejecutar 'sudo chown root:wheel /Library/LaunchDaemons/com.lab.agent.plist && sudo chmod 644 /Library/LaunchDaemons/com.lab.agent.plist'."
            }
        ],
        "alternatives": [
            "Para servicios de usuario en sesión gráfica, utilizar el dominio 'gui/<uid>' en lugar de 'system/'."
        ],
        "explanation": "El subsistema [[launchd]] es el orquestador unificado de procesos en [[macOS]], reemplazando tanto a `init/systemd` como a `cron`. Los daemons del sistema residen en `/Library/LaunchDaemons/` y exigen propiedad estricta `root:wheel` bajo el sistema de archivos [[APFS]]."
    },

    # 9. Cross-Platform Translation: Listing Hidden Files and Metadata (cross_platform_translation)
    {
        "id": "terminal_00000009",
        "os": "cross_platform",
        "distribution": "universal",
        "shell": "bash",
        "difficulty": "beginner",
        "category": "cross_platform_comparison",
        "subcategory": "file_listing",
        "example_type": "cross_platform_translation",
        "user_request": "Proporciona los comandos equivalentes para listar todos los archivos, incluyendo ocultos, con permisos, propietario, tamaño legible y marcas de tiempo en Linux (Bash), Windows (PowerShell) y Windows (CMD).",
        "context": {
            "cwd": "~ o C:\\Users\\User",
            "user": "operador",
            "privileges": "standard",
            "system_state": "Entorno multiplataforma heterogéneo."
        },
        "analysis": [
            "En Linux/macOS (POSIX/Bash): el comando canónico es ls con banderas -l (formato largo), -a (todos incluyendo punto), -h (tamaños humanos).",
            "En Windows PowerShell: se utiliza Get-ChildItem con las banderas -Force (incluye archivos ocultos/sistema) y proyección de propiedades mediante Format-Table o Select-Object.",
            "En Windows CMD: se utiliza dir con el modificador /a (todos los atributos) y /q (propietario) o /o (orden)."
        ],
        "commands": [
            "# Linux / macOS (Bash / zsh):\nls -lah",
            "# Windows PowerShell:\nGet-ChildItem -Path . -Force | Select-Object Mode, Length, LastWriteTime, Name | Format-Table -AutoSize",
            "# Windows CMD:\ndir /a /q"
        ],
        "expected_output": "Linux/Bash:\ndrwxr-xr-x 4 user user 4.0K Sep 26 17:15 .\n-rw-r--r-- 1 user user  220 Sep 26 17:14 .bash_logout\n-rw-r--r-- 1 user user 3.7K Sep 26 17:14 .bashrc\n\nPowerShell:\nMode   Length LastWriteTime       Name\n----   ------ -------------       ----\nd----         26/09/2026 17:15:10 .git\n-a---     220 26/09/2026 17:14:02 .gitignore\n-a---    3820 26/09/2026 17:14:02 README.md\n\nCMD:\n26/09/2026  17:15    <DIR>          DOMAIN\\user    .\n26/09/2026  17:14               220 DOMAIN\\user    .gitignore",
        "verification": [
            "Cada comando revela los elementos con prefijo '.' o atributos ocultos en sus respectivos sistemas operativos."
        ],
        "failure_cases": [
            {
                "error": "'ls' no se reconoce como un comando interno o externo en CMD",
                "cause": "CMD clásico no incluye alias para comandos POSIX.",
                "recovery": "Utilizar 'dir' en CMD clásico o abrir PowerShell donde 'ls' existe como alias de 'Get-ChildItem'."
            }
        ],
        "alternatives": [
            "Usar 'exa' o 'eza' en Linux para salidas enriquecidas con colores y metadatos Git."
        ],
        "explanation": "La diferencia arquitectónica fundamental reside en que [[Bash]] produce flujos de texto plano sin tipar formateados por columnas de caracteres, mientras que [[PowerShell]] emite una colección de objetos fuertemente tipados (`System.IO.FileInfo`) que pueden ser filtrados numéricamente sin necesidad de `awk` o `grep`."
    },

    # 10. Containers & Docker: Composition, volume persistence and network bridge (instruction_to_multistep)
    {
        "id": "terminal_00000010",
        "os": "linux",
        "distribution": "debian",
        "shell": "bash",
        "difficulty": "intermediate",
        "category": "containers",
        "subcategory": "docker_compose_deploy",
        "example_type": "instruction_to_multistep",
        "user_request": "Despliega una pila de contenedores aislada con Docker Compose para PostgreSQL 16 y Redis 7 con volúmenes persistentes y una red tipo puente propia.",
        "context": {
            "cwd": "/opt/deploy",
            "user": "deployer",
            "privileges": "sudo o grupo docker",
            "system_state": "Debian 12, Docker Engine 27.2.0 y Docker Compose Plugin v2.29 instalados."
        },
        "analysis": [
            "Crear el directorio de despliegue y un archivo docker-compose.yml atómico con heredoc.",
            "Definir el servicio 'db' con imagen postgres:16-alpine, variables de entorno básicas y volumen persistente pgdata.",
            "Definir el servicio 'cache' con redis:7-alpine con persistencia appendonly y volumen redisdata.",
            "Definir la red bridge personalizada 'internal_net'.",
            "Desplegar en segundo plano con 'docker compose up -d'.",
            "Verificar el estado de salud de los contenedores con 'docker compose ps'."
        ],
        "commands": [
            "sudo mkdir -p /opt/deploy && cd /opt/deploy",
            "cat << 'EOF' | sudo tee docker-compose.yml > /dev/null\nservices:\n  db:\n    image: postgres:16-alpine\n    restart: unless-stopped\n    environment:\n      POSTGRES_DB: appdb\n      POSTGRES_USER: admin\n      POSTGRES_PASSWORD: DB_SECURE_PASSWORD\n    volumes:\n      - pgdata:/var/lib/postgresql/data\n    networks:\n      - internal_net\n\n  cache:\n    image: redis:7-alpine\n    command: redis-server --appendonly yes\n    restart: unless-stopped\n    volumes:\n      - redisdata:/data\n    networks:\n      - internal_net\n\nvolumes:\n  pgdata:\n  redisdata:\n\nnetworks:\n  internal_net:\n    driver: bridge\nEOF",
            "sudo docker compose up -d",
            "sudo docker compose ps"
        ],
        "expected_output": "[+] Running 4/4\n ✔ Network deploy_internal_net  Created\n ✔ Volume \"deploy_pgdata\"       Created\n ✔ Volume \"deploy_redisdata\"    Created\n ✔ Container deploy-db-1        Started\n ✔ Container deploy-cache-1     Started\nNAME                IMAGE                COMMAND                  SERVICE   CREATED         STATUS         PORTS\ndeploy-cache-1      redis:7-alpine       \"docker-entrypoint.s…\"   cache     5 seconds ago   Up 4 seconds   6379/tcp\ndeploy-db-1         postgres:16-alpine   \"docker-entrypoint.s…\"   db        5 seconds ago   Up 4 seconds   5432/tcp",
        "verification": [
            "docker compose ps confirma que ambos contenedores están en estado 'Up'.",
            "docker volume ls confirma la creación de los volúmenes persistentes aislados."
        ],
        "failure_cases": [
            {
                "error": "docker: 'compose' is not a docker command",
                "cause": "Está instalado el binario heredado de Python (docker-compose v1) en lugar del plugin v2 oficial de Docker.",
                "recovery": "Instalar 'docker-compose-plugin' mediante el repositorio oficial o invocar 'docker-compose up -d'."
            }
        ],
        "alternatives": [
            "Crear manualmente los contenedores con 'docker run -d --net ... -v ...'."
        ],
        "explanation": "El uso de [[Docker]] y Compose garantiza aislamiento de red mediante puentes virtuales (`bridge`), impidiendo que los puertos de PostgreSQL (5432) y Redis (6379) queden expuestos directamente al tráfico externo del host a menos que se defina la directiva explícita `ports`."
    },

    # 11. Git: Merge conflict recovery and clean commit history (failed_to_corrected)
    {
        "id": "terminal_00000011",
        "os": "linux",
        "distribution": "ubuntu",
        "shell": "bash",
        "difficulty": "intermediate",
        "category": "git_repositories",
        "subcategory": "merge_conflict",
        "example_type": "failed_to_corrected",
        "user_request": "Durante un 'git merge feature' se produjo un conflicto en el archivo 'main.py'. Diagnostica los marcadores de conflicto, resuelve priorizando la rama entrante y completa el merge.",
        "context": {
            "cwd": "/home/developer/app",
            "user": "developer",
            "privileges": "standard",
            "system_state": "Repositorio Git local, estado CONFLICT (content): Merge conflict in main.py."
        },
        "analysis": [
            "Comprobar el estado del árbol de trabajo con 'git status'.",
            "Inspeccionar las diferencias y marcadores de conflicto (<<<<<<< HEAD ... ======= ... >>>>>>> feature) con 'git diff'.",
            "Si la política es aceptar los cambios de la rama entrante, se puede checkout --theirs o editar el archivo.",
            "Usar 'git checkout --theirs main.py' para resolver inmediatamente a favor de la rama feature.",
            "Registrar el archivo en el índice con 'git add main.py' y finalizar el merge con 'git commit'."
        ],
        "commands": [
            "git status",
            "git checkout --theirs main.py",
            "git diff main.py",
            "git add main.py",
            "git commit -m 'Merge feature branch: resolved conflict in main.py favoring incoming changes'",
            "git log -n 1 --oneline"
        ],
        "expected_output": "On branch master\nYou have unmerged paths.\n  (fix conflicts and run \"git commit\")\n\nUnmerged paths:\n  both modified:   main.py\n\n[master a8f12c4] Merge feature branch: resolved conflict in main.py favoring incoming changes",
        "verification": [
            "git status reporta 'nothing to commit, working tree clean'.",
            "git log confirma la creación del commit de fusión con dos padres."
        ],
        "failure_cases": [
            {
                "error": "fatal: You have not concluded your merge (MERGE_HEAD exists)",
                "cause": "Se intentó cambiar de rama o ejecutar pull con un merge inconcluso.",
                "recovery": "Completar el commit de merge o abortar limpiamente con 'git merge --abort'."
            }
        ],
        "alternatives": [
            "Usar 'git mergetool' para resolución interactiva mediante herramientas gráficas como VSCode o KDiff3."
        ],
        "explanation": "Los conflictos en [[Git]] ocurren cuando dos ramas modifican las mismas líneas de un archivo desde su ancestro común. La opción `--theirs` descarta las modificaciones de la rama receptora (`HEAD`) e integra limpiamente el código de la rama fusionada (`MERGE_HEAD`)."
    },

    # 12. Hard Negatives: rm vs rm -rf directory semantics (instruction_to_command)
    {
        "id": "terminal_00000012",
        "os": "linux",
        "distribution": "debian",
        "shell": "bash",
        "difficulty": "beginner",
        "category": "filesystem",
        "subcategory": "safe_deletion",
        "example_type": "instruction_to_command",
        "user_request": "Explica y demuestra la diferencia semántica y de seguridad entre 'rm archivo.txt', 'rm -r carpeta/' y el riesgo destructivo de 'rm -rf'.",
        "context": {
            "cwd": "/tmp/test_workspace",
            "user": "developer",
            "privileges": "standard",
            "system_state": "Directorio de prueba con ficheros regulares y subcarpetas anidadas."
        },
        "analysis": [
            "El comando 'rm' básico únicamente elimina archivos regulares o enlaces simbólicos; falla inmediatamente con 'Is a directory' si el objetivo es una carpeta.",
            "El modificador '-r' (recursivo) desciende por la jerarquía de directorios eliminando contenido, solicitando confirmación si los ficheros carecen de permiso de escritura.",
            "El modificador '-f' (force) anula cualquier advertencia de confirmación interactiva e ignora ficheros inexistentes.",
            "Demostrar que 'rm' sobre un directorio arroja error controlado."
        ],
        "commands": [
            "mkdir -p dir_demo && touch dir_demo/file.txt",
            "rm dir_demo 2>&1 || true",
            "rm -r dir_demo"
        ],
        "expected_output": "rm: cannot remove 'dir_demo': Is a directory",
        "verification": [
            "El primer comando falla de forma segura protegiendo el directorio.",
            "El segundo comando 'rm -r' elimina la carpeta de manera explícita y controlada."
        ],
        "failure_cases": [
            {
                "error": "rm: cannot remove 'dir_demo/file.txt': Permission denied",
                "cause": "El usuario carece de permisos de escritura ('w') sobre el directorio contenedor.",
                "recovery": "Asignar permisos con 'chmod +w .' o ejecutar con el usuario propietario."
            }
        ],
        "alternatives": [
            "Utilizar 'rmdir' que únicamente elimina carpetas si están estrictamente vacías, garantizando seguridad absoluta."
        ],
        "explanation": "En la filosofía [[POSIX]], `rm` opera de forma irreversible ya que no existe un concepto nativo de papelera de reciclaje en el sistema de ficheros ext4/xfs. La bandera `-f` jamás debe combinarse con comodines ambiguos o variables de entorno no sanitizadas (e.g., `rm -rf $DIR/` cuando `$DIR` está vacía puede borrar `/`)."
    }
]

def main():
    os.makedirs(os.path.dirname(OUTPUT_SAMPLE_FILE), exist_ok=True)
    valid_count = 0
    errors = 0

    print("=" * 80)
    print("INICIANDO VALIDACIÓN ESTRICTA DEL ESQUEMA DEL DATASET DE CONTROL DE TERMINAL")
    print(f"Destino de Muestra: {OUTPUT_SAMPLE_FILE}")
    print("=" * 80)

    with open(OUTPUT_SAMPLE_FILE, "w", encoding="utf-8") as f:
        for idx, item in enumerate(VALIDATION_SAMPLES):
            try:
                validate_sample(item)
                line = json.dumps(item, ensure_ascii=False)
                f.write(line + "\n")
                valid_count += 1
                print(f"[VALID] ({idx+1}/{len(VALIDATION_SAMPLES)}) ID: {item['id']} | OS: {item['os']} | Cat: {item['category']} | Type: {item['example_type']}")
            except Exception as e:
                errors += 1
                print(f"[ERROR] En muestra ID {item.get('id', idx)}: {e}")

    print("=" * 80)
    print(f"RESUMEN DE VALIDACIÓN: {valid_count} VÁLIDOS | {errors} ERRORES")
    print(f"Muestra escrita exitosamente en: {OUTPUT_SAMPLE_FILE}")
    print("=" * 80)

if __name__ == "__main__":
    main()
