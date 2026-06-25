# Script para crear la tarea programada usando PowerShell en lugar de schtasks
# Este método es más flexible y a menudo funciona mejor

$scriptPath = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$agentPath = Join-Path $scriptPath "agent.py"
$wrapperPath = Join-Path $scriptPath "run_agent.cmd"
$pythonPath = (Get-Command python.exe -ErrorAction SilentlyContinue).Source

# Validaciones
if (-not (Test-Path $agentPath)) {
    Write-Host "[ERROR] No se encontro agent.py en: $agentPath" -ForegroundColor Red
    exit 1
}

if (-not $pythonPath) {
    Write-Host "[ERROR] No se encontro Python. Asegúrate de que esté instalado y en el PATH" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Encontrado agent.py: $agentPath" -ForegroundColor Green
Write-Host "[OK] Encontrado Python: $pythonPath" -ForegroundColor Green
Write-Host ""

# Crear archivo wrapper .cmd
Write-Host "[INFO] Creando wrapper para ejecutar Python..." -ForegroundColor Yellow
$wrapperContent = @"
@echo off
cd /d "$scriptPath"
"$pythonPath" "$agentPath" > "$scriptPath\agent.log" 2>&1
"@

Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding ASCII
Write-Host "[OK] Wrapper creado: $wrapperPath" -ForegroundColor Green
Write-Host ""

# Crear la tarea programada usando PowerShell
Write-Host "[INFO] Creando tarea programada..." -ForegroundColor Yellow

$taskName = "SMAT_Agent"
$taskPath = "\SMAT_Agent"

# Eliminar tarea antigua si existe
try {
    Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "[INFO] Tarea anterior eliminada" -ForegroundColor Yellow
} catch {
    # Ignorar si no existe
}

# Crear la acción (ejecutar el wrapper)
$action = New-ScheduledTaskAction -Execute $wrapperPath

# Crear el trigger (al iniciar)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Crear configuración de la tarea
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0

# Crear la tarea
try {
    $task = Register-ScheduledTask -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Sistema de Monitoreo Activo de Procesos - Agente Local" `
        -User $env:USERNAME `
        -Force

    Write-Host ""
    Write-Host "[SUCCESS] ¡Tarea programada creada exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Detalles:" -ForegroundColor Cyan
    Write-Host "  - Nombre: $taskName" -ForegroundColor Cyan
    Write-Host "  - Usuario: $($env:USERNAME)" -ForegroundColor Cyan
    Write-Host "  - Trigger: Al iniciar el sistema" -ForegroundColor Cyan
    Write-Host "  - Acción: $wrapperPath" -ForegroundColor Cyan
    Write-Host "  - Logs: $scriptPath\agent.log" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "El agente se ejecutará automáticamente cada vez que se encienda la máquina." -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERROR] No se pudo crear la tarea programada" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
