"""
Data table components — styled tables for invoice, client, and email data.
"""

import streamlit as st
import pandas as pd
from utils.formatters import format_currency, format_date, severity_badge, status_badge


def invoice_table(invoices: list, show_client: bool = True):
    """Render a styled invoice table."""
    if not invoices:
        st.info("📋 No invoices to display.")
        return

    rows = []
    for inv in invoices:
        row = {
            "Status": f"{status_badge(inv.get('status', ''))} {inv.get('status', '')}",
            "Invoice #": inv.get("invoice_number", ""),
            "Amount": format_currency(inv.get("amount", 0)),
            "Paid": format_currency(inv.get("amount_paid", 0)),
            "Due Date": format_date(inv.get("due_date", "")),
            "Overdue": f"{inv.get('overdue_days', 0)} days",
            "Severity": f"{severity_badge(inv.get('severity', 'None'))} {inv.get('severity', 'None')}",
        }
        if show_client:
            row["Company"] = inv.get("company_name", "Unknown")
        rows.append(row)

    df = pd.DataFrame(rows)
    if show_client:
        cols = ["Status", "Company", "Invoice #", "Amount", "Paid", "Due Date", "Overdue", "Severity"]
    else:
        cols = ["Status", "Invoice #", "Amount", "Paid", "Due Date", "Overdue", "Severity"]
    df = df[cols]
    st.dataframe(df, use_container_width=True, hide_index=True)


def client_table(clients: list):
    """Render a client table."""
    if not clients:
        st.info("👤 No clients to display.")
        return

    rows = []
    for c in clients:
        rows.append({
            "Company": c.get("company_name", ""),
            "Contact": c.get("contact_name", ""),
            "Email": c.get("contact_email", ""),
            "Outstanding": format_currency(c.get("total_outstanding", 0)),
            "Paid": format_currency(c.get("total_paid", 0)),
            "Invoices": c.get("invoices_count", 0),
            "Risk": c.get("risk_category", "Low"),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def email_table(emails: list):
    """Render an email log table."""
    if not emails:
        st.info("✉️ No emails to display.")
        return

    rows = []
    for e in emails:
        rows.append({
            "Status": f"{status_badge(e.get('status', ''))} {e.get('status', '')}",
            "Company": e.get("company_name", ""),
            "Subject": e.get("subject", "")[:60],
            "Tone": e.get("tone", ""),
            "Emotion": e.get("detected_emotion", "N/A"),
            "Created": format_date(e.get("created_at", "")),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def audit_table(logs: list):
    """Render an audit log table."""
    if not logs:
        st.info("📝 No audit logs to display.")
        return

    rows = []
    for log in logs:
        rows.append({
            "Time": format_date(log.get("performed_at", "")),
            "Action": log.get("user_action", ""),
            "Entity": log.get("entity_type", ""),
            "Entity ID": log.get("entity_id", "")[:20] if log.get("entity_id") else "",
            "By": log.get("performed_by", "System"),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def promise_table(promises: list):
    """Render a payment promise table."""
    if not promises:
        st.info("🤝 No payment promises to display.")
        return

    rows = []
    for p in promises:
        rows.append({
            "Status": f"{status_badge(p.get('status', ''))} {p.get('status', '')}",
            "Company": p.get("company_name", ""),
            "Amount": format_currency(p.get("promised_amount", 0)),
            "Promised Date": format_date(p.get("promised_date", "")),
            "Source": p.get("source", ""),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
