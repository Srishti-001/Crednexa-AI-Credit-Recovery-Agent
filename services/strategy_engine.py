"""
Strategy Engine — AI-powered recovery strategy generation.
──────────────────────────────────────────────────────────────
Analyses a client's overdue profile and asks Gemini / OpenAI to
propose a tailored recovery strategy (Negotiation, Installment,
Discount, Legal, or Write-Off) with step-by-step actions.

Falls back to a deterministic rules-engine when no AI key is set.
"""

import json
from datetime import datetime

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

import config
from database.connection import init_db
from ai import gemini_client, openai_client
from ai.response_parser import extract_strategy_data
from models.client import get_client
from models.invoice import get_invoices_by_client
from models.recovery_strategy import create_strategy, get_strategies_by_client
from models.risk_score import get_latest_risk_score
from models.payment_promise import get_promises_by_client
from services.audit_service import log_action


# ════════════════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ════════════════════════════════════════════════════════════════════════

def _build_strategy_prompt(client: dict, overdue_invoices: list,
                           risk_data: dict, promise_history: list) -> str:
    """Build a rich prompt with all the context an LLM needs."""
    inv_lines = "\n".join(
        f"  • {i['invoice_number']}: ₹{i['amount']:,.2f} "
        f"(paid ₹{i.get('amount_paid', 0):,.2f}), "
        f"{i.get('overdue_days', 0)} days overdue, severity={i.get('severity', 'N/A')}"
        for i in overdue_invoices
    )

    broken = sum(1 for p in promise_history if p.get("status") == "Broken")
    fulfilled = sum(1 for p in promise_history if p.get("status") == "Fulfilled")

    return f"""You are a senior credit recovery strategist for an Indian B2B business.

CLIENT PROFILE
  Company   : {client.get('company_name', 'Unknown')}
  Industry  : {client.get('industry', 'N/A')}
  Contact   : {client.get('contact_name', 'N/A')} ({client.get('contact_email', '')})
  Risk Score: {risk_data.get('risk_score', 0):.0f}/100  ({risk_data.get('risk_category', 'Unknown')})
  Outstanding: ₹{client.get('total_outstanding', 0):,.2f}

OVERDUE INVOICES
{inv_lines or '  (none)'}

PAYMENT PROMISE HISTORY
  Total promises: {len(promise_history)}
  Fulfilled: {fulfilled}  |  Broken: {broken}

Analyse this client and respond with a JSON object:
{{
  "strategy_type": "Negotiation" | "Installment" | "Discount" | "Legal" | "Write-Off",
  "description": "2-3 sentence summary of the recommended approach",
  "recommended_actions": ["Step 1: …", "Step 2: …", "Step 3: …", "Step 4: …"],
  "priority": "Critical" | "High" | "Medium" | "Low",
  "reasoning": "Why this strategy suits this client",
  "estimated_recovery_rate": 0.0 to 1.0,
  "timeline_days": integer
}}

Only respond with the JSON object — no markdown, no extra text."""


# ════════════════════════════════════════════════════════════════════════
# AI GENERATION
# ════════════════════════════════════════════════════════════════════════

def generate_recovery_strategy(client_id: str) -> dict:
    """
    Generate a recovery strategy for one client.

    Returns
    -------
    {
      "success": bool,
      "strategy": dict | None,
      "strategy_id": str | None,
      "model": str,
      "error": str | None
    }
    """
    init_db()

    # ── gather context ──
    client = get_client(client_id)
    if not client:
        return {"success": False, "strategy": None, "strategy_id": None,
                "model": "", "error": "Client not found"}

    invoices = get_invoices_by_client(client_id)
    overdue  = [i for i in invoices if i["status"] in ("Overdue", "Partially Paid")]
    risk     = get_latest_risk_score(client_id) or {"risk_score": 0, "risk_category": "Low"}
    promises = get_promises_by_client(client_id)

    # ── AI or fallback ──
    model_name = ""
    strategy_data: dict = {}

    prompt = _build_strategy_prompt(client, overdue, risk, promises)

    try:
        if config.AI_PROVIDER == "gemini" and gemini_client.is_configured():
            raw = gemini_client.generate_strategy(prompt)
            strategy_data = extract_strategy_data(raw)
            model_name = f"Gemini ({config.GEMINI_MODEL})"

        elif openai_client.is_configured():
            raw = openai_client.generate_strategy(prompt)
            strategy_data = extract_strategy_data(raw)
            model_name = f"OpenAI ({config.OPENAI_MODEL})"

        else:
            strategy_data = _rules_based_strategy(client, overdue, risk, promises)
            model_name = "Rules Engine"

    except Exception as exc:
        logger.error(f"AI strategy generation failed: {exc}")
        strategy_data = _rules_based_strategy(client, overdue, risk, promises)
        model_name = "Rules Engine (AI fallback)"

    # ── persist ──
    strategy_id = create_strategy(
        client_id=client_id,
        strategy_type=strategy_data.get("strategy_type", "Negotiation"),
        description=strategy_data.get("description", ""),
        recommended_actions=strategy_data.get("actions",
                                               strategy_data.get("recommended_actions", [])),
        priority=strategy_data.get("priority", "Medium"),
        ai_reasoning=strategy_data.get("reasoning", ""),
    )

    log_action("Generate", "Strategy", strategy_id,
               details={"client_id": client_id, "model": model_name})

    strategy_data["strategy_id"] = strategy_id
    return {
        "success": True,
        "strategy": strategy_data,
        "strategy_id": strategy_id,
        "model": model_name,
        "error": None,
    }


# ════════════════════════════════════════════════════════════════════════
# DETERMINISTIC FALLBACK
# ════════════════════════════════════════════════════════════════════════

def _rules_based_strategy(client: dict, overdue: list,
                          risk: dict, promises: list) -> dict:
    """Generate a strategy when no AI provider is available."""
    outstanding = client.get("total_outstanding", 0)
    max_days = max((i.get("overdue_days", 0) for i in overdue), default=0)
    broken_count = sum(1 for p in promises if p.get("status") == "Broken")
    risk_score = risk.get("risk_score", 0)

    # ─ decision tree ─
    if max_days > config.LEGAL_ESCALATION_DAYS and outstanding > config.LEGAL_ESCALATION_AMOUNT:
        stype = "Legal"
        priority = "Critical"
        desc = (f"Client has ₹{outstanding:,.0f} outstanding for {max_days} days "
                f"with {broken_count} broken promises. Recommend formal legal action.")
        actions = [
            "Step 1: Send final demand notice via registered mail",
            "Step 2: Engage legal counsel for demand letter under Section 138 NI Act",
            "Step 3: File suit for recovery if no response in 15 days",
            "Step 4: Apply for interim relief / attachment order",
        ]
    elif risk_score >= 75 or max_days > 90:
        stype = "Installment"
        priority = "High"
        desc = (f"High-risk client with ₹{outstanding:,.0f} overdue. "
                f"Propose a structured payment plan to recover dues gradually.")
        actions = [
            "Step 1: Call the client's finance head for a personal meeting",
            f"Step 2: Propose 3-month installment plan (₹{outstanding/3:,.0f}/month)",
            "Step 3: Get signed commitment letter with post-dated cheques / PDCs",
            "Step 4: Set up automated monthly reminders",
        ]
    elif risk_score >= 50 or max_days > 60:
        stype = "Negotiation"
        priority = "Medium"
        desc = (f"Moderate-risk client. Engage in direct negotiation to settle "
                f"₹{outstanding:,.0f} outstanding.")
        actions = [
            "Step 1: Schedule a call with the client's accounts team",
            "Step 2: Understand cash flow constraints and payment timeline",
            "Step 3: Agree on a realistic payment date with written confirmation",
            "Step 4: Follow up 3 days before the agreed date",
        ]
    elif outstanding < 20000 and max_days > 90:
        stype = "Write-Off"
        priority = "Low"
        desc = (f"Small balance of ₹{outstanding:,.0f} overdue for {max_days} days. "
                f"Cost of recovery may exceed the balance.")
        actions = [
            "Step 1: Make one final collection attempt by phone",
            "Step 2: If unsuccessful, prepare write-off memo for management approval",
            "Step 3: Update client risk status and blacklist flag",
            "Step 4: Report as bad debt in financial statements",
        ]
    else:
        stype = "Negotiation"
        priority = "Medium"
        desc = (f"Standard follow-up recommended for ₹{outstanding:,.0f} "
                f"outstanding ({max_days} days overdue).")
        actions = [
            "Step 1: Send a professional reminder email with invoice copy",
            "Step 2: Follow up with a phone call after 3 business days",
            "Step 3: Offer flexible payment options if client needs",
            "Step 4: Escalate to senior contact if no response in 7 days",
        ]

    return {
        "strategy_type": stype,
        "description": desc,
        "actions": actions,
        "priority": priority,
        "reasoning": f"Rules-based: risk_score={risk_score:.0f}, "
                     f"max_days={max_days}, outstanding=₹{outstanding:,.0f}, "
                     f"broken_promises={broken_count}",
    }
