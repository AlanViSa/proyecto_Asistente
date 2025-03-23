# Script para configurar la tarea programada de recordatorios
$ErrorActionPreference = "Stop"

# Obtener el directorio actual del script
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath

# Crear directorio de logs si no existe
$logDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir
}

$logFile = Join-Path $logDir "recordatorios.log"
if (-not (Test-Path $logFile)) {
    New-Item -ItemType File -Path $logFile
}

# Configurar la tarea programada
$taskName = "EnviarRecordatoriosCitas"
$pythonPath = Join-Path $projectRoot "venv\Scripts\python.exe"
$scriptPath = Join-Path $projectRoot "app\scripts\enviar_recordatorios.py"

# Crear la acción
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $scriptPath `
    -WorkingDirectory $projectRoot

# Crear el trigger (cada 30 minutos)
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# Configurar las opciones
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Registrar la tarea
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Envía recordatorios automáticos para las citas programadas" `
    -Force

Write-Host "Tarea programada configurada correctamente"
Write-Host "Los logs se guardarán en: $logFile"
Write-Host "Para ver los logs en tiempo real, abra PowerShell y ejecute: Get-Content $logFile -Wait" 