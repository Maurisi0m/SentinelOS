#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from ..banner import Colors, print_info, print_success

class NetSecSkill:
    id = "netsec"
    name_es = "Pentesting & Topología de Red (Auditoría e Inventario LAN)"
    name_en = "Pentesting & Network Topology (LAN Audit & Inventory)"
    desc_es = "Mapeo dinámico de red, escaneo nmap/arp-scan y detección de vulnerabilidades."
    desc_en = "Dynamic topology mapping, nmap/arp-scan audits and vulnerability detection."

    def __init__(self):
        self.subnet = "192.168.1.0/24"
        self.scan_mode = "safe" # safe, aggressive

    def configure_interactive(self, lang="es"):
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- CONFIGURANDO SKILL: Red & Pentesting ---{Colors.RESET}")
        
        prompt_sub = "Rango de subred LAN a monitorear [192.168.1.0/24]: " if lang == "es" else "LAN subnet range to monitor [192.168.1.0/24]: "
        val = input(prompt_sub).strip()
        if val: self.subnet = val

        prompt_mode = "Modo de auditoría (1: Pasivo/Seguro, 2: Activo Exhaustivo) [1]: " if lang == "es" else "Audit mode (1: Passive/Safe, 2: Active Comprehensive) [1]: "
        val = input(prompt_mode).strip()
        self.scan_mode = "aggressive" if val == "2" else "safe"

        os.makedirs("config", exist_ok=True)
        with open("config/netsec.env", "w", encoding="utf-8") as f:
            f.write(f"NETSEC_SUBNET={self.subnet}\n")
            f.write(f"NETSEC_MODE={self.scan_mode}\n")

        print_success("Configuración de Seguridad de Red guardada en config/netsec.env")
