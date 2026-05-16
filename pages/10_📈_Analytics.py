"""
📈 Analytics — Audit logs, reports, and trend analysis.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.metrics_cards import metric_card
from components.data_tables import audit_table
from components.charts import bar_chart, donut_chart
from services.analytics_service import (
    get_dashboard_metrics, get_tone_analytics, get_audit_analytics,
    get_recovery_trends
)
from models.audit_log import get_all_audit_logs, get_audit_logs_by_date_range
from models.email_log import get_tone_distribution
from utils.constants import TONE_COLORS, STATUS_COLORS

st.set_page_config(page_title="Analytics | Crednexa AI", page_icon="📈", layout="wide")
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">📈 Analytics & Audit Logs</h1>
<p style="color: #94a3b8;">Comprehensive reporting, trend analysis, and audit trail</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Overview Metrics ────────────────────────────────────────────────────
metrics = get_dashboard_metrics()

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Recovery Rate", f"{metrics['recovery_rate']}%", icon="📈", color="#22c55e")
with col2:
    metric_card("Emails Sent", str(metrics["emails_sent"]), icon="📧", color="#3b82f6")
with col3:
    metric_card("Promise Rate", f"{metrics['promise_rate']}%", icon="🤝", color="#f59e0b")
with col4:
    metric_card("Total Clients", str(metrics["total_clients"]), icon="👥", color="#8b5cf6")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Charts", "🎯 Tone Analytics", "📝 Audit Logs", "📥 Export"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Invoice Status Breakdown")
        trends = get_recovery_trends()
        if trends:
            labels = [t["status"] for t in trends]
            values = [t["count"] for t in trends]
            colors = [STATUS_COLORS.get(s, "#6B7280") for s in labels]
            donut_chart(labels, values, colors)
        else:
            st.info("No data available")

    with col2:
        st.markdown("### 📧 Communication Summary")
        st.markdown(f"""
        <div style="background: #1e293b; border-radius: 10px; padding: 1.5rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <span style="color: #94a3b8;">Total Emails</span>
                <span style="color: #e2e8f0; font-weight: 600;">{metrics['total_emails']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <span style="color: #94a3b8;">Sent</span>
                <span style="color: #22c55e; font-weight: 600;">{metrics['emails_sent']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <span style="color: #94a3b8;">Pending Approval</span>
                <span style="color: #f59e0b; font-weight: 600;">{metrics['emails_pending']}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #94a3b8;">Drafts</span>
                <span style="color: #6B7280; font-weight: 600;">{metrics['emails_draft']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### 🎯 Tone Usage Distribution")
    tone_dist = get_tone_distribution()
    if tone_dist:
        labels = [t["tone"] for t in tone_dist]
        values = [t["count"] for t in tone_dist]
        colors = [TONE_COLORS.get(t, "#6B7280") for t in labels]
        col1, col2 = st.columns(2)
        with col1:
            donut_chart(labels, values, colors, "Tones Used in Sent Emails")
        with col2:
            bar_chart(labels, values, colors, "Email Count by Tone", y_label="Count")
    else:
        st.info("No tone data. Send some emails first!")

with tab3:
    st.markdown("### 📝 Audit Trail")

    col1, col2 = st.columns([1, 3])
    with col1:
        log_limit = st.number_input("Show last N logs", min_value=10, max_value=500, value=50, step=10)

    logs = get_all_audit_logs(log_limit)
    audit_table(logs)

    # Audit summary
    audit_data = get_audit_analytics()
    if audit_data.get("action_summary"):
        st.markdown("### 📊 Action Summary")
        labels = [a["user_action"] for a in audit_data["action_summary"]]
        values = [a["count"] for a in audit_data["action_summary"]]
        bar_chart(labels, values, title="Actions Performed", y_label="Count")

with tab4:
    st.markdown("### 📥 Export Data")
    st.info("Export your data in various formats.")

    import pandas as pd
    from models.invoice import get_all_invoices
    from models.client import get_all_clients

    col1, col2, col3 = st.columns(3)
    with col1:
        invoices = get_all_invoices()
        if invoices:
            df = pd.DataFrame(invoices)
            csv = df.to_csv(index=False)
            st.download_button("📥 Export Invoices CSV", csv, "invoices_export.csv", "text/csv",
                               use_container_width=True)
    with col2:
        clients_data = get_all_clients()
        if clients_data:
            df = pd.DataFrame(clients_data)
            csv = df.to_csv(index=False)
            st.download_button("📥 Export Clients CSV", csv, "clients_export.csv", "text/csv",
                               use_container_width=True)
    with col3:
        if logs:
            df = pd.DataFrame(logs)
            csv = df.to_csv(index=False)
            st.download_button("📥 Export Audit Logs CSV", csv, "audit_logs_export.csv", "text/csv",
                               use_container_width=True)
