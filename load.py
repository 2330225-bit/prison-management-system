"""
ETL Step 3 — Load
Upserts transformed data into PostgreSQL via SQLAlchemy.
"""

import pandas as pd
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.db import SessionLocal, engine, create_tables
from models.models import Inmate, Cell, InmateStat
from utils.logger import get_logger

logger = get_logger("etl.load")


def upsert_inmates(df: pd.DataFrame) -> int:
    """
    UPSERT inmates: insert new rows, update existing by inmate_id.
    Returns number of records processed.
    """
    create_tables()
    db: Session = SessionLocal()
    count = 0

    try:
        for _, row in df.iterrows():
            existing = db.query(Inmate).filter(Inmate.inmate_id == int(row["inmate_id"])).first()

            if existing:
                # Update fields
                existing.name = str(row["name"])
                existing.age = int(row["age"])
                existing.offense = str(row["offense"])
                existing.offense_category = str(row["offense_category"])
                existing.sentence_years = float(row["sentence_years"])
                existing.admission_date = row["admission_date"]
                existing.release_date = row["release_date"]
                existing.status = str(row["status"])
                existing.nationality = str(row["nationality"])
                logger.debug(f"[LOAD] Updated inmate_id={row['inmate_id']}")
            else:
                # Handle cell_id: check if the cell exists, else use None
                cell_id = None
                if pd.notna(row.get("cell_id")):
                    cell = db.query(Cell).filter(Cell.cell_id == int(row["cell_id"])).first()
                    if cell:
                        cell_id = int(row["cell_id"])

                new_inmate = Inmate(
                    inmate_id=int(row["inmate_id"]),
                    name=str(row["name"]),
                    age=int(row["age"]),
                    offense=str(row["offense"]),
                    offense_category=str(row["offense_category"]),
                    sentence_years=float(row["sentence_years"]),
                    cell_id=cell_id,
                    admission_date=row["admission_date"],
                    release_date=row["release_date"],
                    status=str(row["status"]),
                    nationality=str(row["nationality"])
                )
                db.add(new_inmate)
                logger.debug(f"[LOAD] Inserted inmate_id={row['inmate_id']}")

            count += 1

        db.commit()
        logger.info(f"[LOAD] Upserted {count} inmate records.")

    except Exception as e:
        db.rollback()
        logger.error(f"[LOAD] Inmate upsert failed: {e}")
        raise
    finally:
        db.close()

    return count


def upsert_stats(df: pd.DataFrame) -> int:
    """Upsert inmate stats (rehabilitation scores)."""
    db: Session = SessionLocal()
    count = 0
    today = date.today()

    try:
        for _, row in df.iterrows():
            inmate_id = int(row["inmate_id"])
            # Check inmate exists
            inmate = db.query(Inmate).filter(Inmate.inmate_id == inmate_id).first()
            if not inmate:
                continue

            existing_stat = db.query(InmateStat).filter(
                InmateStat.inmate_id == inmate_id,
                InmateStat.date == today
            ).first()

            if existing_stat:
                existing_stat.behavior_score = float(row.get("behavior_score", 50))
                existing_stat.rehabilitation_score = float(row.get("rehabilitation_score", 50))
                existing_stat.work_hours = float(row.get("work_hours", 0))
            else:
                stat = InmateStat(
                    inmate_id=inmate_id,
                    behavior_score=float(row.get("behavior_score", 50)),
                    rehabilitation_score=float(row.get("rehabilitation_score", 50)),
                    work_hours=float(row.get("work_hours", 0)),
                    date=today
                )
                db.add(stat)

            count += 1

        db.commit()
        logger.info(f"[LOAD] Upserted {count} stat records.")

    except Exception as e:
        db.rollback()
        logger.error(f"[LOAD] Stats upsert failed: {e}")
        raise
    finally:
        db.close()

    return count


if __name__ == "__main__":
    from etl.extract import extract_inmates_csv
    from etl.transform import transform
    raw = extract_inmates_csv()
    clean = transform(raw)
    upsert_inmates(clean)
    upsert_stats(clean)
