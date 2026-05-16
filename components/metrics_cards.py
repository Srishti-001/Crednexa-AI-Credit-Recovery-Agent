"""
Metric card components — reusable KPI cards for dashboards.
"""

import streamlit as st
from utils.formatters import format_currency, format_percentage


def metric_card(title: str, value: str, delta: str = None, icon: str = "📊",
                color: str = "#667eea", delta_color: str = "normal"):
    """Render a styled metric card."""
    delta_html = ""
    if delta:
        dc = "#22c55e" if delta_color == "normal" or delta_color == "green" else "#ef4444"
        delta_html = f'<p style="color: {dc}; font-size: 0.8rem; margin: 0;">{delta}</p>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}15 0%, {color}08 100%);
        border: 1px solid {color}30;
        border-radius: 12px;
        padding: 1.25rem;
        height: 100%;
        transition: transform 0.2s;
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.3rem;">{icon}</span>
            <p style="color: #94a3b8; font-size: 0.8rem; margin: 0; font-weight: 500;">{title}</p>
        </div>
        <p style="
            font-size: 1.6rem;
            font-weight: 700;
            color: #e2e8f0;
            margin: 0;
            letter-spacing: -0.5px;
        ">{value}</p>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def financial_metric(title: str, amount: float, currency: str = "INR",
                     icon: str = "💰", color: str = "#22c55e"):
    """Render a financial metric card with currency formatting."""
    metric_card(title, format_currency(amount, currency), icon=icon, color=color)


def percentage_metric(title: str, value: float, icon: str = "📈",
                      color: str = "#3b82f6"):
    """Render a percentage metric card."""
    metric_card(title, format_percentage(value), icon=icon, color=color)


def count_metric(title: str, count: int, icon: str = "📋", color: str = "#8b5cf6"):
    """Render a count metric card."""
    metric_card(title, str(count), icon=icon, color=color)


def render_metric_row(metrics: list):
    """Render a row of metric cards. Each metric is a dict with card params."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            metric_card(**m)
