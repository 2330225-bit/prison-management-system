from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from models.models import Cell

router = APIRouter(prefix="/cells", tags=["Cells"])


class CellOut(BaseModel):
    cell_id: int
    block: str
    capacity: int
    current_count: int
    status: str

    class Config:
        from_attributes = True


class CellCreate(BaseModel):
    block: str
    capacity: int = 4
    current_count: int = 0
    status: str = "vacant"


@router.get("/", response_model=List[CellOut])
def get_cells(db: Session = Depends(get_db)):
    return db.query(Cell).all()


@router.get("/{cell_id}", response_model=CellOut)
def get_cell(cell_id: int, db: Session = Depends(get_db)):
    cell = db.query(Cell).filter(Cell.cell_id == cell_id).first()
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    return cell


@router.post("/", response_model=CellOut, status_code=201)
def create_cell(cell_data: CellCreate, db: Session = Depends(get_db)):
    cell = Cell(**cell_data.model_dump())
    db.add(cell)
    db.commit()
    db.refresh(cell)
    return cell
