"""
Global configuration for Crednexa AI & Finance Management App.
Loads environment variables and defines application-wide settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "finance_recovery.db"
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"

# Ensure directories exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Primary AI provider: "gemini" or "openai"
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")

# ── AI Model Settings ─────────────────────────────────────────────────
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "2048"))

# ── Email Settings ─────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

# ── Overdue Thresholds (days) ──────────────────────────────────────────
SEVERITY_THRESHOLDS = {
    "Low": 30,
    "Medium": 60,
    "High": 90,
    "Critical": 120,
}

# ── Tone Escalation Mapping ───────────────────────────────────────────
TONE_LEVELS = {
    1: "Friendly",
    2: "Professional",
    3: "Firm",
    4: "Urgent",
    5: "Legal",
}

# Days overdue → tone level mapping
TONE_ESCALATION = {
    (0, 15): 1,       # Friendly
    (16, 30): 2,      # Professional
    (31, 60): 3,      # Firm
    (61, 90): 4,      # Urgent
    (91, 9999): 5,    # Legal
}

# ── Risk Scoring Weights ──────────────────────────────────────────────
RISK_WEIGHTS = {
    "overdue_amount": 0.30,
    "overdue_days": 0.25,
    "payment_history": 0.20,
    "broken_promises": 0.15,
    "communication_response": 0.10,
}

# ── Legal Escalation Thresholds ────────────────────────────────────────
LEGAL_ESCALATION_DAYS = int(os.getenv("LEGAL_ESCALATION_DAYS", "120"))
LEGAL_ESCALATION_AMOUNT = float(os.getenv("LEGAL_ESCALATION_AMOUNT", "100000"))

# ── Application Settings ──────────────────────────────────────────────
APP_NAME = "Crednexa AI"
APP_VERSION = "1.0.0"
CURRENCY = os.getenv("CURRENCY", "INR")
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%d %b %Y"
