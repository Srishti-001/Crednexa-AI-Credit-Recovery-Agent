"""
Approval workflow service — manages human-in-the-loop email approval pipeline.
"""

from loguru import logger
from models.email_log import (
    get_pending_approvals, get_email_log, update_email_status, update_email_content
)
from models.client import get_client
from services.email_sender import send_email
from services.audit_service import log_email_approved, log_email_rejected, log_email_sent


def submit_for_approval(email_id: str) -> bool:
    """Submit a draft email for human approval."""
    try:
        update_email_status(email_id, "Pending Approval")
        return True
    except Exception as e:
        logger.error(f"Failed to submit for approval: {e}")
        return False


def approve_email(email_id: str, approved_by: str = "Admin") -> dict:
    """
    Approve an email and optionally send it immediately.
    Returns {'success': bool, 'message': str}.
    """
    try:
        email = get_email_log(email_id)
        if not email:
            return {"success": False, "message": "Email not found"}

        update_email_status(email_id, "Approved", approved_by)
        log_email_approved(email_id, approved_by)

        return {"success": True, "message": "Email approved successfully"}
    except Exception as e:
        logger.error(f"Approval failed: {e}")
        return {"success": False, "message": str(e)}


def reject_email(email_id: str, reason: str = "") -> dict:
    """Reject an email with optional reason."""
    try:
        update_email_status(email_id, "Rejected")
        log_email_rejected(email_id, reason)
        return {"success": True, "message": "Email rejected"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def approve_and_send(email_id: str, approved_by: str = "Admin") -> dict:
    """Approve and immediately send an email."""
    try:
        email = get_email_log(email_id)
        if not email:
            return {"success": False, "message": "Email not found"}

        # Get client email
        client = get_client(email["client_id"])
        to_email = client.get("contact_email", "") if client else ""

        if not to_email:
            return {"success": False, "message": "Client email not found"}

        # Approve
        update_email_status(email_id, "Approved", approved_by)
        log_email_approved(email_id, approved_by)

        # Send
        result = send_email(to_email, email["subject"], email["body"])
        if result["success"]:
            update_email_status(email_id, "Sent")
            log_email_sent(email_id, to_email)
            return {"success": True, "message": f"Email approved and sent to {to_email}"}
        else:
            update_email_status(email_id, "Failed")
            return {"success": False, "message": f"Approved but send failed: {result['message']}"}

    except Exception as e:
        logger.error(f"Approve & send failed: {e}")
        return {"success": False, "message": str(e)}


def edit_and_resubmit(email_id: str, subject: str = None, body: str = None) -> bool:
    """Edit email content and resubmit for approval."""
    try:
        update_email_content(email_id, subject, body)
        update_email_status(email_id, "Pending Approval")
        return True
    except Exception as e:
        logger.error(f"Edit/resubmit failed: {e}")
        return False


def get_approval_queue() -> list:
    """Get all emails awaiting approval."""
    return get_pending_approvals()
