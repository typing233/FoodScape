from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from . import crud, models, schemas, analysis
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FoodScape - 情绪进食追踪与分析工具",
    description="基于情绪和环境触发器追踪的心理认知辅助工具",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "FoodScape API 运行中", "docs": "/docs"}

@app.post("/api/records/", response_model=schemas.EatingRecordResponse)
def create_record(record: schemas.EatingRecordCreate, db: Session = Depends(get_db)):
    return crud.create_eating_record(db=db, record=record)

@app.get("/api/records/", response_model=List[schemas.EatingRecordResponse])
def read_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    records = crud.get_eating_records(db, skip=skip, limit=limit)
    return records

@app.get("/api/records/{record_id}", response_model=schemas.EatingRecordResponse)
def read_record(record_id: int, db: Session = Depends(get_db)):
    db_record = crud.get_eating_record(db, record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return db_record

@app.put("/api/records/{record_id}", response_model=schemas.EatingRecordResponse)
def update_record(record_id: int, record: schemas.EatingRecordUpdate, db: Session = Depends(get_db)):
    db_record = crud.update_eating_record(db, record_id=record_id, record=record)
    if db_record is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return db_record

@app.delete("/api/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    success = crud.delete_eating_record(db, record_id=record_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "删除成功"}

@app.get("/api/analysis/")
def get_analysis(db: Session = Depends(get_db)):
    return analysis.analyze_associations(db)

@app.get("/api/stats/")
def get_stats(db: Session = Depends(get_db)):
    total = crud.get_total_records_count(db)
    out_of_control = len(crud.get_out_of_control_records(db))
    
    return {
        "total_records": total,
        "out_of_control_count": out_of_control,
        "control_rate": round((total - out_of_control) / total * 100, 1) if total > 0 else 0
    }
