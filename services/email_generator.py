"""
Email Generator — AI-powered follow-up email service (rewritten).
──────────────────────────────────────────────────────────────
Orchestrates:
  • Tone selection (via learning_engine)
  • Sentiment detection on client replies (via sentiment_analysis)
  • AI content generation (Gemini → OpenAI → template fallback)
  • Email log persistence
  • Audit trail

This file REPLACES the earlier services/email_generator.py.
"""

from datetime import datetime

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

import config
from database.connection import init_db
from ai import gemini_client, openai_client
from ai.response_parser import extract_email_content
from models.email_log import create_email_log
from models.invoice import get_invoice_by_number
from services.learning_engine import determine_optimal_tone
from services.sentiment_analysis import analyse_sentiment
from services.audit_service import log_action


# ════════════════════════════════════════════════════════════════════════
# PROMPT
# ════════════════════════════════════════════════════════════════════════

def _build_email_prompt(
    company_name: str, contact_name: str, invoice_number: str,
    amount: float, currency: str, due_date: str, overdue_days: int,
    tone: str, emotion: str = "", additional_context: str = "",
) -> str:
    """Construct a detailed LLM prompt for email generation."""

    tone_guidance = {
        "Friendly":     "warm, empathetic, helpful — assume the delay is accidental",
        "Professional": "polite yet clear — state facts, set expectations",
        "Firm":         "direct and assertive — emphasise the seriousness",
        "Urgent":       "high urgency — mention consequences of further delay",
        "Legal":        "formal legal tone — reference potential legal proceedings",
    }

    emotion_line = ""
    if emotion and emotion != "Neutral":
        emotion_line = f"\nThe client's recent tone was detected as **{emotion}**. Adjust your language empathetically.\n"

    context_line = ""
    if additional_context:
        context_line = f"\nAdditional context: {additional_context}\n"

    return f"""You are a professional credit recovery specialist writing a follow-up
email for an Indian B2B business.

INVOICE DETAILS
  Client    : {company_name}
  Contact   : {contact_name or 'Sir/Madam'}
  Invoice # : {invoice_number}
  Amount    : {currency} {amount:,.2f}
  Due Date  : {due_date}
  Overdue   : {overdue_days} days

TONE: {tone}
Guidance: {tone_guidance.get(tone, 'professional and clear')}
{emotion_line}{context_line}
Write the email as a JSON object:
{{
  "subject": "Short, clear subject line",
  "body": "Full email body with greeting, context, clear ask, and sign-off"
}}

Rules:
- Sign off as "Accounts Receivable Team"
- Keep the body under 200 words
- Reference the invoice number and exact amount
- Do NOT include markdown formatting in the body
- Respond ONLY with the JSON object"""


# ════════════════════════════════════════════════════════════════════════
# MAIN — generate follow-up email
# ════════════════════════════════════════════════════════════════════════

def generate_follow_up_email(
    client_id: str,
    company_name: str,
    contact_name: str,
    contact_email: str,
    invoice_number: str,
    amount: float,
    currency: str = "INR",
    due_date: str = "",
    overdue_days: int = 0,
    tone_override: str | None = None,
    client_response: str = "",
    additional_context: str = "",
) -> dict:
    """
    End-to-end email generation.

    Steps:
      1. Determine tone (self-learning or override)
      2. Detect emotion from client reply (if any)
      3. Build prompt → call LLM → parse result
      4. Save to email_logs as Draft
      5. Audit log

    Returns
    -------
    {
      "success":  bool,
      "email_id": str,
      "subject":  str,
      "body":     str,
      "tone":     str,
      "emotion":  str,
      "model":    str,
      "error":    str | None
    }
    """
    init_db()

    # ── 1. Tone ──
    if tone_override:
        tone = tone_override
        tone_source = "Manual Override"
    else:
        tone_info = determine_optimal_tone(client_id, overdue_days)
        tone = tone_info["tone"]
        tone_source = tone_info["source"]

    # ── 2. Emotion ──
    emotion = ""
    confidence = 0.0
    if client_response:
        sentiment = analyse_sentiment(client_response)
        emotion    = sentiment.get("emotion", "Neutral")
        confidence = sentiment.get("confidence", 0.0)

    # ── 3. Generate ──
    prompt = _build_email_prompt(
        company_name=company_name,
        contact_name=contact_name,
        invoice_number=invoice_number,
        amount=amount,
        currency=currency,
        due_date=due_date,
        overdue_days=overdue_days,
        tone=tone,
        emotion=emotion,
        additional_context=additional_context,
    )

    model_name = ""
    subject = ""
    body = ""

    try:
        if config.AI_PROVIDER == "gemini" and gemini_client.is_configured():
            raw = gemini_client.generate_email(prompt)
            parsed = extract_email_content(raw)
            subject = parsed.get("subject", "")
            body    = parsed.get("body", "")
            model_name = f"Gemini ({config.GEMINI_MODEL})"

        elif openai_client.is_configured():
            raw = openai_client.generate_email(prompt)
            parsed = extract_email_content(raw)
            subject = parsed.get("subject", "")
            body    = parsed.get("body", "")
            model_name = f"OpenAI ({config.OPENAI_MODEL})"

        else:
            email = _template_email(
                company_name, contact_name, invoice_number,
                amount, currency, due_date, overdue_days, tone,
            )
            subject = email["subject"]
            body    = email["body"]
            model_name = "Template Engine"

    except Exception as exc:
        logger.error(f"AI email generation failed: {exc}")
        email = _template_email(
            company_name, contact_name, invoice_number,
            amount, currency, due_date, overdue_days, tone,
        )
        subject = email["subject"]
        body    = email["body"]
        model_name = "Template Engine (AI fallback)"

    if not subject or not body:
        return {
            "success": False, "email_id": "", "subject": "", "body": "",
            "tone": tone, "emotion": emotion, "model": model_name,
            "error": "AI returned empty content",
        }

    # ── 4. Persist ──
    tone_level = {"Friendly": 1, "Professional": 2, "Firm": 3,
                  "Urgent": 4, "Legal": 5}.get(tone, 2)

    # find invoice_id if possible
    inv_data = get_invoice_by_number(invoice_number)
    inv_id   = inv_data["invoice_id"] if inv_data else None

    email_id = create_email_log(
        client_id=client_id,
        subject=subject,
        body=body,
        tone=tone,
        tone_level=tone_level,
        invoice_id=inv_id,
        ai_model_used=model_name,
        detected_emotion=emotion,
        confidence_score=confidence,
    )

    # ── 5. Audit ──
    log_action("Generate", "Email", email_id, details={
        "client_id": client_id, "tone": tone, "tone_source": tone_source,
        "model": model_name, "emotion": emotion,
    })

    return {
        "success": True,
        "email_id": email_id,
        "subject": subject,
        "body": body,
        "tone": tone,
        "emotion": emotion,
        "model": model_name,
        "error": None,
    }


# ════════════════════════════════════════════════════════════════════════
# DEMO — for first-time users without real data
# ════════════════════════════════════════════════════════════════════════

def generate_demo_email(tone: str = "Professional") -> dict:
    """Generate a sample email with demo data for preview."""
    return generate_follow_up_email(
        client_id="DEMO",
        company_name="Acme Corp",
        contact_name="Rajesh Sharma",
        contact_email="rajesh@acme.com",
        invoice_number="INV-DEMO-001",
        amount=250000,
        due_date="2025-03-15",
        overdue_days=45,
        tone_override=tone,
    )


# ════════════════════════════════════════════════════════════════════════
# TEMPLATE FALLBACK — works without any AI API key
# ════════════════════════════════════════════════════════════════════════

def _template_email(
    company_name: str, contact_name: str, invoice_number: str,
    amount: float, currency: str, due_date: str, overdue_days: int,
    tone: str,
) -> dict:
    """Deterministic template email for each tone."""

    name = contact_name or "Sir/Madam"
    amt  = f"{currency} {amount:,.2f}"

    templates: dict[str, dict] = {
        "Friendly": {
            "subject": f"Gentle Reminder: Invoice {invoice_number} Payment",
            "body": (
                f"Dear {name},\n\n"
                f"I hope this message finds you well. This is a friendly reminder that "
                f"invoice {invoice_number} for {amt} was due on {due_date} and is now "
                f"{overdue_days} days past due.\n\n"
                f"We understand that oversights happen. Could you please arrange the "
                f"payment at your earliest convenience?\n\n"
                f"If you've already made the payment, please disregard this message.\n\n"
                f"Warm regards,\nAccounts Receivable Team\n{company_name}"
            ),
        },
        "Professional": {
            "subject": f"Payment Follow-Up: Invoice {invoice_number} — {overdue_days} Days Overdue",
            "body": (
                f"Dear {name},\n\n"
                f"This is to bring to your attention that invoice {invoice_number} for "
                f"{amt}, due on {due_date}, remains unpaid. The payment is now "
                f"{overdue_days} days overdue.\n\n"
                f"We kindly request you to process the outstanding payment within the "
                f"next 5 business days. Please share the payment reference once done.\n\n"
                f"For any queries, feel free to reach out.\n\n"
                f"Best regards,\nAccounts Receivable Team"
            ),
        },
        "Firm": {
            "subject": f"Urgent: Overdue Payment — Invoice {invoice_number}",
            "body": (
                f"Dear {name},\n\n"
                f"Despite our previous reminders, invoice {invoice_number} for {amt} "
                f"(due {due_date}) is now {overdue_days} days overdue.\n\n"
                f"We must insist on immediate payment. Continued non-payment may "
                f"result in suspension of services and late payment charges as per "
                f"our agreed terms.\n\n"
                f"Please arrange payment within 3 business days and share the "
                f"transaction details.\n\n"
                f"Regards,\nAccounts Receivable Team"
            ),
        },
        "Urgent": {
            "subject": f"FINAL NOTICE: Invoice {invoice_number} — Immediate Action Required",
            "body": (
                f"Dear {name},\n\n"
                f"This is a final notice regarding the overdue payment of {amt} "
                f"against invoice {invoice_number}. The payment is now {overdue_days} "
                f"days past the due date of {due_date}.\n\n"
                f"PLEASE NOTE: If payment is not received within 48 hours, we will "
                f"be forced to escalate this matter, which may include:\n"
                f"• Suspension of all credit facilities\n"
                f"• Application of late-payment interest\n"
                f"• Referral to our collections department\n\n"
                f"We strongly urge you to settle this immediately.\n\n"
                f"Regards,\nAccounts Receivable Team"
            ),
        },
        "Legal": {
            "subject": f"Legal Notice: Recovery of Dues — Invoice {invoice_number}",
            "body": (
                f"Dear {name},\n\n"
                f"SUBJECT: NOTICE BEFORE LEGAL ACTION\n\n"
                f"This notice is served in connection with the unpaid amount of {amt} "
                f"against invoice {invoice_number}, which has been outstanding for "
                f"{overdue_days} days beyond the due date of {due_date}.\n\n"
                f"Despite multiple reminders, the payment remains unsettled. We hereby "
                f"put you on notice that unless the full outstanding amount is received "
                f"within 7 days of this notice, we shall be constrained to:\n\n"
                f"1. Initiate legal proceedings for recovery of dues\n"
                f"2. Claim interest and legal costs\n"
                f"3. Report the default to credit agencies\n\n"
                f"We trust you will treat this matter with the urgency it deserves.\n\n"
                f"For and on behalf of,\nAccounts & Legal Department"
            ),
        },
    }

    return templates.get(tone, templates["Professional"])
