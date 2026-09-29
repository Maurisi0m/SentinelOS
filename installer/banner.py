#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Banner y Sistema de Animación Fluida para Terminal.
Provee soporte VT100/ANSI en Windows/Linux y animación del laboratorio STEM y mascota con lentes.
"""
import sys, time, os

# Configurar salida UTF-8 universal para consolas Windows y Linux
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Habilitar soporte VT100 en consola de Windows
if sys.platform == "win32":
    os.system('')
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        h_stdout = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode))
        mode.value |= 0x0004 | 0x0001
        kernel32.SetConsoleMode(h_stdout, mode)
    except Exception:
        pass

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

ASCII_BANNER = f"""{Colors.CYAN}{Colors.BOLD}
  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
{Colors.YELLOW}             O P E R A T I N G   S Y S T E M   ( v 2 . 0 )
{Colors.DIM}          Distributed STEM Lab & Autonomous Systems Core
{Colors.RESET}"""

ANIMATION_FRAMES = [
f"""
       {Colors.CYAN}╭──────────────────────────────────────────────────╮
       │      [ ( •_•) ]            ⚗️   . . .   🧪         │
       │   SENTINEL COGNITIVE CORE                        │
       │   Iniciando sensores de laboratorio STEM...      │
       ╰──────────────────────────────────────────────────╯{Colors.RESET}
""",
f"""
       {Colors.CYAN}╭──────────────────────────────────────────────────╮
       │      [ ( •_•)>⌐■-■ ]       ⚗️ ─── 🧪 ─── 🔬        │
       │   SENTINEL COGNITIVE CORE                        │
       │   Calibrando gafas de laboratorio y tensores...  │
       ╰──────────────────────────────────────────────────╯{Colors.RESET}
""",
f"""
       {Colors.YELLOW}╭──────────────────────────────────────────────────╮
       │      [ ( ⌐■_■ ) ]          ⚡ ═══ 🧠 ═══ ⚡        │
       │   SENTINEL COGNITIVE CORE                        │
       │   Sincronizando bus de cómputo y telemetría...   │
       ╰──────────────────────────────────────────────────╯{Colors.RESET}
""",
f"""
       {Colors.GREEN}╭──────────────────────────────────────────────────╮
       │      [ ( ✧■_■ ) ]  S E N T I N E L   O S         │
       │   STEM LAB OPERATING SYSTEM                      │
       │   ✔ Núcleo Listo  |  ✔ Laboratorio Preparado     │
       ╰──────────────────────────────────────────────────╯{Colors.RESET}
"""
]

def play_intro_animation():
    """Reproduce la animación fluida de bienvenida y limpia la pantalla."""
    try:
        for frame in ANIMATION_FRAMES:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(frame)
            time.sleep(0.35)
        time.sleep(0.2)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(ASCII_BANNER)
    except Exception:
        print(ASCII_BANNER)

def print_header(title: str, step: str = ""):
    print("\n" + f"{Colors.DIM}" + "─" * 70 + f"{Colors.RESET}")
    if step:
        print(f" {Colors.BOLD}{Colors.GREEN}◈ [{step}] {title.upper()}{Colors.RESET}")
    else:
        print(f" {Colors.BOLD}{Colors.CYAN}◈ {title.upper()}{Colors.RESET}")
    print(f"{Colors.DIM}" + "─" * 70 + f"{Colors.RESET}\n")

def print_success(msg: str):
    print(f" {Colors.GREEN}✔{Colors.RESET} {msg}")

def print_warning(msg: str):
    print(f" {Colors.YELLOW}⚠{Colors.RESET} {msg}")

def print_error(msg: str):
    print(f" {Colors.RED}✖{Colors.RESET} {msg}")

def print_info(msg: str):
    print(f" {Colors.CYAN}ℹ{Colors.RESET} {msg}")

def print_step(msg: str):
    print(f" {Colors.BOLD}{Colors.MAGENTA}⚡{Colors.RESET} {msg}")

def print_badge(label: str, value: str, color=Colors.CYAN):
    print(f"  {Colors.BOLD}{label}:{Colors.RESET} {color}{value}{Colors.RESET}")

def print_panel(title: str, lines: list, border_color=Colors.CYAN, title_color=Colors.BOLD + Colors.CYAN):
    width = 72
    print(f"\n{border_color}╭─ {title_color}{title}{border_color} " + "─" * max(0, width - len(title) - 5) + f"╮{Colors.RESET}")
    for line in lines:
        print(f"  {line}")
    print(f"{border_color}╰" + "─" * (width - 1) + f"╯{Colors.RESET}\n")

def print_menu_item(key: str, title: str, desc: str = "", tag: str = "", color=Colors.CYAN):
    tag_str = f" {Colors.DIM}[{tag}]{Colors.RESET}" if tag else ""
    print(f"  {Colors.BOLD}{color}[{key}]{Colors.RESET} {Colors.BOLD}{title}{Colors.RESET}{tag_str}")
    if desc:
        print(f"      {Colors.DIM}{desc}{Colors.RESET}")

def print_prompt(label: str, default: str = "") -> str:
    def_str = f" {Colors.DIM}[{default}]{Colors.RESET}" if default else ""
    return input(f"\n  {Colors.BOLD}{Colors.CYAN}❯{Colors.RESET} {label}{def_str}: ").strip()

