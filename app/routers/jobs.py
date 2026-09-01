from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import EmploymentType, WorkMode
from app.models.user import User
from app.schemas.job import (
    JobFilterOptionsResponse,
    JobListResponse,
    JobResponse,
    JobSortField,
    ScrapeNextResponse,
    ScrapeStatusResponse,
    ScrapeStopResponse,
    SortOrder,
)
from app.services.job_templates import (
    get_scrape_status,
    scrape_next_job,
    start_scrape_session,
    stop_scrape_session,
)
from app.services.jobs import ensure_default_jobs, get_filter_options, list_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
def get_jobs(
    search: str | None = None,
    company: str | None = None,
    industry: str | None = None,
    work_mode: WorkMode | None = None,
    employment_type: EmploymentType | None = None,
    location: str | None = None,
    is_real: bool | None = None,
    sort_by: JobSortField = JobSortField.created_at,
    sort_order: SortOrder = SortOrder.desc,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_default_jobs(db, current_user)
    items, total = list_jobs(
        db,
        current_user,
        search=search,
        company=company,
        industry=industry,
        work_mode=work_mode,
        employment_type=employment_type,
        location=location,
        is_real=is_real,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return JobListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/filter-options", response_model=JobFilterOptionsResponse)
def job_filter_options(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    companies, industries = get_filter_options(db, current_user)
    return JobFilterOptionsResponse(companies=companies, industries=industries)


@router.post("/scrape/start", response_model=ScrapeStatusResponse)
def scrape_start(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_scrape_session(db, current_user)
    return ScrapeStatusResponse(**get_scrape_status(db, current_user))


@router.post("/scrape/stop", response_model=ScrapeStopResponse)
def scrape_stop(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _, real_jobs = stop_scrape_session(db, current_user)
    status = get_scrape_status(db, current_user)
    return ScrapeStopResponse(
        is_active=status["is_active"],
        real_jobs=[JobResponse.model_validate(job) for job in real_jobs],
    )


@router.post("/scrape/next", response_model=ScrapeNextResponse)
def scrape_next(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job, status = scrape_next_job(db, current_user)
    return ScrapeNextResponse(status=status, job=JobResponse.model_validate(job) if job else None)


@router.get("/scrape/status", response_model=ScrapeStatusResponse)
def scrape_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ScrapeStatusResponse(**get_scrape_status(db, current_user))
