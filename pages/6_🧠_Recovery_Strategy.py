"""
🧠 Recovery Strategy — AI-powered recovery strategy generation.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.filters import client_selector
from components.metrics_cards import metric_card
from services.recovery_strategist import generate_recovery_strategy
from models.client import get_all_clients
from models.recovery_strategy import get_active_strategies, get_strategies_by_client, update_strategy_status
from utils.constants import RISK_COLORS

st.set_page_config(page_title="Recovery Strategy | Crednexa AI", page_icon="🧠", layout="wide")
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">🧠 AI Recovery Strategy Engine</h1>
<p style="color: #94a3b8;">AI-powered recovery strategies tailored to each client</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Generate Strategy Section ───────────────────────────────────────────
st.markdown("### 🎯 Generate New Strategy")
col1, col2 = st.columns([2, 1])

with col1:
    clients = get_all_clients()
    selected_client = client_selector(clients, key="strategy_client")

with col2:
    if selected_client:
        st.markdown(f"""
        <div style="background: #1e293b; border-radius: 10px; padding: 1rem; margin-top: 1.5rem;">
            <p style="color: #e2e8f0; font-weight: 600; margin: 0;">
                {selected_client['company_name']}
            </p>
            <p style="color: #94a3b8; font-size: 0.8rem; margin: 0.25rem 0;">
                Outstanding: ₹{selected_client.get('total_outstanding', 0):,.2f}
            </p>
            <p style="color: {RISK_COLORS.get(selected_client.get('risk_category', 'Low'), '#6B7280')};
               font-size: 0.8rem; margin: 0;">
                Risk: {selected_client.get('risk_category', 'Low')}
            </p>
        </div>
        """, unsafe_allow_html=True)

if selected_client:
    if st.button("🧠 Generate AI Strategy", type="primary"):
        with st.spinner("🤖 AI is analyzing client profile and generating strategy..."):
            result = generate_recovery_strategy(selected_client["client_id"])

        if result["success"]:
            strategy = result["strategy"]
            st.success("✅ Strategy generated successfully!")

            strategy_colors = {
                "Negotiation": "#3b82f6", "Installment": "#22c55e",
                "Discount": "#f59e0b", "Legal": "#ef4444", "Write-Off": "#6B7280"
            }
            color = strategy_colors.get(strategy.get("strategy_type", ""), "#667eea")

            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}15 0%, {color}08 100%);
                border: 1px solid {color}40;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="color: {color}; margin: 0;">
                        {strategy.get('strategy_type', 'Recovery')} Strategy
                    </h3>
                    <span style="
                        background: {color}20; color: {color};
                        padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;
                    ">Priority: {strategy.get('priority', 'Medium')}</span>
                </div>
                <p style="color: #e2e8f0; line-height: 1.6; margin-bottom: 1rem;">
                    {strategy.get('description', '')}
                </p>
                <p style="color: #94a3b8; font-size: 0.85rem; font-style: italic;">
                    💡 {strategy.get('reasoning', '')}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Action steps
            actions = strategy.get("actions", [])
            if actions:
                st.markdown("#### 📋 Recommended Actions")
                for i, action in enumerate(actions, 1):
                    st.markdown(f"""
                    <div style="
                        background: #1e293b; border-left: 3px solid {color};
                        border-radius: 6px; padding: 0.75rem 1rem; margin: 0.5rem 0;
                    ">
                        <p style="color: #e2e8f0; margin: 0; font-size: 0.9rem;">
                            <strong>Step {i}:</strong> {action}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.error(f"❌ {result['error']}")

# ── Active Strategies ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Active Strategies")

active = get_active_strategies()
if active:
    for s in active:
        priority_colors = {
            "Critical": "#ef4444", "High": "#f59e0b",
            "Medium": "#3b82f6", "Low": "#22c55e"
        }
        color = priority_colors.get(s.get("priority", "Medium"), "#6B7280")

        with st.expander(f"🏢 {s.get('company_name', '')} — {s.get('strategy_type', '')} ({s.get('priority', '')} Priority)"):
            st.markdown(f"**Description:** {s.get('description', '')}")
            st.markdown(f"**Status:** {s.get('status', '')}")
            if s.get("ai_reasoning"):
                st.markdown(f"**AI Reasoning:** {s['ai_reasoning']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Mark Complete", key=f"complete_{s['strategy_id']}"):
                    update_strategy_status(s["strategy_id"], "Completed")
                    st.success("Strategy marked complete!")
                    st.rerun()
            with col2:
                if st.button("❌ Abandon", key=f"abandon_{s['strategy_id']}"):
                    update_strategy_status(s["strategy_id"], "Abandoned")
                    st.rerun()
else:
    st.info("No active strategies. Generate one above!")
