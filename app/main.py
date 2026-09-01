from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.dependencies import get_current_user
from app.models import Job, JobTemplate, RealJob, ScrapeSession, User, UserImportedRealJob, UserImportedTemplate  # noqa: F401
from app.routers import auth, jobs
from app.schemas.auth import UserResponse
from app.services.job_templates import seed_job_templates
from app.services.real_jobs import seed_real_jobs

Base.metadata.create_all(bind=engine)

with engine.connect() as connection:
    columns = connection.exec_driver_sql("PRAGMA table_info(jobs)").fetchall()
    column_names = {column[1] for column in columns}
    if columns and "is_real" not in column_names:
        connection.exec_driver_sql("ALTER TABLE jobs ADD COLUMN is_real BOOLEAN NOT NULL DEFAULT 0")
        connection.commit()

with SessionLocal() as db:
    seed_job_templates(db)
    seed_real_jobs(db)

app = FastAPI(title="Iasty Bid API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/auth/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
