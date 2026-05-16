"""
Analytics service — aggregates data for dashboard and reporting.
"""

from models.invoice import get_invoice_stats, get_all_invoices
from models.email_log import get_email_stats, get_tone_distribution
from models.client import get_all_clients, get_client_count
from models.payment_promise import get_promise_stats
from models.risk_score import get_risk_distribution, get_all_latest_risk_scores
from models.audit_log import get_all_audit_logs, get_audit_summary
from utils.helpers import safe_divide


def get_dashboard_metrics() -> dict:
    """Get all key metrics for the main dashboard."""
    inv_stats = get_invoice_stats() or {}
    email_stats = get_email_stats() or {}
    promise_stats = get_promise_stats() or {}

    total_amount = inv_stats.get("total_amount", 0)
    total_collected = inv_stats.get("total_collected", 0)
    total_overdue = inv_stats.get("total_overdue", 0)

    recovery_rate = safe_divide(total_collected, total_amount, 0) * 100

    promise_total = promise_stats.get("total_promises", 0)
    promise_fulfilled = promise_stats.get("fulfilled", 0)
    promise_rate = safe_divide(promise_fulfilled, promise_total, 0) * 100

    return {
        # Invoice metrics
        "total_invoices": inv_stats.get("total_invoices", 0),
        "total_amount": total_amount,
        "total_collected": total_collected,
        "total_overdue": total_overdue,
        "overdue_count": inv_stats.get("overdue_count", 0),
        "paid_count": inv_stats.get("paid_count", 0),
        "avg_overdue_days": inv_stats.get("avg_overdue_days", 0),
        "recovery_rate": round(recovery_rate, 1),

        # Email metrics
        "total_emails": email_stats.get("total_emails", 0),
        "emails_sent": email_stats.get("sent_count", 0),
        "emails_pending": email_stats.get("pending_count", 0),
        "emails_draft": email_stats.get("draft_count", 0),

        # Promise metrics
        "total_promises": promise_total,
        "promises_fulfilled": promise_fulfilled,
        "promises_broken": promise_stats.get("broken", 0),
        "promise_rate": round(promise_rate, 1),

        # Client metrics
        "total_clients": get_client_count(),
    }


def get_risk_overview() -> dict:
    """Get risk distribution and top-risk clients."""
    distribution = get_risk_distribution()
    top_risk = get_all_latest_risk_scores()

    return {
        "distribution": {d["risk_category"]: d["count"] for d in distribution},
        "top_risk_clients": top_risk[:10],
    }


def get_recovery_trends() -> list:
    """Get invoice status distribution for trend analysis."""
    invoices = get_all_invoices()
    status_counts = {}
    for inv in invoices:
        status = inv.get("status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return [{"status": k, "count": v} for k, v in status_counts.items()]


def get_tone_analytics() -> dict:
    """Get tone usage distribution."""
    dist = get_tone_distribution()
    return {"distribution": dist}


def get_audit_analytics() -> dict:
    """Get audit log analytics."""
    summary = get_audit_summary()
    recent = get_all_audit_logs(20)
    return {
        "action_summary": summary,
        "recent_activity": recent,
    }


def get_overdue_aging_data() -> dict:
    """Get aging analysis of overdue invoices."""
    invoices = get_all_invoices()
    aging = {"0-15 days": 0, "16-30 days": 0, "31-60 days": 0, "61-90 days": 0, "90+ days": 0}

    for inv in invoices:
        days = inv.get("overdue_days", 0)
        if days <= 0:
            continue
        elif days <= 15:
            aging["0-15 days"] += 1
        elif days <= 30:
            aging["16-30 days"] += 1
        elif days <= 60:
            aging["31-60 days"] += 1
        elif days <= 90:
            aging["61-90 days"] += 1
        else:
            aging["90+ days"] += 1

    return aging
