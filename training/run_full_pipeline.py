#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coordinador del Pipeline Completo de Ingeniería de Tensores:
Fase 3 -> Fase 4 -> Fase 5 -> Fase 6 -> Fase 7 -> Fase 8 -> Verificación
"""

import sys
import subprocess
import time

def run_phase(name, script_path):
    print("\n" + "=" * 80)
    print(f"EJECUTANDO: {name}")
    print(f"Script: {script_path}")
    print("=" * 80)
    t0 = time.time()
    res = subprocess.run([sys.executable, "-u", script_path], text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Fallo crítico en {name} (Error {res.returncode})")
    print(f"\n[OK] {name} finalizado con éxito en {time.time() - t0:.2f}s.")

def main():
    print("********************************************************************************")
    print("INICIANDO CADENA DE INGENIERÍA DE TENSORES SENTINEL STEM (PURA PRECISIÓN RAÍZ)")
    print("********************************************************************************")
    t_global = time.time()

    # 1. Fusión DoRA + Task Vector Subtraction
    run_phase("Fase 3: Fusión DoRA y Sustracción Quirúrgica de Ficción", "training/subtract_and_merge_dora.py")

    # 2. MEMIT: Edición de Memoria e Identidad
    run_phase("Fase 4: MEMIT (Massive Editing of Memory)", "training/apply_memit_identity.py")

    # 3. TIES-Merging
    run_phase("Fase 5: TIES-Merging (Poda de Ruido y Fusión Disjunta)", "training/ties_merge_sentinel.py")

    # 4. DPO con TRL
    run_phase("Fase 6: Alineamiento DPO (Direct Preference Optimization)", "training/train_dpo_sentinel_1b.py")

    # 5. RepE: Representation Engineering
    run_phase("Fase 7: Representation Engineering (Dirección Latente STEM)", "training/apply_repe_steering.py")

    # 6. Compilación GGUF Q4_K_M y Despliegue Remoto
    run_phase("Fase 8: GGUF iMatrix + SFTP + Despliegue en Servidor HP", "training/compile_and_deploy_pure_stem.py")

    print("\n" + "*" * 80)
    print(f"PIPELINE COMPLETO FINALIZADO CON ÉXITO TOTAL EN {time.time() - t_global:.2f}s.")
    print("*" * 80)

if __name__ == "__main__":
    main()
