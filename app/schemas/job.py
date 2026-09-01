from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl

from app.models.job import EmploymentType, WorkMode


class JobSortField(str, Enum):
    job_title = "job_title"
    company_name = "company_name"
    industry = "industry"
    work_mode = "work_mode"
    employment_type = "employment_type"
    salary_expected = "salary_expected"
    required_locations = "required_locations"
    created_at = "created_at"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class JobCreateRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    job_link: HttpUrl | None = None
    job_description: str | None = None
    required_role: str | None = Field(default=None, max_length=255)
    required_locations: str | None = Field(default=None, max_length=512)
    work_mode: WorkMode
    employment_type: EmploymentType
    salary_expected: str | None = Field(default=None, max_length=128)
    industry: str | None = Field(default=None, max_length=128)


class JobResponse(BaseModel):
    id: int
    job_title: str
    company_name: str
    job_link: str | None
    job_description: str | None
    required_role: str | None
    required_locations: str | None
    work_mode: WorkMode
    employment_type: EmploymentType
    salary_expected: str | None
    industry: str | None
    is_real: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int


class JobFilterOptionsResponse(BaseModel):
    companies: list[str]
    industries: list[str]


class ScrapeStopResponse(BaseModel):
    is_active: bool
    real_jobs: list[JobResponse]


class ScrapeStatusResponse(BaseModel):
    is_active: bool
    remaining_in_queue: int
    imported_count: int
    total_templates: int
    available_templates: int


class ScrapeNextResponse(BaseModel):
    status: str
    job: JobResponse | None = None
