import smtplib
from email.message import EmailMessage
from typing import Optional
from app.core.config import settings


def send_email(to: str, subject: str, body: str) -> None:
    """Send a simple email using SMTP. In tests this function should be mocked."""
    msg = EmailMessage()
    msg["Subject"] = subject
    # Set From header from MAIL_FROM setting (allows name + address)
    msg["From"] = getattr(settings, "MAIL_FROM", "noreply@example.com")
    msg["To"] = to
    msg.set_content(body)
    # Optionally set Reply-To for broadcasts
    reply_to = getattr(settings, "BROADCAST_REPLY_TO", None)
    if reply_to:
        msg["Reply-To"] = reply_to

    host = getattr(settings, "SMTP_HOST", None)
    port = getattr(settings, "SMTP_PORT", None)
    user = getattr(settings, "SMTP_USER", None)
    password = getattr(settings, "SMTP_PASSWORD", None)
    use_tls = getattr(settings, "SMTP_USE_TLS", True)

    if not host or not port:
        raise RuntimeError("SMTP host/port not configured")

    with smtplib.SMTP(host, int(port)) as server:
        # Upgrade to TLS if configured
        if use_tls:
            server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)
