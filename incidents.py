from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from database.db import get_db
from models.models import Incident

router = APIRouter(prefix="/incidents", tags=["Incidents"])


class IncidentCreate(BaseModel):
    inmate_id: int
    staff_id: int
    date: date
    type: str
    severity: Optional[str] = "Low"
    description: Optional[str] = None
    resolved: Optional[str] = "No"


class IncidentOut(BaseModel):
    incident_id: int
    inmate_id: int
    staff_id: int
    date: date
    type: str
    severity: str
    description: Optional[str]
    resolved: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[IncidentOut])
def get_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).all()


@router.post("/", response_model=IncidentOut, status_code=201)
def create_incident(incident_data: IncidentCreate, db: Session = Depends(get_db)):
    incident = Incident(**incident_data.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident
