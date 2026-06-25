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
set WRAPPER_PATH=%SCRIPT_DIR%run_agent.cmd

REM Verificar que agent.py existe
if not exist "%AGENT_PATH%" (
    echo [ERROR] No se encontro agent.py en:
    echo         %AGENT_PATH%
    echo.
    pause
    exit /b 1
)

echo [OK] Encontrado agent.py
echo     %AGENT_PATH%
echo.

REM Buscar la ruta de Python
for /f "delims=" %%i in ('where python.exe 2^>nul') do set PYTHON_PATH=%%i

if not defined PYTHON_PATH (
    echo [ERROR] No se encontro Python en el sistema
    echo.
    echo Por favor:
    echo   1. Descarga Python desde: https://python.org
    echo   2. Durante la instalacion MARCA: "Add Python to PATH"
    echo   3. Reinicia este script
    echo.
    pause
    exit /b 1
)

echo [OK] Encontrado Python:
echo     %PYTHON_PATH%
echo.

REM Verificar permisos de administrador (sin bloquear)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ADVERTENCIA] Este script funciona mejor con permisos de administrador
    echo.
    echo Si ves errores al crear la tarea, ejecuta nuevamente como administrador.
    echo.
    timeout /t 3 /nobreak
)

REM Crear archivo wrapper para ejecutar el agente
echo [INFO] Creando wrapper para ejecutar Python...
(
    echo @echo off
    echo cd /d "%SCRIPT_DIR%"
    echo "%PYTHON_PATH%" "%AGENT_PATH%" 1>> "%SCRIPT_DIR%agent.log" 2^>^&1
) > "%WRAPPER_PATH%"

if not exist "%WRAPPER_PATH%" (
    echo [ERROR] No se pudo crear el archivo wrapper
    echo.
    pause
    exit /b 1
)

echo [OK] Wrapper creado:
echo     %WRAPPER_PATH%
echo.

REM Crear la tarea programada
echo [INFO] Creando tarea programada...
echo.

set TASK_NAME=SMAT_Agent
set TASK_DESCRIPTION=Sistema de Monitoreo Activo de Procesos - Agente Local

REM Eliminar tarea antigua si existe (silenciosamente)
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Obtener usuario actual
for /f "tokens=*" %%A in ('whoami') do set CURRENT_USER=%%A

REM Crear nueva tarea
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%WRAPPER_PATH%\"" ^
    /sc onstart ^
    /ru "%CURRENT_USER%" ^
    /f

if %errorLevel% equ 0 (
    echo.
    echo ============================================
    echo [SUCCESS] INSTALACION EXITOSA!
    echo ============================================
    echo.
    echo La tarea programada "%TASK_NAME%" ha sido creada.
    echo.
    echo Detalles:
    echo   - Nombre de la tarea: %TASK_NAME%
    echo   - Ejecuta: %WRAPPER_PATH%
    echo   - Usuario: %CURRENT_USER%
    echo   - Trigger: Al iniciar el sistema
    echo   - Logs: %SCRIPT_DIR%agent.log
    echo.
    echo El agente SMAT se ejecutara automaticamente cada vez que
    echo enciendas la maquina o reinicies.
    echo.
) else (
    echo.
    echo ============================================
    echo [ERROR] NO SE PUDO CREAR LA TAREA
    echo ============================================
    echo.
    echo Codigo de error: %errorLevel%
    echo.
    echo Posibles soluciones:
    echo.
    echo 1. EJECUTA COMO ADMINISTRADOR:
    echo    - Haz clic derecho en este archivo .bat
    echo    - Selecciona "Ejecutar como administrador"
    echo.
    echo 2. VERIFICA PYTHON:
    echo    - Abre CMD y ejecuta: python --version
    echo    - Si no aparece, reinstala Python con "Add to PATH"
    echo.
    echo 3. CREA LA TAREA MANUALMENTE:
    echo    - Abre "Programador de Tareas"
    echo    - Nueva tarea > General
    echo    - Nombre: SMAT_Agent
    echo    - Activar: Ejecutar con permisos maximos
    echo    - Ir a "Desencadenadores" > Nueva > "Al iniciar"
    echo    - Ir a "Acciones" > Nueva > %WRAPPER_PATH%
    echo.
    pause
    exit /b 1
)

echo.
echo Verifica que la tarea se creo correctamente con:
echo   schtasks /query /tn "SMAT_Agent"
echo.
echo ============================================
echo.
pause
