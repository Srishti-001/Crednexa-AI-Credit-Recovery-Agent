"""
📧 AI Email Center — Generate, preview, and manage AI follow-up emails.
──────────────────────────────────────────────────────────────
Combines:
  • Client & invoice selector
  • Auto tone detection (self-learning)
  • Emotion analysis on client replies
  • AI email generation (Gemini / OpenAI / template)
  • Inline email preview & approval submission
  • Tone feedback recording
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
from components.email_preview import render_email_preview
from components.metrics_cards import metric_card
from components.filters import client_selector
from services.email_generator import generate_follow_up_email, generate_demo_email
from services.learning_engine import (
    determine_optimal_tone, get_all_tones,
    record_tone_outcome, get_client_learning_data,
)
from services.sentiment_analysis import analyse_sentiment
from models.client import get_all_clients
from models.invoice import get_invoices_by_client
from models.email_log import (
    get_email_stats, get_emails_by_status,
    update_email_status, update_email_content,
)
from utils.constants import TONE_COLORS

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Email Center | Crednexa AI",
    page_icon="📧",
    layout="wide",
)
render_sidebar()

st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">📧 AI Email Center</h1>
<p style="color: #94a3b8;">
    Generate AI-powered follow-up emails with dynamic tone escalation &amp; emotion awareness
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 1 — email KPI snapshot
# ═══════════════════════════════════════════════════════════════════════
e_stats = get_email_stats() or {}
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("Total Emails", str(e_stats.get("total_emails", 0)),
                icon="✉️", color="#3b82f6")
with k2:
    metric_card("Sent", str(e_stats.get("sent_count", 0)),
                icon="📤", color="#22c55e")
with k3:
    metric_card("Pending", str(e_stats.get("pending_count", 0)),
                icon="🔍", color="#f59e0b")
with k4:
    metric_card("Drafts", str(e_stats.get("draft_count", 0)),
                icon="📝", color="#6B7280")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 2 — Generate new email
# ═══════════════════════════════════════════════════════════════════════
st.markdown("## ✨ Generate New Email")

clients = get_all_clients()

if not clients:
    st.info("No clients found. Upload invoices first on the **📤 Upload Invoices** page.")
    st.markdown("---")
    st.markdown("### 🧪 Demo Preview")
    demo_tone = st.selectbox("Demo Tone", ["Friendly", "Professional", "Firm", "Urgent", "Legal"],
                             key="demo_tone")
    if st.button("🎯 Generate Demo Email"):
        with st.spinner("Generating…"):
            demo = generate_demo_email(tone=demo_tone)
        if demo.get("success"):
            render_email_preview(demo["subject"], demo["body"], demo_tone, model=demo.get("model", ""))
        else:
            st.error(f"Error: {demo.get('error')}")
    st.stop()

# ── client + invoice selection ──
col_client, col_inv = st.columns(2)

with col_client:
    st.markdown("### 👤 Select Client")
    selected_client = client_selector(clients, key="email_client")

selected_invoice = None
overdue_days = 0

with col_inv:
    if selected_client:
        st.markdown("### 📄 Select Invoice")
        invoices = get_invoices_by_client(selected_client["client_id"])
        overdue_invs = [i for i in invoices
                        if i.get("status") in ("Overdue", "Partially Paid")]
        if overdue_invs:
            options = {
                f"{i['invoice_number']} — ₹{i['amount']:,.2f} "
                f"({i.get('overdue_days', 0)}d overdue)": i
                for i in overdue_invs
            }
            sel_key = st.selectbox("Choose overdue invoice", list(options.keys()),
                                   key="inv_sel")
            selected_invoice = options[sel_key]
            overdue_days = selected_invoice.get("overdue_days", 0)
        else:
            st.warning("No overdue invoices for this client.")

# ── tone + emotion config ──
if selected_client and selected_invoice:
    st.markdown("---")
    st.markdown("### 🎯 Tone & Emotion Configuration")

    t1, t2, t3 = st.columns(3)

    with t1:
        auto = determine_optimal_tone(selected_client["client_id"], overdue_days)
        tone_color = TONE_COLORS.get(auto["tone"], "#3b82f6")
        st.markdown(f"""
        <div style="background:#1e293b; border-left:4px solid {tone_color};
                    border-radius:10px; padding:1rem;">
            <p style="color:#94a3b8; font-size:0.75rem; margin:0;">
                🤖 Auto-Detected Tone ({auto['source']})</p>
            <p style="color:#e2e8f0; font-size:1.2rem; font-weight:700; margin:0.2rem 0;">
                {auto['tone']}</p>
            <p style="color:#64748b; font-size:0.7rem; margin:0;">
                Level {auto['level']} • {overdue_days} days overdue</p>
        </div>
        """, unsafe_allow_html=True)

    with t2:
        all_tones = get_all_tones()
        tone_opts = ["Auto (recommended)"] + [f"{t['emoji']} {t['tone']}" for t in all_tones]
        tone_choice = st.selectbox("Override Tone", tone_opts, key="tone_ov")
        tone_override = None
        if tone_choice != "Auto (recommended)":
            tone_override = tone_choice.split(" ", 1)[1]

    with t3:
        client_response = st.text_area(
            "Client's Last Response (optional)",
            placeholder="Paste the client's reply for emotion detection…",
            height=110, key="cli_resp",
        )

    # quick sentiment preview
    if client_response:
        with st.spinner("Analysing sentiment…"):
            sent = analyse_sentiment(client_response)
        st.markdown(f"""
        <div style="background:#1e293b; border-radius:8px; padding:0.75rem; margin-top:0.5rem;">
            <span style="color:#8b5cf6; font-weight:600;">
                😊 {sent['emotion']}</span>
            <span style="color:#64748b;"> • Confidence {sent['confidence']:.0%}</span>
            <span style="color:#64748b;"> • Intent: {sent['intent']}</span>
            <span style="color:#475569; font-size:0.75rem;"> ({sent['model']})</span>
        </div>
        """, unsafe_allow_html=True)

    additional = st.text_input("Additional Context (optional)",
                               placeholder="E.g. 'Client promised last month'",
                               key="add_ctx")

    # ── generate button ──
    st.markdown("---")
    g1, g2 = st.columns([1, 3])
    with g1:
        gen_btn = st.button("🚀 Generate Email", type="primary", use_container_width=True)

    if gen_btn:
        with st.spinner("🤖 AI is crafting your email…"):
            result = generate_follow_up_email(
                client_id=selected_client["client_id"],
                company_name=selected_client["company_name"],
                contact_name=selected_client.get("contact_name", ""),
                contact_email=selected_client.get("contact_email", ""),
                invoice_number=selected_invoice["invoice_number"],
                amount=selected_invoice["amount"],
                currency=selected_invoice.get("currency", "INR"),
                due_date=selected_invoice.get("due_date", ""),
                overdue_days=overdue_days,
                tone_override=tone_override,
                client_response=client_response,
                additional_context=additional,
            )

        if result["success"]:
            st.success("✅ Email generated!")

            render_email_preview(
                subject=result["subject"],
                body=result["body"],
                tone=result["tone"],
                emotion=result.get("emotion", ""),
                model=result.get("model", ""),
            )

            # action buttons
            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button("📨 Submit for Approval", use_container_width=True):
                    update_email_status(result["email_id"], "Pending Approval")
                    st.success("Submitted for approval!")
            with a2:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.rerun()
            with a3:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.code(f"Subject: {result['subject']}\n\n{result['body']}")
        else:
            st.error(f"❌ {result.get('error', 'Unknown error')}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 3 — Tone Feedback Recorder
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
with st.expander("📝 Record Tone Feedback (Self-Learning)", expanded=False):
    st.markdown("Record a client's response to improve future tone recommendations.")

    sent_emails = get_emails_by_status("Sent")
    if sent_emails:
        email_opts = {
            f"{e['company_name']} — {e['subject'][:40]}": e for e in sent_emails[:20]
        }
        sel_email = st.selectbox("Select a sent email", list(email_opts.keys()), key="fb_email")
        chosen_email = email_opts[sel_email]

        fb_response = st.text_area("Client's response text",
                                   placeholder="Paste the client's reply…",
                                   key="fb_resp")
        fb_outcome = st.selectbox("Or manually set outcome",
                                  ["(auto-detect)", "Positive", "Neutral", "Negative", "No Response"],
                                  key="fb_out")

        if st.button("💾 Record Feedback", key="fb_save"):
            manual = fb_outcome if fb_outcome != "(auto-detect)" else None
            res = record_tone_outcome(
                email_id=chosen_email["email_id"],
                client_response=fb_response,
                manual_outcome=manual,
            )
            if res.get("success"):
                st.success(f"✅ Recorded: {res['outcome']} (score {res['score']:.1f})")
            else:
                st.error(res.get("error", "Unknown error"))
    else:
        st.info("No sent emails yet. Generate and send some emails first.")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 4 — Learning data for selected client
# ═══════════════════════════════════════════════════════════════════════
if selected_client:
    st.markdown("---")
    with st.expander(f"🧠 Tone Learning Data for {selected_client['company_name']}",
                     expanded=False):
        ld = get_client_learning_data(selected_client["client_id"])
        if ld["data_points"]:
            st.markdown(f"**Data points:** {ld['data_points']}  •  "
                        f"**Recommended tone:** {ld['recommended_tone'] or 'Not enough data'}")
            for h in ld["history"][:10]:
                st.markdown(
                    f"- **{h.get('tone_used', '')}** → "
                    f"{h.get('detected_outcome', 'N/A')} "
                    f"(score {h.get('effectiveness_score', 0):.1f})"
                )
        else:
            st.info("No feedback data for this client yet. "
                    "Record feedback above to enable self-learning.")
