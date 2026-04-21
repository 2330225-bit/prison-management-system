from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

from database.db import get_db
from models.models import Inmate, Cell, InmateStat
from utils.logger import log_activity

router = APIRouter(prefix="/inmates", tags=["Inmates"])


class InmateCreate(BaseModel):
    name: str
    age: int
    offense: str
    offense_category: Optional[str] = "Other"
    sentence_years: float
    cell_id: Optional[int] = None
    admission_date: date
    release_date: Optional[date] = None
    status: Optional[str] = "active"
    nationality: Optional[str] = "Unknown"


class InmateOut(BaseModel):
    inmate_id: int
    name: str
    age: int
    offense: str
    offense_category: Optional[str]
    sentence_years: float
    cell_id: Optional[int]
    admission_date: date
    release_date: Optional[date]
    status: str
    nationality: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[InmateOut])
def get_inmates(
    status: Optional[str] = Query(None),
    offense_category: Optional[str] = Query(None),
    cell_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Inmate)
    if status:
        query = query.filter(Inmate.status == status)
    if offense_category:
        query = query.filter(Inmate.offense_category == offense_category)
    if cell_id:
        query = query.filter(Inmate.cell_id == cell_id)
    if search:
        query = query.filter(
            or_(Inmate.name.ilike(f"%{search}%"), Inmate.offense.ilike(f"%{search}%"))
        )
    return query.offset(skip).limit(limit).all()


@router.get("/{inmate_id}", response_model=InmateOut)
def get_inmate(inmate_id: int, db: Session = Depends(get_db)):
    inmate = db.query(Inmate).filter(Inmate.inmate_id == inmate_id).first()
    if not inmate:
        raise HTTPException(status_code=404, detail="Inmate not found")
    return inmate


@router.post("/", response_model=InmateOut, status_code=201)
def create_inmate(inmate_data: InmateCreate, db: Session = Depends(get_db)):
    inmate = Inmate(**inmate_data.model_dump())
    db.add(inmate)
    db.commit()
    db.refresh(inmate)
    if inmate.cell_id:
        cell = db.query(Cell).filter(Cell.cell_id == inmate.cell_id).first()
        if cell:
            cell.current_count += 1
            cell.status = "occupied"
            db.commit()
    log_activity("Inmate Added", f"New inmate: {inmate.name} (ID: {inmate.inmate_id})", "INFO")
    return inmate
