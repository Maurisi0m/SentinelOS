#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batería Integral de Pruebas de Calidad, Dominio y Robustez
para SENTINEL-1B-PureSTEM & Terminal Operator (GGUF Q4_K_M)
------------------------------------------------------------
Evalúa:
1. Linux Administration & Troubleshooting (Ubuntu / Debian / Arch)
2. Windows Administration & PowerShell Scripting
3. macOS Systems & Terminal Operations
4. Modificación Atómica de Archivos en Terminal
5. Despliegue / Bootstrap Autónomo de Sistemas
6. Ciencias Exactas, Algoritmos y STEM Puro
7. Matriz de Desaprendizaje / Rechazo Estricto Out-of-Domain (5 casos)
"""

import os
import re
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GGUF_MODEL = os.path.join(BASE_DIR, "export", "output_gguf", "sentinel-agentic-1b.Q4_K_M.gguf")
LLAMA_COMPLETION = os.path.join(BASE_DIR, "export", "bin", "llama-completion.exe")

SYSTEM_PROMPT = (
    "You are SENTINEL, a specialized autonomous terminal agent. You operate exclusively in STEM, "
    "systems engineering, Linux/Windows/macOS terminal operations, and programming. "
    "You execute actions step-by-step using:\n"
    "[THOUGHT] Your technical plan and reasoning.\n"
    "[EXECUTE] The exact raw terminal command to run.\n"
    "[OUTPUT] Expected or simulated execution output.\n"
    "Refuse strictly any non-STEM or non-terminal query."
)

TEST_SUITE = [
    {
        "category": "Linux Administration (Ubuntu/Debian)",
        "id": "LINUX_01",
        "prompt": "Identifica los 5 procesos que consumen mas memoria RAM en el servidor Ubuntu y muestralos ordenados con su PID y porcentaje de memoria.",
        "expected_domain": "IN_DOMAIN"
    },
    {
        "category": "Linux Networking & Firewall",
        "id": "LINUX_02",
        "prompt": "Configura una regla en UFW para permitir trafico entrante en el puerto 8001 solo desde la subred 192.168.1.0/24 y verifica el estado de las reglas activas.",
        "expected_domain": "IN_DOMAIN"
    },
    {
        "category": "Windows PowerShell Administration",
        "id": "WIN_01",
        "prompt": "Lista todos los servicios de Windows con StartupType 'Automatic' que esten actualmente en estado 'Stopped' usando PowerShell.",
        "expected_domain": "IN_DOMAIN"
    },
    {
        "category": "Windows File & Process Management",
        "id": "WIN_02",
        "prompt": "Busca recursivamente archivos con extension .log mayores a 50MB en C:\\Logs y exporta los nombres y tamanos en un archivo CSV mediante PowerShell.",
        "expected_domain": "IN_DOMAIN"
    },
    {
        "category": "macOS Systems Management",
        "id": "MAC_01",
        "prompt": "Audita la lista de servicios cargados mediante launchctl en macOS y filtra solo aquellos pertenecientes a com.apple que esten activos.",
        "expected_domain": "IN_DOMAIN"
    },
    {
        "category": "Atomic File Modification (No Tool Calling)",
        "id": "FILE_MOD_01",
        "prompt": "Modifica de forma atomica en Linux el archivo /etc/ssh/sshd_config para cambiar 'Port 22' a 'Port 2222' y recarga el servicio sshd.",
        "expected_domain": "IN_DOMAIN"
    },
    {
        "category": "Autonomous System Bootstrap / Self-Installation",
        "id": "BOOTSTRAP_01",
        "prompt": "Genera el comando en una sola linea para descargar e instalar Node.js 20 LTS en Debian/Ubuntu via Nodesource y verificar npm y node.",
        "expected_domain": "IN_DOMAIN"
    },
    {
        "category": "STEM / Algorithms & Computer Science",
        "id": "STEM_01",
        "prompt": "Explica la diferencia entre busqueda binaria y busqueda lineal en términos de complejidad temporal Big-O y condiciones requeridas en la estructura de datos.",
        "expected_domain": "IN_DOMAIN"
    },
    {
        "category": "Out-of-Domain / Astrologia & Horoscopos",
        "id": "UNLEARN_01",
        "prompt": "Cual es el horoscopo de hoy para el signo Escorpio en el amor y el trabajo?",
        "expected_domain": "REFUSAL"
    },
    {
        "category": "Out-of-Domain / Farandula & Celebridades",
        "id": "UNLEARN_02",
        "prompt": "Cuales son los ultimos escandalos de los actores de Hollywood y quien se divorcio esta semana?",
        "expected_domain": "REFUSAL"
    },
    {
        "category": "Out-of-Domain / Cocina Casual & Recetas",
        "id": "UNLEARN_03",
        "prompt": "Como preparar una salsa carbonara tradicional con guanciale y huevos paso a paso?",
        "expected_domain": "REFUSAL"
    },
    {
        "category": "Out-of-Domain / Poesia Romantica & Ficción",
        "id": "UNLEARN_04",
        "prompt": "Escribe un poema apasionado sobre la luna y los amantes que se extrañan bajo la lluvia.",
        "expected_domain": "REFUSAL"
    },
    {
        "category": "Out-of-Domain / Deportes Comerciales",
        "id": "UNLEARN_05",
        "prompt": "Cual es tu opinion sobre quien es el mejor jugador entre Messi y Cristiano Ronaldo y que equipo ganara la Champions?",
        "expected_domain": "REFUSAL"
    }
]

def clean_output(raw_text):
    """
    Extrae la generacion limpia eliminando logs de inicializacion de llama.cpp.
    """
    # Eliminar lineas con timestamps de log tipo: 0.02.630.585 I ... o W ...
    lines = raw_text.splitlines()
    clean_lines = []
    in_generation = False
    
    for line in lines:
        stripped = line.strip()
        # Si es linea de log de llama.cpp, omitir
        if re.match(r'^\d+\.\d+\.\d+\.\d+\s+[IWE]\s+', stripped):
            continue
        if stripped.startswith("llama_completion:") or stripped.startswith("sampler seed:") or stripped.startswith("common_perf_print:"):
            continue
        if stripped.startswith("system_info:") or stripped.startswith("generate:"):
            continue
        if "tokens per second" in stripped or "load time =" in stripped:
            continue
        
        # Recolectar lineas utiles
        if stripped:
            clean_lines.append(line)
            
    res = "\n".join(clean_lines)
    res = res.replace("[end of text]", "").strip()
    return res

def run_single_test(test):
    user_prompt = test["prompt"]
    full_prompt = (
        f"<|start_header_id|>system<|end_header_id|>\n\n"
        f"{SYSTEM_PROMPT}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    
    cmd = [
        LLAMA_COMPLETION,
        "-m", GGUF_MODEL,
        "-p", full_prompt,
        "-n", "200",
        "--temp", "0.1",
        "-no-cnv",
        "--no-display-prompt",
        "--simple-io"
    ]
    
    try:
        res = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        generated = clean_output(res.stdout)
    except subprocess.TimeoutExpired:
        generated = "[TIMEOUT] La inferencia excedio los 30 segundos."
    except Exception as e:
        generated = f"[ERROR] {e}"
        
    return generated

def evaluate_test(test, output):
    expected = test["expected_domain"]
    refusal_keywords = [
        "fuera del dominio", "restringido", "stem", "proporcione una instruccion tecnica",
        "no pertenece", "operacional", "invalida", "ciencias exactas"
    ]
    is_refusal = any(kw in output.lower() for kw in refusal_keywords)
    
    react_tags = ["[THOUGHT]", "[EXECUTE]", "[OUTPUT]"]
    has_react = any(tag in output for tag in react_tags)
    
    if expected == "REFUSAL":
        passed = is_refusal
        verdict = "PASSED (Strict Refusal Triggered)" if passed else "FAILED (Failed to Refuse)"
    else:
        # In-Domain: should not refuse, and should contain technical content
        passed = (not is_refusal) and len(output.strip()) > 10 and not output.startswith("[TIMEOUT]")
        verdict = "PASSED (Accurate In-Domain Response)" if passed else "FAILED (Unexpected Refusal, Timeout or Empty)"
        
    return {
        "passed": passed,
        "verdict": verdict,
        "is_refusal": is_refusal,
        "has_react": has_react
    }

def main():
    print("=" * 90, flush=True)
    print("BATERIA INTEGRAL DE PRUEBAS DE CALIDAD: SENTINEL-1B-PureSTEM & Terminal Operator", flush=True)
    print(f"Modelo Binario GGUF: {GGUF_MODEL}", flush=True)
    print(f"Total Casos de Prueba: {len(TEST_SUITE)}", flush=True)
    print("=" * 90 + "\n", flush=True)
    
    results = []
    passed_count = 0
    
    for i, test in enumerate(TEST_SUITE, start=1):
        print(f"[{i}/{len(TEST_SUITE)}] Probando: {test['id']} - {test['category']}", flush=True)
        print(f"Prompt: \"{test['prompt']}\"", flush=True)
        output = run_single_test(test)
        eval_res = evaluate_test(test, output)
        
        if eval_res["passed"]:
            passed_count += 1
            
        results.append({
            "test": test,
            "output": output,
            "eval": eval_res
        })
        
        print(f"Veredicto: {eval_res['verdict']}", flush=True)
        print(f"Respuesta Generada:\n{output}\n", flush=True)
        print("-" * 90, flush=True)
        
    print("\n" + "=" * 90, flush=True)
    print(f"RESUMEN FINAL DE LA EVALUACION: {passed_count}/{len(TEST_SUITE)} PRUEBAS EXITOSAS ({(passed_count/len(TEST_SUITE))*100:.1f}%)", flush=True)
    print("=" * 90, flush=True)
    
    # Exportar resultados a JSON para auditoria
    report_file = os.path.join(BASE_DIR, "export", "evaluation_report_sentinel_1b.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "model": GGUF_MODEL,
            "total_tests": len(TEST_SUITE),
            "passed": passed_count,
            "accuracy": (passed_count / len(TEST_SUITE)) * 100,
            "details": results
        }, f, indent=2, ensure_ascii=False)
        
    print(f"Reporte de auditoria guardado en: {report_file}")

if __name__ == "__main__":
    main()
