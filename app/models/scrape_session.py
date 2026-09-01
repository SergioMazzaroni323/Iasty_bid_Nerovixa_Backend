from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScrapeSession(Base):
    __tablename__ = "scrape_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    queue: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class UserImportedTemplate(Base):
    __tablename__ = "user_imported_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    template_id: Mapped[int] = mapped_column(ForeignKey("job_templates.id"), index=True, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserImportedRealJob(Base):
    __tablename__ = "user_imported_real_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    real_job_id: Mapped[int] = mapped_column(ForeignKey("real_jobs.id"), index=True, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
