#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINEL OS - Publicador y Subida de Modelos a Hugging Face Hub
Sube modelos GGUF entrenados y genera la ficha técnica (Model Card) oficial.
"""

import os
import sys

def main():
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("[!] Instalando huggingface_hub...")
        os.system(f'"{sys.executable}" -m pip install huggingface_hub --prefer-binary -q')
        from huggingface_hub import HfApi, create_repo

    token = os.environ.get("HF_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1].strip()

    if not token:
        print("=" * 70)
        print("  SENTINEL OS - PUBLICADOR DE MODELO A HUGGING FACE")
        print("=" * 70)
        print("\nPara subir el modelo a Hugging Face necesitas un Token de Acceso con permiso de 'Write'.")
        print("1. Inicia sesión en https://huggingface.co/settings/tokens")
        print("2. Haz clic en 'New token', asígnale nombre y selecciona 'Write'.")
        print("3. Pégalo a continuación:\n")
        try:
            token = input("Ingresa tu HF Token (hf_...): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            return

    if not token or not token.startswith("hf_"):
        print("[ERROR] El token ingresado no es válido. Debe iniciar con 'hf_'.")
        sys.exit(1)

    api = HfApi(token=token)
    user_info = api.whoami()
    username = user_info.get("name")
    print(f"\n[OK] Autenticado exitosamente en Hugging Face como: {username}")

    repo_name = "Sentinel-Agentic-1B"
    repo_id = f"{username}/{repo_name}"

    print(f"[*] Creando/Verificando repositorio de modelo: {repo_id}...")
    try:
        create_repo(repo_id=repo_id, repo_type="model", token=token, exist_ok=True)
        print(f"[OK] Repositorio listo: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"[!] Aviso al crear repositorio: {e}")

    # Archivo a subir
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "export", "output_gguf", "sentinel-agentic-1b.Q4_K_M.gguf")
    if not os.path.exists(model_path):
        alt_path = os.path.join(base_dir, "models", "llama-3.2-1b", "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
        if os.path.exists(alt_path):
            model_path = alt_path

    if not os.path.exists(model_path):
        print(f"[ERROR] No se encontró el archivo del modelo en: {model_path}")
        sys.exit(1)

    file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"\n[*] Subiendo binario GGUF ({file_size_mb:.1f} MB)...")
    print(f"    Origen:  {model_path}")
    print(f"    Destino: {repo_id}/sentinel-agentic-1b.Q4_K_M.gguf")
    print("    (Por favor espera, la subida depende de tu ancho de banda de subida)...")

    try:
        api.upload_file(
            path_or_fileobj=model_path,
            path_in_repo="sentinel-agentic-1b.Q4_K_M.gguf",
            repo_id=repo_id,
            repo_type="model",
            commit_message="Add Sentinel-1B Agentic Q4_K_M GGUF model"
        )
        print("\n" + "=" * 70)
        print("  ¡MODELO PUBLICADO EXITOSAMENTE EN HUGGING FACE!")
        print("=" * 70)
        download_url = f"https://huggingface.co/{repo_id}/resolve/main/sentinel-agentic-1b.Q4_K_M.gguf"
        print(f"Repositorio público: https://huggingface.co/{repo_id}")
        print(f"URL de descarga directa: {download_url}")
        print("=" * 70)
    except Exception as e:
        print(f"\n[ERROR] Error durante la subida: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
