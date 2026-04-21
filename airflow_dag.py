"""
Apache Airflow DAG — Prison Management ETL
Runs every 30 minutes.

Deploy: copy this file to $AIRFLOW_HOME/dags/
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "email": ["admin@prison.gov"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="prison_management_etl",
    default_args=default_args,
    description="ETL pipeline for Prison Management System — runs every 30 minutes",
    schedule_interval="*/30 * * * *",  # every 30 minutes
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["prison", "etl", "data-engineering"],
)


def task_extract(**context):
    """Extract raw inmate data from CSV source."""
    import sys, os
    sys.path.insert(0, "/opt/prison_management")
    from etl.extract import extract_inmates_csv
    df = extract_inmates_csv()
    # Push to XCom for downstream tasks
    context["ti"].xcom_push(key="row_count", value=len(df))
    print(f"[EXTRACT] {len(df)} rows extracted.")


def task_transform(**context):
    """Transform and clean extracted data."""
    import sys, os
    sys.path.insert(0, "/opt/prison_management")
    from etl.extract import extract_inmates_csv
    from etl.transform import transform
    raw = extract_inmates_csv()
    clean = transform(raw)
    context["ti"].xcom_push(key="clean_count", value=len(clean))
    print(f"[TRANSFORM] {len(clean)} clean rows ready.")


def task_load(**context):
    """Load transformed data into PostgreSQL."""
    import sys, os
    sys.path.insert(0, "/opt/prison_management")
    from etl.extract import extract_inmates_csv
    from etl.transform import transform
    from etl.load import upsert_inmates, upsert_stats
    raw = extract_inmates_csv()
    clean = transform(raw)
    inmates = upsert_inmates(clean)
    stats = upsert_stats(clean)
    print(f"[LOAD] {inmates} inmates, {stats} stats upserted.")


def task_notify(**context):
    """Log pipeline completion."""
    extract_count = context["ti"].xcom_pull(key="row_count", task_ids="extract")
    clean_count = context["ti"].xcom_pull(key="clean_count", task_ids="transform")
    print(f"[NOTIFY] ETL complete: {extract_count} extracted → {clean_count} loaded.")


extract_task = PythonOperator(
    task_id="extract",
    python_callable=task_extract,
    dag=dag,
)

transform_task = PythonOperator(
    task_id="transform",
    python_callable=task_transform,
    dag=dag,
)

load_task = PythonOperator(
    task_id="load",
    python_callable=task_load,
    dag=dag,
)

notify_task = PythonOperator(
    task_id="notify",
    python_callable=task_notify,
    dag=dag,
)

# Define pipeline order
extract_task >> transform_task >> load_task >> notify_task
