"""
Audit log model — CRUD operations for the audit_logs table.
"""

from database.connection import execute_query
from utils.helpers import generate_id
import json


def create_audit_log(user_action: str, entity_type: str, entity_id: str = "",
                     details: dict = None, performed_by: str = "System") -> str:
    """Create an audit log entry. Returns log_id."""
    log_id = generate_id("AUD")
    details_json = json.dumps(details) if details else ""
    execute_query(
        """INSERT INTO audit_logs (log_id, user_action, entity_type, entity_id,
           details, performed_by) VALUES (?, ?, ?, ?, ?, ?)""",
        (log_id, user_action, entity_type, entity_id, details_json, performed_by),
        fetch="none"
    )
    return log_id


def get_all_audit_logs(limit: int = 100) -> list:
    """Get recent audit logs."""
    return execute_query(
        "SELECT * FROM audit_logs ORDER BY performed_at DESC LIMIT ?",
        (limit,)
    )


def get_audit_logs_by_entity(entity_type: str, entity_id: str) -> list:
    """Get audit trail for a specific entity."""
    return execute_query(
        """SELECT * FROM audit_logs
           WHERE entity_type = ? AND entity_id = ?
           ORDER BY performed_at DESC""",
        (entity_type, entity_id)
    )


def get_audit_logs_by_action(action: str, limit: int = 50) -> list:
    """Get audit logs by action type."""
    return execute_query(
        "SELECT * FROM audit_logs WHERE user_action = ? ORDER BY performed_at DESC LIMIT ?",
        (action, limit)
    )


def get_audit_logs_by_date_range(start_date: str, end_date: str) -> list:
    """Get audit logs within a date range."""
    return execute_query(
        """SELECT * FROM audit_logs
           WHERE DATE(performed_at) BETWEEN ? AND ?
           ORDER BY performed_at DESC""",
        (start_date, end_date)
    )


def get_audit_summary() -> list:
    """Get summary of actions grouped by action type."""
    return execute_query(
        """SELECT user_action, COUNT(*) as count
           FROM audit_logs GROUP BY user_action ORDER BY count DESC"""
    )
