#!/usr/bin/env python3
# -*- coding: utf-8 -*-

TRANSLATIONS = {
    "es": {
        "welcome": "Bienvenido al asistente de instalación de SentinelOS.",
        "subtitle": "Vamos a configurar tu servidor de laboratorio en unos sencillos pasos.",
        "select_lang": "Selecciona el idioma del sistema:",
        "step1": "Selección de Idioma",
        "step2": "Catálogo de Skills & Módulos",
        "step2_desc": "Selecciona los módulos a desplegar (escribe números separados por comas):",
        "step3": "Términos, Responsabilidad Ética y Seguridad",
        "step4": "Conexión Segura con Tailscale (Recomendado)",
        "step5": "Despliegue y Activación de Servicios",
        "terms_text": (
            "DECLARACIÓN DE USO ÉTICO Y RESPONSABILIDAD EN LABORATORIOS:\n"
            "SentinelOS es un sistema operativo cognitivo con capacidades de ejecución\n"
            "de comandos de bajo nivel, análisis perimetral de red y control de hardware.\n"
            "El usuario asume la total responsabilidad de su uso exclusivamente en equipos,\n"
            "redes y laboratorios propios o expresamente autorizados con fines educativos y de investigación."
        ),
        "accept_terms": "¿Aceptas los términos y condiciones de uso? (s/n): ",
        "terms_rejected": "La instalación ha sido cancelada por el usuario.",
        "tailscale_prompt": "¿Deseas configurar Tailscale para acceso remoto seguro y dominio HTTPS único? (S/n): ",
        "tailscale_installing": "Verificando e instalando Tailscale en el sistema...",
        "tailscale_qr_instruction": "Escanea este código QR con la cámara de tu teléfono para iniciar sesión:",
        "tailscale_waiting": "Esperando autorización de Tailscale...",
        "tailscale_success": "¡Conectado exitosamente a Tailscale!",
        "skills_config_header": "CONFIGURACIÓN DE SKILL:",
        "deploying": "Iniciando contenedores Docker y servicios del sistema...",
        "success_title": "¡SENTINEL OS HA SIDO INSTALADO Y CONFIGURADO CON ÉXITO!",
        "step_autostart": "Inicio Automático del Servidor (Boot / Reinicio)",
        "step_autostart_desc": "¿Deseas que SentinelOS se inicie automáticamente al encender el equipo/servidor? (Opcional pero Recomendado) [S/n]: ",
        "access_local": "Acceso Red Local:",
        "access_remote": "Acceso Remoto Tailscale HTTPS:",
        "docs_link": "Documentación y Gestión de Nodos:"
    },
    "en": {
        "welcome": "Welcome to the SentinelOS Setup Wizard.",
        "subtitle": "We will configure your STEM laboratory server in just a few steps.",
        "select_lang": "Select system language:",
        "step1": "Language Selection",
        "step2": "Skills & Modules Catalog",
        "step2_desc": "Select the modules to deploy (type comma-separated numbers):",
        "step3": "Terms, Ethical Responsibility & Security",
        "step4": "Secure Networking with Tailscale (Recommended)",
        "step5": "Deployment & Service Activation",
        "terms_text": (
            "ETHICAL USAGE AND LABORATORY RESPONSIBILITY STATEMENT:\n"
            "SentinelOS is a cognitive operating system with low-level command\n"
            "execution, perimeter network scanning, and hardware control capabilities.\n"
            "The user assumes full responsibility for using this software strictly on\n"
            "hardware, networks, and laboratories owned or explicitly authorized for research/education."
        ),
        "accept_terms": "Do you accept the terms and conditions? (y/n): ",
        "terms_rejected": "Installation cancelled by user.",
        "tailscale_prompt": "Do you want to configure Tailscale for secure remote access and HTTPS domain? (Y/n): ",
        "tailscale_installing": "Verifying and installing Tailscale on the host system...",
        "tailscale_qr_instruction": "Scan this QR code with your mobile camera to authenticate this server:",
        "tailscale_waiting": "Waiting for Tailscale authorization...",
        "tailscale_success": "Successfully authenticated with Tailscale!",
        "skills_config_header": "CONFIGURING SKILL:",
        "deploying": "Starting Docker containers and core system services...",
        "success_title": "SENTINEL OS HAS BEEN SUCCESSFULLY INSTALLED & CONFIGURED!",
        "step_autostart": "Server Autostart (On Boot / Reboot)",
        "step_autostart_desc": "Enable SentinelOS to start automatically on system boot? (Optional but Recommended) [Y/n]: ",
        "access_local": "Local Network URL:",
        "access_remote": "Tailscale HTTPS URL:",
        "docs_link": "Documentation & Node Management:"
    }
}

class I18n:
    def __init__(self, lang="es"):
        self.lang = lang

    def t(self, key: str) -> str:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["es"]).get(key, key)
