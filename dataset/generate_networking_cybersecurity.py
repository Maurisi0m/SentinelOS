#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador Especializado de Redes de Computadoras, Bits y Ciberseguridad para SENTINEL
Cubre a profundidad extrema:
- Nivel de enlace, bits, bytes, tramas Ethernet 802.3, MTU, CRC-32.
- Subnetting, VLSM, IPv4 e IPv6 a nivel de bits y máscaras.
- Capa de red y transporte: TCP, UDP, Handshakes, MSS, Congestión (BBR/CUBIC), Enrutamiento.
- Servicios esenciales: ARP, DNS, DHCP, Sockets en C y Python (epoll, Berkeley API).
- Ciberseguridad: Criptografía aplicada (AES-GCM, ChaCha20, Ed25519), TLS 1.3 a nivel de paquetes.
- Defensas en Linux: nftables, SYN cookies, Buffer Overflows (Canaries, ASLR, DEP/NX).
- Seguridad Web/APIs (CSP, SameSite, JWT PKCE) e IDS/IPS (Suricata/Snort).

Reglas estrictas:
- 0% emojis.
- Sintaxis Obsidian [[Concepto_Clave]].
- Prohibición explícita de Wikipedia (referencias a RFCs de IETF, IEEE 802, NIST SP 800, MITRE).
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset", "specialized_datasets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_PROMPT = (
    "Eres SENTINEL, el sistema operativo cognitivo y tutor pedagógico del Laboratorio STEM.\n"
    "Misión: Formar a estudiantes en Inteligencia Artificial, Impresión 3D (Klipper), IoT/ESP32, Robótica, Programación, Redes, Ciberseguridad y Linux.\n"
    "Reglas estrictas:\n"
    "1. Responde en español con máximo rigor científico, pedagógico y código de producción directo.\n"
    "2. Prohibido emojis al 100%.\n"
    "3. Usa [[Concepto]] para todos los conceptos técnicos clave (sintaxis Obsidian).\n"
    "4. Prohibido citar, consultar o recomendar Wikipedia o fuentes terciarias; utiliza exclusivamente estándares primarios (RFCs de IETF, IEEE, ISO/IEC, NIST, MITRE), documentación técnica oficial y código fuente verificable.\n"
    "5. Descarta tajantemente cualquier consulta ajena a STEM, reorientando al usuario hacia el método científico y el laboratorio."
)

DATASETS = {}

# ==============================================================================
# 08. REDES DE COMPUTADORAS, BITS, PROTOCOLOS Y CAPAS OSI/TCP
# ==============================================================================
DATASETS["08_networking_bits_and_protocols"] = [
    {
        "instruction": "Detalla la anatomía a nivel de bits de una trama Ethernet II (IEEE 802.3), explicando el preámbulo, direcciones MAC, MTU y el cálculo del CRC-32.",
        "response": (
            "En la capa de enlace de datos del modelo [[TCP/IP]], la unidad fundamental de transferencia es la [[Trama_Ethernet_II]]. "
            "Cada paquete IP se encapsula en esta estructura con alineación estricta de bytes:\n\n"
            "### Estructura de Campos de la Trama Ethernet II:\n"
            "1. **Preámbulo (7 bytes / 56 bits)**: Secuencia de sincronización de reloj alternante `10101010` repeated 7 veces.\n"
            "2. **Delimitador de Inicio de Trama (SFD - 1 byte / 8 bits)**: Patrón `10101011`. El par de bits finales `11` señaliza al hardware de la interfaz (PHY) que el siguiente bit corresponde a la dirección de destino.\n"
            "3. **Dirección MAC de Destino (6 bytes / 48 bits)**: Dirección física del receptor o broadcast (`FF:FF:FF:FF:FF:FF`). El bit menos significativo del primer octeto define si el tráfico es Unicast (`0`) o Multicast (`1`).\n"
            "4. **Dirección MAC de Origen (6 bytes / 48 bits)**: Identificador físico único de la tarjeta de red (NIC) emisora (primeros 24 bits: OUI del fabricante; últimos 24 bits: serial asignado).\n"
            "5. **EtherType (2 bytes / 16 bits)**: Indica el protocolo de capa de red contenido en la carga útil (`0x0800` para [[IPv4]], `0x86DD` para [[IPv6]], `0x0806` para [[ARP]]).\n"
            "6. **Carga Útil (Payload / 46 a 1500 bytes)**: Contiene el paquete IP. La [[MTU]] (*Maximum Transmission Unit*) por defecto es de 1500 bytes. Si el paquete es menor a 46 bytes, se inserta relleno (*padding*) para cumplir la longitud mínima de ranura de colisión (64 bytes totales en CSMA/CD).\n"
            "7. **Secuencia de Verificación de Trama (FCS / 4 bytes / 32 bits)**: Suma de verificación mediante código de redundancia cíclica [[CRC-32]].\n\n"
            "### Cálculo Matemático del CRC-32 (IEEE 802.3):\n"
            "El emisor trata los bits del mensaje como coeficientes de un polinomio en el campo de Galois $\\mathbb{GF}(2)$ y realiza una división módulo 2 por el polinomio generador irreducible:\n"
            "$$G(x) = x^{32} + x^{26} + x^{23} + x^{22} + x^{16} + x^{12} + x^{11} + x^{10} + x^8 + x^7 + x^5 + x^4 + x^2 + x + 1$$\n"
            "Representación hexadecimal: `0x04C11DB7`. El resto de 32 bits resultante se invierte a nivel de bits y se adosa como FCS. Si la tarjeta receptora recalcula el CRC y detecta un resto distinto de cero, descarta la trama silenciosamente a nivel de silicio antes de interrumpir a la CPU del sistema operativo."
        )
    },
    {
        "instruction": "Explica y desarrolla paso a paso el cálculo de subnetting VLSM en IPv4 para dividir una red /24 en subredes eficientes para servidores y enlaces punto a punto.",
        "response": (
            "El esquema [[VLSM]] (*Variable Length Subnet Masking*, estandarizado en [[RFC_1878]]) permite asignar máscaras de longitud variable a diferentes subredes derivadas de un mismo bloque, eliminando el desperdicio masivo del direccionamiento con clases (*classful*).\n\n"
            "### Planteamiento del Problema en el Laboratorio:\n"
            "Partimos del prefijo base `192.168.10.0/24` (256 direcciones totales). Se requiere diseñar:\n"
            "- **Subred A (Laboratorio de IA)**: Mínimo 50 hosts útiles.\n"
            "- **Subred B (Sensores IoT ESP32)**: Mínimo 25 hosts útiles.\n"
            "- **Subred C (Enlace troncal de routers WAN)**: Exactamente 2 hosts útiles.\n\n"
            "### Regla Fundamental de Asignación:\n"
            "Se ordenan las necesidades de mayor a menor tamaño para evitar superposición de bloques.\n\n"
            "#### 1. Subred A (50 hosts útiles):\n"
            "- Fórmula: $2^h - 2 \\ge 50$. Con $h = 6$ bits de host: $2^6 - 2 = 64 - 2 = 62$ hosts útiles.\n"
            "- Bits de red: $32 - 6 = 26$ bits (Máscara `/26` o `255.255.255.192`).\n"
            "- **Dirección de Red**: `192.168.10.0/26`\n"
            "- **Rango de Hosts Útiles**: `192.168.10.1` a `192.168.10.62`\n"
            "- **Dirección de Broadcast**: `192.168.10.63`\n\n"
            "#### 2. Subred B (25 hosts útiles):\n"
            "- Siguiente dirección libre disponible: `192.168.10.64`.\n"
            "- Fórmula: $2^h - 2 \\ge 25$. Con $h = 5$ bits de host: $2^5 - 2 = 32 - 2 = 30$ hosts útiles.\n"
            "- Bits de red: $32 - 5 = 27$ bits (Máscara `/27` o `255.255.255.224`).\n"
            "- **Dirección de Red**: `192.168.10.64/27`\n"
            "- **Rango de Hosts Útiles**: `192.168.10.65` a `192.168.10.94`\n"
            "- **Dirección de Broadcast**: `192.168.10.95`\n\n"
            "#### 3. Subred C (Enlace punto a punto - 2 hosts):\n"
            "- Siguiente dirección libre: `192.168.10.96`.\n"
            "- Fórmula: $2^h - 2 \\ge 2$. Con $h = 2$ bits de host: $2^2 - 2 = 2$ hosts exactos.\n"
            "- Bits de red: $32 - 2 = 30$ bits (Máscara `/30` o `255.255.255.252`).\n"
            "- **Dirección de Red**: `192.168.10.96/30`\n"
            "- **Rango de Hosts Útiles**: `192.168.10.97` a `192.168.10.98`\n"
            "- **Dirección de Broadcast**: `192.168.10.99`\n\n"
            "Este cálculo reserva el bloque continuo desde `192.168.10.100` hasta `192.168.10.255` para futuras expansiones sin fragmentación."
        )
    },
    {
        "instruction": "Explica la máquina de estados de TCP, el Three-Way Handshake, el estado TIME_WAIT y la diferencia entre los algoritmos de congestión CUBIC y BBR.",
        "response": (
            "El protocolo [[TCP]] ([[RFC_9293]]) es un protocolo de capa de transporte orientado a conexión con entrega confiable, control de flujo por ventana deslizante y control de saturación de red.\n\n"
            "### 1. Three-Way Handshake (Establecimiento de Conexión):\n"
            "```text\n"
            "Cliente                                                 Servidor\n"
            "   |  --- [SYN] Seq = X, MSS = 1460, WScale = 7 -------->  |  (Servidor en LISTEN)\n"
            "   |                                                       |  (Pasa a SYN_RECEIVED)\n"
            "   |  <-- [SYN+ACK] Seq = Y, Ack = X + 1, MSS = 1460 ----  |  \n"
            "   |  (Pasa a ESTABLISHED)                                 |  \n"
            "   |  --- [ACK] Seq = X + 1, Ack = Y + 1 --------------->  |  (Pasa a ESTABLISHED)\n"
            "```\n"
            "El intercambio acuerda los números de secuencia iniciales aleatorios ([[ISN]]), el tamaño máximo de segmento ([[MSS]]) y el factor de escala de ventana para enlaces de alto producto ancho de banda-retardo (*BDP*).\n\n"
            "### 2. Cierre de Conexión y Estado TIME_WAIT:\n"
            "El cierre estándar requiere 4 paquetes (`FIN -> ACK`, `FIN -> ACK`). El extremo que inicia el cierre activo entra obligatoriamente en el estado **TIME_WAIT** durante un período de **2MSL** (Maximum Segment Lifetime, típicamente 60 a 120 segundos en kernels de Linux).\n"
            "- **Objetivo 1**: Asegurar que el último `ACK` alcance al par. Si ese paquete se pierde en la red, el par retransmite el `FIN`; si el socket estuviera destruido, respondería con `RST` espurio.\n"
            "- **Objetivo 2**: Permitir que cualquier segmento duplicado o retrasado en los routers de tránsito expire antes de que una nueva conexión reutilice la misma tupla de 4 elementos (IP origen, puerto origen, IP destino, puerto destino).\n\n"
            "### 3. Control de Congestión: CUBIC vs BBR:\n"
            "- **CUBIC ([[RFC_8312]])**: Algoritmo tradicional basado en pérdidas de paquetes (*loss-based*). Incrementa la ventana de congestión (`cwnd`) siguiendo una función cúbica del tiempo transcurrido desde la última caída. Asume que la pérdida de paquetes es sinónimo de congestión física, lo que provoca subutilización severa en enlaces Wi-Fi con ruido o bufferbloat en routers de borde.\n"
            "- **BBR (Bottleneck Bandwidth and RTT)**: Diseñado por Google. Modela la red como un conducto físico midiendo de forma periódica e independiente dos variables: el ancho de banda máximo del cuello de botella ($BtlBw$) y el retardo mínimo de propagación de ida y vuelta ($RTprop$). "
            "BBR modula la tasa de inyección de paquetes para operar exactamente en el punto óptimo de Kleinrock (máximo rendimiento sin acumular colas en los buffers intermedios), reduciendo la latencia de transmisión a la mitad frente a CUBIC."
        )
    },
    {
        "instruction": "¿Cómo implementar un servidor TCP concurrente de alto rendimiento en C mediante la API de epoll en Linux para manejar miles de conexiones?",
        "response": (
            "En sistemas operativos Linux, el uso de hilos individuales por socket (`pthread_create`) o llamadas tradicionales `select()` colapsa al escalar a más de 1024 conexiones concurrentes (el problema C10K). "
            "La solución industrial es la llamada al sistema [[epoll]] en modo no bloqueante (*Non-blocking I/O*):\n\n"
            "```c\n"
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n"
            "#include <string.h>\n"
            "#include <unistd.h>\n"
            "#include <fcntl.h>\n"
            "#include <sys/socket.h>\n"
            "#include <netinet/in.h>\n"
            "#include <sys/epoll.h>\n"
            "#include <errno.h>\n\n"
            "#define MAX_EVENTS 64\n"
            "#define PORT 8080\n\n"
            "static int set_nonblocking(int fd) {\n"
            "    int flags = fcntl(fd, F_GETFL, 0);\n"
            "    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);\n"
            "}\n\n"
            "int main() {\n"
            "    int server_fd = socket(AF_INET, SOCK_STREAM, 0);\n"
            "    int opt = 1;\n"
            "    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));\n\n"
            "    struct sockaddr_in addr = {\n"
            "        .sin_family = AF_INET,\n"
            "        .sin_port = htons(PORT),\n"
            "        .sin_addr.s_addr = INADDR_ANY\n"
            "    };\n"
            "    bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));\n"
            "    set_nonblocking(server_fd);\n"
            "    listen(server_fd, SOMAXCONN);\n\n"
            "    int epoll_fd = epoll_create1(0);\n"
            "    struct epoll_event ev, events[MAX_EVENTS];\n"
            "    ev.events = EPOLLIN | EPOLLET; // Edge-Triggered mode\n"
            "    ev.data.fd = server_fd;\n"
            "    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, server_fd, &ev);\n\n"
            "    printf(\"[INFO] Servidor epoll escuchando en puerto %d\\n\", PORT);\n\n"
            "    while (1) {\n"
            "        int nfds = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);\n"
            "        for (int i = 0; i < nfds; i++) {\n"
            "            if (events[i].data.fd == server_fd) {\n"
            "                // Aceptar todas las conexiones entrantes en cola (modo Edge-Triggered)\n"
            "                while (1) {\n"
            "                    struct sockaddr_in client_addr;\n"
            "                    socklen_t client_len = sizeof(client_addr);\n"
            "                    int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);\n"
            "                    if (client_fd < 0) {\n"
            "                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;\n"
            "                        break;\n"
            "                    }\n"
            "                    set_nonblocking(client_fd);\n"
            "                    ev.events = EPOLLIN | EPOLLET | EPOLLRDHUP;\n"
            "                    ev.data.fd = client_fd;\n"
            "                    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, client_fd, &ev);\n"
            "                }\n"
            "            } else if (events[i].events & EPOLLIN) {\n"
            "                char buffer[1024];\n"
            "                ssize_t bytes_read = read(events[i].data.fd, buffer, sizeof(buffer) - 1);\n"
            "                if (bytes_read > 0) {\n"
            "                    buffer[bytes_read] = '\\0';\n"
            "                    write(events[i].data.fd, \"ACK\\n\", 4);\n"
            "                } else if (bytes_read == 0 || (bytes_read < 0 && errno != EAGAIN)) {\n"
            "                    close(events[i].data.fd);\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "    close(server_fd);\n"
            "    return 0;\n"
            "}\n"
            "```\n\n"
            "El modo `EPOLLET` (Edge-Triggered) notifica únicamente cuando cambia el estado del descriptor, reduciendo a cero el número de llamadas redundantes del kernel y alcanzando decenas de miles de conexiones concurrentes con consumo mínimo de CPU."
        )
    }
]

# ==============================================================================
# 09. CIBERSEGURIDAD, CRIPTOGRAFÍA APLICADA Y DEFENSA DE SISTEMAS
# ==============================================================================
DATASETS["09_cybersecurity_and_defense"] = [
    {
        "instruction": "Explica la arquitectura y el apretón de manos (handshake) de TLS 1.3 a nivel de paquetes, comparándolo con TLS 1.2.",
        "response": (
            "El protocolo [[TLS_1.3]] ([[RFC_8446]]) rediseñó de forma integral la capa criptográfica de Internet para maximizar la velocidad y erradicar fallos estructurales de versiones anteriores.\n\n"
            "### Comparativa Arquitectónica contra TLS 1.2:\n"
            "1. **Depuración de Criptografía Insegura**: TLS 1.3 eliminó completamente el intercambio de claves RSA estático (que impedía el Secreto Perfecto hacia Adelante o *PFS*), el modo de cifrado CBC (vulnerable a ataques padding oracle tipo POODLE/Lucky13), algoritmos obsoletos como RC4, 3DES, MD5 y SHA-1.\n"
            "2. **Cifrado Obligatorio AEAD**: Exclusivamente admite suites [[AEAD]] (*Authenticated Encryption with Associated Data*): `AES-128-GCM`, `AES-256-GCM` y `CHACHA20-POLY1305`.\n"
            "3. **Reducción de Latencia a 1-RTT**: En TLS 1.2 se requerían 2 viajes de ida y vuelta (2-RTT) para negociar parámetros antes de transmitir datos de aplicación. TLS 1.3 resuelve el intercambio en **1 solo RTT** combinando el intercambio de claves [[ECDHE]] en el primer paquete `ClientHello`.\n\n"
            "### Flujo de Paquetes en el Handshake 1-RTT de TLS 1.3:\n"
            "```text\n"
            "Cliente                                                 Servidor\n"
            "   |  --- ClientHello --------------------------------->   |  (Envía supported_versions, cipher_suites\n"
            "   |      + KeyShare (Clave pública efímera X25519)        |   y KeyShare con su mitad ECDHE)\n"
            "   |                                                       |  (Calcula secreto compartido premaster)\n"
            "   |  <-- ServerHello ----------------------------------   |  (Selecciona suite y envía su KeyShare)\n"
            "   |      + KeyShare (Clave efímera del servidor)          |  [A partir de aquí, todo el tráfico va cifrado]\n"
            "   |      {EncryptedExtensions}                            |  \n"
            "   |      {Certificate}                                    |  (Certificado X.509 del servidor)\n"
            "   |      {CertificateVerify}                              |  (Firma digital sobre todo el handshake)\n"
            "   |      {Finished}                                       |  (HMAC sobre la transcripción del handshake)\n"
            "   |  (Cliente verifica certificado y firma)               |  \n"
            "   |  --- {Finished} ---------------------------------->   |  \n"
            "   |  --- [Datos de Aplicación Cifrados (HTTP/2-3)] --->   |  \n"
            "```\n\n"
            "Adicionalmente, TLS 1.3 provee el modo **0-RTT** (*Early Data*) que permite al cliente enviar datos de aplicación en el primer paquete en conexiones reanudadas, utilizando la clave previamente derivada de la sesión previa."
        )
    },
    {
        "instruction": "¿Cómo configurar un firewall robusto en Linux mediante nftables para bloquear escaneos de puertos, mitigar ataques SYN flood y filtrar paquetes?",
        "response": (
            "En el kernel de Linux, el subsistema [[nftables]] reemplazó por completo a `iptables`, unificando IPv4, IPv6, ARP y bridging en un solo motor de máquina virtual basado en bytecode de alto rendimiento.\n\n"
            "### Configuración de Producción (`/etc/nftables.conf`):\n"
            "```nft\n"
            "#!/usr/sbin/nft -f\n\n"
            "flush ruleset\n\n"
            "table inet filter {\n"
            "    # Conjunto para mitigar fuerza bruta bloqueando IPs temporalmente\n"
            "    set denylist {\n"
            "        type ipv4_addr\n"
            "        flags timeout\n"
            "    }\n\n"
            "    chain input {\n"
            "        type filter hook input priority 0; policy drop;\n\n"
            "        # 1. Permitir tráfico de loopback local obligatorio\n"
            "        iif \"lo\" accept\n\n"
            "        # 2. Descartar paquetes de IPs en la lista negra temporal\n"
            "        ip saddr @denylist drop\n\n"
            "        # 3. Filtrado por seguimiento de estado (Connection Tracking)\n"
            "        # Permite tráfico de conexiones ya establecidas o relacionadas legítimas\n"
            "        ct state established,related accept\n"
            "        ct state invalid drop\n\n"
            "        # 4. Mitigación de escaneos TCP anómalos (XMAS, NULL, SYN-FIN)\n"
            "        tcp flags & (fin|syn|rst|psh|ack|urg) == 0 drop\n"
            "        tcp flags & (fin|syn) == fin|syn drop\n"
            "        tcp flags & (syn|rst) == syn|rst drop\n\n"
            "        # 5. Mitigación de SYN Flood: Límite de tasa para nuevas conexiones TCP\n"
            "        tcp flags syn tcp dport { 22, 80, 443 } limit rate over 25/second burst 50 packets drop\n\n"
            "        # 6. Permitir servicios autorizados del laboratorio\n"
            "        tcp dport 22 accept   # SSH\n"
            "        tcp dport 8080 accept # Panel SENTINEL\n"
            "        tcp dport 1883 accept # Broker MQTT de sensores\n\n"
            "        # 7. Permitir ICMP (Ping) controlado para diagnóstico de red\n"
            "        icmp type echo-request limit rate 5/second accept\n"
            "    }\n\n"
            "    chain forward {\n"
            "        type filter hook forward priority 0; policy drop;\n"
            "    }\n\n"
            "    chain output {\n"
            "        type filter hook output priority 0; policy accept;\n"
            "    }\n"
            "}\n"
            "```\n\n"
            "### Fortalecimiento adicional en el Kernel de Linux (`/etc/sysctl.d/99-network-security.conf`):\n"
            "```ini\n"
            "# Habilita SYN cookies para resistir ataques de denegación de servicio sin agotar memoria\n"
            "net.ipv4.tcp_syncookies = 1\n"
            "# Desactiva aceptación de paquetes ICMP redirect para prevenir envenenamiento de rutas\n"
            "net.ipv4.conf.all.accept_redirects = 0\n"
            "# Habilita filtrado de ruta inversa para mitigar falsificación de IP (IP Spoofing)\n"
            "net.ipv4.conf.all.rp_filter = 1\n"
            "```\n\n"
            "Se aplican de inmediato con: `sudo sysctl -p /etc/sysctl.d/99-network-security.conf` y `sudo nft -f /etc/nftables.conf`."
        )
    },
    {
        "instruction": "Explica los mecanismos de mitigación a nivel de binario contra desbordamientos de búfer (Buffer Overflow): Stack Canaries, ASLR, DEP/NX y PIE.",
        "response": (
            "En la ejecución de binarios compilados en C/C++, la manipulación insegura de memoria en la pila (*stack*) puede permitir a un atacante sobrescribir la dirección de retorno (`$rip` / `$eip`) para desviar el flujo de control hacia código malicioso o una cadena ROP (*Return-Oriented Programming*). "
            "Los sistemas operativos y compiladores modernos implementan cuatro barreras defensivas de hardware y software:\n\n"
            "### 1. Canarios de Pila (Stack Canaries / `-fstack-protector-strong`):\n"
            "- El compilador inserta un valor pseudoaleatorio secreto (obtenido del registro de segmento `%fs:0x28` en x86_64) en el marco de pila inmediatamente antes de la dirección de retorno guardada.\n"
            "- Antes de que la función ejecute la instrucción de retorno `ret`, compara el valor del canario con el valor de referencia.\n"
            "- Si hubo un desbordamiento de búfer, el canario queda corrompido, disparando de forma instantánea la rutina `__stack_chk_fail()` que aborta el proceso con un `SIGABRT`, impidiendo la ejecución de código secuestrado.\n\n"
            "### 2. DEP / NX (Data Execution Prevention / No-Execute Bit):\n"
            "- Mecanismo asistido por la CPU (bit NX en tablas de páginas x86_64).\n"
            "- Implementa el principio estricto **$W \\oplus X$ (Write XOR Execute)**: las regiones de memoria que son escribibles (como el Stack y el Heap) no tienen permisos de ejecución. Si el contador de programa salta a una dirección en la pila para ejecutar un shellcode, la CPU genera una excepción de falla de página (*Segmentation Fault*).\n\n"
            "### 3. ASLR (Address Space Layout Randomization):\n"
            "- El kernel aleatoriza las direcciones base en memoria virtual cada vez que el binario se ejecuta:\n"
            "  - Base de la pila (Stack).\n  - Base de la memoria dinámica (Heap).\n  - Base de las bibliotecas compartidas (`libc.so`).\n"
            "- Impide que un atacante utilice direcciones de memoria fijas codificadas en duro para saltar a funciones de la biblioteca estándar (ej. `system()`).\n\n"
            "### 4. PIE (Position Independent Executable / `-fPIE -pie`):\n"
            "- Extiende la aleatorización de ASLR a la sección de código principal (`.text`) y datos del propio ejecutable.\n"
            "- Al compilar con `-fPIE`, todas las referencias a funciones e instrucciones se resuelven mediante direccionamiento relativo al puntero de instrucción (`[rip + offset]`), garantizando que ninguna parte del binario resida en una dirección estática predecible."
        )
    },
    {
        "instruction": "¿Cómo estructurar una regla de detección para Suricata o Snort para alertar sobre inyecciones SQL ciegas basadas en tiempo (Blind SQLi)?",
        "response": (
            "Los sistemas de detección y prevención de intrusiones ([[IDS]] / [[IPS]]) como [[Suricata]] y [[Snort]] analizan el tráfico de red mediante inspección profunda de paquetes ([[DPI]]) aplicando autómatas de correspondencia de patrones sobre encabezados y cargas útiles.\n\n"
            "### Estructura Canónica de una Regla Suricata:\n"
            "```text\n"
            "alert http any any -> $HOME_NET any (\n"
            "    msg:\"SENTINEL-IDS: Intento de Inyeccion SQL Ciega por Retardo Temporal (pg_sleep / WAITFOR DELAY)\";\n"
            "    flow:established,to_server;\n"
            "    http.uri;\n"
            "    content:\"sleep\"; nocase;\n"
            "    pcre:\"/(pg_sleep\\s*\\(|waitfor\\s+delay|sleep\\s*\\(\\s*\\d+)/i\";\n"
            "    classtype:web-application-attack;\n"
            "    sid:2026001;\n"
            "    rev:1;\n"
            ")\n"
            "```\n\n"
            "### Desglose de Parámetros de Inspección:\n"
            "1. **`alert http any any -> $HOME_NET any`**: Acción a tomar (`alert`), protocolo decodificado (`http`), origen (cualquier IP y puerto) y destino (servidores locales protegidos en la variable `$HOME_NET`).\n"
            "2. **`flow:established,to_server`**: Filtra mediante seguimiento de flujo TCP, evaluando exclusivamente peticiones de clientes hacia el servidor tras el Three-Way Handshake.\n"
            "3. **`http.uri`**: Modificador de búfer normalizado. Descomprime y normaliza la URL decodificando caracteres en codificación percent-encoding (ej. `%20` a espacio, `%27` a comilla) antes de evaluar los patrones.\n"
            "4. **`content:\"sleep\"; nocase;`**: Búsqueda rápida por algoritmo de Boyer-Moore/Aho-Corasick. Si esta palabra no está presente, el motor descarta el paquete sin evaluar la expresión regular costosa.\n"
            "5. **`pcre:\"/.../i\"`**: Expresión regular compatible con Perl que valida firmas de funciones de retardo temporal comunes en PostgreSQL (`pg_sleep`), Microsoft SQL Server (`WAITFOR DELAY`) y MySQL (`sleep(N)`).\n"
            "6. **`sid:2026001`**: Identificador único de regla (*Signature ID*), obligatorio para auditoría y correlación en plataformas [[SIEM]]."
        )
    }
]

def generate_networking_files():
    print("=== GENERANDO DATASETS DE REDES Y CIBERSEGURIDAD PARA SENTINEL ===")
    
    total_samples = 0
    for key, pairs in DATASETS.items():
        jsonl_filename = os.path.join(OUTPUT_DIR, f"{key}.jsonl")
        txt_filename = os.path.join(OUTPUT_DIR, f"{key}.txt")

        # 1. Escritura en JSONL
        with open(jsonl_filename, "w", encoding="utf-8") as f_jsonl:
            for item in pairs:
                entry = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": item["instruction"]},
                        {"role": "assistant", "content": item["response"]}
                    ]
                }
                f_jsonl.write(json.dumps(entry, ensure_ascii=False) + "\n")
                total_samples += 1

        # 2. Escritura en TXT
        with open(txt_filename, "w", encoding="utf-8") as f_txt:
            f_txt.write(f"# DATASET ESPECIALIZADO: {key.upper()}\n")
            f_txt.write("=" * 80 + "\n")
            f_txt.write("REGLA ESTRICTA DE INVESTIGACIÓN: PROHIBIDO EL USO DE WIKIPEDIA.\n")
            f_txt.write("REFERENCIAS OBLIGATORIAS: ESTÁNDARES PRIMARIOS (RFCs, IEEE 802, NIST, MITRE).\n")
            f_txt.write("=" * 80 + "\n\n")
            for idx, item in enumerate(pairs, 1):
                f_txt.write(f"## MÓDULO {idx}: {item['instruction']}\n\n")
                f_txt.write(f"{item['response']}\n\n")
                f_txt.write("-" * 80 + "\n\n")

        size_jsonl = os.path.getsize(jsonl_filename)
        size_txt = os.path.getsize(txt_filename)
        print(f"[OK] {key} -> {len(pairs)} pares generados | JSONL: {size_jsonl} bytes | TXT: {size_txt} bytes")

    print(f"\n[ÉXITO] Total de nuevos pares de Redes y Ciberseguridad: {total_samples}")

if __name__ == "__main__":
    generate_networking_files()
