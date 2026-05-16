"""
Email preview component — displays email content for review.
"""

import streamlit as st
from utils.constants import TONE_COLORS


def render_email_preview(subject: str, body: str, tone: str = "",
                         emotion: str = "", model: str = ""):
    """Render a styled email preview card."""
    tone_color = TONE_COLORS.get(tone, "#3b82f6")

    badges = ""
    if tone:
        badges += f'<span style="background: {tone_color}20; color: {tone_color}; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">🎯 {tone}</span> '
    if emotion:
        badges += f'<span style="background: #8b5cf620; color: #8b5cf6; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">😊 {emotion}</span> '
    if model:
        badges += f'<span style="background: #06b6d420; color: #06b6d4; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">🤖 {model}</span>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e1b4b 0%, #1e293b 100%);
        border: 1px solid {tone_color}40;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    ">
        <div style="margin-bottom: 0.75rem;">
            {badges}
        </div>
        <div style="
            border-bottom: 1px solid #334155;
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        ">
            <p style="color: #94a3b8; font-size: 0.75rem; margin: 0 0 0.25rem;">Subject:</p>
            <p style="color: #e2e8f0; font-size: 1rem; font-weight: 600; margin: 0;">{subject}</p>
        </div>
        <div>
            <p style="color: #94a3b8; font-size: 0.75rem; margin: 0 0 0.5rem;">Body:</p>
            <div style="
                color: #cbd5e1;
                font-size: 0.9rem;
                line-height: 1.6;
                white-space: pre-wrap;
            ">{body}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_email_card(email: dict, show_actions: bool = False):
    """Render a compact email card for lists."""
    tone_color = TONE_COLORS.get(email.get("tone", ""), "#3b82f6")

    st.markdown(f"""
    <div style="
        background: #1e293b;
        border-left: 4px solid {tone_color};
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <p style="color: #e2e8f0; font-weight: 600; margin: 0; font-size: 0.9rem;">
                {email.get('subject', 'No subject')[:60]}
            </p>
            <span style="
                background: {tone_color}20;
                color: {tone_color};
                padding: 2px 8px;
                border-radius: 8px;
                font-size: 0.7rem;
            ">{email.get('tone', '')}</span>
        </div>
        <p style="color: #64748b; font-size: 0.75rem; margin: 0.25rem 0 0;">
            📧 {email.get('company_name', '')} • {email.get('status', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)
