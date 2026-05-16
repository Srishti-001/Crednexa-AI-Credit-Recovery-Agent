"""
🔥 Priority Recovery Queue — Ranked clients by recovery priority score.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.metrics_cards import metric_card
from services.risk_scorer import get_priority_queue, recalculate_all_risks
from utils.formatters import format_currency
from utils.constants import RISK_COLORS

st.set_page_config(page_title="Priority Queue | Crednexa AI", page_icon="🔥", layout="wide")
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #ef4444 0%, #f59e0b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">🔥 Priority Recovery Queue</h1>
<p style="color: #94a3b8;">Clients ranked by composite priority score for recovery action</p>
""", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Recalculate Priorities", type="primary", use_container_width=True):
        with st.spinner("Recalculating..."):
            recalculate_all_risks()
        st.success("✅ Priorities recalculated!")
        st.rerun()

# ── Priority Queue ──────────────────────────────────────────────────────
queue = get_priority_queue()

if not queue:
    st.info("📋 No overdue clients in the queue. Upload invoices to get started.")
else:
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Clients in Queue", str(len(queue)), icon="👥", color="#ef4444")
    with col2:
        total_overdue = sum(c["total_overdue"] for c in queue)
        metric_card("Total At Risk", format_currency(total_overdue), icon="💸", color="#f59e0b")
    with col3:
        critical = len([c for c in queue if c["risk_category"] == "Critical"])
        metric_card("Critical Clients", str(critical), icon="🔥", color="#dc2626")
    with col4:
        avg_score = sum(c["priority_score"] for c in queue) / len(queue)
        metric_card("Avg Priority Score", f"{avg_score:.1f}", icon="📊", color="#8b5cf6")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Client Cards ────────────────────────────────────────────────────
    for rank, client in enumerate(queue, 1):
        risk_color = RISK_COLORS.get(client["risk_category"], "#6B7280")
        priority = client["priority_score"]
        bar_width = min(priority / (queue[0]["priority_score"] if queue[0]["priority_score"] > 0 else 1) * 100, 100)

        st.markdown(f"""
        <div style="
            background: #1e293b;
            border-left: 4px solid {risk_color};
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 1.5rem;
        ">
            <div style="
                min-width: 40px;
                height: 40px;
                border-radius: 50%;
                background: {risk_color}20;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                color: {risk_color};
                font-size: 1rem;
            ">#{rank}</div>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <p style="color: #e2e8f0; font-weight: 700; margin: 0; font-size: 1rem;">
                        {client['company_name']}
                    </p>
                    <span style="
                        background: {risk_color}20; color: {risk_color};
                        padding: 2px 10px; border-radius: 10px; font-size: 0.75rem; font-weight: 600;
                    ">{client['risk_category']} Risk</span>
                </div>
                <div style="display: flex; gap: 2rem; margin-top: 0.3rem;">
                    <span style="color: #94a3b8; font-size: 0.8rem;">
                        💸 {format_currency(client['total_overdue'])}
                    </span>
                    <span style="color: #94a3b8; font-size: 0.8rem;">
                        📋 {client['overdue_count']} invoices
                    </span>
                    <span style="color: #94a3b8; font-size: 0.8rem;">
                        📅 {client['max_days_overdue']} days max
                    </span>
                    <span style="color: #94a3b8; font-size: 0.8rem;">
                        🎯 Score: {client['priority_score']:.1f}
                    </span>
                </div>
                <div style="
                    margin-top: 0.5rem;
                    height: 4px;
                    background: #334155;
                    border-radius: 2px;
                    overflow: hidden;
                ">
                    <div style="
                        width: {bar_width}%;
                        height: 100%;
                        background: linear-gradient(90deg, {risk_color}, {risk_color}80);
                        border-radius: 2px;
                    "></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"📊 Priority Score = Risk Score (40%) + Days Overdue (30%) + Outstanding Amount (30%)")
