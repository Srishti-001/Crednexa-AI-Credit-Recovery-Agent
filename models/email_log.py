"""
Email log model — CRUD operations for the email_logs table.
"""

from database.connection import execute_query
from utils.helpers import generate_id
from datetime import datetime


def create_email_log(client_id: str, subject: str, body: str, tone: str,
                     tone_level: int = 1, invoice_id: str = None,
                     ai_model_used: str = "", detected_emotion: str = "",
                     confidence_score: float = 0.0) -> str:
    """Create a new email log entry. Returns email_id."""
    email_id = generate_id("EML")
    execute_query(
        """INSERT INTO email_logs (email_id, invoice_id, client_id, subject, body, tone,
           tone_level, status, ai_model_used, detected_emotion, confidence_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'Draft', ?, ?, ?)""",
        (email_id, invoice_id, client_id, subject, body, tone, tone_level,
         ai_model_used, detected_emotion, confidence_score),
        fetch="none"
    )
    return email_id


def get_email_log(email_id: str) -> dict:
    """Get a single email log by ID."""
    return execute_query("SELECT * FROM email_logs WHERE email_id = ?", (email_id,), fetch="one")


def get_emails_by_client(client_id: str) -> list:
    """Get all emails for a client."""
    return execute_query(
        "SELECT * FROM email_logs WHERE client_id = ? ORDER BY created_at DESC",
        (client_id,)
    )


def get_emails_by_status(status: str) -> list:
    """Get emails by status with client info."""
    return execute_query(
        """SELECT e.*, c.company_name, c.contact_email
           FROM email_logs e JOIN clients c ON e.client_id = c.client_id
           WHERE e.status = ? ORDER BY e.created_at DESC""",
        (status,)
    )


def get_pending_approvals() -> list:
    """Get all emails pending approval."""
    return get_emails_by_status("Pending Approval")


def get_draft_emails() -> list:
    """Get all draft emails."""
    return get_emails_by_status("Draft")


def update_email_status(email_id: str, status: str, approved_by: str = None) -> None:
    """Update email status."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status == "Approved":
        execute_query(
            "UPDATE email_logs SET status = ?, approved_by = ?, approved_at = ? WHERE email_id = ?",
            (status, approved_by or "Admin", now, email_id), fetch="none"
        )
    elif status == "Sent":
        execute_query(
            "UPDATE email_logs SET status = ?, sent_at = ?, send_status = 'Success' WHERE email_id = ?",
            (status, now, email_id), fetch="none"
        )
    else:
        execute_query(
            "UPDATE email_logs SET status = ? WHERE email_id = ?",
            (status, email_id), fetch="none"
        )


def update_email_content(email_id: str, subject: str = None, body: str = None) -> None:
    """Update email subject and/or body."""
    if subject:
        execute_query(
            "UPDATE email_logs SET subject = ? WHERE email_id = ?",
            (subject, email_id), fetch="none"
        )
    if body:
        execute_query(
            "UPDATE email_logs SET body = ? WHERE email_id = ?",
            (body, email_id), fetch="none"
        )


def get_email_stats() -> dict:
    """Get email statistics."""
    return execute_query(
        """SELECT
            COUNT(*) as total_emails,
            COUNT(CASE WHEN status = 'Sent' THEN 1 END) as sent_count,
            COUNT(CASE WHEN status = 'Pending Approval' THEN 1 END) as pending_count,
            COUNT(CASE WHEN status = 'Draft' THEN 1 END) as draft_count,
            COUNT(CASE WHEN status = 'Rejected' THEN 1 END) as rejected_count
        FROM email_logs""",
        fetch="one"
    )


def get_tone_distribution() -> list:
    """Get distribution of tones used in sent emails."""
    return execute_query(
        """SELECT tone, COUNT(*) as count
           FROM email_logs WHERE status = 'Sent'
           GROUP BY tone ORDER BY count DESC"""
    )
