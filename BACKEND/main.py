# BACKEND/main.py
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from .database import Base, engine, SessionLocal, ensure_event_columns
from .models import Event, Whitelist
from sqlalchemy.orm import Session
import asyncio
import traceback

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)
try:
    ensure_event_columns()
except Exception:
    pass

app = FastAPI()

# Importar router (relativo) y registrar
try:
    from .routes import router, WHITELIST_PROCESSES
except Exception:
    traceback.print_exc()
    raise

# Cargar whitelist desde la base de datos al iniciar
def load_whitelist_from_db():
    """Carga los procesos de whitelist desde la BD al iniciar."""
    db = SessionLocal()
    try:
        whitelist_entries = db.query(Whitelist).all()
        for entry in whitelist_entries:
            WHITELIST_PROCESSES.add(entry.proceso.lower())
    except Exception as e:
        print(f"Error loading whitelist from DB: {e}")
    finally:
        db.close()

load_whitelist_from_db()

app.include_router(router)

# Plantillas (asume carpeta 'templates' en la raíz del proyecto)
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

from .ws_manager import register, unregister, broadcast

# Mostrar rutas registradas (útil para debug al iniciar)
print("Rutas registradas:")
for r in app.routes:
    try:
        print(r.path, r.methods)
    except Exception:
        pass

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db: Session = SessionLocal()
    try:
        events = db.query(Event).order_by(Event.id.desc()).all()
    finally:
        db.close()
    return templates.TemplateResponse("index.html", {"request": request, "events": events})

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
