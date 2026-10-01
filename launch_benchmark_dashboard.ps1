# SENTINEL - Lanzador del Centro de Control & Dashboard de Benchmarking
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SENTINEL // STEM Cognitive OS - Centro de Control MLOps" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Iniciando servidor web en http://localhost:8501..." -ForegroundColor Green
Write-Host "Presiona Ctrl + C para detener el servidor.`n" -ForegroundColor Yellow

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Entorno virtual no encontrado en .\.venv"
    exit 1
}

& $python benchmark\server.py
