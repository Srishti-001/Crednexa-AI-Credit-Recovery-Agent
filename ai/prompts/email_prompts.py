"""
Prompt templates for AI-generated follow-up emails.
"""


def get_email_prompt(
    company_name: str,
    contact_name: str,
    invoice_number: str,
    amount: float,
    currency: str,
    due_date: str,
    overdue_days: int,
    tone: str,
    detected_emotion: str = "Neutral",
    previous_emails_count: int = 0,
    payment_history: str = "",
    additional_context: str = "",
) -> str:
    """Generate the prompt for follow-up email creation."""

    tone_instructions = {
        "Friendly": """Use a warm, understanding tone. Express empathy and offer to help.
Suggest it might be an oversight. Keep it light and supportive.""",

        "Professional": """Use a polished, business-appropriate tone. Be courteous but clear
about the overdue payment. Reference company policies professionally.""",

        "Firm": """Be direct and assertive while remaining respectful. Clearly state the
consequences of continued non-payment. Set a firm deadline for resolution.""",

        "Urgent": """Convey strong urgency. Emphasize the serious consequences of non-payment
including potential service disruption and credit impact. Demand immediate action.""",

        "Legal": """Use formal legal language. Reference potential legal proceedings, collections
action, and contractual obligations. This is a final notice before escalation.""",
    }

    emotion_context = ""
    if detected_emotion and detected_emotion != "Neutral":
        emotion_context = f"""
IMPORTANT - Client Emotion Context:
The client's last communication showed signs of "{detected_emotion}" sentiment.
Adjust your email accordingly:
- If "Frustrated": Acknowledge their frustration, offer solutions
- If "Angry": Be calm, professional, avoid escalating tension
- If "Desperate": Show empathy, offer flexible payment options
- If "Cooperative": Reinforce positive relationship, encourage prompt resolution
- If "Happy": Maintain positive momentum, gently remind about payment
"""

    return f"""You are a professional credit recovery specialist. Generate a follow-up email
for an overdue invoice payment.

CLIENT DETAILS:
- Company: {company_name}
- Contact Person: {contact_name or "Sir/Madam"}
- Invoice Number: {invoice_number}
- Outstanding Amount: {currency} {amount:,.2f}
- Due Date: {due_date}
- Days Overdue: {overdue_days} days
- Previous Follow-ups Sent: {previous_emails_count}
{f"- Payment History Notes: {payment_history}" if payment_history else ""}
{f"- Additional Context: {additional_context}" if additional_context else ""}

TONE: {tone}
{tone_instructions.get(tone, tone_instructions["Professional"])}
{emotion_context}

GUIDELINES:
1. Address the contact by name if available
2. Clearly reference the invoice number and amount
3. Be specific about the overdue duration
4. Include a clear call-to-action
5. Suggest payment methods or contact information
6. Keep the email concise (under 200 words)
7. Include appropriate greeting and sign-off
8. If this is a repeat follow-up (#{previous_emails_count + 1}), reference previous attempts

Respond with a JSON object containing:
{{
    "subject": "Email subject line",
    "body": "Complete email body with proper formatting"
}}"""


def get_bulk_email_prompt(invoices: list, tone: str) -> str:
    """Generate prompt for bulk email generation for multiple overdue invoices."""
    invoice_list = "\n".join([
        f"- {inv['invoice_number']}: {inv.get('currency', 'INR')} {inv['amount']:,.2f} "
        f"(Due: {inv['due_date']}, {inv.get('overdue_days', 0)} days overdue)"
        for inv in invoices
    ])

    return f"""Generate a professional follow-up email addressing multiple overdue invoices.

OVERDUE INVOICES:
{invoice_list}

TONE: {tone}

Generate a single email that references all overdue invoices with their details.
Include total outstanding amount. Be clear and professional.

Respond with JSON: {{"subject": "...", "body": "..."}}"""
