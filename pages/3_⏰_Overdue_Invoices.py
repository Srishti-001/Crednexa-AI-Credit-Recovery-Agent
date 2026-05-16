"""
⏰ Overdue Invoices — Detection, severity classification, and management.
──────────────────────────────────────────────────────────────
Shows:
  • KPI cards (total overdue, amount, avg / max days)
  • Severity donut chart  +  Aging bar chart
  • Tabbed invoice tables filtered by severity
  • Buttons to refresh overdue status & recalculate risk
"""

# ── Python path fix ──────────────────────────────────────────────────
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ── Initialise DB ────────────────────────────────────────────────────
from database.connection import init_db
init_db()

# ── Project imports ──────────────────────────────────────────────────
from components.sidebar import render_sidebar
from components.metrics_cards import metric_card, financial_metric
from components.data_tables import invoice_table
from components.charts import donut_chart, aging_chart
from services.overdue_detector import detect_overdue_invoices, get_overdue_summary
from services.analytics_service import get_overdue_aging_data
from utils.formatters import format_currency
from utils.constants import SEVERITY_COLORS

# ── Optional import: risk_scorer may import AI deps that are missing ──
try:
    from services.risk_scorer import recalculate_all_risks
    _HAS_RISK_SCORER = True
except ImportError:
    _HAS_RISK_SCORER = False

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Overdue Invoices | Crednexa AI",
    page_icon="⏰",
    layout="wide",
)
render_sidebar()

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #ef4444 0%, #f59e0b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">⏰ Overdue Invoices</h1>
<p style="color: #94a3b8;">Detect and manage overdue invoice payments</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# CONTROLS — Refresh / Recalculate
# ═══════════════════════════════════════════════════════════════════════
col_btn1, col_btn2, _ = st.columns([1, 1, 2])

with col_btn1:
    if st.button("🔄 Refresh Overdue Status", type="primary", use_container_width=True):
        overdue_list = detect_overdue_invoices()
        st.success(f"✅ Refreshed!  Found **{len(overdue_list)}** overdue invoices.")
        st.rerun()

with col_btn2:
    if _HAS_RISK_SCORER:
        if st.button("📊 Recalculate Risk Scores", use_container_width=True):
            with st.spinner("Calculating risk scores…"):
                result = recalculate_all_risks()
            st.success(f"✅ Updated risk scores for **{result['updated']}** clients")
            st.rerun()
    else:
        st.button("📊 Risk Scorer Not Available", disabled=True, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════
# KPI CARDS
# ═══════════════════════════════════════════════════════════════════════
summary = get_overdue_summary()

st.markdown("<br>", unsafe_allow_html=True)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    metric_card(
        "Total Overdue", str(summary["total_overdue"]),
        icon="⚠️", color="#ef4444",
    )
with kpi2:
    financial_metric(
        "Overdue Amount", summary["total_overdue_amount"],
        icon="💸", color="#f59e0b",
    )
with kpi3:
    metric_card(
        "Avg Days Overdue", f"{summary['avg_days_overdue']:.0f}",
        icon="📅", color="#8b5cf6",
    )
with kpi4:
    metric_card(
        "Max Days", str(summary["max_days_overdue"]),
        icon="🔥", color="#dc2626",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# CHARTS — Severity Donut  +  Aging Analysis
# ═══════════════════════════════════════════════════════════════════════
chart1, chart2 = st.columns(2)

with chart1:
    st.markdown("### 🎯 Severity Breakdown")
    sev_counts: dict = summary.get("severity_counts", {})
    if sum(sev_counts.values()) > 0:
        labels = list(sev_counts.keys())
        values = list(sev_counts.values())
        colors = [SEVERITY_COLORS.get(s, "#6B7280") for s in labels]
        donut_chart(labels, values, colors, "")
    else:
        st.info("No overdue invoices detected yet.")

with chart2:
    st.markdown("### 📆 Aging Analysis")
    aging: dict = get_overdue_aging_data()
    if sum(aging.values()) > 0:
        aging_chart(aging, "")
    else:
        st.info("No aging data available.")

# ═══════════════════════════════════════════════════════════════════════
# TABBED TABLES — All / Critical / High / Medium / Low
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📋 Overdue Invoices by Severity")

overdue_invoices = detect_overdue_invoices()

tab_all, tab_crit, tab_high, tab_med, tab_low = st.tabs(
    ["🔥 All", "🔴 Critical", "🟠 High", "🟡 Medium", "🟢 Low"]
)

with tab_all:
    if overdue_invoices:
        invoice_table(overdue_invoices)
    else:
        st.info("🎉 No overdue invoices — great job!")

with tab_crit:
    items = [i for i in overdue_invoices if i.get("severity") == "Critical"]
    invoice_table(items) if items else st.info("No Critical invoices")

with tab_high:
    items = [i for i in overdue_invoices if i.get("severity") == "High"]
    invoice_table(items) if items else st.info("No High-severity invoices")

with tab_med:
    items = [i for i in overdue_invoices if i.get("severity") == "Medium"]
    invoice_table(items) if items else st.info("No Medium-severity invoices")

with tab_low:
    items = [i for i in overdue_invoices if i.get("severity") == "Low"]
    invoice_table(items) if items else st.info("No Low-severity invoices")
