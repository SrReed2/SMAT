from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Event

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/events/")
def get_event(event: dict, db: Session = Depends(get_db)):
    new = Event(proceso=event["proceso"], pid=event["pid"])
    db.add(new)
    db.commit()
    return {"status": "ok"}

@router.get("/alert")
def check_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return [
        {
            "id": event.id,
            "proceso": event.proceso,
            "pid": event.pid,
            "fecha": event.fecha,
        }
        for event in events
    ]