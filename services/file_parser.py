"""
File parser service — CSV / Excel upload, validation, and database import.
──────────────────────────────────────────────────────────────
This is the *only* module that should know how to turn an uploaded
file into rows inside the invoices + clients tables.

Workflow:
  1. parse_uploaded_file()  → validate columns & data, return DataFrame
  2. import_invoices()      → iterate DataFrame, upsert clients, create invoices
  3. generate_sample_csv()  → produce a demo DataFrame for first-time users
"""

import pandas as pd
from datetime import datetime

# ─── optional: pretty logging ────────────────────────────────────────
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from utils.validators import validate_invoice_dataframe
from models.client import upsert_client, update_client_financials
from models.invoice import create_invoice, get_invoice_by_number
from services.audit_service import log_action


# ════════════════════════════════════════════════════════════════════════
# 1. PARSE — turn the uploaded file into a clean DataFrame
# ════════════════════════════════════════════════════════════════════════

def parse_uploaded_file(uploaded_file) -> dict:
    """
    Accept a Streamlit UploadedFile (CSV or Excel).

    Returns
    -------
    {
      "success": bool,
      "data":    pd.DataFrame | None,
      "errors":  list[str]
    }
    """
    try:
        filename = uploaded_file.name.lower()

        # --- read into DataFrame ----
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            return {
                "success": False,
                "data": None,
                "errors": ["Unsupported file format. Upload a .csv or .xlsx file."],
            }

        # --- normalise column names (lowercase, underscores) ----
        df.columns = [
            col.strip().lower().replace(" ", "_") for col in df.columns
        ]

        # --- structural & row-level validation ----
        validation = validate_invoice_dataframe(df)
        if not validation["valid"]:
            return {"success": False, "data": df, "errors": validation["errors"]}

        return {"success": True, "data": df, "errors": []}

    except Exception as exc:
        logger.error(f"File parsing error: {exc}")
        return {
            "success": False,
            "data": None,
            "errors": [f"Error reading file: {exc}"],
        }


# ════════════════════════════════════════════════════════════════════════
# 2. IMPORT — write validated DataFrame into the database
# ════════════════════════════════════════════════════════════════════════

def _safe_str(value, default: str = "") -> str:
    """Convert a possibly-NaN pandas value to a plain string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return str(value).strip()


def _safe_float(value, default: float = 0.0) -> float:
    """Convert a possibly-NaN value to float."""
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def _parse_date(value) -> str:
    """
    Best-effort conversion of any date-like value to 'YYYY-MM-DD'.
    Handles strings, datetime objects, numpy timestamps, etc.
    """
    try:
        dt = pd.to_datetime(value)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        # last resort: return as-is (will be caught by row-level error)
        return str(value).strip()


def import_invoices(df: pd.DataFrame) -> dict:
    """
    Walk through every row of a validated DataFrame and:
      • upsert the client (by company_name)
      • create the invoice (skip if invoice_number already exists)
      • recalculate client financial totals afterwards

    Returns
    -------
    {
      "imported": int,   — rows successfully inserted
      "skipped":  int,   — duplicate invoice_numbers
      "errors":   list[str]
    }
    """
    imported = 0
    skipped  = 0
    errors: list[str] = []
    touched_clients: set[str] = set()

    for idx, row in df.iterrows():
        row_label = f"Row {idx + 2}"  # +2 because idx is 0-based and row 1 is header
        try:
            inv_num = _safe_str(row.get("invoice_number"))
            if not inv_num:
                errors.append(f"{row_label}: invoice_number is blank — skipped")
                continue

            # ---- duplicate check ----
            if get_invoice_by_number(inv_num):
                skipped += 1
                continue

            # ---- upsert client ----
            client_id = upsert_client(
                company_name  = _safe_str(row.get("company_name")),
                contact_name  = _safe_str(row.get("contact_name")),
                contact_email = _safe_str(row.get("contact_email")),
                phone         = _safe_str(row.get("phone")),
                industry      = _safe_str(row.get("industry")),
            )
            touched_clients.add(client_id)

            # ---- create invoice ----
            create_invoice(
                client_id     = client_id,
                invoice_number= inv_num,
                amount        = _safe_float(row.get("amount")),
                issue_date    = _parse_date(row.get("issue_date")),
                due_date      = _parse_date(row.get("due_date")),
                amount_paid   = _safe_float(row.get("amount_paid")),
                currency      = _safe_str(row.get("currency"), "INR"),
                payment_terms = _safe_str(row.get("payment_terms")),
                notes         = _safe_str(row.get("notes")),
            )
            imported += 1

        except Exception as exc:
            errors.append(f"{row_label}: {exc}")
            logger.error(f"Import error at {row_label}: {exc}")

    # ---- recalculate every touched client's totals ----
    for cid in touched_clients:
        try:
            update_client_financials(cid)
        except Exception as exc:
            logger.error(f"Error updating financials for client {cid}: {exc}")

    # ---- audit log ----
    log_action(
        action="Upload",
        entity_type="Invoice",
        details={
            "imported": imported,
            "skipped": skipped,
            "errors_count": len(errors),
        },
    )

    return {"imported": imported, "skipped": skipped, "errors": errors}


# ════════════════════════════════════════════════════════════════════════
# 3. DEMO DATA
# ════════════════════════════════════════════════════════════════════════

def generate_sample_csv() -> pd.DataFrame:
    """
    Return a DataFrame with realistic Indian-market invoices.
    Prioritises loading sample_invoices.csv from the project root.
    """
    import os
    import config
    sample_path = config.BASE_DIR / "sample_invoices.csv"
    
    if sample_path.exists():
        try:
            return pd.read_csv(sample_path)
        except Exception as exc:
            logger.error(f"Error reading sample_invoices.csv: {exc}")

    # Fallback if file doesn't exist
    data = {
        "invoice_number": [
            "INV-2025-001", "INV-2025-002", "INV-2025-003", "INV-2025-004",
            "INV-2025-005", "INV-2025-006", "INV-2025-007", "INV-2025-008",
            "INV-2025-009", "INV-2025-010",
        ],
        "company_name": [
            "Acme Corp", "TechVista Solutions", "Global Traders Ltd",
            "Pinnacle Industries", "Quantum Dynamics", "Acme Corp",
            "Nexus Enterprises", "TechVista Solutions", "Summit Holdings",
            "Pinnacle Industries",
        ],
        "contact_name": [
            "Rajesh Sharma", "Priya Patel", "Amit Verma",
            "Sneha Gupta", "Vikram Singh", "Rajesh Sharma",
            "Neha Kapoor", "Priya Patel", "Arjun Mehta",
            "Sneha Gupta",
        ],
        "contact_email": [
            "rajesh@acme.com", "priya@techvista.com", "amit@globaltraders.com",
            "sneha@pinnacle.com", "vikram@quantum.com", "rajesh@acme.com",
            "neha@nexus.com", "priya@techvista.com", "arjun@summit.com",
            "sneha@pinnacle.com",
        ],
        "phone": [
            "+91-9876543210", "+91-9876543211", "+91-9876543212",
            "+91-9876543213", "+91-9876543214", "+91-9876543210",
            "+91-9876543215", "+91-9876543211", "+91-9876543216",
            "+91-9876543213",
        ],
        "industry": [
            "Manufacturing", "Technology", "Trading", "Construction",
            "Technology", "Manufacturing", "Services", "Technology",
            "Finance", "Construction",
        ],
        "amount": [
            250000, 180000, 420000, 95000, 310000,
            175000, 88000, 225000, 560000, 145000,
        ],
        "amount_paid": [
            0, 50000, 0, 0, 100000,
            0, 88000, 0, 200000, 50000,
        ],
        "issue_date": [
            "2025-01-15", "2025-02-01", "2024-12-10", "2025-03-01",
            "2024-11-20", "2025-03-15", "2025-04-01", "2025-01-10",
            "2024-10-01", "2025-02-15",
        ],
        "due_date": [
            "2025-02-15", "2025-03-01", "2025-01-10", "2025-04-01",
            "2024-12-20", "2025-04-15", "2025-05-01", "2025-02-10",
            "2024-11-01", "2025-03-15",
        ],
        "currency": ["INR"] * 10,
        "payment_terms": ["Net 30"] * 10,
    }
    return pd.DataFrame(data)
