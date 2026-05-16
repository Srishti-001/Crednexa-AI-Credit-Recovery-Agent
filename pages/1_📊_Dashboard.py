"""
📊 Dashboard — Financial Risk Intelligence Dashboard
Main overview page with KPIs, charts, and risk heatmap.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.metrics_cards import metric_card, financial_metric
from components.charts import (
    donut_chart, bar_chart, gauge_chart, status_distribution_chart,
    risk_distribution_chart, aging_chart
)
from components.risk_heatmap import render_risk_matrix
from services.analytics_service import (
    get_dashboard_metrics, get_risk_overview, get_recovery_trends,
    get_overdue_aging_data
)
from utils.formatters import format_currency, format_large_number

st.set_page_config(page_title="Dashboard | Crednexa AI", page_icon="📊", layout="wide")
render_sidebar()

# ── Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom: 2rem;">
    <h1 style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
    ">📊 Financial Risk Intelligence Dashboard</h1>
    <p style="color: #94a3b8; font-size: 0.9rem;">Real-time overview of your credit recovery portfolio</p>
</div>
""", unsafe_allow_html=True)

# ── Load Data ───────────────────────────────────────────────────────────
metrics = get_dashboard_metrics()

# ── KPI Row 1: Financial Overview ───────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Invoices", str(metrics["total_invoices"]), icon="📋", color="#3b82f6")
with col2:
    financial_metric("Total Amount", metrics["total_amount"], icon="💰", color="#8b5cf6")
with col3:
    financial_metric("Collected", metrics["total_collected"], icon="✅", color="#22c55e")
with col4:
    financial_metric("Overdue Amount", metrics["total_overdue"], icon="⚠️", color="#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# ── KPI Row 2: Performance Metrics ──────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Overdue Invoices", str(metrics["overdue_count"]), icon="⏰", color="#f59e0b")
with col2:
    metric_card("Recovery Rate", f"{metrics['recovery_rate']}%", icon="📈", color="#22c55e")
with col3:
    metric_card("Avg Overdue Days", f"{metrics['avg_overdue_days']:.0f}", icon="📅", color="#ef4444")
with col4:
    metric_card("Promise Rate", f"{metrics['promise_rate']}%", icon="🤝", color="#06b6d4")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row ──────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Invoice Status Distribution")
    trends = get_recovery_trends()
    if trends:
        status_data = {t["status"]: t["count"] for t in trends}
        status_distribution_chart(status_data)
    else:
        st.info("Upload invoices to see distribution")

with col2:
    st.markdown("### 🎯 Recovery Rate")
    gauge_chart(metrics["recovery_rate"], "Recovery Rate")

st.markdown("<br>", unsafe_allow_html=True)

# ── Risk & Aging Row ────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⚡ Risk Distribution")
    risk_overview = get_risk_overview()
    if risk_overview["distribution"]:
        risk_distribution_chart(risk_overview["distribution"])
    else:
        st.info("Calculate risk scores to see distribution")

with col2:
    st.markdown("### 📆 Overdue Aging Analysis")
    aging = get_overdue_aging_data()
    if sum(aging.values()) > 0:
        aging_chart(aging)
    else:
        st.info("No overdue invoices for aging analysis")

# ── Risk Matrix ─────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
risk_overview = get_risk_overview()
if risk_overview.get("top_risk_clients"):
    render_risk_matrix(risk_overview["top_risk_clients"])

# ── Email & Activity Metrics ────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📧 Communication Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Emails", str(metrics["total_emails"]), icon="✉️", color="#3b82f6")
with col2:
    metric_card("Emails Sent", str(metrics["emails_sent"]), icon="📤", color="#22c55e")
with col3:
    metric_card("Pending Approval", str(metrics["emails_pending"]), icon="🔍", color="#f59e0b")
with col4:
    metric_card("Total Clients", str(metrics["total_clients"]), icon="👥", color="#8b5cf6")
