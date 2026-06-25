# Instrucciones para instalar el Agente SMAT

## Opción 1: Método manual simple (recomendado)

### Pasos:

1. **Haz clic derecho** en el archivo `install_agent_startup.bat`
2. Selecciona **"Ejecutar como administrador"**
3. Se abrirá una ventana de CMD
4. Presiona cualquier tecla para continuar si todo es correcto

---

## Opción 2: Desde PowerShell como administrador

1. **Abre PowerShell como administrador**:
   - Presiona `Win + X`
   - Selecciona "Windows PowerShell (Admin)" o "Terminal (Admin)"

2. **Navega a la carpeta SMAT**:
   ```powershell
   cd "C:\Users\djc0n\OneDrive\Desktop\SMAT"
   ```

3. **Ejecuta el script PowerShell mejorado**:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   .\install_powershell.ps1
   ```

---

## Opción 3: Desde CMD como administrador

1. **Abre CMD como administrador**:
   - Presiona `Win + R`
   - Escribe `cmd` y presiona Ctrl+Shift+Enter

2. **Navega a la carpeta SMAT**:
   ```cmd
   cd C:\Users\djc0n\OneDrive\Desktop\SMAT
   ```

3. **Ejecuta el instalador**:
   ```cmd
   install_agent_startup.bat
   ```

---

## Verificar que se instaló correctamente

Una vez instalado, verifica que la tarea programada se creó:

```powershell
Get-ScheduledTask -TaskName "SMAT_Agent" | Select-Object TaskName, State
```

Deberías ver algo como:
```
TaskName    State
--------    -----
SMAT_Agent  Ready
```

---

## ¿Qué archivos se crean?

- **run_agent.cmd**: Script wrapper para ejecutar Python
- **agent.log**: Archivo de logs del agente (se actualiza cada vez que se ejecuta)

---

## Para desinstalar

Ejecuta como administrador:
```cmd
uninstall_agent_startup.bat
```

---

## Solución de problemas

### Error: "Access Denied"
- Asegúrate de ejecutar como **Administrador**
- Los archivos deben estar en una carpeta donde tienes permisos de lectura/escritura

### Error: "Python not found"
- Verifica que Python está instalado: `python --version`
- Verifica que Python está en el PATH

### Error: "Ya existe una tarea con ese nombre"
- Ejecuta primero: `uninstall_agent_startup.bat`
- Luego: `install_agent_startup.bat`

---

## Contacto

Si tienes problemas, revisa los logs en: `C:\Users\djc0n\OneDrive\Desktop\SMAT\agent.log`
