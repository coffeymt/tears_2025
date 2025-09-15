import smtplib
from email.message import EmailMessage
from typing import Optional
from app.core.config import settings


def send_email(to: str, subject: str, body: str) -> None:
    """Send a simple email using SMTP. In tests this function should be mocked."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = getattr(settings, "SMTP_FROM", "noreply@example.com")
    msg["To"] = to
    msg.set_content(body)

    host = getattr(settings, "SMTP_HOST", None)
    port = getattr(settings, "SMTP_PORT", None)
    user = getattr(settings, "SMTP_USER", None)
    password = getattr(settings, "SMTP_PASSWORD", None)

    if not host or not port:
        raise RuntimeError("SMTP host/port not configured")

    with smtplib.SMTP(host, int(port)) as server:
        if user and password:
            server.starttls()
            server.login(user, password)
        server.send_message(msg)
