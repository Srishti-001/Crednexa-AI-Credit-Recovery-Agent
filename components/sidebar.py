"""
Sidebar component — shared navigation and global filters.
"""

import streamlit as st
import config


def render_sidebar():
    """Render the application sidebar with branding and info."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 1.5rem;
                font-weight: 800;
                margin: 0;
            ">💰 Crednexa AI</h1>
            <p style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.25rem;">
                Intelligent Credit Recovery & Finance Management Platform
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # App info
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <p style="color: #c4b5fd; font-size: 0.75rem; margin: 0;">
                📌 Version {config.APP_VERSION}<br>
                🤖 AI: {config.AI_PROVIDER.title()}<br>
                💱 Currency: {config.CURRENCY}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        if st.button("🔄 Refresh Data", use_container_width=True, key="sidebar_refresh"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown(
            "<p style='color: #64748b; font-size: 0.7rem; text-align: center;'>"
            "Built with ❤️ using Streamlit & AI</p>",
            unsafe_allow_html=True
        )
