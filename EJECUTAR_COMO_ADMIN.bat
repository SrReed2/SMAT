@echo off
REM Script para ejecutar el instalador con permisos de administrador
REM Solo haz doble-click en este archivo

cd /d "%~dp0"

echo Abriendo el instalador como administrador...
echo.

REM Ejecutar el instalador con permisos elevados
powershell -Command "Start-Process '%~dp0install_agent_startup.bat' -Verb RunAs"

echo.
echo La ventana del instalador debería abrirse en segundos.
echo.
pause
