"""
Filter components — reusable filter widgets.
"""

import streamlit as st
from utils.constants import InvoiceStatus, Severity, ToneLevel, RiskCategory


def status_filter(key: str = "status_filter") -> list:
    """Render invoice status filter. Returns list of selected statuses."""
    options = [s.value for s in InvoiceStatus]
    return st.multiselect("Filter by Status", options, default=options, key=key)


def severity_filter(key: str = "severity_filter") -> list:
    """Render severity filter."""
    options = [s.value for s in Severity if s.value != "None"]
    return st.multiselect("Filter by Severity", options, default=options, key=key)


def risk_filter(key: str = "risk_filter") -> list:
    """Render risk category filter."""
    options = [r.value for r in RiskCategory]
    return st.multiselect("Filter by Risk", options, default=options, key=key)


def tone_filter(key: str = "tone_filter") -> str:
    """Render tone selector. Returns selected tone."""
    options = [t.value for t in ToneLevel]
    return st.selectbox("Select Tone", options, key=key)


def date_range_filter(key: str = "date_filter"):
    """Render date range filter. Returns (start_date, end_date)."""
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("From Date", key=f"{key}_start")
    with col2:
        end = st.date_input("To Date", key=f"{key}_end")
    return start, end


def client_selector(clients: list, key: str = "client_selector") -> dict:
    """Render client dropdown selector. Returns selected client dict."""
    if not clients:
        st.info("No clients available.")
        return None

    client_names = {c["company_name"]: c for c in clients}
    selected = st.selectbox(
        "Select Client",
        options=list(client_names.keys()),
        key=key
    )
    return client_names.get(selected)
