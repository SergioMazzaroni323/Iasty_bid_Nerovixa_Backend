from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.models.job import EmploymentType, Job, WorkMode
from app.models.job_template import JobTemplate
from app.models.scrape_session import UserImportedTemplate
from app.models.user import User
from app.schemas.job import JobCreateRequest, JobSortField, SortOrder

DEFAULT_JOB_COUNT = 243


SORT_COLUMNS = {
    JobSortField.job_title: Job.job_title,
    JobSortField.company_name: Job.company_name,
    JobSortField.industry: Job.industry,
    JobSortField.work_mode: Job.work_mode,
    JobSortField.employment_type: Job.employment_type,
    JobSortField.salary_expected: Job.salary_expected,
    JobSortField.required_locations: Job.required_locations,
    JobSortField.created_at: Job.created_at,
}


def ensure_default_jobs(db: Session, user: User) -> int:
    """Ensure each user has up to DEFAULT_JOB_COUNT starter jobs."""
    from app.services.real_jobs import import_real_jobs_for_user

    import_real_jobs_for_user(db, user)

    current = db.query(Job).filter(Job.user_id == user.id).count()
    if current >= DEFAULT_JOB_COUNT:
        return current

    needed = DEFAULT_JOB_COUNT - current

    imported_ids = {
        row[0]
        for row in db.query(UserImportedTemplate.template_id)
        .filter(UserImportedTemplate.user_id == user.id)
        .all()
    }

    query = db.query(JobTemplate).order_by(JobTemplate.id.asc())
    if imported_ids:
        query = query.filter(~JobTemplate.id.in_(imported_ids))
    templates = query.limit(needed).all()

    for template in templates:
        db.add(
            Job(
                user_id=user.id,
                job_title=template.job_title,
                company_name=template.company_name,
                job_link=template.job_link,
                job_description=template.job_description,
                required_role=template.required_role,
                required_locations=template.required_locations,
                work_mode=template.work_mode,
                employment_type=template.employment_type,
                salary_expected=template.salary_expected,
                industry=template.industry,
                is_real=False,
            )
        )
        db.add(UserImportedTemplate(user_id=user.id, template_id=template.id))

    db.commit()
    return db.query(Job).filter(Job.user_id == user.id).count()


def seed_sample_jobs(db: Session, user: User) -> None:
    ensure_default_jobs(db, user)


def create_job(db: Session, user: User, payload: JobCreateRequest) -> Job:
    job = Job(
        user_id=user.id,
        job_title=payload.job_title,
        company_name=payload.company_name,
        job_link=str(payload.job_link) if payload.job_link else None,
        job_description=payload.job_description,
        required_role=payload.required_role,
        required_locations=payload.required_locations,
        work_mode=payload.work_mode,
        employment_type=payload.employment_type,
        salary_expected=payload.salary_expected,
        industry=payload.industry,
    )
    db.add(job)
    return job


def list_jobs(
    db: Session,
    user: User,
    *,
    search: str | None,
    company: str | None,
    industry: str | None,
    work_mode: WorkMode | None,
    employment_type: EmploymentType | None,
    location: str | None,
    is_real: bool | None,
    sort_by: JobSortField,
    sort_order: SortOrder,
    page: int,
    page_size: int,
) -> tuple[list[Job], int]:
    query = db.query(Job).filter(Job.user_id == user.id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Job.job_title.ilike(term),
                Job.company_name.ilike(term),
                Job.job_description.ilike(term),
                Job.required_role.ilike(term),
                Job.industry.ilike(term),
            )
        )

    if company:
        query = query.filter(Job.company_name == company)

    if industry:
        query = query.filter(Job.industry == industry)

    if work_mode:
        query = query.filter(Job.work_mode == work_mode)

    if employment_type:
        query = query.filter(Job.employment_type == employment_type)

    if location:
        query = query.filter(Job.required_locations.ilike(f"%{location.strip()}%"))

    if is_real is not None:
        query = query.filter(Job.is_real.is_(is_real))

    total = query.count()

    sort_column = SORT_COLUMNS[sort_by]
    sort_direction = asc(sort_column) if sort_order == SortOrder.asc else desc(sort_column)
    items = (
        query.order_by(desc(Job.is_real), sort_direction)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total


def get_filter_options(db: Session, user: User) -> tuple[list[str], list[str]]:
    companies = [
        row[0]
        for row in db.query(Job.company_name)
        .filter(Job.user_id == user.id)
        .distinct()
        .order_by(Job.company_name)
        .all()
    ]
    industries = [
        row[0]
        for row in db.query(Job.industry)
        .filter(Job.user_id == user.id, Job.industry.isnot(None), Job.industry != "")
        .distinct()
        .order_by(Job.industry)
        .all()
    ]
    return companies, industries
