#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador Exhaustivo de Dataset de Control Total de Terminal Multiplataforma para SENTINEL.
Cubre 9 pilares con rigor de ingeniería de sistemas y formato ReAct puro:
1. Linux Ubuntu / Debian (APT, Systemd, Netplan, UFW, Cron, Permisos, Logs, Sysctl, Cgroups)
2. Linux Arch (Pacman, Makepkg, AUR, Reflector, Mkinitcpio, Systemd-boot)
3. Linux Kali (Auditoría de Red, Wireless, Nmap, Tcpdump, Tshark, Forense dd)
4. Manipulación Atómica de Ficheros POSIX (cat heredoc, sed in-place, awk, find, rsync, tar/zstd)
5. Windows PowerShell (Cmdlets de Procesos, Servicios, Red, Ficheros, WMI/CIM, EventLog)
6. Windows CMD (Tasklist, Taskkill, Robocopy, SC, Netstat, Registros Reg, Icacls)
7. macOS Darwin / Zsh (Homebrew, Launchctl, Defaults, Diskutil APFS, Networksetup)
8. Auto-instalación y Despliegue Autónomo (Bootstrap de agente, venv, persistencia de demonios)
9. ReAct Resiliente con Recuperación de Errores (Conflictos de puerto, bloqueos dpkg, disco lleno)

Formato:
[THOUGHT] ... [/THOUGHT]
[EXECUTE] ... [/EXECUTE]
[OUTPUT] ... [/OUTPUT]
0% Emojis. [[Concepto]] en Obsidian.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "dataset", "cross_platform_terminal_dataset.jsonl")

SYSTEM_PROMPT = (
    "Eres SENTINEL, operador autónomo de sistemas y terminal. "
    "Para interactuar con el sistema operativo debes razonar dentro de [THOUGHT]...[/THOUGHT], "
    "emitir el comando exacto encerrado estrictamente en [EXECUTE]...[/EXECUTE] "
    "y analizar la respuesta que recibas en [OUTPUT]...[/OUTPUT]. "
    "Responde siempre con rigor técnico y enlaces de Obsidian [[Concepto]]. Prohibido el uso de emojis."
)

SAMPLES = []

def add(platform, instruction, thought, command, output, final_answer):
    SAMPLES.append({
        "platform": platform,
        "instruction": instruction,
        "thought": thought,
        "command": command,
        "output": output,
        "final_answer": final_answer
    })

# =============================================================================
# 1. LINUX UBUNTU / DEBIAN
# =============================================================================
add("linux_ubuntu_debian",
    "En un servidor Ubuntu 24.04 el servicio nginx falló al reiniciar. Necesito ver las últimas 30 líneas del log de systemd para ese servicio y verificar la sintaxis de configuración.",
    "Debo consultar los logs específicos de la unidad nginx mediante journalctl con la bandera no-pager y limitar las líneas, y luego ejecutar la comprobación de sintaxis de nginx con la bandera -t.",
    "journalctl -u nginx -n 30 --no-pager && nginx -t",
    "Sep 26 12:04:11 srv-hp nginx[21034]: nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)\nnginx: the configuration file /etc/nginx/nginx.conf syntax is ok\nnginx: configuration file /etc/nginx/nginx.conf test is successful",
    "El análisis de [[journalctl]] revela que la configuración sintáctica es correcta (`nginx -t` exitoso), pero existe un conflicto de enlace en el puerto 80 (`Address already in use`). Otro proceso ya está ocupando dicho puerto TCP.")

add("linux_ubuntu_debian",
    "Actualiza la lista de repositorios APT, muestra cuántos paquetes están pendientes y actualiza exclusivamente los paquetes relacionados con docker y containerd sin intervención humana.",
    "Debo ejecutar apt update de forma no interactiva, verificar los paquetes disponibles mediante apt list --upgradable y aplicar apt-get install --only-upgrade con las banderas -y para docker-ce y containerd.io.",
    "sudo apt update && apt list --upgradable 2>/dev/null | grep -E 'docker|containerd' && sudo apt-get --only-upgrade install -y containerd.io docker-ce docker-ce-cli",
    "Hit:1 http://archive.ubuntu.com/ubuntu noble InRelease\ncontainerd.io/noble 2.3.5-1 amd64 [upgradable from: 2.3.3-1]\ndocker-ce/noble 28.0.1-1 amd64 [upgradable from: 27.5.1-1]\nSetting up containerd.io (2.3.5-1) ...\nSetting up docker-ce (28.0.1-1) ...\nProcessing triggers for systemd (255.4) ...",
    "Se sincronizaron los repositorios y se aplicó la actualización focalizada de [[containerd.io]] y [[docker-ce]] mediante [[apt]] sin alterar el resto de paquetes del sistema operativo.")

add("linux_ubuntu_debian",
    "Configura una dirección IP estática en Ubuntu Server mediante Netplan en la interfaz eth0 con IP 192.168.1.150/24, gateway 192.168.1.1 y DNS 1.1.1.1, aplicando los cambios de forma segura.",
    "Netplan utiliza archivos YAML en /etc/netplan. Debo crear un archivo de configuración atómico con permisos 600, verificar con netplan generate y aplicar con netplan apply.",
    "cat << 'EOF' | sudo tee /etc/netplan/01-static-eth0.yaml > /dev/null\nnetwork:\n  version: 2\n  renderer: networkd\n  ethernets:\n    eth0:\n      dhcp4: no\n      addresses:\n        - 192.168.1.150/24\n      routes:\n        - to: default\n          via: 192.168.1.1\n      nameservers:\n        addresses: [1.1.1.1, 8.8.8.8]\nEOF\nsudo chmod 600 /etc/netplan/01-static-eth0.yaml && sudo netplan apply",
    "[OK] Netplan configuration rendered and applied successfully.",
    "Se configuró la interfaz estática en [[Netplan]] bajo el renderizador `networkd` y se aplicaron las tablas de enrutamiento y servidores DNS con permisos restringidos.")

add("linux_ubuntu_debian",
    "Crea una unidad de servicio systemd para un worker Python en /etc/systemd/system/sentinel-worker.service que arranque tras la red, use usuario mauro, reinicie ante fallos tras 5 segundos y habilítala.",
    "Debo escribir la definición de servicio con las secciones [Unit], [Service] y [Install] atómicamente, recargar el demonio con systemctl daemon-reload y habilitar el servicio con --now.",
    "cat << 'EOF' | sudo tee /etc/systemd/system/sentinel-worker.service > /dev/null\n[Unit]\nDescription=SENTINEL Background Worker\nAfter=network.target\n\n[Service]\nType=simple\nUser=mauro\nWorkingDirectory=/opt/sentinel\nExecStart=/opt/sentinel/.venv/bin/python worker.py\nRestart=on-failure\nRestartSec=5s\nStandardOutput=journal\nStandardError=journal\n\n[Install]\nWantedBy=multi-user.target\nEOF\nsudo systemctl daemon-reload && sudo systemctl enable --now sentinel-worker.service && sudo systemctl is-active sentinel-worker.service",
    "Created symlink /etc/systemd/system/multi-user.target.wants/sentinel-worker.service -> /etc/systemd/system/sentinel-worker.service.\nactive",
    "La unidad [[systemd]] fue aprovisionada en `/etc/systemd/system/`, registrada mediante `daemon-reload` e inicializada en estado `active` con política de reconexión automática.")

add("linux_ubuntu_debian",
    "Configura el cortafuegos UFW para bloquear todo tráfico entrante por defecto, permitir tráfico saliente, autorizar SSH con limitación de tasa contra ataques de fuerza bruta y permitir el puerto 8001.",
    "Debo aplicar ufw default deny incoming, ufw default allow outgoing, ufw limit ssh y ufw allow 8001/tcp, habilitando luego el cortafuegos con --force.",
    "sudo ufw default deny incoming && sudo ufw default allow outgoing && sudo ufw limit 22/tcp && sudo ufw allow 8001/tcp && sudo ufw --force enable && sudo ufw status verbose",
    "Default: deny (incoming), allow (outgoing), disabled (routed)\nTo                         Action      From\n--                         ------      ----\n22/tcp                     LIMIT IN    Anywhere\n8001/tcp                   ALLOW IN    Anywhere",
    "El firewall [[ufw]] quedó asegurado bajo el principio de menor privilegio con mitigación activa de ataques de fuerza bruta en el puerto SSH y exposición del puerto 8001.")

add("linux_ubuntu_debian",
    "Ajusta en caliente y de manera permanente el parámetro de kernel vm.swappiness a 10 y fs.file-max a 2097152 para optimizar la latencia del servidor.",
    "Para ajuste permanente en Linux, debo registrar las directivas en /etc/sysctl.d/99-performance.conf y luego cargar los parámetros inmediatamente con sysctl --system.",
    "cat << 'EOF' | sudo tee /etc/sysctl.d/99-performance.conf > /dev/null\nvm.swappiness=10\nfs.file-max=2097152\nEOF\nsudo sysctl --system | grep -E 'swappiness|file-max'",
    "* Applying /etc/sysctl.d/99-performance.conf ...\nvm.swappiness = 10\nfs.file-max = 2097152",
    "Los parámetros del subsistema de memoria virtual y descriptores de archivo del [[kernel]] fueron actualizados de forma atómica y persistente mediante [[sysctl]].")

add("linux_ubuntu_debian",
    "Analiza el tiempo de inicio de los servicios del sistema mediante systemd-analyze e identifica los 5 servicios que más retrasan el arranque.",
    "Debo invocar systemd-analyze blame y filtrar los primeros 5 resultados con head.",
    "systemd-analyze blame | head -n 5",
    "8.421s plymouth-quit-wait.service\n3.140s snapd.service\n2.810s systemd-journal-flush.service\n1.905s NetworkManager-wait-online.service\n1.120s uvicorn-sentinel.service",
    "El análisis de arranque con [[systemd-analyze]] determinó que `plymouth-quit-wait` y `snapd` concentran la mayor parte de la latencia de inicialización del sistema operativo.")

add("linux_ubuntu_debian",
    "Bloquea la actualización automática de un paquete específico como linux-image-generic para evitar que una actualización de kernel desestabilice los drivers propietarios.",
    "Debo usar apt-mark hold para congelar la versión del paquete y verificar el estado con apt-mark showhold.",
    "sudo apt-mark hold linux-image-generic && apt-mark showhold",
    "linux-image-generic set on hold.\nlinux-image-generic",
    "Se aplicó un anclaje de versión mediante [[apt-mark]] sobre el metapaquete del kernel impidiendo sobreescrituras automáticas en futuros ciclos de actualización de [[apt]].")

# =============================================================================
# 2. LINUX ARCH
# =============================================================================
add("linux_arch",
    "En Arch Linux, limpia la caché de paquetes de pacman conservando únicamente la última versión instalada y elimina todos los paquetes huérfanos del sistema.",
    "En Arch Linux, la herramienta estándar paccache de pacman-contrib permite purgar versiones viejas (-r -k1), y los paquetes huérfanos se identifican con pacman -Qdtq y se remueven con pacman -Rns.",
    "paccache -rk1 && pacman -Qdtq | sudo pacman -Rns - --noconfirm 2>/dev/null || echo 'No hay paquetes huerfanos'",
    "==> finished: 142 packages removed (disk space saved: 2.41 GiB)\nchecking dependencies...\n:: removing lib32-glibc-orphan...\n:: removing unused-lib...\n(2/2) removing [------------------------------------] 100%",
    "Se liberó espacio en disco mediante [[paccache]] manteniendo el respaldo de la versión actual y se desinstalaron las dependencias huérfanas mediante [[pacman]] de forma no interactiva.")

add("linux_arch",
    "Actualiza el sistema completo en Arch Linux ignorando paquetes corruptos de base de datos y reconstruye la imagen del kernel initramfs.",
    "Debo forzar la sincronización de bases de datos de repositorios con pacman -Syyu y luego invocar mkinitcpio con la bandera -P para regenerar todos los presets de inicio.",
    "sudo pacman -Syyu --noconfirm && sudo mkinitcpio -P",
    ":: Synchronizing package databases...\n core [######################] 100%\n extra [#####################] 100%\n:: Starting full system upgrade...\n there is nothing to do\n==> Building image from preset: /etc/mkinitcpio.d/linux.preset: 'default'\n==> Image generation successful",
    "Los repositorios de [[Arch_Linux]] fueron resincronizados y el binario initramfs fue recompilado exitosamente mediante [[mkinitcpio]].")

add("linux_arch",
    "Optimiza la lista de mirrors de Arch Linux utilizando reflector para filtrar los 10 mirrors HTTPS más rápidos y actualizados en las últimas 12 horas guardándolos en /etc/pacman.d/mirrorlist.",
    "Utilizo la utilidad oficial reflector especificando --latest 10, --protocol https, --sort rate, filtrando por edad con --age 12 y sobreescribiendo el archivo con sudo.",
    "sudo reflector --latest 10 --protocol https --sort rate --age 12 --save /etc/pacman.d/mirrorlist && head -n 8 /etc/pacman.d/mirrorlist",
    "################################################################################\n################# Arch Linux mirrorlist generated by Reflector #################\n################################################################################\nServer = https://mirror.rackspace.com/archlinux/$repo/os/$arch\nServer = https://arch.hu.fo/archlinux/$repo/os/$arch",
    "La lista de réplicas de paquetes fue jerarquizada por velocidad de descarga y frescura temporal utilizando [[reflector]] para optimizar [[pacman]].")

add("linux_arch",
    "Inspecciona el gestor de arranque systemd-boot en Arch Linux, muestra la configuración de loaders y verifica si la partición ESP está montada en /boot o /efi.",
    "Debo invocar bootctl status para auditar el estado del firmware UEFI y systemd-boot, y consultar findmnt /boot /efi para determinar el punto de montaje del ESP.",
    "bootctl status && findmnt -t vfat",
    "System:\n     Firmware: UEFI 2.70 (Lenovo)\n  Boot Loader: systemd-boot 255.4-2-arch\n       Loader: /boot/EFI/systemd/systemd-bootx64.efi\nTARGET SOURCE    FSTYPE OPTIONS\n/boot  /dev/nvme0n1p1 vfat   rw,relatime,fmask=0077,dmask=0077",
    "Se verificó la arquitectura [[UEFI]] gestionada por `systemd-boot` confirmando el montaje de la partición EFI System Partition (`vfat`) en `/boot` con máscaras de seguridad.")

add("linux_arch",
    "Clona y compila de forma segura un paquete del repositorio de usuarios de Arch (AUR) sin ejecutar makepkg como usuario root.",
    "Debo clonar el repositorio Git en un directorio de trabajo local, inspeccionar el PKGBUILD y ejecutar makepkg con las banderas -si para resolver dependencias e instalar.",
    "git clone https://aur.archlinux.org/yay-bin.git /tmp/yay-bin && cd /tmp/yay-bin && makepkg -si --noconfirm && rm -rf /tmp/yay-bin",
    "==> Making package: yay-bin 12.3.5-1 (Sun Sep 26 12:20:01 2026)\n==> Checking runtime dependencies...\n==> Installing package with pacman -U...\n[OK] yay installed successfully",
    "La compilación e instalación del binario desde [[AUR]] se ejecutó con [[makepkg]] preservando el principio de aislamiento de privilegios.")

# =============================================================================
# 3. LINUX KALI
# =============================================================================
add("linux_kali",
    "Inspecciona el estado de todas las interfaces de red, desbloquea cualquier bloqueo por software en la tarjeta inalámbrica y muestra los sockets TCP/UDP escuchando en el sistema.",
    "Para administración en entornos como Kali o Debian, debo inspeccionar interfaces con ip -br link, consultar bloqueos de radio con rfkill, desbloquear con rfkill unblock all y auditar sockets activos con ss -tulpn.",
    "ip -br link && sudo rfkill unblock all && ss -tulpn",
    "lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>\neth0             UP             52:54:00:12:34:56 <BROADCAST,MULTICAST,UP,LOWER_UP>\nwlan0            DOWN           00:c0:ca:98:76:54 <BROADCAST,MULTICAST>\nNetid  State   Recv-Q  Send-Q   Local Address:Port   Peer Address:Port  Process\ntcp    LISTEN  0       128            0.0.0.0:22          0.0.0.0:*      users:((\"sshd\",pid=842))\ntcp    LISTEN  0       511          127.0.0.1:8001        0.0.0.0:*      users:((\"uvicorn\",pid=2581))",
    "Las interfaces fueron auditadas; se liberó cualquier bloqueo de [[rfkill]] y se verificó mediante [[ss]] que únicamente el demonio SSH (puerto 22) y el backend de Sentinel (puerto 8001) mantienen sockets en escucha.")

add("linux_kali",
    "Captura en segundo plano exactamente 5 paquetes ICMP en la interfaz eth0 y guárdalos en formato pcap en /tmp/test_ping.pcap para su posterior análisis de latencia.",
    "Uso tcpdump limitando el conteo a 5 paquetes (-c 5), filtrando por protocolo icmp, especificando la interfaz eth0 (-i) y escribiendo a archivo con -w.",
    "sudo tcpdump -i eth0 -c 5 icmp -w /tmp/test_ping.pcap && ls -lh /tmp/test_ping.pcap",
    "tcpdump: listening on eth0, link-type EN10MB (Ethernet), snapshot length 262144 bytes\n5 packets captured\n5 packets received by filter\n0 packets dropped by kernel\n-rw-r--r-- 1 root root 590 Sep 26 12:15 /tmp/test_ping.pcap",
    "Se capturaron 5 datagramas ICMP mediante [[tcpdump]] almacenados en formato binario PCAP en `/tmp/test_ping.pcap` sin pérdida de paquetes en el buffer del kernel.")

add("linux_kali",
    "Ejecuta un escaneo de puertos SYN sigiloso con Nmap sobre el host 192.168.1.1 verificando únicamente los puertos de administración 22, 80, 443, 8001 y 8080 con detección de versión y sin resolución DNS reversa.",
    "Debo estructurar la orden nmap con la bandera -sS para TCP SYN stealth, -p para la lista de puertos, -sV para sondas de versiones, -n para omitir DNS y -T4 para temporizado óptimo.",
    "sudo nmap -sS -sV -n -T4 -p 22,80,443,8001,8080 192.168.1.1",
    "Starting Nmap 7.94 ( https://nmap.org )\nNmap scan report for 192.168.1.1\nHost is up (0.0012s latency).\nPORT     STATE  SERVICE VERSION\n22/tcp   open   ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.6\n80/tcp   closed http\n443/tcp  closed https\n8001/tcp open   http    uvicorn (ASGI)\n8080/tcp closed http-proxy",
    "El análisis de puertos con [[Nmap]] determinó que los servicios activos en el objetivo corresponden a [[OpenSSH]] en puerto 22 y un servidor ASGI [[uvicorn]] en puerto 8001.")

add("linux_kali",
    "Realiza una adquisición forense bit a bit del sector de arranque MBR del dispositivo /dev/sdb hacia /tmp/mbr_backup.bin con un tamaño de bloque de 512 bytes y calcula su hash SHA-256 de cadena de custodia.",
    "Uso dd especificando if=/dev/sdb, of=/tmp/mbr_backup.bin, bs=512 y count=1, seguido inmediatamente del cálculo criptográfico con sha256sum.",
    "sudo dd if=/dev/sdb of=/tmp/mbr_backup.bin bs=512 count=1 status=none && sha256sum /tmp/mbr_backup.bin",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  /tmp/mbr_backup.bin",
    "Se extrajo atómicamente el sector MBR (512 bytes) mediante [[dd]] y se generó el hash [[sha256]] garantizando la integridad forense de la imagen.")

add("linux_kali",
    "Pone la interfaz inalámbrica wlan0 en modo monitor deshabilitando procesos que puedan causar interferencias con airmon-ng check kill.",
    "Debo ejecutar sudo airmon-ng check kill para terminar network-manager y wpa_supplicant, seguido de sudo airmon-ng start wlan0.",
    "sudo airmon-ng check kill && sudo airmon-ng start wlan0 && iw dev",
    "Killing these processes:\n  PID Name\n  845 NetworkManager\n  910 wpa_supplicant\nPHY     Interface       Driver          Chipset\nphy0    wlan0mon        ath9k           Atheros AR9271",
    "La tarjeta Wi-Fi fue conmutada al modo promiscuo/monitor `wlan0mon` mediante la suite [[airmon-ng]] habiendo aislado procesos concurrentes.")

# =============================================================================
# 4. MANIPULACIÓN ATÓMICA DE FICHEROS POSIX (UNIVERSAL)
# =============================================================================
add("posix_file_ops",
    "Crea un script de monitoreo en /opt/sentinel/monitor.sh con un bloque heredoc, asigna permisos de ejecución 755 al usuario actual y configura una tarea en crontab para que se ejecute cada 5 minutos.",
    "Debo asegurar el directorio con mkdir -p, escribir el script con heredoc cat << 'EOF', aplicar chmod 755 y agregar la entrada a crontab sin duplicarla si ya existe.",
    "sudo mkdir -p /opt/sentinel && sudo tee /opt/sentinel/monitor.sh > /dev/null << 'EOF'\n#!/usr/bin/env bash\necho \"[$(date -Iseconds)] CPU Load: $(awk '{print $1}' /proc/loadavg)\" >> /var/log/sentinel_load.log\nEOF\nsudo chmod 755 /opt/sentinel/monitor.sh\n(crontab -l 2>/dev/null | grep -v 'sentinel/monitor.sh' ; echo '*/5 * * * * /opt/sentinel/monitor.sh') | crontab -",
    "[OK] Script written to /opt/sentinel/monitor.sh\n[OK] Permissions set to 755\n[OK] Crontab updated successfully",
    "El script atómico fue creado con [[Bash]] en `/opt/sentinel/` y registrado de forma idempotente en el planificador [[cron]] con cadencia quinquenal.")

add("posix_file_ops",
    "Encuentra en /var/www todos los archivos .php modificados en las últimas 24 horas y reemplaza recursivamente la cadena 'http://inseguro.local' por 'https://seguro.local' creando una copia de respaldo para cada archivo.",
    "Debo combinar find con las banderas -type f -name '*.php' -mtime -1 y ejecutar sed con la bandera -i.bak para realizar el reemplazo atómico preservando copia de respaldo.",
    "find /var/www -type f -name '*.php' -mtime -1 -exec sed -i.bak 's|http://inseguro.local|https://seguro.local|g' {} +",
    "find: executed sed replacement across 18 matched files.",
    "Se aplicó el reemplazo atómico mediante [[sed]] sobre los archivos identificados por [[find]], conservando copias `.bak` de seguridad para reversión inmediata ante contingencias.")

add("posix_file_ops",
    "Analiza el archivo /var/log/nginx/access.log, extrae las 10 direcciones IP con mayor volumen de solicitudes HTTP y el porcentaje que representan del total de accesos.",
    "Utilizo awk para extraer la primera columna ($1), ordenar con sort, contar frecuencias con uniq -c, ordenar numéricamente descendente y calcular porcentajes combinando awk y wc -l.",
    "TOTAL=$(wc -l < /var/log/nginx/access.log); awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10 | awk -v total=\"$TOTAL\" '{printf \"%-15s %8d peticiones (%5.2f%%)\\n\", $2, $1, ($1/total)*100}'",
    "192.168.1.105       4120 peticiones (42.15%)\n10.0.0.42           2150 peticiones (21.99%)\n172.16.0.8          1200 peticiones (12.28%)\n192.168.1.201        850 peticiones ( 8.70%)\n192.168.1.11         410 peticiones ( 4.20%)",
    "El perfilado de tráfico web mediante canalizaciones de [[awk]] y [[sort]] identificó que la IP `192.168.1.105` concentra más del 42% del tráfico entrante total registrado en el servidor.")

add("posix_file_ops",
    "Empaqueta y comprime el directorio /opt/sentinel/data utilizando zstandard (zstd) con nivel de compresión multihilo 6 excluyendo ficheros temporales .tmp y genera la suma de comprobación.",
    "Debo utilizar tar con la bandera -I 'zstd -6 -T0' para aprovechar todos los núcleos de CPU disponibles, especificando la exclusión de patrones con --exclude.",
    "tar --exclude='*.tmp' -I 'zstd -6 -T0' -cvf /opt/sentinel_backup.tar.zst -C /opt/sentinel data && sha256sum /opt/sentinel_backup.tar.zst",
    "data/\ndata/records.db\ndata/config.json\na8fbc0913e7123bf01...  /opt/sentinel_backup.tar.zst",
    "El respaldo fue compilado utilizando compresión moderna [[zstd]] con paralelismo de hilos de CPU y verificación criptográfica íntegra.")

add("posix_file_ops",
    "Sincroniza el directorio local /data/ hacia un servidor remoto mediante rsync preservando permisos, enlaces simbólicos, timestamps y eliminando ficheros huérfanos en destino con límite de ancho de banda a 5MB/s.",
    "Debo usar rsync con -avzP --delete --bwlimit=5000 especificando origen y destino SSH.",
    "rsync -avzP --delete --bwlimit=5000 /data/ mauro@192.168.1.50:/backup/data/",
    "sending incremental file list\ndeleting old_cache.bin\nfile1.dat\n        10.48M 100%    4.89MB/s    0:00:02\nsent 10.49M bytes  received 48 bytes  4.20M bytes/sec\ntotal size is 450.12M  speedup is 42.89",
    "La sincronización diferencial e idempotente fue completada con [[rsync]] restringiendo el consumo de enlace a 5000 KB/s y depurando ficheros obsoletos en destino.")

# =============================================================================
# 5. WINDOWS POWERSHELL
# =============================================================================
add("windows_powershell",
    "En Windows PowerShell, busca todos los procesos que consuman más de 500MB de memoria RAM privada, ordénalos de forma descendente y muestra el ID, nombre del proceso y memoria en MB.",
    "Debo usar Get-Process, filtrar con Where-Object por WorkingSet64 mayor a 500MB, ordenar con Sort-Object descendente y proyectar las propiedades con Select-Object calculando MB.",
    "Get-Process | Where-Object { $_.WorkingSet64 -gt 500MB } | Sort-Object WorkingSet64 -Descending | Select-Object Id, ProcessName, @{Name='RAM_MB';Expression={[math]::Round($_.WorkingSet64 / 1MB, 2)}} | Format-Table -AutoSize",
    "   Id ProcessName RAM_MB\n   -- ----------- ------\n14208 chrome     1254.32\n 8920 python      842.15\n 3140 code        612.80",
    "Se auditaron los procesos en memoria mediante [[PowerShell]] filtrando sobre el conjunto de trabajo privado (`WorkingSet64`) con ordenamiento jerárquico.")

add("windows_powershell",
    "Comprueba si el servicio 'Spooler' de impresión está corriendo en Windows. Si está detenido, inícialo; si está activo, reinícialo y verifica su nuevo estado.",
    "Uso Get-Service para consultar el servicio. Aplico una bifurcación condicional: si Status es Running llamo a Restart-Service, de lo contrario Start-Service, seguido de Get-Service.",
    "$svc = Get-Service -Name Spooler; if ($svc.Status -eq 'Running') { Restart-Service -Name Spooler -Force } else { Start-Service -Name Spooler }; Get-Service -Name Spooler | Select-Object Name, Status, StartType",
    "Name    Status StartType\n----    ------ ---------\nSpooler Running Automatic",
    "El servicio de cola de impresión fue gestionado mediante [[PowerShell]] comprobando su estado operacional en el subsistema de servicios de Windows (`scm`).")

add("windows_powershell",
    "Descarga de forma no interactiva un archivo binario desde una URL a C:\\Tools\\app.zip y expande su contenido en C:\\Tools\\app\\ validando si el directorio existe.",
    "Debo comprobar la ruta con Test-Path y crearla con New-Item si falta. Luego invoco Invoke-WebRequest con -UseBasicParsing para evitar dependencias de Internet Explorer, y desempaco con Expand-Archive.",
    "$dest = 'C:\\Tools'; if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force }; Invoke-WebRequest -Uri 'https://ejemplo.local/app.zip' -OutFile \"$dest\\app.zip\" -UseBasicParsing; Expand-Archive -Path \"$dest\\app.zip\" -DestinationPath \"$dest\\app\" -Force",
    "[OK] Directory C:\\Tools ready\n[OK] Downloaded 14.2 MB\n[OK] Archive expanded to C:\\Tools\\app",
    "El aprovisionamiento del paquete se completó mediante los cmdlets `Invoke-WebRequest` y `Expand-Archive` de [[PowerShell]] de forma desatendida.")

add("windows_powershell",
    "Obtén la telemetría de hardware de la máquina en Windows: modelo exacto de procesador, núcleos físicos/lógicos y cantidad de memoria física instalada en gigabytes utilizando CIM.",
    "Debo consultar las clases WMI/CIM Win32_Processor y Win32_PhysicalMemory mediante Get-CimInstance y agregar la memoria con Measure-Object.",
    "$cpu = Get-CimInstance Win32_Processor; $ram = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB; [PSCustomObject]@{ CPU = $cpu.Name; Cores = $cpu.NumberOfCores; Threads = $cpu.NumberOfLogicalProcessors; TotalRAM_GB = [math]::Round($ram, 2) } | Format-List",
    "CPU         : Intel(R) Core(TM) i5-4310U CPU @ 2.00GHz\nCores       : 2\nThreads     : 4\nTotalRAM_GB : 15.5",
    "La telemetría de hardware fue extraída directamente de la capa de instrumentación [[CIM]] de Windows reflejando la arquitectura física de cómputo.")

add("windows_powershell",
    "Comprueba la conectividad TCP contra el host 192.168.1.1 en el puerto 8001 y muestra la latencia en milisegundos y el estado de resolución de ruta.",
    "Utilizo el cmdlet nativo Test-NetConnection con los parámetros -ComputerName y -Port.",
    "Test-NetConnection -ComputerName 192.168.1.1 -Port 8001 -InformationLevel Detailed",
    "ComputerName            : 192.168.1.1\nRemoteAddress           : 192.168.1.1\nRemotePort              : 8001\nNameResolutionSucceeded : True\nTcpTestSucceeded        : True\nRoundTripTime(ms)       : 1.84",
    "La sonda de capa de transporte TCP mediante [[Test-NetConnection]] verificó que el socket remoto en el puerto 8001 responde con 1.84 ms de latencia media.")

# =============================================================================
# 6. WINDOWS CMD
# =============================================================================
add("windows_cmd",
    "En el símbolo del sistema (CMD) de Windows, encuentra el identificador PID del proceso que tiene abierto el puerto 8080 y termina el proceso forzadamente.",
    "Uso netstat -ano filtrando por :8080 para identificar el PID en la última columna, y luego ejecuto taskkill /F /PID especificando dicho identificador.",
    "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :8080') do taskkill /F /PID %a",
    "CORRECTO: se finalizó el proceso con PID 18442.",
    "Se identificó el socket activo mediante [[netstat]] y se terminó el proceso asociado de manera atómica mediante [[taskkill]] desde la consola clásica de comandos.")

add("windows_cmd",
    "Sincroniza el directorio C:\\Proyecto hacia D:\\Backup\\Proyecto mediante Robocopy excluyendo carpetas .git y archivos temporales .tmp, reflejando cambios exactamente.",
    "Debo usar el comando nativo robocopy con la bandera /MIR (mirror), /XD .git para excluir el directorio y /XF *.tmp para excluir los archivos.",
    "robocopy C:\\Proyecto D:\\Backup\\Proyecto /MIR /XD .git /XF *.tmp /R:1 /W:1 /NP",
    "               Total    Copiado   Omitido    Error\n    Directorios:    14          2        12        0\n       Archivos:   180         15       165        0\n\nVelocidad: 45.2 MB/seg. Estado: FINALIZADO CON ÉXITO.",
    "La sincronización incremental se efectuó mediante [[robocopy]] aplicando políticas de exclusión de metadatos y reintentos automáticos.")

add("windows_cmd",
    "Consulta el registro de Windows para comprobar el valor de inicio de sesión automático y modifica la clave para deshabilitarlo de forma segura.",
    "Uso reg query para auditar la clave en HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon y reg add con /f para forzar la actualización del valor AutoAdminLogon a 0.",
    "reg query \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon\" /v AutoAdminLogon && reg add \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon\" /v AutoAdminLogon /t REG_SZ /d \"0\" /f",
    "    AutoAdminLogon    REG_SZ    1\nLa operación se completó correctamente.",
    "Se inspeccionó y modificó la configuración de autenticación en el [[Registro_de_Windows]] garantizando que el inicio de sesión interactivo requiera credenciales.")

add("windows_cmd",
    "Toma propiedad administrativa del directorio C:\\Logs\\Corrupt y concede control total al grupo de Administradores de forma recursiva.",
    "Debo usar takeown /F para adueñarse del directorio de forma recursiva (/R) y luego icacls para asignar los permisos de control total (/grant Administradores:F /T).",
    "takeown /f \"C:\\Logs\\Corrupt\" /r /d y && icacls \"C:\\Logs\\Corrupt\" /grant Administradores:F /t",
    "CORRECTO: el archivo (o carpeta) pertenece ahora al usuario actual.\nprocesado correctamente 48 archivos; error de procesamiento 0 archivos",
    "La estructura de permisos ACL de [[NTFS]] fue reapropiada mediante `takeown` e `icacls` restaurando el acceso administrativo irrestricto.")

add("windows_cmd",
    "Limpia la caché de resolución DNS local y renueva la concesión de dirección IP de todos los adaptadores de red en Windows.",
    "Debo concatenar ipconfig /flushdns con ipconfig /renew.",
    "ipconfig /flushdns && ipconfig /renew",
    "Se vació correctamente la caché de resolución de DNS.\nConfiguración IP de Windows\nAdaptador de Ethernet Ethernet:\n   Dirección IPv4. . . . . . . . . . . . . . : 192.168.1.102\n   Máscara de subred . . . . . . . . . . . . : 255.255.255.0",
    "Se purgó la memoria de nombres de host y se renegoció la concesión DHCP mediante [[ipconfig]].")

# =============================================================================
# 7. MACOS (DARWIN / ZSH)
# =============================================================================
add("macos_zsh",
    "En macOS, instala el gestor de base de datos redis mediante Homebrew, levántalo como servicio en segundo plano que arranque con el sistema y comprueba si responde al ping.",
    "En macOS Darwin con Homebrew, la secuencia estándar es brew install redis, seguido de brew services start redis, y finalmente redis-cli ping para validar el socket de loopback.",
    "brew install redis && brew services start redis && sleep 1 && redis-cli ping",
    "==> Downloading https://ghcr.io/v2/homebrew/core/redis/manifests/7.2.4\n==> Pouring redis--7.2.4.arm64_sonoma.bottle.tar.gz\n==> Successfully started `redis` (label: homebrew.mxcl.redis)\nPONG",
    "El motor de base de datos fue instalado mediante [[Homebrew]] y registrado en el subsistema [[launchd]] de macOS respondiendo con éxito (`PONG`).")

add("macos_zsh",
    "Muestra la tabla de particiones APFS de los discos conectados en macOS y lista el orden de prioridad de todos los adaptadores de red de hardware.",
    "Debo utilizar la utilidad diskutil con la orden list apfs para la estructura de volúmenes, y networksetup con -listallhardwareports para los dispositivos físicos de red.",
    "diskutil list apfs && networksetup -listallhardwareports",
    "APFS Container (1 found)\n|-- Container disk3 on disk0s2 (Synthesized)\n    ====================================================\n    APFS Container Reference:     disk3\n    Capacity Ceiling (Size):      494384111616 B (494.4 GB)\n    Capacity In Use By Volumes:   215438100480 B (215.4 GB) (43.6%)\n\nHardware Port: Wi-Fi\nDevice: en0\nEthernet Address: f4:d4:88:ab:cd:ef\n\nHardware Port: Thunderbolt Bridge\nDevice: bridge0",
    "Se extrajo la jerarquía del contenedor [[APFS]] mediante `diskutil` y la asignación física de interfaces de red con `networksetup` en el kernel XNU de macOS.")

add("macos_zsh",
    "Configura macOS para que la barra de menús oculte automáticamente las aplicaciones y activa la visualización de ficheros ocultos en el Finder reiniciando el proceso.",
    "Debo invocar defaults write para el dominio com.apple.finder con AppleShowAllFiles en true y reiniciar el Finder con killall Finder.",
    "defaults write com.apple.finder AppleShowAllFiles -bool true && killall Finder",
    "[OK] Finder defaults updated and process refreshed.",
    "Las políticas de visualización de ficheros de sistema fueron aplicadas mediante [[defaults]] sobre el subsistema gráfico de macOS.")

add("macos_zsh",
    "Crea y carga un demonio Launchd en /Library/LaunchDaemons/com.sentinel.service.plist que arranque un binario en /opt/sentinel/agent al iniciar macOS.",
    "Debo generar el fichero XML de Property List (.plist) atómicamente con cat heredoc y registrarlo con launchctl bootstrap.",
    "cat << 'EOF' | sudo tee /Library/LaunchDaemons/com.sentinel.service.plist > /dev/null\n<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n<plist version=\"1.0\">\n<dict>\n    <key>Label</key>\n    <string>com.sentinel.service</string>\n    <key>ProgramArguments</key>\n    <array>\n        <string>/opt/sentinel/agent</string>\n    </array>\n    <key>RunAtLoad</key>\n    <true/>\n    <key>KeepAlive</key>\n    <true/>\n</dict>\n</plist>\nEOF\nsudo launchctl bootstrap system /Library/LaunchDaemons/com.sentinel.service.plist && sudo launchctl print system/com.sentinel.service",
    "state = running\npid = 918\nlast exit code = (never exited)",
    "El servicio en segundo plano quedó orquestado en el subsistema [[launchd]] de macOS bajo ciclo de vida vigilado (`KeepAlive`).")

# =============================================================================
# 8. AUTO-INSTALACIÓN Y DESPLIEGUE AUTÓNOMO
# =============================================================================
add("self_installation",
    "Instala de manera autónoma el agente de Sentinel en esta máquina Linux: detecta la arquitectura, clona el repositorio en /opt/sentinel, inicializa un entorno virtual, instala dependencias de requirements.txt y registra el demonio systemd.",
    "Debo auditar la arquitectura con uname -m, verificar dependencias esenciales (git, python3-venv), crear el directorio en /opt/sentinel, clonar o configurar el repo, construir el venv e instalar paquetes.",
    "ARCH=$(uname -m) && echo \"[SETUP] Detectada arquitectura: $ARCH\" && sudo mkdir -p /opt/sentinel && sudo chown -R $USER:$USER /opt/sentinel && cd /opt/sentinel && python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install uvicorn fastapi pydantic requests",
    "[SETUP] Detectada arquitectura: x86_64\nRequirement already satisfied: pip\nSuccessfully installed fastapi-0.110.0 pydantic-2.6.4 uvicorn-0.29.0 requests-2.31.0",
    "El entorno de ejecución para [[SENTINEL]] quedó inicializado de forma aislada en un [[venv]] con resolución automática de dependencias y detección de arquitectura `x86_64`.")

add("self_installation",
    "En Windows, instala y aprovisiona el entorno autónomo de Sentinel en C:\\Sentinel creando el entorno virtual de Python y configurando una tarea programada para que inicie automáticamente al arrancar la máquina.",
    "Debo crear la carpeta con New-Item, invocar python -m venv, instalar dependencias con pip y registrar una tarea programada con Register-ScheduledTask ejecutándose como SYSTEM.",
    "powershell -Command \"$path = 'C:\\Sentinel'; if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force }; Set-Location $path; python -m venv .venv; .\\.venv\\Scripts\\python.exe -m pip install --upgrade pip; .\\.venv\\Scripts\\pip.exe install fastapi uvicorn; $action = New-ScheduledTaskAction -Execute '$path\\.venv\\Scripts\\python.exe' -Argument '$path\\main.py'; $trigger = New-ScheduledTaskTrigger -AtStartup; Register-ScheduledTask -TaskName 'SentinelService' -Action $action -Trigger $trigger -RunLevel Highest -Force\"",
    "TaskPath TaskName        State\n-------- --------        -----\n\\        SentinelService Ready",
    "Se aprovisionó el subsistema de Sentinel en `C:\\Sentinel` y se registró la persistencia operativa mediante el Programador de Tareas de Windows ([[Task_Scheduler]]) con privilegios elevados.")

add("self_installation",
    "Realiza una autoverificación de salud del nodo recién desplegado comprobando el socket TCP local, la latencia de respuesta HTTP en /health y el uso de RAM del proceso del agente.",
    "Debo ejecutar un curl contra 127.0.0.1:8001/health con métricas de tiempo y consultar ps para la memoria residente RSS del proceso uvicorn.",
    "curl -s -w '\\nTiempo Total: %{time_total}s | Codigo HTTP: %{http_code}\\n' http://127.0.0.1:8001/health && ps -C python3 -o pid,rss,cmd | grep uvicorn",
    "{\"status\":\"healthy\",\"version\":\"1.0.0\",\"service\":\"sentinel-backend\"}\nTiempo Total: 0.003s | Codigo HTTP: 200\n 18942  42512 python3 -m uvicorn main:app --port 8001",
    "La verificación de integridad concluyó exitosamente: el endpoint responde en 3 ms con código 200 y una huella de memoria física de aproximadamente 42 MB en [[RSS]].")

# =============================================================================
# 9. REACT RESILIENTE CON RECUPERACIÓN DE ERRORES (MULTI-STEP ERROR RECOVERY)
# =============================================================================
add("error_recovery",
    "Inicia el servidor backend en el puerto 8001. Si el puerto está bloqueado por otro proceso zombi, identifícalo, termina el proceso bloqueante y levanta el servicio exitosamente.",
    "Primero intentaré verificar si el puerto 8001 está ocupado. Usaré fuser o ss para auditar el socket.",
    "sudo fuser -k 8001/tcp || echo 'Puerto libre'",
    "8001/tcp:             15422",
    "Se identificó y eliminó el proceso huérfano con PID 15422 que retenía el socket TCP mediante [[fuser]], dejando el puerto 8001 listo para el enlace inmediato del servidor ASGI.")

add("error_recovery",
    "Al intentar instalar un paquete con apt en Ubuntu aparece el error 'Could not get lock /var/lib/dpkg/lock-frontend'. Diagnostica qué proceso retiene el bloqueo, libéralo y repara el estado del gestor de paquetes.",
    "El bloqueo de frontend de dpkg ocurre cuando unattended-upgrades u otro proceso apt está activo. Debo encontrar el PID con lsof o fuser, esperar o terminar el proceso, y reconfigurar la base de datos con dpkg --configure -a.",
    "sudo fuser -v /var/lib/dpkg/lock-frontend 2>/dev/null; sudo killall apt apt-get 2>/dev/null; sudo rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock; sudo dpkg --configure -a",
    "Configuring unattended-upgrades (2.9.1) ...\nProcessing triggers for man-db (2.12.0) ...",
    "Se resolvió la colisión de bloqueos sobre la base de datos de [[dpkg]], terminando procesos bloqueantes y restaurando la consistencia transaccional del gestor de paquetes [[apt]].")

add("error_recovery",
    "En Windows PowerShell, un script de automatización falla con el error 'File cannot be loaded because running scripts is disabled on this system'. Corrige la restricción para el ámbito actual sin alterar la directiva global del sistema.",
    "El error se debe a la ExecutionPolicy de PowerShell. Para corregirlo de forma segura sin vulnerar las directivas de máquina, debo establecer la política en RemoteSigned o Bypass exclusivamente con -Scope Process.",
    "Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; Get-ExecutionPolicy -List",
    "        Scope ExecutionPolicy\n        ----- ---------------\nMachinePolicy       Undefined\n   UserPolicy       Undefined\n      Process          Bypass\n  CurrentUser       Undefined\n LocalMachine    Restricted",
    "Se desbloqueó la ejecución de scripts asignando la directiva `Bypass` en el ámbito volátil del proceso actual mediante `Set-ExecutionPolicy` en [[PowerShell]], garantizando el aislamiento de seguridad sobre la máquina local.")

add("error_recovery",
    "El servidor se quedó sin espacio en disco impidiendo la escritura de logs ('No space left on device'). Identifica las causas, depura logs rotados antiguos y libera espacio inmediatamente.",
    "Debo auditar las particiones con df -h, identificar directorios masivos con du y liberar espacio en los diarios de systemd mediante journalctl --vacuum-size.",
    "df -h / && sudo journalctl --vacuum-size=100M && sudo apt-get clean && df -h /",
    "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        20G   20G    0G 100% /\nVacuuming done, freed 3.8G of archived journals from /var/log/journal.\nFilesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        20G   15G  4.2G  78% /",
    "Se recuperó el espacio crítico de almacenamiento purgando diarios archivados con `journalctl --vacuum-size` y limpiando el almacén de paquetes de [[apt]], restaurando la operatividad del sistema de ficheros.")

def generate_expanded_terminal_samples():
    # 1. Ubuntu / Debian combinatorios
    services_debian = [
        ("postgresql", 5432, "motor de base de datos relacional PostgreSQL"),
        ("mariadb", 3306, "servidor de base de datos MariaDB / MySQL"),
        ("redis-server", 6379, "almacén en memoria de clave-valor Redis"),
        ("docker", 2375, "motor de contenedores Docker"),
        ("tailscaled", 41641, "demonio de túneles VPN en malla Tailscale"),
        ("ssh", 22, "demonio de acceso remoto seguro OpenSSH"),
        ("cron", 0, "planificador de tareas periódicas cron")
    ]
    for svc, port, desc in services_debian:
        add(
            "linux_ubuntu_debian",
            f"Verifica el estado de ejecución de {svc} en Ubuntu, reinícialo de forma limpia y valida que esté activo.",
            f"Debo invocar systemctl restart para {svc} y verificar el estado con is-active.",
            f"sudo systemctl restart {svc} && sudo systemctl is-active {svc}",
            f"active",
            f"El servicio de [[{svc}]] ({desc}) fue reiniciado y confirmado en estado operacional activo mediante [[systemd]]."
        )
        if port > 0:
            add(
                "linux_ubuntu_debian",
                f"Configura UFW para permitir el tráfico entrante al puerto {port}/tcp de {svc} limitando el acceso a la subred local 192.168.1.0/24.",
                f"Debo estructurar la regla de ufw permitiendo proto tcp desde la subred local hacia cualquier IP en el puerto {port}.",
                f"sudo ufw allow proto tcp from 192.168.1.0/24 to any port {port} comment '{svc} LAN' && sudo ufw status | grep {port}",
                f"{port}/tcp                     ALLOW       192.168.1.0/24             # {svc} LAN",
                f"El puerto {port} para [[{svc}]] fue expuesto exclusivamente al segmento LAN seguro mediante directivas de [[ufw]]."
            )

    # 2. Arch Linux combinatorios
    arch_packages = [
        ("ripgrep", "rg", "utilidad de búsqueda recursiva de expresiones regulares ultrarrápida"),
        ("htop", "htop", "monitor interactivo de procesos del sistema"),
        ("git", "git", "sistema de control de versiones distribuido"),
        ("neovim", "nvim", "editor de texto modal optimizado y extensible"),
        ("tmux", "tmux", "multiplexor de terminales de consola")
    ]
    for pkg, bin_name, desc in arch_packages:
        add(
            "linux_arch",
            f"En Arch Linux, comprueba si el paquete {pkg} está instalado. Si no lo está, instálalo con pacman sin confirmación interactiva y muestra la ruta de su binario.",
            f"Uso pacman -Q para auditar la presencia local del paquete, y si falta ejecuto pacman -S --noconfirm seguido de which.",
            f"pacman -Q {pkg} 2>/dev/null || sudo pacman -S --noconfirm {pkg} && which {bin_name}",
            f"/usr/bin/{bin_name}",
            f"El paquete [[{pkg}]] ({desc}) fue validado e instalado mediante [[pacman]], ubicando el binario ejecutable en el path del sistema."
        )

    # 3. Kali Linux escaneos y auditorías
    kali_targets = [
        ("192.168.1.10", "22,80,443", "servidor web de producción"),
        ("192.168.1.254", "53,67,80", "puerta de enlace y router principal"),
        ("10.0.0.15", "8001,8080", "instancia backend de microservicios")
    ]
    for ip, ports, desc in kali_targets:
        add(
            "linux_kali",
            f"Realiza un análisis rápido de puertos con nmap sobre {ip} ({desc}) para los puertos {ports} identificando versiones sin resolución DNS.",
            f"Uso nmap con banderas -sV, -n, -T4 y -p para {ports}.",
            f"sudo nmap -sV -n -T4 -p {ports} {ip}",
            f"Starting Nmap 7.94\nNmap scan report for {ip}\nHost is up (0.0011s latency).\nPORT     STATE SERVICE VERSION\n(puertos auditados respondiendo con sockets abiertos)",
            f"La auditoría de superficie sobre [[{ip}]] ({desc}) fue completada mediante [[Nmap]] determinando el perfil de exposición de red."
        )

    # 4. Manipulación POSIX de ficheros y streams
    posix_scenarios = [
        ("/etc/hosts", "127.0.0.1\\s+localhost", "127.0.0.1 localhost sentinel.local", "inyección de hostname en resolución local"),
        ("/opt/sentinel/.env", "DEBUG=True", "DEBUG=False", "conmutación de entorno de desarrollo a producción"),
        ("/opt/sentinel/config.json", "\"log_level\": \"debug\"", "\"log_level\": \"warning\"", "modificación de granularidad de registro de logs")
    ]
    for filepath, pattern, repl, desc in posix_scenarios:
        add(
            "posix_file_ops",
            f"Modifica de manera atómica el fichero {filepath} reemplazando '{pattern}' por '{repl}' conservando una copia de seguridad.",
            f"Utilizo sed con la bandera -i.bak aplicando la sustitución con delimitador seguro.",
            f"sudo sed -i.bak 's|{pattern}|{repl}|g' {filepath} && diff -u {filepath}.bak {filepath} || true",
            f"-{pattern}\n+{repl}",
            f"Se aplicó la mutación atómica en [[sed]] para `{filepath}` ({desc}) verificando el diff unificado del parche."
        )

    # 5. Windows PowerShell administración
    ps_services = [
        ("wuauserv", "servicio de Windows Update"),
        ("WinDefend", "servicio de protección de Windows Defender"),
        ("Dnscache", "servicio de caché de resolución de nombres DNS")
    ]
    for svc, desc in ps_services:
        add(
            "windows_powershell",
            f"En PowerShell, inspecciona el estado actual del {desc} ({svc}) mostrando el modo de inicio y el estado de ejecución.",
            f"Utilizo Get-Service proyectando Name, Status y StartType.",
            f"Get-Service -Name {svc} | Select-Object Name, Status, StartType | Format-Table -AutoSize",
            f"Name      Status  StartType\n----      ------  ---------\n{svc}     Running Automatic",
            f"El estado del [[{svc}]] ({desc}) fue auditado exitosamente a través del proveedor de servicios de [[PowerShell]]."
        )

    # 6. Windows CMD control
    cmd_scenarios = [
        ("explorer.exe", "árbol de procesos del explorador gráfico de Windows"),
        ("notepad.exe", "instancias huérfanas de editor de texto"),
        ("conhost.exe", "procesos de consola de comandos en desuso")
    ]
    for proc, desc in cmd_scenarios:
        add(
            "windows_cmd",
            f"En el símbolo del sistema de Windows (CMD), verifica cuántos procesos {proc} existen y finalízalos de forma forzada si están colgados.",
            f"Debo invocar tasklist filtrando por el nombre del ejecutable y terminar con taskkill /F /IM.",
            f"tasklist /FI \"IMAGENAME eq {proc}\" && taskkill /F /IM {proc} /T",
            f"Nombre de imagen               PID Nombre de sesión Núm. de ses   Uso de mem\n========================= ======== ================ =========== ============\n{proc}                     1024 Console                    1      12,410 KB\nCORRECTO: se finalizó el proceso \"{proc}\" con PID 1024.",
            f"Se gestionó la terminación controlada del [[{proc}]] ({desc}) mediante los comandos nativos [[tasklist]] y [[taskkill]]."
        )

    # 7. macOS Darwin administración
    mac_services = [
        ("postgresql@16", "instancia relacional PostgreSQL 16"),
        ("nginx", "servidor proxy reverso Nginx"),
        ("tailscale", "interfaz de red segura Tailscale")
    ]
    for svc, desc in mac_services:
        add(
            "macos_zsh",
            f"En macOS, reinicia el servicio {svc} mediante Homebrew Services y muestra el código de salida y estado del demonio.",
            f"Uso brew services restart seguido de brew services list.",
            f"brew services restart {svc} && brew services list | grep {svc}",
            f"Stopping `{svc}`... (might take a while)\n==> Successfully started `{svc}` (label: homebrew.mxcl.{svc})\n{svc} started mauro ~/Library/LaunchAgents/homebrew.mxcl.{svc}.plist",
            f"El ciclo de vida del servicio [[{svc}]] ({desc}) fue reanudado bajo el orquestador [[Homebrew]] y [[launchd]] en macOS."
        )

    # 8. Redes avanzadas Linux (Policy Routing, VLANs, Bonding)
    add(
        "linux_ubuntu_debian",
        "Configura en caliente una tabla de enrutamiento por políticas para que todo el tráfico proveniente de la IP 192.168.1.200 salga por la interfaz eth1 con puerta de enlace 192.168.2.1.",
        "Debo registrar la tabla de enrutamiento personalizada, asociar la ruta por defecto mediante ip route add y crear la regla de política mediante ip rule add.",
        "sudo ip route add default via 192.168.2.1 dev eth1 table 100 && sudo ip rule add from 192.168.1.200/32 table 100 && ip rule show",
        "0:      from all lookup local\n32765:  from 192.168.1.200 lookup 100\n32766:  from all lookup main",
        "El enrutamiento por políticas ([[Policy_Routing]]) fue aplicado vinculando la IP de origen a la tabla 100 a través de [[iproute2]]."
    )
    add(
        "linux_ubuntu_debian",
        "Configura una regla NAT de enmascaramiento con iptables para compartir Internet desde eth0 hacia la red local en eth1 y habilita el reenvío de paquetes en el kernel.",
        "Debo habilitar net.ipv4.ip_forward mediante sysctl y añadir la regla POSTROUTING MASQUERADE en la tabla nat de iptables.",
        "sudo sysctl -w net.ipv4.ip_forward=1 && sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE && sudo iptables -t nat -L POSTROUTING -n -v",
        "net.ipv4.ip_forward = 1\nChain POSTROUTING (policy ACCEPT 12 packets, 840 bytes)\n pkts bytes target     prot opt in     out     source               destination\n    0     0 MASQUERADE  all  --  *      eth0    0.0.0.0/0            0.0.0.0/0",
        "La traducción de direcciones de red ([[NAT]]) por enmascaramiento y el forward de paquetes IPv4 en el [[kernel]] quedaron operativos."
    )

    # 9. Seguridad y Auditoría Kali / Linux
    add(
        "linux_kali",
        "Inspecciona el tráfico de peticiones DNS en tiempo real en la interfaz eth0 extrayendo el nombre de dominio consultado y la IP origen utilizando tshark.",
        "Debo ejecutar tshark filtrando por puerto udp 53, extrayendo los campos dns.qry.name e ip.src en formato de texto tabulado.",
        "sudo tshark -i eth0 -n -f 'udp port 53' -Y 'dns.flags.response == 0' -T fields -e ip.src -e dns.qry.name -c 5",
        "192.168.1.105   api.github.com\n192.168.1.105   raw.githubusercontent.com\n192.168.1.102   labsentinel.tailc83bd7.ts.net\n192.168.1.105   pypi.org\n192.168.1.105   files.pythonhosted.org",
        "La telemetría de resolución [[DNS]] en tiempo real fue decodificada con [[tshark]] revelando consultas de telemetría y dominios de paquetes."
    )
    add(
        "linux_kali",
        "Verifica si un ejecutable o binario sospechoso en /tmp/payload contiene URLs, direcciones IP o rutas de depuración antes de ejecutarlo.",
        "Uso strings filtrando con grep por expresiones regulares de direcciones IPv4 y esquemas HTTP/HTTPS.",
        "strings -n 8 /tmp/payload | grep -E 'https?://|[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}' | head -10",
        "http://192.168.1.50:8000/connect\nhttps://telemetry.service.local/ping",
        "El análisis estático preliminar con [[strings]] extrajo las referencias de red incrustadas en el binario sin comprometer la máquina."
    )

    # 10. Diagnóstico Avanzado de Rendimiento en POSIX
    add(
        "posix_file_ops",
        "Muestra los 5 procesos que mayor tasa de operaciones de entrada/salida (I/O) en disco están generando en el sistema utilizando pidstat.",
        "Uso pidstat con la bandera -d para I/O de disco, muestreando cada 1 segundo y ordenando por la columna de escritura.",
        "pidstat -d 1 1 | sort -k5 -rn | head -n 5",
        "12:30:01      1842    2540.00    8420.00      postgres\n12:30:01      2104       0.00    1200.00      uvicorn\n12:30:01       412       0.00     310.00      systemd-journal",
        "El perfilado de almacenamiento mediante [[pidstat]] identificó que el clúster [[PostgreSQL]] genera el 80% de escrituras en disco del host."
    )

    # 11. Windows Event Log y Firewall PowerShell
    add(
        "windows_powershell",
        "Consulta en Windows los últimos 5 eventos críticos o de error en el visor de sucesos (EventLog) del sistema ocurridos en las últimas 24 horas.",
        "Utilizo Get-WinEvent con un FilterHashtable que filtre LogName='System', Level=1,2 (Critical, Error) y StartTime de 24 horas atrás.",
        "Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=(Get-Date).AddDays(-1)} -MaxEvents 5 | Select-Object TimeCreated, Id, ProviderName, Message | Format-List",
        "TimeCreated  : 26/09/2026 11:15:20\nId           : 10016\nProviderName : Microsoft-Windows-DistributedCOM\nMessage      : La configuración de permisos específicos de la aplicación...",
        "La auditoría del [[EventLog]] de Windows mediante `Get-WinEvent` recuperó los sucesos de anomalías del subsistema DCOM y kernel."
    )
    add(
        "windows_powershell",
        "Crea una regla de firewall en Windows para permitir el puerto entrante 8001 para la aplicación de Sentinel en perfiles Privado y Dominio.",
        "Debo utilizar New-NetFirewallRule con el nombre SentinelPort, Direction Inbound, Action Allow, Protocol TCP, LocalPort 8001 y Profile Domain, Private.",
        "New-NetFirewallRule -DisplayName 'SENTINEL Backend 8001' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8001 -Profile Domain, Private",
        "Name                  : {9b23-sentinel}\nDisplayName           : SENTINEL Backend 8001\nEnabled               : True\nProfile               : Domain, Private\nDirection             : Inbound\nAction                : Allow\nLocalPort             : 8001\nProtocol              : TCP",
        "Se provisionó la directiva perimetral en el Firewall de Windows con seguridad avanzada ([[Windows_Firewall]]) para el backend."
    )

    # 12. Windows CMD Reparación y Verificación de Integridad
    add(
        "windows_cmd",
        "Ejecuta una comprobación de integridad del almacén de componentes de Windows mediante DISM y repara cualquier archivo corrupto utilizando Windows Update como fuente.",
        "Uso dism con /Online /Cleanup-Image /RestoreHealth.",
        "DISM.exe /Online /Cleanup-Image /RestoreHealth",
        "Herramienta Administración y mantenimiento de imágenes de implementación\nVersión: 10.0.22621.1\n[==========================100.0%==========================]\nLa operación de restauración se completó correctamente.\nLa operación se completó correctamente.",
        "El almacén de componentes de la imagen del sistema operativo fue saneado mediante la utilidad nativa [[DISM]]."
    )

    # 13. Auto-instalación y Bootstrap Desatendido Cross-Platform
    add(
        "self_installation",
        "Genera un script bootstrap en Bash autónomo que descargue el agente, configure el entorno y levante el servicio sin interacción.",
        "Debo estructurar un script seguro con set -euo pipefail, comprobar dependencias (python3, curl, git), inicializar venv y desplegar servicio.",
        "cat << 'EOF' > /tmp/bootstrap_sentinel.sh\n#!/usr/bin/env bash\nset -euo pipefail\nINSTALL_DIR=\"/opt/sentinel\"\necho \"[1/4] Creando directorio en $INSTALL_DIR...\"\nsudo mkdir -p \"$INSTALL_DIR\" && sudo chown -R \"$USER:$USER\" \"$INSTALL_DIR\"\necho \"[2/4] Aprovisionando entorno virtual Python...\"\npython3 -m venv \"$INSTALL_DIR/.venv\"\n\"$INSTALL_DIR/.venv/bin/pip\" install --upgrade pip uvicorn fastapi pydantic requests >/dev/null\necho \"[3/4] Creando servicio systemd...\"\ncat << 'SERVICE' | sudo tee /etc/systemd/system/sentinel.service > /dev/null\n[Unit]\nDescription=SENTINEL Core Service\nAfter=network.target\n[Service]\nExecStart=/opt/sentinel/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001\nRestart=always\n[Install]\nWantedBy=multi-user.target\nSERVICE\nsudo systemctl daemon-reload && sudo systemctl enable --now sentinel.service\necho \"[4/4] Bootstrap completado exitosamente.\"\nEOF\nchmod +x /tmp/bootstrap_sentinel.sh && /tmp/bootstrap_sentinel.sh",
        "[1/4] Creando directorio en /opt/sentinel...\n[2/4] Aprovisionando entorno virtual Python...\n[3/4] Creando servicio systemd...\nCreated symlink /etc/systemd/system/multi-user.target.wants/sentinel.service -> /etc/systemd/system/sentinel.service.\n[4/4] Bootstrap completado exitosamente.",
        "Se ejecutó el aprovisionamiento autónomo integral de [[SENTINEL]] mediante un script [[Bash]] idempotente con persistencia de servicio."
    )

def main():
    generate_expanded_terminal_samples()
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in SAMPLES:
            entry = {
                "system": SYSTEM_PROMPT,
                "platform": item["platform"],
                "instruction": item["instruction"],
                "trajectory": [
                    {"role": "user", "content": item["instruction"]},
                    {"role": "assistant", "content": f"[THOUGHT] {item['thought']} [/THOUGHT]\n[EXECUTE] {item['command']} [/EXECUTE]"},
                    {"role": "environment", "content": f"[OUTPUT]\n{item['output']}\n[/OUTPUT]"},
                    {"role": "assistant", "content": item["final_answer"]}
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            count += 1

    print(f"[OK] Generado dataset de control de terminal multiplataforma: {OUTPUT_FILE} ({count} trayectorias listas)")

if __name__ == "__main__":
    main()

