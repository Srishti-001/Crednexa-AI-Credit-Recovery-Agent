"""
Legal escalation service — monitors and triggers legal escalation alerts.
"""

from loguru import logger
import config
from models.invoice import get_all_invoices
from models.client import get_all_clients, get_client
from models.payment_promise import get_promises_by_client
from services.audit_service import log_action


def check_legal_escalation_candidates() -> list:
    """
    Identify clients meeting legal escalation thresholds.
    Criteria: overdue > LEGAL_ESCALATION_DAYS and amount > LEGAL_ESCALATION_AMOUNT.
    Returns list of candidates with details.
    """
    invoices = get_all_invoices()
    candidates = {}

    for inv in invoices:
        if inv.get("status") not in ("Overdue", "Partially Paid"):
            continue

        overdue_days = inv.get("overdue_days", 0)
        outstanding = inv["amount"] - inv.get("amount_paid", 0)

        if overdue_days < config.LEGAL_ESCALATION_DAYS and outstanding < config.LEGAL_ESCALATION_AMOUNT:
            continue

        client_id = inv["client_id"]
        if client_id not in candidates:
            candidates[client_id] = {
                "client_id": client_id,
                "company_name": inv.get("company_name", "Unknown"),
                "contact_email": inv.get("contact_email", ""),
                "invoices": [],
                "total_outstanding": 0,
                "max_overdue_days": 0,
                "escalation_reasons": [],
            }

        candidates[client_id]["invoices"].append(inv)
        candidates[client_id]["total_outstanding"] += outstanding
        candidates[client_id]["max_overdue_days"] = max(
            candidates[client_id]["max_overdue_days"], overdue_days
        )

    # Add escalation reasons
    for cid, data in candidates.items():
        reasons = []
        if data["max_overdue_days"] >= config.LEGAL_ESCALATION_DAYS:
            reasons.append(f"Overdue for {data['max_overdue_days']} days (threshold: {config.LEGAL_ESCALATION_DAYS})")
        if data["total_outstanding"] >= config.LEGAL_ESCALATION_AMOUNT:
            reasons.append(f"Outstanding ₹{data['total_outstanding']:,.2f} (threshold: ₹{config.LEGAL_ESCALATION_AMOUNT:,.2f})")

        # Check broken promises
        promises = get_promises_by_client(cid)
        broken = len([p for p in promises if p.get("status") == "Broken"])
        if broken >= 2:
            reasons.append(f"{broken} broken payment promises")

        data["escalation_reasons"] = reasons
        data["broken_promises"] = broken

    return list(candidates.values())


def create_legal_alert(client_id: str, reason: str = "") -> str:
    """Create an audit log entry for legal escalation alert."""
    return log_action(
        "Legal Escalation",
        "Client",
        client_id,
        details={"reason": reason},
        performed_by="System"
    )


def get_escalation_summary() -> dict:
    """Get summary of legal escalation status."""
    candidates = check_legal_escalation_candidates()
    return {
        "total_candidates": len(candidates),
        "total_at_risk_amount": sum(c["total_outstanding"] for c in candidates),
        "candidates": candidates,
    }
