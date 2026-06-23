from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    proceso = Column(String, index=True)
    pid = Column(Integer)
    fecha = Column(DateTime, default=datetime.utcnow)
    