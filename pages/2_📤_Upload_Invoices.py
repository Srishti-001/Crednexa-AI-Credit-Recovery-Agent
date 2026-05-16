"""
📤 Upload Invoices — CSV / Excel upload with validation and import.
──────────────────────────────────────────────────────────────
This page lets the user:
  • Upload a .csv or .xlsx file
  • Preview and validate the data
  • Import into the SQLite database
  • Download sample demo data or load it directly
  • View all invoices currently in the DB
"""

# ── Python path fix so "from models…" works inside pages/ ────────────
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

# ── Initialise DB before anything else ───────────────────────────────
from database.connection import init_db
init_db()

# ── Project imports ──────────────────────────────────────────────────
from components.sidebar import render_sidebar
from components.data_tables import invoice_table
from services.file_parser import (
    parse_uploaded_file,
    import_invoices,
    generate_sample_csv,
)
from models.invoice import get_all_invoices

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Upload Invoices | Crednexa AI",
    page_icon="📤",
    layout="wide",
)
render_sidebar()

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem; font-weight: 800; margin: 0;
">📤 Upload Invoices</h1>
<p style="color: #94a3b8;">Import your invoice data from CSV or Excel files</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 1 — File uploader + required-columns cheat-sheet
# ═══════════════════════════════════════════════════════════════════════
col_upload, col_info = st.columns([2, 1])

with col_upload:
    st.markdown("### 📁 Upload Invoice File")
    uploaded_file = st.file_uploader(
        "Drag and drop your CSV or Excel file here",
        type=["csv", "xlsx", "xls"],
        help="Required columns: invoice_number, company_name, contact_email, amount, issue_date, due_date",
    )

with col_info:
    st.markdown("### 📋 Required Columns")
    st.markdown("""
    <div style="background:#1e293b; border-radius:10px; padding:1rem; font-size:0.8rem;">
        <p style="color:#22c55e; margin:0.2rem 0;">✅ invoice_number</p>
        <p style="color:#22c55e; margin:0.2rem 0;">✅ company_name</p>
        <p style="color:#22c55e; margin:0.2rem 0;">✅ contact_email</p>
        <p style="color:#22c55e; margin:0.2rem 0;">✅ amount</p>
        <p style="color:#22c55e; margin:0.2rem 0;">✅ issue_date</p>
        <p style="color:#22c55e; margin:0.2rem 0;">✅ due_date</p>
        <hr style="border-color:#334155;">
        <p style="color:#94a3b8; margin:0.2rem 0;">📎 contact_name (optional)</p>
        <p style="color:#94a3b8; margin:0.2rem 0;">📎 phone (optional)</p>
        <p style="color:#94a3b8; margin:0.2rem 0;">📎 industry (optional)</p>
        <p style="color:#94a3b8; margin:0.2rem 0;">📎 amount_paid (optional)</p>
        <p style="color:#94a3b8; margin:0.2rem 0;">📎 payment_terms (optional)</p>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 2 — Parse + preview + import
# ═══════════════════════════════════════════════════════════════════════
if uploaded_file is not None:
    st.markdown("---")

    with st.spinner("📊 Parsing file…"):
        result = parse_uploaded_file(uploaded_file)

    if result["success"]:
        df: pd.DataFrame = result["data"]
        st.success(f"✅ File parsed successfully — **{len(df)}** invoice rows found.")

        # preview
        st.markdown("### 👀 Data Preview (first 10 rows)")
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

        # import controls
        st.markdown("---")
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if st.button("📥 Import All Invoices", type="primary", use_container_width=True):
                with st.spinner("Importing invoices into database…"):
                    imp = import_invoices(df)

                if imp["imported"] > 0:
                    st.success(
                        f"✅ Imported **{imp['imported']}** invoices! "
                        f"({imp['skipped']} duplicates skipped)"
                    )
                elif imp["skipped"] > 0:
                    st.info(f"All {imp['skipped']} invoices already exist — nothing new imported.")
                else:
                    st.warning("No invoices were imported.")

                if imp["errors"]:
                    with st.expander(f"⚠️ {len(imp['errors'])} row-level errors"):
                        for err in imp["errors"]:
                            st.warning(err)
        with c2:
            st.metric("Rows Found", len(df))

    else:
        # validation failed
        st.error("❌ File validation failed!")
        for err in result["errors"]:
            st.warning(f"⚠️ {err}")
        if result["data"] is not None:
            st.markdown("#### Raw data (for debugging)")
            st.dataframe(result["data"].head(5), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 3 — Demo data
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🧪 Demo Data")
st.markdown("Don't have an invoice file? Download a sample or load demo data directly.")

col_dl, col_load = st.columns([1, 3])

with col_dl:
    sample_df = generate_sample_csv()
    csv_bytes = sample_df.to_csv(index=False)
    st.download_button(
        "📥 Download Sample CSV",
        data=csv_bytes,
        file_name="sample_invoices.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_load:
    if st.button("🚀 Load Demo Data Directly", use_container_width=True):
        with st.spinner("Loading demo data…"):
            imp = import_invoices(sample_df)
        if imp["imported"] > 0:
            st.success(
                f"✅ Loaded **{imp['imported']}** demo invoices! "
                f"Go to the Dashboard or Overdue Invoices page to explore."
            )
            st.balloons()
        else:
            st.info("Demo data already loaded (all invoice numbers are duplicates).")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 4 — Current database contents
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📋 Current Invoices in Database")

all_invoices = get_all_invoices()
if all_invoices:
    st.info(f"📊 Total: **{len(all_invoices)}** invoices in the database")
    invoice_table(all_invoices)
else:
    st.info("No invoices in the database yet. Upload a file or load demo data above! ☝️")
