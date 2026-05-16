"""
Timeline component — renders client communication and activity timelines.
"""

import streamlit as st
from utils.formatters import format_date, time_ago
from utils.constants import TONE_COLORS


def render_timeline(events: list):
    """
    Render a vertical timeline of events.
    Each event: {'date': str, 'title': str, 'description': str, 'type': str, 'icon': str}.
    """
    if not events:
        st.info("📅 No timeline events to display.")
        return

    for i, event in enumerate(events):
        icon = event.get("icon", "📌")
        event_type = event.get("type", "default")
        color = _get_event_color(event_type)
        is_last = i == len(events) - 1

        st.markdown(f"""
        <div style="
            display: flex;
            gap: 1rem;
            margin-bottom: 0;
            position: relative;
        ">
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                min-width: 40px;
            ">
                <div style="
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: {color}20;
                    border: 2px solid {color};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.8rem;
                    z-index: 1;
                ">{icon}</div>
                {"" if is_last else f'<div style="width: 2px; flex: 1; background: {color}30; margin: 4px 0;"></div>'}
            </div>
            <div style="
                flex: 1;
                padding-bottom: 1.5rem;
            ">
                <p style="color: #64748b; font-size: 0.7rem; margin: 0;">
                    {format_date(event.get('date', ''))} • {time_ago(event.get('date', ''))}
                </p>
                <p style="color: #e2e8f0; font-weight: 600; margin: 0.2rem 0; font-size: 0.9rem;">
                    {event.get('title', '')}
                </p>
                <p style="color: #94a3b8; font-size: 0.8rem; margin: 0; line-height: 1.4;">
                    {event.get('description', '')}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)


def build_client_timeline(emails: list, promises: list = None, invoices: list = None) -> list:
    """Build a combined timeline from emails, promises, and invoices."""
    events = []

    for email in (emails or []):
        events.append({
            "date": email.get("created_at", ""),
            "title": f"📧 Email: {email.get('subject', '')[:50]}",
            "description": f"Tone: {email.get('tone', '')} | Status: {email.get('status', '')}",
            "type": "email",
            "icon": "✉️",
        })

    for promise in (promises or []):
        events.append({
            "date": promise.get("created_at", ""),
            "title": f"🤝 Payment Promise: ₹{promise.get('promised_amount', 0):,.2f}",
            "description": f"Due: {format_date(promise.get('promised_date', ''))} | Status: {promise.get('status', '')}",
            "type": "promise",
            "icon": "🤝",
        })

    for inv in (invoices or []):
        events.append({
            "date": inv.get("created_at", ""),
            "title": f"📄 Invoice: {inv.get('invoice_number', '')}",
            "description": f"Amount: ₹{inv.get('amount', 0):,.2f} | Status: {inv.get('status', '')}",
            "type": "invoice",
            "icon": "📄",
        })

    # Sort by date descending
    events.sort(key=lambda x: x.get("date", ""), reverse=True)
    return events


def _get_event_color(event_type: str) -> str:
    """Get color for event type."""
    colors = {
        "email": "#3b82f6",
        "promise": "#f59e0b",
        "invoice": "#8b5cf6",
        "strategy": "#22c55e",
        "default": "#64748b",
    }
    return colors.get(event_type, "#64748b")
