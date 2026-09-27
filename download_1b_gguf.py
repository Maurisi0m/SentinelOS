#!/usr/bin/env python3
"""
Descarga Llama-3.2-1B-Instruct en formato GGUF Q4_K_M desde bartowski en HuggingFace.
No requiere token ni aceptar licencia.
Modelo: bartowski/Llama-3.2-1B-Instruct-GGUF
Archivo: Llama-3.2-1B-Instruct-Q4_K_M.gguf (~670 MB)
"""
import urllib.request
import os
import sys
import time

# URL directa de descarga (bartowski es el cuantizador oficial de llama.cpp community)
REPO = "bartowski/Llama-3.2-1B-Instruct-GGUF"
FILENAME = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
URL = f"https://huggingface.co/{REPO}/resolve/main/{FILENAME}"
DEST = os.path.join(os.path.dirname(__file__), "models", "llama-3.2-1b", FILENAME)

def download_with_progress(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    
    # Si ya existe y tiene tamaño razonable, saltar
    if os.path.exists(dest) and os.path.getsize(dest) > 100_000_000:
        print(f"[OK] Ya existe: {dest} ({os.path.getsize(dest)/1024**3:.2f} GB)")
        return

    print(f"[INFO] Descargando: {FILENAME}")
    print(f"[INFO] Desde: {url}")
    print(f"[INFO] Hacia: {dest}")
    print()

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    with urllib.request.urlopen(req) as response:
        total = int(response.getheader("Content-Length", 0))
        downloaded = 0
        chunk = 1024 * 1024  # 1 MB chunks
        t0 = time.time()

        with open(dest, "wb") as f:
            while True:
                data = response.read(chunk)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                elapsed = time.time() - t0
                speed = downloaded / elapsed / 1024**2
                pct = downloaded / total * 100 if total else 0
                done = int(pct / 2)
                bar = "#" * done + "-" * (50 - done)
                sys.stdout.buffer.write(
                    f"\r[{bar}] {pct:.1f}% -- {downloaded/1024**2:.0f}/{total/1024**2:.0f} MB -- {speed:.1f} MB/s".encode("utf-8")
                )
                sys.stdout.buffer.flush()

    print(f"\n\n[DONE] Descarga completada: {os.path.getsize(dest)/1024**3:.3f} GB")
    print(f"[PATH] {dest}")

if __name__ == "__main__":
    download_with_progress(URL, DEST)
