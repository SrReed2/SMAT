# FUNCIONAMIENTO DE SMAT

Este README describe el funcionamiento de cada archivo del proyecto SMAT y su lógica interna. Al leerlo, debes comprender cómo está construido el sistema y cómo recrearlo.

---

## 1. Visión general

SMAT es un sistema de monitoreo distribuido para detectar procesos no autorizados en máquinas cliente y enviarlos a un servidor central.

Componentes:

- `agent.py`: agente que corre en cada máquina cliente, inspecciona procesos y envía eventos al servidor.
- `run_server.py`: arranca el servidor FastAPI.
- `BACKEND/`: carpeta con la lógica del servidor, modelos, rutas y WebSocket.
- `templates/index.html`: interfaz web del servidor.
- `install_agent_startup.bat`: instala el agente como tarea de Windows al iniciar.
- `uninstall_agent_startup.bat`: elimina esa tarea.

---

## 2. Desglose de archivos

- `agent.py`: detecta procesos, filtra whitelist, construye eventos y los envía al servidor.
- `run_server.py`: arranca Uvicorn con la app FastAPI.
- `BACKEND/database.py`: configura SQLite, genera tablas y ajusta columnas faltantes.
- `BACKEND/models.py`: define las tablas `Event` y `Whitelist`.
- `BACKEND/main.py`: inicializa la aplicación FastAPI, carga la whitelist desde la BD y registra rutas.
- `BACKEND/routes.py`: API REST para recibir eventos, listar eventos y manejar whitelist.
- `BACKEND/ws_manager.py`: gestiona conexiones WebSocket y broadcast de eventos.
- `templates/index.html`: UI de monitoreo con filtros, búsqueda y notificaciones.

---

## 3. `agent.py` (agente cliente)

### 3.1 Importaciones y configuración

```python
import psutil
import requests
import time
import socket
import datetime
import os
import sys
```

- `psutil`: recorre procesos del equipo.
- `requests`: envía POST HTTP al servidor.
- `time`: espera entre iteraciones.
- `socket`: obtiene nombre de host e IP local.
- `datetime`: marca la hora de los eventos.
- `os`: lee variables de entorno.
- `sys`: permite terminar el script con códigos de salida.

```python
def get_server_url():
    if "SMAT_SERVER_URL" in os.environ:
        return os.environ["SMAT_SERVER_URL"]
    host = os.getenv("SMAT_SERVER_HOST", "192.168.1.10")
    port = os.getenv("SMAT_SERVER_PORT", "8000")
    return f"http://{host}:{port}/events/"
```

- Intenta leer `SMAT_SERVER_URL` primero.
- Si no existe, arma la URL desde host y puerto.
- Devuelve siempre la URL exacta del endpoint de eventos.

```python
SERVER_URL = get_server_url()
BATCH_INTERVAL = int(os.getenv("SMAT_BATCH_INTERVAL", "5"))
POST_TIMEOUT = float(os.getenv("SMAT_POST_TIMEOUT", "5.0"))
```

- `SERVER_URL`: URL de destino.
- `BATCH_INTERVAL`: segundos entre escaneos.
- `POST_TIMEOUT`: tiempo máximo de espera para el envío.

### 3.2 Whitelist local

```python
WHITE_LIST_ENV = os.getenv("SMAT_WHITE_LIST", None)
if WHITE_LIST_ENV:
    WHITE_LIST = [p.strip() for p in WHITE_LIST_ENV.split(",") if p.strip()]
else:
    WHITE_LIST = [
        "chrome.exe",
        "firefox.exe",
        "explorer.exe",
        "notepad.exe",
        "code.exe",
        "python.exe",
        "java.exe",
        "notepad++.exe",
        "vlc.exe"
    ]
```

- Si existe `SMAT_WHITE_LIST`, divide la cadena por comas y crea la lista.
- Si no, usa una lista por defecto de procesos comunes.
- Esta whitelist previene que se envíen procesos autorizados.

### 3.3 IP local segura

```python
def local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
```

- Intenta obtener IP por nombre de host.
- Si falla, abre un socket UDP a Google sin enviar datos.
- Si sigue fallando, regresa `127.0.0.1`.

### 3.4 Envío de eventos

```python
def send_batch_http(batch):
    if not batch:
        return
    try:
        res = requests.post(SERVER_URL, json=batch, timeout=POST_TIMEOUT)
        status = "OK" if res.status_code == 200 else "WARN"
        print(f"[{status}] [{datetime.datetime.now().strftime('%H:%M:%S')}] HTTP {res.status_code} - {len(batch)} eventos enviados")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] No se puede conectar a {SERVER_URL}")
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] Timeout conectando a {SERVER_URL}")
    except Exception as e:
        print(f"[ERROR] Error al enviar: {type(e).__name__}: {e}")
```

- Si no hay eventos, no hace nada.
- Envía la lista como JSON al servidor.
- Maneja conexión, timeout y errores generales.

### 3.5 Bucle principal de monitoreo

```python
def monitoring():
    hostname = socket.gethostname()
    ip_addr = local_ip()
    while True:
        try:
            batch = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info.get('name') or ""
                    pid = proc.info.get('pid')
                    if not name:
                        continue
                    if name.lower() in (p.lower() for p in WHITE_LIST):
                        continue
                    event = {
                        "proceso": name,
                        "pid": int(pid) if pid is not None else 0,
                        "fecha": datetime.datetime.now().isoformat(),
                        "pc": hostname,
                        "ip": ip_addr
                    }
                    batch.append(event)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if batch:
                send_batch_http(batch)
            time.sleep(BATCH_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] Error en loop de monitoreo: {e}")
            time.sleep(BATCH_INTERVAL)
```

- Recorre procesos usando `psutil.process_iter`.
- Ignora procesos sin nombre.
- Compara el nombre contra la whitelist en minúsculas.
- Construye un diccionario con `proceso`, `pid`, `fecha`, `pc` e `ip`.
- Envía el lote si hay eventos.
- Espera `BATCH_INTERVAL` segundos.
- Captura interrupciones y errores.

### 3.6 Entrada principal

```python
if __name__ == "__main__":
    try:
        monitoring()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        sys.exit(1)
```

- Permite ejecutar el script directamente.
- Finaliza con código de salida apropiado.

---

## 4. `run_server.py` (arranque del servidor)

```python
import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("SMAT_HOST", "0.0.0.0")
    port = int(os.getenv("SMAT_PORT", "8000"))
    reload = os.getenv("SMAT_RELOAD", "True").lower() == "true"
    uvicorn.run(
        "BACKEND.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
```

- Lee variables de entorno `SMAT_HOST`, `SMAT_PORT` y `SMAT_RELOAD`.
- Ejecuta Uvicorn apuntando a la app FastAPI en `BACKEND.main`.
- `0.0.0.0` recibe conexiones desde cualquier IP.
- `reload=True` recarga el servidor si cambia el código.

---

## 5. `BACKEND/database.py` (configuración de BD)

### 5.1 Rutas y URL

```python
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT_DIR / "smat.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
```

- Calcula la ruta raíz del proyecto.
- Define la ubicación por defecto del archivo SQLite.
- Permite sobreescribir con `DATABASE_URL`.

### 5.2 Normalización de la URL

```python
if not DATABASE_URL.startswith("sqlite://"):
    candidate = Path(DATABASE_URL)
    if not candidate.is_absolute():
        candidate = (ROOT_DIR / candidate).resolve()
    DATABASE_URL = f"sqlite:///{candidate}"
```

- Si la URL no es un esquema SQLite, la convierte en ruta válida.
- Soporta rutas relativas.

### 5.3 Engine y sesión

```python
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

- Crea la conexión a la base de datos.
- `check_same_thread=False` es necesario para SQLite en aplicaciones multihilo.
- `SessionLocal` administra sesiones.

### 5.4 Ajuste de columnas

```python
def ensure_event_columns():
    if not DATABASE_URL.startswith("sqlite://"):
        return
    with engine.connect() as conn:
        res = conn.exec_driver_sql("PRAGMA table_info('events')")
        cols = [row[1] for row in res.all()]
        if 'pc' not in cols:
            conn.exec_driver_sql("ALTER TABLE events ADD COLUMN pc TEXT")
        if 'ip' not in cols:
            conn.exec_driver_sql("ALTER TABLE events ADD COLUMN ip TEXT")
        if 'fecha' not in cols:
            conn.exec_driver_sql("ALTER TABLE events ADD COLUMN fecha TEXT")
```

- Garantiza que la tabla `events` tenga columnas `pc`, `ip` y `fecha`.
- No altera datos existentes.

```python
def ensure_autorizado_column():
    if not DATABASE_URL.startswith("sqlite://"):
        return
    with engine.connect() as conn:
        res = conn.exec_driver_sql("PRAGMA table_info('events')")
        cols = [row[1] for row in res.all()]
        if 'autorizado' not in cols:
            conn.exec_driver_sql("ALTER TABLE events ADD COLUMN autorizado INTEGER")
            conn.exec_driver_sql("UPDATE events SET autorizado = 1 WHERE autorizado IS NULL")
```

- Agrega la columna `autorizado` si falta.
- Asegura que los registros antiguos no queden con valor `NULL`.

---

## 6. `BACKEND/models.py` (modelos SQLAlchemy)

### 6.1 Modelo `Event`

```python
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    proceso = Column(String, index=True, nullable=False)
    pid = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=True)
    pc = Column(String, index=True, nullable=True)
    ip = Column(String, index=True, nullable=True)
    autorizado = Column(Boolean, default=True, nullable=False)
```

- `id`: identificador único.
- `proceso`: nombre del ejecutable.
- `pid`: identificador del proceso.
- `fecha`: instante del evento.
- `pc`: nombre del equipo.
- `ip`: dirección IP del equipo.
- `autorizado`: si el proceso está en whitelist.

### 6.2 Modelo `Whitelist`

```python
class Whitelist(Base):
    __tablename__ = "whitelist"
    id = Column(Integer, primary_key=True, index=True)
    proceso = Column(String, unique=True, index=True, nullable=False)
```

- Guarda procesos autorizados persistentemente.
- `proceso` es único para evitar duplicados.

---

## 7. `BACKEND/main.py` (startup del servidor)

### 7.1 Creación de tablas

```python
Base.metadata.create_all(bind=engine)
```

- Crea las tablas `events` y `whitelist` si no existen.

### 7.2 Carga de whitelist

```python
def load_whitelist_from_db():
    db = SessionLocal()
    try:
        whitelist_entries = db.query(Whitelist).all()
        for entry in whitelist_entries:
            WHITELIST_PROCESSES.add(entry.proceso.lower())
    finally:
        db.close()
load_whitelist_from_db()
```

- Sincroniza la whitelist almacenada en BD con el conjunto en memoria.
- Esto permite que el servidor use lista autorizada en tiempo real.

### 7.3 Enrutamiento y plantillas

```python
app.include_router(router)
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
```

- Incluye las rutas definidas en `routes.py`.
- Configura la carpeta de plantillas.

### 7.4 Ruta raíz

```python
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = SessionLocal()
    try:
        events = db.query(Event).order_by(Event.id.desc()).all()
    finally:
        db.close()
    return templates.TemplateResponse("index.html", {"request": request, "events": events})
```

- Devuelve la página principal con todos los eventos.
- Ordena del más reciente al más antiguo.

### 7.5 WebSocket de actualización en tiempo real

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await register(websocket)
    try:
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                await asyncio.sleep(0.1)
    finally:
        await unregister(websocket)
```

- Acepta conexiones WebSocket.
- Registra la conexión.
- Mantiene el canal abierto hasta la desconexión.
- Desregistra la conexión al cerrar.

---

## 8. `BACKEND/routes.py` (API REST)

### 8.1 Esquema de whitelist

```python
class WhitelistItem(BaseModel):
    proceso: str
```

- Valida peticiones con `proceso`.

### 8.2 Conjunto de procesos autorizados

```python
WHITELIST_PROCESSES = {
    "chrome.exe",
    "firefox.exe",
    "explorer.exe",
    "notepad.exe",
    "code.exe",
    "python.exe"
}
```

- Lista inicial en memoria.
- Se completa con valores de la base de datos al iniciar.

### 8.3 Registro de sesiones

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- Permite inyectar sesiones de BD en rutas FastAPI.
- Cierra sesión automáticamente.

### 8.4 Parseo de fechas

```python
def _parse_fecha(fecha_raw):
    if not fecha_raw:
        return None
    try:
        if isinstance(fecha_raw, str) and fecha_raw.endswith("Z"):
            return datetime.datetime.fromisoformat(fecha_raw.rstrip("Z"))
        return datetime.datetime.fromisoformat(fecha_raw)
    except Exception:
        return None
```

- Convierte la fecha ISO enviada por el agente a `datetime`.
- Soporta sufijo `Z`.

### 8.5 Broadcast seguro

```python
async def _broadcast_safe(payload):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(broadcast(payload))
        else:
            asyncio.run(broadcast(payload))
    except Exception:
        pass
```

- Envía eventos a los clientes WebSocket sin bloquear la ruta.
- Silencia fallos de broadcast.

### 8.6 Endpoint `/events/` POST

```python
@router.post("/events/")
async def create_event(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    items = payload if isinstance(payload, list) else [payload]
    created = []
    for item in items:
        if not isinstance(item, dict):
            continue
        proceso = item.get("proceso")
        pid = item.get("pid")
        if not proceso or pid is None:
            continue
        fecha_val = _parse_fecha(item.get("fecha"))
        nuevo = Event(
            proceso=proceso,
            pid=int(pid),
            pc=item.get("pc"),
            ip=item.get("ip"),
            fecha=fecha_val,
            autorizado=is_process_authorized(proceso)
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        data = {
            "id": nuevo.id,
            "pc": nuevo.pc,
            "ip": nuevo.ip,
            "proceso": nuevo.proceso,
            "pid": nuevo.pid,
            "fecha": nuevo.fecha.isoformat() if nuevo.fecha else None,
            "autorizado": getattr(nuevo, "autorizado", True)
        }
        created.append(data)
    if created:
        payload_to_send = created if len(created) > 1 else created[0]
        await _broadcast_safe(payload_to_send)
    if not created:
        raise HTTPException(status_code=400, detail="No se crearon eventos válidos")
    return {"status": "ok", "created": len(created), "items": created}
```

- Acepta lista o un objeto único.
- Valida `proceso` y `pid`.
- Guarda cada evento en BD.
- Asigna `autorizado` según la whitelist.
- Notifica a los clientes WebSocket.
- Responde con recuento de eventos creados.

### 8.7 Endpoint `/events/` GET

```python
@router.get("/events/")
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.id.desc()).all()
    return [
        {
            "id": event.id,
            "proceso": event.proceso,
            "pid": event.pid,
            "fecha": event.fecha.isoformat() if event.fecha else None,
            "pc": event.pc,
            "ip": event.ip,
            "autorizado": getattr(event, "autorizado", True)
        }
        for event in events
    ]
```

- Devuelve todos los eventos guardados.
- Orden descendente por `id`.
- Incluye campo `autorizado`.

### 8.8 Endpoint `/whitelist/` POST

```python
@router.post("/whitelist/")
def add_to_whitelist(item: WhitelistItem, db: Session = Depends(get_db)):
    proceso = item.proceso.strip()
    if not proceso:
        raise HTTPException(status_code=400, detail="Proceso no proporcionado")
    existing = db.query(Whitelist).filter(Whitelist.proceso.ilike(proceso)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"'{proceso}' ya está en whitelist")
    new_entry = Whitelist(proceso=proceso)
    db.add(new_entry)
    db.query(Event).filter(Event.proceso.ilike(proceso)).update({Event.autorizado: True})
    db.commit()
    WHITELIST_PROCESSES.add(proceso.lower())
    return {"status": "ok", "msg": f"Proceso '{proceso}' agregado a whitelist", "proceso": proceso}
```

- Añade un proceso a la whitelist persistida.
- Evita duplicados.
- Marca eventos antiguos de ese proceso como autorizados.
- Actualiza la whitelist en memoria.

---

## 9. `BACKEND/ws_manager.py` (broadcast WebSocket)

```python
import asyncio
import json
from typing import Set
from fastapi import WebSocket

_connections: Set[WebSocket] = set()
_connections_lock = asyncio.Lock()
```

- Lleva un conjunto de conexiones activas.
- Protege el acceso con un lock asíncrono.

```python
async def register(ws: WebSocket):
    async with _connections_lock:
        _connections.add(ws)

async def unregister(ws: WebSocket):
    async with _connections_lock:
        if ws in _connections:
            _connections.remove(ws)
```

- Añade o quita conexiones.

```python
async def broadcast(event: dict):
    text = json.dumps(event)
    to_remove = []
    async with _connections_lock:
        conns = list(_connections)
    for conn in conns:
        try:
            await conn.send_text(text)
        except Exception:
            to_remove.append(conn)
    if to_remove:
        async with _connections_lock:
            for c in to_remove:
                if c in _connections:
                    _connections.remove(c)
```

- Recorre conexiones activas y envía el evento.
- Si una conexión falla, se elimina.

---

## 10. `templates/index.html` (UI)

### 10.1 Estructura HTML

- Barra de navegación con nombre y estado WebSocket.
- Controles de filtro: todos, autorizados, no autorizados.
- Campo de búsqueda por PC, proceso o IP.
- Botones de refresco y limpiar cache.
- Tabla de eventos con columnas `ID`, `PC`, `IP`, `Proceso`, `PID`, `Fecha`, `Estado`.
- Modal para agregar a whitelist.
- Contenedor de toasts para mensajes.

### 10.2 Lógica JavaScript

- `fetchEvents()`: obtiene eventos de `/events/`.
- `setupWebSocket()`: abre conexión a `/ws`.
- `handleIncomingEvent(d)`: agrega eventos nuevos al caché y la tabla.
- `renderFromCache()`: aplica filtro y búsqueda.
- `createRowElement(d)`: construye la fila de tabla.
- `openWhitelistModal(proceso)`: muestra el modal para autorizar un proceso.
- `whitelistConfirmBtn`: envía POST a `/whitelist/` para autorizar un proceso.
- La UI actualiza `rowsCache` y vuelve a renderizar.

### 10.3 Flujo de la UI

1. La página carga y solicita eventos al servidor.
2. Muestra eventos existentes.
3. Conecta WebSocket para recibir actualizaciones en tiempo real.
4. Cuando llega un nuevo evento, se agrega inmediatamente.
5. Si el usuario agrega un proceso a whitelist, la tabla se refresca en memoria.

---

## 11. `install_agent_startup.bat` y `uninstall_agent_startup.bat`

### 11.1 `install_agent_startup.bat`

- Verifica que `agent.py` exista en la misma carpeta.
- Requiere ejecutarse como administrador.
- Elimina tareas antiguas llamadas `SMAT_Agent`.
- Crea una tarea programada para ejecutar `python "<ruta>\agent.py"` al iniciar Windows con usuario SYSTEM.
- Informa éxito o error.

### 11.2 `uninstall_agent_startup.bat`

- Requiere administrador.
- Comprueba si la tarea `SMAT_Agent` existe.
- Si existe, la elimina con `schtasks /delete /f`.
- Informa el resultado.

---

## 12. Flujo completo de ejecución

1. Inicia el servidor con `python run_server.py`.
2. El servidor levanta FastAPI y crea la base de datos `smat.db`.
3. Cada agente ejecuta `agent.py` y comienza a escanear procesos.
4. El agente ignora procesos en su whitelist local.
5. Procesos no autorizados se agrupan y se envían a `/events/`.
6. El servidor guarda cada evento en la tabla `events`.
7. Si un proceso está en la whitelist del servidor, se marca `autorizado`.
8. El servidor transmite el evento a clientes WebSocket.
9. La UI muestra eventos y permite agregar procesos a la whitelist.
10. Agregar un proceso a whitelist actualiza la base de datos y eventos previos.

---

## 13. Variables de entorno importantes

- `SMAT_SERVER_URL`: URL completa del servidor para el agente.
- `SMAT_SERVER_HOST`: host del servidor para el agente.
- `SMAT_SERVER_PORT`: puerto del servidor para el agente.
- `SMAT_BATCH_INTERVAL`: segundos entre escaneos del agente.
- `SMAT_POST_TIMEOUT`: timeout de HTTP del agente.
- `SMAT_WHITE_LIST`: lista de procesos autorizados del agente.
- `SMAT_HOST`: host donde escucha el servidor.
- `SMAT_PORT`: puerto donde escucha el servidor.
- `SMAT_RELOAD`: recarga automática del servidor.
- `DATABASE_URL`: URL de conexión de la base de datos.

---

## 14. Cómo recrear el programa sin ayuda

1. Crear `agent.py` con lecturas de procesos y envíos HTTP.
2. Construir la lógica de whitelist y el bucle de envío.
3. Crear `run_server.py` para arrancar Uvicorn.
4. Configurar `BACKEND/database.py` con SQLite y migraciones ligeras.
5. Definir modelos `Event` y `Whitelist`.
6. Crear rutas para recibir eventos, listar eventos y autorizar procesos.
7. Crear el gestor WebSocket para broadcasting.
8. Crear la UI en `templates/index.html`.
9. Añadir los scripts `.bat` para iniciar/desinstalar el agente.
10. Probar el flujo completo: agente → servidor → UI.

---

## 15. Resumen final

- `agent.py` detecta y reporta procesos no autorizados.
- `run_server.py` inicia el servidor FastAPI.
- `BACKEND/` contiene la capa de persistencia y la API.
- `templates/index.html` es la interfaz de monitoreo.
- El sistema se basa en SQLite, HTTP y WebSocket.
- Todo el flujo está documentado para permitir reconstrucción completa.
