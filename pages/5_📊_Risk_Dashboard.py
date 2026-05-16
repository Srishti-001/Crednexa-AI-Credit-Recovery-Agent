"""
📊 Risk Dashboard — Financial Risk Intelligence with heatmap, charts, and queue.
──────────────────────────────────────────────────────────────
Displays:
  • Risk distribution donut + risk matrix cards
  • Client risk heatmap (top 20)
  • Priority recovery queue
  • Per-client risk drill-down
  • Risk recalculation trigger
"""

# ── path fix ──
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ── DB init ──
from database.connection import init_db
init_db()

# ── project imports ──
from components.sidebar import render_sidebar
from components.metrics_cards import metric_card, financial_metric
from components.charts import donut_chart, bar_chart, gauge_chart
from components.risk_heatmap import render_risk_heatmap, render_risk_matrix
from components.filters import client_selector
from services.risk_engine import (
    recalculate_all_risks, calculate_client_risk,
    get_priority_queue, get_risk_overview,
)
from services.analytics_service import get_dashboard_metrics
from models.client import get_all_clients
from models.risk_score import get_latest_risk_score, get_all_latest_risk_scores, get_risk_history
from utils.formatters import format_currency
from utils.constants import RISK_COLORS

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Risk Dashboard | Crednexa AI",
    page_icon="📊",
    layout="wide",
)
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #ef4444 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">📊 Financial Risk Intelligence Dashboard</h1>
<p style="color: #94a3b8;">
    Multi-factor risk analysis, heatmaps, and priority recovery queue
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Controls ─────────────────────────────────────────────────────────
c1, c2, _ = st.columns([1, 1, 2])
with c1:
    if st.button("🔄 Recalculate All Risk Scores", type="primary", use_container_width=True):
        with st.spinner("Crunching numbers…"):
            res = recalculate_all_risks()
        st.success(f"✅ Updated risk scores for **{res['updated']}** clients")
        st.rerun()
with c2:
    pass  # spacer

# ═══════════════════════════════════════════════════════════════════════
# KPI ROW
# ═══════════════════════════════════════════════════════════════════════
metrics = get_dashboard_metrics()
risk_ov = get_risk_overview()
dist    = risk_ov.get("distribution", {})

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("Total Clients", str(metrics["total_clients"]),
                icon="👥", color="#3b82f6")
with k2:
    critical = dist.get("Critical", 0)
    metric_card("Critical Risk", str(critical), icon="🔥", color="#dc2626")
with k3:
    high = dist.get("High", 0)
    metric_card("High Risk", str(high), icon="⚠️", color="#ef4444")
with k4:
    financial_metric("Total Overdue", metrics["total_overdue"],
                     icon="💸", color="#f59e0b")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# RISK DISTRIBUTION + MATRIX
# ═══════════════════════════════════════════════════════════════════════
chart1, chart2 = st.columns(2)

with chart1:
    st.markdown("### 🎯 Risk Category Distribution")
    if dist and sum(dist.values()) > 0:
        labels = list(dist.keys())
        values = list(dist.values())
        colors = [RISK_COLORS.get(l, "#6B7280") for l in labels]
        donut_chart(labels, values, colors, "")
    else:
        st.info("No risk scores yet. Click **Recalculate** above.")

with chart2:
    st.markdown("### 📈 Recovery Rate")
    gauge_chart(metrics["recovery_rate"], "Portfolio Recovery Rate")

# ── Risk matrix cards ──
st.markdown("<br>", unsafe_allow_html=True)
top_risk = risk_ov.get("top_risk_clients", [])
if top_risk:
    render_risk_matrix(top_risk)

# ═══════════════════════════════════════════════════════════════════════
# RISK HEATMAP — top 20 riskiest clients
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🔥 Client Risk Heatmap")

all_scores = get_all_latest_risk_scores()
if all_scores:
    render_risk_heatmap(all_scores)
else:
    st.info("Calculate risk scores to generate the heatmap.")

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY RECOVERY QUEUE
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🏆 Priority Recovery Queue")

queue = get_priority_queue()

if queue:
    st.caption(
        "Priority Score = Risk Score (40%) + Normalised Days (30%) + Normalised Amount (30%)"
    )

    for rank, c in enumerate(queue[:15], 1):
        rc = RISK_COLORS.get(c["risk_category"], "#6B7280")
        bar_w = min(c["priority_score"] / max(queue[0]["priority_score"], 1) * 100, 100)

        st.markdown(f"""
        <div style="
            background:#1e293b; border-left:4px solid {rc};
            border-radius:8px; padding:0.8rem 1.2rem; margin:0.4rem 0;
            display:flex; align-items:center; gap:1.2rem;
        ">
            <div style="
                min-width:36px; height:36px; border-radius:50%;
                background:{rc}20; display:flex; align-items:center;
                justify-content:center; font-weight:800; color:{rc};
            ">#{rank}</div>
            <div style="flex:1;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#e2e8f0; font-weight:700;">{c['company_name']}</span>
                    <span style="background:{rc}20; color:{rc}; padding:2px 10px;
                                 border-radius:10px; font-size:0.75rem; font-weight:600;">
                        {c['risk_category']}</span>
                </div>
                <div style="display:flex; gap:1.5rem; margin-top:0.2rem;">
                    <span style="color:#94a3b8; font-size:0.8rem;">
                        💸 {format_currency(c['total_overdue'])}</span>
                    <span style="color:#94a3b8; font-size:0.8rem;">
                        📋 {c['overdue_count']} inv</span>
                    <span style="color:#94a3b8; font-size:0.8rem;">
                        📅 {c['max_days_overdue']}d max</span>
                    <span style="color:#94a3b8; font-size:0.8rem;">
                        🎯 {c['priority_score']:.1f}</span>
                </div>
                <div style="margin-top:0.4rem; height:4px; background:#334155;
                            border-radius:2px; overflow:hidden;">
                    <div style="width:{bar_w}%; height:100%;
                                background:linear-gradient(90deg,{rc},{rc}80);
                                border-radius:2px;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No overdue clients in the queue. Upload invoices to get started.")

# ═══════════════════════════════════════════════════════════════════════
# CLIENT DRILL-DOWN
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🔍 Client Risk Drill-Down")

all_clients = get_all_clients()
drill_client = client_selector(all_clients, key="risk_drill")

if drill_client:
    c1, c2 = st.columns([1, 1])

    with c1:
        if st.button("📊 (Re)calculate Risk", key="drill_calc"):
            with st.spinner("Calculating…"):
                r = calculate_client_risk(drill_client["client_id"])
            st.success(f"Score: **{r['risk_score']:.1f}/100** — {r['risk_category']}")
            st.rerun()

    risk = get_latest_risk_score(drill_client["client_id"])
    if risk:
        rc = RISK_COLORS.get(risk.get("risk_category", "Low"), "#6B7280")

        with c2:
            metric_card("Risk Score",
                        f"{risk['risk_score']:.0f}/100 — {risk['risk_category']}",
                        icon="🎯", color=rc)

        # contributing factors
        factors = risk.get("contributing_factors", {})
        if isinstance(factors, str):
            import json
            try:
                factors = json.loads(factors)
            except Exception:
                factors = {}

        if factors:
            st.markdown("#### Contributing Factors")
            f1, f2, f3, f4 = st.columns(4)
            with f1:
                metric_card("Overdue Amount",
                            format_currency(factors.get("overdue_amount", 0)),
                            icon="💸", color="#ef4444")
            with f2:
                metric_card("Avg Days Overdue",
                            f"{factors.get('avg_overdue_days', 0):.0f}",
                            icon="📅", color="#f59e0b")
            with f3:
                metric_card("Reliability",
                            f"{factors.get('payment_reliability', 1):.0%}",
                            icon="📈", color="#22c55e")
            with f4:
                metric_card("Broken Promises",
                            str(factors.get("broken_promises", 0)),
                            icon="💔", color="#dc2626")

        # risk trend
        history = get_risk_history(drill_client["client_id"])
        if len(history) > 1:
            st.markdown("#### 📈 Risk Score Trend")
            from components.charts import line_chart
            dates  = [h.get("calculated_at", "")[:10] for h in reversed(history)]
            scores = [h.get("risk_score", 0) for h in reversed(history)]
            line_chart(dates, scores, "", "Date", "Score", rc)
    else:
        st.info("No risk data. Click **Calculate Risk** above.")
