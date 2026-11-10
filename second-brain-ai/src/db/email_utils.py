"""
Email sending for password resets.
Uses SMTP if configured via environment variables. If not configured,
logs the reset link to the console instead — so local development
works immediately without any email setup.
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def is_smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_password_reset_email(to_email: str, username: str, token: str) -> bool:
    """
    Send a password reset email with a link containing the token.
    Returns True if sent (or logged in dev mode), False on failure.
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    if not is_smtp_configured():
        # Dev fallback — no SMTP configured, just log the link so
        # developers can test the flow without setting up email.
        logger.warning(
            "SMTP not configured — password reset link for %s (%s):\n%s",
            username, to_email, reset_link
        )
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset your NoteMind password"
        msg["From"] = SMTP_FROM
        msg["To"] = to_email

        text = (
            f"Hi {username},\n\n"
            f"Someone requested a password reset for your account.\n"
            f"Click the link below to set a new password (valid for 30 minutes):\n\n"
            f"{reset_link}\n\n"
            f"If you didn't request this, you can safely ignore this email."
        )
        html = f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
            <h2>🧠 Reset your password</h2>
            <p>Hi {username},</p>
            <p>Someone requested a password reset for your NoteMind account.</p>
            <p>
                <a href="{reset_link}"
                   style="display:inline-block; padding:12px 24px; background:#6366f1;
                          color:#fff; text-decoration:none; border-radius:8px; font-weight:600;">
                    Reset Password
                </a>
            </p>
            <p style="color:#888; font-size:13px;">This link expires in 30 minutes.
            If you didn't request this, you can safely ignore this email.</p>
        </div>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Password reset email sent to %s", to_email)
        return True

    except Exception as e:
        logger.error("Failed to send password reset email to %s: %s", to_email, e)
        return False