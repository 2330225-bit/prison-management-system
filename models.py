from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base


class Cell(Base):
    __tablename__ = "cells"

    cell_id = Column(Integer, primary_key=True, index=True)
    block = Column(String(10), nullable=False)
    capacity = Column(Integer, default=4)
    current_count = Column(Integer, default=0)
    status = Column(String(20), default="vacant")  # occupied, vacant, maintenance

    inmates = relationship("Inmate", back_populates="cell")


class Inmate(Base):
    __tablename__ = "inmates"

    inmate_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    offense = Column(String(100), nullable=False)
    offense_category = Column(String(50), default="Other")
    sentence_years = Column(Float, nullable=False)
    cell_id = Column(Integer, ForeignKey("cells.cell_id"), nullable=True)
    admission_date = Column(Date, nullable=False)
    release_date = Column(Date, nullable=True)
    status = Column(String(20), default="active")  # active, released, transferred
    nationality = Column(String(50), default="Unknown")
    created_at = Column(DateTime, server_default=func.now())

    cell = relationship("Cell", back_populates="inmates")
    incidents = relationship("Incident", back_populates="inmate")
    stats = relationship("InmateStat", back_populates="inmate")


class Staff(Base):
    __tablename__ = "staff"

    staff_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # Warden, Guard, Medical, Admin
    shift = Column(String(20), default="Day")   # Day, Night, Rotating
    cell_block_assigned = Column(String(10), nullable=True)
    years_of_service = Column(Integer, default=0)
    contact = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    incidents = relationship("Incident", back_populates="staff")


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(Integer, primary_key=True, index=True)
    inmate_id = Column(Integer, ForeignKey("inmates.inmate_id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.staff_id"), nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String(50), nullable=False)        # Fight, Escape Attempt, Medical, etc.
    severity = Column(String(20), default="Low")     # Low, Medium, High, Critical
    description = Column(Text, nullable=True)
    resolved = Column(String(5), default="No")
    created_at = Column(DateTime, server_default=func.now())

    inmate = relationship("Inmate", back_populates="incidents")
    staff = relationship("Staff", back_populates="incidents")


class InmateStat(Base):
    __tablename__ = "inmate_stats"

    stat_id = Column(Integer, primary_key=True, index=True)
    inmate_id = Column(Integer, ForeignKey("inmates.inmate_id"), nullable=False)
    behavior_score = Column(Float, default=50.0)
    rehabilitation_score = Column(Float, default=50.0)
    work_hours = Column(Float, default=0.0)
    date = Column(Date, nullable=False)

    inmate = relationship("Inmate", back_populates="stats")
