"""
ETL Step 2 — Transform
Cleans and enriches the raw DataFrame before loading into the database.
"""

import pandas as pd
import numpy as np
from datetime import date, datetime
from utils.logger import get_logger

logger = get_logger("etl.transform")

VALID_OFFENSE_CATEGORIES = ["Violent", "Drug-related", "Theft/Fraud", "Cybercrime", "White-collar", "Other"]
VALID_STATUSES = ["active", "released", "transferred"]


def transform(df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"[TRANSFORM] Starting transformation on {len(df)} rows.")

    # ── 1. Remove duplicates ──────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates(subset=["inmate_id"], keep="last")
    logger.info(f"[TRANSFORM] Removed {before - len(df)} duplicate inmate_id rows.")

    # ── 2. Handle nulls ───────────────────────────────────────────────
    df["name"] = df["name"].fillna("Unknown Inmate")
    df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(30).astype(int)
    df["offense"] = df["offense"].fillna("Unknown Offense")
    df["offense_category"] = df["offense_category"].fillna("Other")
    df["sentence_years"] = pd.to_numeric(df["sentence_years"], errors="coerce").fillna(1.0)
    df["nationality"] = df["nationality"].fillna("Unknown")
    df["behavior_score"] = pd.to_numeric(df["behavior_score"], errors="coerce").fillna(50.0)
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce").fillna(0.0)
    df["status"] = df["status"].fillna("active")

    # ── 3. Normalize offense categories ──────────────────────────────
    df["offense_category"] = df["offense_category"].apply(
        lambda x: x if x in VALID_OFFENSE_CATEGORIES else "Other"
    )

    # ── 4. Normalize status ───────────────────────────────────────────
    df["status"] = df["status"].str.lower().apply(
        lambda x: x if x in VALID_STATUSES else "active"
    )

    # ── 5. Parse dates ────────────────────────────────────────────────
    df["admission_date"] = pd.to_datetime(df["admission_date"], errors="coerce")
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    # Fill missing admission date with today
    df["admission_date"] = df["admission_date"].fillna(pd.Timestamp(date.today()))

    # Compute release_date where missing: admission + sentence_years
    mask = df["release_date"].isna()
    df.loc[mask, "release_date"] = df.loc[mask].apply(
        lambda row: row["admission_date"] + pd.DateOffset(years=int(row["sentence_years"])), axis=1
    )

    # ── 6. Compute sentence_remaining (days) ─────────────────────────
    today = pd.Timestamp(date.today())
    df["sentence_remaining_days"] = (df["release_date"] - today).dt.days.clip(lower=0)

    # ── 7. Clip scores to valid ranges ───────────────────────────────
    df["behavior_score"] = df["behavior_score"].clip(0, 100)
    df["work_hours"] = df["work_hours"].clip(0, 1000)

    # ── 8. Compute rehabilitation score ──────────────────────────────
    # Formula: 60% behavior_score + 40% normalized work_hours (max 300h = 100%)
    df["rehabilitation_score"] = (
        0.6 * df["behavior_score"] + 0.4 * (df["work_hours"] / 300 * 100)
    ).clip(0, 100).round(1)

    # ── 9. Validate age bounds ────────────────────────────────────────
    df = df[(df["age"] >= 18) & (df["age"] <= 90)]

    # ── 10. Convert dates to Python date for DB compatibility ─────────
    df["admission_date"] = df["admission_date"].dt.date
    df["release_date"] = df["release_date"].dt.date

    logger.info(f"[TRANSFORM] Transformation complete. Output: {len(df)} rows.")
    return df


if __name__ == "__main__":
    from etl.extract import extract_inmates_csv
    raw = extract_inmates_csv()
    clean = transform(raw)
    print(clean[["inmate_id", "name", "status", "rehabilitation_score", "sentence_remaining_days"]].head(10))
