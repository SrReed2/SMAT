@echo off
REM Script para instalar el agente SMAT como tarea programada en Windows
REM Se ejecutara automaticamente al iniciar la maquina

setlocal enabledelayedexpansion

echo.
echo ============================================
echo INSTALADOR DE AGENTE SMAT
echo ============================================
echo.

REM Obtener la ruta del script actual
set SCRIPT_DIR=%~dp0
set AGENT_PATH=%SCRIPT_DIR%agent.py

REM Verificar que agent.py existe
if not exist "%AGENT_PATH%" (
    echo [ERROR] No se encontro agent.py en: %AGENT_PATH%
    echo.
    pause
    exit /b 1
)

echo [OK] Encontrado agent.py en: %AGENT_PATH%
echo.

REM Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Este script requiere permisos de ADMINISTRADOR
    echo.
    echo Por favor:
    echo 1. Abre CMD como administrador
    echo 2. Navega a esta carpeta
    echo 3. Ejecuta: install_agent_startup.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Ejecutando con permisos de administrador
echo.

REM Crear la tarea programada
echo [INFO] Creando tarea programada...
echo.

REM Nombre de la tarea
set TASK_NAME=SMAT_Agent
set TASK_DESCRIPTION=Sistema de Monitoreo Activo de Procesos - Agente Local

REM Eliminar tarea antigua si existe
tasklist /fi "IMAGENAME eq python.exe" | find /i "SMAT_Agent" >nul 2>&1
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Crear nueva tarea
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "python \"%AGENT_PATH%\"" ^
    /sc onstart ^
    /ru SYSTEM ^
    /f ^
    /rl highest

if %errorLevel% equ 0 (
    echo.
    echo [SUCCESS] Tarea programada creada exitosamente
    echo.
    echo Detalles:
    echo   - Nombre: %TASK_NAME%
    echo   - Ruta: %AGENT_PATH%
    echo   - Ejecutar: Al iniciar el sistema
    echo   - Usuario: SYSTEM (sin interfaz grafica)
    echo.
    echo El agente se ejecutara automaticamente cada vez que se encienda la maquina.
    echo.
) else (
    echo.
    echo [ERROR] No se pudo crear la tarea programada
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo INSTALACION COMPLETADA
echo ============================================
echo.
pause
