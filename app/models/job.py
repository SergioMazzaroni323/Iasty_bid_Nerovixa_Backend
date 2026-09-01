import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WorkMode(str, enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    on_site = "on-site"


class EmploymentType(str, enum.Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"
    temporary = "temporary"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    job_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    required_locations: Mapped[str | None] = mapped_column(String(512), nullable=True)
    work_mode: Mapped[WorkMode] = mapped_column(Enum(WorkMode, native_enum=False), nullable=False, index=True)
    employment_type: Mapped[EmploymentType] = mapped_column(Enum(EmploymentType, native_enum=False), nullable=False, index=True)
    salary_expected: Mapped[str | None] = mapped_column(String(128), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    is_real: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="jobs")
