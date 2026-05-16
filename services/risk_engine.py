"""
Risk Engine — multi-factor client risk scoring and prioritisation.
──────────────────────────────────────────────────────────────
Combines overdue amounts, days, payment history & broken promises
into a single 0-100 risk score with automatic category labelling.

Also produces the Priority Recovery Queue used by page 9.
"""

import json
from datetime import datetime

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

import config
from database.connection import init_db
from utils.helpers import calculate_risk_score, categorize_risk
from models.client import get_all_clients, update_client
from models.invoice import get_invoices_by_client
from models.risk_score import create_risk_score, get_latest_risk_score, get_all_latest_risk_scores
from models.payment_promise import get_promises_by_client


# ════════════════════════════════════════════════════════════════════════
# SINGLE-CLIENT RISK CALCULATION
# ════════════════════════════════════════════════════════════════════════

def calculate_client_risk(client_id: str) -> dict:
    """
    Compute a composite risk score (0-100) for one client.

    Factors
    -------
    • Overdue amount (weight 30%)
    • Average overdue days (weight 25%)
    • Payment reliability — ratio of overdue vs total invoices (20%)
    • Broken-promise ratio (15%)
    • Base factor from count of overdue invoices (10%)

    Returns  { risk_score, risk_category, contributing_factors,
               payment_reliability, avg_days_overdue, overdue_count }
    """
    init_db()

    invoices = get_invoices_by_client(client_id)
    if not invoices:
        return _empty_result()

    # --- partition invoices ---
    overdue = [i for i in invoices if i["status"] in ("Overdue", "Partially Paid")]
    overdue_amount = sum(i["amount"] - i.get("amount_paid", 0) for i in overdue)
    overdue_days_list = [i.get("overdue_days", 0) for i in overdue if i.get("overdue_days", 0) > 0]
    avg_days = sum(overdue_days_list) / len(overdue_days_list) if overdue_days_list else 0

    # --- promises ---
    promises = get_promises_by_client(client_id)
    broken   = sum(1 for p in promises if p.get("status") == "Broken")
    total_p  = len(promises)

    # --- composite score ---
    score = calculate_risk_score(
        overdue_amount=overdue_amount,
        avg_overdue_days=avg_days,
        total_invoices=len(invoices),
        overdue_invoices=len(overdue),
        broken_promises=broken,
        total_promises=total_p,
    )

    category = categorize_risk(score)
    reliability = 1.0 - (len(overdue) / len(invoices)) if invoices else 1.0

    factors = {
        "overdue_amount": round(overdue_amount, 2),
        "avg_overdue_days": round(avg_days, 1),
        "overdue_invoice_count": len(overdue),
        "total_invoices": len(invoices),
        "broken_promises": broken,
        "total_promises": total_p,
        "payment_reliability": round(reliability, 2),
    }

    # --- persist ---
    create_risk_score(
        client_id=client_id,
        risk_score=round(score, 2),
        risk_category=category,
        contributing_factors=factors,
        payment_reliability=reliability,
        avg_days_overdue=avg_days,
        total_overdue_count=len(overdue),
    )
    update_client(client_id, risk_category=category)

    return {
        "risk_score": round(score, 2),
        "risk_category": category,
        "contributing_factors": factors,
        "payment_reliability": round(reliability, 2),
        "avg_days_overdue": round(avg_days, 1),
        "overdue_count": len(overdue),
    }


def _empty_result() -> dict:
    return {
        "risk_score": 0, "risk_category": "Low",
        "contributing_factors": {}, "payment_reliability": 1.0,
        "avg_days_overdue": 0, "overdue_count": 0,
    }


# ════════════════════════════════════════════════════════════════════════
# BATCH — recalculate all clients
# ════════════════════════════════════════════════════════════════════════

def recalculate_all_risks() -> dict:
    """
    Walk through every client, recalculate risk, persist scores.
    Returns { "updated": int, "results": [{ client_id, risk_score, … }] }
    """
    init_db()
    clients = get_all_clients()
    results = []
    for c in clients:
        try:
            r = calculate_client_risk(c["client_id"])
            r["client_id"] = c["client_id"]
            r["company_name"] = c["company_name"]
            results.append(r)
        except Exception as exc:
            logger.error(f"Risk calc failed for {c['company_name']}: {exc}")

    return {"updated": len(results), "results": results}


# ════════════════════════════════════════════════════════════════════════
# PRIORITY RECOVERY QUEUE
# ════════════════════════════════════════════════════════════════════════

def get_priority_queue() -> list[dict]:
    """
    Ranked list of clients needing recovery action.

    Priority Score = risk_score * 0.4
                   + normalised_days * 0.3
                   + normalised_amount * 0.3
    """
    init_db()
    clients = get_all_clients()
    queue: list[dict] = []

    for c in clients:
        invoices = get_invoices_by_client(c["client_id"])
        overdue  = [i for i in invoices if i["status"] in ("Overdue", "Partially Paid")]
        if not overdue:
            continue

        total_overdue = sum(i["amount"] - i.get("amount_paid", 0) for i in overdue)
        max_days = max((i.get("overdue_days", 0) for i in overdue), default=0)

        risk_data = get_latest_risk_score(c["client_id"])
        risk_score = risk_data["risk_score"] if risk_data else 0

        # Normalise days (cap at 365) and amount (cap at 1 000 000)
        norm_days   = min(max_days / 365.0, 1.0) * 100
        norm_amount = min(total_overdue / 1_000_000.0, 1.0) * 100

        priority = risk_score * 0.4 + norm_days * 0.3 + norm_amount * 0.3

        queue.append({
            "client_id": c["client_id"],
            "company_name": c["company_name"],
            "risk_category": c.get("risk_category", "Low"),
            "total_overdue": total_overdue,
            "overdue_count": len(overdue),
            "max_days_overdue": max_days,
            "risk_score": risk_score,
            "priority_score": round(priority, 2),
        })

    queue.sort(key=lambda x: x["priority_score"], reverse=True)
    return queue


# ════════════════════════════════════════════════════════════════════════
# RISK OVERVIEW — dashboard helper
# ════════════════════════════════════════════════════════════════════════

def get_risk_overview() -> dict:
    """
    Return { distribution: {category: count}, top_risk_clients: [...] }
    """
    from models.risk_score import get_risk_distribution
    dist_rows = get_risk_distribution()
    distribution = {r["risk_category"]: r["count"] for r in dist_rows}

    top = get_all_latest_risk_scores()[:10]
    return {"distribution": distribution, "top_risk_clients": top}
