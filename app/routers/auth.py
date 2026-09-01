from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services import gmail
from app.services.security import (
    create_access_token,
    generate_token,
    get_user_by_email,
    get_user_by_reset_token,
    get_user_by_verification_token,
    hash_password,
    is_expired,
    utcnow,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()

    if get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    token = generate_token()
    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        is_verified=False,
        verification_token=token,
        verification_token_expires=utcnow() + timedelta(hours=settings.verification_token_expire_hours),
    )
    db.add(user)
    db.commit()

    verify_url = f"{settings.frontend_url}/verify-email?token={token}"
    try:
        gmail.send_verification_email(email, verify_url)
    except Exception as exc:
        db.delete(user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to send verification email: {exc}",
        ) from exc

    return MessageResponse(message="Verification link sent to your Gmail. Please check your inbox and spam folder.")


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    user = get_user_by_verification_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification link")

    if is_expired(user.verification_token_expires):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link has expired")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    return MessageResponse(message="Email verified successfully. You can now log in.")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = get_user_by_email(db, email)

    if not user:
        return MessageResponse(
            message="If an unverified account exists for this email, a verification link has been sent. Please check your inbox and spam folder."
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified. You can log in.",
        )

    token = generate_token()
    user.verification_token = token
    user.verification_token_expires = utcnow() + timedelta(hours=settings.verification_token_expire_hours)
    db.commit()

    verify_url = f"{settings.frontend_url}/verify-email?token={token}"
    try:
        gmail.send_verification_email(email, verify_url)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to send verification email: {exc}",
        ) from exc

    return MessageResponse(
        message="Verification link sent to your Gmail. Please check your inbox and spam folder."
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email.lower())
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox for the verification link.",
        )

    return TokenResponse(access_token=create_access_token(user.email))


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = get_user_by_email(db, email)

    if user:
        token = generate_token()
        user.reset_token = token
        user.reset_token_expires = utcnow() + timedelta(hours=settings.reset_token_expire_hours)
        db.commit()

        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        try:
            gmail.send_password_reset_email(email, reset_url)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to send reset email: {exc}",
            ) from exc

    return MessageResponse(
        message="If an account exists for this email, a password reset link has been sent. Please check your inbox and spam folder."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_reset_token(db, payload.token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset link")

    if is_expired(user.reset_token_expires):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link has expired")

    user.hashed_password = hash_password(payload.password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return MessageResponse(message="Password reset successfully. You can now log in with your new password.")
