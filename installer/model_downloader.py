#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Gestor de Descarga de Modelos Cognitivos (v2.0)
Descarga modelos GGUF optimizados desde Hugging Face / CDN con reanudación
automática de descargas interrumpidas y barra de progreso en vivo.
"""

import os
import sys
import time
import urllib.request
import urllib.error

from .banner import Colors, print_info, print_success, print_warning, print_error, print_step

DEFAULT_MODEL_REPO = "Maurisi0m/Sentinel-Agentic-1B"
DEFAULT_MODEL_FILE = "sentinel-agentic-1b.Q4_K_M.gguf"

def download_with_resume(url: str, dest_path: str, lang="es") -> bool:
    """Descarga un archivo con soporte de reanudación HTTP (Range) y visualización de progreso."""
    temp_path = dest_path + ".part"
    headers = {"User-Agent": "SentinelOS-ModelDownloader/2.0"}
    
    existing_bytes = 0
    if os.path.exists(temp_path):
        existing_bytes = os.path.getsize(temp_path)
        if existing_bytes > 0:
            headers["Range"] = f"bytes={existing_bytes}-"
            msg = f"Reanudando descarga desde {existing_bytes / (1024*1024):.1f} MB..." if lang == "es" else f"Resuming download from {existing_bytes / (1024*1024):.1f} MB..."
            print_info(msg)

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_range = resp.headers.get("Content-Range")
            total_bytes = None
            if content_range:
                try:
                    total_bytes = int(content_range.split("/")[-1])
                except Exception:
                    pass
            elif resp.headers.get("Content-Length"):
                try:
                    total_bytes = int(resp.headers.get("Content-Length")) + existing_bytes
                except Exception:
                    pass

            mode = "ab" if existing_bytes > 0 and resp.status == 206 else "wb"
            if mode == "wb":
                existing_bytes = 0

            downloaded = existing_bytes
            start_time = time.time()
            last_print = 0

            with open(temp_path, mode) as f_out:
                chunk_size = 1024 * 512  # 512 KB chunks
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if now - last_print > 0.5:
                        elapsed = now - start_time
                        speed_mb = ((downloaded - existing_bytes) / (1024 * 1024)) / (elapsed if elapsed > 0 else 1)
                        if total_bytes and total_bytes > 0:
                            pct = (downloaded / total_bytes) * 100
                            mb_down = downloaded / (1024 * 1024)
                            mb_tot = total_bytes / (1024 * 1024)
                            bar_len = 28
                            filled = int(bar_len * (downloaded / total_bytes))
                            bar = "=" * filled + "-" * (bar_len - filled)
                            sys.stdout.write(f"\r  [{Colors.CYAN}{bar}{Colors.RESET}] {pct:5.1f}% ({mb_down:.1f}/{mb_tot:.1f} MB) @ {speed_mb:.2f} MB/s ")
                        else:
                            mb_down = downloaded / (1024 * 1024)
                            sys.stdout.write(f"\r  Descargados: {mb_down:.1f} MB @ {speed_mb:.2f} MB/s ")
                        sys.stdout.flush()
                        last_print = now

            sys.stdout.write("\n")
            sys.stdout.flush()

        # Completado exitosamente
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(temp_path, dest_path)
        return True

    except urllib.error.HTTPError as e:
        if e.code == 416: # Range not satisfiable (ya descargado completamente)
            if os.path.exists(temp_path):
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                os.rename(temp_path, dest_path)
                return True
        print_error(f"Error HTTP al descargar: {e}")
        return False
    except Exception as e:
        print_error(f"Error durante la descarga del modelo: {e}")
        return False

def ensure_sentinel_model(root_dir: str, repo_id: str = DEFAULT_MODEL_REPO, filename: str = DEFAULT_MODEL_FILE, lang="es", auto_accept=False) -> str:
    """Verifica si el modelo GGUF existe localmente. Si no, ofrece descargarlo desde Hugging Face."""
    models_dir = os.path.join(root_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    target_path = os.path.join(models_dir, filename)

    if os.path.exists(target_path) and os.path.getsize(target_path) > 100 * 1024 * 1024:
        msg = f"Modelo cognitivo detectado: {filename} ({os.path.getsize(target_path)/(1024*1024):.1f} MB)" if lang == "es" else f"Cognitive model detected: {filename} ({os.path.getsize(target_path)/(1024*1024):.1f} MB)"
        print_success(msg)
        return target_path

    # URL directa de Hugging Face
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"

    print_step(f"Modelo local '{filename}' no encontrado en models/." if lang == "es" else f"Local model '{filename}' not found in models/.")
    if not auto_accept:
        prompt_txt = f"¿Deseas descargar el modelo cognitivo agéntico Sentinel-1B (~770 MB) desde Hugging Face? [S/n]: " if lang == "es" else f"Do you want to download the Sentinel-1B agentic model (~770 MB) from Hugging Face? [Y/n]: "
        try:
            choice = input(prompt_txt).strip().lower()
            if choice == "n":
                print_info("Descarga omitida. El sistema puede conectarse a un servidor remoto o usar APIs cloud." if lang == "es" else "Download skipped. System can connect to a remote server or use cloud APIs.")
                return ""
        except (KeyboardInterrupt, EOFError):
            return ""

    print_step(f"Iniciando descarga de {filename} desde Hugging Face..." if lang == "es" else f"Starting download of {filename} from Hugging Face...")
    print_info(f"URL: {url}")
    
    ok = download_with_resume(url, target_path, lang=lang)
    if ok and os.path.exists(target_path):
        size_mb = os.path.getsize(target_path) / (1024 * 1024)
        print_success(f"Modelo cognitivo descargado e instalado exitosamente ({size_mb:.1f} MB)." if lang == "es" else f"Cognitive model downloaded and installed successfully ({size_mb:.1f} MB).")
        return target_path
    else:
        print_warning("No se pudo completar la descarga del modelo. Puedes descargarlo manualmente más tarde." if lang == "es" else "Model download could not be completed. You can download it manually later.")
        return ""
