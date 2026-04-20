from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

def get_eating_record(db: Session, record_id: int):
    return db.query(models.EatingRecord).filter(models.EatingRecord.id == record_id).first()

def get_eating_records(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.EatingRecord).order_by(models.EatingRecord.timestamp.desc()).offset(skip).limit(limit).all()

def create_eating_record(db: Session, record: schemas.EatingRecordCreate):
    db_record = models.EatingRecord(
        emotion=record.emotion,
        situation=record.situation,
        hunger_level=record.hunger_level,
        is_out_of_control=record.is_out_of_control,
        notes=record.notes
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def update_eating_record(db: Session, record_id: int, record: schemas.EatingRecordUpdate):
    db_record = get_eating_record(db, record_id)
    if db_record:
        update_data = record.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_record, key, value)
        db.commit()
        db.refresh(db_record)
    return db_record

def delete_eating_record(db: Session, record_id: int):
    db_record = get_eating_record(db, record_id)
    if db_record:
        db.delete(db_record)
        db.commit()
        return True
    return False

def get_out_of_control_records(db: Session):
    return db.query(models.EatingRecord).filter(models.EatingRecord.is_out_of_control == True).all()

def get_total_records_count(db: Session):
    return db.query(models.EatingRecord).count()
