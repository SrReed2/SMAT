# SMAT - Sistema de Monitoreo Activo de Procesos


┌─────────────────────────────────────────────────────────────┐
│            SERVIDOR CENTRAL (Tu máquina)                    │
│                                                             │
│  📡 run_server.py → Escucha en 0.0.0.0:8000                │
│  ✅ Recibe eventos de procesos                             │
│  💾 Almacena en BD (smat.db)                               │
│  🌐 Interfaz web en http://localhost:8000                  │
└────────────────┬────────────────────────────────────────────┘
                 │
        HTTP POST /events/
                 │
    ┌────────────┴────────────┬─────────────┐
    │                         │             │
    ▼                         ▼             ▼
 [PC02]                    [PC03]         [PC04]
 agent.py                  agent.py       agent.py
 Monitorea procesos        Monitorea     Monitorea
 Envía no autorizados      procesos      procesos


## Descripcion
SMAT es un sistema centralizado de monitoreo que permite supervisar procesos no autorizados en maquinas del laboratorio de computacion.

**Componentes:**
- **Servidor Central**: Recibe eventos de procesos desde los agentes
- **Agentes**: Se instalan en cada maquina del laboratorio y envian informacion de procesos

---

## Instalacion del Servidor

### 1. Dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar el servidor
```bash
python run_server.py
```

**Salida esperada:**
```
[SMAT] Iniciando servidor en 0.0.0.0:8000
[SMAT] Los agentes se conectaran a esta maquina en puerto 8000
```

El servidor ahora escucha en **todas las interfaces** (`0.0.0.0`), permitiendo conexiones desde cualquier maquina en la red.

### 3. Acceder a la interfaz web
```
http://localhost:8000
```

---

## Instalacion del Agente (en maquinas del laboratorio)

### 1. Preparar maquina destino
- Copiar `agent.py` a la maquina
- Instalar dependencia: `pip install psutil requests`

### 2. Obtener IP del servidor
En la maquina servidor, ejecuta:
```bash
ipconfig
```
Busca la **IPv4** (ej: `192.168.1.10`)

### 3. Ejecutar el agente MANUALMENTE

#### Opcion 1: Ejecucion manual (para pruebas)
```bash
# Opcion 1: Con variable de entorno
set SMAT_SERVER_HOST=192.168.1.10
python agent.py

# Opcion 2: URL completa
set SMAT_SERVER_URL=http://192.168.1.10:8000/events/
python agent.py

# Opcion 3: Valores por defecto (si el servidor esta en 192.168.1.10)
python agent.py
```

**Salida esperada:**
```
[SMAT] Iniciando monitoreo desde: PC03 (192.168.0.12)
[SMAT] Servidor: http://192.168.1.10:8000/events/
[SMAT] Intervalo de escaneo: 5s
[SMAT] Procesos en whitelist: 9
------------------------------------------------------------
[OK] [15:31:05] HTTP 200 - 3 eventos enviados
```

### 4. Ejecutar el agente AUTOMATICAMENTE al iniciar (RECOMENDADO)

Para que el agente se ejecute automaticamente cuando se encienda la computadora:

#### Paso 1: Instalar el agente como tarea programada
1. Abre CMD como **ADMINISTRADOR**
2. Navega a la carpeta donde esta `agent.py`
3. Ejecuta: `install_agent_startup.bat`

```bash
cd C:\ruta\a\SMAT
install_agent_startup.bat
```

El script hara lo siguiente:
- Creara una tarea programada llamada "SMAT_Agent"
- Se ejecutara automaticamente al iniciar la maquina
- Se ejecutara con permisos SYSTEM (en segundo plano)
- No se vera ventana de consola

#### Paso 2: Verificar que esta instalado
Para verificar que la tarea se creo correctamente:
```bash
schtasks /query /tn SMAT_Agent
```

#### Paso 3: Desinstalar (opcional)
Si quieres remover el agente del inicio:
```bash
cd C:\ruta\a\SMAT
uninstall_agent_startup.bat
```

**Ventajas de usar la tarea programada:**
- No requiere intervencion manual
- Se ejecuta automaticamente cada vez que se enciende
- Se ejecuta en background sin interferir
- Persiste despues de reiniciar
- Facil de desinstalar

---

## Configuracion de Whitelist

### En el servidor
**Agregar procesos a whitelist:**
1. En la interfaz web, haz clic en "Agregar" en un proceso no autorizado
2. Se guardara automaticamente en la base de datos
3. Los eventos futuros de ese proceso apareceran como autorizados

### En los agentes
**Personalizar whitelist en cada maquina:**
```bash
set SMAT_WHITE_LIST=chrome.exe,firefox.exe,code.exe,python.exe
python agent.py
```

---

## Uso de la Interfaz Web

### Pestanas de filtros
- **Todos**: Todos los eventos
- **Autorizados**: Solo procesos permitidos
- **No autorizados**: Procesos sospechosos

### Acciones
- **Buscar**: Filtra por PC, proceso o IP
- **Refrescar**: Recarga eventos desde servidor
- **Limpiar cache**: Limpia la lista local del navegador
- **Agregar**: Anade un proceso a la whitelist

---

## Variables de Entorno

### Servidor
```bash
SMAT_HOST=0.0.0.0              # Host a escuchar (default: 0.0.0.0)
SMAT_PORT=8000                 # Puerto (default: 8000)
SMAT_RELOAD=True               # Auto-reload en cambios (default: True)
```

### Agente
```bash
SMAT_SERVER_HOST=192.168.1.10  # Host del servidor
SMAT_SERVER_PORT=8000          # Puerto del servidor
SMAT_SERVER_URL=http://...     # URL completa (alternativa a HOST+PORT)
SMAT_BATCH_INTERVAL=5          # Segundos entre escaneos (default: 5)
SMAT_POST_TIMEOUT=5.0          # Timeout de requests en segundos (default: 5)
SMAT_WHITE_LIST=proc1,proc2    # Lista de procesos autorizados (opcional)
```

---

## Solucion de Problemas

### "No se puede conectar a 192.168.1.10"
- Verifica que el servidor este corriendo: `python run_server.py`
- Verifica la IP del servidor: `ipconfig`
- Verifica que ambas maquinas esten en la misma red
- Desactiva el firewall temporalmente para pruebas

### El agente no envia datos
- Verifica que psutil y requests esten instalados: `pip install psutil requests`
- Ejecuta el agente con permisos de administrador

### Los eventos no aparecen en la web
- Recarga la pagina (F5)
- Haz clic en "Refrescar"
- Revisa la consola del servidor por errores
