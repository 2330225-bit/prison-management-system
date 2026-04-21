import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from database.db import create_tables
from routes import inmates, cells, staff, incidents, analytics
from utils.logger import get_logger, log_activity

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Prison Management System API...")
    create_tables()
    log_activity("System Started", "Prison Management API initialized", "INFO")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Prison Management System API",
    description="Data Engineering Capstone Project — REST API for Prison Management System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(inmates.router)
app.include_router(cells.router)
app.include_router(staff.router)
app.include_router(incidents.router)
app.include_router(analytics.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Prison Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online"
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "Prison Management API"}


@app.get("/leaderboard", tags=["Analytics"])
def leaderboard_shortcut():
    from database.db import SessionLocal
    from models.models import InmateStat, Inmate
    db = SessionLocal()
    try:
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
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
