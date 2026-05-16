"""
👤 Client History — Comprehensive client profile with communication timeline.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.filters import client_selector
from components.metrics_cards import metric_card, financial_metric
from components.data_tables import invoice_table
from components.timeline import render_timeline, build_client_timeline
from components.charts import line_chart
from models.client import get_all_clients, get_client
from models.invoice import get_invoices_by_client
from models.email_log import get_emails_by_client
from models.payment_promise import get_promises_by_client
from models.risk_score import get_risk_history, get_latest_risk_score
from utils.formatters import format_currency
from utils.constants import RISK_COLORS

st.set_page_config(page_title="Client History | Crednexa AI", page_icon="👤", layout="wide")
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">👤 Client History</h1>
<p style="color: #94a3b8;">Complete client profile, payment history, and communication timeline</p>
""", unsafe_allow_html=True)

st.markdown("---")

clients = get_all_clients()
selected_client = client_selector(clients, key="history_client")

if selected_client:
    client = get_client(selected_client["client_id"])
    invoices = get_invoices_by_client(client["client_id"])
    emails = get_emails_by_client(client["client_id"])
    promises = get_promises_by_client(client["client_id"])
    risk_data = get_latest_risk_score(client["client_id"])

    # ── Client Profile Card ─────────────────────────────────────────────
    risk_cat = client.get("risk_category", "Low")
    risk_color = RISK_COLORS.get(risk_cat, "#6B7280")

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e1b4b 0%, #1e293b 100%);
        border: 1px solid {risk_color}40;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="color: #e2e8f0; margin: 0;">{client['company_name']}</h2>
                <p style="color: #94a3b8; margin: 0.25rem 0;">
                    👤 {client.get('contact_name', 'N/A')} • 📧 {client.get('contact_email', 'N/A')}
                    • 📞 {client.get('phone', 'N/A')}
                </p>
                <p style="color: #64748b; margin: 0;">
                    🏭 {client.get('industry', 'N/A')} • 📋 {client.get('invoices_count', 0)} invoices
                </p>
            </div>
            <div style="text-align: center;">
                <span style="
                    background: {risk_color}20; color: {risk_color};
                    padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.9rem;
                ">{risk_cat} Risk</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Financial Metrics ───────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        financial_metric("Outstanding", client.get("total_outstanding", 0), icon="💸", color="#ef4444")
    with col2:
        financial_metric("Total Paid", client.get("total_paid", 0), icon="✅", color="#22c55e")
    with col3:
        metric_card("Emails Sent", str(len(emails)), icon="✉️", color="#3b82f6")
    with col4:
        risk_score = risk_data["risk_score"] if risk_data else 0
        metric_card("Risk Score", f"{risk_score:.0f}/100", icon="🎯", color=risk_color)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Timeline", "📄 Invoices", "✉️ Emails", "📈 Risk Trend"])

    with tab1:
        timeline = build_client_timeline(emails, promises, invoices)
        render_timeline(timeline[:20])

    with tab2:
        invoice_table(invoices, show_client=False)

    with tab3:
        if emails:
            from components.email_preview import render_email_preview
            for email in emails[:10]:
                with st.expander(f"{'📧' if email['status'] == 'Sent' else '📝'} {email.get('subject', '')[:60]}"):
                    render_email_preview(email["subject"], email["body"], email.get("tone", ""))
        else:
            st.info("No emails for this client yet.")

    with tab4:
        risk_history = get_risk_history(client["client_id"])
        if risk_history:
            dates = [r.get("calculated_at", "")[:10] for r in reversed(risk_history)]
            scores = [r.get("risk_score", 0) for r in reversed(risk_history)]
            line_chart(dates, scores, "Risk Score Over Time", "Date", "Risk Score", risk_color)
        else:
            st.info("No risk score history. Calculate risk scores from the Overdue Invoices page.")
else:
    st.info("👤 Select a client to view their history")
