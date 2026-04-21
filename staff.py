from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from models.models import Staff
from utils.logger import log_activity

router = APIRouter(prefix="/staff", tags=["Staff"])


class StaffCreate(BaseModel):
    name: str
    role: str
    shift: Optional[str] = "Day"
    cell_block_assigned: Optional[str] = None
    years_of_service: Optional[int] = 0
    contact: Optional[str] = None


class StaffOut(BaseModel):
    staff_id: int
    name: str
    role: str
    shift: str
    cell_block_assigned: Optional[str]
    years_of_service: int
    contact: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[StaffOut])
def get_staff(db: Session = Depends(get_db)):
    return db.query(Staff).all()


@router.get("/{staff_id}", response_model=StaffOut)
def get_staff_member(staff_id: int, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff


@router.post("/", response_model=StaffOut, status_code=201)
def create_staff(staff_data: StaffCreate, db: Session = Depends(get_db)):
    staff = Staff(**staff_data.model_dump())
    db.add(staff)
    db.commit()
    db.refresh(staff)
    log_activity("Staff Added", f"New staff: {staff.name} ({staff.role})", "INFO")
    return staff
