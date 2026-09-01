from sqlalchemy.orm import Session

from app.models.job import EmploymentType, Job, WorkMode
from app.models.real_job import RealJob
from app.models.scrape_session import UserImportedRealJob
from app.models.user import User

REAL_JOB_DEFINITIONS = [
    {
        "job_title": "Software Engineer - Full Stack",
        "company_name": "Figma",
        "job_link": "https://job-boards.greenhouse.io/figma/jobs/5691911004?gh_jid=5691911004&gh_src=28109e334us",
        "job_description": (
            "Build high-quality features across the stack for Figma's design and collaboration platform. "
            "Work with React/TypeScript, Ruby, Python, Go, and PostgreSQL to ship polished front-end "
            "experiences and scalable back-end systems. Collaborate with Product, Design, Research, and Data."
        ),
        "required_role": "Full Stack Engineer",
        "required_locations": "San Francisco, CA; New York, NY; United States (Remote)",
        "work_mode": WorkMode.remote,
        "employment_type": EmploymentType.full_time,
        "salary_expected": "$153,000 - $376,000",
        "industry": "Technology",
    },
    {
        "job_title": "Sr AI Engineer - Product",
        "company_name": "MeridianLink",
        "job_link": "https://jobs.ashbyhq.com/meridianlink/f2e6be30-4b89-4adf-897e-ea5e36678917/application?utm_source=LinkedInPaid",
        "job_description": (
            "Build financial products on Meridianlink Coach for credit union members. "
            "Own full-stack features using React 19, TypeScript, Hono, Drizzle/Postgres, and AWS. "
            "Work with AI agents in the engineering workflow and integrate APIs such as OpenAI or Anthropic Claude."
        ),
        "required_role": "Senior AI Engineer",
        "required_locations": "US Remote",
        "work_mode": WorkMode.remote,
        "employment_type": EmploymentType.full_time,
        "salary_expected": "$126,000 - $214,900",
        "industry": "FinTech",
    },
]


def _apply_template_fields(job: Job | RealJob, data: dict) -> None:
    job.job_title = data["job_title"]
    job.company_name = data["company_name"]
    job.job_link = data["job_link"]
    job.job_description = data["job_description"]
    job.required_role = data["required_role"]
    job.required_locations = data["required_locations"]
    job.work_mode = data["work_mode"]
    job.employment_type = data["employment_type"]
    job.salary_expected = data["salary_expected"]
    job.industry = data["industry"]


def seed_real_jobs(db: Session) -> None:
    valid_links = {item["job_link"] for item in REAL_JOB_DEFINITIONS}

    for data in REAL_JOB_DEFINITIONS:
        existing = db.query(RealJob).filter(RealJob.job_link == data["job_link"]).first()
        if existing:
            _apply_template_fields(existing, data)
        else:
            db.add(RealJob(**data))

    obsolete = db.query(RealJob).filter(~RealJob.job_link.in_(valid_links)).all()
    for old in obsolete:
        imports = db.query(UserImportedRealJob).filter(UserImportedRealJob.real_job_id == old.id).all()
        for imp in imports:
            db.query(Job).filter(
                Job.user_id == imp.user_id,
                Job.is_real.is_(True),
                Job.company_name == old.company_name,
                Job.job_title == old.job_title,
            ).delete(synchronize_session=False)
            db.delete(imp)
        db.delete(old)

    db.commit()
    _sync_imported_user_jobs(db)


def _sync_imported_user_jobs(db: Session) -> None:
    for imp in db.query(UserImportedRealJob).all():
        template = db.get(RealJob, imp.real_job_id)
        if not template:
            continue

        job = (
            db.query(Job)
            .filter(
                Job.user_id == imp.user_id,
                Job.is_real.is_(True),
                Job.job_link == template.job_link,
            )
            .first()
        )
        if job:
            _apply_template_fields(job, {
                "job_title": template.job_title,
                "company_name": template.company_name,
                "job_link": template.job_link,
                "job_description": template.job_description,
                "required_role": template.required_role,
                "required_locations": template.required_locations,
                "work_mode": template.work_mode,
                "employment_type": template.employment_type,
                "salary_expected": template.salary_expected,
                "industry": template.industry,
            })

    db.commit()


def get_user_real_jobs(db: Session, user: User) -> list[Job]:
    return (
        db.query(Job)
        .filter(Job.user_id == user.id, Job.is_real.is_(True))
        .order_by(Job.id.asc())
        .all()
    )


def import_real_jobs_for_user(db: Session, user: User) -> list[Job]:
    imported_real_ids = {
        row[0]
        for row in db.query(UserImportedRealJob.real_job_id)
        .filter(UserImportedRealJob.user_id == user.id)
        .all()
    }

    for real_job in db.query(RealJob).order_by(RealJob.id.asc()).all():
        if real_job.id in imported_real_ids:
            existing = (
                db.query(Job)
                .filter(
                    Job.user_id == user.id,
                    Job.is_real.is_(True),
                    Job.job_link == real_job.job_link,
                )
                .first()
            )
            if existing:
                _apply_template_fields(existing, {
                    "job_title": real_job.job_title,
                    "company_name": real_job.company_name,
                    "job_link": real_job.job_link,
                    "job_description": real_job.job_description,
                    "required_role": real_job.required_role,
                    "required_locations": real_job.required_locations,
                    "work_mode": real_job.work_mode,
                    "employment_type": real_job.employment_type,
                    "salary_expected": real_job.salary_expected,
                    "industry": real_job.industry,
                })
            continue

        job = Job(
            user_id=user.id,
            job_title=real_job.job_title,
            company_name=real_job.company_name,
            job_link=real_job.job_link,
            job_description=real_job.job_description,
            required_role=real_job.required_role,
            required_locations=real_job.required_locations,
            work_mode=real_job.work_mode,
            employment_type=real_job.employment_type,
            salary_expected=real_job.salary_expected,
            industry=real_job.industry,
            is_real=True,
        )
        db.add(job)
        db.flush()
        db.add(UserImportedRealJob(user_id=user.id, real_job_id=real_job.id))
        imported_real_ids.add(real_job.id)

    db.commit()
    return get_user_real_jobs(db, user)
