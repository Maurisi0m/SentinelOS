#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
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

def print_header(title: str, step: str = ""):
    print("\n" + "=" * 70)
    if step:
        print(f"{Colors.BOLD}{Colors.GREEN}[{step}] {title.upper()}{Colors.RESET}")
    else:
        print(f"{Colors.BOLD}{Colors.CYAN}{title.upper()}{Colors.RESET}")
    print("=" * 70 + "\n")

def print_success(msg: str):
    print(f"{Colors.GREEN}✔ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}✖ {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.RESET}")
