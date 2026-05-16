"""
Invoice model — CRUD operations for the invoices table.
──────────────────────────────────────────────────────────────
Handles:
  • create / read / update individual invoices
  • batch "refresh" of overdue_days & severity
  • aggregate stats for dashboards
"""

from database.connection import execute_query
from utils.helpers import generate_id, calculate_overdue_days, classify_severity
from datetime import datetime


# ════════════════════════════════════════════════════════════════════════
# INTERNAL HELPER
# ════════════════════════════════════════════════════════════════════════

def _determine_status(amount: float, amount_paid: float, overdue_days: int) -> str:
    """
    Derive the human-readable status from financial + time data.
    Order matters:  Paid → Partially Paid → Overdue → Pending
    """
    if amount_paid >= amount and amount > 0:
        return "Paid"
    elif amount_paid > 0:
        return "Partially Paid"
    elif overdue_days > 0:
        return "Overdue"
    else:
        return "Pending"


# ════════════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════════════

def create_invoice(
    client_id: str,
    invoice_number: str,
    amount: float,
    issue_date: str,
    due_date: str,
    amount_paid: float = 0.0,
    currency: str = "INR",
    payment_terms: str = "",
    notes: str = "",
) -> str:
    """
    Insert a new invoice.  Automatically calculates overdue_days,
    severity, and status from the due_date and amount_paid.
    Returns the generated invoice_id.
    """
    invoice_id = generate_id("INV")
    overdue_days = calculate_overdue_days(due_date)
    severity = classify_severity(overdue_days)
    status = _determine_status(amount, amount_paid, overdue_days)

    execute_query(
        """INSERT INTO invoices
           (invoice_id, client_id, invoice_number,
            amount, amount_paid, currency,
            issue_date, due_date,
            overdue_days, status, severity,
            payment_terms, notes)
           VALUES (?, ?, ?,
                   ?, ?, ?,
                   ?, ?,
                   ?, ?, ?,
                   ?, ?)""",
        (invoice_id, client_id, invoice_number,
         amount, amount_paid, currency,
         issue_date, due_date,
         overdue_days, status, severity,
         payment_terms, notes),
        fetch="none",
    )
    return invoice_id


# ════════════════════════════════════════════════════════════════════════
# READ — single
# ════════════════════════════════════════════════════════════════════════

def get_invoice(invoice_id: str) -> dict | None:
    """Get one invoice by its primary key."""
    return execute_query(
        "SELECT * FROM invoices WHERE invoice_id = ?",
        (invoice_id,), fetch="one",
    )


def get_invoice_by_number(invoice_number: str) -> dict | None:
    """Lookup by the user-facing invoice_number (UNIQUE column)."""
    return execute_query(
        "SELECT * FROM invoices WHERE invoice_number = ?",
        (invoice_number,), fetch="one",
    )


# ════════════════════════════════════════════════════════════════════════
# READ — many
# ════════════════════════════════════════════════════════════════════════

def get_all_invoices() -> list[dict]:
    """All invoices joined with client name / email, oldest-due first."""
    return execute_query(
        """SELECT i.*, c.company_name, c.contact_name, c.contact_email
           FROM invoices i
           JOIN clients c ON i.client_id = c.client_id
           ORDER BY i.due_date ASC"""
    )


def get_invoices_by_client(client_id: str) -> list[dict]:
    """Invoices for one client, newest-due first."""
    return execute_query(
        "SELECT * FROM invoices WHERE client_id = ? ORDER BY due_date DESC",
        (client_id,),
    )


def get_overdue_invoices() -> list[dict]:
    """
    All invoices whose status is Overdue *or* Partially Paid
    AND whose due_date is in the past.
    Sorted by overdue_days descending (worst offenders first).
    """
    return execute_query(
        """SELECT i.*, c.company_name, c.contact_name, c.contact_email
           FROM invoices i
           JOIN clients c ON i.client_id = c.client_id
           WHERE i.status IN ('Overdue', 'Partially Paid')
             AND i.due_date < date('now')
           ORDER BY i.overdue_days DESC"""
    )


def get_invoices_by_severity(severity: str) -> list[dict]:
    """Filter by severity level (Low / Medium / High / Critical)."""
    return execute_query(
        """SELECT i.*, c.company_name, c.contact_email
           FROM invoices i
           JOIN clients c ON i.client_id = c.client_id
           WHERE i.severity = ?
           ORDER BY i.overdue_days DESC""",
        (severity,),
    )


# ════════════════════════════════════════════════════════════════════════
# UPDATE — single
# ════════════════════════════════════════════════════════════════════════

def update_invoice(invoice_id: str, **kwargs) -> None:
    """
    Update any combination of allowed columns on one invoice.

    Usage:
        update_invoice("INV_abc", overdue_days=45, severity="Medium")
    """
    allowed_cols = {
        "amount", "amount_paid", "currency", "issue_date", "due_date",
        "overdue_days", "status", "severity", "payment_terms", "notes",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed_cols}
    if not updates:
        return

    updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [invoice_id]

    execute_query(
        f"UPDATE invoices SET {set_clause} WHERE invoice_id = ?",
        tuple(values), fetch="none",
    )


# ════════════════════════════════════════════════════════════════════════
# BATCH REFRESH  — recalculate overdue for all unpaid invoices
# ════════════════════════════════════════════════════════════════════════

def refresh_overdue_status() -> int:
    """
    Recalculate overdue_days, severity, and status for every invoice
    that is NOT Paid / Written Off.
    Returns the number of invoices touched.
    """
    rows = execute_query(
        """SELECT invoice_id, due_date, amount, amount_paid
           FROM invoices
           WHERE status NOT IN ('Paid', 'Written Off')"""
    )
    count = 0
    for row in rows:
        days = calculate_overdue_days(row["due_date"])
        sev  = classify_severity(days)
        stat = _determine_status(row["amount"], row["amount_paid"], days)
        update_invoice(
            row["invoice_id"],
            overdue_days=days,
            severity=sev,
            status=stat,
        )
        count += 1
    return count


# ════════════════════════════════════════════════════════════════════════
# AGGREGATE STATS — for dashboards
# ════════════════════════════════════════════════════════════════════════

def get_invoice_stats() -> dict:
    """
    Single-row summary used by the dashboard.
    Returns keys:
        total_invoices, total_amount, total_collected, total_overdue,
        overdue_count, paid_count, avg_overdue_days
    """
    return execute_query(
        """SELECT
               COUNT(*)                                            AS total_invoices,
               COALESCE(SUM(amount), 0)                            AS total_amount,
               COALESCE(SUM(amount_paid), 0)                       AS total_collected,

               COALESCE(SUM(
                   CASE WHEN status IN ('Overdue','Partially Paid')
                        THEN amount - amount_paid
                        ELSE 0
                   END
               ), 0)                                               AS total_overdue,

               COUNT(CASE WHEN status IN ('Overdue','Partially Paid')
                     THEN 1 END)                                   AS overdue_count,

               COUNT(CASE WHEN status = 'Paid' THEN 1 END)        AS paid_count,

               COALESCE(AVG(
                   CASE WHEN overdue_days > 0 THEN overdue_days END
               ), 0)                                               AS avg_overdue_days

           FROM invoices""",
        fetch="one",
    )
