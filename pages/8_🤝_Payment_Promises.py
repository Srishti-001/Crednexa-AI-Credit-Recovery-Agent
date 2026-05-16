"""
🤝 Payment Promises — Track payment commitments from clients.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.metrics_cards import metric_card, financial_metric
from components.data_tables import promise_table
from components.charts import donut_chart
from components.filters import client_selector
from models.client import get_all_clients
from models.invoice import get_invoices_by_client
from models.payment_promise import (
    create_promise, get_all_promises, get_pending_promises,
    get_promise_stats, check_overdue_promises, update_promise_status
)
from utils.formatters import format_currency
from datetime import date

st.set_page_config(page_title="Payment Promises | Crednexa AI", page_icon="🤝", layout="wide")
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #f59e0b 0%, #22c55e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">🤝 Payment Promise Tracker</h1>
<p style="color: #94a3b8;">Track and manage client payment commitments</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Auto-check overdue promises ─────────────────────────────────────────
overdue_promises = check_overdue_promises()
if overdue_promises:
    st.warning(f"⚠️ {len(overdue_promises)} promises have been auto-marked as broken (past due date)")

# ── Metrics ─────────────────────────────────────────────────────────────
stats = get_promise_stats()
col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Promises", str(stats.get("total_promises", 0)), icon="📋", color="#3b82f6")
with col2:
    metric_card("Fulfilled", str(stats.get("fulfilled", 0)), icon="✅", color="#22c55e")
with col3:
    metric_card("Broken", str(stats.get("broken", 0)), icon="💔", color="#ef4444")
with col4:
    financial_metric("Promised Amount", stats.get("total_promised_amount", 0), icon="💰", color="#f59e0b")

st.markdown("<br>", unsafe_allow_html=True)

# ── Add New Promise ─────────────────────────────────────────────────────
with st.expander("➕ Add New Payment Promise", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        clients = get_all_clients()
        selected_client = client_selector(clients, key="promise_client")
        promised_amount = st.number_input("Promised Amount (₹)", min_value=0.0, step=1000.0)
        promised_date = st.date_input("Promised Payment Date", min_value=date.today())

    with col2:
        source = st.selectbox("Source", ["Email", "Phone", "Meeting", "Letter", "Other"])
        notes = st.text_area("Notes", placeholder="Any additional notes about this promise...")

        # Invoice selector (optional)
        selected_invoice_id = None
        if selected_client:
            invoices = get_invoices_by_client(selected_client["client_id"])
            if invoices:
                inv_options = {"None": None}
                inv_options.update({
                    f"{inv['invoice_number']} — ₹{inv['amount']:,.2f}": inv["invoice_id"]
                    for inv in invoices
                })
                selected_inv = st.selectbox("Link to Invoice (optional)", list(inv_options.keys()))
                selected_invoice_id = inv_options[selected_inv]

    if st.button("💾 Save Promise", type="primary"):
        if selected_client and promised_amount > 0:
            create_promise(
                client_id=selected_client["client_id"],
                promised_amount=promised_amount,
                promised_date=promised_date.strftime("%Y-%m-%d"),
                invoice_id=selected_invoice_id,
                source=source,
                notes=notes,
            )
            st.success("✅ Payment promise recorded!")
            st.rerun()
        else:
            st.error("Please select a client and enter a valid amount.")

# ── Tabs ────────────────────────────────────────────────────────────────
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📋 All Promises", "⏳ Pending", "📊 Analytics"])

with tab1:
    all_promises = get_all_promises()
    promise_table(all_promises)

    # Quick status update
    if all_promises:
        st.markdown("### ⚡ Quick Status Update")
        for p in all_promises:
            if p.get("status") == "Pending":
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{p.get('company_name', '')}** — ₹{p.get('promised_amount', 0):,.2f}")
                with col2:
                    if st.button("✅ Fulfilled", key=f"fulfill_{p['promise_id']}"):
                        update_promise_status(p["promise_id"], "Fulfilled", "Manually marked as fulfilled")
                        st.rerun()
                with col3:
                    if st.button("💔 Broken", key=f"break_{p['promise_id']}"):
                        update_promise_status(p["promise_id"], "Broken", "Manually marked as broken")
                        st.rerun()

with tab2:
    pending = get_pending_promises()
    if pending:
        promise_table(pending)
    else:
        st.info("No pending promises.")

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        if stats.get("total_promises", 0) > 0:
            labels = ["Fulfilled", "Pending", "Broken"]
            values = [stats.get("fulfilled", 0), stats.get("pending", 0), stats.get("broken", 0)]
            colors = ["#22c55e", "#f59e0b", "#ef4444"]
            donut_chart(labels, values, colors, "Promise Status Distribution")
    with col2:
        st.markdown("### 📈 Key Metrics")
        total = stats.get("total_promises", 0)
        if total > 0:
            fulfillment_rate = (stats.get("fulfilled", 0) / total) * 100
            st.metric("Fulfillment Rate", f"{fulfillment_rate:.1f}%")
            st.metric("Fulfilled Amount", format_currency(stats.get("fulfilled_amount", 0)))
