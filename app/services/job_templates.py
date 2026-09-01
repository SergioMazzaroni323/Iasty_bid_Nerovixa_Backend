import json
import random

from sqlalchemy.orm import Session

from app.models.job import EmploymentType, Job, WorkMode
from app.models.job_template import JobTemplate
from app.models.scrape_session import ScrapeSession, UserImportedTemplate
from app.models.user import User

TEMPLATE_TARGET_COUNT = 1500

TITLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "DevOps Engineer",
    "Data Analyst",
    "Product Manager",
    "QA Engineer",
    "Mobile Developer",
    "Cloud Architect",
    "Security Engineer",
    "Machine Learning Engineer",
    "UI/UX Designer",
    "Technical Writer",
]

COMPANIES = [
    "Acme Corp",
    "DataFlow Inc",
    "CloudNine",
    "HealthPlus",
    "StartupLab",
    "NovaTech",
    "BlueRiver Systems",
    "Summit Analytics",
    "PixelWorks",
    "GreenField Labs",
    "Orbit Finance",
    "BrightPath Health",
    "Quantum Soft",
    "Redwood Digital",
    "Skyline Media",
    "Atlas Logistics",
    "Vertex AI",
    "Harbor Insurance",
    "Lumen Retail",
    "Forge Automotive",
]

INDUSTRIES = [
    "Technology",
    "FinTech",
    "Healthcare",
    "E-commerce",
    "Education",
    "Manufacturing",
    "Media",
    "Logistics",
    "Insurance",
    "Automotive",
]

LOCATIONS = [
    "Remote",
    "San Francisco, CA",
    "New York, NY",
    "Austin, TX",
    "Seattle, WA",
    "Chicago, IL",
    "Boston, MA",
    "Denver, CO",
    "Los Angeles, CA",
    "Atlanta, GA",
    "Toronto, ON",
    "London, UK",
]

ROLES = [
    "Software Engineer",
    "Frontend Developer",
    "Backend Engineer",
    "Full Stack Developer",
    "DevOps",
    "Data Analyst",
    "Product Manager",
    "QA Engineer",
]

WORK_MODES = list(WorkMode)
EMPLOYMENT_TYPES = list(EmploymentType)

SALARY_RANGES = [
    "$60k - $80k",
    "$80k - $100k",
    "$100k - $130k",
    "$130k - $160k",
    "$160k - $200k",
    "$40/hr",
    "$55/hr",
    "$75/hr",
    "$90/hr",
    "$110/hr",
]


def seed_job_templates(db: Session) -> None:
    existing = db.query(JobTemplate).count()
    if existing >= 1000:
        return

    if existing > 0:
        db.query(JobTemplate).delete()
        db.commit()

    templates: list[JobTemplate] = []
    for index in range(TEMPLATE_TARGET_COUNT):
        title = random.choice(TITLES)
        level = random.choice(["Junior", "Mid", "Senior", "Lead", "Principal", ""])
        job_title = f"{level} {title}".strip() if level else title
        company = random.choice(COMPANIES)
        industry = random.choice(INDUSTRIES)
        work_mode = random.choice(WORK_MODES)
        employment_type = random.choice(EMPLOYMENT_TYPES)
        location = random.choice(LOCATIONS)
        if work_mode == WorkMode.remote:
            location = "Remote"
        elif work_mode == WorkMode.hybrid and location == "Remote":
            location = random.choice(LOCATIONS[1:])

        templates.append(
            JobTemplate(
                job_title=job_title,
                company_name=company,
                job_link=f"https://jobs.example.com/{index + 1}/{company.lower().replace(' ', '-')}",
                job_description=(
                    f"{company} is hiring a {job_title} to build scalable products in {industry}. "
                    f"Work with cross-functional teams, ship features, and improve platform reliability."
                ),
                required_role=random.choice(ROLES),
                required_locations=location,
                work_mode=work_mode,
                employment_type=employment_type,
                salary_expected=random.choice(SALARY_RANGES),
                industry=industry,
            )
        )

    db.add_all(templates)
    db.commit()


def _imported_template_ids(db: Session, user: User) -> set[int]:
    rows = (
        db.query(UserImportedTemplate.template_id)
        .filter(UserImportedTemplate.user_id == user.id)
        .all()
    )
    return {row[0] for row in rows}


def start_scrape_session(db: Session, user: User) -> ScrapeSession:
    imported = _imported_template_ids(db, user)
    query = db.query(JobTemplate.id)
    if imported:
        query = query.filter(~JobTemplate.id.in_(imported))
    available_ids = [row[0] for row in query.all()]
    random.shuffle(available_ids)

    session = db.query(ScrapeSession).filter(ScrapeSession.user_id == user.id).first()
    if not session:
        session = ScrapeSession(user_id=user.id)
        db.add(session)

    session.is_active = True
    session.queue = json.dumps(available_ids)
    db.commit()
    db.refresh(session)
    return session


def stop_scrape_session(db: Session, user: User) -> tuple[ScrapeSession | None, list[Job]]:
    from app.services.real_jobs import import_real_jobs_for_user

    session = db.query(ScrapeSession).filter(ScrapeSession.user_id == user.id).first()
    if session:
        session.is_active = False
        db.commit()
        db.refresh(session)

    real_jobs = import_real_jobs_for_user(db, user)
    return session, real_jobs


def scrape_next_job(db: Session, user: User) -> tuple[Job | None, str]:
    session = db.query(ScrapeSession).filter(ScrapeSession.user_id == user.id).first()
    if not session or not session.is_active:
        return None, "stopped"

    while True:
        queue: list[int] = json.loads(session.queue or "[]")
        if not queue:
            session.is_active = False
            db.commit()
            return None, "completed"

        template_id = queue.pop(0)
        session.queue = json.dumps(queue)
        db.commit()

        already = (
            db.query(UserImportedTemplate)
            .filter(
                UserImportedTemplate.user_id == user.id,
                UserImportedTemplate.template_id == template_id,
            )
            .first()
        )
        if already:
            continue

        template = db.get(JobTemplate, template_id)
        if not template:
            continue

        job = Job(
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
        db.add(job)
        db.add(UserImportedTemplate(user_id=user.id, template_id=template_id))
        db.commit()
        db.refresh(job)
        return job, "added"


def get_scrape_status(db: Session, user: User) -> dict:
    session = db.query(ScrapeSession).filter(ScrapeSession.user_id == user.id).first()
    imported = len(_imported_template_ids(db, user))
    total_templates = db.query(JobTemplate).count()
    remaining = 0
    is_active = False
    if session:
        is_active = session.is_active
        remaining = len(json.loads(session.queue or "[]"))
    return {
        "is_active": is_active,
        "remaining_in_queue": remaining,
        "imported_count": imported,
        "total_templates": total_templates,
        "available_templates": max(total_templates - imported, 0),
    }
