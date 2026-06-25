@echo off
REM Script para desinstalar el agente SMAT
REM Elimina la tarea programada que se ejecutaba al iniciar

setlocal enabledelayedexpansion

echo.
echo ============================================
echo DESINSTALADOR DE AGENTE SMAT
echo ============================================
echo.

REM Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Este script requiere permisos de ADMINISTRADOR
    echo.
    echo Por favor:
    echo 1. Abre CMD como administrador
    echo 2. Navega a esta carpeta
    echo 3. Ejecuta: uninstall_agent_startup.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Ejecutando con permisos de administrador
echo.

set TASK_NAME=SMAT_Agent
set SCRIPT_DIR=%~dp0
set WRAPPER_PATH=%SCRIPT_DIR%run_agent.cmd

REM Verificar si la tarea existe
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] La tarea "%TASK_NAME%" no esta instalada
    echo.
) else (
    echo [INFO] Encontrada tarea "%TASK_NAME%"
    echo.
    echo [INFO] Eliminando tarea programada...
    echo.

    REM Eliminar la tarea
    schtasks /delete /tn "%TASK_NAME%" /f

    if %errorLevel% equ 0 (
        echo [SUCCESS] Tarea programada eliminada exitosamente
        echo.
    ) else (
        echo [ERROR] No se pudo eliminar la tarea programada
        echo.
        pause
        exit /b 1
    )
)

REM Limpiar archivos generados
if exist "%WRAPPER_PATH%" (
    echo [INFO] Limpiando archivos de instalacion...
    del "%WRAPPER_PATH%" >nul 2>&1
    if %errorLevel% equ 0 (
        echo [OK] Archivo wrapper eliminado
    )
)

echo.
echo ============================================
echo DESINSTALACION COMPLETADA
echo ============================================
echo.
echo El agente SMAT NO se ejecutara mas al iniciar.
echo.
pause
