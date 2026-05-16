"""
Formatting utilities for currency, dates, percentages, and display values.
"""

from datetime import datetime, date
from typing import Union, Optional
import config


def format_currency(amount: Union[int, float], currency: str = None) -> str:
    """Format amount as currency string."""
    curr = currency or config.CURRENCY
    if curr == "INR":
        return f"₹{amount:,.2f}"
    elif curr == "USD":
        return f"${amount:,.2f}"
    elif curr == "EUR":
        return f"€{amount:,.2f}"
    elif curr == "GBP":
        return f"£{amount:,.2f}"
    else:
        return f"{curr} {amount:,.2f}"


def format_date(d: Union[str, datetime, date], output_fmt: str = None) -> str:
    """Format date for display."""
    fmt = output_fmt or config.DISPLAY_DATE_FORMAT
    if isinstance(d, str):
        try:
            d = datetime.strptime(d, config.DATE_FORMAT)
        except ValueError:
            try:
                d = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return str(d)
    if isinstance(d, (datetime, date)):
        return d.strftime(fmt)
    return str(d)


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage."""
    return f"{value:.{decimals}f}%"


def format_days(days: int) -> str:
    """Format days with proper singular/plural."""
    if days == 0:
        return "Today"
    elif days == 1:
        return "1 day"
    else:
        return f"{days} days"


def format_large_number(value: Union[int, float]) -> str:
    """Format large numbers with K, L, Cr suffixes (Indian numbering)."""
    if abs(value) >= 1e7:
        return f"₹{value / 1e7:.2f} Cr"
    elif abs(value) >= 1e5:
        return f"₹{value / 1e5:.2f} L"
    elif abs(value) >= 1e3:
        return f"₹{value / 1e3:.1f}K"
    else:
        return f"₹{value:,.0f}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis."""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length - 3] + "..."


def severity_badge(severity: str) -> str:
    """Return emoji badge for severity level."""
    badges = {
        "None": "⚪",
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🔴",
        "Critical": "🔥",
    }
    return badges.get(severity, "⚪")


def status_badge(status: str) -> str:
    """Return emoji badge for status."""
    badges = {
        "Pending": "⏳",
        "Overdue": "⚠️",
        "Partially Paid": "💰",
        "Paid": "✅",
        "Written Off": "❌",
        "Draft": "📝",
        "Pending Approval": "🔍",
        "Approved": "✅",
        "Rejected": "🚫",
        "Sent": "📧",
        "Failed": "❌",
        "Fulfilled": "✅",
        "Broken": "💔",
    }
    return badges.get(status, "⚪")


def time_ago(dt: Union[str, datetime]) -> str:
    """Return human-readable time difference."""
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return str(dt)

    now = datetime.now()
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years}y ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"
