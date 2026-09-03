from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.services.security import decode_access_token, get_user_by_email

security = HTTPBearer()


def ensure_admin_privileges(user: User) -> bool:
    """Promote the configured admin email. Returns True if the user row changed."""
    if user.email.lower() != settings.admin_email.lower():
        return False

    changed = False
    if user.role != UserRole.admin:
        user.role = UserRole.admin
        changed = True
    if user.status != UserStatus.active:
        user.status = UserStatus.active
        changed = True
    if not user.is_verified:
        user.is_verified = True
        changed = True
    return changed


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    email = decode_access_token(credentials.credentials)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if ensure_admin_privileges(user):
        db.add(user)
        db.commit()
        db.refresh(user)

    if user.status != UserStatus.active:
        detail = (
            "Your account is pending admin approval."
            if user.status == UserStatus.pending
            else "Your account has been deactivated."
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin and current_user.email.lower() != settings.admin_email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
