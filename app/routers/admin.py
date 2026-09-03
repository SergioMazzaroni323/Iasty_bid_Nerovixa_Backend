from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_admin
from app.models.job import Job
from app.models.scrape_session import ScrapeSession, UserImportedRealJob, UserImportedTemplate
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import MessageResponse, UserResponse
from app.services import gmail
from app.services.security import generate_token, hash_password, utcnow

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminUserResponse(UserResponse):
    created_at: str | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int


class UpdateStatusRequest(BaseModel):
    status: UserStatus


class AdminResetPasswordRequest(BaseModel):
    password: str | None = None


def _serialize_user(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        is_verified=user.is_verified,
        role=user.role,
        status=user.status,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return AdminUserListResponse(
        items=[_serialize_user(user) for user in users],
        total=len(users),
    )


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
def update_user_status(
    user_id: int,
    payload: UpdateStatusRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.email.lower() == settings.admin_email.lower() and payload.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the primary admin account status",
        )

    if payload.status == UserStatus.active and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot activate an unverified account",
        )

    user.status = payload.status
    if user.email.lower() == settings.admin_email.lower():
        user.role = UserRole.admin
        user.status = UserStatus.active

    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
def admin_reset_password(
    user_id: int,
    payload: AdminResetPasswordRequest = AdminResetPasswordRequest(),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.password:
        if len(payload.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters",
            )
        user.hashed_password = hash_password(payload.password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        return MessageResponse(message="Password updated successfully.")

    token = generate_token()
    user.reset_token = token
    user.reset_token_expires = utcnow() + timedelta(hours=settings.reset_token_expire_hours)
    db.commit()

    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    try:
        gmail.send_password_reset_email(user.email, reset_url)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to send reset email: {exc}",
        ) from exc

    return MessageResponse(message="Password reset link sent to the user.")


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove your own account")

    if user.email.lower() == settings.admin_email.lower():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the primary admin account")

    db.query(Job).filter(Job.user_id == user.id).delete(synchronize_session=False)
    db.query(ScrapeSession).filter(ScrapeSession.user_id == user.id).delete(synchronize_session=False)
    db.query(UserImportedTemplate).filter(UserImportedTemplate.user_id == user.id).delete(synchronize_session=False)
    db.query(UserImportedRealJob).filter(UserImportedRealJob.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()

    return MessageResponse(message="Account removed.")
