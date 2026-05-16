"""
Prompt templates for Self-Learning Tone Optimization AI.
"""


def get_tone_optimization_prompt(
    client_name: str,
    overdue_days: int,
    tone_history: list,
    client_emotion: str = "Neutral",
    industry: str = "",
    default_tone: str = "Professional",
) -> str:
    """Generate prompt for AI-recommended optimal tone."""

    history_text = ""
    if tone_history:
        history_text = "\nPAST TONE EFFECTIVENESS:\n" + "\n".join([
            f"  - Tone: {h.get('tone_used', 'Unknown')} → "
            f"Outcome: {h.get('detected_outcome', 'Unknown')} "
            f"(Score: {h.get('effectiveness_score', 0):.2f})"
            for h in tone_history
        ])

    return f"""You are a tone optimization AI for credit recovery communications.
Based on historical data and context, recommend the optimal communication tone.

CONTEXT:
- Client: {client_name}
- Industry: {industry or "Not specified"}
- Days Overdue: {overdue_days}
- Client's Current Emotion: {client_emotion}
- Default Tone (rules-based): {default_tone}
{history_text}

AVAILABLE TONES:
1. Friendly - Warm, supportive, understanding
2. Professional - Business-appropriate, polished
3. Firm - Direct, assertive but respectful
4. Urgent - Strong urgency, emphasize consequences
5. Legal - Formal legal language, final notice tone

Based on the historical effectiveness data and current context, what tone would
maximize the probability of payment recovery?

Respond with JSON:
{{
    "recommended_tone": "Friendly|Professional|Firm|Urgent|Legal",
    "reasoning": "Why this tone is recommended",
    "confidence": 0.0 to 1.0,
    "alternative_tone": "Second-best tone option",
    "avoid_tone": "Tone to definitely avoid and why"
}}"""
