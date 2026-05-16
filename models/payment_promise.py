"""
Payment promise model — CRUD operations for the payment_promises table.
"""

from database.connection import execute_query
from utils.helpers import generate_id
from datetime import datetime, date


def create_promise(client_id: str, promised_amount: float, promised_date: str,
                   invoice_id: str = None, source: str = "Email", notes: str = "") -> str:
    """Create a new payment promise. Returns promise_id."""
    promise_id = generate_id("PRM")
    execute_query(
        """INSERT INTO payment_promises (promise_id, client_id, invoice_id,
           promised_amount, promised_date, source, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (promise_id, client_id, invoice_id, promised_amount, promised_date, source, notes),
        fetch="none"
    )
    return promise_id


def get_promise(promise_id: str) -> dict:
    """Get a single promise by ID."""
    return execute_query(
        "SELECT * FROM payment_promises WHERE promise_id = ?", (promise_id,), fetch="one"
    )


def get_promises_by_client(client_id: str) -> list:
    """Get all promises for a client."""
    return execute_query(
        "SELECT * FROM payment_promises WHERE client_id = ? ORDER BY promised_date DESC",
        (client_id,)
    )


def get_all_promises() -> list:
    """Get all promises with client info."""
    return execute_query(
        """SELECT pp.*, c.company_name, c.contact_email
           FROM payment_promises pp JOIN clients c ON pp.client_id = c.client_id
           ORDER BY pp.promised_date ASC"""
    )


def get_pending_promises() -> list:
    """Get promises that are pending and past their date."""
    return execute_query(
        """SELECT pp.*, c.company_name, c.contact_email
           FROM payment_promises pp JOIN clients c ON pp.client_id = c.client_id
           WHERE pp.status = 'Pending'
           ORDER BY pp.promised_date ASC"""
    )


def get_broken_promises() -> list:
    """Get broken promises."""
    return execute_query(
        """SELECT pp.*, c.company_name
           FROM payment_promises pp JOIN clients c ON pp.client_id = c.client_id
           WHERE pp.status = 'Broken'
           ORDER BY pp.promised_date DESC"""
    )


def update_promise_status(promise_id: str, status: str, notes: str = "") -> None:
    """Update promise status."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query(
        "UPDATE payment_promises SET status = ?, notes = ?, updated_at = ? WHERE promise_id = ?",
        (status, notes, now, promise_id), fetch="none"
    )


def check_overdue_promises() -> list:
    """Find promises past due date that are still pending → mark as broken."""
    today = date.today().strftime("%Y-%m-%d")
    overdue = execute_query(
        """SELECT pp.*, c.company_name
           FROM payment_promises pp JOIN clients c ON pp.client_id = c.client_id
           WHERE pp.status = 'Pending' AND pp.promised_date < ?""",
        (today,)
    )
    for p in overdue:
        update_promise_status(p["promise_id"], "Broken", "Auto-marked: past promised date")
    return overdue


def get_promise_stats() -> dict:
    """Get promise statistics."""
    return execute_query(
        """SELECT
            COUNT(*) as total_promises,
            COUNT(CASE WHEN status = 'Fulfilled' THEN 1 END) as fulfilled,
            COUNT(CASE WHEN status = 'Broken' THEN 1 END) as broken,
            COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending,
            COALESCE(SUM(promised_amount), 0) as total_promised_amount,
            COALESCE(SUM(CASE WHEN status = 'Fulfilled' THEN promised_amount ELSE 0 END), 0) as fulfilled_amount
        FROM payment_promises""",
        fetch="one"
    )


def get_client_promise_reliability(client_id: str) -> float:
    """Calculate promise fulfillment rate for a client (0.0 to 1.0)."""
    stats = execute_query(
        """SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'Fulfilled' THEN 1 END) as fulfilled
        FROM payment_promises WHERE client_id = ?""",
        (client_id,), fetch="one"
    )
    if stats and stats["total"] > 0:
        return stats["fulfilled"] / stats["total"]
    return 1.0  # No promises = assume reliable
