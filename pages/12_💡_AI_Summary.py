"""
💡 AI Finance Summary — AI-generated financial insights and forecasts.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.metrics_cards import metric_card
from services.analytics_service import get_dashboard_metrics, get_risk_overview
from models.payment_promise import get_promise_stats
from models.risk_score import get_all_latest_risk_scores
from ai.prompts.summary_prompts import get_finance_summary_prompt
from ai import gemini_client, openai_client
import config

st.set_page_config(page_title="AI Summary | Crednexa AI", page_icon="💡", layout="wide")
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #f59e0b 0%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">💡 AI Finance Summary</h1>
<p style="color: #94a3b8;">AI-generated financial insights, analysis, and actionable recommendations</p>
""", unsafe_allow_html=True)

st.markdown("---")

def _generate_template_summary(metrics: dict, risk_overview: dict, promise_rate: float) -> str:
    """Generate a template summary when no AI is available."""
    high_risk = risk_overview.get("distribution", {}).get("High", 0)
    critical_risk = risk_overview.get("distribution", {}).get("Critical", 0)
    return f"""## Executive Summary

Your credit recovery portfolio contains {metrics['total_invoices']} invoices totaling ₹{metrics['total_amount']:,.2f}.
Currently, {metrics['overdue_count']} invoices are overdue with a total outstanding amount of ₹{metrics['total_overdue']:,.2f}.

## Key Performance Indicators
- **Recovery Rate:** {metrics['recovery_rate']}%
- **Average Days Overdue:** {metrics['avg_overdue_days']:.0f} days
- **Promise Fulfillment Rate:** {promise_rate:.1f}%

## Risk Assessment
The portfolio contains clients across various risk levels, including **{high_risk} High Risk** and **{critical_risk} Critical Risk** clients. Active monitoring and follow-up are highly recommended for these groups.

## Recommendations
1. **Prioritize High-Risk Clients** — Focus recovery efforts on critical and high-risk clients first.
2. **Increase Follow-Up Frequency** — Clients with 60+ days overdue need more active engagement.
3. **Leverage Payment Plans** — Offer installment options for large outstanding amounts.
4. **Monitor Promises** — Track payment promise fulfillment to identify unreliable clients.

_This summary was generated from template data. Connect an AI provider for more detailed analysis._"""

# ── Generate Summary ────────────────────────────────────────────────────
if st.button("🧠 Generate AI Financial Summary", type="primary"):
    with st.spinner("🤖 AI is analyzing your portfolio..."):
        metrics = get_dashboard_metrics()
        risk_overview = get_risk_overview()
        promise_stats = get_promise_stats()
        top_risk = get_all_latest_risk_scores()[:5]

        # Calculate promise fulfillment rate
        total_promises = promise_stats.get("total_promises", 0)
        fulfilled = promise_stats.get("fulfilled", 0)
        promise_rate = (fulfilled / total_promises * 100) if total_promises > 0 else 0

        # Build top debtors list
        top_debtors = []
        for t in top_risk:
            top_debtors.append({
                "company_name": t.get("company_name", "Unknown"),
                "total_outstanding": t.get("total_outstanding", 0),
                "risk_category": t.get("risk_category", "Medium"),
            })

        prompt = get_finance_summary_prompt(
            total_invoices=metrics["total_invoices"],
            total_amount=metrics["total_amount"],
            total_collected=metrics["total_collected"],
            total_overdue=metrics["total_overdue"],
            overdue_count=metrics["overdue_count"],
            avg_overdue_days=metrics["avg_overdue_days"],
            risk_distribution=risk_overview.get("distribution", {}),
            top_debtors=top_debtors,
            recovery_rate=metrics["recovery_rate"],
            promise_fulfillment_rate=promise_rate,
        )

        # Generate via AI
        ai_client = None
        model_name = ""
        if config.AI_PROVIDER == "gemini" and gemini_client.is_configured():
            ai_client = gemini_client
            model_name = "Gemini"
        elif openai_client.is_configured():
            ai_client = openai_client
            model_name = "OpenAI"

        if ai_client:
            try:
                summary = ai_client.generate_summary(prompt)
                st.session_state["ai_summary"] = summary
                st.session_state["ai_model"] = model_name
            except Exception as e:
                st.error(f"❌ AI generation failed: {e}")
        else:
            st.warning("⚠️ No AI provider configured. Please add your API key to the .env file.")
            st.session_state["ai_summary"] = _generate_template_summary(metrics, risk_overview, promise_rate)
            st.session_state["ai_model"] = "Template"

# ── Display Summary ─────────────────────────────────────────────────────
if st.session_state.get("ai_summary"):
    model = st.session_state.get("ai_model", "AI")

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e1b4b 0%, #1e293b 100%);
        border: 1px solid #667eea40;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="color: #e2e8f0; margin: 0;">📊 Financial Intelligence Report</h3>
            <span style="
                background: #667eea20; color: #667eea;
                padding: 4px 12px; border-radius: 12px; font-size: 0.75rem;
            ">🤖 Generated by {model}</span>
        </div>
        <div style="color: #cbd5e1; line-height: 1.8; font-size: 0.95rem; white-space: pre-wrap;">
{st.session_state['ai_summary']}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Quick Stats ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Quick Portfolio Stats")

metrics = get_dashboard_metrics()
col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Invoices", str(metrics["total_invoices"]), icon="📋", color="#3b82f6")
with col2:
    metric_card("Recovery Rate", f"{metrics['recovery_rate']}%", icon="📈", color="#22c55e")
with col3:
    metric_card("Overdue Count", str(metrics["overdue_count"]), icon="⏰", color="#ef4444")
with col4:
    metric_card("Avg Days Overdue", f"{metrics['avg_overdue_days']:.0f}", icon="📅", color="#f59e0b")


