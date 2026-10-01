#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from ..banner import Colors, print_info, print_success

class VoiceSkill:
    id = "voice"
    name_es = "Voice Core & Alexa Bridge (Voz Local + Domótica)"
    name_en = "Voice Core & Alexa Bridge (Local Voice + Smart Home)"
    desc_es = "Reconocimiento de voz local con Whisper, síntesis Piper-TTS y puente Alexa."
    desc_en = "Local speech recognition via Whisper, Piper-TTS synthesis and Alexa bridge."

    def __init__(self):
        self.tts_voice = "es_ES-davefx-medium"
        self.enable_alexa = True
        self.wake_word = "sentinel"

    def configure_interactive(self, lang="es"):
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- CONFIGURANDO SKILL: Voice Core & Alexa ---{Colors.RESET}")
        
        prompt_wake = "Palabra de activación (Wake Word) [sentinel]: " if lang == "es" else "Wake word [sentinel]: "
        val = input(prompt_wake).strip().lower()
        if val: self.wake_word = val

        prompt_alexa = "¿Habilitar emulador de puente para control por Alexa? (S/n): " if lang == "es" else "Enable bridge emulator for Alexa integration? (Y/n): "
        val = input(prompt_alexa).strip().lower()
        self.enable_alexa = (val != 'n')

        os.makedirs("config", exist_ok=True)
        with open("config/voice.env", "w", encoding="utf-8") as f:
            f.write(f"VOICE_WAKE_WORD={self.wake_word}\n")
            f.write(f"VOICE_TTS_MODEL={self.tts_voice}\n")
            f.write(f"VOICE_ALEXA_BRIDGE={str(self.enable_alexa).lower()}\n")

        print_success("Configuración de Voice Core guardada en config/voice.env")
