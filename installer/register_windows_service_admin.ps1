param(
    [string]$RootDir = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$RootDir = [System.IO.Path]::GetFullPath($RootDir)
$pythonw = Join-Path $RootDir '.venv\Scripts\pythonw.exe'
$configPath = Join-Path $RootDir 'config\service.json'
$taskName = 'SentinelOS_Service'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Ejecuta este archivo desde PowerShell como administrador.'
}

if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) {
    throw "No existe pythonw del entorno SentinelOS: $pythonw"
}
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "No existe la configuración de SentinelOS: $configPath"
}

$serviceConfig = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
if ($serviceConfig.node_role -eq 'master') {
    $cockpitLauncher = Join-Path $RootDir 'start_sentinel_cockpit.vbs'
    if (-not (Test-Path -LiteralPath $cockpitLauncher -PathType Leaf)) {
        throw "El rol es central pero falta el lanzador de Cockpit: $cockpitLauncher"
    }
}

$action = New-ScheduledTaskAction `
    -Execute $pythonw `
    -Argument '-m installer.background_service --no-open-ui' `
    -WorkingDirectory $RootDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId 'SYSTEM' `
    -LogonType ServiceAccount `
    -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $taskPrincipal `
    -Settings $settings `
    -Description 'SentinelOS HTTP backend supervisor; runs hidden at Windows startup.' `
    -Force | Out-Null

# Hand the manager lock to the SYSTEM task so the current session is supervised too.
$managerProcesses = Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -and
    [System.IO.Path]::GetFullPath($_.ExecutablePath) -ieq [System.IO.Path]::GetFullPath($pythonw) -and
    $_.CommandLine -match '(?i)-m\s+installer\.background_service'
}
foreach ($manager in $managerProcesses) {
    Stop-Process -Id $manager.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-ScheduledTask -TaskName $taskName
$deadline = (Get-Date).AddSeconds(120)
$healthy = $false
do {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:$($serviceConfig.http_port)/api/health" -TimeoutSec 2
        $healthy = $response.status -eq 'ok'
    } catch {
        $healthy = $false
    }
    $task = Get-ScheduledTask -TaskName $taskName
} until ($healthy -and $task.State -eq 'Running' -or (Get-Date) -ge $deadline)

if (-not $healthy -or $task.State -ne 'Running') {
    throw "La tarea $taskName se registró pero no se confirmó el backend saludable bajo SYSTEM. Estado: $($task.State)"
}

Write-Host "Tarea $taskName registrada como SYSTEM al arrancar Windows."
Write-Host "Backend saludable en http://127.0.0.1:$($serviceConfig.http_port)/api/health; estado de tarea: $($task.State)."
if ($serviceConfig.node_role -eq 'master') {
    Write-Host 'Cockpit permanece configurado para abrirse al iniciar sesión en modo central.'
}
