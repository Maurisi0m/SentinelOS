#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector universal de Sistema Operativo y Hardware para SentinelOS.
Reconoce Windows 10/11, Windows Server, Ubuntu, Debian, Arch, Kali, Fedora, macOS y hardware subyacente.
"""
import sys, os, platform, subprocess, shutil

def get_detailed_os():
    system = platform.system()
    arch = platform.machine()
    distro_name = ""
    distro_id = ""
    is_server = False

    if system == "Windows":
        release = platform.release()
        version = platform.version()
        # Detectar si es Windows 11 (build >= 22000) o Windows Server
        build = 0
        try:
            build = int(version.split('.')[2])
        except Exception:
            pass

        if "server" in platform.win32_edition().lower() if hasattr(platform, 'win32_edition') else False:
            distro_name = f"Windows Server ({release})"
            distro_id = "win_server"
            is_server = True
        elif build >= 22000 or release == "11":
            distro_name = "Windows 11"
            distro_id = "win11"
        else:
            distro_name = f"Windows {release}"
            distro_id = "win"

        pkg_manager = "winget" if shutil.which("winget") else "powershell"

    elif system == "Linux":
        pkg_manager = "unknown"
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                lines = f.readlines()
            info = {}
            for l in lines:
                if "=" in l:
                    k, v = l.strip().split("=", 1)
                    info[k] = v.strip('"')

            distro_name = info.get("PRETTY_NAME", "Linux")
            distro_id = info.get("ID", "linux").lower()

            if "ubuntu" in distro_id:
                pkg_manager = "apt"
                is_server = not bool(shutil.which("gnome-shell") or shutil.which("startx"))
            elif "debian" in distro_id or "kali" in distro_id:
                pkg_manager = "apt"
            elif "arch" in distro_id or "manjaro" in distro_id:
                pkg_manager = "pacman"
            elif "fedora" in distro_id or "rhel" in distro_id or "centos" in distro_id:
                pkg_manager = "dnf"
        else:
            distro_name = "Generic Linux"
            distro_id = "linux"

    elif system == "Darwin":
        distro_name = f"macOS ({platform.mac_ver()[0]})"
        distro_id = "macos"
        pkg_manager = "brew" if shutil.which("brew") else "native"
    else:
        distro_name = system
        distro_id = system.lower()
        pkg_manager = "unknown"

    # Detección de CPU y RAM
    cpu_model = platform.processor() or "Desconocido"
    mem_total_gb = 0
    try:
        if system == "Windows":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            mem_total_gb = round(stat.ullTotalPhys / (1024**3), 1)
        elif os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        mem_total_gb = round(kb / (1024**2), 1)
                        break
    except Exception:
        pass

    # Detección de GPU NVIDIA
    has_nvidia = shutil.which("nvidia-smi") is not None

    return {
        "system": system,
        "distro_name": distro_name,
        "distro_id": distro_id,
        "pkg_manager": pkg_manager,
        "arch": arch,
        "is_server": is_server,
        "ram_gb": mem_total_gb,
        "has_nvidia": has_nvidia
    }

if __name__ == "__main__":
    info = get_detailed_os()
    print("Detected OS Info:", info)
