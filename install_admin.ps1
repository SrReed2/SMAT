# Script para ejecutar install_agent_startup.bat con permisos de administrador
# Uso: .\install_admin.ps1

$scriptPath = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$batchFile = Join-Path $scriptPath "install_agent_startup.bat"

# Verificar que el archivo batch existe
if (-not (Test-Path $batchFile)) {
    Write-Host "[ERROR] No se encontro $batchFile" -ForegroundColor Red
    exit 1
}

# Ejecutar con permisos elevados
Write-Host "[INFO] Ejecutando con permisos de administrador..." -ForegroundColor Yellow
Start-Process -FilePath $batchFile -Verb RunAs -Wait

Write-Host "[OK] Instalacion completada" -ForegroundColor Green
