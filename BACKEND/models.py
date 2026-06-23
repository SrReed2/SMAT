# BACKEND/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    proceso = Column(String, index=True, nullable=False)
    pid = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=True)
    pc = Column(String, index=True, nullable=True)
    ip = Column(String, index=True, nullable=True)
    autorizado = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Event id={self.id} proceso={self.proceso} pc={self.pc} ip={self.ip} pid={self.pid} autorizado={self.autorizado}>"


class Whitelist(Base):
    __tablename__ = "whitelist"

    id = Column(Integer, primary_key=True, index=True)
    proceso = Column(String, unique=True, index=True, nullable=False)

    def __repr__(self):
        return f"<Whitelist proceso={self.proceso}>"
