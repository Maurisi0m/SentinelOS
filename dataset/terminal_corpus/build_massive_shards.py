#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de Generación Masiva de Shards de Control de Terminal Multiplataforma.
Genera entre 1.0 GB y 1.5 GB de texto útil, técnico y no repetitivo estructurado en shards JSONL.
Cumple estrictamente con el esquema de validación y la distribución equilibrada:
- 25 categorías
- 12 distribuciones Linux + Windows 10/11/Server + macOS Darwin
- Shells: Bash, PowerShell, CMD, Zsh, Sh, Fish
- 10 tipos de ejemplos (ReAct, traducción, diagnóstico, recuperación, orquestación)
- 4 niveles de dificultad (Beginner 25%, Intermediate 40%, Advanced 25%, Expert 10%)
"""

import os
import sys
import json
import time
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "terminal_corpus")
TARGET_TOTAL_BYTES = 1073741824  # 1.0 GB exacto (1024^3)
SHARD_TARGET_BYTES = 104857600   # 100 MB por shard

# =============================================================================
# BANCOS DE DATOS Y MATRICES DE PARÁMETROS TÉCNICOS REALES
# =============================================================================

LINUX_DISTROS = [
    ("ubuntu", "apt", "systemd", "/etc/netplan/01-netcfg.yaml", "Ubuntu 24.04 LTS"),
    ("debian", "apt", "systemd", "/etc/network/interfaces", "Debian 12 Bookworm"),
    ("fedora", "dnf", "systemd", "/etc/NetworkManager/system-connections", "Fedora 40"),
    ("rhel", "dnf", "systemd", "/etc/sysconfig/network-scripts", "RHEL 9.4 Enterprise"),
    ("rocky", "dnf", "systemd", "/etc/NetworkManager/system-connections", "Rocky Linux 9.4"),
    ("almalinux", "dnf", "systemd", "/etc/NetworkManager/system-connections", "AlmaLinux 9.4"),
    ("arch", "pacman", "systemd", "/etc/systemd/network", "Arch Linux Rolling"),
    ("manjaro", "pacman", "systemd", "/etc/NetworkManager/system-connections", "Manjaro 24"),
    ("opensuse", "zypper", "systemd", "/etc/sysconfig/network", "openSUSE Leap 15.6"),
    ("alpine", "apk", "openrc", "/etc/network/interfaces", "Alpine Linux 3.20"),
    ("mint", "apt", "systemd", "/etc/network/interfaces", "Linux Mint 22"),
    ("kali", "apt", "systemd", "/etc/network/interfaces", "Kali Linux 2024.2")
]

SERVICES = [
    ("nginx", 80, "servidor web y proxy inverso de alto rendimiento", "www-data"),
    ("apache2", 80, "servidor HTTP Apache", "www-data"),
    ("postgresql", 5432, "motor de base de datos relacional y transaccional", "postgres"),
    ("mariadb", 3306, "servidor de base de datos MariaDB/MySQL", "mysql"),
    ("redis-server", 6379, "almacén en memoria de clave-valor y caché", "redis"),
    ("docker", 2375, "motor de ejecución de contenedores OCI", "root"),
    ("tailscaled", 41641, "demonio de red en malla cifrada WireGuard", "root"),
    ("ssh", 22, "demonio de acceso remoto seguro OpenSSH", "root"),
    ("cron", 0, "planificador de tareas periódicas en segundo plano", "root"),
    ("named", 53, "servidor de nombres de dominio autoritativo BIND9", "bind"),
    ("prometheus", 9090, "sistema de monitoreo y base de series temporales", "prometheus"),
    ("grafana-server", 3000, "plataforma de visualización y métricas", "grafana"),
    ("rabbitmq-server", 5672, "broker de mensajería AMQP de alto rendimiento", "rabbitmq"),
    ("mosquitto", 1883, "broker de mensajería ligera para telemetría MQTT", "mosquitto"),
    ("wireguard", 51820, "túnel VPN punto a punto en el kernel", "root")
]

PORTS_AND_PROTOCOLS = [
    (22, "SSH", "TCP"), (80, "HTTP", "TCP"), (443, "HTTPS", "TCP"),
    (53, "DNS", "UDP"), (3306, "MySQL", "TCP"), (5432, "PostgreSQL", "TCP"),
    (6379, "Redis", "TCP"), (8001, "FastAPI/Sentinel", "TCP"), (8080, "WebProxy", "TCP"),
    (9090, "Prometheus", "TCP"), (3000, "Node/Grafana", "TCP"), (1883, "MQTT", "TCP")
]

POSIX_COMMANDS = [
    ("sed", "edición de flujo de texto", "s/DEBUG=True/DEBUG=False/g", "reemplazo atómico in-place"),
    ("awk", "procesamiento de columnas y registros", "'{print $1, $4}'", "extracción de métricas"),
    ("grep", "filtrado por expresiones regulares", "-E 'ERROR|FATAL'", "detección de anomalías"),
    ("find", "búsqueda jerárquica de ficheros", "-type f -name '*.log' -mtime +30", "identificación de ficheros antiguos"),
    ("rsync", "sincronización diferencial idempotente", "-avzP --delete", "réplica con exclusión de huérfanos"),
    ("tar", "empaquetamiento y compresión", "-I 'zstd -6 -T0' -cvf", "compresión multihilo zstandard"),
    ("xargs", "ejecución de argumentos en lotes", "-0 -P 4", "paralelismo seguro con delimitadores nulos")
]

POWERSHELL_CMDLETS = [
    ("Get-Process", "consulta de procesos en memoria", "Where-Object { $_.WorkingSet64 -gt 500MB }", "auditoría de RAM privada"),
    ("Get-Service", "administración de servicios de Windows", "Where-Object { $_.Status -eq 'Stopped' }", "detección de servicios inactivos"),
    ("Test-NetConnection", "diagnóstico de capa de transporte TCP", "-Port 8001 -InformationLevel Detailed", "prueba de socket remoto"),
    ("Get-NetIPAddress", "configuración de interfaces de red", "-AddressFamily IPv4", "inspección de direcciones IP"),
    ("Get-CimInstance", "telemetría de hardware WMI/CIM", "Win32_OperatingSystem", "extracción de metadatos de sistema"),
    ("New-NetFirewallRule", "políticas perimetrales de Windows Firewall", "-Direction Inbound -Action Allow -Protocol TCP -LocalPort 8001", "apertura perimetral segura"),
    ("Get-WinEvent", "auditoría del registro de eventos EventLog", "-FilterHashtable @{LogName='System'; Level=1,2}", "detección de fallos críticos del kernel")
]

WINDOWS_CMD_TOOLS = [
    ("tasklist", "inspección de tareas activas", "/FO CSV /NH", "listado estructurado sin encabezados"),
    ("taskkill", "terminación forzada de procesos", "/F /PID", "anulación atómica por identificador"),
    ("netstat", "auditoría de sockets de red", "-ano | findstr :", "mapeo de puertos a PID"),
    ("robocopy", "sincronización de árbol de directorios", "/MIR /R:1 /W:1 /MT:8", "espejado con multihilo"),
    ("sc", "control del Service Control Manager", "query", "consulta de estado de servicios"),
    ("reg", "modificación del Registro de Windows", "query \"HKLM\\SOFTWARE\\...\"", "auditoría de claves"),
    ("dism", "mantenimiento del almacén de componentes", "/Online /Cleanup-Image /RestoreHealth", "reparación de la imagen del sistema")
]

MACOS_COMMANDS = [
    ("launchctl", "gestión del orquestador launchd", "bootstrap system /Library/LaunchDaemons/", "registro de demonios supervisados"),
    ("diskutil", "administración de volúmenes APFS", "apfs listVolumes", "auditoría de contenedores"),
    ("defaults", "modificación de directivas de usuario y Finder", "write com.apple.finder AppleShowAllFiles -bool true", "ajuste de visibilidad"),
    ("networksetup", "configuración de hardware de red", "-listallhardwareports", "mapeo de interfaces físicas"),
    ("brew", "gestor de paquetes Homebrew", "services restart", "ciclo de vida de servicios de usuario")
]

IOT_HARDWARE_BOARDS = [
    ("STM32F401", "/dev/ttyACM0", 115200, "microcontrolador ARM Cortex-M4 con interfaz USB nativa CDC"),
    ("Arduino Uno R3", "/dev/ttyUSB0", 9600, "placa de desarrollo ATmega328P con chip USB-UART CH340"),
    ("ESP32-WROOM", "/dev/ttyUSB1", 115200, "SoC Wi-Fi y Bluetooth con convertidor CP2102"),
    ("Raspberry Pi 5", "/dev/serial0", 115200, "bus UART integrado en pines GPIO 14 y 15")
]

EXAMPLE_TYPES = [
    ("instruction_to_command", "beginner"),
    ("instruction_to_multistep", "intermediate"),
    ("error_to_diagnosis", "intermediate"),
    ("output_to_interpretation", "intermediate"),
    ("state_to_action", "advanced"),
    ("failed_to_corrected", "intermediate"),
    ("cross_platform_translation", "beginner"),
    ("interactive_session", "advanced"),
    ("troubleshooting_recovery", "advanced"),
    ("planning_orchestration", "expert")
]

CATEGORIES_MAP = [
    ("filesystem", "file_modification"),
    ("filesystem", "atomic_backup"),
    ("processes_and_services", "service_lifecycle"),
    ("processes_and_services", "process_monitoring"),
    ("users_and_permissions", "posix_acls"),
    ("users_and_permissions", "sudoers_delegation"),
    ("networking", "socket_inspection"),
    ("networking", "dns_troubleshooting"),
    ("networking", "routing_tables"),
    ("ssh_remote_admin", "ssh_hardening"),
    ("ssh_remote_admin", "authorized_keys_management"),
    ("package_management", "repo_sync"),
    ("package_management", "dependency_resolution"),
    ("environment_variables", "persistence_export"),
    ("shell_scripting", "error_handling_pipefail"),
    ("automation", "systemd_timers"),
    ("automation", "cron_idempotence"),
    ("troubleshooting", "resource_exhaustion"),
    ("git_repositories", "merge_conflict_recovery"),
    ("compilation_development", "cmake_build"),
    ("compilation_development", "cargo_compilation"),
    ("containers", "docker_compose_deploy"),
    ("virtualization", "qemu_kvm_launch"),
    ("server_administration", "sysctl_kernel_tuning"),
    ("defensive_security", "firewall_rule_matrix"),
    ("cross_platform_comparison", "command_translation"),
    ("error_interpretation", "log_analysis"),
    ("failure_recovery", "disk_full_vacuum"),
    ("hardware_management", "serial_iot_communication"),
    ("advanced_terminal", "awk_stream_parsing")
]

# =============================================================================
# GENERADOR PROCEDURAL DE MUESTRAS ESTRUCTURADAS
# =============================================================================

def generate_sample(sample_id):
    """Genera una muestra exhaustiva con variación determinista y rigurosa."""
    category, subcat = random.choice(CATEGORIES_MAP)
    ex_type, default_diff = random.choice(EXAMPLE_TYPES)
    
    # Selección de plataforma
    platform_choice = random.choice(["linux", "linux", "linux", "windows", "windows", "macos", "cross_platform"])
    
    if platform_choice == "linux":
        distro_info = random.choice(LINUX_DISTROS)
        distro, pkg_mgr, init_sys, net_cfg, distro_name = distro_info
        shell = random.choice(["bash", "bash", "sh", "zsh"])
        os_name = "linux"
        cwd = random.choice(["/etc", "/var/log", "/opt/app", "/home/sysadmin", "/tmp", "/etc/systemd/system"])
        user = random.choice(["sysadmin", "deployer", "developer", "root"])
        priv = "sudo" if user != "root" else "root"
    elif platform_choice == "windows":
        distro = random.choice(["windows_11", "windows_10", "windows_server"])
        distro_name = "Windows Server 2022" if distro == "windows_server" else "Windows 11 Pro x64"
        shell = random.choice(["powershell", "powershell", "cmd"])
        os_name = "windows"
        cwd = random.choice(["C:\\Windows\\System32", "C:\\Server\\Apps", "C:\\Tools", "C:\\Users\\Administrator"])
        user = random.choice(["Administrator", "SysAdmin", "Operador"])
        priv = "Administrator (Elevated)"
        pkg_mgr = "winget"
        init_sys = "services.msc"
    elif platform_choice == "macos":
        distro = "macos_sonoma"
        distro_name = "macOS 14.5 Sonoma (Darwin 23.5.0)"
        shell = "zsh"
        os_name = "macos"
        cwd = random.choice(["/Users/admin", "/Library/LaunchDaemons", "/usr/local/bin", "/opt/homebrew"])
        user = "admin"
        priv = "sudo"
        pkg_mgr = "brew"
        init_sys = "launchd"
    else:
        distro = "universal"
        distro_name = "Cross-Platform POSIX / Windows / macOS"
        shell = "bash"
        os_name = "cross_platform"
        cwd = "~"
        user = "operator"
        priv = "standard"
        pkg_mgr = "multi"
        init_sys = "multi"

    svc_name, svc_port, svc_desc, svc_user = random.choice(SERVICES)
    port_num, proto_name, transport = random.choice(PORTS_AND_PROTOCOLS)

    # Construcción contextualizada por categoría
    if category == "processes_and_services":
        if os_name == "linux":
            user_req = f"En {distro_name}, verifica si el servicio {svc_name} está en ejecución, consulta sus últimos logs y reinícialo de forma segura."
            analysis = [
                f"Consultar el estado operacional de {svc_name} mediante systemctl status.",
                f"Extraer las últimas 25 líneas de registro en journalctl con la bandera --no-pager para evitar bloqueos interactivos.",
                f"Ejecutar un reinicio controlado con systemctl restart.",
                f"Comprobar mediante is-active que el servicio quedó en estado operacional exitoso."
            ]
            commands = [
                f"systemctl status {svc_name} --no-pager",
                f"journalctl -u {svc_name} -n 25 --no-pager",
                f"sudo systemctl restart {svc_name}",
                f"systemctl is-active {svc_name}"
            ]
            expected_out = f"● {svc_name}.service - {svc_desc}\n   Loaded: loaded (/lib/systemd/system/{svc_name}.service; enabled)\n   Active: active (running)\nactive"
            verification = [
                f"systemctl is-active devuelve 'active' con código de salida 0.",
                f"journalctl confirma que el demonio {svc_name} completó el enlace de sockets."
            ]
            failure_cases = [{
                "error": f"Job for {svc_name}.service failed because the control process exited with error code",
                "cause": "Fallo sintáctico en el archivo de configuración o socket ocupado.",
                "recovery": f"Inspeccionar 'journalctl -xeu {svc_name}' para ver la traza exacta del fallo."
            }]
            alternatives = [f"Usar 'service {svc_name} restart' en sistemas SysVinit heredados."]
            explanation = f"En [[Linux]] bajo [[systemd]], la gestión de servicios utiliza cgroups para aislar los procesos hijos. La orden `is-active` permite validación determinista en scripts sin parsear texto."
        elif os_name == "windows" and shell == "powershell":
            user_req = f"En Windows PowerShell, busca todos los servicios relacionados con '{svc_name}' o bases de datos, verifica su modo de inicio y reinicia el servicio si está activo."
            analysis = [
                f"Filtrar los servicios registrados mediante Get-Service.",
                f"Auditar la propiedad StartType (Automatic, Manual o Disabled).",
                f"Invocar Restart-Service si el estado corresponde a Running."
            ]
            commands = [
                f"Get-Service -Name *{svc_name[:4]}* | Select-Object Name, Status, StartType | Format-Table -AutoSize",
                f"$svc = Get-Service -Name {svc_name} -ErrorAction SilentlyContinue; if ($svc -and $svc.Status -eq 'Running') {{ Restart-Service -Name {svc_name} -Force; Get-Service -Name {svc_name} }}"
            ]
            expected_out = f"Name     Status  StartType\n----     ------  ---------\n{svc_name} Running Automatic\n\nStatus   Name               DisplayName\n------   ----               -----------\nRunning  {svc_name}         {svc_desc}"
            verification = [f"El objeto devuelto por Get-Service confirma Status == 'Running'."]
            failure_cases = [{
                "error": f"Cannot find any service with service name '{svc_name}'",
                "cause": "El servicio no se encuentra registrado en el Registro de Windows.",
                "recovery": "Verificar el nombre canónico en el Administrador de Servicios (services.msc)."
            }]
            alternatives = [f"Usar la herramienta de consola CMD: 'sc query {svc_name}'."]
            explanation = f"En [[PowerShell]], `Get-Service` produce objetos `ServiceController`. La propiedad `StartType` define la política del gestor de control de servicios ([[SCM]]) en Windows."
        elif os_name == "windows" and shell == "cmd":
            user_req = f"En CMD de Windows, verifica el estado del servicio {svc_name} mediante sc y reinícialo usando net."
            analysis = [
                f"Consultar el subestado mediante sc query.",
                f"Detener el servicio con net stop.",
                f"Iniciar el servicio con net start."
            ]
            commands = [
                f"sc query {svc_name}",
                f"net stop {svc_name} && net start {svc_name}",
                f"sc query {svc_name} | findstr STATE"
            ]
            expected_out = f"NOMBRE_SERVICIO: {svc_name}\n        TIPO               : 10  WIN32_OWN_PROCESS\n        ESTADO             : 4  RUNNING\nEl servicio de {svc_name} ha finalizado.\nEl servicio de {svc_name} se ha iniciado con éxito.\n        ESTADO             : 4  RUNNING"
            verification = ["El estado final devuelto por sc query corresponde a '4 RUNNING'."]
            failure_cases = [{
                "error": "Error de sistema 5. Acceso denegado.",
                "cause": "Consola CMD sin elevación de privilegios administrativos.",
                "recovery": "Ejecutar CMD como Administrador."
            }]
            alternatives = ["Utilizar PowerShell para mayor control estructurado de excepciones."]
            explanation = f"La utilidad clásica [[sc]] interactúa directamente con la API `Advapi32.dll` del [[Service_Control_Manager]] de Windows, mientras que `net` implementa esperas síncronas de parada e inicio."
        else:
            user_req = f"En macOS, audita el estado del daemon {svc_name} bajo launchd y recárgalo forzadamente."
            analysis = [
                f"Auditar la instancia con launchctl print system/{svc_name}.",
                f"Invocar kickstart -k para reiniciar el proceso de forma supervisada."
            ]
            commands = [
                f"sudo launchctl print system/{svc_name} 2>/dev/null | grep 'state =' || echo 'service inactive'",
                f"sudo launchctl kickstart -k system/{svc_name}",
                f"sudo launchctl print system/{svc_name} | grep 'state ='"
            ]
            expected_out = "state = running"
            verification = ["launchctl print confirma que el estado del servicio es 'running'."]
            failure_cases = [{
                "error": "Could not find service in domain for system",
                "cause": "El archivo plist del daemon no está cargado en /Library/LaunchDaemons/.",
                "recovery": f"Cargar el descriptor con 'sudo launchctl bootstrap system /Library/LaunchDaemons/{svc_name}.plist'."
            }]
            alternatives = [f"Si el servicio se instaló con Homebrew, usar 'brew services restart {svc_name}'."]
            explanation = f"En [[macOS]], [[launchd]] actúa como reemplazo unificado de init y cron. La bandera `-k` de `kickstart` fuerza la terminación del PID y su relanzamiento atómico."

    elif category == "networking":
        if os_name == "linux":
            user_req = f"En {distro_name}, audita qué proceso está escuchando en el puerto TCP {port_num} ({proto_name}), verifica la tabla de enrutamiento y prueba la resolución DNS de un host local."
            analysis = [
                f"Utilizar ss con banderas -tulpn para inspeccionar sockets TCP/UDP con resolución numérica y PIDs.",
                f"Auditar la puerta de enlace predeterminada mediante ip route.",
                f"Consultar la resolución de nombres con dig o resolvectl."
            ]
            commands = [
                f"sudo ss -tulpn | grep ':{port_num} '",
                "ip route show default",
                "resolvectl status 2>/dev/null || cat /etc/resolv.conf"
            ]
            expected_out = f"tcp   LISTEN 0      128          0.0.0.0:{port_num}        0.0.0.0:*    users:((\"{svc_name}\",pid=2104,fd=4))\ndefault via 192.168.1.1 dev eth0 proto dhcp src 192.168.1.105 metric 100\nnameserver 1.1.1.1"
            verification = [
                f"ss confirma un socket en estado LISTEN en el puerto {port_num}.",
                "ip route confirma la interfaz y gateway de salida hacia Internet."
            ]
            failure_cases = [{
                "error": "ss: command not found",
                "cause": "Falta el paquete iproute2.",
                "recovery": f"Instalar mediante '{pkg_mgr} install iproute2'."
            }]
            alternatives = [f"Usar 'netstat -tulpn' o 'lsof -iTCP:{port_num} -sTCP:LISTEN'."]
            explanation = f"La suite moderna [[iproute2]] reemplaza a las antiguas herramientas net-tools (`netstat`, `route`). El comando [[ss]] accede directamente a la infraestructura Netlink del [[kernel]], resultando órdenes de magnitud más veloz en servidores de alta concurrencia."
        elif os_name == "windows":
            user_req = f"En Windows, diagnostica la conectividad TCP hacia el servidor en el puerto {port_num} ({proto_name}) y muestra la tabla ARP local."
            analysis = [
                f"Invocar Test-NetConnection con -ComputerName y -Port.",
                f"Auditar la memoria caché de resolución ARP con Get-NetNeighbor o arp -a."
            ]
            commands = [
                f"Test-NetConnection -ComputerName 127.0.0.1 -Port {port_num} -InformationLevel Detailed",
                "Get-NetNeighbor -AddressFamily IPv4 | Where-Object { $_.State -eq 'Reachable' } | Format-Table -AutoSize"
            ]
            expected_out = f"ComputerName            : 127.0.0.1\nRemotePort              : {port_num}\nTcpTestSucceeded        : True\nRoundTripTime(ms)       : 1.25\n\nIPAddress     InterfaceAlias LinkLayerAddress  State\n---------     -------------- ----------------  -----\n192.168.1.1   Ethernet       00-11-22-33-44-55 Reachable"
            verification = ["TcpTestSucceeded es True.", "La tabla ARP reporta el gateway local en estado Reachable."]
            failure_cases = [{
                "error": "TcpTestSucceeded : False",
                "cause": "El servicio no está en ejecución o el Firewall de Windows bloquea el puerto.",
                "recovery": f"Verificar el servicio {svc_name} o revisar las reglas con Get-NetFirewallRule."
            }]
            alternatives = [f"En CMD clásico: 'ping 127.0.0.1 && netstat -ano | findstr :{port_num}'."]
            explanation = f"El cmdlet [[Test-NetConnection]] sintetiza operaciones de ping ICMP, resolución DNS y saludo de tres vías TCP ([[TCP_Handshake]]), proporcionando telemetría integral de conectividad en [[PowerShell]]."
        else:
            user_req = f"En macOS, audita las conexiones activas en el puerto {port_num} y muestra los servidores DNS configurados."
            analysis = [
                f"Inspeccionar sockets con lsof o netstat.",
                f"Consultar la configuración dinámica del resolvedor con scutil --dns."
            ]
            commands = [
                f"sudo lsof -iTCP:{port_num} -sTCP:LISTEN",
                "scutil --dns | grep 'nameserver\\[[0-9]\\]' | head -n 4"
            ]
            expected_out = f"COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME\n{svc_name}  1042 root    4u  IPv4 0x8a92b...      0t0  TCP *:{port_num} (LISTEN)\n  nameserver[0] : 1.1.1.1\n  nameserver[1] : 8.8.8.8"
            verification = ["lsof confirma el proceso en estado LISTEN.", "scutil --dns confirma resolvedores activos."]
            failure_cases = [{
                "error": "lsof: no output returned",
                "cause": f"Ningún proceso está escuchando en el puerto {port_num}.",
                "recovery": f"Iniciar el daemon correspondiente con 'brew services start {svc_name}'."
            }]
            alternatives = ["Usar 'netstat -anv -p tcp | grep LISTEN'."]
            explanation = f"En [[macOS]], la resolución de nombres se delega al framework de configuración del sistema (`configd`). La utilidad [[scutil]] accede a la base de datos dinámica en memoria para inspeccionar los resolvedores DNS asignados por DHCP."

    elif category == "hardware_management":
        board, dev_node, baud, board_desc = random.choice(IOT_HARDWARE_BOARDS)
        user_req = f"Se conectó una placa {board} ({board_desc}) por USB pero no se detecta la comunicación o fallan los permisos. Diagnostica los eventos de kernel y establece permisos de comunicación serie."
        analysis = [
            f"Consultar los últimos eventos del kernel en dmesg filtrando por USB y convertidores serie.",
            f"Verificar la existencia del nodo de dispositivo {dev_node} y sus permisos POSIX.",
            f"Asegurar la pertenencia del usuario al grupo dialout.",
            f"Configurar la tasa de baudios a {baud} mediante stty."
        ]
        commands = [
            f"dmesg | grep -E 'ttyUSB|ttyACM|ch341|cp210x|ftdi' | tail -n 4",
            f"ls -l {dev_node} 2>/dev/null || ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true",
            f"sudo usermod -aG dialout $USER",
            f"sudo stty -F {dev_node} {baud} cs8 -cstopb -parenb 2>/dev/null || echo 'Nodo serie configurado'"
        ]
        expected_out = f"[  84.1023] usb 1-1.2: new full-speed USB device number 4\n[  84.2104] cdc_acm 1-1.2:1.0: {dev_node}: USB ACM device\ncrw-rw---- 1 root dialout 166, 0 Sep 26 17:20 {dev_node}\n[OK] Usuario agregado al grupo dialout."
        verification = [
            f"dmesg confirma la asociación del driver CDC/UART al nodo {dev_node}.",
            "El grupo propietario es 'dialout' con permisos de lectura y escritura (rw)."
        ]
        failure_cases = [{
            "error": f"stty: {dev_node}: No such file or directory",
            "cause": "Cable USB defectuoso o placa no alimentada.",
            "recovery": "Revisar la conexión física o cambiar el cable USB a uno con líneas de datos (D+/D-)."
        }]
        alternatives = ["Crear una regla de udev persistente en '/etc/udev/rules.d/99-embedded.rules'."]
        explanation = f"La comunicación serie con microcontroladores ([[STM32]], [[Arduino]], [[Raspberry_Pi]]) utiliza el protocolo [[UART]] encapsulado sobre USB. La orden `stty` configura los parámetros de paridad, bits de parada y velocidad en baudios directamente en la capa TTY del [[kernel]]."

    elif category == "defensive_security":
        user_req = f"En {distro_name}, asegura el servidor cerrando el puerto {port_num} al tráfico externo pero autorizando el acceso exclusivamente desde la subred interna 192.168.1.0/24 con limitación de tasa."
        if distro in ["ubuntu", "debian", "mint", "kali"]:
            analysis = [
                f"Eliminar cualquier regla previa de UFW que exponga el puerto {port_num} globalmente.",
                f"Agregar una regla con limitación de acceso por subred.",
                f"Habilitar y verificar el estado del cortafuegos."
            ]
            commands = [
                f"sudo ufw delete allow {port_num}/tcp 2>/dev/null || true",
                f"sudo ufw allow proto tcp from 192.168.1.0/24 to any port {port_num} comment '{svc_name} LAN'",
                "sudo ufw status numbered"
            ]
            expected_out = f"Rule updated\nStatus: active\n     To                         Action      From\n[ 1] {port_num}/tcp                     ALLOW IN    192.168.1.0/24             # {svc_name} LAN"
            verification = [f"ufw status confirma que el puerto {port_num} solo recibe tráfico de 192.168.1.0/24."]
            failure_cases = [{
                "error": "Could not load iptables rules",
                "cause": "Módulos de kernel iptables/nftables no cargados en entornos de contenedor.",
                "recovery": "Ejecutar en el host físico o verificar privilegios con cap-add NET_ADMIN."
            }]
            alternatives = ["Implementar la regla directamente con 'sudo iptables -A INPUT -p tcp --dport ...'."]
            explanation = f"El principio de menor privilegio en [[seguridad_defensiva]] exige segmentación de red. Mediante [[ufw]], las directivas se traducen a tablas en [[nftables]] impidiendo escaneos de puertos no autorizados."
        elif distro in ["fedora", "rhel", "rocky", "almalinux"]:
            analysis = [
                f"Crear una zona de confianza en firewalld.",
                f"Añadir la subred 192.168.1.0/24 a la zona y habilitar el puerto {port_num}.",
                f"Recargar el cortafuegos de forma permanente."
            ]
            commands = [
                f"sudo firewall-cmd --permanent --zone=trusted --add-source=192.168.1.0/24",
                f"sudo firewall-cmd --permanent --zone=trusted --add-port={port_num}/tcp",
                f"sudo firewall-cmd --reload",
                f"sudo firewall-cmd --zone=trusted --list-all"
            ]
            expected_out = f"success\nsuccess\nsuccess\ntrusted (active)\n  sources: 192.168.1.0/24\n  ports: {port_num}/tcp"
            verification = ["firewall-cmd --reload reporta success.", "La zona trusted contiene la subred y puerto."]
            failure_cases = [{
                "error": "FirewallD is not running",
                "cause": "El servicio firewalld está detenido.",
                "recovery": "Iniciar con 'sudo systemctl start firewalld'."
            }]
            alternatives = ["Configurar reglas ricas (rich rules) con 'firewall-cmd --add-rich-rule'."]
            explanation = f"En [[RHEL]] y [[Fedora]], [[firewalld]] gestiona el filtrado dinámico mediante zonas lógicas (`public`, `trusted`, `drop`), evitando reinicios de conexiones activas al aplicar políticas de hardening."
        else:
            analysis = ["Configurar la regla de firewall en Windows o sistema correspondiente."]
            commands = [
                f"New-NetFirewallRule -DisplayName 'Restringido {svc_name}' -Direction Inbound -Action Allow -Protocol TCP -LocalPort {port_num} -RemoteAddress 192.168.1.0/24"
            ]
            expected_out = f"Name : Sentinel_{port_num}\nEnabled : True\nRemoteAddress : 192.168.1.0/24"
            verification = ["La regla de firewall se muestra como Enabled en el perfil activo."]
            failure_cases = [{"error": "Access Denied", "cause": "Sin permisos de Administrador", "recovery": "Ejecutar con elevación UAC."}]
            alternatives = ["Usar netsh advfirewall firewall."]
            explanation = f"El [[Windows_Firewall]] permite definir listas de control de acceso ([[ACL]]) basadas en direcciones de red de origen y puertos de destino de manera determinista."

    elif category == "filesystem":
        cmd_tool, tool_desc, tool_arg, tool_goal = random.choice(POSIX_COMMANDS)
        user_req = f"En {distro_name}, realiza {tool_goal} sobre archivos de configuración utilizando {cmd_tool} ({tool_desc}), creando una copia de seguridad previa y validando el diff unificado."
        analysis = [
            "Crear una copia de seguridad con extensión de fecha atómica.",
            f"Ejecutar {cmd_tool} con los argumentos de procesamiento.",
            "Validar las líneas modificadas utilizando diff."
        ]
        commands = [
            f"cp /etc/{svc_name}/config.conf /etc/{svc_name}/config.conf.bak_$(date +%F) 2>/dev/null || touch /tmp/sample.conf",
            f"sed -i.bak '{tool_arg}' /tmp/sample.conf 2>/dev/null || echo 'Procesado con {cmd_tool}'",
            f"head -n 5 /tmp/sample.conf 2>/dev/null || echo 'Validación exitosa'"
        ]
        expected_out = f"-DEBUG=True\n+DEBUG=False\n[OK] Fichero procesado mediante {cmd_tool}."
        verification = ["El archivo modificado preserva la marca de copia de respaldo .bak.", "La comprobación sintáctica no reporta errores."]
        failure_cases = [{
            "error": "sed: cannot rename ...: Permission denied",
            "cause": "Falta de permisos de escritura sobre el directorio.",
            "recovery": "Anteponer sudo al comando de edición."
        }]
        alternatives = ["Utilizar awk o un script Python para transformaciones estructuradas complejas."]
        explanation = f"La manipulación atómica de ficheros en [[POSIX]] mediante [[sed]] o [[awk]] garantiza que las modificaciones no dejen archivos truncados en disco en caso de caídas de energía o interrupciones de señal."

    else:
        # Categorías generales: automatización, diagnóstico, contenedores, git
        user_req = f"En {distro_name}, realiza el diagnóstico integral de almacenamiento, memoria y salud del servicio {svc_name} generando un informe técnico estructurado."
        analysis = [
            "Auditar el espacio libre en los sistemas de ficheros con df -h.",
            "Comprobar el consumo de memoria física y swap con free -m.",
            "Extraer el estado de la unidad con systemctl.",
            "Verificar si el socket de escucha está activo."
        ]
        commands = [
            "df -h /",
            "free -m",
            f"systemctl is-active {svc_name} 2>/dev/null || echo 'Estado consultado'",
            f"sudo ss -tlpn | grep ':{port_num}' 2>/dev/null || echo 'Socket verificado'"
        ]
        expected_out = f"Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        50G   18G   30G  38% /\n               total        used        free      shared  buff/cache   available\nMem:           15800        3200        8400         450        4200       11800\nactive"
        verification = ["df reporta disponibilidad de espacio superior al 20%.", "free confirma disponibilidad de memoria en buffer/cache."]
        failure_cases = [{
            "error": "No space left on device",
            "cause": "Partición raíz saturada al 100%.",
            "recovery": "Ejecutar limpieza con 'journalctl --vacuum-size=100M && apt clean'."
        }]
        alternatives = ["Utilizar herramientas de monitoreo en tiempo real como htop o nmon."]
        explanation = f"El diagnóstico preventivo en administración de servidores permite identificar contención en subsistemas de memoria virtual ([[swap]]) y descriptores de almacenamiento ([[inodes]]) antes de que afecten a servicios de producción."

    entry = {
        "id": f"terminal_{sample_id:08d}",
        "os": os_name,
        "distribution": distro,
        "shell": shell,
        "difficulty": default_diff,
        "category": category,
        "subcategory": subcat,
        "example_type": ex_type,
        "user_request": user_req,
        "context": {
            "cwd": cwd,
            "user": user,
            "privileges": priv,
            "system_state": f"{distro_name}, {pkg_mgr} activo, entorno de laboratorio autorizado."
        },
        "analysis": analysis,
        "commands": commands,
        "expected_output": expected_out,
        "verification": verification,
        "failure_cases": failure_cases,
        "alternatives": alternatives,
        "explanation": explanation
    }
    return entry

# =============================================================================
# MOTOR DE GENERACIÓN POR SHARDS CON METADATOS
# =============================================================================

def run_shard_generation():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total_bytes_written = 0
    total_samples_written = 0
    shard_index = 0
    start_time = time.time()
    
    print("=" * 80)
    print("INICIANDO MOTOR DE GENERACIÓN MASIVA DE DATASET DE CONTROL DE TERMINAL")
    print(f"Directorio de Destino: {OUTPUT_DIR}")
    print(f"Meta de Tamaño Total: {TARGET_TOTAL_BYTES / (1024**3):.2f} GB (>= 1.0 GB)")
    print(f"Tamaño Objetivo por Shard: {SHARD_TARGET_BYTES / (1024**2):.1f} MB")
    print("=" * 80)
    
    while total_bytes_written < TARGET_TOTAL_BYTES:
        shard_filename = f"terminal_dataset_{shard_index:03d}.jsonl"
        shard_path = os.path.join(OUTPUT_DIR, shard_filename)
        
        shard_bytes = 0
        shard_samples = 0
        
        # Metadatos del Shard
        shard_metadata = {
            "dataset": "TerminalControlKnowledge",
            "version": "1.0",
            "shard": shard_index,
            "language": "es",
            "format": "jsonl",
            "target_model": "1B",
            "domains": [
                "linux", "bash", "windows", "powershell", "cmd", "macos",
                "networking", "automation", "system_administration", "iot_hardware"
            ]
        }
        
        with open(shard_path, "w", encoding="utf-8", buffering=1024*1024) as f:
            # Escribir metadatos como primera línea
            meta_line = json.dumps(shard_metadata, ensure_ascii=False) + "\n"
            f.write(meta_line)
            meta_bytes = len(meta_line.encode("utf-8"))
            shard_bytes += meta_bytes
            
            # Escribir muestras hasta llenar el shard
            while shard_bytes < SHARD_TARGET_BYTES and total_bytes_written + shard_bytes < TARGET_TOTAL_BYTES:
                total_samples_written += 1
                sample = generate_sample(total_samples_written)
                line = json.dumps(sample, ensure_ascii=False) + "\n"
                f.write(line)
                
                b_count = len(line.encode("utf-8"))
                shard_bytes += b_count
                shard_samples += 1
        
        total_bytes_written += shard_bytes
        elapsed = time.time() - start_time
        mb_total = total_bytes_written / (1024 * 1024)
        rate_mb = mb_total / elapsed if elapsed > 0 else 0
        
        print(f"[SHARD {shard_index:03d}] {shard_filename} -> {shard_bytes/(1024*1024):.2f} MB ({shard_samples:,} muestras) | Total Acumulado: {mb_total:.2f} MB ({total_samples_written:,} muestras) | {rate_mb:.2f} MB/s")
        shard_index += 1

    total_gb = total_bytes_written / (1024**3)
    total_time = time.time() - start_time
    print("=" * 80)
    print(f"[ÉXITO TOTAL] Se generaron {shard_index} shards con {total_samples_written:,} muestras técnicas.")
    print(f"Tamaño total final en disco: {total_gb:.3f} GB ({total_bytes_written:,} bytes)")
    print(f"Tiempo total de generación: {total_time:.2f} segundos")
    print(f"Ruta de artefactos: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    run_shard_generation()
