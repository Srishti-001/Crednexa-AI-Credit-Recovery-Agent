"""
Client model — CRUD operations for the clients table.
──────────────────────────────────────────────────────────────
Every function talks to SQLite through database.connection helpers.
No raw SQL outside this file should touch the clients table.
"""

from database.connection import execute_query
from utils.helpers import generate_id
from datetime import datetime


# ════════════════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════════════════

def create_client(
    company_name: str,
    contact_name: str = "",
    contact_email: str = "",
    phone: str = "",
    industry: str = "",
    notes: str = "",
) -> str:
    """Insert a new client row. Returns the generated client_id."""
    client_id = generate_id("CLI")
    execute_query(
        """INSERT INTO clients
           (client_id, company_name, contact_name, contact_email, phone, industry, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (client_id, company_name, contact_name, contact_email, phone, industry, notes),
        fetch="none",
    )
    return client_id


# ════════════════════════════════════════════════════════════════════════
# READ (single)
# ════════════════════════════════════════════════════════════════════════

def get_client(client_id: str) -> dict | None:
    """Return one client dict by its ID, or None."""
    return execute_query(
        "SELECT * FROM clients WHERE client_id = ?", (client_id,), fetch="one"
    )


def get_client_by_email(email: str) -> dict | None:
    """Lookup by contact_email (first match)."""
    return execute_query(
        "SELECT * FROM clients WHERE contact_email = ?", (email,), fetch="one"
    )


def get_client_by_company(company_name: str) -> dict | None:
    """Lookup by exact company_name (first match)."""
    return execute_query(
        "SELECT * FROM clients WHERE company_name = ?",
        (company_name,), fetch="one",
    )


# ════════════════════════════════════════════════════════════════════════
# READ (many)
# ════════════════════════════════════════════════════════════════════════

def get_all_clients() -> list[dict]:
    """Return every client, alphabetically by company_name."""
    return execute_query("SELECT * FROM clients ORDER BY company_name")


def get_clients_by_risk(risk_category: str) -> list[dict]:
    """Clients in a given risk bucket, highest outstanding first."""
    return execute_query(
        "SELECT * FROM clients WHERE risk_category = ? ORDER BY total_outstanding DESC",
        (risk_category,),
    )


def get_client_count() -> int:
    """Total number of client rows."""
    row = execute_query("SELECT COUNT(*) AS cnt FROM clients", fetch="one")
    return row["cnt"] if row else 0


# ════════════════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════════════════

def update_client(client_id: str, **kwargs) -> None:
    """
    Update any combination of allowed columns.

    Usage:
        update_client("CLI_abc123", total_outstanding=50000, risk_category="High")
    """
    allowed_cols = {
        "company_name", "contact_name", "contact_email", "phone",
        "industry", "total_outstanding", "total_paid",
        "invoices_count", "risk_category", "notes",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed_cols}
    if not updates:
        return

    updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [client_id]

    execute_query(
        f"UPDATE clients SET {set_clause} WHERE client_id = ?",
        tuple(values), fetch="none",
    )


def update_client_financials(client_id: str) -> None:
    """
    Re-aggregate invoice totals and write them back to the clients row.
    Call this after any invoice INSERT / UPDATE for the client.
    """
    stats = execute_query(
        """SELECT
               COUNT(*)                                              AS total_invoices,
               COALESCE(SUM(amount), 0)                              AS total_amount,
               COALESCE(SUM(amount_paid), 0)                         AS total_paid,
               COALESCE(SUM(
                   CASE WHEN status IN ('Pending','Overdue','Partially Paid')
                        THEN amount - amount_paid
                        ELSE 0
                   END
               ), 0)                                                 AS total_outstanding
           FROM invoices
           WHERE client_id = ?""",
        (client_id,), fetch="one",
    )
    if stats:
        update_client(
            client_id,
            invoices_count=stats["total_invoices"],
            total_paid=stats["total_paid"],
            total_outstanding=stats["total_outstanding"],
        )


# ════════════════════════════════════════════════════════════════════════
# UPSERT  (insert-or-return-existing)
# ════════════════════════════════════════════════════════════════════════

def upsert_client(
    company_name: str,
    contact_name: str = "",
    contact_email: str = "",
    phone: str = "",
    industry: str = "",
) -> str:
    """
    If a client with this company_name already exists → return its ID.
    Otherwise create a new row and return the new ID.
    """
    existing = get_client_by_company(company_name)
    if existing:
        # optionally update contact info if the existing row is blank
        if contact_email and not existing.get("contact_email"):
            update_client(existing["client_id"], contact_email=contact_email)
        if contact_name and not existing.get("contact_name"):
            update_client(existing["client_id"], contact_name=contact_name)
        return existing["client_id"]
    return create_client(company_name, contact_name, contact_email, phone, industry)


# ════════════════════════════════════════════════════════════════════════
# DELETE (with manual cascade)
# ════════════════════════════════════════════════════════════════════════

def delete_client(client_id: str) -> None:
    """Remove a client and all related rows (invoices, emails, etc.)."""
    for table in ("invoices", "email_logs", "payment_promises",
                  "risk_scores", "recovery_strategies"):
        execute_query(
            f"DELETE FROM {table} WHERE client_id = ?",
            (client_id,), fetch="none",
        )
    execute_query(
        "DELETE FROM clients WHERE client_id = ?",
        (client_id,), fetch="none",
    )
