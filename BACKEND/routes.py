# BACKEND/routes.py
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Event, Whitelist
import datetime
import asyncio
from .ws_manager import broadcast

router = APIRouter()


class WhitelistItem(BaseModel):
    proceso: str

# Whitelist de procesos autorizados (inicializada desde la BD en main.py)
WHITELIST_PROCESSES = {
    "chrome.exe",
    "firefox.exe",
    "explorer.exe",
    "notepad.exe",
    "code.exe",
    "python.exe"
}

def is_process_authorized(proceso_name):
    """Determina si un proceso está autorizado (debe estar en la whitelist)."""
    return proceso_name.lower() in WHITELIST_PROCESSES


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_fecha(fecha_raw):
    if not fecha_raw:
        return None
    try:
        if isinstance(fecha_raw, str) and fecha_raw.endswith("Z"):
            return datetime.datetime.fromisoformat(fecha_raw.rstrip("Z"))
        return datetime.datetime.fromisoformat(fecha_raw)
    except Exception:
        return None


async def _broadcast_safe(payload):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(broadcast(payload))
        else:
            asyncio.run(broadcast(payload))
    except Exception:
        # No queremos que un fallo en el broadcast rompa la API
        pass


@router.post("/events/")
async def create_event(request: Request, db: Session = Depends(get_db)):
    """
    Recibe un evento (objeto) o una lista de eventos desde el agente.
    Guarda cada evento en la base de datos y lanza un broadcast asíncrono
    con los datos insertados (lista o único objeto según el payload).
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    # Normalizar a lista para procesar de forma uniforme
    items = payload if isinstance(payload, list) else [payload]

    created = []
    for item in items:
        if not isinstance(item, dict):
            continue  # ignorar entradas inválidas en la lista

        proceso = item.get("proceso")
        pid = item.get("pid")

        if not proceso or pid is None:
            # Saltamos el registro inválido; podríamos acumular errores si se desea
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
            # Si el modelo Event tiene la columna 'autorizado', la incluimos; si no, asumimos True
            "autorizado": getattr(nuevo, "autorizado", True)
        }
        created.append(data)

    # Broadcast: si se creó más de un evento enviamos lista, si fue uno enviamos objeto
    if created:
        payload_to_send = created if len(created) > 1 else created[0]
        await _broadcast_safe(payload_to_send)

    if not created:
        raise HTTPException(status_code=400, detail="No se crearon eventos válidos")

    return {"status": "ok", "created": len(created), "items": created}


@router.get("/events/")
def list_events(db: Session = Depends(get_db)):
    """
    Devuelve todos los eventos guardados en la base de datos (más recientes primero).
    Incluye el campo 'autorizado' si existe en el modelo.
    """
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


@router.post("/whitelist/")
def add_to_whitelist(item: WhitelistItem, db: Session = Depends(get_db)):
    """
    Agrega un proceso a la whitelist.
    Espera JSON con formato: {"proceso": "nombre.exe"}
    También actualiza todos los eventos existentes de ese proceso a autorizado=True
    """
    proceso = item.proceso.strip()
    
    if not proceso:
        raise HTTPException(status_code=400, detail="Proceso no proporcionado")
    
    # Verificar si ya existe
    existing = db.query(Whitelist).filter(
        Whitelist.proceso.ilike(proceso)
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail=f"'{proceso}' ya está en whitelist")
    
    # Agregar a BD
    new_entry = Whitelist(proceso=proceso)
    db.add(new_entry)
    
    # Actualizar todos los eventos de ese proceso a autorizado=True
    db.query(Event).filter(
        Event.proceso.ilike(proceso)
    ).update({Event.autorizado: True})
    
    db.commit()
    
    # Agregar al set en memoria
    WHITELIST_PROCESSES.add(proceso.lower())
    
    return {
        "status": "ok",
        "msg": f"Proceso '{proceso}' agregado a whitelist",
        "proceso": proceso
    }
