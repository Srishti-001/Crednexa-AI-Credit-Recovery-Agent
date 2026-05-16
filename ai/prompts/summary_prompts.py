"""
Prompt templates for AI Finance Summary generation.
"""


def get_finance_summary_prompt(
    total_invoices: int,
    total_amount: float,
    total_collected: float,
    total_overdue: float,
    overdue_count: int,
    avg_overdue_days: float,
    risk_distribution: dict = None,
    top_debtors: list = None,
    recovery_rate: float = 0,
    promise_fulfillment_rate: float = 0,
) -> str:
    """Generate prompt for financial summary with insights."""

    debtors_text = ""
    if top_debtors:
        debtors_text = "\nTOP DEBTORS:\n" + "\n".join([
            f"  - {d.get('company_name', 'Unknown')}: ₹{d.get('total_outstanding', 0):,.2f} "
            f"(Risk: {d.get('risk_category', 'Unknown')})"
            for d in top_debtors[:5]
        ])

    risk_text = ""
    if risk_distribution:
        risk_text = "\nRISK DISTRIBUTION:\n" + "\n".join([
            f"  - {k}: {v} clients" for k, v in risk_distribution.items()
        ])

    return f"""You are an AI financial analyst. Generate a comprehensive financial summary
and actionable insights based on the following credit recovery data.

PORTFOLIO OVERVIEW:
- Total Invoices: {total_invoices}
- Total Invoice Amount: ₹{total_amount:,.2f}
- Total Collected: ₹{total_collected:,.2f}
- Total Overdue: ₹{total_overdue:,.2f}
- Overdue Invoice Count: {overdue_count}
- Average Days Overdue: {avg_overdue_days:.1f} days
- Recovery Rate: {recovery_rate:.1f}%
- Promise Fulfillment Rate: {promise_fulfillment_rate:.1f}%
{risk_text}
{debtors_text}

Generate a professional financial summary including:
1. Executive Summary (2-3 sentences)
2. Key Performance Indicators analysis
3. Risk Assessment overview
4. Top 3 Actionable Recommendations
5. Cash Flow Impact forecast
6. Areas of Concern

Keep it concise, data-driven, and actionable. Write for a finance manager audience."""


def get_client_summary_prompt(
    company_name: str,
    total_outstanding: float,
    total_paid: float,
    invoices: list,
    email_history: list = None,
    risk_score: float = 0,
) -> str:
    """Generate prompt for individual client financial summary."""
    return f"""Generate a brief financial summary for this client:

CLIENT: {company_name}
- Outstanding: ₹{total_outstanding:,.2f}
- Total Paid: ₹{total_paid:,.2f}
- Active Invoices: {len(invoices)}
- Risk Score: {risk_score:.1f}/100
- Emails Sent: {len(email_history) if email_history else 0}

Provide a 3-4 sentence summary of this client's payment behavior, risk level,
and recommended next action."""
