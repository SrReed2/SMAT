# SMAT - Sistema de Monitoreo Activo de Procesos
## Guía de Instalación del Agente

---

## 📋 Resumen de cambios realizados

He corregido y mejorado los scripts de instalación. Aquí están los archivos nuevos y modificados:

### ✅ Archivos corregidos/creados:

1. **`install_agent_startup.bat`** - Script principal de instalación (mejorado)
   - Ahora es más tolerante con permisos
   - Mejor manejo de errores
   - Crea un archivo wrapper automáticamente
   - Genera logs en `agent.log`

2. **`EJECUTAR_COMO_ADMIN.bat`** - NUEVO - Forma más fácil de instalar
   - Simplemente haz **doble-click** en este archivo
   - Automáticamente ejecuta el instalador como administrador

3. **`install_powershell.ps1`** - NUEVO - Instalador PowerShell alternativo
   - Usa cmdlets de PowerShell en lugar de `schtasks`
   - Más flexible

4. **`install_admin.ps1`** - NUEVO - Ejecutor PowerShell
   - Abre el instalador batch con permisos elevados

5. **`uninstall_agent_startup.bat`** - Desinstalador (mejorado)
   - Limpia todos los archivos generados

6. **`INSTRUCCIONES_INSTALACION.md`** - NUEVO - Instrucciones completas
   - Guía paso a paso para varias opciones

7. **`run_agent.cmd`** - Se crea automáticamente
   - Wrapper que ejecuta Python sin ventana de consola

---

## 🚀 Cómo instalar ahora (RECOMENDADO)

### **OPCIÓN 1: La más fácil (recomendada)**

1. Busca el archivo `EJECUTAR_COMO_ADMIN.bat` en tu carpeta SMAT
2. Haz **doble-click** en él
3. Si aparece un aviso de UAC (Control de cuentas de usuario), haz **clic en "Sí"**
4. Se abrirá la ventana del instalador automáticamente
5. Presiona cualquier tecla para continuar

---

### **OPCIÓN 2: Manualmente con clic derecho**

1. Busca el archivo `install_agent_startup.bat`
2. Haz **clic derecho** > **"Ejecutar como administrador"**
3. Presiona cualquier tecla para continuar

---

### **OPCIÓN 3: Desde PowerShell como administrador**

1. Abre PowerShell como administrador (Win + X → PowerShell Admin)
2. Ejecuta:
   ```powershell
   cd "C:\Users\djc0n\OneDrive\Desktop\SMAT"
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   .\install_powershell.ps1
   ```

---

## ✅ Verificar la instalación

Una vez instalado, abre PowerShell y ejecuta:

```powershell
Get-ScheduledTask -TaskName "SMAT_Agent" | Select-Object TaskName, State
```

Deberías ver:
```
TaskName    State
--------    -----
SMAT_Agent  Ready
```

---

## 📁 Archivos generados

Después de instalar, se crearán:

- **`run_agent.cmd`** - Script que ejecuta el agente (creado automáticamente)
- **`agent.log`** - Archivo de logs del agente
  - Se actualiza cada vez que el agente se ejecuta
  - **Revísalo si hay problemas**

---

## 🔍 Solucionar problemas

### ❌ Error: "No se pudo crear la tarea programada"

**Soluciones:**

1. **Verifica que tienes permisos de administrador**
   - Usa la OPCIÓN 1 (EJECUTAR_COMO_ADMIN.bat)
   - Esto abre una ventana de administrador automáticamente

2. **Verifica que Python está instalado y en el PATH**
   ```powershell
   python --version
   where python.exe
   ```

3. **Si aún falla, crea la tarea manualmente:**
   - Abre el **Programador de Tareas** (búscalo en Windows)
   - Nueva tarea > General
   - Nombre: `SMAT_Agent`
   - Activar: Ejecutar con permisos más altos
   - Ir a "Desencadenadores" > Nueva > "Al iniciar"
   - Ir a "Acciones" > Nueva > Programa: `C:\Users\djc0n\OneDrive\Desktop\SMAT\run_agent.cmd`

### ❌ Error: "Python no encontrado"

```powershell
# Descarga Python desde: https://python.org
# IMPORTANTE: Al instalar, marca la casilla "Add Python to PATH"
# Después reinicia la computadora
```

### ❌ El agente no se ejecuta al iniciar

1. Verifica que la tarea está habilitada:
   ```powershell
   Get-ScheduledTask -TaskName "SMAT_Agent"
   ```

2. Revisa los logs:
   ```powershell
   Get-Content "C:\Users\djc0n\OneDrive\Desktop\SMAT\agent.log"
   ```

3. Intenta ejecutar el wrapper manualmente:
   ```cmd
   "C:\Users\djc0n\OneDrive\Desktop\SMAT\run_agent.cmd"
   ```

---

## 🗑️ Desinstalar

Si necesitas desinstalar:

1. **Haz clic derecho** en `uninstall_agent_startup.bat`
2. Selecciona **"Ejecutar como administrador"**
3. Presiona cualquier tecla

---

## 📝 Información técnica

### ¿Qué hace el instalador?

1. ✅ Verifica que `agent.py` existe
2. ✅ Busca la ruta de Python
3. ✅ Crea `run_agent.cmd` (wrapper)
4. ✅ Crea una tarea programada en Windows que ejecuta el wrapper
5. ✅ La tarea se dispara al iniciar el sistema

### ¿Dónde está la tarea?

Puedes verla en:
- **Programador de Tareas** > Biblioteca > Raíz > `SMAT_Agent`
- O con: `schtasks /query /tn "SMAT_Agent"`

### ¿Qué hace el agente?

El agente `agent.py`:
- Monitorea procesos que se ejecutan en tu máquina
- Filtra procesos autorizados (whitelist)
- Envía procesos NO autorizados a `http://192.168.1.10:8000/events/`
- Se ejecuta cada 5 segundos (configurable)
- Registra todo en `agent.log`

---

## 🎯 Próximos pasos

1. **Instala usando EJECUTAR_COMO_ADMIN.bat**
2. **Verifica que la tarea se creó**: `schtasks /query /tn "SMAT_Agent"`
3. **Revisa los logs**: `agent.log`
4. **Reinicia la computadora** para probar que se ejecuta automáticamente

---

## ❓ Dudas frecuentes

**P: ¿Necesito ejecutar como administrador cada vez?**
A: No. Solo necesitas permisos de administrador para INSTALAR. Después, la tarea se ejecuta automáticamente.

**P: ¿Se ejecuta en segundo plano?**
A: Sí. El agente se ejecuta sin interfaz gráfica (sin ventana visible).

**P: ¿Cómo desactivo el agente temporalmente?**
A: Abre el Programador de Tareas > Busca SMAT_Agent > Deshabilitar.

**P: ¿Dónde se guardan los logs?**
A: En `C:\Users\djc0n\OneDrive\Desktop\SMAT\agent.log`

---

## 📞 Contacto

Si tienes problemas que no se resuelven:
1. Revisa los logs en `agent.log`
2. Copia el contenido del log
3. Contacta al administrador del sistema

---

**Actualizado:** 2026-06-24  
**Estado:** ✅ Listo para instalar
