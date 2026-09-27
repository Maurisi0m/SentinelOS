#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
from ..banner import Colors, print_info, print_success

class KlipperSkill:
    id = "klipper"
    name_es = "Klipper & Moonraker (Control de Impresión 3D STEM)"
    name_en = "Klipper & Moonraker (3D Printing STEM Control)"
    desc_es = "Telemetría de extrusor, control de motores paso a paso y macros G-Code."
    desc_en = "Extruder telemetry, stepper motor control and G-Code macros."

    def __init__(self):
        self.serial_port = "/dev/ttyUSB0"
        self.baudrate = "250000"
        self.enable_webcam = True

    def configure_interactive(self, lang="es"):
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- CONFIGURANDO SKILL: Klipper & Impresión 3D ---{Colors.RESET}")
        
        default_port = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
        prompt_port = f"Puerto serial de la placa 3D [{default_port}]: " if lang == "es" else f"3D board serial port [{default_port}]: "
        val = input(prompt_port).strip()
        self.serial_port = val if val else default_port

        prompt_baud = "Baudrate de comunicación [250000]: " if lang == "es" else "Communication baudrate [250000]: "
        val = input(prompt_baud).strip()
        if val: self.baudrate = val

        prompt_cam = "¿Habilitar cámara web en vivo para monitoreo? (S/n): " if lang == "es" else "Enable live monitoring webcam? (Y/n): "
        val = input(prompt_cam).strip().lower()
        self.enable_webcam = (val != 'n')

        os.makedirs("config", exist_ok=True)
        with open("config/klipper.env", "w", encoding="utf-8") as f:
            f.write(f"KLIPPER_SERIAL={self.serial_port}\n")
            f.write(f"KLIPPER_BAUDRATE={self.baudrate}\n")
            f.write(f"KLIPPER_WEBCAM={str(self.enable_webcam).lower()}\n")

        print_success("Configuración de Klipper guardada en config/klipper.env")
