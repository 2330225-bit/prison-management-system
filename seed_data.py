"""
Seed script: populates the database with realistic sample data.
Run: python seed_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
import random
from database.db import SessionLocal, create_tables
from models.models import Cell, Inmate, Staff, Incident, InmateStat
from utils.logger import get_logger

logger = get_logger("seed")

OFFENSE_CATEGORIES = ["Violent", "Drug-related", "Theft/Fraud", "Cybercrime", "White-collar", "Other"]

OFFENSES = {
    "Violent": ["Armed Robbery", "Assault", "Homicide", "Kidnapping", "Manslaughter"],
    "Drug-related": ["Drug Trafficking", "Drug Possession", "Manufacturing Narcotics"],
    "Theft/Fraud": ["Grand Theft", "Identity Theft", "Bank Fraud", "Burglary", "Embezzlement"],
    "Cybercrime": ["Hacking", "Cyberstalking", "Online Fraud", "Data Breach"],
    "White-collar": ["Tax Evasion", "Money Laundering", "Insider Trading", "Bribery"],
    "Other": ["Arson", "Vandalism", "Trespassing", "Contempt of Court"],
}

NAMES = [
    "Marcus Reid", "Darnell Washington", "James Holden", "Carlos Rivera", "Mohammed Al-Amin",
    "Victor Okonkwo", "Tyler Brooks", "Nathan Pierce", "Isaiah Jefferson", "Diego Salazar",
    "Raymond Chu", "Patrick Nwosu", "Sean McCarthy", "Andre Dubois", "Boris Petrov",
    "Kevin Yamamoto", "Leon Adeyemi", "Rashid Khan", "Jonah Mbeki", "Ivan Kowalski",
    "Felix Osei", "Hamid Nazari", "Emmanuel Tetteh", "Alejandro Vega", "Desmond Hall"
]

STAFF_DATA = [
    ("Eleanor Grant", "Warden", "Day", "ALL"),
    ("Victor Drago", "Guard", "Day", "A"),
    ("Samira Okafor", "Guard", "Night", "B"),
    ("Thomas Holt", "Guard", "Day", "C"),
    ("Patricia Nkosi", "Guard", "Night", "D"),
    ("Dr. James Reyes", "Medical", "Day", "ALL"),
    ("Nurse Aisha Cole", "Medical", "Night", "ALL"),
    ("Henry Marsh", "Admin", "Day", "ALL"),
    ("Linda Tran", "Admin", "Day", "ALL"),
    ("Captain Roy Blake", "Guard", "Rotating", "B"),
]


def seed():
    create_tables()
    db = SessionLocal()

    try:
        # --- CELLS ---
        if db.query(Cell).count() == 0:
            cells = []
            for block in ["A", "B", "C", "D"]:
                for i in range(1, 6):  # 5 cells per block
                    cell = Cell(
                        block=block,
                        capacity=4,
                        current_count=0,
                        status="vacant"
                    )
                    cells.append(cell)
            db.add_all(cells)
            db.commit()
            logger.info(f"Created {len(cells)} cells across 4 blocks.")

        # --- STAFF ---
        if db.query(Staff).count() == 0:
            staff_list = []
            for name, role, shift, block in STAFF_DATA:
                s = Staff(
                    name=name,
                    role=role,
                    shift=shift,
                    cell_block_assigned=block,
                    years_of_service=random.randint(1, 20),
                    contact=f"{name.lower().replace(' ', '.')}@prison.gov"
                )
                staff_list.append(s)
            db.add_all(staff_list)
            db.commit()
            logger.info(f"Created {len(staff_list)} staff members.")

        # --- INMATES ---
        if db.query(Inmate).count() == 0:
            cells_db = db.query(Cell).all()
            inmates = []
            for i, name in enumerate(NAMES[:20]):
                cat = random.choice(OFFENSE_CATEGORIES)
                offense = random.choice(OFFENSES[cat])
                sentence = round(random.uniform(1.5, 25.0), 1)
                admit = date.today() - timedelta(days=random.randint(180, 2000))
                release = admit + timedelta(days=int(sentence * 365))
                status = "released" if release < date.today() else "active"
                cell = cells_db[i % len(cells_db)]

                inmate = Inmate(
                    name=name,
                    age=random.randint(20, 60),
                    offense=offense,
                    offense_category=cat,
                    sentence_years=sentence,
                    cell_id=cell.cell_id,
                    admission_date=admit,
                    release_date=release,
                    status=status,
                    nationality=random.choice(["Nigerian", "American", "British", "Indian", "Brazilian", "Russian", "Ghanaian", "Mexican"])
                )
                inmates.append(inmate)

                if status == "active":
                    cell.current_count = min(cell.current_count + 1, cell.capacity)
                    cell.status = "occupied"

            db.add_all(inmates)
            db.commit()
            logger.info(f"Created {len(inmates)} inmates.")

        # --- INCIDENTS ---
        if db.query(Incident).count() == 0:
            inmates_db = db.query(Inmate).limit(20).all()
            staff_db = db.query(Staff).all()
            incident_types = ["Fight", "Escape Attempt", "Contraband", "Medical Emergency", "Property Damage", "Verbal Altercation"]
            severities = ["Low", "Low", "Medium", "Medium", "High", "Critical"]

            incidents = []
            for _ in range(15):
                inmate = random.choice(inmates_db)
                staff_member = random.choice(staff_db)
                inc_type = random.choice(incident_types)
                sev = random.choice(severities)
                inc_date = date.today() - timedelta(days=random.randint(1, 365))
                incident = Incident(
                    inmate_id=inmate.inmate_id,
                    staff_id=staff_member.staff_id,
                    date=inc_date,
                    type=inc_type,
                    severity=sev,
                    description=f"{inc_type} involving inmate {inmate.name}. Handled by {staff_member.name}.",
                    resolved=random.choice(["Yes", "No"])
                )
                incidents.append(incident)

            db.add_all(incidents)
            db.commit()
            logger.info(f"Created {len(incidents)} incident records.")

        # --- INMATE STATS ---
        if db.query(InmateStat).count() == 0:
            inmates_db = db.query(Inmate).all()
            stats = []
            for inmate in inmates_db:
                behavior = round(random.uniform(30, 95), 1)
                work_hours = round(random.uniform(0, 200), 1)
                # Rehabilitation score: weighted avg of behavior + work contribution
                rehab = round(min(100, behavior * 0.6 + (work_hours / 200) * 40), 1)
                stat = InmateStat(
                    inmate_id=inmate.inmate_id,
                    behavior_score=behavior,
                    rehabilitation_score=rehab,
                    work_hours=work_hours,
                    date=date.today()
                )
                stats.append(stat)

            db.add_all(stats)
            db.commit()
            logger.info(f"Created {len(stats)} inmate stat records.")

        logger.info("✅ Seed complete! Database is ready.")

    except Exception as e:
        db.rollback()
        logger.error(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
