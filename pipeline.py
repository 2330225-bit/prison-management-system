"""
ETL Pipeline Runner
Run: python -m etl.pipeline
Run with scheduling: python -m etl.pipeline --schedule
"""

import argparse
import time
from datetime import datetime
from utils.logger import get_logger, log_activity

logger = get_logger("etl.pipeline")


def run_pipeline():
    """Execute the full ETL pipeline."""
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("  PRISON MANAGEMENT ETL PIPELINE — STARTING")
    logger.info("=" * 60)
    log_activity("ETL Pipeline", "Pipeline execution started", "INFO")

    try:
        # ── STEP 1: EXTRACT ──────────────────────────────────────────
        logger.info("[PIPELINE] Step 1/3 — EXTRACT")
        from etl.extract import extract_inmates_csv
        raw_df = extract_inmates_csv()
        logger.info(f"[PIPELINE] Extracted {len(raw_df)} raw records.")

        # ── STEP 2: TRANSFORM ────────────────────────────────────────
        logger.info("[PIPELINE] Step 2/3 — TRANSFORM")
        from etl.transform import transform
        clean_df = transform(raw_df)
        logger.info(f"[PIPELINE] Transformed → {len(clean_df)} clean records.")

        # ── STEP 3: LOAD ─────────────────────────────────────────────
        logger.info("[PIPELINE] Step 3/3 — LOAD")
        from etl.load import upsert_inmates, upsert_stats
        inmates_count = upsert_inmates(clean_df)
        stats_count = upsert_stats(clean_df)
        logger.info(f"[PIPELINE] Loaded {inmates_count} inmates, {stats_count} stats.")

        elapsed = (datetime.now() - start).total_seconds()
        logger.info("=" * 60)
        logger.info(f"  PIPELINE COMPLETE in {elapsed:.2f}s")
        logger.info("=" * 60)
        log_activity("ETL Pipeline", f"Completed in {elapsed:.2f}s. Inmates: {inmates_count}, Stats: {stats_count}", "INFO")
        return True

    except Exception as e:
        elapsed = (datetime.now() - start).total_seconds()
        logger.error(f"[PIPELINE] FAILED after {elapsed:.2f}s: {e}")
        log_activity("ETL Pipeline", f"FAILED: {e}", "ERROR")
        return False


def run_scheduled(interval_minutes: int = 30):
    """Run the pipeline on a schedule."""
    logger.info(f"[SCHEDULER] ETL will run every {interval_minutes} minutes.")
    while True:
        success = run_pipeline()
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"[SCHEDULER] Run {status}. Next run in {interval_minutes} minutes...")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prison Management ETL Pipeline")
    parser.add_argument("--schedule", action="store_true", help="Run on schedule (every 30 min)")
    parser.add_argument("--interval", type=int, default=30, help="Schedule interval in minutes")
    args = parser.parse_args()

    if args.schedule:
        run_scheduled(args.interval)
    else:
        success = run_pipeline()
        exit(0 if success else 1)
