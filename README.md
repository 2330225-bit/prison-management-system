# 🏛️ PrisonOS — Prison Management System
### Data Engineering Capstone Project

A full-stack data engineering platform for correctional facility management featuring a REST API, ETL pipeline, PostgreSQL storage, and interactive analytics dashboard.

---

## 🏗️ Architecture

```
Data Source (CSV)
     ↓
ETL Pipeline (Extract → Transform → Load)
     ↓
PostgreSQL Database (5 tables)
     ↓
FastAPI REST Layer (15+ endpoints)
     ↓
HTML Dashboard (Chart.js, dark UI)
```

---

## 📁 Project Structure

```
prison_management/
├── main.py                  ← FastAPI app entry point
├── requirements.txt
├── .env.example
├── seed_data.py             ← Populate sample data
├── index.html               ← Standalone frontend
├── database/
│   └── db.py                ← SQLAlchemy engine & session
├── models/
│   └── models.py            ← ORM models (5 tables)
├── routes/
│   ├── inmates.py
│   ├── cells.py
│   ├── staff.py
│   ├── incidents.py
│   └── analytics.py
├── etl/
│   ├── extract.py           ← Read CSV/DB
│   ├── transform.py         ← Clean & enrich
│   ├── load.py              ← UPSERT to PostgreSQL
│   ├── pipeline.py          ← Full runner
│   └── airflow_dag.py       ← Airflow DAG (30 min)
├── data/
│   └── raw_data.csv         ← 35 sample inmate records
└── utils/
    └── logger.py            ← Logging utility
```

---

## 🚀 How to Run

### Step 1 — Setup PostgreSQL

```sql
-- In psql or pgAdmin:
CREATE DATABASE prison_db;
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Configure Environment

```bash
cp .env.example .env
# Edit .env and set your DB password:
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/prison_db
```

### Step 4 — Start the API

```bash
python main.py
```

This auto-creates all tables on startup.

### Step 5 — Seed Sample Data

```bash
python seed_data.py
```

Loads 20 inmates, 10 staff, 4 cell blocks, 15 incidents.

### Step 6 — Run ETL Pipeline

```bash
python -m etl.pipeline
```

Reads `data/raw_data.csv`, transforms it, and upserts into DB.

**Scheduled mode (every 30 min):**
```bash
python -m etl.pipeline --schedule
```

### Step 7 — Open Frontend

Open `index.html` in your browser, or visit:

- **Dashboard:** `http://localhost:8000` → open `index.html`
- **API Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inmates` | All inmates (filterable) |
| GET | `/inmates/{id}` | Single inmate |
| POST | `/inmates` | Add new inmate |
| GET | `/cells` | All cells |
| POST | `/cells` | Add cell |
| GET | `/staff` | All staff |
| POST | `/staff` | Add staff member |
| GET | `/incidents` | All incidents |
| GET | `/leaderboard` | Top rehab scores |
| GET | `/analytics/overview` | Dashboard stats |
| GET | `/analytics/offense-stats` | Offense breakdown |
| GET | `/analytics/population-trend` | Population over time |
| GET | `/analytics/staff-stats` | Staff by role |
| GET | `/analytics/sentence-distribution` | Sentence ranges |
| GET | `/analytics/pipeline-status` | ETL pipeline health |
| GET | `/analytics/activity-log` | System activity log |

---

## 🗄️ Database Schema

### `inmates`
| Column | Type | Description |
|--------|------|-------------|
| inmate_id | PK INT | Unique identifier |
| name | VARCHAR(100) | Full name |
| age | INT | Age |
| offense | VARCHAR(100) | Crime committed |
| offense_category | VARCHAR(50) | Normalized category |
| sentence_years | FLOAT | Sentence length |
| cell_id | FK INT | Assigned cell |
| admission_date | DATE | Entry date |
| release_date | DATE | Expected release |
| status | VARCHAR(20) | active/released/transferred |

### `cells`
| Column | Type | Description |
|--------|------|-------------|
| cell_id | PK INT | Unique identifier |
| block | VARCHAR(10) | Block label (A/B/C/D) |
| capacity | INT | Max occupants |
| current_count | INT | Current occupants |
| status | VARCHAR(20) | occupied/vacant/maintenance |

### `staff`
| Column | Type | Description |
|--------|------|-------------|
| staff_id | PK INT | Unique identifier |
| name | VARCHAR(100) | Full name |
| role | VARCHAR(50) | Warden/Guard/Medical/Admin |
| shift | VARCHAR(20) | Day/Night/Rotating |
| cell_block_assigned | VARCHAR(10) | Assigned block |

### `incidents`
| Column | Type | Description |
|--------|------|-------------|
| incident_id | PK INT | Unique identifier |
| inmate_id | FK INT | Linked inmate |
| staff_id | FK INT | Reporting staff |
| date | DATE | Incident date |
| type | VARCHAR(50) | Incident type |
| severity | VARCHAR(20) | Low/Medium/High/Critical |

### `inmate_stats`
| Column | Type | Description |
|--------|------|-------------|
| stat_id | PK INT | Unique identifier |
| inmate_id | FK INT | Linked inmate |
| behavior_score | FLOAT | 0–100 behavior rating |
| rehabilitation_score | FLOAT | Computed rehab score |
| work_hours | FLOAT | Work program hours |
| date | DATE | Record date |

---

## ⚡ ETL Pipeline Details

### Extract (`etl/extract.py`)
- Reads `data/raw_data.csv` using pandas
- Supports direct DB query extraction

### Transform (`etl/transform.py`)
- Removes duplicate inmate_id records
- Fills nulls with safe defaults
- Normalizes offense categories (6 types)
- Computes `rehabilitation_score = 0.6 × behavior + 0.4 × normalized_work_hours`
- Calculates `sentence_remaining_days`
- Validates age bounds (18–90)

### Load (`etl/load.py`)
- UPSERT strategy — safe to re-run
- Updates existing records, inserts new ones
- Upserts daily inmate_stats

### Airflow DAG (`etl/airflow_dag.py`)
- DAG ID: `prison_management_etl`
- Schedule: `*/30 * * * *` (every 30 minutes)
- 4 tasks: extract → transform → load → notify

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 15 |
| ETL | Pandas, NumPy |
| Scheduler | Apache Airflow |
| Frontend | HTML5, CSS3, JavaScript |
| Charts | Chart.js 4 |
| Fonts | Exo 2, JetBrains Mono |
| Validation | Pydantic v2 |

---

## 🔧 Troubleshooting

**Database connection error:**
```python
# In database/db.py, hardcode:
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/prison_db"
```

**Airflow setup:**
```bash
export AIRFLOW_HOME=~/airflow
airflow db init
cp etl/airflow_dag.py ~/airflow/dags/
airflow scheduler &
airflow webserver
```

---

## 👤 Author

Data Engineering Capstone Project  
Prison Management System — Full Stack  
Built with FastAPI + PostgreSQL + Pandas + ETL Pipeline
