"""
Prompt templates for AI Recovery Strategy Engine.
"""


def get_strategy_prompt(
    company_name: str,
    total_outstanding: float,
    overdue_invoices: list,
    payment_history: str = "",
    risk_score: float = 0,
    risk_category: str = "Medium",
    broken_promises: int = 0,
    previous_strategies: list = None,
    industry: str = "",
) -> str:
    """Generate prompt for recovery strategy generation."""

    invoices_detail = "\n".join([
        f"  - {inv.get('invoice_number', 'N/A')}: ₹{inv.get('amount', 0):,.2f} "
        f"({inv.get('overdue_days', 0)} days overdue, Status: {inv.get('status', 'Unknown')})"
        for inv in overdue_invoices
    ])

    prev_strategies = ""
    if previous_strategies:
        prev_strategies = "\nPREVIOUS STRATEGIES TRIED:\n" + "\n".join([
            f"  - {s.get('strategy_type', 'Unknown')}: {s.get('status', 'Unknown')} - {s.get('description', '')[:100]}"
            for s in previous_strategies
        ])

    return f"""You are an expert credit recovery strategist. Analyze the following client profile
and recommend the optimal recovery strategy.

CLIENT PROFILE:
- Company: {company_name}
- Industry: {industry or "Not specified"}
- Total Outstanding: ₹{total_outstanding:,.2f}
- Risk Score: {risk_score:.1f}/100 ({risk_category})
- Broken Payment Promises: {broken_promises}

OVERDUE INVOICES:
{invoices_detail}

{f"PAYMENT HISTORY: {payment_history}" if payment_history else ""}
{prev_strategies}

STRATEGY OPTIONS:
1. Negotiation - Direct discussion for payment arrangement
2. Installment - Propose structured payment plan
3. Discount - Offer early settlement discount
4. Legal - Initiate legal proceedings
5. Write-Off - Recommend writing off as bad debt

Analyze the situation and recommend the best strategy.

Respond with JSON:
{{
    "strategy_type": "Negotiation|Installment|Discount|Legal|Write-Off",
    "description": "Detailed strategy description (2-3 sentences)",
    "recommended_actions": [
        "Step 1: ...",
        "Step 2: ...",
        "Step 3: ...",
        "Step 4: ..."
    ],
    "priority": "Low|Medium|High|Critical",
    "reasoning": "Why this strategy is recommended based on the data",
    "expected_recovery_rate": "Estimated percentage of amount recoverable",
    "timeline": "Expected timeline for recovery"
}}"""
