from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.dependencies import ensure_admin_privileges, get_current_user
from app.models import Job, JobTemplate, RealJob, ScrapeSession, User, UserImportedRealJob, UserImportedTemplate  # noqa: F401
from app.routers import admin, auth, jobs
from app.schemas.auth import UserResponse
from app.services.job_templates import seed_job_templates
from app.services.real_jobs import seed_real_jobs

Base.metadata.create_all(bind=engine)


def migrate_schema() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "role" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'"))
        if "status" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'pending'"))
            # Existing verified accounts stay usable after deploy
            connection.execute(
                text("UPDATE users SET status = 'active' WHERE is_verified = true OR is_verified = 1")
            )

        if "jobs" in inspector.get_table_names():
            job_columns = {column["name"] for column in inspector.get_columns("jobs")}
            if "is_real" not in job_columns:
                if settings.database_url.startswith("sqlite"):
                    connection.execute(text("ALTER TABLE jobs ADD COLUMN is_real BOOLEAN NOT NULL DEFAULT 0"))
                else:
                    connection.execute(text("ALTER TABLE jobs ADD COLUMN is_real BOOLEAN NOT NULL DEFAULT FALSE"))


def ensure_admin_account() -> None:
    with SessionLocal() as db:
        admin = (
            db.query(User)
            .filter(User.email == settings.admin_email.lower())
            .first()
        )
        if not admin:
            return
        if ensure_admin_privileges(admin):
            db.add(admin)
            db.commit()


migrate_schema()

with SessionLocal() as db:
    seed_job_templates(db)
    seed_real_jobs(db)

ensure_admin_account()

app = FastAPI(title="Iasty Bid API", version="1.0.0")

cors_origins = {
    settings.frontend_url.rstrip("/"),
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/auth/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
