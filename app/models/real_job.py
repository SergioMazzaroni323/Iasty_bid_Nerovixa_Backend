from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.job import EmploymentType, WorkMode


class RealJob(Base):
    __tablename__ = "real_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    required_locations: Mapped[str | None] = mapped_column(String(512), nullable=True)
    work_mode: Mapped[WorkMode] = mapped_column(Enum(WorkMode, native_enum=False), nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(Enum(EmploymentType, native_enum=False), nullable=False)
    salary_expected: Mapped[str | None] = mapped_column(String(128), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
