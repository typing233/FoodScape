from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class EatingRecord(Base):
    __tablename__ = "eating_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    emotion = Column(String(50), nullable=False)
    situation = Column(String(50), nullable=False)
    hunger_level = Column(Integer, nullable=False)
    is_out_of_control = Column(Boolean, nullable=False)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "emotion": self.emotion,
            "situation": self.situation,
            "hunger_level": self.hunger_level,
            "is_out_of_control": self.is_out_of_control,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
