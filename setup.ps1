# ==============================================================================
# SentinelOS Universal Installer Bootstrap (Windows PowerShell v2.5)
# Auto-Deteccion, Auto-Reparacion de Entornos Virtuales y Despliegue Autonomo
# ==============================================================================
$ErrorActionPreference = "Continue"

# Habilitar codificacion UTF-8 universal en la consola PowerShell
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "       SENTINEL OS - ASISTENTE DE INSTALACION UNIVERSAL" -ForegroundColor Cyan
Write-Host "  Auto-Deteccion de Sistema, Entornos Aislados y Auto-Reparacion" -ForegroundColor DarkCyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $projectRoot) { $projectRoot = Get-Location }
Set-Location $projectRoot

# 1. Deteccion de interprete Python funcional (omitiendo stubs de Windows Store)
$pythonCmd = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    $testPy = & python -c "import sys; print(sys.version_info[0])" 2>$null
    if ($testPy -match "3") {
        $pythonCmd = "python"
    }
}

if (-not $pythonCmd -and (Get-Command py -ErrorAction SilentlyContinue)) {
    $testPy = & py -3 -c "import sys; print(sys.version_info[0])" 2>$null
    if ($testPy -match "3") {
        $pythonCmd = "py -3"
    }
}

# 2. Si no hay Python funcional, auto-instalar Python 3.12 via Winget
if (-not $pythonCmd) {
    Write-Host "[!] Python 3 no detectado o stub inactivo de Windows Store." -ForegroundColor Yellow
    Write-Host "[*] Auto-reparacion: Instalando Python 3.12 via Windows Package Manager (Winget)..." -ForegroundColor Cyan
    try {
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements -e --silent
        # Recargar variable PATH en la sesion actual
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $pythonCmd = "python"
    } catch {
        Write-Host "[ERROR] No se pudo instalar Python automaticamente." -ForegroundColor Red
        Write-Host "Por favor instala Python 3.10+ desde https://python.org marcando 'Add python.exe to PATH'." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "[OK] Interprete Python detectado: $pythonCmd" -ForegroundColor Green

# 3. Auto-Reparacion de Entorno Virtual Aislado (.venv)
$venvDir = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

$needsCreate = $true
if (Test-Path $venvPython) {
    $testPy = & "$venvPython" -c "import sys; print(1)" 2>$null
    if ($testPy -eq "1") {
        $needsCreate = $false
    }
}

if ($needsCreate) {
    Write-Host "[*] Auto-reparacion: Creando entorno virtual aislado (.venv)..." -ForegroundColor Cyan
    Write-Host "    (Garantiza instalacion de librerias sin requerir permisos de Administrador)" -ForegroundColor Gray
    
    # Intento 1: venv estandar
    if ($pythonCmd -eq "py -3") {
        & py -3 -m venv "$venvDir" 2>$null
    } else {
        & python -m venv "$venvDir" 2>$null
    }
    
    # Intento 2: Fallback si ensurepip esta roto/desactivado en Windows 11 (usar --without-pip)
    if (-not (Test-Path $venvPython)) {
        Write-Host "[*] Auto-reparacion: Inicializando entorno seguro con --without-pip..." -ForegroundColor Cyan
        if ($pythonCmd -eq "py -3") {
            & py -3 -m venv --without-pip "$venvDir" 2>$null
        } else {
            & python -m venv --without-pip "$venvDir" 2>$null
        }
    }
}

# 4. Asegurar pip funcional dentro del venv
$localGetPip = Join-Path $projectRoot "installer\get-pip.py"

if (Test-Path $venvPython) {
    Write-Host "[OK] Entorno virtual activo: $venvDir" -ForegroundColor Green
    
    $pipCheck = & "$venvPython" -m pip --version 2>$null
    if (-not $pipCheck) {
        Write-Host "[*] Auto-reparacion: Desplegando gestor pip autonomamente dentro del entorno virtual..." -ForegroundColor Cyan
        if (Test-Path $localGetPip) {
            & "$venvPython" "$localGetPip" --no-setuptools --no-wheel
        } else {
            & "$venvPython" -m ensurepip --upgrade 2>$null
        }
        $pipCheck = & "$venvPython" -m pip --version 2>$null
    }
    
    if (-not $pipCheck) {
        Write-Host "[*] Auto-reparacion: Descargando bootstrap oficial de pip..." -ForegroundColor Cyan
        $tempPip = Join-Path $env:TEMP "sentinel_get_pip.py"
        curl.exe -sSL https://bootstrap.pypa.io/get-pip.py -o "$tempPip" 2>$null
        if (Test-Path $tempPip) {
            & "$venvPython" "$tempPip" --no-setuptools --no-wheel
        }
    }
    
    # Pre-instalar dependencias criticas con ruedas pre-compiladas (--only-binary=:all: para omitir compilador C++)
    Write-Host "[*] Auto-reparacion: Asegurando paquetes criticos (fastapi, uvicorn, psutil, pydantic)..." -ForegroundColor Cyan
    & "$venvPython" -m pip install --prefer-binary --only-binary=:all: --trusted-host pypi.org --trusted-host files.pythonhosted.org fastapi uvicorn aiohttp requests psutil pydantic --quiet
    
    # 5. Ejecutar instalador de SentinelOS dentro del entorno virtual seguro
    $env:PYTHONPATH = $projectRoot
    & "$venvPython" -m installer
} else {
    Write-Host "[!] Aviso: No se pudo aislar en .venv. Continuando con Python del sistema..." -ForegroundColor Yellow
    $sysPipCheck = & $pythonCmd -m pip --version 2>$null
    if (-not $sysPipCheck -and (Test-Path $localGetPip)) {
        Write-Host "[*] Auto-reparacion: Instalando pip en espacio de usuario..." -ForegroundColor Cyan
        & $pythonCmd "$localGetPip" --user --no-setuptools --no-wheel 2>$null
    }
    $env:PYTHONPATH = $projectRoot
    & $pythonCmd -m installer
}
