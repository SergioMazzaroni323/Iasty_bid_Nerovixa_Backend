import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings


def _get_gmail_service():
    if not all(
        [
            settings.gmail_client_id,
            settings.gmail_client_secret,
            settings.gmail_refresh_token,
            settings.gmail_sender_email,
        ]
    ):
        raise RuntimeError(
            "Gmail is not configured. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, "
            "GMAIL_REFRESH_TOKEN, and GMAIL_SENDER_EMAIL in backend/.env"
        )

    credentials = Credentials(
        token=None,
        refresh_token=settings.gmail_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )

    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def send_email(to_email: str, subject: str, html_body: str) -> None:
    message = MIMEText(html_body, "html")
    message["to"] = to_email
    message["from"] = settings.gmail_sender_email
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    service = _get_gmail_service()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_verification_email(to_email: str, verify_url: str) -> None:
    html = f"""
    <h2>Verify your email</h2>
    <p>Thanks for registering with Iasty Bid.</p>
    <p><a href="{verify_url}">Click here to verify your email</a></p>
    <p>This link expires in {settings.verification_token_expire_hours} hours.</p>
    <p>If you did not create an account, you can ignore this email.</p>
    """
    send_email(to_email, "Verify your Iasty Bid account", html)


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    html = f"""
    <h2>Reset your password</h2>
    <p>We received a request to reset your Iasty Bid password.</p>
    <p><a href="{reset_url}">Click here to reset your password</a></p>
    <p>This link expires in {settings.reset_token_expire_hours} hour(s).</p>
    <p>If you did not request this, you can ignore this email.</p>
    """
    send_email(to_email, "Reset your Iasty Bid password", html)
