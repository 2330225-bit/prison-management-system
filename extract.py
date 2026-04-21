"""
ETL Step 1 — Extract
Reads raw CSV data from the data/ directory into a pandas DataFrame.
"""

import pandas as pd
import os
from utils.logger import get_logger

logger = get_logger("etl.extract")

RAW_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_data.csv")


def extract_inmates_csv(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Read raw inmate log CSV into a DataFrame."""
    logger.info(f"[EXTRACT] Reading CSV from: {filepath}")
    try:
        df = pd.read_csv(filepath)
        logger.info(f"[EXTRACT] Loaded {len(df)} rows, {len(df.columns)} columns.")
        logger.info(f"[EXTRACT] Columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        logger.error(f"[EXTRACT] File not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"[EXTRACT] Failed to read CSV: {e}")
        raise


def extract_from_db_query(query: str, conn_string: str = None) -> pd.DataFrame:
    """Extract data directly from database using a SQL query (for advanced ETL)."""
    if not conn_string:
        from dotenv import load_dotenv
        load_dotenv()
        conn_string = os.getenv("DATABASE_URL")
    from sqlalchemy import create_engine
    engine = create_engine(conn_string)
    logger.info(f"[EXTRACT] Running DB query...")
    df = pd.read_sql(query, engine)
    logger.info(f"[EXTRACT] DB query returned {len(df)} rows.")
    return df


if __name__ == "__main__":
    df = extract_inmates_csv()
    print(df.head())
    print(df.dtypes)
