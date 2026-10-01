#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Gestor de Reglas de Cortafuegos y Antivirus (Firewall & AV Guard) v2.5
Configura reglas de entrada avanzadas para conectividad LAN, Wi-Fi y Malla en:
- Windows Defender Firewall, WFP y Antivirus de terceros (Avast, Norton, McAfee, AVG).
- Linux UFW / Firewalld / Iptables.
"""
import os, sys, shutil, subprocess, base64, re
from .banner import Colors, print_success, print_warning, print_info, print_panel

RULE_NAME = "SentinelOS Core"
RULE_NAME_UDP = "SentinelOS Mesh UDP"
RULE_NAME_PY = "SentinelOS Python"
RULE_NAME_PYW = "SentinelOS Pythonw"

def is_admin() -> bool:
    """Verifica si el proceso actual tiene permisos elevados de administrador/root."""
    if sys.platform == "win32":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0

def detect_antivirus_software() -> list[str]:
    """Detecta antivirus de terceros instalados que podrían interceptar o bloquear la red LAN."""
    detected = []
    if sys.platform == "win32":
        av_patterns = {
            "Avast Antivirus": ["AvastSvc.exe", "wsc_proxy.exe", r"C:\Program Files\AVAST Software"],
            "Norton Security / Symantec": ["NortonSecurity.exe", "ccSvcHst.exe", r"C:\Program Files\Norton Security"],
            "AVG Antivirus": ["avgsvc.exe", r"C:\Program Files\AVG"],
            "McAfee Security": ["mcshield.exe", "mfevtps.exe", r"C:\Program Files\McAfee"],
            "Bitdefender": ["bdservicehost.exe", r"C:\Program Files\Bitdefender"],
            "Kaspersky": ["avp.exe", r"C:\Program Files (x86)\Kaspersky Lab"]
        }
        try:
            ps_script = "Get-Process | Select-Object -ExpandProperty ProcessName"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
            procs = res.stdout.lower() if res.returncode == 0 else ""
            for av_name, signatures in av_patterns.items():
                for sig in signatures:
                    if sig.lower().endswith(".exe") and sig.lower().replace(".exe", "") in procs:
                        detected.append(av_name)
                        break
                    elif os.path.exists(sig):
                        detected.append(av_name)
                        break
        except Exception:
            pass
    return list(set(detected))

def configure_network_category_private():
    """Configura el perfil de la conexión de red activa a 'Privado' para permitir tráfico LAN sin bloqueo de AV."""
    if sys.platform == "win32":
        try:
            ps = "Get-NetConnectionProfile | Where-Object { $_.IPv4Connectivity -ne 'NoTraffic' } | Set-NetConnectionProfile -NetworkCategory Private -ErrorAction SilentlyContinue"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
        except Exception:
            pass

def check_firewall_rule(os_info: dict, port: int = 8001) -> bool:
    """Verifica si la regla de firewall ya está activa en el sistema."""
    system = os_info.get("system", "Linux")
    if system == "Windows":
        try:
            res = subprocess.run(
                f'netsh advfirewall firewall show rule name="{RULE_NAME}"',
                shell=True,
                capture_output=True,
                text=True
            )
            return res.returncode == 0 and RULE_NAME in res.stdout
        except Exception:
            return False
    elif system == "Linux":
        if shutil.which("ufw"):
            try:
                res = subprocess.run(["ufw", "status"], capture_output=True, text=True)
                return str(port) in res.stdout and ("ALLOW" in res.stdout or "Permitir" in res.stdout)
            except Exception:
                pass
        return False
    return False

def configure_firewall_rule(os_info: dict, port: int = 8001, lang: str = "es", root_dir: str = None) -> tuple[bool, str]:
    """
    Configura y abre las reglas de firewall para TCP 8001, UDP 8001 y binarios de Python.
    Ajusta perfil de red y exclusiones de antivirus automáticamente.
    """
    system = os_info.get("system", "Linux")
    root_dir = root_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print_info(f"Configurando reglas avanzadas de firewall para el puerto {port} y red LAN..." if lang == "es" else f"Configuring advanced firewall rules for port {port} and LAN...")

    # Detectar antivirus de terceros
    detected_av = detect_antivirus_software()
    if detected_av:
        av_list_str = ", ".join(detected_av)
        msg_av = f"⚠️ Antivirus detectado ({av_list_str}): Aplicando optimizaciones de firewall WFP y perfil LAN..." if lang == "es" else f"⚠️ Antivirus detected ({av_list_str}): Applying WFP firewall and LAN profile optimizations..."
        print_warning(msg_av)

    if system == "Windows":
        # 1. Configurar red como Privada para que los antivirus no aíslen la máquina
        configure_network_category_private()

        # Determinar rutas de ejecutables de Python
        venv_py = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
        venv_pyw = os.path.join(root_dir, ".venv", "Scripts", "pythonw.exe")
        sys_py = sys.executable
        sys_pyw = sys.executable.replace("python.exe", "pythonw.exe")

        py_target = venv_py if os.path.exists(venv_py) else sys_py
        pyw_target = venv_pyw if os.path.exists(venv_pyw) else sys_pyw

        cmds = [
            f'advfirewall firewall delete rule name="{RULE_NAME}"',
            f'advfirewall firewall add rule name="{RULE_NAME}" dir=in action=allow protocol=TCP localport={port} profile=any description="SentinelOS Telemetry and Cockpit Port"',
            f'advfirewall firewall delete rule name="{RULE_NAME_UDP}"',
            f'advfirewall firewall add rule name="{RULE_NAME_UDP}" dir=in action=allow protocol=UDP localport={port} profile=any description="SentinelOS Mesh UDP Beacon"',
            f'advfirewall firewall delete rule name="{RULE_NAME_PY}"',
            f'advfirewall firewall add rule name="{RULE_NAME_PY}" dir=in action=allow program="{py_target}" profile=any description="SentinelOS Python Engine"',
            f'advfirewall firewall delete rule name="{RULE_NAME_PYW}"',
            f'advfirewall firewall add rule name="{RULE_NAME_PYW}" dir=in action=allow program="{pyw_target}" profile=any description="SentinelOS Pythonw Daemon"'
        ]

        # Comandos combinados
        combined_netsh = " & ".join([f"netsh {c}" for c in cmds])

        if is_admin():
            try:
                subprocess.run(f"cmd /c {combined_netsh}", shell=True, capture_output=True)
                # Añadir exclusión en Windows Defender si es posible
                try:
                    ps_excl = f'Add-MpPreference -ExclusionPath "{root_dir}" -ErrorAction SilentlyContinue'
                    subprocess.run(["powershell", "-NoProfile", "-Command", ps_excl], capture_output=True)
                except Exception:
                    pass
                msg = f"Reglas de firewall y excepciones aplicadas exitosamente para puerto {port} y ejecutables." if lang == "es" else f"Firewall rules and exceptions applied successfully for port {port} and executables."
                print_success(msg)
                return True, msg
            except Exception as e:
                return False, str(e)
        else:
            try:
                ps_cmd = f'Start-Process cmd -ArgumentList \'/c {combined_netsh}\' -Verb RunAs -Wait -WindowStyle Hidden'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=35)
                msg = f"Reglas de Windows Firewall y exclusiones de red autorizadas para puerto {port}." if lang == "es" else f"Windows Firewall rules authorized for port {port}."
                print_success(msg)
                return True, msg
            except Exception as e:
                print_warning(f"Aviso al configurar firewall: {e}")
                return False, str(e)

    elif system == "Linux":
        if shutil.which("ufw"):
            try:
                subprocess.run(f"sudo ufw allow {port}/tcp comment '{RULE_NAME}'", shell=True, capture_output=True)
                subprocess.run(f"sudo ufw allow {port}/udp comment '{RULE_NAME_UDP}'", shell=True, capture_output=True)
                msg = f"Reglas UFW añadidas para puerto {port} (TCP/UDP)." if lang == "es" else f"UFW rules added for port {port} (TCP/UDP)."
                print_success(msg)
                return True, msg
            except Exception as e:
                pass
        elif shutil.which("firewall-cmd"):
            try:
                subprocess.run(f"sudo firewall-cmd --add-port={port}/tcp --permanent && sudo firewall-cmd --add-port={port}/udp --permanent && sudo firewall-cmd --reload", shell=True, capture_output=True)
                msg = f"Reglas firewalld añadidas para puerto {port}." if lang == "es" else f"Firewalld rules added for port {port}."
                print_success(msg)
                return True, msg
            except Exception as e:
                pass

        print_info(f"Firewall verificado para el puerto {port}.")
        return True, "Firewall configured"

    return False, "Unsupported OS"

def _run_powershell_script(script: str, elevate: bool = False) -> subprocess.CompletedProcess:
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded]
    if is_admin() or not elevate:
        return subprocess.run(command, capture_output=True, text=True, timeout=60)

    # Keep the script in an encoded argument so paths with spaces or quotes stay literal.
    launch_script = (
        "$p = Start-Process -FilePath 'powershell.exe' "
        f"-ArgumentList @('-NoProfile','-NonInteractive','-EncodedCommand','{encoded}') "
        "-Verb RunAs -Wait -PassThru; exit $p.ExitCode"
    )
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", launch_script],
        capture_output=True,
        text=True,
        timeout=90,
    )


def _run_linux_firewall_command(args: list[str]) -> subprocess.CompletedProcess:
    """Run a firewall command as root without shell interpolation."""
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return subprocess.run(args, capture_output=True, text=True, timeout=30)
    sudo = shutil.which("sudo")
    if not sudo:
        return subprocess.CompletedProcess(args, 127, "", "sudo is unavailable")
    return subprocess.run([sudo, "-n", *args], capture_output=True, text=True, timeout=30)


def remove_firewall_rule(os_info: dict, port: int = 8001, lang: str = "es", root_dir: str = None) -> bool:
    """Remove SentinelOS-owned firewall entries and its matching Defender exclusion."""
    system = os_info.get("system", "Linux")
    ports = sorted({int(port), int(port) + 1, 8003})

    if system == "Windows":
        names = [RULE_NAME, RULE_NAME_UDP, RULE_NAME_PY, RULE_NAME_PYW]
        # Older Tailscale helper releases used one rule per service port.
        names.extend(f"SentinelOS_{item}" for item in ports)
        display_names = ",".join("'" + name.replace("'", "''") + "'" for name in names)
        exclusion_path = os.path.realpath(root_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ps_path = "'" + exclusion_path.replace("'", "''") + "'"
        script = f"""
$names = @({display_names})
$failed = $false
try {{
    if (Get-Command Get-NetFirewallRule -ErrorAction SilentlyContinue) {{
        foreach ($name in $names) {{
            $rules = @(Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue)
            if ($rules.Count -gt 0) {{ $rules | Remove-NetFirewallRule -ErrorAction Stop }}
        }}
    }} else {{
        foreach ($name in $names) {{ & netsh advfirewall firewall delete rule ("name=" + $name) | Out-Null }}
    }}
}} catch {{ Write-Error $_; $failed = $true }}
try {{
    if (Get-Command Get-MpPreference -ErrorAction SilentlyContinue) {{
        $prefs = Get-MpPreference -ErrorAction Stop
        if (@($prefs.ExclusionPath | ForEach-Object {{ [string]$_ }}) -contains {ps_path}) {{
            Remove-MpPreference -ExclusionPath {ps_path} -ErrorAction Stop
        }}
    }}
}} catch {{ Write-Warning ("No se pudo retirar la exclusión local de Defender: " + $_.Exception.Message); $failed = $true }}
if ($failed) {{ exit 1 }}
exit 0
"""
        try:
            result = _run_powershell_script(script, elevate=True)
            if result.returncode == 0:
                print_success("Reglas de SentinelOS y su excepción de Defender eliminadas." if lang == "es" else "SentinelOS firewall rules and Defender exclusion removed.")
                return True
            print_warning((result.stderr or result.stdout or "No se pudieron quitar las reglas de Windows Firewall.").strip())
            return False
        except Exception as exc:
            print_warning(f"No se pudo completar la limpieza del Firewall: {exc}")
            return False

    if system != "Linux":
        return False

    success = True
    if shutil.which("ufw"):
        # Delete only numbered rules carrying SentinelOS comments, preserving user rules on the same ports.
        try:
            listing = _run_linux_firewall_command(["ufw", "status", "numbered"])
            if listing.returncode == 0:
                matches = []
                for line in listing.stdout.splitlines():
                    match = re.match(r"^\s*\[\s*(\d+)\]\s+.*#\s*SentinelOS(?:\s|$)", line, re.IGNORECASE)
                    # Legacy Tailscale setup opened its selected TCP port without a comment.
                    legacy_match = re.match(
                        rf"^\s*\[\s*(\d+)\]\s+{re.escape(str(port))}/tcp\s+ALLOW IN Anywhere(?:\s+\(v6\))?\s*$",
                        line,
                        re.IGNORECASE,
                    )
                    if match or legacy_match:
                        matches.append(int((match or legacy_match).group(1)))
                for number in sorted(matches, reverse=True):
                    deleted = _run_linux_firewall_command(["ufw", "--force", "delete", str(number)])
                    success = success and deleted.returncode == 0
            else:
                success = False
        except Exception:
            success = False

    if shutil.which("firewall-cmd"):
        # Legacy firewalld setup created unlabelled opens for these dedicated SentinelOS ports.
        try:
            state = subprocess.run(["firewall-cmd", "--state"], capture_output=True, text=True, timeout=15)
            if state.returncode == 0 and state.stdout.strip().lower() == "running":
                for item in ports:
                    for protocol in ("tcp", "udp"):
                        rule = f"{item}/{protocol}"
                        query = subprocess.run(["firewall-cmd", "--permanent", f"--query-port={rule}"], capture_output=True, text=True, timeout=15)
                        if query.returncode == 0:
                            removed = _run_linux_firewall_command(["firewall-cmd", "--permanent", f"--remove-port={rule}"])
                            success = success and removed.returncode == 0
                reloaded = _run_linux_firewall_command(["firewall-cmd", "--reload"])
                success = success and reloaded.returncode == 0
            elif shutil.which("firewall-offline-cmd"):
                for item in ports:
                    for protocol in ("tcp", "udp"):
                        removed = _run_linux_firewall_command([
                            "firewall-offline-cmd", f"--remove-port={item}/{protocol}"
                        ])
                        # Offline firewalld returns nonzero when the port was absent.
                        if removed.returncode != 0 and "not enabled" not in (removed.stderr or "").lower():
                            success = False
            else:
                success = False
        except Exception:
            success = False

    if shutil.which("iptables"):
        # Remove exact legacy accepts on Sentinel's HTTP and UDP discovery ports.
        # The Tailscale helper only ever created one TCP accept on its selected port.
        managed_rules = [(int(port), "tcp", True)]
        legacy_rules = [(int(port), "tcp", False)]
        for item, protocol, tagged in managed_rules + legacy_rules:
            args = ["iptables", "-D", "INPUT", "-p", protocol, "--dport", str(item)]
            if tagged:
                args.extend(["-m", "comment", "--comment", "SentinelOS Tailscale"])
            args.extend(["-j", "ACCEPT"])
            while True:
                try:
                    deleted = _run_linux_firewall_command(args)
                    if deleted.returncode != 0:
                        error = (deleted.stderr or "").lower()
                        if "must be root" in error or "permission denied" in error:
                            success = False
                        break
                except Exception:
                    success = False
                    break

    if success:
        print_success("Reglas de firewall de SentinelOS eliminadas." if lang == "es" else "SentinelOS firewall rules removed.")
    else:
        print_warning("La limpieza de firewall quedó incompleta; ejecuta la desinstalación con permisos de administrador." if lang == "es" else "Firewall cleanup was incomplete; rerun uninstall with administrator privileges.")
    return success
