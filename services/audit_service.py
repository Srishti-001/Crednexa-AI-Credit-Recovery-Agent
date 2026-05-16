"""
Audit logging service — wraps audit_log model with convenience methods.
"""

from models.audit_log import create_audit_log, get_all_audit_logs, get_audit_logs_by_entity
from loguru import logger


def log_action(action: str, entity_type: str, entity_id: str = "",
               details: dict = None, performed_by: str = "Admin"):
    """Log an action to the audit trail."""
    try:
        create_audit_log(action, entity_type, entity_id, details, performed_by)
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")


def log_upload(filename: str, imported: int, skipped: int):
    """Log a file upload action."""
    log_action("Upload", "Invoice", details={
        "filename": filename, "imported": imported, "skipped": skipped
    })


def log_email_generated(email_id: str, client_id: str, tone: str):
    """Log email generation."""
    log_action("Generate", "Email", email_id, details={
        "client_id": client_id, "tone": tone
    })


def log_email_approved(email_id: str, approved_by: str = "Admin"):
    """Log email approval."""
    log_action("Approve", "Email", email_id, details={"approved_by": approved_by})


def log_email_rejected(email_id: str, reason: str = ""):
    """Log email rejection."""
    log_action("Reject", "Email", email_id, details={"reason": reason})


def log_email_sent(email_id: str, recipient: str):
    """Log email sent."""
    log_action("Send", "Email", email_id, details={"recipient": recipient})


def get_recent_activity(limit: int = 20) -> list:
    """Get recent audit activity."""
    return get_all_audit_logs(limit)


def get_entity_trail(entity_type: str, entity_id: str) -> list:
    """Get full audit trail for a specific entity."""
    return get_audit_logs_by_entity(entity_type, entity_id)
