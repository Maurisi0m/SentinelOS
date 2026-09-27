# ==============================================================================
# SentinelOS Universal Installer Bootstrap (Windows PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "[*] Verificando entorno de ejecucion en Windows..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Python no detectado. Instalando via Winget..." -ForegroundColor Yellow
    winget install Python.Python.3.12 -e --silent
}

$env:PYTHONPATH = "."
python -m installer
