# ==============================================================================
# SentinelOS Universal Installer Bootstrap (Windows PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

# Habilitar codificacion UTF-8 universal en la consola PowerShell
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "[*] Verificando entorno de ejecucion en Windows..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Python no detectado. Instalando via Winget..." -ForegroundColor Yellow
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements -e --silent
}

$env:PYTHONPATH = "."
python -m installer
