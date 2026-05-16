"""
Miscellaneous helper functions.
"""

import uuid
from datetime import datetime, date


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    uid = uuid.uuid4().hex[:12]
    if prefix:
        return f"{prefix}_{uid}"
    return uid


def calculate_overdue_days(due_date: str) -> int:
    """Calculate days overdue from due date."""
    try:
        if isinstance(due_date, str):
            due = datetime.strptime(due_date, "%Y-%m-%d").date()
        elif isinstance(due_date, datetime):
            due = due_date.date()
        elif isinstance(due_date, date):
            due = due_date
        else:
            return 0

        today = date.today()
        diff = (today - due).days
        return max(0, diff)
    except (ValueError, TypeError):
        return 0


def classify_severity(overdue_days: int) -> str:
    """Classify invoice severity based on overdue days."""
    if overdue_days <= 0:
        return "None"
    elif overdue_days <= 30:
        return "Low"
    elif overdue_days <= 60:
        return "Medium"
    elif overdue_days <= 90:
        return "High"
    else:
        return "Critical"


def get_tone_for_days(overdue_days: int) -> tuple:
    """Get recommended tone level and name based on overdue days."""
    if overdue_days <= 15:
        return 1, "Friendly"
    elif overdue_days <= 30:
        return 2, "Professional"
    elif overdue_days <= 60:
        return 3, "Firm"
    elif overdue_days <= 90:
        return 4, "Urgent"
    else:
        return 5, "Legal"


def calculate_risk_score(
    overdue_amount: float,
    avg_overdue_days: float,
    total_invoices: int,
    overdue_invoices: int,
    broken_promises: int = 0,
    total_promises: int = 0,
) -> float:
    """
    Calculate a composite risk score (0-100).
    Higher score = higher risk.
    """
    score = 0.0

    # Amount factor (0-30 points)
    if overdue_amount > 500000:
        score += 30
    elif overdue_amount > 100000:
        score += 20
    elif overdue_amount > 50000:
        score += 15
    elif overdue_amount > 10000:
        score += 10
    else:
        score += 5

    # Days factor (0-25 points)
    if avg_overdue_days > 90:
        score += 25
    elif avg_overdue_days > 60:
        score += 20
    elif avg_overdue_days > 30:
        score += 15
    elif avg_overdue_days > 15:
        score += 10
    else:
        score += 5

    # Payment reliability (0-20 points)
    if total_invoices > 0:
        overdue_ratio = overdue_invoices / total_invoices
        score += overdue_ratio * 20

    # Broken promises (0-15 points)
    if total_promises > 0:
        broken_ratio = broken_promises / total_promises
        score += broken_ratio * 15

    # Base factor (0-10 points based on total overdue count)
    score += min(overdue_invoices * 2, 10)

    return min(score, 100.0)


def categorize_risk(score: float) -> str:
    """Categorize risk score into risk levels."""
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    else:
        return "Low"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers."""
    if denominator == 0:
        return default
    return numerator / denominator
