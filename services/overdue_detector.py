"""
Overdue invoice detection and classification service.
──────────────────────────────────────────────────────────────
This service sits between the Streamlit pages and the invoice model.
It refreshes the live overdue_days / severity fields, then returns
the data grouped / summarised however the UI needs it.
"""

from models.invoice import (
    get_all_invoices,
    refresh_overdue_status,
    get_overdue_invoices,
)
from utils.helpers import classify_severity

# ─── optional: pretty logging ────────────────────────────────────────
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# CORE — refresh + return overdue list
# ════════════════════════════════════════════════════════════════════════

def detect_overdue_invoices() -> list[dict]:
    """
    1. Refresh overdue_days / severity / status for every unpaid invoice.
    2. Return the list of currently-overdue invoices (sorted worst-first).
    """
    updated = refresh_overdue_status()
    logger.info(f"Refreshed overdue status for {updated} invoices")
    return get_overdue_invoices()


# ════════════════════════════════════════════════════════════════════════
# SUMMARY — aggregate stats for the Overdue page KPI cards
# ════════════════════════════════════════════════════════════════════════

def get_overdue_summary() -> dict:
    """
    Returns
    -------
    {
      "total_overdue":         int,
      "total_overdue_amount":  float,
      "avg_days_overdue":      float,
      "max_days_overdue":      int,
      "by_severity":   {"Low": [...], "Medium": [...], "High": [...], "Critical": [...]},
      "severity_counts": {"Low": N, "Medium": N, ...}
    }
    """
    overdue = detect_overdue_invoices()

    # --- base container ---
    summary: dict = {
        "total_overdue": len(overdue),
        "total_overdue_amount": 0.0,
        "avg_days_overdue": 0.0,
        "max_days_overdue": 0,
        "by_severity": {
            "Low": [],
            "Medium": [],
            "High": [],
            "Critical": [],
        },
        "severity_counts": {
            "Low": 0,
            "Medium": 0,
            "High": 0,
            "Critical": 0,
        },
    }

    if not overdue:
        return summary

    # --- compute aggregates ---
    total_amount = 0.0
    total_days   = 0
    max_days     = 0

    for inv in overdue:
        outstanding = inv["amount"] - inv.get("amount_paid", 0)
        days = inv.get("overdue_days", 0)
        sev  = inv.get("severity") or classify_severity(days)

        total_amount += outstanding
        total_days   += days
        if days > max_days:
            max_days = days

        if sev in summary["by_severity"]:
            summary["by_severity"][sev].append(inv)

    summary["total_overdue_amount"] = total_amount
    summary["avg_days_overdue"]     = total_days / len(overdue)
    summary["max_days_overdue"]     = max_days
    summary["severity_counts"]      = {
        k: len(v) for k, v in summary["by_severity"].items()
    }

    return summary


# ════════════════════════════════════════════════════════════════════════
# GROUP BY CLIENT — used by email-generation pages
# ════════════════════════════════════════════════════════════════════════

def get_overdue_by_client() -> dict[str, dict]:
    """
    Return a dict keyed by client_id:
    {
      "CLI_abc": {
         "company_name": "…",
         "contact_email": "…",
         "invoices":      [dict, …],
         "total_overdue": float,
         "max_days":      int,
      }
    }
    """
    overdue = detect_overdue_invoices()
    by_client: dict[str, dict] = {}

    for inv in overdue:
        cid = inv["client_id"]
        if cid not in by_client:
            by_client[cid] = {
                "company_name":  inv.get("company_name", "Unknown"),
                "contact_email": inv.get("contact_email", ""),
                "invoices":      [],
                "total_overdue": 0.0,
                "max_days":      0,
            }
        outstanding = inv["amount"] - inv.get("amount_paid", 0)
        by_client[cid]["invoices"].append(inv)
        by_client[cid]["total_overdue"] += outstanding
        by_client[cid]["max_days"] = max(
            by_client[cid]["max_days"],
            inv.get("overdue_days", 0),
        )

    return by_client
