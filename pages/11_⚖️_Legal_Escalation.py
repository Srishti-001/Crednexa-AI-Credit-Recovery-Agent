"""
⚖️ Legal Escalation — Monitor and manage legal escalation alerts.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.metrics_cards import metric_card, financial_metric
from services.legal_escalation import check_legal_escalation_candidates, get_escalation_summary
from utils.formatters import format_currency
import config

st.set_page_config(page_title="Legal Escalation | Crednexa AI", page_icon="⚖️", layout="wide")
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #dc2626 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">⚖️ Legal Escalation Alerts</h1>
<p style="color: #94a3b8;">Monitor clients approaching legal escalation thresholds</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Thresholds ──────────────────────────────────────────────────────────
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #7c3aed15 0%, #dc262615 100%);
    border: 1px solid #7c3aed30;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
">
    <p style="color: #e2e8f0; font-weight: 600; margin: 0 0 0.5rem;">⚙️ Escalation Thresholds</p>
    <div style="display: flex; gap: 2rem;">
        <span style="color: #94a3b8; font-size: 0.85rem;">
            📅 Days Overdue: <strong style="color: #ef4444;">{config.LEGAL_ESCALATION_DAYS}+ days</strong>
        </span>
        <span style="color: #94a3b8; font-size: 0.85rem;">
            💰 Amount: <strong style="color: #ef4444;">{format_currency(config.LEGAL_ESCALATION_AMOUNT)}+</strong>
        </span>
        <span style="color: #94a3b8; font-size: 0.85rem;">
            💔 Broken Promises: <strong style="color: #ef4444;">2+</strong>
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Summary ─────────────────────────────────────────────────────────────
summary = get_escalation_summary()

col1, col2 = st.columns(2)
with col1:
    metric_card("Escalation Candidates", str(summary["total_candidates"]), icon="⚠️", color="#dc2626")
with col2:
    financial_metric("Total At-Risk Amount", summary["total_at_risk_amount"], icon="💸", color="#ef4444")

st.markdown("<br>", unsafe_allow_html=True)

# ── Candidate Cards ─────────────────────────────────────────────────────
candidates = summary["candidates"]

if not candidates:
    st.markdown("""
    <div style="
        background: #22c55e15;
        border: 1px solid #22c55e30;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
    ">
        <p style="font-size: 2rem; margin: 0;">✅</p>
        <p style="color: #22c55e; font-size: 1.2rem; font-weight: 600; margin: 0.5rem 0;">
            No Legal Escalation Required
        </p>
        <p style="color: #94a3b8; margin: 0;">
            All clients are within acceptable thresholds.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("### ⚠️ Clients Requiring Legal Attention")

    for candidate in candidates:
        with st.expander(
            f"🔴 {candidate['company_name']} — {format_currency(candidate['total_outstanding'])} "
            f"({candidate['max_overdue_days']} days)",
            expanded=True
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("**Escalation Reasons:**")
                for reason in candidate.get("escalation_reasons", []):
                    st.markdown(f"- ⚠️ {reason}")

                st.markdown(f"**Overdue Invoices:** {len(candidate.get('invoices', []))}")
                for inv in candidate.get("invoices", []):
                    st.markdown(
                        f"  - `{inv.get('invoice_number', '')}`: "
                        f"{format_currency(inv.get('amount', 0))} "
                        f"({inv.get('overdue_days', 0)} days overdue)"
                    )

            with col2:
                st.markdown(f"""
                <div style="background: #1e293b; border-radius: 10px; padding: 1rem;">
                    <p style="color: #94a3b8; font-size: 0.8rem; margin: 0 0 0.5rem;">Client Details</p>
                    <p style="color: #e2e8f0; margin: 0.2rem 0;">
                        📧 {candidate.get('contact_email', 'N/A')}
                    </p>
                    <p style="color: #e2e8f0; margin: 0.2rem 0;">
                        💔 {candidate.get('broken_promises', 0)} broken promises
                    </p>
                    <p style="color: #e2e8f0; margin: 0.2rem 0;">
                        📅 Max overdue: {candidate['max_overdue_days']} days
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("**Recommended Actions:**")
            st.markdown("""
            1. 📧 Send formal legal notice via registered mail
            2. 👨‍⚖️ Consult with legal counsel
            3. 📋 Document all communication history
            4. ⏳ Allow 15-day response window before filing
            """)
