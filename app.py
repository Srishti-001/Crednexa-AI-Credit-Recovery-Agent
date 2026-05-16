"""
Crednexa AI & Finance Management
Main Application Entry Point
"""

import streamlit as st
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import init_db
from components.sidebar import render_sidebar
from components.metrics_cards import metric_card
from services.analytics_service import get_dashboard_metrics

# ── Page Configuration ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Crednexa AI | Intelligent Credit Recovery & Finance Management Platform",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Crednexa AI — Intelligent Credit Recovery & Finance Management Platform v1.0.0"
    }
)

# ── Initialize Database ────────────────────────────────────────────────
init_db()

# ── Custom CSS ──────────────────────────────────────────────────────────
css_path = Path(__file__).parent / "static" / "styles" / "main.css"
if css_path.exists():
    try:
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load custom CSS: {e}")

# ── Sidebar ─────────────────────────────────────────────────────────────
render_sidebar()

# ── Hero Section ────────────────────────────────────────────────────────
st.markdown("""
<div style="
    text-align: center;
    padding: 3rem 1rem;
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e293b 100%);
    border-radius: 16px;
    margin-bottom: 2rem;
    border: 1px solid #667eea30;
">
    <h1 style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f59e0b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 900;
        margin: 0;
        letter-spacing: -1px;
    ">💰 Crednexa AI</h1>
    <p style="
        color: #94a3b8;
        font-size: 1.1rem;
        margin: 0.75rem 0 0;
        font-weight: 300;
    ">Intelligent Credit Recovery & Finance Management Platform</p>
    <div style="margin-top: 1.5rem; display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
        <span style="background: #667eea20; color: #667eea; padding: 6px 16px; border-radius: 20px; font-size: 0.8rem;">
            🤖 AI Email Generation
        </span>
        <span style="background: #22c55e20; color: #22c55e; padding: 6px 16px; border-radius: 20px; font-size: 0.8rem;">
            📊 Risk Intelligence
        </span>
        <span style="background: #f59e0b20; color: #f59e0b; padding: 6px 16px; border-radius: 20px; font-size: 0.8rem;">
            🧠 Self-Learning AI
        </span>
        <span style="background: #8b5cf620; color: #8b5cf6; padding: 6px 16px; border-radius: 20px; font-size: 0.8rem;">
            ⚖️ Legal Escalation
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Quick Start Guide ──────────────────────────────────────────────────
st.markdown("## 🚀 Quick Start")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="background: #1e293b; border-radius: 12px; padding: 1.5rem; border-top: 3px solid #3b82f6; height: 200px;">
        <p style="font-size: 1.5rem; margin: 0;">📤</p>
        <h3 style="color: #e2e8f0; font-size: 1rem; margin: 0.5rem 0;">Step 1: Upload</h3>
        <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">
            Upload your invoice data via CSV or Excel file, or load the demo data.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: #1e293b; border-radius: 12px; padding: 1.5rem; border-top: 3px solid #f59e0b; height: 200px;">
        <p style="font-size: 1.5rem; margin: 0;">⏰</p>
        <h3 style="color: #e2e8f0; font-size: 1rem; margin: 0.5rem 0;">Step 2: Detect</h3>
        <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">
            Auto-detect overdue invoices with severity classification.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: #1e293b; border-radius: 12px; padding: 1.5rem; border-top: 3px solid #22c55e; height: 200px;">
        <p style="font-size: 1.5rem; margin: 0;">✉️</p>
        <h3 style="color: #e2e8f0; font-size: 1rem; margin: 0.5rem 0;">Step 3: Generate</h3>
        <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">
            AI generates follow-up emails with dynamic tone escalation.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="background: #1e293b; border-radius: 12px; padding: 1.5rem; border-top: 3px solid #8b5cf6; height: 200px;">
        <p style="font-size: 1.5rem; margin: 0;">✅</p>
        <h3 style="color: #e2e8f0; font-size: 1rem; margin: 0.5rem 0;">Step 4: Approve</h3>
        <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">
            Review and approve emails before sending. Full audit trail.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Feature Grid ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("## ✨ Features")

features = [
    ("📤 Invoice Upload", "Import CSV/Excel invoice data with validation", "#3b82f6"),
    ("⏰ Overdue Detection", "Auto-detect and classify overdue payments", "#f59e0b"),
    ("✉️ AI Email Generator", "Dynamic follow-up emails with tone control", "#22c55e"),
    ("🧠 Recovery Strategies", "AI-powered recovery plan generation", "#8b5cf6"),
    ("😊 Emotion Detection", "Detect client emotions from responses", "#ec4899"),
    ("🎯 Tone Optimization", "Self-learning tone effectiveness engine", "#06b6d4"),
    ("📊 Risk Dashboard", "Financial risk intelligence with heatmaps", "#ef4444"),
    ("✅ Approval Queue", "Human-in-the-loop before email sending", "#22c55e"),
    ("👤 Client History", "Complete timeline and payment history", "#3b82f6"),
    ("🤝 Promise Tracker", "Track payment commitments and fulfillment", "#f59e0b"),
    ("🔥 Priority Queue", "Score-ranked recovery priority list", "#dc2626"),
    ("⚖️ Legal Escalation", "Automated legal escalation alerts", "#7c3aed"),
]

cols = st.columns(4)
for i, (title, desc, color) in enumerate(features):
    with cols[i % 4]:
        st.markdown(f"""
        <div style="
            background: {color}08;
            border: 1px solid {color}20;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            min-height: 100px;
        ">
            <p style="color: #e2e8f0; font-weight: 600; margin: 0 0 0.25rem; font-size: 0.9rem;">
                {title}
            </p>
            <p style="color: #64748b; font-size: 0.75rem; margin: 0;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 1.5rem; border-top: 1px solid #334155;">
    <p style="color: #64748b; font-size: 0.8rem; margin: 0;">
        💰 Crednexa AI v1.0.0 • Built with Streamlit, Python & AI
    </p>
    <p style="color: #475569; font-size: 0.7rem; margin: 0.25rem 0 0;">
        👈 Navigate using the sidebar to get started
    </p>
</div>
""", unsafe_allow_html=True)
