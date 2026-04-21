from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List
from datetime import date, timedelta
import random

from database.db import get_db
from models.models import Inmate, Cell, Staff, Incident, InmateStat
from utils.logger import activity_log

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    total_inmates = db.query(func.count(Inmate.inmate_id)).scalar() or 0
    active_inmates = db.query(func.count(Inmate.inmate_id)).filter(Inmate.status == "active").scalar() or 0
    total_cells = db.query(func.count(Cell.cell_id)).scalar() or 0
    occupied_cells = db.query(func.count(Cell.cell_id)).filter(Cell.status == "occupied").scalar() or 0
    total_staff = db.query(func.count(Staff.staff_id)).scalar() or 0
    total_incidents = db.query(func.count(Incident.incident_id)).scalar() or 0
    capacity = db.query(func.sum(Cell.capacity)).scalar() or 1
    occupancy_rate = round((active_inmates / capacity) * 100, 1)

    return {
        "total_inmates": total_inmates,
        "active_inmates": active_inmates,
        "total_cells": total_cells,
        "occupied_cells": occupied_cells,
        "vacant_cells": total_cells - occupied_cells,
        "total_staff": total_staff,
        "total_incidents": total_incidents,
        "occupancy_rate": occupancy_rate,
        "total_capacity": capacity
    }


@router.get("/offense-stats")
def get_offense_stats(db: Session = Depends(get_db)):
    stats = db.query(
        Inmate.offense_category,
        func.count(Inmate.inmate_id).label("count")
    ).group_by(Inmate.offense_category).all()
    return [{"category": s[0] or "Unknown", "count": s[1]} for s in stats]


@router.get("/population-trend")
def get_population_trend(db: Session = Depends(get_db)):
    today = date.today()
    trend = []
    for i in range(12, 0, -1):
        month_date = today - timedelta(days=30 * i)
        # count inmates admitted before or on this date
        count = db.query(func.count(Inmate.inmate_id)).filter(
            Inmate.admission_date <= month_date
        ).scalar() or 0
        # add some randomness for demo
        base = max(count, 5)
        trend.append({
            "month": month_date.strftime("%b %Y"),
            "count": base + random.randint(-2, 3)
        })
    # current
    current = db.query(func.count(Inmate.inmate_id)).filter(Inmate.status == "active").scalar() or 0
    trend.append({"month": today.strftime("%b %Y"), "count": current})
    return trend


@router.get("/staff-stats")
def get_staff_stats(db: Session = Depends(get_db)):
    stats = db.query(
        Staff.role,
        func.count(Staff.staff_id).label("count")
    ).group_by(Staff.role).all()
    return [{"role": s[0], "count": s[1]} for s in stats]


@router.get("/sentence-distribution")
def get_sentence_distribution(db: Session = Depends(get_db)):
    buckets = [
        ("0-2 yrs", 0, 2),
        ("2-5 yrs", 2, 5),
        ("5-10 yrs", 5, 10),
        ("10-20 yrs", 10, 20),
        ("20+ yrs", 20, 200),
    ]
    result = []
    for label, lo, hi in buckets:
        count = db.query(func.count(Inmate.inmate_id)).filter(
            Inmate.sentence_years >= lo,
            Inmate.sentence_years < hi
        ).scalar() or 0
        result.append({"range": label, "count": count})
    return result


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    stats = db.query(InmateStat, Inmate.name).join(
        Inmate, InmateStat.inmate_id == Inmate.inmate_id
    ).order_by(InmateStat.rehabilitation_score.desc()).limit(10).all()
    return [
        {
            "inmate_id": s[0].inmate_id,
            "name": s[1],
            "rehabilitation_score": round(s[0].rehabilitation_score, 1),
            "behavior_score": round(s[0].behavior_score, 1),
            "work_hours": s[0].work_hours
        }
        for s in stats
    ]


@router.get("/activity-log")
def get_activity_log():
    return list(reversed(activity_log[-50:]))


@router.get("/pipeline-status")
def get_pipeline_status():
    return {
        "status": "healthy",
        "last_run": "2025-01-01 08:00:00",
        "records_processed": 150,
        "records_loaded": 148,
        "errors": 2,
        "stages": [
            {"name": "Extract", "status": "success", "duration_ms": 320},
            {"name": "Transform", "status": "success", "duration_ms": 880},
            {"name": "Load", "status": "success", "duration_ms": 210},
        ]
    }
