# SMAT - Sistema de Monitoreo Activo de Procesos

SMAT es una solución para monitorear procesos no autorizados en las computadoras de un laboratorio. Consta de un servidor central que recibe los eventos y de agentes instalados en las máquinas cliente que detectan procesos y los envían al servidor.

## Qué hace SMAT
- Recibe datos de procesos desde varias máquinas.
- Registra eventos en una base de datos local (`smat.db`).
- Ofrece una interfaz web para ver, filtrar y autorizar procesos.
- Permite marcar procesos como "whitelist" para que no se consideren no autorizados.

## Estructura del sistema
- `run_server.py`: inicia el servidor central.
- `agent.py`: ejecuta el agente en cada máquina cliente.
- `install_agent_startup.bat`: instala el agente para que se ejecute al iniciar Windows.
- `uninstall_agent_startup.bat`: elimina la instalación de inicio automático.
- `templates/index.html`: interfaz web del servidor.

---

## Requisitos
- Python 3.x
- `pip`
- Dependencias del servidor:
  ```bash
  pip install -r requirements.txt
  ```
- Dependencias del agente:
  ```bash
  pip install psutil requests
  ```

---

## Instalar y ejecutar el servidor
1. En la máquina que actuará como servidor, abre una terminal.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta el servidor:
   ```bash
   python run_server.py
   ```
4. Abre el navegador y visita:
   ```
   http://localhost:8000
   ```

### Comportamiento esperado
- El servidor escucha en `0.0.0.0:8000`.
- Está disponible desde otras máquinas de la misma red.
- Guarda los eventos en `smat.db`.

---

## Configurar los agentes

### Preparar cada máquina cliente
1. Copia `agent.py` a la máquina cliente.
2. Instala las dependencias:
   ```bash
   pip install psutil requests
   ```
3. Obtén la IP del servidor ejecutando en este servidor:
   ```bash
   ipconfig
   ```
   Usa la dirección **IPv4**.

### Ejecutar el agente manualmente
En la máquina cliente, abre una terminal y usa una de estas opciones:

- Opción 1: definir host y puerto del servidor:
  ```bash
  set SMAT_SERVER_HOST=192.168.1.10
  set SMAT_SERVER_PORT=8000
  python agent.py
  ```

- Opción 2: usar URL completa del servidor:
  ```bash
  set SMAT_SERVER_URL=http://192.168.1.10:8000/events/
  python agent.py
  ```

- Opción 3: usar valores por defecto si el servidor está en `192.168.1.10`:
  ```bash
  python agent.py
  ```

### Ejecución recomendada: inicio automático
Para que el agente se ejecute automáticamente en Windows:

1. Abre CMD como administrador.
2. Navega a la carpeta del proyecto:
   ```bash
   cd C:\ruta\a\SMAT
   ```
3. Ejecuta:
   ```bash
   install_agent_startup.bat
   ```

Esto crea una tarea programada llamada `SMAT_Agent` que arranca el agente al iniciar Windows en segundo plano.

Para verificar la tarea:
```bash
schtasks /query /tn SMAT_Agent
```

Para desinstalar el inicio automático:
```bash
cd C:\ruta\a\SMAT
uninstall_agent_startup.bat
```

---

## Whitelist de procesos

### En el servidor
- Abre la interfaz web.
- Localiza un evento no autorizado.
- Haz clic en "Agregar" para autorizar el proceso.
- El proceso se guarda en la base de datos y, en adelante, se considera permitido.

### En el agente
Puedes indicar procesos autorizados antes de iniciar el agente:
```bash
set SMAT_WHITE_LIST=chrome.exe,firefox.exe,code.exe,python.exe
python agent.py
```

---

## Uso de la interfaz web

La web permite:
- Ver todos los eventos.
- Filtrar solo autorizados.
- Ver solo eventos no autorizados.
- Buscar por nombre de proceso, PC o dirección IP.
- Actualizar la lista.
- Agregar procesos a la whitelist.

---

## Variables de entorno

### Servidor
```bash
SMAT_HOST=0.0.0.0      # Host que escucha el servidor
SMAT_PORT=8000         # Puerto del servidor
SMAT_RELOAD=True       # Auto-reload en cambios (opcional)
```

### Agente
```bash
SMAT_SERVER_HOST=192.168.1.10   # IP del servidor
SMAT_SERVER_PORT=8000           # Puerto del servidor
SMAT_SERVER_URL=http://...      # URL completa del servidor
SMAT_BATCH_INTERVAL=5           # Segundos entre escaneos
SMAT_POST_TIMEOUT=5.0           # Timeout para enviar datos
SMAT_WHITE_LIST=proc1,proc2     # Procesos permitidos
```

---

## Solución de problemas

### No se puede conectar al servidor
- Asegúrate de que `run_server.py` esté ejecutándose.
- Revisa la IP del servidor con `ipconfig`.
- Confirma que ambas máquinas estén en la misma red.
- Si es necesario, prueba con el firewall desactivado temporalmente.

### El agente no envía datos
- Verifica que `psutil` y `requests` estén instalados.
- Ejecuta el agente como administrador.
- Revisa la salida del agente para errores.

### No aparecen eventos en la web
- Recarga la página del navegador.
- Presiona "Refrescar" en la interfaz web.
- Revisa la consola del servidor por posibles errores.
