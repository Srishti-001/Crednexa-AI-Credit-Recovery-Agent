"""
Risk heatmap component — visualizes client risk distribution.
"""

import streamlit as st
import plotly.graph_objects as go
from utils.constants import RISK_COLORS


def render_risk_heatmap(risk_data: list):
    """
    Render a risk heatmap showing clients by risk score.
    risk_data: list of dicts with 'company_name', 'risk_score', 'total_outstanding', 'risk_category'.
    """
    if not risk_data:
        st.info("📊 No risk data available. Upload invoices and calculate risk scores first.")
        return

    # Sort by risk score
    sorted_data = sorted(risk_data, key=lambda x: x.get("risk_score", 0), reverse=True)[:20]

    companies = [d.get("company_name", "Unknown") for d in sorted_data]
    scores = [d.get("risk_score", 0) for d in sorted_data]
    amounts = [d.get("total_outstanding", 0) for d in sorted_data]
    categories = [d.get("risk_category", "Low") for d in sorted_data]

    colors = [RISK_COLORS.get(cat, "#6B7280") for cat in categories]

    fig = go.Figure(data=[go.Bar(
        y=companies,
        x=scores,
        orientation='h',
        marker_color=colors,
        text=[f"{s:.0f} | ₹{a:,.0f}" for s, a in zip(scores, amounts)],
        textposition='auto',
        textfont=dict(size=10, color='white'),
    )])

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="🔥 Client Risk Heatmap", font=dict(size=16, color="#e2e8f0")),
        xaxis_title="Risk Score",
        yaxis=dict(autorange="reversed"),
        height=max(300, len(companies) * 35),
        margin=dict(l=150, r=20, t=50, b=40),
        font=dict(color="#94a3b8"),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_risk_matrix(risk_data: list):
    """Render a simplified risk matrix as colored cards."""
    if not risk_data:
        return

    st.markdown("### 🎯 Risk Overview")
    categories = {"Critical": [], "High": [], "Medium": [], "Low": []}

    for d in risk_data:
        cat = d.get("risk_category", "Low")
        if cat in categories:
            categories[cat].append(d)

    cols = st.columns(4)
    for col, (cat, clients) in zip(cols, categories.items()):
        color = RISK_COLORS.get(cat, "#6B7280")
        with col:
            st.markdown(f"""
            <div style="
                background: {color}15;
                border: 1px solid {color}40;
                border-radius: 10px;
                padding: 1rem;
                text-align: center;
            ">
                <p style="color: {color}; font-size: 2rem; font-weight: 700; margin: 0;">
                    {len(clients)}
                </p>
                <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">{cat} Risk</p>
            </div>
            """, unsafe_allow_html=True)
