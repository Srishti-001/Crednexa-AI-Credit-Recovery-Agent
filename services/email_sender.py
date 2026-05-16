"""
Email sender service — handles SMTP email dispatch.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
import config


def send_email(to_email: str, subject: str, body: str, is_html: bool = False) -> dict:
    """
    Send an email via SMTP.
    Returns {'success': bool, 'message': str}.
    """
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        logger.warning("SMTP not configured — simulating email send")
        return {"success": True, "message": "Email simulated (SMTP not configured)"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config.EMAIL_FROM
        msg["To"] = to_email

        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type))

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}: {subject}")
        return {"success": True, "message": f"Email sent to {to_email}"}

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed")
        return {"success": False, "message": "Email authentication failed. Check SMTP credentials."}
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return {"success": False, "message": f"SMTP error: {str(e)}"}
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}


def is_configured() -> bool:
    """Check if SMTP is properly configured."""
    return bool(
        config.SMTP_USER and config.SMTP_PASSWORD
        and config.SMTP_USER != "your_email@gmail.com"
    )
